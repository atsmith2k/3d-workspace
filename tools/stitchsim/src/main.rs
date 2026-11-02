//! stitchsim: open a machine embroidery file and watch it sew.
//!
//!   stitchsim [file.pes]          GUI (drag a file onto the window, or File > Open)
//!   stitchsim --info file.pes     print the stats and exit (no window)
//!   stitchsim file.pes --screenshot out.png [--at 0.5|5000] [--zoom 30] [--size 1280x820]
//!                                 render one frame (half sewn, or 5000 stitches in)
//!                                 to a PNG and exit
//!
//!     [--realistic] [--article tshirt|pants|cap|tote|plain] [--color 2=#ffd100 ...]
//!     [--density] [--hoop 4x4] [--clean] [--fabric #rrggbb]
//!   --clean renders only the design (no panels, markers, needle or scale bar): product shots
//!
//! Keys: Space play/pause, Left/Right step (Shift x100), Home/End, PgUp/PgDn colour
//! block, +/- speed, F fit design, I fit item, G ghost, J jumps, R real-time,
//! L realistic, P place mode (drag moves the design, scroll resizes), [ ] rotate,
//! X problem markers, D density map, N / Shift+N next / previous problem.

mod analysis;
mod formats;
mod garment;
mod palettes;
mod pattern;
mod sim;
mod thread;

use eframe::egui::{self, Color32, Mesh, Pos2, Rect, Sense, Shape, Stroke, TextureHandle, TextureOptions, Vec2};
use analysis::{Report, Severity};
use garment::{Article, Fabric};

/// Hoop sewing fields (mm), as in `cad stitch`.
const HOOPS: [(&str, f32, f32); 7] = [
    ("1.5x2", 40.0, 50.0), ("4x4", 100.0, 100.0), ("2x6", 50.0, 150.0), ("5x7", 130.0, 180.0),
    ("6x10", 160.0, 260.0), ("8x8", 200.0, 200.0), ("8x12", 200.0, 300.0),
];

fn sev_color(s: Severity) -> Color32 {
    match s {
        Severity::Error => Color32::from_rgb(214, 39, 40),
        Severity::Warning => Color32::from_rgb(236, 138, 20),
    }
}
use pattern::Pattern;
use sim::{fmt_time, Machine, Sim};
use std::path::{Path, PathBuf};
use std::sync::Arc;

const CHUNK: usize = 4096;

fn main() -> eframe::Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.first().map(|a| a == "--info").unwrap_or(false) {
        let Some(path) = args.get(1) else {
            eprintln!("usage: stitchsim --info FILE");
            std::process::exit(2);
        };
        match load(Path::new(path)) {
            Ok((p, s)) => print_info(&p, &s),
            Err(e) => {
                eprintln!("{e}");
                std::process::exit(1);
            }
        }
        return Ok(());
    }
    if args.first().map(|a| a == "--segs").unwrap_or(false) {
        // debug: --segs FILE FROM COUNT prints stitch lengths and ends
        let (Some(path), Some(from), Some(n)) = (args.get(1), args.get(2).and_then(|v| v.parse::<usize>().ok()), args.get(3).and_then(|v| v.parse::<usize>().ok())) else {
            eprintln!("usage: stitchsim --segs FILE FROM COUNT");
            std::process::exit(2);
        };
        let (_, s) = load(Path::new(path)).unwrap_or_else(|e| { eprintln!("{e}"); std::process::exit(1) });
        for (i, g) in s.segs.iter().enumerate().skip(from).take(n) {
            let l = ((g.b[0] - g.a[0]).powi(2) + (g.b[1] - g.a[1]).powi(2)).sqrt();
            println!("{i:>7} block {} len {l:5.2}  ({:.2}, {:.2}) -> ({:.2}, {:.2})", g.block, g.a[0], g.a[1], g.b[0], g.b[1]);
        }
        return Ok(());
    }
    let flag = |name: &str| args.iter().position(|a| a == name).and_then(|i| args.get(i + 1)).cloned();
    let shot = flag("--screenshot").map(|out| Shot {
        out: PathBuf::from(out),
        at: flag("--at").and_then(|v| v.parse().ok()),
        zoom: flag("--zoom").and_then(|v| v.parse().ok()),
        frames: 0,
        done: Arc::new(std::sync::atomic::AtomicBool::new(false)),
    });
    let size = flag("--size")
        .and_then(|v| v.split_once('x').and_then(|(w, h)| Some([w.parse().ok()?, h.parse().ok()?])))
        .unwrap_or([1280.0, 820.0]);
    let realistic = args.iter().any(|a| a == "--realistic");
    let article = flag("--article").map(|a| match a.as_str() {
        "tshirt" | "t-shirt" | "shirt" => Article::TShirt,
        "pants" | "jeans" => Article::Pants,
        "cap" | "hat" => Article::Cap,
        "tote" | "bag" => Article::Tote,
        _ => Article::Plain,
    });
    // --color N=#rrggbb (repeatable): thread N shown in another colour
    let recolor: Vec<(usize, Color32)> = args
        .windows(2)
        .filter(|w| w[0] == "--color")
        .filter_map(|w| {
            let (n, hex) = w[1].split_once('=')?;
            let c = u32::from_str_radix(hex.trim_start_matches('#'), 16).ok()?;
            Some((n.parse::<usize>().ok()?.checked_sub(1)?, Color32::from_rgb((c >> 16) as u8, (c >> 8) as u8, c as u8)))
        })
        .collect();
    let color_vals: Vec<&String> = args.windows(2).filter(|w| w[0] == "--color").map(|w| &w[1]).collect();
    let density_map = args.iter().any(|a| a == "--density");
    let clean = args.iter().any(|a| a == "--clean");
    let fabric = flag("--fabric").and_then(|h| u32::from_str_radix(h.trim_start_matches('#'), 16).ok())
        .map(|c| Color32::from_rgb((c >> 16) as u8, (c >> 8) as u8, c as u8));
    let hoop = flag("--hoop").and_then(|h| HOOPS.iter().position(|x| x.0 == h));
    let skip: Vec<&String> = ["--screenshot", "--at", "--size", "--zoom", "--article", "--hoop", "--fabric"].iter().filter_map(|f| flag(f).map(|_| *f)).flat_map(|f| {
        let i = args.iter().position(|a| a == f).unwrap();
        [&args[i], &args[i + 1]]
    }).collect();
    let initial = args.iter().find(|a| !a.starts_with("--") && !skip.contains(a) && !color_vals.contains(a)).map(PathBuf::from);
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("stitchsim")
            .with_inner_size(size)
            .with_drag_and_drop(true),
        ..Default::default()
    };
    eframe::run_native("stitchsim", options, Box::new(move |_cc| {
        let mut app = App::new(initial);
        app.shot = shot;
        app.realistic = realistic;
        app.density_map = density_map;
        if clean {
            app.clean = true;
            app.problems = false;
            app.jumps = false;
            app.ghost = false;
        }
        if hoop.is_some() {
            app.hoop = hoop;
            app.reanalyze();
        }
        if let Some(d) = &mut app.doc {
            for (i, c) in &recolor {
                if let Some(slot) = d.colors.get_mut(*i) {
                    *slot = *c;
                }
            }
        }
        if let Some(a) = article {
            app.set_article(a);
        }
        if let Some(c) = fabric {
            *app.color_mut() = c;
        }
        Ok(Box::new(app))
    }))
}

fn load(path: &Path) -> Result<(Pattern, Sim), String> {
    let p = formats::read(path)?;
    let s = Sim::new(&p, Machine::default());
    Ok((p, s))
}

