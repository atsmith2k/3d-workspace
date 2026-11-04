//! Garments to stage a design on: a flat-lay t-shirt, jeans, a baseball cap front and a
//! tote bag, at real size in mm (Y up, origin near the garment centre).
//!
//! Each garment is drawn once into an image on the CPU (parts filled in order, soft
//! pillow shading toward the edges, folds and grain from `drape`, seam grooves,
//! topstitching, rivets, a drop shadow) and shown as one textured quad; the cap is ray
//! cast three-quarter on by `drape::raster_cap`. A small repeating
//! fabric tile (jersey knit, denim twill, cap twill, canvas) is laid over the garment
//! outline as a mesh, so the weave stays crisp when zoomed in on the embroidery.

use eframe::egui::{Color32, ColorImage};

use crate::drape;

type P = [f32; 2];

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Article {
    Plain,
    TShirt,
    Pants,
    Cap,
    Tote,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Fabric {
    Plain,
    Jersey,
    Denim,
    Twill,
    Canvas,
}

impl Article {
    pub const ALL: [Article; 5] = [Article::Plain, Article::TShirt, Article::Pants, Article::Cap, Article::Tote];

    pub fn name(self) -> &'static str {
        match self {
            Article::Plain => "Plain background",
            Article::TShirt => "T-shirt",
            Article::Pants => "Jeans",
            Article::Cap => "Baseball cap",
            Article::Tote => "Tote bag",
        }
    }

    pub fn default_color(self) -> Color32 {
        match self {
            Article::Plain => Color32::from_rgb(238, 233, 222),
            Article::TShirt => Color32::from_rgb(214, 214, 210),
            Article::Pants => Color32::from_rgb(52, 78, 120),
            Article::Cap => Color32::from_rgb(36, 46, 66),
            Article::Tote => Color32::from_rgb(232, 220, 196),
        }
    }

    pub fn fabric(self) -> Fabric {
        match self {
            Article::Plain => Fabric::Plain,
            Article::TShirt => Fabric::Jersey,
            Article::Pants => Fabric::Denim,
            Article::Cap => Fabric::Twill,
            Article::Tote => Fabric::Canvas,
        }
    }

    /// Where a design usually goes: (centre x, centre y, width mm, label).
    pub fn placement(self) -> (f32, f32, f32, &'static str) {
        match self {
            Article::Plain => (0.0, 0.0, 0.0, "as designed"),
            Article::TShirt => (118.0, 190.0, 90.0, "left chest"),
            Article::Pants => (-112.0, 40.0, 80.0, "right thigh"),
            Article::Cap => (0.0, 50.0, 100.0, "front centre"),
            Article::Tote => (0.0, -10.0, 180.0, "front centre"),
        }
    }
}

pub struct Part {
    pub poly: Vec<P>,
    shade: f32,
    rib: bool,
}

pub struct Spec {
    pub article: Article,
    pub parts: Vec<Part>,
    grooves: Vec<Vec<P>>,
    topstitch: Vec<Vec<P>>,
    thread: Option<[u8; 3]>, // topstitch colour (None: tone on tone)
    discs: Vec<(P, f32, [u8; 3])>,
    pub bounds: [f32; 4],
}

// ---------- geometry helpers ----------

/// Catmull-Rom through control points, `k` points per span.
fn smooth(pts: &[P], k: usize) -> Vec<P> {
    if pts.len() < 3 {
        return pts.to_vec();
    }
    let mut out = Vec::new();
    for i in 0..pts.len() - 1 {
        let p0 = pts[i.saturating_sub(1)];
        let (p1, p2) = (pts[i], pts[i + 1]);
        let p3 = pts[(i + 2).min(pts.len() - 1)];
        for s in 0..k {
            let t = s as f32 / k as f32;
            let (t2, t3) = (t * t, t * t * t);
            let f = |a: f32, b: f32, c: f32, d: f32| {
                0.5 * (2.0 * b + (-a + c) * t + (2.0 * a - 5.0 * b + 4.0 * c - d) * t2 + (-a + 3.0 * b - 3.0 * c + d) * t3)
            };
            out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
        }
    }
    out.push(*pts.last().unwrap());
    out
}

fn mx(p: &[P]) -> Vec<P> {
    p.iter().map(|q| [-q[0], q[1]]).collect()
}

