//! Realism for the staged garments: folds lit from the upper left, the fabric's grain
//! at garment scale, a structured cap seen three-quarter on (ray cast in 3D, with the
//! design wrapped round its crown), and the puckering stitching pulls into fabric.

use eframe::egui::{Color32, ColorImage};

use crate::garment::{box_blur, chamfer, Article, Fabric, Image, SHADOW_MM};

type P = [f32; 2];
type V = [f32; 3];

// ---------- folds, light and grain on flat-laid garments ----------

/// A soft fold: a ridge (amp > 0) or valley along a segment, `w` mm wide, `amp` mm high.
struct Fold {
    a: P,
    b: P,
    w: f32,
    amp: f32,
}

const fn fold(a: P, b: P, w: f32, amp: f32) -> Fold {
    Fold { a, b, w, amp }
}

/// Where a flat-laid garment rises and sinks: long drapes from the shoulders and
/// armpits, ripples along the hem, creases in the sleeves.
fn folds(a: Article) -> &'static [Fold] {
    static TEE: [Fold; 12] = [
        fold([232.0, 205.0], [118.0, 30.0], 30.0, 2.6),
        fold([-232.0, 205.0], [-104.0, 52.0], 26.0, 2.2),
        fold([40.0, 120.0], [70.0, -345.0], 46.0, 2.2),
        fold([-120.0, 110.0], [-168.0, -345.0], 52.0, -2.6),
        fold([196.0, -30.0], [214.0, -345.0], 34.0, 1.9),
        fold([-36.0, -120.0], [-20.0, -345.0], 22.0, 1.4),
        fold([-232.0, -292.0], [-70.0, -328.0], 18.0, 1.6),
        fold([30.0, -286.0], [170.0, -324.0], 20.0, -1.3),
        fold([300.0, 262.0], [252.0, 216.0], 10.0, 1.3),
        fold([-302.0, 258.0], [-258.0, 214.0], 11.0, -1.2),
        fold([276.0, 300.0], [226.0, 258.0], 14.0, 1.0),
        fold([-60.0, 268.0], [60.0, 266.0], 26.0, -1.0),
    ];
    static PANTS: [Fold; 6] = [
        fold([-150.0, 150.0], [-120.0, -480.0], 30.0, 2.0),
        fold([110.0, 120.0], [150.0, -480.0], 34.0, -2.0),
        fold([-210.0, -120.0], [-40.0, -150.0], 14.0, 1.6),
        fold([40.0, -160.0], [205.0, -130.0], 14.0, 1.6),
        fold([-200.0, -330.0], [-40.0, -350.0], 12.0, 1.4),
        fold([40.0, -340.0], [200.0, -320.0], 12.0, -1.2),
    ];
    static TOTE: [Fold; 5] = [
        fold([-150.0, 160.0], [-120.0, -210.0], 40.0, 2.2),
        fold([140.0, 150.0], [170.0, -210.0], 36.0, -2.0),
        fold([-185.0, -170.0], [-60.0, -205.0], 20.0, 1.5),
        fold([60.0, -200.0], [185.0, -175.0], 18.0, -1.4),
        fold([-40.0, 120.0], [30.0, 60.0], 30.0, 1.0),
    ];
    match a {
        Article::TShirt => &TEE,
        Article::Pants => &PANTS,
        Article::Tote => &TOTE,
        _ => &[],
    }
}

fn fold_height(fs: &[Fold], p: P) -> f32 {
    let mut h = 0.0;
    for f in fs {
        let (dx, dy) = (f.b[0] - f.a[0], f.b[1] - f.a[1]);
        let l2 = (dx * dx + dy * dy).max(1e-6);
        // across: distance from the fold's line; along: a smooth fade in and out over
        // its first and last quarter (a clamped or square-root fade creases the light)
        let t = ((p[0] - f.a[0]) * dx + (p[1] - f.a[1]) * dy) / l2;
        if !(0.0..=1.0).contains(&t) {
            continue;
        }
        let (ex, ey) = (p[0] - f.a[0] - t * dx, p[1] - f.a[1] - t * dy);
        let ss = |e: f32| {
            let e = e.clamp(0.0, 1.0);
            e * e * (3.0 - 2.0 * e)
        };
        let taper = ss(t / 0.3) * ss((1.0 - t) / 0.3);
        let w = f.w * 0.7;
        h += f.amp * taper * (-(ex * ex + ey * ey) / (w * w)).exp();
    }
    h
}

