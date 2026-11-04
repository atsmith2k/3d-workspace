//! Readers for the machine formats: PES (+ its PEC block), PEC, DST, EXP, JEF, VP3,
//! XXX and U01.
//! Byte layouts follow pyembroidery's readers (MIT), which cadkit writes with, so a
//! file decodes here exactly as `cad stitch inspect` sees it.

use crate::palettes::{JEF, PEC};
use crate::pattern::{Kind, Pattern, Thread};
use std::path::Path;

struct R<'a> {
    b: &'a [u8],
    p: usize,
}

impl<'a> R<'a> {
    fn new(b: &'a [u8]) -> Self {
        R { b, p: 0 }
    }
    fn at(b: &'a [u8], p: usize) -> Self {
        R { b, p }
    }
    fn u8(&mut self) -> Option<u8> {
        let v = *self.b.get(self.p)?;
        self.p += 1;
        Some(v)
    }
    fn skip(&mut self, n: usize) {
        self.p += n;
    }
    fn bytes(&mut self, n: usize) -> Option<&'a [u8]> {
        let s = self.b.get(self.p..self.p + n)?;
        self.p += n;
        Some(s)
    }
    fn u16le(&mut self) -> Option<u16> {
        let s = self.bytes(2)?;
        Some(u16::from_le_bytes([s[0], s[1]]))
    }
    fn u24le(&mut self) -> Option<u32> {
        let s = self.bytes(3)?;
        Some(s[0] as u32 | (s[1] as u32) << 8 | (s[2] as u32) << 16)
    }
    fn u24be(&mut self) -> Option<u32> {
        let s = self.bytes(3)?;
        Some((s[0] as u32) << 16 | (s[1] as u32) << 8 | s[2] as u32)
    }
    fn u16be(&mut self) -> Option<u16> {
        let s = self.bytes(2)?;
        Some(u16::from_be_bytes([s[0], s[1]]))
    }
    fn u32be(&mut self) -> Option<u32> {
        let s = self.bytes(4)?;
        Some(u32::from_be_bytes([s[0], s[1], s[2], s[3]]))
    }
    fn i32be(&mut self) -> Option<i32> {
        self.u32be().map(|v| v as i32)
    }
    fn u32le(&mut self) -> Option<u32> {
        let s = self.bytes(4)?;
        Some(u32::from_le_bytes([s[0], s[1], s[2], s[3]]))
    }
    /// Length-prefixed string (PES headers).
    fn pstr(&mut self) -> Option<String> {
        let n = self.u8()? as usize;
        Some(String::from_utf8_lossy(self.bytes(n)?).into_owned())
    }
}

fn rgb(c: u32) -> [u8; 3] {
    [(c >> 16) as u8, (c >> 8) as u8, c as u8]
}

fn signed8(b: u8) -> i32 {
    b as i8 as i32
}