/// A right half (from the top centre round to the bottom centre) mirrored into a
/// closed outline.
fn mirrored(half: &[P]) -> Vec<P> {
    let mut out = half.to_vec();
    let mut left = mx(half);
    left.reverse();
    out.extend(left.into_iter().skip(1).take(half.len().saturating_sub(2)));
    out
}

/// Band of width `w` around a centreline, as a polygon.
fn band(c: &[P], w: f32) -> Vec<P> {
    let n = c.len();
    let mut l = Vec::with_capacity(n);
    let mut r = Vec::with_capacity(n);
    for i in 0..n {
        let a = c[i.saturating_sub(1)];
        let b = c[(i + 1).min(n - 1)];
        let (dx, dy) = (b[0] - a[0], b[1] - a[1]);
        let len = (dx * dx + dy * dy).sqrt().max(1e-6);
        let nn = [-dy / len * w / 2.0, dx / len * w / 2.0];
        l.push([c[i][0] + nn[0], c[i][1] + nn[1]]);
        r.push([c[i][0] - nn[0], c[i][1] - nn[1]]);
    }
    r.reverse();
    l.extend(r);
    l
}

/// Polyline offset by `d` to its left.
fn offset(c: &[P], d: f32) -> Vec<P> {
    let n = c.len();
    (0..n)
        .map(|i| {
            let a = c[i.saturating_sub(1)];
            let b = c[(i + 1).min(n - 1)];
            let (dx, dy) = (b[0] - a[0], b[1] - a[1]);
            let len = (dx * dx + dy * dy).sqrt().max(1e-6);
            [c[i][0] - dy / len * d, c[i][1] + dx / len * d]
        })
        .collect()
}