/// Light from the upper left, a little above the table.
const LIGHT_2D: V = [-0.45, 0.62, 0.64];

/// Brightness of the fabric at a garment point (mm): a soft gradient across the
/// garment, the folds lit from the upper left, valleys a touch darker. Stitches sewn
/// there take the same light, so the design sits in the garment's folds.
pub fn light(a: Article, p: P) -> f32 {
    match a {
        Article::Plain => 1.0,
        Article::Cap => cap_light(p),
        _ => {
            let fs = folds(a);
            let e = 0.6;
            let hx = (fold_height(fs, [p[0] + e, p[1]]) - fold_height(fs, [p[0] - e, p[1]])) / (2.0 * e);
            let hy = (fold_height(fs, [p[0], p[1] + e]) - fold_height(fs, [p[0], p[1] - e])) / (2.0 * e);
            let h = fold_height(fs, p);
            let [lx, ly, lz] = LIGHT_2D;
            let n = (hx * hx + hy * hy + 1.0).sqrt();
            let lambert = (-hx * lx - hy * ly + lz) / (n * lz);
            let grad = 1.0 + 0.00012 * (p[1] - 0.6 * p[0]);
            (lambert.clamp(0.7, 1.25) * (1.0 + 0.018 * h.min(0.0)) * grad).clamp(0.6, 1.3)
        }
    }
}

/// Where a design point (garment mm) appears: on the cap it wraps round the crown and
/// is seen three-quarter on; flat-laid garments show it where it is.
pub fn warp(a: Article, p: P) -> P {
    if a == Article::Cap {
        let s = view(cap_point(p));
        return [s[0], s[1]];
    }
    p
}

fn hash2(x: i32, y: i32, seed: u32) -> f32 {
    let mut h = (x as u32).wrapping_mul(0x8da6_b343) ^ (y as u32).wrapping_mul(0xd816_3841) ^ seed.wrapping_mul(0xcb1a_b31f);
    h ^= h >> 13;
    h = h.wrapping_mul(0x5bd1_e995);
    h ^= h >> 15;
    (h & 0xFFFF) as f32 / 65535.0
}

/// Smooth value noise in [-0.5, 0.5], cells `sx` by `sy` mm.
fn vnoise(x: f32, y: f32, sx: f32, sy: f32, seed: u32) -> f32 {
    let (u, v) = (x / sx, y / sy);
    let (ix, iy) = (u.floor() as i32, v.floor() as i32);
    let (fx, fy) = (u - ix as f32, v - iy as f32);
    let (fx, fy) = (fx * fx * (3.0 - 2.0 * fx), fy * fy * (3.0 - 2.0 * fy));
    let a = hash2(ix, iy, seed) + (hash2(ix + 1, iy, seed) - hash2(ix, iy, seed)) * fx;
    let b = hash2(ix, iy + 1, seed) + (hash2(ix + 1, iy + 1, seed) - hash2(ix, iy + 1, seed)) * fx;
    a + (b - a) * fy - 0.5
}

/// The fabric's grain as it reads at garment scale (a brightness factor): a jersey's
/// wales and heathered yarn, denim's slubby diagonal, twill ridges, canvas's basket.
pub fn grain(f: Fabric, x: f32, y: f32) -> f32 {
    let tau = std::f32::consts::TAU;
    let mottle = vnoise(x, y, 9.0, 9.0, 7) * 0.012 + vnoise(x, y, 31.0, 31.0, 8) * 0.018;
    let g = match f {
        Fabric::Plain => 0.0,
        Fabric::Jersey => vnoise(x, y, 0.45, 2.4, 1) * 0.045 + vnoise(x, y, 0.9, 6.0, 2) * 0.025 + 0.015 * (tau * x / 0.8).sin(),
        Fabric::Denim => 0.06 * (tau * (x + y) / 1.4).sin() + vnoise(x, y, 0.5, 5.0, 3) * 0.12,
        Fabric::Twill => 0.05 * (tau * (x - y) / 1.1).sin() + vnoise(x, y, 0.6, 0.6, 4) * 0.04,
        Fabric::Canvas => 0.04 * (tau * x / 1.0).sin() * (tau * y / 1.0).cos() + vnoise(x, y, 0.8, 0.8, 5) * 0.06,
    };
    1.0 + g + mottle
}