fn print_info(p: &Pattern, s: &Sim) {
    let (w, h) = s.size();
    println!("format      {}", p.format);
    println!("label       {}", p.label);
    println!("size        {w:.1} x {h:.1} mm");
    println!("stitches    {}", s.penetrations);
    println!("sewn        {}", s.len());
    println!("colours     {}", s.block_start.len());
    println!("trims       {}", s.trims);
    println!("jumps       {} ({} untrimmed)", s.jumps.len(), s.jumps.iter().filter(|j| !j.trimmed && !j.color_change).count());
    println!("longest     {:.2} mm", s.longest);
    println!("thread      {:.1} m", s.thread_m);
    println!("sew time    {} at 650 spm", fmt_time(s.total_time()));
    for (i, n) in s.block_count.iter().enumerate() {
        let t = p.thread(i);
        println!("thread {}    #{:02x}{:02x}{:02x} {:>7} st  {}", i + 1, t.rgb[0], t.rgb[1], t.rgb[2], n, t.name);
    }
    for n in &p.notes {
        println!("note        {n}");
    }
    let r = analysis::analyze(s, None);
    let errors = r.issues.iter().filter(|i| i.sev == Severity::Error).count();
    println!("density     max {:.2} thread layers", r.density.max());
    println!("problems    {} ({} errors, {} warnings)", r.issues.len(), errors, r.issues.len() - errors);
    for i in &r.issues {
        let sev = if i.sev == Severity::Error { "ERROR" } else { "warn " };
        println!("  {sev} {:<16} at ({:.1}, {:.1}) stitch {}: {}", i.kind, i.at[0], i.at[1], i.k, i.detail);
    }
}

/// `--screenshot`: render a frame of the window's own framebuffer to a PNG, then quit.
struct Shot {
    out: PathBuf,
    at: Option<f64>,
    zoom: Option<f32>, // px per mm, centred on the needle
    frames: u32,
    done: Arc<std::sync::atomic::AtomicBool>,
}

fn save_png(path: &Path, img: &egui::ColorImage) -> Result<(), String> {
    let f = std::fs::File::create(path).map_err(|e| e.to_string())?;
    let mut enc = png::Encoder::new(std::io::BufWriter::new(f), img.size[0] as u32, img.size[1] as u32);
    enc.set_color(png::ColorType::Rgba);
    enc.set_depth(png::BitDepth::Eight);
    let mut w = enc.write_header().map_err(|e| e.to_string())?;
    let data: Vec<u8> = img.pixels.iter().flat_map(|c| c.to_array()).collect();
    w.write_image_data(&data).map_err(|e| e.to_string())
}

// ---------- view ----------

#[derive(Clone, Copy, PartialEq)]
struct Camera {
    center: [f32; 2], // mm
    zoom: f32,        // px per mm
}

/// Where the design sits on the garment: its centre at (x, y) mm, scaled and rotated.
#[derive(Clone, Copy, PartialEq)]
struct Stage {
    x: f32,
    y: f32,
    scale: f32,
    rot: f32, // degrees, counter-clockwise
}

#[derive(Clone, PartialEq)]
struct CacheKey {
    cam: Camera,
    rect: Rect,
    width: f32,
    shade: bool,
    realistic: bool,
    stage: Stage,
    hidden: Vec<bool>,
    colors: Vec<Color32>,
}

struct GarmentTex {
    article: Article,
    color: Option<Color32>, // baked-in colour (contrast topstitching); None: tinted white
    tex: TextureHandle,
    rect: [f32; 4],
    tris: Vec<[[f32; 2]; 3]>,
}

struct Loaded {
    path: PathBuf,
    pat: Pattern,
    sim: Sim,
    report: Report,
    colors: Vec<Color32>,
    hidden: Vec<bool>,
}

struct App {
    doc: Option<Loaded>,
    error: Option<String>,
    cam: Camera,
    fit_pending: bool,
    pos: f64,       // stitches sewn (fractional while playing)
    playing: bool,
    speed: f32,     // stitches per second
    realtime: bool, // play at machine speed x `mult`, trims and colour stops included
    mult: f32,
    sim_t: f32,
    width: f32, // thread width mm
    shade: bool,
    ghost: bool,
    jumps: bool,
    realistic: bool,
    problems: bool,
    density_map: bool,
    hoop: Option<usize>,
    selected: Option<usize>,
    article: Article,
    garment_colors: Vec<Color32>,
    stage: Stage,
    place: bool,
    fit_item_pending: bool,
    thread_tex: Option<TextureHandle>,
    tiles: Vec<(Fabric, TextureHandle, f32)>,
    garment: Option<GarmentTex>,
    key: Option<CacheKey>,
    sewn_chunks: Vec<Arc<Mesh>>,
    ghost_chunks: Vec<Arc<Mesh>>,
    frame_ms: f32,
    shot: Option<Shot>,
    clean: bool,
}

impl App {
    fn new(initial: Option<PathBuf>) -> Self {
        let mut app = App {
            doc: None,
            error: None,
            cam: Camera { center: [0.0, 0.0], zoom: 4.0 },
            fit_pending: true,
            pos: 0.0,
            playing: false,
            speed: 400.0,
            realtime: false,
            mult: 10.0,
            sim_t: 0.0,
            width: 0.45,
            shade: true,
            ghost: true,
            jumps: true,
            realistic: false,
            problems: true,
            density_map: false,
            hoop: None,
            selected: None,
            article: Article::Plain,
            garment_colors: Article::ALL.iter().map(|a| a.default_color()).collect(),
            stage: Stage { x: 0.0, y: 0.0, scale: 1.0, rot: 0.0 },
            place: false,
            fit_item_pending: false,
            thread_tex: None,
            tiles: Vec::new(),
            garment: None,
            key: None,
            sewn_chunks: Vec::new(),
            ghost_chunks: Vec::new(),
            frame_ms: 0.0,
            shot: None,
            clean: false,
        };
        if let Some(p) = initial {
            app.open(&p);
        }
        app
    }

    fn open(&mut self, path: &Path) {
        match load(path) {
            Ok((pat, sim)) => {
                let n = sim.block_start.len();
                let colors = (0..n).map(|i| {
                    let c = pat.thread(i).rgb;
                    Color32::from_rgb(c[0], c[1], c[2])
                });
                self.pos = sim.len() as f64; // show the finished design first
                self.sim_t = sim.total_time();
                let report = analysis::analyze(&sim, self.hoop_spec());
                self.doc = Some(Loaded { path: path.to_path_buf(), colors: colors.collect(), hidden: vec![false; n], pat, sim, report });
                self.selected = None;
                self.error = None;
                self.playing = false;
                self.fit_pending = true;
                self.key = None;
                self.reset_stage();
                if self.article != Article::Plain {
                    self.fit_pending = false;
                    self.fit_item_pending = true;
                }
            }
            Err(e) => self.error = Some(e),
        }
    }

    fn open_dialog(&mut self) {
        if let Some(p) = rfd::FileDialog::new()
            .add_filter("Embroidery", &["pes", "pec", "dst", "exp", "jef"])
            .pick_file()
        {
            self.open(&p);
        }
    }

    fn hoop_spec(&self) -> Option<(&'static str, f32, f32)> {
        self.hoop.map(|i| HOOPS[i])
    }

    fn reanalyze(&mut self) {
        let hoop = self.hoop_spec();
        if let Some(d) = &mut self.doc {
            d.report = analysis::analyze(&d.sim, hoop);
            self.selected = None;
        }
    }

    /// Jump the timeline to problem `i` and centre the view on it.
    fn go_to_issue(&mut self, i: usize) {
        let Some(d) = &self.doc else { return };
        let Some(is) = d.report.issues.get(i) else { return };
        let (k, at) = (is.k, is.at);
        self.selected = Some(i);
        self.playing = false;
        self.seek(k as f64);
        self.cam.center = self.place_fn()(at);
        self.cam.zoom = self.cam.zoom.max(8.0);
    }

