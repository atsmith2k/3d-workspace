//! Problem finder: walks the timeline and flags what goes wrong on a real machine.
//!
//!   long stitch      > 7 mm snags (warning), > 12.1 mm is past most machines' limit (error)
//!   tiny stitches    3+ stitches in a row under 0.3 mm away from a cut (the needle
//!                    hammering one spot): thread breaks, bird nests. Lock stitches next
//!                    to a trim, and lone short stitches at row ends, are normal.
//!   doubled stitch   a stitch onto the point the needle is already in: a second
//!                    penetration in one hole (machines have frozen on files full of them)
//!   needle pile-up   8+ penetrations (any colour) within 0.1 mm of one: holes in the
//!                    fabric, thread shreds
//!   coincident       the needle comes back to one hole 7+ separate times in a colour
//!                    (a bean or lock pass is one visit): each return cuts the thread
//!                    already there; 9+ is an error
//!   stitch clump     45+ penetrations of one colour within 1 mm: a knot under the
//!                    fabric that jams the needle plate
//!   short stitches   over 10 % of stitches under 0.5 mm away from ties: no proper loop
//!   stacked locks    two tie groups at one start or end: knots, breaks, mistrims
//!   too dense        over 3.5 thread layers (fill ~1, satin ~1.7): puckering, needle
//!                    breaks; over 5 is an error
//!   untrimmed jump   thread carried over 3 mm without a trim: snip by hand or it shows
//!   no tie-in/off    a run that starts or ends at a cut without lock stitches unravels
//!   hoop             the design is bigger than the chosen hoop's sewing field
//!   off-centre       extents centred over 1 mm from the origin (error over 10 mm)
//!   machine limits   stitch length, stitch count and colour changes past the
//!                    `--machine` profile (machines.rs)
//!
//! Issues of one kind close together are grouped into one marker. Positions are in the
//! file's mm (Y up), `k` is the stitch index the timeline jumps to.

use crate::machines::Profile;
use crate::sim::{Seg, Sim};
use std::collections::HashMap;

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Severity {
    Error,
    Warning,
}

#[derive(Clone, Debug)]
pub struct Issue {
    pub kind: &'static str,
    pub sev: Severity,
    pub at: [f32; 2],
    pub k: usize,
    pub detail: String,
    pub fix: &'static str,
}

pub struct Density {
    pub grid: Vec<f32>, // thread layers per cell, row 0 = lowest y
    pub nx: usize,
    pub ny: usize,
    pub x0: f32,
    pub y0: f32,
    pub cell: f32,
}

impl Density {
    pub fn max(&self) -> f32 {
        self.grid.iter().cloned().fold(0.0, f32::max)
    }
}

pub struct Report {
    pub issues: Vec<Issue>,
    pub density: Density,
    pub stats: Stats,
}

/// Counts `--info` prints for scripts, whether or not they raise a problem.
pub struct Stats {
    pub doubled: usize,
    /// stitches under 0.5 mm more than 8 stitches from a cut
    pub short: usize,
    pub short_share: f32,
    pub trims_per_1k: f32,
    /// centre of the design's extents (mm from the file origin)
    pub centre: [f32; 2],
}

pub const LONG_WARN: f32 = 7.0;
pub const SHORT: f32 = 0.3;
pub const DENSE: f32 = 3.5;
pub const VERY_DENSE: f32 = 5.0;
pub const JUMP: f32 = 3.0;
// Thresholds below were calibrated on the 398 published size builds (2026-11-03,
// `stitchsim --metrics`): normal Ink/Stitch fill, satin, underlay and travel must pass,
// the known-bad fixture in tests/test_stitch.py and the unit tests below must not.

/// needle pile-up: PILE+ penetrations (any colour) within PILE_R of one, counted around
/// each penetration. A 0.1 mm radius is a 0.2 mm spot, the old grid cell's size; the
/// corpus peaks at 9 (11 files reach 8, all clusters the grid cells used to split).
pub const PILE: usize = 8;
pub const PILE_R: f32 = 0.1;
/// one needle hole: a 0.75 mm needle's hole is ~0.3 mm across
pub const HOLE_R: f32 = 0.15;
/// coincident: separate needle visits to one hole within a colour (a bean run's or a
/// lock's a-b-a-b is one visit). Brother warns at 3 overlapping stitches, but Ink/Stitch
/// routes underlay, travel and fill edges through shared shape corners: corpus files
/// peak at 4-6 visits (median 5, p95 6, max 7 in 15 files), so 3 would flag every file.
pub const COINCIDENT: usize = 7;
pub const COINCIDENT_ERR: usize = 9;
/// clump: CLUMP+ penetrations of one colour within CLUMP_R. A 0.4 mm fill puts ~6 in a
/// 1 mm circle and satin up to ~20 (corpus median of per-file p99 18, p95 22); satin
/// pivots peak at 41 (per-file max: median 26, p95 34). 45 is above every corpus file.
pub const CLUMP: usize = 45;
pub const CLUMP_R: f32 = 1.0;
/// short stitches away from ties: the floor, and the share of sewn stitches that warns.
/// Ink/Stitch fill row ends and satin turns make 0.4-0.5 mm stitches: corpus median 4.7 %,
/// p95 7.2 %, max 16 %. 10 % flags the 4 outliers.
pub const SHORT_FLOOR: f32 = 0.5;
pub const SHORT_SHARE: f32 = 0.10;
/// design centre from the file origin (cadkit writes centred files: corpus max 0.25 mm)
pub const OFF_CENTRE: f32 = 1.0;
pub const OFF_CENTRE_ERR: f32 = 10.0;
const THREAD_W: f32 = 0.3;
const CELL: f32 = 1.0;