// ---------- the cap: a structured six-panel cap, three-quarter on, in 3D ----------
//
// Cap space: x right, y up, z out of the front, origin at the centre of the crown's
// base (mm). The crown is half an ellipsoid; the brim a curved plate in front of it.

const CROWN: V = [96.0, 116.0, 100.0]; // half width, height, half depth
const BRIM_A: f32 = 96.0; // outer edge: half width (it meets the crown at the sides)
const BRIM_C: f32 = 176.0; // outer edge: reach from the crown's centre
const BRIM_T: f32 = 3.2; // thickness
const YAW: f32 = 32.0; // degrees: the front turns to the viewer's left
const PITCH: f32 = 17.0; // degrees: seen from a little above
const CAP_LIGHT: V = [-0.42, 0.62, 0.66]; // view space

fn dot(a: V, b: V) -> f32 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

fn norm(a: V) -> V {
    let l = dot(a, a).sqrt().max(1e-9);
    [a[0] / l, a[1] / l, a[2] / l]
}

/// Cap space to view space (x right, y up, z toward the viewer).
fn view(p: V) -> V {
    let (sy, cy) = (-YAW).to_radians().sin_cos();
    let (sp, cp) = PITCH.to_radians().sin_cos();
    let (x, z) = (p[0] * cy + p[2] * sy, -p[0] * sy + p[2] * cy);
    let (y, z) = (p[1] * cp - z * sp, p[1] * sp + z * cp);
    [x, y, z]
}

/// View space back to cap space.
fn unview(p: V) -> V {
    let (sy, cy) = (-YAW).to_radians().sin_cos();
    let (sp, cp) = PITCH.to_radians().sin_cos();
    let (y, z) = (p[1] * cp + p[2] * sp, -p[1] * sp + p[2] * cp);
    let (x, z) = (p[0] * cy - z * sy, p[0] * sy + z * cy);
    [x, y, z]
}

fn crown_normal(p: V) -> V {
    let [a, h, c] = CROWN;
    norm([p[0] / (a * a), p[1] / (h * h), p[2] / (c * c)])
}

/// Arc length up the front of the crown from its base, at 257 latitudes.
fn meridian() -> &'static [f32; 257] {
    static T: std::sync::OnceLock<[f32; 257]> = std::sync::OnceLock::new();
    T.get_or_init(|| {
        let [_, h, c] = CROWN;
        let step = std::f32::consts::FRAC_PI_2 / 256.0;
        let mut t = [0.0f32; 257];
        for i in 1..257 {
            let th = step * (i as f32 - 0.5);
            t[i] = t[i - 1] + ((h * th.cos()).powi(2) + (c * th.sin()).powi(2)).sqrt() * step;
        }
        t
    })
}

/// A design point on the crown: `p[0]` mm across the front, `p[1]` mm up it from the
/// base, laid on the surface (the cap's front-centre placement is in these units).
fn cap_point(p: P) -> V {
    let [a, h, c] = CROWN;
    let t = meridian();
    let v = p[1].clamp(0.0, t[256] - 1.0);
    let j = t.partition_point(|&s| s < v).clamp(1, 256);
    let f = (v - t[j - 1]) / (t[j] - t[j - 1]).max(1e-6);
    let th = std::f32::consts::FRAC_PI_2 * (j as f32 - 1.0 + f) / 256.0;
    let r = a * th.cos();
    let lam = (p[0] / r.max(1.0)).clamp(-1.4, 1.4);
    [r * lam.sin(), h * th.sin(), c * th.cos() * lam.cos()]
}

/// Ambient plus diffuse, 1.0 where the surface faces the viewer.
fn lambert_cap(n: V) -> f32 {
    let l = unview(norm(CAP_LIGHT));
    let front = dot(unview([0.0, 0.0, 1.0]), l).max(0.2);
    (0.34 + 0.66 * dot(n, l).max(0.0)) / (0.34 + 0.66 * front)
}

fn cap_light(p: P) -> f32 {
    lambert_cap(crown_normal(cap_point(p))).clamp(0.45, 1.25)
}

