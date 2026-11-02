//! The sewing timeline: every sewn stitch in order, the jumps, trims and colour changes
//! between them, and how long the machine takes to get to each one.
//!
//! Position `k` on the timeline means the first `k` stitches are sewn. Thread is drawn
//! as one quad per stitch, shaded across its width like a round thread, and built in
//! chunks so a frame during playback only rebuilds the chunk being sewn.

use crate::pattern::{Kind, Pattern};

#[derive(Clone, Copy)]
pub struct Seg {
    pub a: [f32; 2],
    pub b: [f32; 2],
    pub block: u16,
}

#[derive(Clone, Copy)]
pub struct Jump {
    pub a: [f32; 2],
    pub b: [f32; 2],
    pub trimmed: bool,
    pub color_change: bool,
    /// stitches sewn before this jump
    pub after: usize,
}

/// Machine model for the time estimate (matches `cad stitch`).
#[derive(Clone, Copy)]
pub struct Machine {
    pub spm: f32,
    pub trim_s: f32,
    pub color_s: f32,
}

impl Default for Machine {
    fn default() -> Self {
        Machine { spm: 650.0, trim_s: 8.0, color_s: 30.0 }
    }
}

pub struct Sim {
    pub segs: Vec<Seg>,
    pub jumps: Vec<Jump>,
    /// first stitch index of each colour block
    pub block_start: Vec<usize>,
    pub block_count: Vec<usize>,
    /// seconds from the start to stitch k (len segs + 1)
    pub time: Vec<f32>,
    pub bounds: [f32; 4],
    pub penetrations: usize,
    pub trims: usize,
    pub thread_m: f32,
    pub longest: f32,
    pub start: [f32; 2],
}

impl Sim {
    pub fn new(p: &Pattern, m: Machine) -> Sim {
        let mut segs = Vec::new();
        let mut jumps = Vec::new();
        let mut block: u16 = 0;
        let mut block_start = vec![0usize];
        let mut prev: Option<[f32; 2]> = None; // last penetration
        let mut sewing = false; // previous command was a stitch we can sew from
        let mut trimmed = false;
        let mut color_change = false;
        let mut pens = 0usize;
        let mut bounds = [f32::MAX, f32::MAX, f32::MIN, f32::MIN];
        let mut start = None;
        for c in &p.cmds {
            let pt = [c.x, c.y];
            match c.kind {
                Kind::Stitch => {
                    pens += 1;
                    bounds = [bounds[0].min(c.x), bounds[1].min(c.y), bounds[2].max(c.x), bounds[3].max(c.y)];
                    start.get_or_insert(pt);
                    if let Some(a) = prev {
                        let moved = (a[0] - pt[0]).abs() + (a[1] - pt[1]).abs() > 1e-4;
                        if sewing {
                            if moved {
                                segs.push(Seg { a, b: pt, block });
                            }
                        } else if moved || trimmed || color_change {
                            jumps.push(Jump { a, b: pt, trimmed, color_change, after: segs.len() });
                        }
                    }
                    if color_change && block_start.len() <= block as usize {
                        block_start.push(segs.len());
                    }
                    prev = Some(pt);
                    sewing = true;
                    trimmed = false;
                    color_change = false;
                }
                Kind::Jump => sewing = false,
                Kind::Trim => {
                    trimmed = true;
                    sewing = false;
                }
                Kind::Color => {
                    if pens > 0 && !color_change {
                        block += 1;
                        color_change = true;
                    }
                    sewing = false;
                }
                Kind::End => break,
            }
        }
        // stop colour changes with no stitches after them from adding empty blocks
        block_start.truncate(block as usize + 1);
        let n_blocks = block_start.len();
        let mut block_count = vec![0usize; n_blocks];
        for s in &segs {
            if let Some(c) = block_count.get_mut(s.block as usize) {
                *c += 1;
            }
        }
        let per = 60.0 / m.spm;
        let mut time = Vec::with_capacity(segs.len() + 1);
        time.push(0.0);
        let mut t = 0.0f32;
        let mut j = 0;
        let mut longest = 0.0f32;
        let mut sewn = 0.0f32;
        for (i, s) in segs.iter().enumerate() {
            while j < jumps.len() && jumps[j].after == i {
                if jumps[j].color_change {
                    t += m.color_s;
                } else if jumps[j].trimmed {
                    t += m.trim_s;
                }
                t += per;
                j += 1;
            }
            let l = ((s.b[0] - s.a[0]).powi(2) + (s.b[1] - s.a[1]).powi(2)).sqrt();
            longest = longest.max(l);
            sewn += l;
            t += per;
            time.push(t);
        }
        // a trim before a colour change is part of the change, not a separate trim
        let trims = jumps.iter().filter(|j| j.trimmed && !j.color_change).count();
        Sim {
            thread_m: (sewn + 0.4 * pens as f32) / 1000.0,
            segs,
            jumps,
            block_start,
            block_count,
            time,
            bounds,
            penetrations: pens,
            trims,
            longest,
            start: start.unwrap_or([0.0, 0.0]),
        }
    }

    pub fn len(&self) -> usize {
        self.segs.len()
    }

    pub fn block_at(&self, k: usize) -> usize {
        match self.block_start.binary_search(&k) {
            Ok(i) => {
                // several blocks can start at k only if empty; take the last
                let mut i = i;
                while i + 1 < self.block_start.len() && self.block_start[i + 1] == k {
                    i += 1;
                }
                i
            }
            Err(i) => i.saturating_sub(1),
        }
    }

    /// Needle position after k stitches.
    pub fn needle(&self, k: usize) -> [f32; 2] {
        if k == 0 {
            self.segs.first().map(|s| s.a).unwrap_or(self.start)
        } else {
            self.segs[(k - 1).min(self.segs.len() - 1)].b
        }
    }

    /// Stitch index reached at time `t` seconds.
    pub fn at_time(&self, t: f32) -> usize {
        match self.time.binary_search_by(|v| v.partial_cmp(&t).unwrap()) {
            Ok(i) => i,
            Err(i) => i.saturating_sub(1),
        }
    }

    pub fn total_time(&self) -> f32 {
        *self.time.last().unwrap_or(&0.0)
    }

    pub fn size(&self) -> (f32, f32) {
        (self.bounds[2] - self.bounds[0], self.bounds[3] - self.bounds[1])
    }
}

pub fn fmt_time(s: f32) -> String {
    let s = s.max(0.0) as u32;
    if s >= 3600 {
        format!("{}:{:02}:{:02}", s / 3600, s / 60 % 60, s % 60)
    } else {
        format!("{}:{:02}", s / 60, s % 60)
    }
}