pub fn read(path: &Path) -> Result<Pattern, String> {
    let data = std::fs::read(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("").to_lowercase();
    let mut pat = match ext.as_str() {
        "pes" => read_pes(&data),
        "pec" => read_pec_file(&data),
        "dst" => read_dst(&data),
        "exp" => read_exp(&data),
        "jef" => read_jef(&data),
        "vp3" => read_vp3(&data),
        "xxx" => read_xxx(&data),
        "u01" => read_u01(&data),
        _ => Err(format!("unsupported format '.{ext}' (PES, PEC, DST, EXP, JEF, VP3, XXX, U01)")),
    }?;
    if pat.cmds.iter().all(|c| c.kind != Kind::Stitch) {
        return Err("no stitches in file".into());
    }
    if pat.label.is_empty() {
        pat.label = path.file_stem().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default();
    }
    Ok(pat)
}

// ---------- PES / PEC ----------

fn read_pes(b: &[u8]) -> Result<Pattern, String> {
    let mut r = R::new(b);
    let magic = String::from_utf8_lossy(r.bytes(8).ok_or("file too short")?).into_owned();
    if magic == "#PEC0001" {
        return read_pec_at(b, 8, Vec::new(), "PEC");
    }
    if !magic.starts_with("#PES") {
        return Err(format!("not a PES file (starts {magic:?})"));
    }
    let pec_at = r.u32le().ok_or("no PEC offset")? as usize;
    let version = &magic[4..];
    let chart = pes_threads(&mut r, version).unwrap_or_default();
    let v: f32 = version.parse::<f32>().unwrap_or(0.0) / 10.0;
    read_pec_at(b, pec_at, chart, &format!("PES v{v}"))
}

/// The PES v5+ thread list (exact RGB, names); empty for older versions or headers
/// with programmable fills / motifs, as in pyembroidery.
fn pes_threads(r: &mut R, version: &str) -> Option<Vec<Thread>> {
    // (skip before the image string, skip after it) per version
    let (a, b2, hoop) = match version {
        "0050" | "0055" | "0056" => (24, 24, false),
        "0060" | "0070" => (36, 24, false),
        "0080" => (38, 26, false),
        "0090" => (30, 34, true),
        "0100" => (38, 34, true),
        _ => return None,
    };
    r.skip(4);
    for _ in 0..5 {
        r.pstr()?; // name, category, author, keywords, comments
    }
    if hoop {
        r.skip(14);
        r.pstr()?;
    }
    r.skip(a);
    r.pstr()?; // image file
    r.skip(b2);
    for _ in 0..3 {
        if r.u16le()? != 0 {
            return None; // programmable fills, motifs, feather patterns
        }
    }
    let n = r.u16le()?;
    let mut out = Vec::new();
    for _ in 0..n {
        let catalog = r.pstr()?;
        let c = r.u24be()?;
        r.skip(5);
        let desc = r.pstr()?;
        let brand = r.pstr()?;
        r.pstr()?; // chart
        let name = [brand, desc, catalog]
            .into_iter()
            .filter(|s| !s.is_empty() && s != "None") // pyembroidery writes unset fields as "None"
            .collect::<Vec<_>>()
            .join(" ");
        out.push(Thread { rgb: rgb(c), name });
    }
    Some(out)
}

fn read_pec_file(b: &[u8]) -> Result<Pattern, String> {
    read_pec_at(b, 8, Vec::new(), "PEC")
}

fn pec_thread(i: u8) -> Thread {
    let (c, n) = PEC[i as usize % PEC.len()];
    Thread { rgb: rgb(c), name: format!("Brother {n}") }
}

fn read_pec_at(b: &[u8], at: usize, chart: Vec<Thread>, format: &str) -> Result<Pattern, String> {
    let mut r = R::at(b, at);
    let mut pat = Pattern { format: format.into(), ..Default::default() };
    r.skip(3); // "LA:"
    pat.label = String::from_utf8_lossy(r.bytes(16).ok_or("PEC block truncated")?).trim().to_string();
    r.skip(0xF);
    r.skip(2); // icon stride, height
    r.skip(0xC);
    let cc = r.u8().ok_or("PEC block truncated")?;
    let n_colors = cc as usize + 1;
    let idx = r.bytes(n_colors).ok_or("PEC colours truncated")?.to_vec();
    pat.threads = if !chart.is_empty() && chart.len() >= idx.len() {
        chart
    } else if !chart.is_empty() {
        // map each distinct palette index to the next chart thread
        let mut chart = chart.into_iter();
        let mut seen: Vec<(u8, Thread)> = Vec::new();
        idx.iter()
            .map(|&i| {
                if let Some((_, t)) = seen.iter().find(|(j, _)| *j == i) {
                    return t.clone();
                }
                let t = chart.next().unwrap_or_else(|| pec_thread(i));
                seen.push((i, t.clone()));
                t
            })
            .collect()
    } else {
        idx.iter().map(|&i| pec_thread(i)).collect()
    };
    r.skip(0x1D0 - cc as usize);
    let _block_end = r.u24le();
    r.skip(0x0B);
    pec_stitches(&mut r, &mut pat);
    Ok(pat)
}

fn signed12(v: u16) -> i32 {
    let v = (v & 0xFFF) as i32;
    if v > 0x7FF { v - 0x1000 } else { v }
}

fn signed7(v: u8) -> i32 {
    if v > 63 { v as i32 - 128 } else { v as i32 }
}

fn pec_stitches(r: &mut R, pat: &mut Pattern) {
    const JUMP: u8 = 0x10;
    const TRIM: u8 = 0x20;
    const LONG: u8 = 0x80;
    loop {
        let (Some(v1), Some(mut v2)) = (r.u8(), r.u8()) else { break };
        if v1 == 0xFF && v2 == 0x00 {
            break;
        }
        if v1 == 0xFE && v2 == 0xB0 {
            r.skip(1);
            pat.push_cmd(Kind::Color);
            continue;
        }
        let (mut jump, mut trim) = (false, false);
        let x = if v1 & LONG != 0 {
            trim |= v1 & TRIM != 0;
            jump |= v1 & JUMP != 0;
            let x = signed12((v1 as u16) << 8 | v2 as u16);
            let Some(n) = r.u8() else { break };
            v2 = n;
            x
        } else {
            signed7(v1)
        };
        let y = if v2 & LONG != 0 {
            trim |= v2 & TRIM != 0;
            jump |= v2 & JUMP != 0;
            let Some(v3) = r.u8() else { break };
            signed12((v2 as u16) << 8 | v3 as u16)
        } else {
            signed7(v2)
        };
        // PEC is Y down
        if jump {
            pat.push_rel(x, -y, Kind::Jump);
        } else if trim {
            pat.push_cmd(Kind::Trim);
            pat.push_rel(x, -y, Kind::Jump);
        } else {
            pat.push_rel(x, -y, Kind::Stitch);
        }
    }
    pat.push_cmd(Kind::End);
}

// ---------- DST ----------

fn bit(b: u8, n: u8) -> i32 {
    ((b >> n) & 1) as i32
}

fn read_dst(b: &[u8]) -> Result<Pattern, String> {
    if b.len() < 512 {
        return Err("DST file too short".into());
    }
    let mut pat = Pattern { format: "DST".into(), ..Default::default() };
    for line in String::from_utf8_lossy(&b[..512]).split(['\r', '\n']) {
        let line = line.trim();
        if let Some(v) = line.strip_prefix("LA:") {
            pat.label = v.trim().to_string();
        } else if let Some(v) = line.strip_prefix("TC:") {
            let f: Vec<&str> = v.split(',').map(str::trim).collect();
            if let Some(c) = f.first().and_then(|h| u32::from_str_radix(h.trim_start_matches('#'), 16).ok()) {
                pat.threads.push(Thread { rgb: rgb(c), name: f.get(1).unwrap_or(&"").to_string() });
            }
        }
    }
    if pat.threads.is_empty() {
        pat.notes.push("DST carries no thread colours: default colours shown".into());
    }
    for rec in b[512..].chunks_exact(3) {
        let (b0, b1, b2) = (rec[0], rec[1], rec[2]);
        let dx = 81 * (bit(b2, 2) - bit(b2, 3)) + 27 * (bit(b1, 2) - bit(b1, 3))
            + 9 * (bit(b0, 2) - bit(b0, 3)) + 3 * (bit(b1, 0) - bit(b1, 1)) + (bit(b0, 0) - bit(b0, 1));
        let dy = 81 * (bit(b2, 5) - bit(b2, 4)) + 27 * (bit(b1, 5) - bit(b1, 4))
            + 9 * (bit(b0, 5) - bit(b0, 4)) + 3 * (bit(b1, 7) - bit(b1, 6)) + (bit(b0, 7) - bit(b0, 6));
        if b2 & 0xF3 == 0xF3 {
            break;
        } else if b2 & 0xC3 == 0xC3 {
            pat.push_rel(dx, dy, Kind::Color);
        } else if b2 & 0x43 == 0x43 {
            pat.push_rel(dx, dy, Kind::Jump); // sequin mode toggle: treat as a move
        } else if b2 & 0x83 == 0x83 {
            pat.push_rel(dx, dy, Kind::Jump);
        } else {
            pat.push_rel(dx, dy, Kind::Stitch);
        }
    }
    pat.push_cmd(Kind::End);
    pat.trims_from_jumps(3, f32::INFINITY);
    Ok(pat)
}

// ---------- EXP ----------

fn read_exp(b: &[u8]) -> Result<Pattern, String> {
    let mut pat = Pattern { format: "EXP".into(), ..Default::default() };
    pat.notes.push("EXP carries no thread colours: default colours shown".into());
    let mut r = R::new(b);
    loop {
        let (Some(a), Some(c)) = (r.u8(), r.u8()) else { break };
        if a != 0x80 {
            pat.push_rel(signed8(a), signed8(c), Kind::Stitch);
            continue;
        }
        let (Some(x), Some(y)) = (r.u8(), r.u8()) else { break };
        let (x, y) = (signed8(x), signed8(y));
        match c {
            0x80 => pat.push_cmd(Kind::Trim),
            0x02 => pat.push_rel(x, y, Kind::Stitch),
            0x04 => pat.push_rel(x, y, Kind::Jump),
            0x01 => {
                pat.push_cmd(Kind::Color);
                if x != 0 || y != 0 {
                    pat.push_rel(x, y, Kind::Jump);
                }
            }
            _ => break,
        }
    }
    pat.push_cmd(Kind::End);
    Ok(pat)
}

// ---------- JEF ----------

fn read_jef(b: &[u8]) -> Result<Pattern, String> {
    let mut r = R::new(b);
    let mut pat = Pattern { format: "JEF".into(), ..Default::default() };
    let start = r.u32le().ok_or("JEF header truncated")? as usize;
    r.skip(20);
    let n = r.u32le().ok_or("JEF header truncated")?;
    r.skip(88);
    for _ in 0..n.min(256) {
        let i = (r.u32le().ok_or("JEF colours truncated")? as i32).unsigned_abs() as usize;
        let (c, name) = JEF[i % JEF.len()];
        pat.threads.push(Thread { rgb: rgb(c), name: format!("Janome {name}") });
    }
    let mut r = R::at(b, start);
    loop {
        let (Some(a), Some(c)) = (r.u8(), r.u8()) else { break };
        if a != 0x80 {
            pat.push_rel(signed8(a), signed8(c), Kind::Stitch);
            continue;
        }
        let (Some(x), Some(y)) = (r.u8(), r.u8()) else { break };
        match c {
            0x02 => pat.push_rel(signed8(x), signed8(y), Kind::Jump),
            0x01 => pat.push_cmd(Kind::Color),
            _ => break, // 0x10 = end
        }
    }
    pat.push_cmd(Kind::End);
    pat.trims_from_jumps(3, 3.0); // cadkit writes trims as three zero jumps
    Ok(pat)
}

// ---------- VP3 (Husqvarna Viking / Pfaff) ----------

/// VP3 strings: a 16-bit big-endian length, then the bytes.
fn vp3_str(r: &mut R) -> Option<String> {
    let n = r.u16be()? as usize;
    Some(String::from_utf8_lossy(r.bytes(n)?).into_owned())
}

fn read_vp3(b: &[u8]) -> Result<Pattern, String> {
    let bad = || "VP3 header truncated".to_string();
    let mut r = R::new(b);
    if r.bytes(6) != Some(b"%vsm%\0".as_slice()) {
        return Err("not a VP3 file".into());
    }
    let mut pat = Pattern { format: "VP3".into(), ..Default::default() };
    vp3_str(&mut r).ok_or_else(bad)?; // producer
    r.skip(7);
    vp3_str(&mut r).ok_or_else(bad)?; // comments
    r.skip(32);
    // design centre and block starts are in 0.001 mm, Y up; stitches are 0.1 mm, Y down
    let cx = r.i32be().ok_or_else(bad)? as f32 / 1000.0;
    let cy = r.i32be().ok_or_else(bad)? as f32 / 1000.0;
    r.skip(27);
    vp3_str(&mut r).ok_or_else(bad)?;
    r.skip(24);
    vp3_str(&mut r).ok_or_else(bad)?;
    let blocks = r.u16be().ok_or_else(bad)?;
    let short = || "VP3 colour block truncated".to_string();
    for i in 0..blocks {
        r.skip(3); // 00 05 00
        let dist = r.u32be().ok_or_else(short)? as usize;
        let end = r.p + dist;
        let sx = r.i32be().ok_or_else(short)? as f32 / 1000.0;
        let sy = r.i32be().ok_or_else(short)? as f32 / 1000.0;
        // each block starts at an absolute position: a move there
        let (x, y) = pat.cmds.last().map(|c| (c.x, c.y)).unwrap_or((0.0, 0.0));
        let (ax, ay) = (sx + cx, sy + cy);
        if (ax - x).abs() > 1e-4 || (ay - y).abs() > 1e-4 {
            pat.cmds.push(crate::pattern::Cmd { x: ax, y: ay, kind: Kind::Jump });
        }
        let n = r.u8().ok_or_else(short)?;
        r.skip(1); // transition
        let mut c = [0u8; 3];
        for _ in 0..n {
            c = rgb(r.u24be().ok_or_else(short)?);
            r.skip(3); // parts, length
        }
        r.skip(2); // type, weight
        let catalog = vp3_str(&mut r).ok_or_else(short)?;
        let desc = vp3_str(&mut r).ok_or_else(short)?;
        let brand = vp3_str(&mut r).ok_or_else(short)?;
        let name: Vec<String> = [brand, desc, catalog].into_iter().filter(|s| !s.is_empty() && s != "None").collect();
        pat.threads.push(Thread { rgb: c, name: name.join(" ") });
        r.skip(15 + 3); // ..., 0A F6 00
        let st = b.get(r.p..end.min(b.len())).ok_or_else(short)?;
        let mut k = 0;
        while k + 1 < st.len() {
            let (x, y) = (st[k], st[k + 1]);
            k += 2;
            if x != 0x80 {
                pat.push_rel(signed8(x), -signed8(y), Kind::Stitch);
                continue;
            }
            match y {
                // long stitch: 16-bit deltas, then an 80 02 with no known effect
                0x01 if k + 4 <= st.len() => {
                    let dx = i16::from_be_bytes([st[k], st[k + 1]]) as i32;
                    let dy = i16::from_be_bytes([st[k + 2], st[k + 3]]) as i32;
                    k += 6;
                    pat.push_rel(dx, -dy, Kind::Stitch);
                }
                0x03 => pat.push_cmd(Kind::Trim),
                _ => {}
            }
        }
        r.p = end;
        if i + 1 < blocks {
            pat.push_cmd(Kind::Color);
        }
    }
    pat.push_cmd(Kind::End);
    Ok(pat)
}

// ---------- XXX (Singer) ----------

fn read_xxx(b: &[u8]) -> Result<Pattern, String> {
    let mut pat = Pattern { format: "XXX".into(), ..Default::default() };
    let n_colors = R::at(b, 0x27).u16le().ok_or("XXX header truncated")?;
    let mut r = R::at(b, 0x100);
    loop {
        let Some(b1) = r.u8() else { break };
        if b1 == 0x7D || b1 == 0x7E {
            // long move: 16-bit little-endian deltas
            let (Some(x), Some(y)) = (r.u16le(), r.u16le()) else { break };
            pat.push_rel(x as i16 as i32, y as i16 as i32, Kind::Jump);
            continue;
        }
        let Some(b2) = r.u8() else { break };
        if b1 != 0x7F {
            pat.push_rel(signed8(b1), signed8(b2), Kind::Stitch);
            continue;
        }
        let (Some(b3), Some(b4)) = (r.u8(), r.u8()) else { break };
        let (x, y) = (signed8(b3), signed8(b4));
        match b2 {
            0x01 => pat.push_rel(x, y, Kind::Jump),
            0x03 => {
                pat.push_cmd(Kind::Trim);
                if x != 0 || y != 0 {
                    pat.push_rel(x, y, Kind::Jump);
                }
            }
            0x08 | 0x0A..=0x17 => pat.push_cmd(Kind::Color),
            _ => break, // 7F 7F / 7F 18: end
        }
    }
    pat.push_cmd(Kind::End);
    let mut t = R::at(b, r.p + 2);
    for _ in 0..n_colors {
        let Some(c) = t.u32be() else { break };
        pat.threads.push(Thread { rgb: rgb(c), name: String::new() });
    }
    Ok(pat)
}

// ---------- U01 (Barudan) ----------

fn read_u01(b: &[u8]) -> Result<Pattern, String> {
    let mut pat = Pattern { format: "U01".into(), ..Default::default() };
    pat.notes.push("U01 carries no thread colours: default colours shown".into());
    for rec in b.get(0x100..).ok_or("U01 file too short")?.chunks_exact(3) {
        let ctrl = rec[0];
        let mut dx = rec[2] as i32;
        let mut dy = rec[1] as i32;
        if ctrl & 0x20 != 0 {
            dx = -dx;
        }
        if ctrl & 0x40 != 0 {
            dy = -dy;
        }
        let moved = dx != 0 || dy != 0;
        match ctrl & 0x1F {
            0x00 | 0x02 | 0x04 => pat.push_rel(dx, dy, Kind::Stitch), // (fast / slow)
            0x01 | 0x03 | 0x05 => pat.push_rel(dx, dy, Kind::Jump),
            0x06..=0x08 => {
                pat.push_cmd(Kind::Trim); // top / bobbin trim, stop
                if moved {
                    pat.push_rel(dx, dy, Kind::Jump);
                }
            }
            0x09..=0x17 => {
                // needle change; the first one only picks the starting needle
                if pat.cmds.iter().any(|c| c.kind == Kind::Stitch) {
                    pat.push_cmd(Kind::Color);
                }
                if moved {
                    pat.push_rel(dx, dy, Kind::Jump);
                }
            }
            _ => break, // 0x18: end
        }
    }
    pat.push_cmd(Kind::End);
    Ok(pat)
}