/// The cap's extent on screen (view-space mm).
pub fn cap_bounds() -> [f32; 4] {
    let mut b = [f32::MAX, f32::MAX, f32::MIN, f32::MIN];
    let mut add = |q: V| {
        let s = view(q);
        b = [b[0].min(s[0]), b[1].min(s[1]), b[2].max(s[0]), b[3].max(s[1])];
    };
    let [a, h, c] = CROWN;
    for i in 0..=48 {
        for j in 0..=96 {
            let th = std::f32::consts::FRAC_PI_2 * i as f32 / 48.0;
            let la = std::f32::consts::TAU * j as f32 / 96.0;
            add([a * th.cos() * la.sin(), h * th.sin(), c * th.cos() * la.cos()]);
        }
    }
    for j in 0..=64 {
        let al = std::f32::consts::PI * (j as f32 / 64.0 - 0.5);
        let (x, z) = (BRIM_A * al.sin(), BRIM_C * al.cos());
        add([x, brim_y(x, z), z]);
        add([x, brim_y(x, z) - BRIM_T, z]);
    }
    b
}

/// Height of the brim's top face: flush with the crown along the seam, then curving
/// down at the sides and pitching down a little toward the tip.
fn brim_y(x: f32, z: f32) -> f32 {
    let [a, _, c] = CROWN;
    // the drop grows with the distance out from the seam (in mm, not as a share of
    // the brim's width, or the narrow sides fall away as a wall)
    let u = (x / BRIM_A).clamp(-1.0, 1.0);
    let base = c * (1.0 - (x / a).powi(2)).max(0.0).sqrt();
    0.6 - (z - base).max(0.0) * (0.08 + 0.34 * u * u)
}

/// Inside the brim's outline (and outside the crown it is sewn to).
fn in_brim(x: f32, z: f32) -> bool {
    let [a, _, c] = CROWN;
    // the brim ends where it is under 5 mm wide: the sliver at the sides only speckles
    let u = (x / BRIM_A).clamp(-1.0, 1.0);
    let width = (BRIM_C - c) * (1.0 - u * u).max(0.0).sqrt();
    z > 0.0 && width > 5.0 && (x / BRIM_A).powi(2) + (z / BRIM_C).powi(2) <= 1.0 && (x / a).powi(2) + (z / c).powi(2) >= 0.97
}

