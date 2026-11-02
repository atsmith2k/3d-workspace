//! A stitch file as the machine sees it: absolute needle positions in mm (Y up) and
//! the command at each one, plus the thread list. Every reader produces this.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Stitch,
    Jump,
    Trim,
    Color,
    End,
}

#[derive(Clone, Copy, Debug)]
pub struct Cmd {
    pub x: f32,
    pub y: f32,
    pub kind: Kind,
}

#[derive(Clone, Debug)]
pub struct Thread {
    pub rgb: [u8; 3],
    pub name: String,
}

#[derive(Clone, Debug, Default)]
pub struct Pattern {
    pub cmds: Vec<Cmd>,
    pub threads: Vec<Thread>,
    pub format: String,
    pub label: String,
    pub notes: Vec<String>,
}

impl Pattern {
    /// Builder used by the readers: relative moves in file units (0.1 mm), Y up.
    pub fn push_rel(&mut self, dx: i32, dy: i32, kind: Kind) {
        let (x, y) = self.cmds.last().map(|c| (c.x, c.y)).unwrap_or((0.0, 0.0));
        self.cmds.push(Cmd { x: x + dx as f32 / 10.0, y: y + dy as f32 / 10.0, kind });
    }

    pub fn push_cmd(&mut self, kind: Kind) {
        let (x, y) = self.cmds.last().map(|c| (c.x, c.y)).unwrap_or((0.0, 0.0));
        self.cmds.push(Cmd { x, y, kind });
    }

    /// Thread for colour block `i`, falling back to a readable default palette.
    pub fn thread(&self, i: usize) -> Thread {
        if let Some(t) = self.threads.get(i) {
            return t.clone();
        }
        const FALLBACK: [[u8; 3]; 8] = [
            [26, 26, 26], [200, 16, 46], [31, 95, 191], [46, 139, 58],
            [255, 209, 0], [106, 61, 154], [255, 127, 30], [26, 138, 138],
        ];
        Thread { rgb: FALLBACK[i % FALLBACK.len()], name: format!("colour {}", i + 1) }
    }

    /// DST/JEF carry no trim command: a run of `n` or more consecutive jumps, or one
    /// that travels at least `dist` mm, means the machine trims there.
    pub fn trims_from_jumps(&mut self, n: usize, dist: f32) {
        let mut out = Vec::with_capacity(self.cmds.len());
        let mut i = 0;
        while i < self.cmds.len() {
            if self.cmds[i].kind == Kind::Jump {
                let mut j = i;
                while j < self.cmds.len() && self.cmds[j].kind == Kind::Jump {
                    j += 1;
                }
                let from = if i > 0 { self.cmds[i - 1] } else { self.cmds[i] };
                let to = self.cmds[j - 1];
                let far = ((to.x - from.x).powi(2) + (to.y - from.y).powi(2)).sqrt() >= dist;
                if j - i >= n || far {
                    let at = if i > 0 { self.cmds[i - 1] } else { self.cmds[i] };
                    out.push(Cmd { x: at.x, y: at.y, kind: Kind::Trim });
                }
                out.extend_from_slice(&self.cmds[i..j]);
                i = j;
            } else {
                out.push(self.cmds[i]);
                i += 1;
            }
        }
        self.cmds = out;
    }
}