    fn set_article(&mut self, a: Article) {
        self.article = a;
        self.reset_stage();
        self.fit_item_pending = true;
    }

    /// The article's usual placement and size (or the design as it is, on plain fabric).
    fn reset_stage(&mut self) {
        let Some(d) = &self.doc else { return };
        let b = d.sim.bounds;
        let (w, h) = d.sim.size();
        let (x, y, width, _) = self.article.placement();
        self.stage = if self.article == Article::Plain {
            Stage { x: (b[0] + b[2]) / 2.0, y: (b[1] + b[3]) / 2.0, scale: 1.0, rot: 0.0 }
        } else {
            // the usual width, but keep tall designs to a sensible height too
            let s = (width / w.max(1.0)).min(width * 1.2 / h.max(1.0));
            Stage { x, y, scale: s, rot: 0.0 }
        };
    }

    fn color(&self) -> Color32 {
        self.garment_colors[Article::ALL.iter().position(|a| *a == self.article).unwrap()]
    }

    fn color_mut(&mut self) -> &mut Color32 {
        let i = Article::ALL.iter().position(|a| *a == self.article).unwrap();
        &mut self.garment_colors[i]
    }

    /// Design (file mm) -> garment (world mm).
    fn place_fn(&self) -> impl Fn([f32; 2]) -> [f32; 2] + Copy {
        let c = match &self.doc {
            Some(d) => {
                let b = d.sim.bounds;
                [(b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0]
            }
            None => [0.0, 0.0],
        };
        let st = self.stage;
        let (sn, cs) = st.rot.to_radians().sin_cos();
        move |p: [f32; 2]| {
            let (x, y) = ((p[0] - c[0]) * st.scale, (p[1] - c[1]) * st.scale);
            [st.x + x * cs - y * sn, st.y + x * sn + y * cs]
        }
    }

    fn design_corners(&self) -> Vec<[f32; 2]> {
        let Some(d) = &self.doc else { return vec![] };
        let b = d.sim.bounds;
        let f = self.place_fn();
        vec![f([b[0], b[1]]), f([b[2], b[1]]), f([b[2], b[3]]), f([b[0], b[3]])]
    }

    fn ensure_textures(&mut self, ctx: &egui::Context) {
        if self.thread_tex.is_none() {
            let opts = TextureOptions { wrap_mode: egui::TextureWrapMode::Repeat, ..TextureOptions::LINEAR };
            self.thread_tex = Some(ctx.load_texture("thread", thread::texture(), opts));
        }
        let fabric = self.article.fabric();
        if !self.tiles.iter().any(|(f, ..)| *f == fabric) {
            let (img, mm) = garment::tile(fabric);
            let opts = TextureOptions {
                wrap_mode: egui::TextureWrapMode::Repeat,
                mipmap_mode: Some(egui::TextureFilter::Linear),
                ..TextureOptions::LINEAR
            };
            self.tiles.push((fabric, ctx.load_texture(format!("tile{fabric:?}"), img, opts), mm));
        }
        if self.article == Article::Plain {
            return;
        }
        let baked = spec_has_thread(self.article).then(|| self.color());
        let stale = match &self.garment {
            Some(g) => g.article != self.article || g.color != baked,
            None => true,
        };
        // re-bake contrast-stitched garments only once the colour picker is let go
        let dragging = self.garment.as_ref().is_some_and(|g| g.article == self.article) && ctx.input(|i| i.pointer.any_down());
        if stale && !dragging {
            let spec = garment::spec(self.article);
            let img = garment::raster(&spec, baked.unwrap_or(Color32::WHITE));
            let mut tris = Vec::new();
            for p in &spec.parts {
                for t in garment::triangulate(&p.poly) {
                    tris.push([p.poly[t[0]], p.poly[t[1]], p.poly[t[2]]]);
                }
            }
            let tex = ctx.load_texture("garment", img.image, TextureOptions::LINEAR);
            self.garment = Some(GarmentTex { article: self.article, color: baked, tex, rect: img.rect, tris });
        }
    }

    fn k(&self) -> usize {
        self.pos.floor().max(0.0) as usize
    }

    fn seek(&mut self, k: f64) {
        if let Some(d) = &self.doc {
            self.pos = k.clamp(0.0, d.sim.len() as f64);
            self.sim_t = d.sim.time[self.k()];
        }
    }
}

/// Garments whose topstitching is a contrast colour are baked in their colour; the
/// rest are drawn white and tinted, so recolouring them is free.
fn spec_has_thread(a: Article) -> bool {
    a == Article::Pants
}

fn shades(c: Color32) -> (Color32, Color32) {
    let f = |v: u8, k: f32| -> u8 {
        if k < 1.0 { (v as f32 * k) as u8 } else { (v as f32 + (255.0 - v as f32) * (k - 1.0)) as u8 }
    };
    (
        Color32::from_rgb(f(c.r(), 0.55), f(c.g(), 0.55), f(c.b(), 0.55)),
        Color32::from_rgb(f(c.r(), 1.35), f(c.g(), 1.35), f(c.b(), 1.35)),
    )
}

/// One stitch as a quad, dark at both edges and light along the middle (a round
/// thread in raking light), or flat when it is too thin on screen to show shading.
fn push_stitch(m: &mut Mesh, a: Pos2, b: Pos2, w: f32, c: Color32, shade: bool) {
    let d = b - a;
    let len = d.length();
    if len < 1e-3 {
        return;
    }
    let n = Vec2::new(-d.y, d.x) / len * (w * 0.5);
    let i = m.vertices.len() as u32;
    if shade && w >= 2.5 {
        let (dark, light) = shades(c);
        for p in [a, b] {
            m.colored_vertex(p + n, dark);
            m.colored_vertex(p, light);
            m.colored_vertex(p - n, dark);
        }
        m.add_triangle(i, i + 1, i + 4);
        m.add_triangle(i, i + 4, i + 3);
        m.add_triangle(i + 1, i + 2, i + 5);
        m.add_triangle(i + 1, i + 5, i + 4);
    } else {
        for p in [a + n, a - n, b - n, b + n] {
            m.colored_vertex(p, c);
        }
        m.add_triangle(i, i + 1, i + 2);
        m.add_triangle(i, i + 2, i + 3);
    }
}

impl eframe::App for App {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut eframe::Frame) {
        let t0 = std::time::Instant::now();
        let ctx = &ui.ctx().clone();
        // dropped files
        let dropped: Vec<PathBuf> = ctx.input(|i| {
            i.raw.dropped_files.iter().map(|f| f.path().to_path_buf()).filter(|p| !p.as_os_str().is_empty()).collect()
        });
        if let Some(p) = dropped.first() {
            self.open(p);
        }
        self.keys(ctx);
        self.advance(ctx);
        self.ensure_textures(ctx);
        let bg = if self.article == Article::Plain { self.color() } else { Color32::from_rgb(228, 226, 221) };

        if !self.clean {
            egui::Panel::top("top").show(ui, |ui| self.top_bar(ui));
            egui::Panel::bottom("transport").show(ui, |ui| self.transport(ui));
            egui::Panel::left("info").resizable(true).default_size(290.0).max_size(420.0).show(ui, |ui| self.side(ui));
        }
        egui::CentralPanel::default().frame(egui::Frame::NONE.fill(bg)).show(ui, |ui| self.canvas(ui));
        self.frame_ms = self.frame_ms * 0.9 + t0.elapsed().as_secs_f32() * 1000.0 * 0.1;
        self.screenshot(ctx);
    }
}