/// One ray straight into the screen at (sx, sy) view-space mm: its colour, or None.
fn cap_ray(sx: f32, sy: f32, base: V) -> Option<V> {
    let [a, h, c] = CROWN;
    let tau = std::f32::consts::TAU;
    let o = unview([sx, sy, 600.0]);
    let d = unview([0.0, 0.0, -1.0]);
    let l = unview(norm(CAP_LIGHT));
    let eye = unview([0.0, 0.0, 1.0]);
    let at = |t: f32| [o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t];
    let fab = |k: f32| [base[0] * k, base[1] * k, base[2] * k];
    let mut best: Option<(f32, V)> = None;
    let mut take = |t: f32, col: V| {
        if best.is_none_or(|(bt, _)| t < bt) {
            best = Some((t, col));
        }
    };
    // crown
    let (q, dq) = ([o[0] / a, o[1] / h, o[2] / c], [d[0] / a, d[1] / h, d[2] / c]);
    let (qa, qb, qc) = (dot(dq, dq), 2.0 * dot(q, dq), dot(q, q) - 1.0);
    let disc = qb * qb - 4.0 * qa * qc;
    if disc > 0.0 {
        let t1 = (-qb - disc.sqrt()) / (2.0 * qa);
        let t2 = (-qb + disc.sqrt()) / (2.0 * qa);
        let p = at(t1);
        if p[1] >= 0.0 {
            let n = crown_normal(p);
            let mut k = lambert_cap(n);
            let th = (p[1] / h).clamp(-1.0, 1.0).asin();
            let lam = (p[0] / a).atan2(p[2] / c);
            let ring = a * th.cos();
            // six panels: seams at 0, +-60, +-120 and 180 degrees, each with a pair of
            // topstitching rows (the front seam runs under the design)
            let sector = std::f32::consts::PI / 3.0;
            let dl = (lam / sector).round() * sector - lam;
            let ds = dl.abs() * ring;
            k *= 1.0 - 0.22 * (-(ds / 0.7).powi(2)).exp();
            let along = th * h;
            for off in [3.2f32, -3.2] {
                if (ds * dl.signum() - off).abs() < 0.32 && along.rem_euclid(3.3) < 2.4 && th < 1.3 {
                    k *= 0.80;
                }
            }
            // twill ridges and a little yarn noise
            let (u, v) = (lam * ring, along);
            k *= 1.0 + 0.045 * (tau * (u - v) / 1.1).sin() + vnoise(u, v, 0.6, 0.6, 4) * 0.05 + vnoise(u, v, 14.0, 14.0, 9) * 0.03;
            // the crown darkens a little just above the brim seam
            k *= 1.0 - 0.10 * (-p[1] / 3.0).exp();
            let mut col = fab(k);
            // a metal eyelet in each panel, high up
            for e in 0..6 {
                let el = sector * (e as f32 + 0.5);
                let et = 57.0f32.to_radians();
                let ep = [a * et.cos() * el.sin(), h * et.sin(), c * et.cos() * el.cos()];
                let rv = [p[0] - ep[0], p[1] - ep[1], p[2] - ep[2]];
                let r = dot(rv, rv).sqrt();
                if r >= 3.4 {
                    continue;
                }
                col = if r < 1.5 {
                    fab(0.18)
                } else {
                    // a rolled ring: tilt the normal across it, then a sharp highlight
                    let rad = norm(rv);
                    let tilt = (r - 2.45) / 0.95;
                    let nn = norm([n[0] + rad[0] * tilt, n[1] + rad[1] * tilt, n[2] + rad[2] * tilt]);
                    let hv = norm([l[0] + eye[0], l[1] + eye[1], l[2] + eye[2]]);
                    let diff = 0.35 + 0.55 * dot(nn, l).max(0.0);
                    let spec = dot(nn, hv).max(0.0).powf(28.0) * 1.1 * 255.0;
                    let rim = if r > 3.0 { 0.7 } else { 1.0 };
                    [(176.0 * diff + spec) * rim, (178.0 * diff + spec) * rim, (182.0 * diff + spec) * rim]
                };
            }
            take(t1, col);
        } else if at(t2)[1] >= 0.0 {
            take(t2, fab(0.22)); // the inside of the crown, through its opening
        }
    }
    // the button on top
    {
        let cb = [0.0, h - 2.5, 0.0];
        let oc = [o[0] - cb[0], o[1] - cb[1], o[2] - cb[2]];
        let (bb, cc) = (dot(oc, d), dot(oc, oc) - 7.5 * 7.5);
        let disc = bb * bb - cc;
        if disc > 0.0 {
            let t = -bb - disc.sqrt();
            let p = at(t);
            if p[1] > h - 2.0 {
                take(t, fab(lambert_cap(norm([p[0] - cb[0], p[1] - cb[1], p[2] - cb[2]])) * 0.96));
            }
        }
    }
    // the brim: march the ray through the heights it can occupy
    {
        let (ta, tb) = ((4.0 - o[1]) / d[1], (-40.0 - o[1]) / d[1]);
        let (ta, tb) = (ta.min(tb), ta.max(tb));
        let steps = 640;
        let mut prev_in = false;
        let mut prev_t = ta;
        for i in 0..=steps {
            let t = ta + (tb - ta) * i as f32 / steps as f32;
            let p = at(t);
            let inside = in_brim(p[0], p[2]);
            if inside {
                let yb = brim_y(p[0], p[2]);
                if p[1] <= yb && p[1] >= yb - BRIM_T - 0.5 {
                    // the bound edge only at the outline (entering from the crown side is
                    // still the top face)
                    let rho0 = ((p[0] / BRIM_A).powi(2) + (p[2] / BRIM_C).powi(2)).sqrt();
                    let edge = !prev_in && rho0 > 0.985;
                    let (mut lo, mut hi) = (prev_t, t);
                    if !edge {
                        for _ in 0..12 {
                            let m = (lo + hi) / 2.0;
                            let q = at(m);
                            if q[1] <= brim_y(q[0], q[2]) { hi = m } else { lo = m }
                        }
                    }
                    let p = at(hi);
                    let (x, z) = (p[0], p[2]);
                    let k = if edge {
                        // the bound edge, facing out
                        lambert_cap(norm([x / (BRIM_A * BRIM_A), 0.0, z / (BRIM_C * BRIM_C)])) * 0.82
                    } else {
                        let e = 0.5;
                        let gx = (brim_y(x + e, z) - brim_y(x - e, z)) / (2.0 * e);
                        let gz = (brim_y(x, z + e) - brim_y(x, z - e)) / (2.0 * e);
                        let mut k = lambert_cap(norm([-gx, 1.0, -gz]));
                        // rows of stitching following the edge, about 6 mm apart
                        let rho = ((x / BRIM_A).powi(2) + (z / BRIM_C).powi(2)).sqrt();
                        let from_edge = (1.0 - rho) * BRIM_C;
                        let along = (x / BRIM_A).atan2(z / BRIM_C) * 140.0;
                        for row in 0..8 {
                            if (from_edge - (4.5 + 6.2 * row as f32)).abs() < 0.3 && along.rem_euclid(3.3) < 2.4 {
                                k *= 0.78;
                            }
                        }
                        // the crown shades the brim where they meet
                        let dc = (((x / a).powi(2) + (z / c).powi(2)).sqrt() - 1.0) * c;
                        k *= 1.0 - 0.42 * (-dc.max(0.0) / 7.0).exp();
                        k * (1.0 + 0.045 * (tau * (x - z) / 1.1).sin() + vnoise(x, z, 0.6, 0.6, 6) * 0.05)
                    };
                    take(hi, fab(k));
                    break;
                }
            }
            prev_in = inside;
            prev_t = t;
        }
    }
    best.map(|(_, c)| c)
}