fn rect(x0: f32, y0: f32, x1: f32, y1: f32) -> Vec<P> {
    vec![[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
}

fn part(poly: Vec<P>, shade: f32) -> Part {
    Part { poly, shade, rib: false }
}

// ---------- the garments ----------

pub fn spec(a: Article) -> Spec {
    let mut s = Spec { article: a, parts: vec![], grooves: vec![], topstitch: vec![], thread: None, discs: vec![], bounds: [0.0; 4] };
    match a {
        Article::Plain => {}
        Article::TShirt => {
            let neck_front = smooth(&[[0.0, 292.0], [40.0, 299.0], [70.0, 318.0], [88.0, 340.0], [96.0, 360.0]], 6);
            let half: Vec<P> = neck_front
                .iter()
                .copied()
                .chain(smooth(&[[96.0, 360.0], [228.0, 332.0]], 2).into_iter().skip(1))
                .chain([[332.0, 250.0], [284.0, 190.0], [262.0, 210.0]])
                .chain(smooth(&[[262.0, 210.0], [258.0, 120.0], [262.0, -352.0]], 8).into_iter().skip(1))
                .chain([[180.0, -357.0], [90.0, -360.0], [0.0, -361.0]])
                .collect();
            s.parts.push(part(mirrored(&half), 1.0));
            // inside of the back neck, seen through the neckline
            let back = smooth(&[[96.0, 360.0], [60.0, 352.0], [0.0, 348.0]], 5);
            let mut inner: Vec<P> = back.clone();
            inner.extend(mx(&back).into_iter().rev().skip(1));
            let mut nf_full: Vec<P> = mx(&neck_front).into_iter().collect();
            nf_full.reverse();
            nf_full.extend(neck_front.iter().copied().skip(1));
            let mut poly = nf_full.clone(); // front neckline left to right, back neckline right to left
            poly.extend(inner.iter().copied().skip(1));
            s.parts.push(part(poly, 0.74));
            // rib collar
            let collar_out = smooth(&[[0.0, 274.0], [44.0, 281.0], [80.0, 302.0], [104.0, 330.0], [118.0, 359.0]], 6);
            let mut c = mx(&collar_out);
            c.reverse();
            c.extend(collar_out.iter().copied().skip(1));
            let mut top = nf_full.clone();
            top.reverse();
            c.extend(top);
            s.parts.push(Part { poly: c, shade: 0.95, rib: true });
            let mut co = mx(&collar_out);
            co.reverse();
            co.extend(collar_out.iter().copied().skip(1));
            s.topstitch.push(offset(&co, -3.0));
            for sgn in [1.0, -1.0] {
                let f = |p: P| [p[0] * sgn, p[1]];
                s.grooves.push(vec![f([118.0, 359.0]), f([228.0, 332.0])]);
                s.grooves.push(smooth(&[f([228.0, 332.0]), f([240.0, 270.0]), f([262.0, 210.0])], 6));
                s.topstitch.push(vec![f([316.0, 263.0]), f([268.0, 203.0])]);
                s.topstitch.push(vec![f([312.0, 266.0]), f([264.0, 206.0])]);
            }
            s.topstitch.push(vec![[-262.0, -336.0], [262.0, -336.0]]);
            s.topstitch.push(vec![[-262.0, -342.0], [262.0, -342.0]]);
        }
        Article::Pants => {
            s.thread = Some([214, 160, 70]);
            let outline = vec![
                [-200.0, 500.0], [200.0, 500.0], [222.0, 320.0], [224.0, 0.0], [215.0, -500.0], [18.0, -500.0],
                [6.0, 150.0], [0.0, 172.0], [-6.0, 150.0], [-18.0, -500.0], [-215.0, -500.0], [-224.0, 0.0], [-222.0, 320.0],
            ];
            s.parts.push(part(outline, 1.0));
            s.parts.push(part(vec![[-200.0, 500.0], [200.0, 500.0], [204.0, 454.0], [-204.0, 454.0]], 0.96));
            for x in [-160.0, -70.0, 70.0, 160.0] {
                s.parts.push(part(rect(x - 6.0, 436.0, x + 6.0, 506.0), 0.93));
                s.topstitch.push(vec![[x - 3.5, 440.0], [x - 3.5, 502.0]]);
                s.topstitch.push(vec![[x + 3.5, 440.0], [x + 3.5, 502.0]]);
            }
            s.topstitch.push(vec![[-200.0, 494.0], [200.0, 494.0]]);
            s.topstitch.push(vec![[-202.0, 460.0], [202.0, 460.0]]);
            s.topstitch.push(smooth(&[[34.0, 454.0], [34.0, 330.0], [26.0, 306.0], [4.0, 292.0]], 6));
            s.grooves.push(vec![[0.0, 454.0], [0.0, 172.0]]);
            for sgn in [1.0f32, -1.0] {
                let f = |p: P| [p[0] * sgn, p[1]];
                let pocket = smooth(&[f([118.0, 454.0]), f([150.0, 420.0]), f([186.0, 388.0]), f([214.0, 372.0])], 6);
                s.grooves.push(pocket.clone());
                s.topstitch.push(offset(&pocket, 5.0 * sgn));
                s.discs.push((f([121.0, 450.0]), 3.2, [176, 112, 60]));
                s.discs.push((f([213.0, 376.0]), 3.2, [176, 112, 60]));
                s.topstitch.push(vec![f([200.0, -482.0]), f([30.0, -482.0])]);
                s.grooves.push(vec![f([12.0, -500.0]), f([4.0, 160.0])]);
            }
            s.parts.push(part(rect(140.0, 400.0, 176.0, 440.0), 0.97)); // coin pocket
            s.topstitch.push(vec![[140.0, 436.0], [176.0, 436.0]]);
            s.discs.push(([0.0, 477.0], 7.0, [150, 150, 150])); // button
        }
        Article::Cap => {
            // drawn in 3D by raster_cap; only its on-screen bounds are needed here
            s.bounds = drape::cap_bounds();
            return s;
        }
        Article::Tote => {
            s.parts.push(part(rect(-190.0, -220.0, 190.0, 200.0), 1.0));
            s.parts.push(part(rect(-190.0, 168.0, 190.0, 200.0), 0.97));
            s.topstitch.push(vec![[-190.0, 172.0], [190.0, 172.0]]);
            s.topstitch.push(vec![[-190.0, 195.0], [190.0, 195.0]]);
            s.grooves.push(vec![[-190.0, -204.0], [190.0, -204.0]]);
            let strap = smooth(&[[-70.0, 150.0], [-72.0, 260.0], [-56.0, 380.0], [0.0, 440.0], [56.0, 380.0], [72.0, 260.0], [70.0, 150.0]], 8);
            s.parts.push(part(band(&strap, 30.0), 0.97));
            s.topstitch.push(offset(&strap, 11.0));
            s.topstitch.push(offset(&strap, -11.0));
            for x in [-70.0f32, 70.0] {
                let (x0, x1, y0, y1) = (x - 13.0, x + 13.0, 150.0, 176.0);
                s.topstitch.push(vec![[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0], [x1, y1]]);
                s.topstitch.push(vec![[x1, y0], [x0, y1]]);
            }
        }
    }
    let mut b = [f32::MAX, f32::MAX, f32::MIN, f32::MIN];
    for p in s.parts.iter().flat_map(|p| p.poly.iter()) {
        b = [b[0].min(p[0]), b[1].min(p[1]), b[2].max(p[0]), b[3].max(p[1])];
    }
    s.bounds = b;
    s
}


// ---------- raster ----------

pub struct Image {
    pub image: ColorImage,
    pub rect: [f32; 4], // world mm covered by the image (x0, y0, x1, y1)
}

pub const SHADOW_MM: f32 = 40.0;

pub fn raster(s: &Spec, color: Color32) -> Image {
    if s.article == Article::Cap {
        return drape::raster_cap(color);
    }
    let b = s.bounds;
    let (w_mm, h_mm) = (b[2] - b[0] + 2.0 * SHADOW_MM, b[3] - b[1] + 2.0 * SHADOW_MM);
    let ppm = (2048.0 / w_mm.max(h_mm)).min(8.0);
    let (w, h) = ((w_mm * ppm).ceil() as usize, (h_mm * ppm).ceil() as usize);
    let x0 = b[0] - SHADOW_MM;
    let y1 = b[3] + SHADOW_MM;
    let to_px = |p: P| [(p[0] - x0) * ppm, (y1 - p[1]) * ppm];
    let base = [color.r() as f32, color.g() as f32, color.b() as f32];
    let mut rgb = vec![[0.0f32; 3]; w * h];
    let mut cov = vec![0.0f32; w * h];
    for pt in &s.parts {
        let poly: Vec<P> = pt.poly.iter().map(|&p| to_px(p)).collect();
        let m = coverage(&poly, w, h);
        for i in 0..w * h {
            if m[i] <= 0.0 {
                continue;
            }
            let mut k = pt.shade;
            if pt.rib {
                let (x, y) = ((i % w) as f32 / ppm + x0, y1 - (i / w) as f32 / ppm);
                let ang = (y - 362.0).atan2(x);
                k *= 0.95 + 0.05 * (ang * 140.0).sin();
            }
            let c = [base[0] * k, base[1] * k, base[2] * k];
            for ch in 0..3 {
                rgb[i][ch] = rgb[i][ch] * (1.0 - m[i]) + c[ch] * m[i];
            }
            cov[i] = cov[i].max(m[i]);
        }
        // each part's own edge reads as a seam
        if !std::ptr::eq(pt, &s.parts[0]) {
            let mut ring = pt.poly.clone();
            ring.push(pt.poly[0]);
            stamp_line(&mut rgb, w, h, &ring.iter().map(|&p| to_px(p)).collect::<Vec<_>>(), 0.55 * ppm, 0.80, None, None);
        }
    }
    // pillow shading toward the outline, light from the upper left, soft folds
    let dist = chamfer(&cov, w, h);
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            if cov[i] <= 0.0 {
                continue;
            }
            let (mxm, mym) = (x as f32 / ppm + x0, y1 - y as f32 / ppm);
            let d = dist[i] / ppm;
            let edge = 1.0 - 0.30 * (-d / 7.0).exp();
            let k = edge * drape::light(s.article, [mxm, mym]) * drape::grain(s.article.fabric(), mxm, mym);
            for ch in 0..3 {
                rgb[i][ch] *= k;
            }
        }
    }
    for g in &s.grooves {
        let px: Vec<P> = g.iter().map(|&p| to_px(p)).collect();
        stamp_line(&mut rgb, w, h, &px, 0.6 * ppm, 0.78, None, None);
    }
    for t in &s.topstitch {
        let px: Vec<P> = t.iter().map(|&p| to_px(p)).collect();
        stamp_line(&mut rgb, w, h, &px, 0.42 * ppm, 0.82, s.thread, Some((2.6 * ppm, 3.4 * ppm)));
    }
    for (c, r, col) in &s.discs {
        let p = to_px(*c);
        let rr = r * ppm;
        let fill = if *col == [0, 0, 0] { [base[0] * 0.92, base[1] * 0.92, base[2] * 0.92] } else { [col[0] as f32, col[1] as f32, col[2] as f32] };
        let (xa, xb) = ((p[0] - rr - 2.0).max(0.0) as usize, ((p[0] + rr + 2.0) as usize).min(w - 1));
        let (ya, yb) = ((p[1] - rr - 2.0).max(0.0) as usize, ((p[1] + rr + 2.0) as usize).min(h - 1));
        for y in ya..=yb {
            for x in xa..=xb {
                let d = ((x as f32 + 0.5 - p[0]).powi(2) + (y as f32 + 0.5 - p[1]).powi(2)).sqrt();
                let a = (rr + 0.5 - d).clamp(0.0, 1.0);
                if a > 0.0 {
                    let i = y * w + x;
                    // a domed disc: lit upper left, a dark rim
                    let lx = (x as f32 - p[0]) / rr;
                    let ly = (y as f32 - p[1]) / rr;
                    let k = (1.0 - 0.25 * (lx + ly)).clamp(0.6, 1.25) * if d > rr * 0.75 { 0.75 } else { 1.0 };
                    for ch in 0..3 {
                        rgb[i][ch] = rgb[i][ch] * (1.0 - a) + (fill[ch] * k).min(255.0) * a;
                    }
                }
            }
        }
    }
    // drop shadow from a blurred, offset copy of the coverage
    let mut sh = cov.clone();
    let r = (5.0 * ppm) as usize;
    for _ in 0..2 {
        box_blur(&mut sh, w, h, r.max(1));
    }
    let (ox, oy) = ((3.0 * ppm) as isize, (5.0 * ppm) as isize);
    let mut out = Vec::with_capacity(w * h * 4);
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            let (sx, sy) = (x as isize - ox, y as isize - oy);
            let s_a = if sx >= 0 && sy >= 0 && (sx as usize) < w && (sy as usize) < h { sh[sy as usize * w + sx as usize] } else { 0.0 };
            let c = cov[i];
            let shadow = s_a * 0.32 * (1.0 - c);
            let a = c + shadow;
            let col = if a > 0.0 { [rgb[i][0] * c / a, rgb[i][1] * c / a, rgb[i][2] * c / a] } else { [0.0; 3] };
            out.extend_from_slice(&[col[0].min(255.0) as u8, col[1].min(255.0) as u8, col[2].min(255.0) as u8, (a.min(1.0) * 255.0) as u8]);
        }
    }
    Image {
        image: ColorImage::from_rgba_unmultiplied([w, h], &out),
        rect: [x0, b[1] - SHADOW_MM, b[2] + SHADOW_MM, y1],
    }
}