impl App {
    fn keys(&mut self, ctx: &egui::Context) {
        if ctx.egui_wants_keyboard_input() {
            return;
        }
        let Some(d) = &self.doc else { return };
        let n = d.sim.len() as f64;
        let k = self.k();
        let blk = d.sim.block_at(k);
        let starts = d.sim.block_start.clone();
        let (mut seek, mut toggle) = (None, false);
        let mut issue_step: Option<i32> = None;
        let n_issues = d.report.issues.len();
        ctx.input(|i| {
            let step = if i.modifiers.shift { 100.0 } else { 1.0 };
            if i.key_pressed(egui::Key::Space) {
                toggle = true;
            }
            if i.key_pressed(egui::Key::ArrowRight) {
                seek = Some(self.pos.floor() + step);
            }
            if i.key_pressed(egui::Key::ArrowLeft) {
                seek = Some(self.pos.floor() - step);
            }
            if i.key_pressed(egui::Key::Home) {
                seek = Some(0.0);
            }
            if i.key_pressed(egui::Key::End) {
                seek = Some(n);
            }
            if i.key_pressed(egui::Key::PageDown) {
                seek = Some(starts.get(blk + 1).map(|&s| s as f64).unwrap_or(n));
            }
            if i.key_pressed(egui::Key::PageUp) {
                let s = starts[blk];
                let target = if k > s { s } else { starts[blk.saturating_sub(1)] };
                seek = Some(target as f64);
            }
            if i.key_pressed(egui::Key::Plus) || i.key_pressed(egui::Key::Equals) {
                self.speed = (self.speed * 2.0).min(100_000.0);
                self.mult = (self.mult * 2.0).min(1000.0);
            }
            if i.key_pressed(egui::Key::Minus) {
                self.speed = (self.speed / 2.0).max(1.0);
                self.mult = (self.mult / 2.0).max(0.25);
            }
            if i.key_pressed(egui::Key::F) {
                self.fit_pending = true;
            }
            if i.key_pressed(egui::Key::G) {
                self.ghost = !self.ghost;
            }
            if i.key_pressed(egui::Key::J) {
                self.jumps = !self.jumps;
            }
            if i.key_pressed(egui::Key::R) {
                self.realtime = !self.realtime;
            }
            if i.key_pressed(egui::Key::L) {
                self.realistic = !self.realistic;
            }
            if i.key_pressed(egui::Key::P) {
                self.place = !self.place;
            }
            if i.key_pressed(egui::Key::I) {
                self.fit_item_pending = true;
            }
            if i.key_pressed(egui::Key::X) {
                self.problems = !self.problems;
            }
            if i.key_pressed(egui::Key::D) {
                self.density_map = !self.density_map;
            }
            if i.key_pressed(egui::Key::N) {
                issue_step = Some(if i.modifiers.shift { -1 } else { 1 });
            }
            if i.key_pressed(egui::Key::OpenBracket) {
                self.stage.rot += 5.0;
            }
            if i.key_pressed(egui::Key::CloseBracket) {
                self.stage.rot -= 5.0;
            }
        });
        if toggle {
            self.toggle_play();
        }
        if let (Some(st), true) = (issue_step, n_issues > 0) {
            let cur = self.selected.map(|v| v as i32).unwrap_or(if st > 0 { -1 } else { 0 });
            self.go_to_issue((cur + st).rem_euclid(n_issues as i32) as usize);
            return;
        }
        if let Some(s) = seek {
            self.playing = false;
            self.seek(s);
        }
    }

    fn screenshot(&mut self, ctx: &egui::Context) {
        let Some(shot) = &mut self.shot else { return };
        shot.frames += 1;
        if shot.frames == 1 {
            if let (Some(at), Some(d)) = (shot.at, &self.doc) {
                let n = d.sim.len() as f64;
                let k = if at <= 1.0 { at * n } else { at };
                self.pos = k.clamp(0.0, n);
            }
        } else if shot.frames == 2 {
            self.fit_pending = self.article == Article::Plain && shot.zoom.is_none();
            self.fit_item_pending = self.article != Article::Plain && shot.zoom.is_none();
            if let (Some(z), Some(d)) = (shot.zoom, &self.doc) {
                self.cam = Camera { center: self.place_fn()(d.sim.needle(self.k())), zoom: z };
            }
        } else if shot.frames == 5 {
            let (out, done, c) = (shot.out.clone(), shot.done.clone(), ctx.clone());
            ctx.send_viewport_cmd(egui::ViewportCommand::Screenshot(egui::ScreenshotCallback::new(move |img| {
                match save_png(&out, &img) {
                    Ok(()) => println!("wrote {}", out.display()),
                    Err(e) => eprintln!("screenshot failed: {e}"),
                }
                done.store(true, std::sync::atomic::Ordering::SeqCst);
                c.request_repaint();
            })));
        } else if shot.done.load(std::sync::atomic::Ordering::SeqCst) {
            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
        }
        ctx.request_repaint();
    }

    fn toggle_play(&mut self) {
        let Some(d) = &self.doc else { return };
        if !self.playing && self.k() >= d.sim.len() {
            self.seek(0.0);
        }
        self.playing = !self.playing;
    }

    fn advance(&mut self, ctx: &egui::Context) {
        let Some(d) = &self.doc else { return };
        if !self.playing {
            return;
        }
        let dt = ctx.input(|i| i.stable_dt).min(0.1);
        let n = d.sim.len();
        if self.realtime {
            self.sim_t += dt * self.mult;
            self.pos = d.sim.at_time(self.sim_t) as f64;
        } else {
            self.pos += (dt * self.speed) as f64;
            self.sim_t = d.sim.time[self.k().min(n)];
        }
        if self.pos >= n as f64 {
            self.pos = n as f64;
            self.playing = false;
        }
        ctx.request_repaint();
    }