/// The cap rendered three-quarter on (view-space mm), anti-aliased, with its shadow.
pub fn raster_cap(color: Color32) -> Image {
    let b = cap_bounds();
    let (w_mm, h_mm) = (b[2] - b[0] + 2.0 * SHADOW_MM, b[3] - b[1] + 2.0 * SHADOW_MM);
    let ppm = (2048.0 / w_mm.max(h_mm)).min(8.0);
    let (w, h) = ((w_mm * ppm).ceil() as usize, (h_mm * ppm).ceil() as usize);
    let x0 = b[0] - SHADOW_MM;
    let y1 = b[3] + SHADOW_MM;
    let base = [color.r() as f32, color.g() as f32, color.b() as f32];
    let mut rgb = vec![[0.0f32; 3]; w * h];
    let mut cov = vec![0.0f32; w * h];
    const THREADS: usize = 8;
    let rows: Vec<(usize, Vec<(V, f32)>)> = std::thread::scope(|sc| {
        let parts: Vec<_> = (0..THREADS)
            .map(|part| {
                sc.spawn(move || {
                    let mut out = Vec::new();
                    for y in (part..h).step_by(THREADS) {
                        let row = (0..w)
                            .map(|x| {
                                let (mut acc, mut n) = ([0.0f32; 3], 0.0f32);
                                for (ox, oy) in [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)] {
                                    if let Some(c) = cap_ray(x0 + (x as f32 + ox) / ppm, y1 - (y as f32 + oy) / ppm, base) {
                                        acc = [acc[0] + c[0], acc[1] + c[1], acc[2] + c[2]];
                                        n += 1.0;
                                    }
                                }
                                (if n > 0.0 { [acc[0] / n, acc[1] / n, acc[2] / n] } else { [0.0; 3] }, n / 4.0)
                            })
                            .collect();
                        out.push((y, row));
                    }
                    out
                })
            })
            .collect();
        parts.into_iter().flat_map(|p| p.join().unwrap()).collect()
    });
    for (y, row) in rows {
        for (x, (c, a)) in row.into_iter().enumerate() {
            rgb[y * w + x] = c;
            cov[y * w + x] = a;
        }
    }
    let mut sh = cov.clone();
    let r = (5.0 * ppm) as usize;
    for _ in 0..2 {
        box_blur(&mut sh, w, h, r.max(1));
    }
    let (ox, oy) = ((3.0 * ppm) as isize, (6.0 * ppm) as isize);
    let mut out = Vec::with_capacity(w * h * 4);
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            let (sx, sy) = (x as isize - ox, y as isize - oy);
            let s_a = if sx >= 0 && sy >= 0 && (sx as usize) < w && (sy as usize) < h { sh[sy as usize * w + sx as usize] } else { 0.0 };
            let c = cov[i];
            let a = c + s_a * 0.34 * (1.0 - c);
            let col = if a > 0.0 { [rgb[i][0] * c / a, rgb[i][1] * c / a, rgb[i][2] * c / a] } else { [0.0; 3] };
            out.extend_from_slice(&[col[0].clamp(0.0, 255.0) as u8, col[1].clamp(0.0, 255.0) as u8, col[2].clamp(0.0, 255.0) as u8, (a.min(1.0) * 255.0) as u8]);
        }
    }
    Image { image: ColorImage::from_rgba_unmultiplied([w, h], &out), rect: [x0, b[1] - SHADOW_MM, b[2] + SHADOW_MM, y1] }
}