/// Anti-aliased coverage of a polygon (pixel coords): 4 sub-rows, exact span ends.
fn coverage(poly: &[P], w: usize, h: usize) -> Vec<f32> {
    let mut m = vec![0.0f32; w * h];
    let (mut ya, mut yb) = (f32::MAX, f32::MIN);
    for p in poly {
        ya = ya.min(p[1]);
        yb = yb.max(p[1]);
    }
    let (ya, yb) = (ya.max(0.0) as usize, (yb.ceil() as usize).min(h));
    const SUB: usize = 4;
    let mut xs = Vec::new();
    for y in ya..yb {
        for s in 0..SUB {
            let fy = y as f32 + (s as f32 + 0.5) / SUB as f32;
            xs.clear();
            for i in 0..poly.len() {
                let (a, b) = (poly[i], poly[(i + 1) % poly.len()]);
                if (a[1] <= fy) != (b[1] <= fy) {
                    xs.push(a[0] + (fy - a[1]) / (b[1] - a[1]) * (b[0] - a[0]));
                }
            }
            xs.sort_by(|a, b| a.partial_cmp(b).unwrap());
            for pair in xs.chunks_exact(2) {
                let (l, r) = (pair[0].clamp(0.0, w as f32), pair[1].clamp(0.0, w as f32));
                if r <= l {
                    continue;
                }
                let (li, ri) = (l as usize, (r as usize).min(w - 1));
                let row = &mut m[y * w..(y + 1) * w];
                if li == ri {
                    row[li] += (r - l) / SUB as f32;
                    continue;
                }
                row[li] += (li as f32 + 1.0 - l) / SUB as f32;
                for v in &mut row[li + 1..ri] {
                    *v += 1.0 / SUB as f32;
                }
                row[ri] += (r - ri as f32) / SUB as f32;
            }
        }
    }
    for v in &mut m {
        *v = v.min(1.0);
    }
    m
}