    fn top_bar(&mut self, ui: &mut egui::Ui) {
        ui.horizontal(|ui| {
            if ui.button("Open…").clicked() {
                self.open_dialog();
            }
            if ui.button("Fit").on_hover_text("F").clicked() {
                self.fit_pending = true;
            }
            ui.separator();
            ui.checkbox(&mut self.ghost, "Ghost").on_hover_text("G: show what is still to sew, faintly");
            ui.checkbox(&mut self.jumps, "Jumps").on_hover_text("J: jump threads (red: left untrimmed)");
            ui.checkbox(&mut self.shade, "Thread shading");
            ui.checkbox(&mut self.problems, "Problems").on_hover_text("X: flag problem areas on the design (N: next)");
            ui.checkbox(&mut self.density_map, "Density").on_hover_text("D: thread-layer heat map (yellow 2.5, orange 3.5, red 5+)");
            ui.checkbox(&mut self.realistic, "Realistic").on_hover_text("L: twisted, glossy thread with shadows");
            ui.add(egui::Slider::new(&mut self.width, 0.2..=0.8).text("thread mm").fixed_decimals(2));
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                ui.weak(format!("{:.1} ms/frame", self.frame_ms));
                if let Some(d) = &self.doc {
                    ui.label(d.path.file_name().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default());
                }
            });
        });
    }

    fn side(&mut self, ui: &mut egui::Ui) {
        let Some(d) = &mut self.doc else {
            ui.add_space(20.0);
            ui.label("Open a PES, PEC, DST, EXP or JEF file,\nor drop one on the window.");
            if let Some(e) = &self.error {
                ui.colored_label(Color32::from_rgb(200, 60, 30), e);
            }
            return;
        };
        let s = &d.sim;
        let (w, h) = s.size();
        egui::Grid::new("stats").num_columns(2).spacing([12.0, 3.0]).show(ui, |ui| {
            for (k, v) in [
                ("format", d.pat.format.clone()),
                ("label", d.pat.label.clone()),
                ("size", format!("{w:.1} x {h:.1} mm")),
                ("stitches", format!("{}", s.penetrations)),
                ("colours", format!("{}", s.block_start.len())),
                ("trims", format!("{}", s.trims)),
                ("jumps", format!("{} ({} untrimmed)", s.jumps.len(),
                    s.jumps.iter().filter(|j| !j.trimmed && !j.color_change).count())),
                ("longest", format!("{:.1} mm", s.longest)),
                ("thread", format!("~{:.0} m", s.thread_m)),
                ("sew time", format!("~{} at 650 spm", fmt_time(s.total_time()))),
            ] {
                ui.weak(k);
                ui.label(v);
                ui.end_row();
            }
        });
        for n in &d.pat.notes {
            ui.colored_label(Color32::from_rgb(170, 110, 20), n);
        }
        ui.separator();
        self.problems_panel(ui);
        ui.separator();
        self.staging(ui);
        let Some(d) = &mut self.doc else { return };
        let s = &d.sim;
        ui.separator();
        ui.horizontal(|ui| {
            ui.strong("Threads (sewing order)");
            let file = |i: usize| {
                let c = d.pat.thread(i).rgb;
                Color32::from_rgb(c[0], c[1], c[2])
            };
            let changed = (0..d.colors.len()).any(|i| d.colors[i] != file(i));
            if ui.add_enabled(changed, egui::Button::new("Reset colours").small()).clicked() {
                for i in 0..d.colors.len() {
                    d.colors[i] = file(i);
                }
            }
        });
        let cur = s.block_at(self.pos.floor() as usize);
        let mut seek = None;
        egui::ScrollArea::vertical().show(ui, |ui| {
            for i in 0..s.block_start.len() {
                let t = d.pat.thread(i);
                let file_col = Color32::from_rgb(t.rgb[0], t.rgb[1], t.rgb[2]);
                ui.horizontal(|ui| {
                    let mut vis = !d.hidden[i];
                    if ui.checkbox(&mut vis, "").on_hover_text("show / hide this colour").changed() {
                        d.hidden[i] = !vis;
                    }
                    // the swatch is a colour picker; the menu next to it picks a Brother spool
                    ui.color_edit_button_srgba(&mut d.colors[i]).on_hover_text("pick a thread colour");
                    ui.menu_button("Brother", |ui| {
                        ui.set_max_width(260.0);
                        egui::Grid::new(("pec", i)).spacing([3.0, 3.0]).show(ui, |ui| {
                            for (n, (c, name)) in palettes::PEC.iter().enumerate().skip(1) {
                                let col = Color32::from_rgb((c >> 16) as u8, (c >> 8) as u8, *c as u8);
                                let (r, resp) = ui.allocate_exact_size(Vec2::new(22.0, 18.0), Sense::click());
                                ui.painter().rect_filled(r, 2.0, col);
                                if d.colors[i] == col {
                                    ui.painter().rect_stroke(r, 2.0, Stroke::new(2.0, Color32::from_rgb(220, 40, 40)), egui::StrokeKind::Outside);
                                }
                                if resp.on_hover_text(*name).clicked() {
                                    d.colors[i] = col;
                                    ui.close();
                                }
                                if n % 8 == 0 {
                                    ui.end_row();
                                }
                            }
                        });
                    });
                    let c = d.colors[i];
                    let text = format!("{}. #{:02x}{:02x}{:02x}  {} st", i + 1, c.r(), c.g(), c.b(), s.block_count[i]);
                    let rt = if i == cur { egui::RichText::new(text).strong() } else { egui::RichText::new(text) };
                    if ui.selectable_label(i == cur, rt).on_hover_text(&t.name).clicked() {
                        seek = Some(s.block_start[i] as f64);
                    }
                });
                if d.colors[i] != file_col {
                    ui.horizontal(|ui| {
                        ui.add_space(24.0);
                        let hex = format!("#{:02x}{:02x}{:02x}", t.rgb[0], t.rgb[1], t.rgb[2]);
                        let name = if t.name.eq_ignore_ascii_case(&hex) { String::new() } else { t.name.clone() };
                        ui.weak(format!("file: {hex} {name}"));
                        if ui.small_button("reset").clicked() {
                            d.colors[i] = file_col;
                        }
                    });
                } else if !t.name.is_empty() {
                    ui.weak(format!("      {}", t.name));
                }
            }
        });
        if let Some(k) = seek {
            self.playing = false;
            self.seek(k);
        }
    }

    fn problems_panel(&mut self, ui: &mut egui::Ui) {
        let mut hoop = self.hoop;
        ui.horizontal(|ui| {
            ui.label("Hoop");
            egui::ComboBox::from_id_salt("hoop")
                .selected_text(hoop.map(|i| format!("{} ({:.0} x {:.0})", HOOPS[i].0, HOOPS[i].1, HOOPS[i].2)).unwrap_or("not checked".into()))
                .show_ui(ui, |ui| {
                    ui.selectable_value(&mut hoop, None, "not checked");
                    for (i, h) in HOOPS.iter().enumerate() {
                        ui.selectable_value(&mut hoop, Some(i), format!("{} ({:.0} x {:.0} mm)", h.0, h.1, h.2));
                    }
                });
        });
        if hoop != self.hoop {
            self.hoop = hoop;
            self.reanalyze();
        }
        let Some(d) = &self.doc else { return };
        let issues = &d.report.issues;
        let errors = issues.iter().filter(|i| i.sev == Severity::Error).count();
        let title = if issues.is_empty() {
            "Problems: none found".to_string()
        } else {
            format!("Problems: {errors} error{}, {} warning{}", if errors == 1 { "" } else { "s" },
                issues.len() - errors, if issues.len() - errors == 1 { "" } else { "s" })
        };
        let mut go = None;
        egui::CollapsingHeader::new(egui::RichText::new(title).strong())
            .id_salt("problems")
            .default_open(true)
            .show(ui, |ui| {
                if issues.is_empty() {
                    ui.weak(format!("max density {:.1} layers; no long, tiny or piled-up stitches, no untrimmed jumps",
                        d.report.density.max()));
                }
                egui::ScrollArea::vertical().id_salt("plist").max_height(220.0).show(ui, |ui| {
                    for (i, is) in issues.iter().enumerate() {
                        ui.horizontal(|ui| {
                            let (r, _) = ui.allocate_exact_size(Vec2::new(18.0, 18.0), Sense::hover());
                            ui.painter().circle_filled(r.center(), 8.0, sev_color(is.sev));
                            ui.painter().text(r.center(), egui::Align2::CENTER_CENTER, format!("{}", i + 1),
                                egui::FontId::proportional(10.0), Color32::WHITE);
                            let txt = egui::RichText::new(format!("{}  (stitch {})", is.kind, is.k));
                            if ui.selectable_label(self.selected == Some(i), txt)
                                .on_hover_text(format!("{}\nstitch {} at ({:.1}, {:.1}) mm", is.fix, is.k, is.at[0], is.at[1]))
                                .clicked()
                            {
                                go = Some(i);
                            }
                        });
                    }
                });
                if let Some(i) = self.selected.and_then(|i| issues.get(i)) {
                    ui.add_space(2.0);
                    ui.add(egui::Label::new(egui::RichText::new(&i.detail).strong()).wrap());
                    ui.add(egui::Label::new(egui::RichText::new(format!("Fix: {}", i.fix)).color(sev_color(i.sev))).wrap());
                } else if !issues.is_empty() {
                    ui.weak("click a problem (or press N) to go to it");
                }
            });
        if let Some(i) = go {
            self.go_to_issue(i);
        }
    }

    fn staging(&mut self, ui: &mut egui::Ui) {
        ui.strong("Stage on");
        let mut art = self.article;
        egui::ComboBox::from_id_salt("article").selected_text(art.name()).show_ui(ui, |ui| {
            for a in Article::ALL {
                ui.selectable_value(&mut art, a, a.name());
            }
        });
        if art != self.article {
            self.set_article(art);
        }
        ui.horizontal(|ui| {
            ui.label("Colour");
            ui.color_edit_button_srgba(self.color_mut());
            if ui.button("Default").clicked() {
                *self.color_mut() = self.article.default_color();
            }
        });
        let Some(d) = &self.doc else { return };
        let (w, h) = d.sim.size();
        if self.article != Article::Plain {
            ui.weak(format!("usual spot: {}", self.article.placement().3));
        }
        ui.checkbox(&mut self.place, "Place design (P)").on_hover_text("drag moves the design, scroll resizes it, [ ] rotate");
        let mut width = w * self.stage.scale;
        egui::Grid::new("stage").num_columns(2).spacing([8.0, 3.0]).show(ui, |ui| {
            ui.weak("x, y mm");
            ui.horizontal(|ui| {
                ui.add(egui::DragValue::new(&mut self.stage.x).speed(0.5).fixed_decimals(0));
                ui.add(egui::DragValue::new(&mut self.stage.y).speed(0.5).fixed_decimals(0));
            });
            ui.end_row();
            ui.weak("width mm");
            if ui.add(egui::DragValue::new(&mut width).speed(0.5).range(5.0..=600.0).fixed_decimals(0)).changed() {
                self.stage.scale = width / w.max(1.0);
            }
            ui.end_row();
            ui.weak("rotate");
            ui.add(egui::DragValue::new(&mut self.stage.rot).speed(0.5).suffix(" deg").fixed_decimals(0));
            ui.end_row();
        });
        ui.horizontal(|ui| {
            if ui.button("Reset").on_hover_text("usual placement and size").clicked() {
                self.reset_stage();
            }
            if ui.button("Actual size").clicked() {
                self.stage.scale = 1.0;
            }
            if ui.button("Fit item (I)").clicked() {
                self.fit_item_pending = true;
            }
        });
        let pct = self.stage.scale * 100.0;
        ui.label(format!("shown {:.0} x {:.0} mm ({pct:.0}%)", w * self.stage.scale, h * self.stage.scale));
        if (self.stage.scale - 1.0).abs() > 0.1 {
            ui.colored_label(Color32::from_rgb(180, 100, 20),
                "Stitch files don't scale cleanly past +-10% (density and pull change): rebuild the design at this size to sew it.");
        }
    }

    fn transport(&mut self, ui: &mut egui::Ui) {
        ui.add_space(4.0);
        let Some(d) = &self.doc else {
            ui.label("No file");
            return;
        };
        let n = d.sim.len();
        let k = self.k().min(n);
        // timeline: colour bands, jumps as ticks, playhead
        let (rect, resp) = ui.allocate_exact_size(Vec2::new(ui.available_width(), 26.0), Sense::click_and_drag());
        let p = ui.painter_at(rect);
        let x_of = |i: usize| rect.left() + rect.width() * i as f32 / n.max(1) as f32;
        for (b, &s0) in d.sim.block_start.iter().enumerate() {
            let s1 = d.sim.block_start.get(b + 1).copied().unwrap_or(n);
            let r = Rect::from_min_max(Pos2::new(x_of(s0), rect.top() + 6.0), Pos2::new(x_of(s1), rect.bottom() - 6.0));
            p.rect_filled(r, 0.0, d.colors[b].gamma_multiply(if d.hidden[b] { 0.25 } else { 1.0 }));
        }
        for j in d.sim.jumps.iter().filter(|j| j.trimmed) {
            let x = x_of(j.after);
            p.line_segment([Pos2::new(x, rect.top() + 2.0), Pos2::new(x, rect.top() + 6.0)], Stroke::new(1.0, Color32::GRAY));
        }
        for is in &d.report.issues {
            let x = x_of(is.k);
            p.line_segment([Pos2::new(x, rect.bottom() - 6.0), Pos2::new(x, rect.bottom())], Stroke::new(2.0, sev_color(is.sev)));
        }
        let hx = x_of(k);
        p.line_segment([Pos2::new(hx, rect.top()), Pos2::new(hx, rect.bottom())], Stroke::new(2.0, Color32::from_rgb(220, 40, 40)));
        let blk = d.sim.block_at(k);
        let s0 = d.sim.block_start[blk];
        let prev_blk = if k > s0 { s0 } else { d.sim.block_start[blk.saturating_sub(1)] };
        let next_blk = d.sim.block_start.get(blk + 1).copied().unwrap_or(n);
        let here = self.pos.floor();
        if let Some(mp) = resp.interact_pointer_pos() {
            if resp.dragged() || resp.clicked() {
                let f = ((mp.x - rect.left()) / rect.width()).clamp(0.0, 1.0);
                self.playing = false;
                self.seek((f * n as f32).round() as f64);
            }
        }
        ui.horizontal(|ui| {
            let mut seek = None;
            if ui.button("|<").on_hover_text("Home: start").clicked() {
                seek = Some(0.0);
            }
            if ui.button("<<").on_hover_text("PgUp: previous colour").clicked() {
                seek = Some(prev_blk as f64);
            }
            if ui.button("<").on_hover_text("Left: one stitch back (Shift: 100)").clicked() {
                seek = Some(here - 1.0);
            }
            if ui.button(if self.playing { "  Pause  " } else { "  Play  " }).on_hover_text("Space").clicked() {
                self.toggle_play();
            }
            if ui.button(">").on_hover_text("Right: one stitch on (Shift: 100)").clicked() {
                seek = Some(here + 1.0);
            }
            if ui.button(">>").on_hover_text("PgDn: next colour").clicked() {
                seek = Some(next_blk as f64);
            }
            if ui.button(">|").on_hover_text("End: finished").clicked() {
                seek = Some(n as f64);
            }
            if let Some(t) = seek {
                self.playing = false;
                self.seek(t);
            }
            ui.separator();
            ui.checkbox(&mut self.realtime, "Machine time").on_hover_text("R: play at machine speed (650 spm) x multiplier, with trim and colour-change stops");
            if self.realtime {
                ui.add(egui::Slider::new(&mut self.mult, 0.25..=1000.0).logarithmic(true).text("x real speed"));
            } else {
                ui.add(egui::Slider::new(&mut self.speed, 1.0..=100_000.0).logarithmic(true).text("stitches/s"));
            }
            ui.separator();
            let d = self.doc.as_ref().unwrap();
            let k = self.k().min(n);
            let blk = d.sim.block_at(k);
            let event = d.sim.jumps.iter().find(|j| j.after == k).map(|j| {
                if j.color_change { "next: COLOUR CHANGE" } else if j.trimmed { "next: TRIM + jump" } else { "next: jump (no trim)" }
            });
            ui.label(format!(
                "stitch {} / {}   colour {}/{}   {} / {}{}",
                k, n, blk + 1, d.sim.block_start.len(),
                fmt_time(d.sim.time[k]), fmt_time(d.sim.total_time()),
                event.map(|e| format!("   {e}")).unwrap_or_default()
            ));
        });
        ui.add_space(2.0);
    }

    fn canvas(&mut self, ui: &mut egui::Ui) {
        let (rect, resp) = ui.allocate_exact_size(ui.available_size(), Sense::click_and_drag());
        let Some(d) = &self.doc else {
            ui.painter().text(rect.center(), egui::Align2::CENTER_CENTER,
                "Drop a PES / DST / EXP / JEF file here", egui::FontId::proportional(20.0), Color32::from_gray(120));
            return;
        };
        let _ = d;
        let fit = |pts: &[[f32; 2]], rect: Rect, margin: f32| -> Camera {
            let (mut x0, mut y0, mut x1, mut y1) = (f32::MAX, f32::MAX, f32::MIN, f32::MIN);
            for p in pts {
                (x0, y0, x1, y1) = (x0.min(p[0]), y0.min(p[1]), x1.max(p[0]), y1.max(p[1]));
            }
            let zoom = ((rect.width() - margin) / (x1 - x0).max(1.0)).min((rect.height() - margin) / (y1 - y0).max(1.0)).max(0.05);
            Camera { center: [(x0 + x1) / 2.0, (y0 + y1) / 2.0], zoom }
        };
        if self.fit_pending || resp.double_clicked() {
            let margin = if self.clean { rect.width().min(rect.height()) * 0.22 } else { 40.0 };
            self.cam = fit(&self.design_corners(), rect, margin);
            self.fit_pending = false;
        }
        if self.fit_item_pending {
            if self.article == Article::Plain {
                self.cam = fit(&self.design_corners(), rect, 40.0);
            } else {
                let b = garment::spec(self.article).bounds;
                self.cam = fit(&[[b[0] - 15.0, b[1] - 15.0], [b[2] + 15.0, b[3] + 15.0]], rect, 30.0);
            }
            self.fit_item_pending = false;
        }
        // pan and zoom about the cursor; in place mode drag moves and scroll resizes the design
        if resp.dragged() {
            let dl = resp.drag_delta();
            if self.place {
                self.stage.x += dl.x / self.cam.zoom;
                self.stage.y -= dl.y / self.cam.zoom;
            } else {
                self.cam.center[0] -= dl.x / self.cam.zoom;
                self.cam.center[1] += dl.y / self.cam.zoom;
            }
        }
        if resp.hovered() {
            let (mut scroll, pinch, hover) = ui.input(|i| (i.smooth_scroll_delta.y, i.zoom_delta(), i.pointer.hover_pos()));
            if self.place && scroll != 0.0 {
                self.stage.scale = (self.stage.scale * (scroll / 400.0).exp()).clamp(0.05, 20.0);
                scroll = 0.0;
            }
            let f = pinch * (scroll / 300.0).exp();
            if (f - 1.0).abs() > 1e-4 {
                if let Some(hp) = hover {
                    let before = self.to_world(rect, hp);
                    self.cam.zoom = (self.cam.zoom * f).clamp(0.05, 400.0);
                    let after = self.to_world(rect, hp);
                    self.cam.center[0] += before[0] - after[0];
                    self.cam.center[1] += before[1] - after[1];
                }
            }
        }
        let d = self.doc.as_ref().unwrap();
        let key = CacheKey {
            cam: self.cam, rect, width: self.width, shade: self.shade, realistic: self.realistic,
            stage: self.stage, hidden: d.hidden.clone(), colors: d.colors.clone(),
        };
        if self.key.as_ref() != Some(&key) {
            self.key = Some(key);
            self.sewn_chunks.clear();
            self.ghost_chunks.clear();
        }
        let n = d.sim.len();
        let k = self.k().min(n);
        let painter = ui.painter_at(rect);
        let mut clicked_issue: Option<usize> = None;
        let cam = self.cam;
        let c = rect.center();
        let world = move |p: [f32; 2]| Pos2::new(c.x + (p[0] - cam.center[0]) * cam.zoom, c.y - (p[1] - cam.center[1]) * cam.zoom);
        let place = self.place_fn();
        let tf = move |p: [f32; 2]| world(place(p));
        self.draw_garment(&painter, world);
        let d = self.doc.as_ref().unwrap();
        let mm_px = cam.zoom * self.stage.scale;
        // +0.5 px: flat meshes are not anti-aliased, so thin threads alias into pinholes
        let wpx = (self.width * mm_px + 0.5).max(1.0);
        let real = match (&self.thread_tex, self.realistic) {
            (Some(t), true) => Some(thread::Real { tex: t.id() }),
            _ => None,
        };
        let build = |from: usize, to: usize, ghost: bool| -> Mesh {
            let mut m = match (&real, ghost) {
                (Some(r), false) => r.mesh(),
                _ => Mesh::default(),
            };
            m.reserve_vertices((to - from) * 12);
            m.reserve_triangles((to - from) * 8);
            for (i, s) in d.sim.segs[from..to].iter().enumerate() {
                if d.hidden[s.block as usize] {
                    continue;
                }
                let col = d.colors[s.block as usize];
                if ghost {
                    push_stitch(&mut m, tf(s.a), tf(s.b), (wpx * 0.6).max(1.0), col.gamma_multiply(0.18), false);
                } else if let Some(r) = &real {
                    // a touch wider: the soft edges would otherwise show fabric between rows
                    r.push(&mut m, tf(s.a), tf(s.b), (self.width * 1.15 * mm_px).max(1.2), mm_px, col, (from + i) as u32);
                } else {
                    push_stitch(&mut m, tf(s.a), tf(s.b), wpx, col, self.shade);
                }
            }
            m
        };
        let n_chunks = n.div_ceil(CHUNK);
        if self.ghost && k < n {
            while self.ghost_chunks.len() < n_chunks {
                let i = self.ghost_chunks.len();
                self.ghost_chunks.push(Arc::new(build(i * CHUNK, ((i + 1) * CHUNK).min(n), true)));
            }
            for m in &self.ghost_chunks[k / CHUNK..] {
                painter.add(Shape::Mesh(m.clone()));
            }
        }
        let full = k / CHUNK;
        while self.sewn_chunks.len() < full {
            let i = self.sewn_chunks.len();
            self.sewn_chunks.push(Arc::new(build(i * CHUNK, (i + 1) * CHUNK, false)));
        }
        for m in &self.sewn_chunks[..full] {
            painter.add(Shape::Mesh(m.clone()));
        }
        if k > full * CHUNK {
            painter.add(Shape::mesh(build(full * CHUNK, k, false)));
        }
        // jump threads so far: red = left untrimmed, grey = trimmed
        if self.jumps {
            for j in d.sim.jumps.iter().take_while(|j| j.after <= k) {
                if j.after == k && k < n {
                    continue; // drawn as the upcoming move below
                }
                let col = if j.trimmed || j.color_change { Color32::from_black_alpha(60) } else { Color32::from_rgb(220, 30, 30) };
                painter.line_segment([tf(j.a), tf(j.b)], Stroke::new(1.0, col));
            }
        }
        // needle and the move it is about to make
        if k < n || self.playing {
            let np = tf(d.sim.needle(k));
            if let Some(j) = d.sim.jumps.iter().find(|j| j.after == k) {
                let col = if j.trimmed || j.color_change { Color32::from_rgb(60, 60, 60) } else { Color32::from_rgb(220, 30, 30) };
                dashed(&painter, tf(j.a), tf(j.b), col);
            }
            painter.circle_stroke(np, 6.0, Stroke::new(1.5, Color32::from_rgb(220, 40, 40)));
            painter.line_segment([np - Vec2::new(10.0, 0.0), np + Vec2::new(10.0, 0.0)], Stroke::new(1.0, Color32::from_rgb(220, 40, 40)));
            painter.line_segment([np - Vec2::new(0.0, 10.0), np + Vec2::new(0.0, 10.0)], Stroke::new(1.0, Color32::from_rgb(220, 40, 40)));
        }
        if self.density_map {
            let dm = &d.report.density;
            let mut m = Mesh::default();
            for iy in 0..dm.ny {
                for ix in 0..dm.nx {
                    let v = dm.grid[iy * dm.nx + ix];
                    if v < 1.8 {
                        continue;
                    }
                    let col = if v >= analysis::VERY_DENSE {
                        Color32::from_rgba_unmultiplied(200, 20, 20, 170)
                    } else if v >= analysis::DENSE {
                        Color32::from_rgba_unmultiplied(235, 110, 30, 150)
                    } else if v >= 2.5 {
                        Color32::from_rgba_unmultiplied(245, 205, 60, 110)
                    } else {
                        Color32::from_rgba_unmultiplied(120, 200, 110, 60)
                    };
                    let (x0, y0) = (dm.x0 + ix as f32 * dm.cell, dm.y0 + iy as f32 * dm.cell);
                    let q = [tf([x0, y0]), tf([x0 + dm.cell, y0]), tf([x0 + dm.cell, y0 + dm.cell]), tf([x0, y0 + dm.cell])];
                    let i = m.vertices.len() as u32;
                    for p in q {
                        m.colored_vertex(p, col.gamma_multiply(1.0));
                    }
                    m.add_triangle(i, i + 1, i + 2);
                    m.add_triangle(i, i + 2, i + 3);
                }
            }
            painter.add(Shape::mesh(m));
        }
        if let Some((name, hw, hh)) = self.hoop_spec() {
            let b = d.sim.bounds;
            let (cx, cy) = ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0);
            let q = [[cx - hw / 2.0, cy - hh / 2.0], [cx + hw / 2.0, cy - hh / 2.0], [cx + hw / 2.0, cy + hh / 2.0], [cx - hw / 2.0, cy + hh / 2.0]];
            let pts: Vec<Pos2> = q.iter().map(|&p| tf(p)).collect();
            let (w, h) = d.sim.size();
            let col = if w > hw || h > hh { Color32::from_rgb(214, 39, 40) } else { Color32::from_gray(110) };
            for i in 0..4 {
                dashed(&painter, pts[i], pts[(i + 1) % 4], col);
            }
            painter.text(pts[3] + Vec2::new(4.0, 4.0), egui::Align2::LEFT_TOP, format!("hoop {name}"), egui::FontId::proportional(12.0), col);
        }
        if self.problems {
            let hover = ui.input(|i| i.pointer.hover_pos());
            let mut tip = None;
            for (i, is) in d.report.issues.iter().enumerate() {
                let p = tf(is.at);
                let col = sev_color(is.sev);
                let sel = self.selected == Some(i);
                let r = if sel { 13.0 } else { 10.0 };
                painter.circle_filled(p, r + 4.0, col.gamma_multiply(0.22));
                painter.circle_filled(p, r, col);
                painter.circle_stroke(p, r, Stroke::new(if sel { 3.0 } else { 1.5 }, Color32::WHITE));
                painter.text(p, egui::Align2::CENTER_CENTER, format!("{}", i + 1), egui::FontId::proportional(11.0), Color32::WHITE);
                if hover.is_some_and(|h| (h - p).length() < r + 2.0) {
                    tip = Some((i, p));
                }
            }
            if let Some((i, p)) = tip {
                let is = &d.report.issues[i];
                let text = format!("{}. {}\n{}\nFix: {}", i + 1, is.kind, is.detail, is.fix);
                let galley = painter.layout(text, egui::FontId::proportional(13.0), Color32::from_gray(20), 320.0);
                let at = p + Vec2::new(16.0, -8.0);
                let bg = Rect::from_min_size(at, galley.size()).expand(6.0);
                painter.rect_filled(bg, 4.0, Color32::from_white_alpha(240));
                painter.rect_stroke(bg, 4.0, Stroke::new(1.0, sev_color(is.sev)), egui::StrokeKind::Inside);
                painter.galley(at, galley, Color32::from_gray(20));
                if resp.clicked() {
                    clicked_issue = Some(i);
                }
            }
        }
        if self.place {
            let pts: Vec<Pos2> = self.design_corners().into_iter().map(world).collect();
            for i in 0..4 {
                dashed(&painter, pts[i], pts[(i + 1) % 4], Color32::from_rgb(30, 120, 220));
            }
            let (w, h) = d.sim.size();
            painter.text(pts[3] + Vec2::new(0.0, -4.0), egui::Align2::LEFT_BOTTOM,
                format!("{:.0} x {:.0} mm", w * self.stage.scale, h * self.stage.scale),
                egui::FontId::proportional(13.0), Color32::from_rgb(30, 120, 220));
        }
        if self.clean {
            return;
        }
        // scale bar
        let mm = [1.0f32, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0].into_iter().find(|v| v * cam.zoom > 60.0).unwrap_or(100.0);
        let y = rect.bottom() - 16.0;
        let x0 = rect.left() + 16.0;
        painter.rect_filled(Rect::from_min_max(Pos2::new(x0 - 8.0, y - 26.0), Pos2::new(x0 + mm * cam.zoom + 8.0, y + 8.0)),
            4.0, Color32::from_white_alpha(200));
        painter.line_segment([Pos2::new(x0, y), Pos2::new(x0 + mm * cam.zoom, y)], Stroke::new(3.0, Color32::from_gray(40)));
        painter.text(Pos2::new(x0, y - 6.0), egui::Align2::LEFT_BOTTOM, format!("{mm} mm"), egui::FontId::proportional(13.0), Color32::from_gray(40));
        if let Some(i) = clicked_issue {
            self.go_to_issue(i);
        }
    }

    /// The garment image as one textured quad, then the fabric weave over its outline.
    fn draw_garment(&self, painter: &egui::Painter, world: impl Fn([f32; 2]) -> Pos2) {
        let fabric = self.article.fabric();
        let tile = self.tiles.iter().find(|(f, ..)| *f == fabric);
        let tint = self.color();
        if self.article == Article::Plain {
            // plain fabric: weave over the visible canvas
            if let Some((_, t, mm)) = tile {
                let r = painter.clip_rect();
                let px = mm * self.cam.zoom;
                if px >= 3.0 {
                    let mut m = Mesh::with_texture(t.id());
                    let uv = |p: Pos2| Pos2::new(p.x / px, p.y / px);
                    m.add_rect_with_uv(r, Rect::from_min_max(uv(r.min), uv(r.max)), Color32::from_white_alpha(255));
                    painter.add(Shape::mesh(m));
                }
            }
            return;
        }
        let Some(g) = &self.garment else { return };
        if g.article != self.article {
            return;
        }
        let [x0, y0, x1, y1] = g.rect;
        let r = Rect::from_min_max(world([x0, y1]), world([x1, y0]));
        let mut m = Mesh::with_texture(g.tex.id());
        let col = if g.color.is_some() { Color32::WHITE } else { tint };
        m.add_rect_with_uv(r, Rect::from_min_max(Pos2::ZERO, Pos2::new(1.0, 1.0)), col);
        painter.add(Shape::mesh(m));
        if let Some((_, t, mm)) = tile {
            let px = mm * self.cam.zoom;
            if px >= 3.0 {
                let fade = ((px - 3.0) / 6.0).clamp(0.0, 1.0);
                let a = (fade * 255.0) as u8;
                let mut m = Mesh::with_texture(t.id());
                for tri in &g.tris {
                    let i = m.vertices.len() as u32;
                    for p in tri {
                        m.vertices.push(egui::epaint::Vertex {
                            pos: world(*p),
                            uv: Pos2::new(p[0] / mm, -p[1] / mm),
                            color: Color32::from_white_alpha(a),
                        });
                    }
                    m.add_triangle(i, i + 1, i + 2);
                }
                painter.add(Shape::mesh(m));
            }
        }
    }

    fn to_world(&self, rect: Rect, p: Pos2) -> [f32; 2] {
        let c = rect.center();
        [self.cam.center[0] + (p.x - c.x) / self.cam.zoom, self.cam.center[1] - (p.y - c.y) / self.cam.zoom]
    }
}

fn dashed(p: &egui::Painter, a: Pos2, b: Pos2, col: Color32) {
    let len = (b - a).length();
    let n = (len / 6.0).ceil().max(1.0) as usize;
    for i in (0..n).step_by(2) {
        let t0 = i as f32 / n as f32;
        let t1 = ((i + 1) as f32 / n as f32).min(1.0);
        p.line_segment([a + (b - a) * t0, a + (b - a) * t1], Stroke::new(1.5, col));
    }
}
