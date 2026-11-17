"""2D art: icons, 9-slice frames and animated sprite sheets, packed into an atlas.

Cinder 0.1.1 has no sprite renderer and its UI draws no images, so this is **built ahead**:
the deliverable is a PNG atlas and a JSON that says where every frame is, in the form most
engines and a future `cinder.ui` image node can read. To prove the art in the engine today,
the build also writes `<name>_quads.glb`: one flat quad per frame, unlit (the art is the
emissive map over a black base colour) and alpha-masked, and puts it through the model ladder.
Cinder 0.1.1 draws masked and blended materials opaque (a forward-shader bug), so those quads
show a black square behind the art until the engine is fixed; the atlas itself is correct.

    c = Canvas(64)
    c.circle((32, 32), 26, fill=(220, 40, 50), outline=(40, 10, 14), width=4)
    sheet = SpriteSheet({"heart": c.image()})

Images are straight (not premultiplied) RGBA floats in 0..1, row 0 at the top.
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw

from .. import outputs
from .checks import Check, _name_ok
from .model import Material, Mesh, Model
from .render import BAD, BG, INK, MUTED, OK, _font
from .texture import to_u8


class Canvas:
    """Anti-aliased vector drawing: shapes are drawn at `scale` times the size and averaged
    down. Coordinates and widths are in final pixels; colours are 0..255 RGB or RGBA."""

    def __init__(self, width, height=None, scale=4):
        self.w, self.h, self.s = width, height or width, scale
        self.img = Image.new("RGBA", (self.w * scale, self.h * scale), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def _p(self, pts):
        return [(x * self.s, y * self.s) for x, y in pts]

    @staticmethod
    def _c(col):
        return None if col is None else tuple(int(v) for v in (tuple(col) + (255,))[:4])

    def polygon(self, pts, fill=None, outline=None, width=0):
        self.d.polygon(self._p(pts), fill=self._c(fill))
        if outline is not None and width:
            self.d.line(self._p(list(pts) + [pts[0], pts[1]]), fill=self._c(outline), width=int(width * self.s), joint="curve")
        return self

    def circle(self, centre, r, fill=None, outline=None, width=0):
        return self.ellipse(centre, r, r, fill, outline, width)

    def ellipse(self, centre, rx, ry, fill=None, outline=None, width=0):
        (x, y), s = centre, self.s
        self.d.ellipse([(x - rx) * s, (y - ry) * s, (x + rx) * s, (y + ry) * s], fill=self._c(fill),
                       outline=self._c(outline), width=int(width * s))
        return self

    def rect(self, box, radius=0, fill=None, outline=None, width=0):
        x0, y0, x1, y1 = (v * self.s for v in box)
        self.d.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=radius * self.s, fill=self._c(fill),
                                 outline=self._c(outline), width=int(width * self.s))
        return self

    def line(self, pts, fill, width=2):
        self.d.line(self._p(pts), fill=self._c(fill), width=int(width * self.s), joint="curve")
        return self

    def image(self):
        """The drawing at its final size, as straight-alpha RGBA floats."""
        a = np.asarray(self.img, float) / 255
        s = self.s
        a = a.reshape(self.h, s, self.w, s, 4)
        alpha = a[..., 3:4]
        cover = alpha.mean((1, 3))
        rgb = (a[..., :3] * alpha).mean((1, 3)) / np.maximum(cover, 1e-6)      # average colour by coverage
        return np.concatenate([np.clip(rgb, 0, 1), cover], -1)


@dataclass
class SpriteSheet:
    """Named frames, and optionally animations (name -> dict(frames=[names], fps=, loop=)) and
    9-slice borders (frame name -> (left, top, right, bottom) pixels that do not stretch)."""
    frames: dict
    animations: dict = field(default_factory=dict)
    slices: dict = field(default_factory=dict)
    padding: int = 2                  # transparent pixels kept between frames against bleed
    pixels_per_metre: float = 128.0   # size of the proof quads


def pack(sheet):
    """Shelf-pack the frames into the smallest power-of-two square. Returns (atlas RGBA,
    {name: dict(x, y, w, h)})."""
    pad = sheet.padding
    order = sorted(sheet.frames, key=lambda k: (-sheet.frames[k].shape[0], k))
    size = 16
    while True:
        x = y = pad
        row = 0
        rects, ok = {}, True
        for name in order:
            h, w = sheet.frames[name].shape[:2]
            if x + w + pad > size:
                x, y, row = pad, y + row + pad, 0
            if w + 2 * pad > size or y + h + pad > size:
                ok = False
                break
            rects[name] = dict(x=x, y=y, w=w, h=h)
            x += w + pad
            row = max(row, h)
        if ok:
            break
        size *= 2
    atlas = np.zeros((size, size, 4))
    for name, r in rects.items():
        atlas[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]] = sheet.frames[name]
    return atlas, {k: rects[k] for k in sheet.frames}


def quads(sheet, atlas, rects):
    """One upright quad per frame in a row, facing +Z, unlit and alpha-masked: the art in 3D."""
    n = atlas.shape[0]
    ppm = sheet.pixels_per_metre
    widths = [rects[k]["w"] / ppm for k in sheet.frames]
    gap = 0.12
    x = -(sum(widths) + gap * (len(widths) - 1)) / 2
    vs, fs, uvs = [], [], []
    for name, w in zip(sheet.frames, widths):
        r = rects[name]
        h = r["h"] / ppm
        i = len(vs)
        vs += [(x, 0, 0), (x + w, 0, 0), (x + w, h, 0), (x, h, 0)]
        u0, v0, u1, v1 = r["x"] / n, r["y"] / n, (r["x"] + r["w"]) / n, (r["y"] + r["h"]) / n
        uvs += [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        fs += [(i, i + 1, i + 2), (i, i + 2, i + 3)]
        x += w + gap
    mesh = Mesh(vs, fs, np.tile([0.0, 0.0, 1.0], (len(vs), 1)), uvs)
    rgb = atlas[..., :3] * (atlas[..., 3:4] > 0)
    mat = Material("sprite_unlit", color=(0.0, 0.0, 0.0, 1.0), roughness=1.0, base=atlas, emission=rgb,
                   emissive=(1.0, 1.0, 1.0), alpha="mask", alpha_cutoff=0.5, double_sided=True)
    return Model((mesh, mat))


# ---------------------------------------------------------------- checks

def frames(*names):
    """The sheet has exactly these frames."""
    def fn(ctx):
        got = list(ctx.sheet.frames)
        return sorted(got) == sorted(names), f"{len(got)} frames: {', '.join(got)}"
    return Check("frames", fn)


def frame_size(w, h=None):
    """Every frame is w x h pixels."""
    h = h or w

    def fn(ctx):
        odd = {k: v.shape[1::-1] for k, v in ctx.sheet.frames.items() if v.shape[:2] != (h, w)}
        return not odd, f"every frame is {w} x {h} px" if not odd else f"not {w} x {h}: {odd}"
    return Check("frame size", fn)


def animation(name, count, fps=None):
    """An animation of `count` frames exists (at `fps`)."""
    def fn(ctx):
        a = ctx.sheet.animations.get(name)
        if a is None:
            return False, f"no animation '{name}'"
        ok = len(a["frames"]) == count and (fps is None or a.get("fps") == fps)
        return ok, f"'{name}': {len(a['frames'])} frames at {a.get('fps')} fps, loop {a.get('loop', True)}"
    return Check(f"animation {name}", fn)


def nine_slice(name, min_centre=4):
    """A frame has 9-slice borders that leave a stretchable centre."""
    def fn(ctx):
        b = ctx.sheet.slices.get(name)
        if b is None:
            return False, f"'{name}' has no 9-slice borders"
        h, w = ctx.sheet.frames[name].shape[:2]
        cw, chh = w - b[0] - b[2], h - b[1] - b[3]
        return cw >= min_centre and chh >= min_centre, f"'{name}' {w} x {h}, borders {tuple(b)}, centre {cw} x {chh} px"
    return Check(f"9-slice {name}", fn)


def custom(name, fn):
    """fn(ctx) -> (ok, detail); ctx.sheet, ctx.atlas, ctx.rects, ctx.params."""
    return Check(name, fn)


def _atlas(ctx):
    n = ctx.atlas.shape[0]
    bad = []
    if n & (n - 1) or ctx.atlas.shape[0] != ctx.atlas.shape[1]:
        bad.append(f"atlas {ctx.atlas.shape[1]} x {n} is not a power-of-two square")
    if ctx.sheet.padding < 2:
        bad.append("padding under 2 px: neighbouring frames bleed when the atlas is filtered or mipped")
    rs = list(ctx.rects.items())
    for i, (a, ra) in enumerate(rs):
        if ra["x"] < 0 or ra["y"] < 0 or ra["x"] + ra["w"] > n or ra["y"] + ra["h"] > n:
            bad.append(f"{a} lies outside the atlas")
        for b, rb in rs[i + 1:]:
            p = ctx.sheet.padding
            if (ra["x"] < rb["x"] + rb["w"] + p and rb["x"] < ra["x"] + ra["w"] + p
                    and ra["y"] < rb["y"] + rb["h"] + p and rb["y"] < ra["y"] + ra["h"] + p):
                bad.append(f"{a} and {b} are closer than the padding")
    return not bad, "; ".join(bad) or f"{n} x {n} atlas, {len(rs)} frames, {ctx.sheet.padding} px apart"


def _frames(ctx):
    bad = []
    for name, img in ctx.sheet.frames.items():
        if not __import__("re").fullmatch(r"[a-z][a-z0-9_]*", name):
            bad.append(f"frame name '{name}' is not snake_case")
        if img.ndim != 3 or img.shape[2] != 4:
            bad.append(f"{name}: not RGBA")
            continue
        a = img[..., 3]
        if a.max() < 0.99:
            bad.append(f"{name}: nothing in it is opaque")
        if (a > 0.5).mean() < 0.05:
            bad.append(f"{name}: under 5 % of it is drawn")
        if not np.isfinite(img).all() or img.min() < 0 or img.max() > 1:
            bad.append(f"{name}: values outside 0..1")
    for name, a in ctx.sheet.animations.items():
        missing = [f for f in a["frames"] if f not in ctx.sheet.frames]
        if missing:
            bad.append(f"animation {name} names frames that do not exist: {missing}")
        if a.get("fps", 0) <= 0:
            bad.append(f"animation {name} has no fps")
    for name in ctx.sheet.slices:
        if name not in ctx.sheet.frames:
            bad.append(f"9-slice borders for a frame that does not exist: {name}")
    return not bad, "; ".join(bad) or "RGBA, each frame has opaque art, animations and slices name real frames"


def _readback(ctx):
    with Image.open(ctx.png) as im:
        got = np.asarray(im.convert("RGBA"), float) / 255
    if got.shape != ctx.atlas.shape:
        return False, f"PNG is {got.shape[1]} x {got.shape[0]}, built {ctx.atlas.shape[1]} x {ctx.atlas.shape[0]}"
    err = np.abs(got - np.asarray(to_u8(ctx.atlas), float) / 255).max()
    data = json.loads(Path(ctx.json).read_text(encoding="utf-8"))
    same = data["frames"] == ctx.rects and data["size"] == [ctx.atlas.shape[1], ctx.atlas.shape[0]]
    return bool(err < 1e-6 and same), ("PNG and JSON read back as built" if err < 1e-6 and same
                                       else "the files differ from what was built")


def static_checks():
    return [Check("name", _name_ok), Check("atlas", _atlas), Check("frames valid", _frames),
            Check("readback", _readback)]


# ---------------------------------------------------------------- build

def render_sprite(path, sheet, atlas, rects, shot, title, lines, results, ready):
    W = 1600
    tile = 440
    sheet_img = Image.new("RGB", (W, 60 + tile + 40 + 18 * (len(lines) + len(results) + 1)), BG)
    d = ImageDraw.Draw(sheet_img)
    d.text((16, 14), title, fill=INK, font=_font(26))
    d.text((W - 190, 16), "ready YES" if ready else "ready NO", fill=OK if ready else BAD, font=_font(24))
    n = atlas.shape[0]
    k = max(1, tile // n)
    checker = np.indices((n * k, n * k)).sum(0) // 8 % 2
    back = np.where(checker[..., None] == 0, 0.32, 0.4) * np.ones(3)
    big = np.kron(atlas, np.ones((k, k, 1)))
    comp = back * (1 - big[..., 3:4]) + big[..., :3] * big[..., 3:4]
    im = Image.fromarray(to_u8(comp))
    dd = ImageDraw.Draw(im)
    for name, r in rects.items():
        dd.rectangle([r["x"] * k, r["y"] * k, (r["x"] + r["w"]) * k - 1, (r["y"] + r["h"]) * k - 1], outline=(120, 200, 255))
        b = sheet.slices.get(name)
        if b:
            for x in (r["x"] + b[0], r["x"] + r["w"] - b[2]):
                dd.line([(x * k, r["y"] * k), (x * k, (r["y"] + r["h"]) * k)], fill=(255, 200, 80))
            for y in (r["y"] + b[1], r["y"] + r["h"] - b[3]):
                dd.line([(r["x"] * k, y * k), ((r["x"] + r["w"]) * k, y * k)], fill=(255, 200, 80))
    sheet_img.paste(im.resize((tile, tile), Image.NEAREST if k * n <= tile else Image.LANCZOS), (10, 60))
    d.text((10, 60 + tile + 4), f"atlas {n} x {n}, frames outlined" + (", 9-slice borders in yellow" if sheet.slices else ""),
           fill=MUTED, font=_font(13))
    if shot:
        with Image.open(shot) as s:
            s = s.convert("RGB")
            w = int(s.width * tile / s.height)
            sheet_img.paste(s.resize((w, tile), Image.LANCZOS), (tile + 30, 60))
        d.text((tile + 30, 60 + tile + 4), "in Cinder: one unlit quad per frame (black where transparent: the engine "
               "ignores alpha mask today)", fill=MUTED, font=_font(13))
    ty = 60 + tile + 28
    for line in lines:
        d.text((12, ty), line, fill=INK, font=_font(13))
        ty += 18
    ty += 4
    for r in results:
        d.text((12, ty), ("PASS  " if r["ok"] else "FAIL  ") + r["name"] + ": " + r["detail"][:170],
               fill=OK if r["ok"] else BAD, font=_font(13))
        ty += 18
    sheet_img.save(path)


def build_sprite(path, mod, params, out_root, use_engine=True, quiet=False):
    from . import build as B
    from . import engine as E
    from . import gltf
    t0 = time.time()
    path = Path(path)
    name = path.stem
    p = SimpleNamespace(**params)
    sheet = mod.build(p)
    if not isinstance(sheet, SpriteSheet):
        raise SystemExit('a KIND = "sprite" script must return cadkit.game.sprite.SpriteSheet from build(p)')
    out = Path(out_root) / name
    out.mkdir(parents=True, exist_ok=True)
    atlas, rects = pack(sheet)
    png, js = out / f"{name}.png", out / f"{name}.json"
    Image.fromarray(to_u8(atlas)).save(png, optimize=True)
    doc = dict(schema="cadkit-sprites/1", image=png.name, size=[atlas.shape[1], atlas.shape[0]],
               padding=sheet.padding, alpha="straight", origin="top-left", frames=rects,
               animations=sheet.animations,
               slices={k: dict(left=v[0], top=v[1], right=v[2], bottom=v[3]) for k, v in sheet.slices.items()})
    js.write_text(json.dumps(doc, indent=1), encoding="utf-8")

    ctx = SimpleNamespace(sheet=sheet, atlas=atlas, rects=rects, params=params, name=name, png=png, json=js)
    spec = mod.checks(p) if callable(getattr(mod, "checks", None)) else []
    results = [c.run(ctx) for c in static_checks() + list(spec)]
    blockers = [f"check {r['name']}: {r['detail']}" for r in results if not r["ok"]]
    steps = dict(static=dict(ok=not blockers, checks=results))

    # the art in the engine: unlit quads through the model ladder's cook, load and visibility steps
    model = quads(sheet, atlas, rects)
    glb = out / f"{name}_quads.glb"
    gltf.write_glb(model, glb, f"{name}_quads")
    eng = E.find() if use_engine else None
    shot = None
    if eng is None:
        blockers.append("not verified in Cinder: " + ("skipped (--no-engine)" if not use_engine else
                        "no engine found; set CAD_CINDER to a Cinder package"))
    else:
        stage = out / "staging"
        stage.mkdir(exist_ok=True)
        cooked = out / "cooked"
        __import__("shutil").rmtree(cooked, ignore_errors=True)
        ck = eng.cook(cooked, glb)
        seen = B._visibility(eng, glb, model.bounds, stage)
        lo, hi = model.bounds
        world = stage / "front.world"
        world.write_text(E.staging_world(glb, model.bounds, 8, reference=False, title=name,
                                         radius=max(0.62 * (hi[1] - lo[1]), 0.32 * (hi[0] - lo[0]))), encoding="utf-8")
        front = out / f"{name}_in_engine.png"
        rep = eng.play(world, frames=3, screenshot=front, width=1280, height=640)
        shot = front if rep.get("ok") and front.exists() else None
        __import__("shutil").rmtree(stage, ignore_errors=True)
        steps["engine"] = dict(ok=bool(ck["ok"] and rep.get("ok") and seen >= 0.002 and not rep.get("run", {}).get("gpu_errors")),
                               cook=ck["outputs"], visible_share=round(seen, 4),
                               gpu_errors=rep.get("run", {}).get("gpu_errors"),
                               method="one unlit alpha-masked quad per frame, cooked and drawn headless")
        if not ck["ok"]:
            blockers.append("engine: cinder-cook rejected the quads: " + ck["text"][-200:])
        if not rep.get("ok") or rep.get("run", {}).get("gpu_errors"):
            blockers.append("engine: the quads did not load cleanly: " + str(rep.get("error", "GPU errors")))
        if seen < 0.002:
            blockers.append("engine: nothing was drawn (the frame with the quads equals the frame without)")
    ready = not blockers
    n = atlas.shape[0]
    used = sum(r["w"] * r["h"] for r in rects.values()) / (n * n)
    lines = [f"{name}  (sprite)  {getattr(mod, 'DESCRIPTION', '')}",
             f"atlas    {n} x {n} px, {len(rects)} frames, {used:.0%} used, {png.stat().st_size / 1024:.0f} kB",
             "frames   " + ", ".join(f"{k} {r['w']}x{r['h']}" for k, r in list(rects.items())[:10])
             + (" ..." if len(rects) > 10 else "")]
    if sheet.animations:
        lines.append("anims    " + ", ".join(f"{k}: {len(a['frames'])} frames at {a.get('fps')} fps"
                                              for k, a in sheet.animations.items()))
    if sheet.slices:
        lines.append("9-slice  " + ", ".join(f"{k} {tuple(v)}" for k, v in sheet.slices.items()))
    if "engine" in steps:
        e = steps["engine"]
        lines.append(f"engine   Cinder {eng.version}: quads cooked ({e['cook'].get('ktx2', 0)} .ktx2), drawn with "
                     f"{e['gpu_errors']} GPU errors, covering {e['visible_share']:.1%} of a frame")
        lines.append("note     built ahead: Cinder has no sprite renderer or UI image node; the atlas + JSON are the "
                     "deliverable, the quads are the proof")
        lines.append("alpha    Cinder 0.1.1's colour pass ignores alpha mask and blend (its forward shader reads the "
                     "alpha mode with u32() where the material wrote integer bits), so each quad shows its black "
                     "base where the art is transparent. The GLB asks for MASK and is right once that is fixed")
    for r in results:
        lines.append(f"check    {'PASS' if r['ok'] else 'FAIL'}  {r['name']}: {r['detail']}")
    lines += ["BLOCKER  " + b for b in blockers]
    lines.append(f"ready    {'YES' if ready else 'NO'}")
    preview = out / f"{name}_preview.png"
    render_sprite(preview, sheet, atlas, rects, shot, f"{name}: {getattr(mod, 'DESCRIPTION', '')}",
                  [l for l in lines if not l.startswith(("check", "BLOCKER", "ready"))], results, ready)
    build = dict(schema="cadkit-game-build/1", name=name, kind="sprite", description=getattr(mod, "DESCRIPTION", ""),
                 params=params, ready=ready, blockers=blockers,
                 stats=dict(atlas=[n, n], frames=rects, animations=sheet.animations,
                            slices={k: list(v) for k, v in sheet.slices.items()}, png_bytes=png.stat().st_size),
                 files=dict(png=png.name, json=js.name, quads=glb.name, preview=preview.name, sha256=outputs.sha256(png)),
                 product=dict(getattr(mod, "PRODUCT", {}) or {}), source_sha256=outputs.sha256(path),
                 engine=eng.info() if eng else None, steps=steps, report=lines, built_at=outputs.now_iso(),
                 seconds=round(time.time() - t0, 1), git=outputs.git_info())
    outputs.save_json(out / "build.json", build)
    outputs.save_json(out / "readiness.json", dict(ready=ready, blockers=blockers, steps=steps))
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    build["out"] = str(out)
    if not quiet:
        print("\n".join(lines))
        print(f"preview  {preview}")
    return build