/// Distance (px) from each covered pixel to the uncovered region (3-4 chamfer).
pub fn chamfer(cov: &[f32], w: usize, h: usize) -> Vec<f32> {
    let big = 1e9f32;
    let mut d: Vec<f32> = cov.iter().map(|&c| if c > 0.5 { big } else { 0.0 }).collect();
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            if d[i] == 0.0 {
                continue;
            }
            let mut v = d[i];
            if x > 0 { v = v.min(d[i - 1] + 1.0); }
            if y > 0 {
                v = v.min(d[i - w] + 1.0);
                if x > 0 { v = v.min(d[i - w - 1] + 1.414); }
                if x + 1 < w { v = v.min(d[i - w + 1] + 1.414); }
            }
            d[i] = v;
        }
    }
    for y in (0..h).rev() {
        for x in (0..w).rev() {
            let i = y * w + x;
            if d[i] == 0.0 {
                continue;
            }
            let mut v = d[i];
            if x + 1 < w { v = v.min(d[i + 1] + 1.0); }
            if y + 1 < h {
                v = v.min(d[i + w] + 1.0);
                if x + 1 < w { v = v.min(d[i + w + 1] + 1.414); }
                if x > 0 { v = v.min(d[i + w - 1] + 1.414); }
            }
            d[i] = v;
        }
    }
    d
}