/// Thread layers per 1 mm cell (sewn length x 0.3 mm thread width / cell area),
/// smoothed over 3x3 cells: the same measure `cad stitch` reports.
pub fn density(sim: &Sim) -> Density {
    let b = sim.bounds;
    let (x0, y0) = (b[0] - 2.0 * CELL, b[1] - 2.0 * CELL);
    let nx = ((b[2] - x0) / CELL) as usize + 3;
    let ny = ((b[3] - y0) / CELL) as usize + 3;
    let mut g = vec![0.0f32; nx * ny];
    for s in &sim.segs {
        let (dx, dy) = (s.b[0] - s.a[0], s.b[1] - s.a[1]);
        let l = (dx * dx + dy * dy).sqrt();
        let n = (l / 0.1).ceil().max(1.0) as usize;
        let w = l / n as f32 * THREAD_W / (CELL * CELL);
        for i in 0..n {
            let t = (i as f32 + 0.5) / n as f32;
            let ix = ((s.a[0] + dx * t - x0) / CELL) as usize;
            let iy = ((s.a[1] + dy * t - y0) / CELL) as usize;
            if ix < nx && iy < ny {
                g[iy * nx + ix] += w;
            }
        }
    }
    let mut sm = vec![0.0f32; nx * ny];
    for y in 0..ny {
        for x in 0..nx {
            let mut acc = 0.0;
            for dy in -1i32..=1 {
                for dx in -1i32..=1 {
                    let (xx, yy) = (x as i32 + dx, y as i32 + dy);
                    if xx >= 0 && yy >= 0 && (xx as usize) < nx && (yy as usize) < ny {
                        acc += g[yy as usize * nx + xx as usize];
                    }
                }
            }
            sm[y * nx + x] = acc / 9.0;
        }
    }
    Density { grid: sm, nx, ny, x0, y0, cell: CELL }
}

/// Collects hits of one kind into regions: a hit within `r` mm of a region's extent
/// joins it, and regions it bridges merge. Each region becomes one marker at its centre,
/// pointing at its earliest stitch.
struct Groups {
    r: f32,
    groups: Vec<([f32; 4], usize, usize, f32)>, // (bbox, first k, count, worst value)
}

