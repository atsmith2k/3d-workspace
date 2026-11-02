//! Problem finder: walks the timeline and flags what goes wrong on a real machine.
//!
//!   long stitch      > 7 mm snags (warning), > 12.1 mm is past most machines' limit (error)
//!   tiny stitches    3+ stitches in a row under 0.3 mm away from a cut (the needle
//!                    hammering one spot): thread breaks, bird nests. Lock stitches next
//!                    to a trim, and lone short stitches at row ends, are normal.
//!   needle pile-up   8+ penetrations in one 0.2 mm spot: holes in the fabric, thread shreds
//!   too dense        over 3.5 thread layers (fill ~1, satin ~1.7): puckering, needle
//!                    breaks; over 5 is an error
//!   untrimmed jump   thread carried over 3 mm without a trim: snip by hand or it shows
//!   no tie-in/off    a run that starts or ends at a cut without lock stitches unravels
//!   hoop             the design is bigger than the chosen hoop's sewing field
//!
//! Issues of one kind close together are grouped into one marker. Positions are in the
//! file's mm (Y up), `k` is the stitch index the timeline jumps to.

use crate::sim::Sim;
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
}

pub const LONG_WARN: f32 = 7.0;
pub const LONG_MAX: f32 = 12.1;
pub const SHORT: f32 = 0.3;
pub const DENSE: f32 = 3.5;
pub const VERY_DENSE: f32 = 5.0;
pub const JUMP: f32 = 3.0;
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

pub fn analyze(sim: &Sim, hoop: Option<(&str, f32, f32)>) -> Report {
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
        issues.push(if v > LONG_MAX {
            Issue {
                kind: "stitch too long", sev: Severity::Error, at, k,
                detail: format!("{n} stitch{} over 7 mm, up to {v:.1} mm (machine limit ~12 mm)", plural(n)),
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

    // needle pile-ups: penetrations sharing one 0.2 mm cell
    let mut holes: HashMap<(i32, i32), (usize, usize)> = HashMap::new();
    for (i, s) in segs.iter().enumerate() {
        let key = ((s.b[0] / 0.2).floor() as i32, (s.b[1] / 0.2).floor() as i32);
        let e = holes.entry(key).or_insert((0, i + 1));
        e.0 += 1;
    }
    let mut pile = Groups::new(3.0);
    for (&(x, y), &(n, k)) in &holes {
        if n >= 8 {
            pile.add([(x as f32 + 0.5) * 0.2, (y as f32 + 0.5) * 0.2], k, n as f32);
        }
    }
    for (at, k, n, v) in pile.regions() {
        issues.push(Issue {
            kind: "needle pile-up", sev: Severity::Warning, at, k,
            detail: if n == 1 {
                format!("{} needle penetrations in one 0.2 mm spot", v as usize)
            } else {
                format!("{n} spots with up to {} penetrations in 0.2 mm", v as usize)
            },
            fix: "cuts a hole and shreds thread: use short stitches at corners, spread the pivot, avoid restarting on the same point",
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
    issues.sort_by(|a, b| a.sev.cmp(&b.sev).then(a.k.cmp(&b.k)));
    Report { issues, density: dens }
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
        lb < 1.2 && va[0] * vb[0] + va[1] * vb[1] < 0.0
    })
}