pub fn box_blur(m: &mut [f32], w: usize, h: usize, r: usize) {
    let mut tmp = vec![0.0f32; m.len()];
    let k = 1.0 / (2 * r + 1) as f32;
    for y in 0..h {
        let row = &m[y * w..(y + 1) * w];
        let mut acc: f32 = (0..=r).map(|x| row[x.min(w - 1)]).sum::<f32>() + row[0] * r as f32;
        for x in 0..w {
            tmp[y * w + x] = acc * k;
            let add = row[(x + r + 1).min(w - 1)];
            let sub = row[x.saturating_sub(r)];
            acc += add - sub;
        }
    }
    for x in 0..w {
        let mut acc: f32 = (0..=r).map(|y| tmp[y.min(h - 1) * w + x]).sum::<f32>() + tmp[x] * r as f32;
        for y in 0..h {
            m[y * w + x] = acc * k;
            let add = tmp[(y + r + 1).min(h - 1) * w + x];
            let sub = tmp[y.saturating_sub(r) * w + x];
            acc += add - sub;
        }
    }
}

/// Stamp a soft line along a polyline: darken by `k`, or paint `color` (thread), with
/// an optional (dash, period) pattern in px.
#[allow(clippy::too_many_arguments)]
fn stamp_line(rgb: &mut [[f32; 3]], w: usize, h: usize, pts: &[P], r: f32, k: f32, color: Option<[u8; 3]>, dash: Option<(f32, f32)>) {
    let mut along = 0.0f32;
    for seg in pts.windows(2) {
        let (a, b) = (seg[0], seg[1]);
        let len = ((b[0] - a[0]).powi(2) + (b[1] - a[1]).powi(2)).sqrt();
        let steps = (len / (r * 0.5).max(0.3)).ceil().max(1.0) as usize;
        for s in 0..steps {
            let t = s as f32 / steps as f32;
            let p = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
            let pos = along + len * t;
            if let Some((on, period)) = dash {
                if pos % period > on {
                    continue;
                }
            }
            let rr = r.max(0.6);
            let (xa, xb) = ((p[0] - rr - 1.0).max(0.0) as usize, ((p[0] + rr + 1.0) as usize).min(w - 1));
            let (ya, yb) = ((p[1] - rr - 1.0).max(0.0) as usize, ((p[1] + rr + 1.0) as usize).min(h - 1));
            for y in ya..=yb {
                for x in xa..=xb {
                    let d = ((x as f32 + 0.5 - p[0]).powi(2) + (y as f32 + 0.5 - p[1]).powi(2)).sqrt();
                    let a = (rr + 0.5 - d).clamp(0.0, 1.0) * 0.5;
                    if a <= 0.0 {
                        continue;
                    }
                    let px = &mut rgb[y * w + x];
                    for ch in 0..3 {
                        let target = match color {
                            Some(c) => c[ch] as f32,
                            None => px[ch] * k,
                        };
                        px[ch] = px[ch] * (1.0 - a) + target * a;
                    }
                }
            }
        }
        along += len;
    }
}