impl Groups {
    fn new(r: f32) -> Self {
        Groups { r, groups: Vec::new() }
    }
    fn add(&mut self, p: [f32; 2], k: usize, v: f32) {
        let r = self.r;
        let near: Vec<usize> = (0..self.groups.len())
            .filter(|&g| {
                let b = self.groups[g].0;
                p[0] >= b[0] - r && p[0] <= b[2] + r && p[1] >= b[1] - r && p[1] <= b[3] + r
            })
            .collect();
        let Some(&first) = near.first() else {
            self.groups.push(([p[0], p[1], p[0], p[1]], k, 1, v));
            return;
        };
        for &g in near[1..].iter().rev() {
            let (b, k2, n2, v2) = self.groups.remove(g);
            let e = &mut self.groups[first];
            e.0 = [e.0[0].min(b[0]), e.0[1].min(b[1]), e.0[2].max(b[2]), e.0[3].max(b[3])];
            e.1 = e.1.min(k2);
            e.2 += n2;
            e.3 = e.3.max(v2);
        }
        let e = &mut self.groups[first];
        e.0 = [e.0[0].min(p[0]), e.0[1].min(p[1]), e.0[2].max(p[0]), e.0[3].max(p[1])];
        e.1 = e.1.min(k);
        e.2 += 1;
        e.3 = e.3.max(v);
    }
    /// (centre, first k, count, worst value)
    fn regions(self) -> Vec<([f32; 2], usize, usize, f32)> {
        self.groups.into_iter().map(|(b, k, n, v)| ([(b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0], k, n, v)).collect()
    }
}

pub fn analyze(sim: &Sim, hoop: Option<(&str, f32, f32)>, machine: &Profile) -> Report {
    let mut issues = Vec::new();
    let segs = &sim.segs;
    let len = |i: usize| {
        let s = &segs[i];
        ((s.b[0] - s.a[0]).powi(2) + (s.b[1] - s.a[1]).powi(2)).sqrt()
    };
    let mid = |i: usize| {
        let s = &segs[i];
        [(s.a[0] + s.b[0]) / 2.0, (s.a[1] + s.b[1]) / 2.0]
    };

    // long stitches
    // one region per area; it is an error when its worst stitch is past the machine limit
    let mut long = Groups::new(3.0);
    for i in 0..segs.len() {
        if len(i) > LONG_WARN {
            long.add(mid(i), i, len(i));
        }
    }
    for (at, k, n, v) in long.regions() {
        issues.push(if v > machine.max_stitch {
            Issue {
                kind: "stitch too long", sev: Severity::Error, at, k,
                detail: format!("{n} stitch{} over 7 mm, up to {v:.1} mm ({} limit {:.1} mm)", plural(n), machine.name, machine.max_stitch),
                fix: "split the column or use a fill; the machine will cut it into jumps or refuse it",
            }
        } else {
            Issue {
                kind: "long stitch", sev: Severity::Warning, at, k,
                detail: format!("{n} stitch{} up to {v:.1} mm", plural(n)),
                fix: "satin over ~7 mm snags and loops: narrow it, split it, or make it a fill",
            }
        });
    }

    // runs of 3+ tiny stitches in a row, except next to a cut (tie-ins and tie-offs)
    let mut near_cut = vec![false; segs.len()];
    for k in std::iter::once(0).chain(sim.jumps.iter().map(|j| j.after)).chain(std::iter::once(segs.len())) {
        for slot in near_cut.iter_mut().take((k + 8).min(segs.len())).skip(k.saturating_sub(8)) {
            *slot = true;
        }
    }
    let mut tiny = Groups::new(2.0);
    let mut run = 0;
    for i in 0..segs.len() {
        run = if len(i) < SHORT && !near_cut[i] { run + 1 } else { 0 };
        if run == 3 {
            tiny.add(mid(i), i - 2, 0.0);
        }
    }
    for (at, k, n, _) in tiny.regions() {
        issues.push(Issue {
            kind: "tiny stitches", sev: Severity::Warning, at, k,
            detail: format!("tiny stitches in a row under {SHORT} mm ({n} spot{})", if n == 1 { "" } else { "s" }),
            fix: "the thread breaks or nests: remove short stitches (min stitch length) or simplify the outline",
        });
    }

    // doubled penetrations: a zero-length stitch
    let mut dbl = Groups::new(3.0);
    for &(p, k) in &sim.doubled {
        dbl.add(p, k, 0.0);
    }
    for (at, k, n, _) in dbl.regions() {
        issues.push(Issue {
            kind: "doubled stitch", sev: Severity::Warning, at, k,
            detail: format!("{n} zero-length stitch{} (the needle goes into the same hole twice)", plural(n)),
            fix: "drop stitches onto the point the needle is already at (cadkit's pattern.prepare does)",
        });
    }

    let pens = penetrations(sim);
    let near4 = near_cuts(sim, 4);
    let by_block = by_block(&pens);

    // needle pile-ups: penetrations within PILE_R of one another, counted around each
    // penetration (a radius, so a cluster straddling a grid line is still one cluster)
    let all: Vec<usize> = (0..pens.len()).collect();
    let counts = neighbours(&pens, &all, PILE_R);
    let mut pile = Groups::new(3.0);
    for (&i, &n) in all.iter().zip(&counts) {
        if n >= PILE {
            pile.add(pens[i].p, pens[i].k, n as f32);
        }
    }
    for (at, k, n, v) in pile.regions() {
        issues.push(Issue {
            kind: "needle pile-up", sev: Severity::Warning, at, k,
            detail: if n == 1 {
                format!("{} needle penetrations in one {:.1} mm spot", v as usize, 2.0 * PILE_R)
            } else {
                format!("{n} penetrations in spots with up to {} in {:.1} mm", v as usize, 2.0 * PILE_R)
            },
            fix: "cuts a hole and shreds thread: use short stitches at corners, spread the pivot, avoid restarting on the same point",
        });
    }

    // coincident penetrations: one hole visited again and again within a colour, lock
    // groups next to a cut left out
    let mut coin = Groups::new(3.0);
    for idx in &by_block {
        let idx: Vec<usize> = idx.iter().copied().filter(|&i| !near4[pens[i].k]).collect();
        for (&i, &n) in idx.iter().zip(&hole_visits(&pens, &idx)) {
            if n >= COINCIDENT {
                coin.add(pens[i].p, pens[i].k, n as f32);
            }
        }
    }
    for (at, k, _, v) in coin.regions() {
        issues.push(Issue {
            kind: "coincident stitches", sev: if v as usize >= COINCIDENT_ERR { Severity::Error } else { Severity::Warning }, at, k,
            detail: format!("the needle comes back to one hole {} separate times in one colour", v as usize),
            fix: "each return cuts the thread already in the hole (Brother warns at 3 overlapping stitches): route travel and underlay off the corner, start the next object elsewhere",
        });
    }

    // clumps: many penetrations of one colour in a 1 mm circle
    let mut clump = Groups::new(2.0);
    for idx in &by_block {
        for (&i, &n) in idx.iter().zip(&neighbours(&pens, idx, CLUMP_R)) {
            if n >= CLUMP {
                clump.add(pens[i].p, pens[i].k, n as f32);
            }
        }
    }
    for (at, k, _, v) in clump.regions() {
        issues.push(Issue {
            kind: "stitch clump", sev: Severity::Warning, at, k,
            detail: format!("up to {} penetrations of one colour within {CLUMP_R} mm (normal fill and satin stay under {CLUMP})", v as usize),
            fix: "a knot of thread builds up underneath and jams the needle plate: thin the stitches there (de-clump), spread the corner",
        });
    }

    // short stitches away from ties, as a share of all stitches
    let near8 = near_cuts(sim, 8);
    let short = (0..segs.len()).filter(|&i| len(i) < SHORT_FLOOR && !near8[i] && !near8[i + 1]).count();
    let share = if segs.is_empty() { 0.0 } else { short as f32 / segs.len() as f32 };
    if share > SHORT_SHARE {
        let first = (0..segs.len()).find(|&i| len(i) < SHORT_FLOOR && !near8[i] && !near8[i + 1]).unwrap_or(0);
        issues.push(Issue {
            kind: "short stitches", sev: Severity::Warning, at: mid(first), k: first,
            detail: format!("{short} stitches under {SHORT_FLOOR} mm away from ties ({:.1} % of stitches, limit {:.1} %)", share * 100.0, SHORT_SHARE * 100.0),
            fix: "stitches under 0.5 mm don't form a proper loop and fray the thread: raise the minimum stitch length",
        });
    }

    // stacked locks: more than one lock group at a run's start or end
    let mut stacked = Groups::new(2.0);
    for (a, b) in runs(sim) {
        let n = lock_groups(segs, a, true, b - a);
        if n > 1 {
            stacked.add(segs[a].a, a, n as f32);
        }
        let n = lock_groups(segs, b, false, b - a);
        if n > 1 {
            stacked.add(segs[b - 1].b, b - 1, n as f32);
        }
    }
    for (at, k, n, v) in stacked.regions() {
        issues.push(Issue {
            kind: "stacked locks", sev: Severity::Warning, at, k,
            detail: format!("{n} run end{} with {} lock groups on top of each other", if n == 1 { "" } else { "s" }, v as usize),
            fix: "doubled ties knot up, break the thread and confuse the trimmer: keep one lock group per start and trim",
        });
    }

    // density hot spots (each tagged with the first stitch that lands near it)
    let dens = density(sim);
    let mut first: HashMap<(i32, i32), usize> = HashMap::new();
    for (i, s) in segs.iter().enumerate() {
        first.entry(((s.b[0] / CELL).floor() as i32, (s.b[1] / CELL).floor() as i32)).or_insert(i + 1);
    }
    let nearest_stitch = |_: &Sim, p: [f32; 2]| -> usize {
        let (cx, cy) = ((p[0] / CELL).floor() as i32, (p[1] / CELL).floor() as i32);
        (0..=3)
            .find_map(|r| {
                (-r..=r).flat_map(|dx| (-r..=r).map(move |dy| (dx, dy))).filter_map(|(dx, dy)| first.get(&(cx + dx, cy + dy))).min().copied()
            })
            .unwrap_or(0)
    };
    let mut dense = Groups::new(1.5);
    for iy in 0..dens.ny {
        for ix in 0..dens.nx {
            let v = dens.grid[iy * dens.nx + ix];
            if v > DENSE {
                let p = [dens.x0 + (ix as f32 + 0.5) * dens.cell, dens.y0 + (iy as f32 + 0.5) * dens.cell];
                dense.add(p, nearest_stitch(sim, p), v);
            }
        }
    }
    for (at, k, n, v) in dense.regions() {
        issues.push(if v > VERY_DENSE {
            Issue {
                kind: "far too dense", sev: Severity::Error, at, k,
                detail: format!("up to {v:.1} thread layers over {n} mm2"),
                fix: "stacked fills or overlapping columns: knock out the layer underneath, open the row spacing",
            }
        } else {
            Issue {
                kind: "too dense", sev: Severity::Warning, at, k,
                detail: format!("up to {v:.1} thread layers over {n} mm2 (limit {DENSE})"),
                fix: "puckering and needle breaks: reduce overlap, open the spacing, tuck fills under borders",
            }
        });
    }

    // jumps: untrimmed carries, and runs that start or end at a cut without locks
    for j in &sim.jumps {
        let d = ((j.b[0] - j.a[0]).powi(2) + (j.b[1] - j.a[1]).powi(2)).sqrt();
        if !j.trimmed && !j.color_change && d > JUMP {
            issues.push(Issue {
                kind: "untrimmed jump", sev: Severity::Warning, at: [(j.a[0] + j.b[0]) / 2.0, (j.a[1] + j.b[1]) / 2.0],
                k: j.after, detail: format!("{d:.1} mm jump thread, no trim"),
                fix: "add a trim (or let the machine trim jumps); otherwise snip it by hand after sewing",
            });
        }
    }
    let cut_after: Vec<usize> = sim.jumps.iter().filter(|j| j.trimmed || j.color_change).map(|j| j.after).collect();
    let mut no_lock = Groups::new(2.0);
    let starts = std::iter::once(0usize).chain(cut_after.iter().copied());
    for k in starts {
        if k < segs.len() && !locked(segs, k, true) {
            no_lock.add(segs[k].a, k, 0.0);
        }
    }
    for &k in cut_after.iter().chain(std::iter::once(&segs.len())) {
        if k > 0 && !locked(segs, k, false) {
            no_lock.add(segs[k - 1].b, k - 1, 1.0);
        }
    }
    for (at, k, _, v) in no_lock.regions() {
        issues.push(Issue {
            kind: if v > 0.5 { "no tie-off" } else { "no tie-in" }, sev: Severity::Warning, at, k,
            detail: format!("thread {} at a trim with no lock stitches", if v > 0.5 { "ends" } else { "starts" }),
            fix: "add lock stitches (2-3 tiny back-and-forth stitches) so it can't unravel",
        });
    }

    // hoop
    if let Some((name, w, h)) = hoop {
        let (dw, dh) = sim.size();
        if dw > w || dh > h {
            let b = sim.bounds;
            issues.push(Issue {
                kind: "too big for hoop", sev: Severity::Error, at: [(b[0] + b[2]) / 2.0, b[3]], k: 0,
                detail: format!("{dw:.0} x {dh:.0} mm design, {name} field is {w:.0} x {h:.0} mm"),
                fix: "use a bigger hoop, or rebuild the design smaller (scaling a stitch file changes its density)",
            });
        }
    }
    // off-centre: machines place the file origin at the hoop centre
    let b = sim.bounds;
    let centre = if segs.is_empty() { [0.0, 0.0] } else { [(b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0] };
    let off = (centre[0].powi(2) + centre[1].powi(2)).sqrt();
    if off > OFF_CENTRE {
        issues.push(Issue {
            kind: "off-centre", sev: if off > OFF_CENTRE_ERR { Severity::Error } else { Severity::Warning }, at: centre, k: 0,
            detail: format!("design centre is {off:.1} mm from the file origin ({:.1}, {:.1})", centre[0], centre[1]),
            fix: "the machine centres the origin in the hoop, so the design sews off-centre or past the field (an SE600 resets): re-centre the file",
        });
    }

    // machine limits
    if sim.penetrations > machine.max_stitches {
        issues.push(Issue {
            kind: "too many stitches", sev: Severity::Error, at: centre, k: 0,
            detail: format!("{} stitches, {} loads at most {}", sim.penetrations, machine.name, machine.max_stitches),
            fix: "the machine refuses the file: split the design into two hoopings or simplify the fills",
        });
    }
    let changes = sim.block_start.len().saturating_sub(1);
    if changes > machine.max_changes {
        issues.push(Issue {
            kind: "too many colours", sev: Severity::Error, at: centre, k: 0,
            detail: format!("{changes} colour changes, {} holds at most {}", machine.name, machine.max_changes),
            fix: "merge blocks of the same thread, or split the design into two files",
        });
    }

    issues.sort_by(|a, b| a.sev.cmp(&b.sev).then(a.k.cmp(&b.k)));
    let stats = Stats {
        doubled: sim.doubled.len(),
        short,
        short_share: share,
        trims_per_1k: if sim.penetrations == 0 { 0.0 } else { sim.trims as f32 * 1000.0 / sim.penetrations as f32 },
        centre,
    };
    Report { issues, density: dens, stats }
}

fn plural(n: usize) -> &'static str {
    if n == 1 { "" } else { "es" }
}

/// Lock stitches: within the first (or last) four stitches of a run, a short stitch
/// that doubles back on the one before it.
fn locked(segs: &[crate::sim::Seg], k: usize, start: bool) -> bool {
    let idx: Vec<usize> = if start { (k..(k + 4).min(segs.len())).collect() } else { (k.saturating_sub(4)..k).collect() };
    idx.windows(2).any(|w| {
        let (a, b) = (&segs[w[0]], &segs[w[1]]);
        let va = [a.b[0] - a.a[0], a.b[1] - a.a[1]];
        let vb = [b.b[0] - b.a[0], b.b[1] - b.a[1]];
        let lb = (vb[0] * vb[0] + vb[1] * vb[1]).sqrt();
        lb < 1.6 && va[0] * vb[0] + va[1] * vb[1] < 0.0
    })
}

/// A needle penetration: where, the timeline index it lands at, its colour block.
struct Pen {
    p: [f32; 2],
    k: usize,
    block: u16,
}

/// Every penetration of the sewn stitches: each run's first point, then every stitch end.
fn penetrations(sim: &Sim) -> Vec<Pen> {
    let segs = &sim.segs;
    let mut starts: Vec<usize> = std::iter::once(0).chain(sim.jumps.iter().map(|j| j.after)).filter(|&k| k < segs.len()).collect();
    starts.dedup();
    let mut out = Vec::with_capacity(segs.len() + starts.len());
    let mut si = 0;
    for (i, s) in segs.iter().enumerate() {
        while si < starts.len() && starts[si] < i {
            si += 1;
        }
        if si < starts.len() && starts[si] == i {
            out.push(Pen { p: s.a, k: i, block: s.block });
            si += 1;
        }
        out.push(Pen { p: s.b, k: i + 1, block: s.block });
    }
    out
}

/// Timeline positions (0..=len) within `w` stitches of a cut, trim, colour change or
/// either end: where lock stitches live.
fn near_cuts(sim: &Sim, w: usize) -> Vec<bool> {
    let n = sim.segs.len();
    let mut near = vec![false; n + 1];
    for c in std::iter::once(0).chain(sim.jumps.iter().map(|j| j.after)).chain(std::iter::once(n)) {
        for slot in near.iter_mut().take((c + w + 1).min(n + 1)).skip(c.saturating_sub(w)) {
            *slot = true;
        }
    }
    near
}

/// Penetration indices per colour block.
fn by_block(pens: &[Pen]) -> Vec<Vec<usize>> {
    let mut out: Vec<Vec<usize>> = Vec::new();
    for (i, p) in pens.iter().enumerate() {
        let b = p.block as usize;
        if out.len() <= b {
            out.resize(b + 1, Vec::new());
        }
        out[b].push(i);
    }
    out
}

/// For each of `idx`, how many of `idx` (itself included) lie within `r` mm: a spatial
/// hash of `r`-sized cells, searched over the 3x3 cells around each point.
fn neighbours(pens: &[Pen], idx: &[usize], r: f32) -> Vec<usize> {
    let key = |p: [f32; 2]| ((p[0] / r).floor() as i32, (p[1] / r).floor() as i32);
    let mut cells: HashMap<(i32, i32), Vec<[f32; 2]>> = HashMap::new();
    for &i in idx {
        cells.entry(key(pens[i].p)).or_default().push(pens[i].p);
    }
    let r2 = r * r + 1e-6;
    idx.iter()
        .map(|&i| {
            let p = pens[i].p;
            let (cx, cy) = key(p);
            let mut n = 0;
            for dx in -1..=1 {
                for dy in -1..=1 {
                    if let Some(v) = cells.get(&(cx + dx, cy + dy)) {
                        n += v.iter().filter(|q| (q[0] - p[0]).powi(2) + (q[1] - p[1]).powi(2) <= r2).count();
                    }
                }
            }
            n
        })
        .collect()
}

/// Lock groups at a cut, read from the cut inward (no more than half the run, so a short
/// run's own tie-off is not read as its tie-in). A lock group is a back-and-forth tie
/// (a-b-a-b: each penetration back in the hole two before, stitches under AB_LEN) or a
/// closed triangle tie (a-b-c-a, sides under TRI_LEN). Groups count while they follow
/// each other directly; an a-b tie with more than AB_MAX returns is two ties sewn on
/// one spot (one 4-stitch tie has 3 returns, a neighbouring stitch landing in its hole
/// makes 4-5: 7,600 of 8,900 corpus ties have 2-3, 12 have 5, none more).
/// Bean (triple) runs also go back into the hole two before, but with stitches over
/// 1 mm, so AB_LEN keeps them out.
/// Returns (groups, longest a-b tie in returns).
const LOCK_WINDOW: usize = 16;
const AB_LEN: f32 = 0.83;   // off the 0.1 mm grid (0.825, 0.849 either side): no knife edge
const TRI_LEN: f32 = 1.23;  // between grid distances 1.221 and 1.237
const AB_MAX: usize = 5;

fn lock_units(segs: &[Seg], k: usize, start: bool, run: usize) -> (usize, usize) {
    let w = LOCK_WINDOW.min(run / 2);
    let mut p: Vec<[f32; 2]> = Vec::new();
    if start {
        for s in segs.iter().skip(k).take(w) {
            if p.is_empty() {
                p.push(s.a);
            }
            p.push(s.b);
        }
    } else {
        for s in segs[..k].iter().rev().take(w) {
            if p.is_empty() {
                p.push(s.b);
            }
            p.push(s.a);
        }
    }
    let d = |a: [f32; 2], b: [f32; 2]| (a[0] - b[0]).hypot(a[1] - b[1]);
    let same = |i: usize, j: usize| d(p[i], p[j]) <= HOLE_R;
    let (mut groups, mut longest, mut i, mut gap) = (0, 0, 0, 0);
    while i + 2 < p.len() && gap <= 1 {
        if same(i + 2, i) && d(p[i], p[i + 1]) < AB_LEN && !same(i, i + 1) {
            let mut j = i + 2;
            while j + 1 < p.len() && same(j + 1, j - 1) {
                j += 1;
            }
            let returns = j - i - 1;
            longest = longest.max(returns);
            groups += if returns > AB_MAX { 2 } else { 1 };
            i = j;
            gap = 0;
        } else if i + 3 < p.len() && same(i + 3, i) && (0..3).all(|t| d(p[i + t], p[i + t + 1]) < TRI_LEN && !same(i + t, i + t + 1)) {
            groups += 1;
            i += 3;
            gap = 0;
        } else {
            i += 1;
            gap += 1;
        }
    }
    (groups, longest)
}

fn lock_groups(segs: &[Seg], k: usize, start: bool, run: usize) -> usize {
    lock_units(segs, k, start, run).0
}

/// Every run between cuts (trims, colour changes, jumps) as (first stitch, end).
fn runs(sim: &Sim) -> Vec<(usize, usize)> {
    let mut b: Vec<usize> = std::iter::once(0).chain(sim.jumps.iter().map(|j| j.after)).chain(std::iter::once(sim.segs.len())).collect();
    b.dedup();
    b.windows(2).filter(|w| w[1] > w[0]).map(|w| (w[0], w[1])).collect()
}

/// For each penetration in `idx`, how many separate visits the needle makes to its hole
/// (within HOLE_R, same list): penetrations of one pass (a bean run's a-b-a-b, a lock)
/// are within VISIT_GAP stitches of each other on the timeline and count as one visit.
const VISIT_GAP: usize = 4;

fn hole_visits(pens: &[Pen], idx: &[usize]) -> Vec<usize> {
    let key = |p: [f32; 2]| ((p[0] / HOLE_R).floor() as i32, (p[1] / HOLE_R).floor() as i32);
    let mut cells: HashMap<(i32, i32), Vec<usize>> = HashMap::new();
    for &i in idx {
        cells.entry(key(pens[i].p)).or_default().push(i);
    }
    let r2 = HOLE_R * HOLE_R + 1e-6;
    let mut ks = Vec::new();
    idx.iter()
        .map(|&i| {
            let p = pens[i].p;
            let (cx, cy) = key(p);
            ks.clear();
            for dx in -1..=1 {
                for dy in -1..=1 {
                    if let Some(v) = cells.get(&(cx + dx, cy + dy)) {
                        ks.extend(v.iter().filter(|&&j| (pens[j].p[0] - p[0]).powi(2) + (pens[j].p[1] - p[1]).powi(2) <= r2).map(|&j| pens[j].k));
                    }
                }
            }
            ks.sort_unstable();
            1 + ks.windows(2).filter(|w| w[1] - w[0] > VISIT_GAP).count()
        })
        .collect()
}

/// Raw measures behind the rules, `name value` pairs: the hidden `--metrics` flag prints
/// them for calibrating the thresholds on a corpus.
pub fn metrics(sim: &Sim) -> Vec<(&'static str, f32)> {
    let segs = &sim.segs;
    let pens = penetrations(sim);
    let near4 = near_cuts(sim, 4);
    let blocks = by_block(&pens);
    let all: Vec<usize> = (0..pens.len()).collect();
    let mut out = Vec::new();
    // the old 0.2 mm grid-cell pile-up count, for comparison
    let mut holes: HashMap<(i32, i32), usize> = HashMap::new();
    for s in segs {
        *holes.entry(((s.b[0] / 0.2).floor() as i32, (s.b[1] / 0.2).floor() as i32)).or_default() += 1;
    }
    out.push(("pile_cell_max", holes.values().copied().max().unwrap_or(0) as f32));
    for (name, r) in [("pile_r01_max", 0.1), ("pile_r02_max", 0.2)] {
        out.push((name, neighbours(&pens, &all, r).into_iter().max().unwrap_or(0) as f32));
    }
    let mut clump = Vec::new();
    for idx in &blocks {
        clump.extend(neighbours(&pens, idx, CLUMP_R));
    }
    clump.sort_unstable();
    let q = |f: f32| clump.get(((clump.len() as f32 - 1.0) * f) as usize).copied().unwrap_or(0) as f32;
    out.push(("clump_p50", q(0.5)));
    out.push(("clump_p99", q(0.99)));
    out.push(("clump_p999", q(0.999)));
    out.push(("clump_max", q(1.0)));
    let near8 = near_cuts(sim, 8);
    let len = |s: &Seg| (s.b[0] - s.a[0]).hypot(s.b[1] - s.a[1]);
    let short = (0..segs.len()).filter(|&i| len(&segs[i]) < SHORT_FLOOR && !near8[i] && !near8[i + 1]).count();
    out.push(("short", short as f32));
    out.push(("short_share", if segs.is_empty() { 0.0 } else { short as f32 / segs.len() as f32 }));
    let mut ab_max = 0;
    let mut stacked = 0;
    for (k, st, run) in runs(sim).into_iter().flat_map(|(a, b)| [(a, true, b - a), (b, false, b - a)]) {
        let (g, ab) = lock_units(segs, k, st, run);
        ab_max = ab_max.max(ab);
        stacked += (g > 1) as usize;
    }
    out.push(("lock_ab_max", ab_max as f32));
    out.push(("lock_stacked", stacked as f32));
    let mut visits = Vec::new();
    for idx in &blocks {
        let far: Vec<usize> = idx.iter().copied().filter(|&i| !near4[pens[i].k]).collect();
        visits.extend(hole_visits(&pens, &far));
    }
    out.push(("visit_max", visits.iter().copied().max().unwrap_or(0) as f32));
    out.push(("visit_ge3", visits.iter().filter(|&&n| n >= 3).count() as f32));
    let b = sim.bounds;
    out.push(("centre_off", ((b[0] + b[2]) / 2.0).hypot((b[1] + b[3]) / 2.0)));
    out.push(("trims_per_1k", sim.trims as f32 * 1000.0 / sim.penetrations.max(1) as f32));
    out.push(("doubled", sim.doubled.len() as f32));
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::machines::PROFILES;
    use crate::pattern::{Cmd, Kind, Pattern};
    use crate::sim::Machine;

    /// A pattern from absolute stitch points (mm); `None` is a trim.
    fn sim_of(pts: &[Option<(f32, f32)>]) -> Sim {
        let mut p = Pattern::default();
        for q in pts {
            match q {
                Some((x, y)) => p.cmds.push(Cmd { x: *x, y: *y, kind: Kind::Stitch }),
                None => p.push_cmd(Kind::Trim),
            }
        }
        p.push_cmd(Kind::End);
        Sim::new(&p, Machine::default())
    }

    fn pts(v: &[(f32, f32)]) -> Vec<Option<(f32, f32)>> {
        v.iter().map(|&q| Some(q)).collect()
    }

    /// A plain running line of 2 mm stitches, to pad runs away from their cuts.
    fn line(from: (f32, f32), n: usize) -> Vec<(f32, f32)> {
        (0..n).map(|i| (from.0 + 2.0 * i as f32, from.1)).collect()
    }

    fn report(s: &Sim) -> Report {
        analyze(s, None, &PROFILES[0])
    }

    fn has(r: &Report, kind: &str) -> bool {
        r.issues.iter().any(|i| i.kind == kind)
    }

    /// Petals out of a centre and back: the needle returns to `centre(i)` once per petal,
    /// 6 stitches apart (separate visits, not one a-b-a-b pass).
    fn petals(n: usize, centre: impl Fn(usize) -> (f32, f32)) -> Vec<(f32, f32)> {
        let mut v = line((-30.0, 0.0), 10);
        for i in 0..n {
            let c = centre(i);
            let a = i as f32 * 0.7;
            v.push(c);
            for r in [1.5, 3.0, 4.5] {
                v.push((c.0 + r * a.cos(), c.1 + r * a.sin()));
            }
            for r in [3.0, 1.5] {
                v.push((c.0 + r * (a + 0.3).cos(), c.1 + r * (a + 0.3).sin()));
            }
        }
        v.extend(line((10.0, 10.0), 10));
        v
    }

    #[test]
    fn coincident_flags_a_hole_visited_again_and_again() {
        let r = report(&sim_of(&pts(&petals(8, |_| (0.0, 0.0)))));
        assert!(has(&r, "coincident stitches"), "{:?}", r.issues);
        let r = report(&sim_of(&pts(&petals(8, |i| (0.0, 0.8 * i as f32)))));
        assert!(!has(&r, "coincident stitches"), "{:?}", r.issues);
    }

    #[test]
    fn coincident_ignores_bean_and_lock_passes() {
        // bean run: every hole three times, in one pass
        let mut v = line((-30.0, 0.0), 10);
        for i in 0..20 {
            let (a, b) = ((i as f32 * 2.0, 5.0), (i as f32 * 2.0 + 2.0, 5.0));
            v.extend([a, b, a, b]);
        }
        let r = report(&sim_of(&pts(&v)));
        assert!(!has(&r, "coincident stitches"), "{:?}", r.issues);
    }

    #[test]
    fn pile_up_found_across_a_grid_line() {
        // 8 penetrations 0.03 mm apart either side of the 0.2 mm cell boundary at 0.2
        let mut v = line((-30.0, 0.0), 10);
        for i in 0..8 {
            let x = if i % 2 == 0 { 0.19 } else { 0.21 };
            v.push((x, x));
            v.push((3.0, i as f32 * 0.5));
        }
        v.extend(line((10.0, 10.0), 10));
        let r = report(&sim_of(&pts(&v)));
        assert!(has(&r, "needle pile-up"), "{:?}", r.issues);
        // five returns stay under the limit
        let mut v = line((-30.0, 0.0), 10);
        for i in 0..5 {
            v.push((0.2, 0.2));
            v.push((3.0, i as f32 * 0.5));
        }
        v.extend(line((10.0, 10.0), 10));
        assert!(!has(&report(&sim_of(&pts(&v))), "needle pile-up"));
    }

    #[test]
    fn clump_flags_a_knot_of_one_colour() {
        let mut v = line((-30.0, 0.0), 10);
        for i in 0..60 {
            let (r, a) = ((i as f32 / 60.0).sqrt() * 0.9, i as f32 * 2.39996);
            v.push((r * a.cos(), r * a.sin()));
        }
        v.extend(line((10.0, 10.0), 10));
        let r = report(&sim_of(&pts(&v)));
        assert!(has(&r, "stitch clump"), "{:?}", r.issues);
        // a 0.4 mm fill, 3 mm stitches, rows offset: ~6 in any 1 mm circle
        let mut v = Vec::new();
        for row in 0..30 {
            let y = row as f32 * 0.4;
            let off = (row % 3) as f32;
            let xs: Vec<f32> = (0..5).map(|i| off + 3.0 * i as f32).collect();
            if row % 2 == 0 { v.extend(xs.iter().map(|&x| (x, y))) } else { v.extend(xs.iter().rev().map(|&x| (x, y))) }
        }
        let r = report(&sim_of(&pts(&v)));
        assert!(!has(&r, "stitch clump"), "{:?}", r.issues);
    }

    #[test]
    fn short_stitch_share() {
        // every third stitch 0.3 mm long, far from any cut
        let mut v = vec![(0.0f32, 0.0f32)];
        for i in 0..150 {
            let (x, y) = *v.last().unwrap();
            v.push(if i % 3 == 0 { (x + 0.3, y) } else { (x + 2.0, y) });
        }
        let r = report(&sim_of(&pts(&v)));
        assert!(has(&r, "short stitches"), "{:?}", r.issues);
        assert!(r.stats.short >= 40 && r.stats.short_share > 0.25, "{}", r.stats.short);
        let r = report(&sim_of(&pts(&line((0.0, 0.0), 150))));
        assert!(!has(&r, "short stitches"));
        assert_eq!(r.stats.short, 0);
    }

    /// A run that starts with `tie` then sews 40 normal stitches.
    fn run_with_tie(tie: &[(f32, f32)]) -> Vec<(f32, f32)> {
        let mut v = tie.to_vec();
        v.extend(line((2.0, 0.0), 40));
        v
    }

    #[test]
    fn stacked_locks() {
        let (a, b) = ((0.0, 0.0), (0.4, 0.0));
        // two a-b-a-b ties on one spot
        let r = report(&sim_of(&pts(&run_with_tie(&[a, b, a, b, a, b, a, b]))));
        assert!(has(&r, "stacked locks"), "{:?}", r.issues);
        // an a-b-a-b tie, then a triangle tie
        let r = report(&sim_of(&pts(&run_with_tie(&[a, b, a, b, (0.9, 0.5), (1.3, -0.1), b]))));
        assert!(has(&r, "stacked locks"), "{:?}", r.issues);
        // one tie is fine, and so is a bean run straight after it
        let r = report(&sim_of(&pts(&run_with_tie(&[a, b, a, b]))));
        assert!(!has(&r, "stacked locks"), "{:?}", r.issues);
        let r = report(&sim_of(&pts(&run_with_tie(&[a, b, a, b, (1.5, 0.0), b, (1.5, 0.0), (2.6, 0.0)]))));
        assert!(!has(&r, "stacked locks"), "{:?}", r.issues);
    }

    #[test]
    fn off_centre() {
        let centred = |dx: f32| -> Vec<(f32, f32)> { (0..21).map(|i| (dx - 20.0 + 2.0 * i as f32, 0.0)).collect() };
        let sev = |dx: f32| report(&sim_of(&pts(&centred(dx)))).issues.into_iter().find(|i| i.kind == "off-centre").map(|i| i.sev);
        assert_eq!(sev(0.0), None);
        assert_eq!(sev(0.5), None);
        assert_eq!(sev(5.0), Some(Severity::Warning));
        assert_eq!(sev(20.0), Some(Severity::Error));
    }

    #[test]
    fn machine_limits() {
        // 12.5 mm stitch: over Brother's 12.1 mm, inside Janome's 12.7 mm
        let s = sim_of(&pts(&[(0.0, 0.0), (12.5, 0.0), (10.0, 0.0)]));
        let too_long = |m: usize| analyze(&s, None, &PROFILES[m]).issues.iter().any(|i| i.kind == "stitch too long");
        assert!(too_long(0));
        assert!(!too_long(crate::machines::find("janome").unwrap()));
        // 130 colour blocks: past Brother's 127 changes, fine on a Tajima
        let mut p = Pattern::default();
        for c in 0..130 {
            for i in 0..3 {
                p.cmds.push(Cmd { x: i as f32, y: c as f32 * 0.5, kind: Kind::Stitch });
            }
            p.push_cmd(Kind::Color);
        }
        let s = Sim::new(&p, Machine::default());
        assert!(has(&analyze(&s, None, &PROFILES[0]), "too many colours"));
        assert!(!has(&analyze(&s, None, &PROFILES[crate::machines::find("tajima").unwrap()]), "too many colours"));
        // stitch count against a small made-up limit
        let tiny = crate::machines::Profile { max_stitches: 100, ..PROFILES[0] };
        assert!(has(&analyze(&s, None, &tiny), "too many stitches"));
        assert!(!has(&analyze(&s, None, &PROFILES[0]), "too many stitches"));
    }

    #[test]
    fn trims_per_thousand() {
        let mut v = pts(&line((0.0, 0.0), 500));
        v.push(None);
        v.extend(pts(&line((0.0, 5.0), 500)));
        let r = report(&sim_of(&v));
        assert!((r.stats.trims_per_1k - 1.0).abs() < 0.01, "{}", r.stats.trims_per_1k);
    }
}
