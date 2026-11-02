//! Realistic thread: each stitch is a textured quad. The texture (one ply-twist period
//! along the thread, the full width across) carries round-thread shading, a specular
//! streak, the twist and soft anti-aliased edges; the vertex colour carries the thread
//! colour, a direction-dependent sheen (stitches lying across the light shine, ones
//! along it go dull, which is what makes fills and satins read as embroidery), darker
//! ends where the thread dives into the fabric, and a little per-stitch variation.
//! A soft shadow quad goes under every stitch.

use eframe::egui::{self, Color32, ColorImage, Mesh, Pos2, TextureId, Vec2};

pub const TWIST_MM: f32 = 0.55; // ply twist period of 40 wt polyester

pub fn texture() -> ColorImage {
    let (w, h) = (32usize, 32usize); // u along the thread, v across
    let mut px = Vec::with_capacity(w * h);
    for y in 0..h {
        for x in 0..w {
            let u = (x as f32 + 0.5) / w as f32;
            let v = (y as f32 + 0.5) / h as f32;
            let a = (v - 0.5) * 2.0; // -1..1 across
            let cyl = (1.0 - a * a).max(0.0).sqrt();
            let spec = (-((a + 0.28) / 0.22).powi(2)).exp();
            let twist = 0.5 + 0.5 * (std::f32::consts::TAU * (u * 2.0 + v * 1.3)).sin();
            let val = (0.50 + 0.36 * cyl) * (0.86 + 0.14 * twist) + 0.22 * spec * (0.7 + 0.3 * twist);
            let alpha = ((1.0 - a.abs()) / 0.22).clamp(0.0, 1.0);
            let g = (val.clamp(0.0, 1.0) * 255.0) as u8;
            px.push(Color32::from_rgba_unmultiplied(g, g, g, (alpha * 255.0) as u8));
        }
    }
    ColorImage::new([w, h], px)
}

fn hash(i: u32) -> f32 {
    let mut x = i.wrapping_mul(0x9E37_79B9) ^ 0x85EB_CA6B;
    x ^= x >> 15;
    x = x.wrapping_mul(0x2C1B_3C6D);
    x ^= x >> 12;
    (x & 0xFFFF) as f32 / 65535.0
}

fn scale(c: Color32, k: f32) -> Color32 {
    let f = |v: u8| (v as f32 * k).clamp(0.0, 255.0) as u8;
    Color32::from_rgba_premultiplied(f(c.r()), f(c.g()), f(c.b()), c.a())
}

/// Light comes from the upper left of the screen.
const LIGHT: Vec2 = Vec2::new(-0.52, -0.85);

pub struct Real {
    pub tex: TextureId,
}

impl Real {
    pub fn mesh(&self) -> Mesh {
        Mesh::with_texture(self.tex)
    }

    /// One stitch from a to b (screen points), `w` px wide, `mm_px` px per mm (for the
    /// twist period and the shadow offset), thread colour `c`, stitch number `i`.
    pub fn push(&self, m: &mut Mesh, a: Pos2, b: Pos2, w: f32, mm_px: f32, c: Color32, i: u32) {
        let d = b - a;
        let len = d.length();
        if len < 1e-3 {
            return;
        }
        let t = d / len;
        let n = Vec2::new(-t.y, t.x);
        // shadow: wider, offset down-right, soft
        let off = Vec2::new(0.10, 0.12) * mm_px;
        let sw = w * 0.75;
        let sh = Color32::from_black_alpha(70);
        let s0 = m.vertices.len() as u32;
        for (p, v) in [(a + off + n * sw, 0.0), (a + off - n * sw, 1.0), (b + off - n * sw, 1.0), (b + off + n * sw, 0.0)] {
            m.vertices.push(egui::epaint::Vertex { pos: p, uv: Pos2::new(0.25, v), color: sh });
        }
        m.add_triangle(s0, s0 + 1, s0 + 2);
        m.add_triangle(s0, s0 + 2, s0 + 3);
        // the thread: 4 rows along it (ends darker), 2 columns across
        let k = t.dot(LIGHT).abs();
        let sheen = 0.84 + 0.20 * (1.0 - k * k) + (hash(i) - 0.5) * 0.06;
        let lit = scale(lighten(c), sheen);
        let end = scale(lit, 0.72);
        let e = (0.22 * mm_px).min(len * 0.3);
        let u_len = len / (TWIST_MM * mm_px);
        let u0 = hash(i ^ 0x5bd1) * 4.0;
        let h = w * 0.5;
        let i0 = m.vertices.len() as u32;
        for (s, col) in [(0.0, end), (e, lit), (len - e, lit), (len, end)] {
            let p = a + t * s;
            let u = u0 + u_len * s / len;
            m.vertices.push(egui::epaint::Vertex { pos: p + n * h, uv: Pos2::new(u, 0.0), color: col });
            m.vertices.push(egui::epaint::Vertex { pos: p - n * h, uv: Pos2::new(u, 1.0), color: col });
        }
        for r in 0..3 {
            let q = i0 + r * 2;
            m.add_triangle(q, q + 1, q + 3);
            m.add_triangle(q, q + 3, q + 2);
        }
    }
}

/// The texture's mid-tone is ~0.75, so the tint is lifted to keep the thread's colour
/// in the body of the thread and leave room for the highlight.
fn lighten(c: Color32) -> Color32 {
    // divide out the texture's average brightness (~0.8), scaling all three channels
    // together so the hue and saturation stay the thread's own
    let k = (1.0 / 0.8f32).min(255.0 / c.r().max(c.g()).max(c.b()).max(1) as f32);
    let f = |v: u8| (v as f32 * k).min(255.0) as u8;
    Color32::from_rgb(f(c.r()), f(c.g()), f(c.b()))
}