// ---------- fabric tile ----------

/// A repeating weave tile (premultiplied white/black with alpha, laid over the
/// garment colour) and the mm it spans.
pub fn tile(f: Fabric) -> (ColorImage, f32) {
    const N: usize = 64;
    let tau = std::f32::consts::TAU;
    let mut px = Vec::with_capacity(N * N);
    let mut rng = 0x1234_5678u32;
    for y in 0..N {
        for x in 0..N {
            let (u, v) = ((x as f32 + 0.5) / N as f32, (y as f32 + 0.5) / N as f32);
            rng ^= rng << 13;
            rng ^= rng >> 17;
            rng ^= rng << 5;
            let noise = (rng & 0xFF) as f32 / 255.0 - 0.5;
            let i = match f {
                Fabric::Plain => 0.25 * noise,
                Fabric::Jersey => {
                    // two wales by two courses of V-shaped knit loops
                    let (fx, fy) = ((u * 2.0).fract(), (v * 2.0).fract());
                    let sgn = if fx < 0.5 { 1.0 } else { -1.0 };
                    let leg = (tau * (fx * 2.0 + sgn * fy * 0.9)).cos();
                    let gap = (-((fx - 0.5).abs() * 18.0).powi(2)).exp() + (-(fx.min(1.0 - fx) * 18.0).powi(2)).exp();
                    0.45 * leg - 0.5 * gap + 0.12 * noise
                }
                Fabric::Denim => 0.55 * (tau * (u * 3.0 + v * 3.0)).sin() + 0.25 * noise + 0.15 * (tau * v * 9.0).sin(),
                Fabric::Twill => 0.35 * (tau * (u * 4.0 - v * 4.0)).sin() + 0.1 * noise,
                Fabric::Canvas => 0.45 * (tau * u * 4.0).sin() * (tau * v * 4.0).cos() + 0.15 * noise,
            };
            let a = (i.abs() * 0.55).min(1.0);
            let g = if i > 0.0 { 255.0 } else { 0.0 };
            let pa = (a * 255.0) as u8;
            let pg = (g * a) as u8;
            px.push(Color32::from_rgba_premultiplied(pg, pg, pg, pa));
        }
    }
    let mm = match f {
        Fabric::Plain => 3.0,
        Fabric::Jersey => 1.6,
        Fabric::Denim => 1.5,
        Fabric::Twill => 1.0,
        Fabric::Canvas => 1.8,
    };
    (ColorImage::new([N, N], px), mm)
}

/// Ear-clipping triangulation of a simple polygon: index triples.
pub fn triangulate(poly: &[P]) -> Vec<[usize; 3]> {
    let n = poly.len();
    if n < 3 {
        return vec![];
    }
    let area: f32 = (0..n).map(|i| {
        let (a, b) = (poly[i], poly[(i + 1) % n]);
        a[0] * b[1] - b[0] * a[1]
    }).sum();
    let mut idx: Vec<usize> = if area > 0.0 { (0..n).collect() } else { (0..n).rev().collect() };
    let cross = |o: P, a: P, b: P| (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    let mut out = Vec::new();
    let mut guard = 0;
    while idx.len() > 3 && guard < n * n {
        guard += 1;
        let m = idx.len();
        let mut clipped = false;
        for i in 0..m {
            let (ia, ib, ic) = (idx[(i + m - 1) % m], idx[i], idx[(i + 1) % m]);
            let (a, b, c) = (poly[ia], poly[ib], poly[ic]);
            if cross(a, b, c) <= 0.0 {
                continue;
            }
            let inside = idx.iter().any(|&j| {
                if j == ia || j == ib || j == ic {
                    return false;
                }
                let p = poly[j];
                cross(a, b, p) > 0.0 && cross(b, c, p) > 0.0 && cross(c, a, p) > 0.0
            });
            if !inside {
                out.push([ia, ib, ic]);
                idx.remove(i);
                clipped = true;
                break;
            }
        }
        if !clipped {
            break;
        }
    }
    if idx.len() == 3 {
        out.push([idx[0], idx[1], idx[2]]);
    }
    out
}