// ---------- puckering round the embroidery ----------

/// A shading overlay for the fabric round a design (premultiplied: white lifts, black
/// darkens): the thread's shadow just outside its edge and the small irregular
/// wrinkles stitching pulls into fabric. `segs` are the sewn stitches in design mm;
/// returns the image and the design-mm rect it covers.
pub fn pucker(segs: &[(P, P)], bounds: [f32; 4], fabric: Fabric) -> (ColorImage, [f32; 4]) {
    const PX: f32 = 0.25; // mm per pixel
    const PAD: f32 = 7.0;
    let r = [bounds[0] - PAD, bounds[1] - PAD, bounds[2] + PAD, bounds[3] + PAD];
    let (w, h) = (((r[2] - r[0]) / PX).ceil() as usize + 1, ((r[3] - r[1]) / PX).ceil() as usize + 1);
    let mut cov = vec![0.0f32; w * h];
    for (a, b) in segs {
        let len = ((b[0] - a[0]).powi(2) + (b[1] - a[1]).powi(2)).sqrt();
        let n = (len / (PX * 0.5)).ceil().max(1.0) as usize;
        for s in 0..=n {
            let t = s as f32 / n as f32;
            let (x, y) = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t);
            let (ix, iy) = (((x - r[0]) / PX) as usize, ((r[3] - y) / PX) as usize);
            if ix < w && iy < h {
                cov[iy * w + ix] = 1.0;
            }
        }
    }
    // close the gaps between rows so fills read as solid
    box_blur(&mut cov, w, h, 2);
    for v in &mut cov {
        *v = if *v > 0.5 { 1.0 } else { 0.0 };
    }
    let inv: Vec<f32> = cov.iter().map(|&c| 1.0 - c).collect();
    let dist = chamfer(&inv, w, h);
    let mut sh = cov.clone();
    box_blur(&mut sh, w, h, 3);
    let amp = match fabric {
        Fabric::Jersey => 1.0,
        Fabric::Plain | Fabric::Canvas => 0.55,
        Fabric::Denim | Fabric::Twill => 0.45,
    };
    // wrinkle height outside the edge: irregular ridges dying away within ~5 mm
    let height = |x: usize, y: usize| -> f32 {
        let d = dist[y * w + x] * PX;
        if d <= 0.0 {
            return 0.0;
        }
        let (mx, my) = (x as f32 * PX, y as f32 * PX);
        let ridges = vnoise(mx, my, 1.7, 1.7, 11) + 0.5 * vnoise(mx, my, 3.4, 0.9, 12);
        // eased in from the edge, or the slope there reads as a bright rim
        let e = (d / 2.0).min(1.0);
        ridges * 0.9 * (-d / 2.4).exp() * e * e * (3.0 - 2.0 * e)
    };
    let [lx, ly, lz] = LIGHT_2D;
    let off = 2usize; // the raised thread's shadow falls down-right
    let mut px = Vec::with_capacity(w * h);
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            let mut v = 0.0f32;
            if cov[i] < 1.0 {
                let (xl, xr, yu, yd) = (x.saturating_sub(1), (x + 1).min(w - 1), y.saturating_sub(1), (y + 1).min(h - 1));
                let gx = (height(xr, y) - height(xl, y)) / (2.0 * PX);
                let gy = (height(x, yu) - height(x, yd)) / (2.0 * PX);
                v += ((-gx * lx - gy * ly) / lz * 0.26 * amp).clamp(-0.12, 0.07);
                // a faint contact shadow down-right (the thread draws its own as well)
                let s = if x >= off && y >= off { sh[(y - off) * w + (x - off)] } else { 0.0 };
                v -= 0.12 * s * amp.sqrt();
            }
            let a = v.abs().min(0.6);
            let g = if v > 0.0 { 255.0 * a } else { 0.0 };
            px.push(Color32::from_rgba_premultiplied(g as u8, g as u8, g as u8, (a * 255.0) as u8));
        }
    }
    (ColorImage::new([w, h], px), r)
}
