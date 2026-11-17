"""Game UI for Cinder: a tree of nodes and a theme, written as the engine's own UI document.

`cinder.ui` is a tree of panels, labels, buttons, toggles and sliders. `Ui.to_text` in the
engine writes it as a `cinder-scene 1` document and `Ui.from_text` reads it back; this module
writes and reads the same text, with the same constructors and the same defaults, so a game
loads an interface with one call instead of building it in code:

    ui = Ui(Theme(accent=(232, 148, 56, 255)))
    hud = ui.root("top_left", "hud", offset=(16, 16))
    ui.label(hud, "GEMS 0 / 3", name="gems")
    menu = ui.root("centre", "pause")
    ui.button(menu, "Resume", name="resume")

A `KIND = "ui"` script returns `UiSet(ui)`. The build proves it in the engine with
cinder-probe: the engine parses the document, lays it out, draws it and writes it back, and
the build compares what came back with what was written, field by field.

Not in Cinder 0.1.1: images, text fields, scrolling, wrapping. A theme is not part of the
document (the engine does not serialise it): node colours travel in the document, and the
theme's hover, pressed, accent and focus colours are set by the Mojo lines in <name>.mojo.
"""
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

from .. import outputs
from . import engine as E
from .checks import Check, _name_ok
from .render import BAD, BG, INK, MUTED, OK, _font

ANCHORS = dict(top_left=0, top=1, top_right=2, left=3, centre=4, right=5, bottom_left=6, bottom=7, bottom_right=8)
ALIGN = dict(start=0, centre=1, end=2, stretch=3)
KINDS = ("panel", "label", "button", "toggle", "slider")
FRAME = (1280, 720)                                   # the probe's frame; lay interfaces out for it
FIELDS = ("parent", "name", "text", "visible", "enabled", "row", "align", "padding", "gap", "min_size",
          "anchor", "offset", "background", "text_color", "font_size", "checked", "range")


@dataclass
class Theme:
    """cinder.ui UiTheme, with the engine's defaults. Colours are 8-bit sRGB with straight alpha."""
    font_size: int = 18
    text: tuple = (236, 236, 240, 255)
    text_disabled: tuple = (130, 130, 138, 255)
    panel: tuple = (18, 20, 28, 224)
    control: tuple = (52, 58, 76, 255)
    control_hot: tuple = (72, 82, 108, 255)
    control_active: tuple = (96, 110, 148, 255)
    accent: tuple = (232, 148, 56, 255)
    focus: tuple = (255, 214, 120, 255)
    padding: float = 10.0
    gap: float = 6.0

    def mojo(self, target="app.ui.theme"):
        """Mojo lines that set a Ui's theme to this one."""
        lines = [f"{target}.font_size = {self.font_size}"]
        for name in ("text", "text_disabled", "panel", "control", "control_hot", "control_active", "accent", "focus"):
            r, g, b, a = (int(x) for x in getattr(self, name))
            lines.append(f"{target}.{name} = UiColor.rgba({r}, {g}, {b}, {a})")
        lines += [f"{target}.padding = {float(self.padding)}", f"{target}.gap = {float(self.gap)}"]
        return lines


def _node(kind, parent, theme):
    """A node as the engine's Ui._add leaves it."""
    return dict(kind=kind, parent=parent, name="", text="", visible=True, enabled=True, row=False, align=0,
                padding=0.0, gap=float(theme.gap), min_size=[0.0, 0.0], anchor=0, offset=[0.0, 0.0],
                background=[0.0, 0.0, 0.0, 0.0], text_color=[float(c) for c in theme.text],
                font_size=int(theme.font_size), checked=False, range=[0.0, 0.0, 1.0, 0.05])


class Ui:
    """The tree. Constructors mirror cinder.ui.Ui and return a node id; `ui[id]` is the node's
    dict of fields, which may be edited directly (as `Ui.nodes[id]` is in Mojo)."""

    def __init__(self, theme=None):
        self.theme = theme or Theme()
        self.nodes = []

    def __getitem__(self, i):
        return self.nodes[i]

    def _add(self, kind, parent, **fields):
        n = _node(kind, parent, self.theme)
        for k, v in fields.items():
            if v is not None:
                n[k] = [float(x) for x in v] if isinstance(v, (tuple, list)) else v
        self.nodes.append(n)
        return len(self.nodes) - 1

    def root(self, anchor="top_left", name="", offset=(0, 0), row=False, **fields):
        """A panel placed against the frame at one of nine anchors, with the theme's background
        and padding. Its children run in a column (or a row). Any node field may be overridden."""
        d = dict(anchor=ANCHORS[anchor], name=name, offset=offset, row=row, align=ALIGN["centre"] if row else 0,
                 background=self.theme.panel, padding=float(self.theme.padding))
        return self._add("panel", -1, **{**d, **fields})

    def panel(self, parent, row=False, name="", **fields):
        """A transparent container; row=True runs its children left to right, centred."""
        d = dict(row=row, align=ALIGN["centre"] if row else 0, name=name)
        return self._add("panel", parent, **{**d, **fields})

    def label(self, parent, text, name="", size=None, color=None, **fields):
        d = dict(text=text, name=name, font_size=size, text_color=color)
        return self._add("label", parent, **{**d, **fields})

    def button(self, parent, text, name="", **fields):
        d = dict(text=text, name=name, background=self.theme.control, padding=float(self.theme.padding))
        return self._add("button", parent, **{**d, **fields})

    def toggle(self, parent, text, checked=False, name="", **fields):
        d = dict(text=text, checked=checked, name=name, background=self.theme.control)
        return self._add("toggle", parent, **{**d, **fields})

    def slider(self, parent, text, value, lo=0.0, hi=1.0, name="", **fields):
        v = min(max(float(value), lo), hi)
        d = dict(text=text, name=name, background=self.theme.control, range=[v, float(lo), float(hi), (hi - lo) / 20.0])
        return self._add("slider", parent, **{**d, **fields})

    def find(self, name):
        return next(i for i, n in enumerate(self.nodes) if n["name"] == name)

    # ---- the engine's document

    def order(self):
        """Node ids in the order the engine writes them: each root, then everything below it,
        a parent before its children, children in their order."""
        kids = {}
        for i, n in enumerate(self.nodes):
            kids.setdefault(n["parent"], []).append(i)
        out = []

        def walk(i):
            out.append(i)
            for c in kids.get(i, []):
                walk(c)
        for r in kids.get(-1, []):
            walk(r)
        return out

    def to_text(self):
        order = self.order()
        index = {old: new for new, old in enumerate(order)}
        lines = ["cinder-scene 1"]
        for new, old in enumerate(order):
            n = self.nodes[old]
            parent = index[n["parent"]] if n["parent"] >= 0 else -1
            lines.append(f"entity {new}")
            lines.append("  " + n["kind"] + " " + " ".join(
                f"{k}={_write(k, parent if k == 'parent' else n[k])}" for k in FIELDS))
        return "\n".join(lines) + "\n"

    @staticmethod
    def from_text(text, theme=None):
        """Parse a UI document (ids are entity indices, as in the engine)."""
        ui = Ui(theme)
        lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        if not lines or lines[0].strip() != "cinder-scene 1":
            raise ValueError("not a cinder-scene 1 document")
        for ln in lines[1:]:
            s = ln.strip()
            if s.startswith("entity "):
                continue
            kind, _, rest = s.partition(" ")
            if kind not in KINDS:
                raise ValueError(f"unknown UI node kind '{kind}'")
            n = _node(kind, -1, ui.theme)
            for key, raw in re.findall(r'(\w+)=("(?:[^"\\]|\\.)*"|\[[^\]]*\]|\S+)', rest):
                n[key] = _read(raw)
            ui.nodes.append(n)
        return ui


def _write(key, v):
    if key == "parent":
        return f"#{v}"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(repr(float(x)) for x in v) + "]"
    if isinstance(v, float):
        return repr(v)
    return str(int(v))


def _read(raw):
    if raw.startswith('"'):
        return raw[1:-1]
    if raw.startswith("#"):
        return int(raw[1:])
    if raw.startswith("["):
        return [float(x) for x in raw[1:-1].split(",") if x.strip()]
    if raw in ("true", "false"):
        return raw == "true"
    return float(raw) if ("." in raw or "e" in raw.lower()) else int(raw)


def same(a, b, tol=1e-4):
    """Are two parsed documents the same tree? Returns (equal, first difference)."""
    if len(a.nodes) != len(b.nodes):
        return False, f"{len(a.nodes)} nodes against {len(b.nodes)}"
    for i, (x, y) in enumerate(zip(a.nodes, b.nodes)):
        for k in ("kind",) + FIELDS:
            u, v = x[k], y[k]
            if isinstance(u, list):
                ok = len(u) == len(v) and all(abs(p - q) <= tol for p, q in zip(u, v))
            elif isinstance(u, float) or isinstance(v, float):
                ok = abs(float(u) - float(v)) <= tol
            else:
                ok = u == v
            if not ok:
                return False, f"node {i} ({x['kind']} '{x['name'] or x['text']}'): {k} {u!r} against {v!r}"
    return True, ""


@dataclass
class UiSet:
    """What a KIND = "ui" script returns: the tree, and optionally a font to draw it in."""
    ui: Ui
    font: str = None                  # name of a KIND = "font" asset (built first), or None for the engine's
    notes: str = ""
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------- checks

def has(name, kind=None):
    """A node of this name exists (and is of this kind): the name is how game code finds it."""
    def fn(ctx):
        hits = [n for n in ctx.ui.nodes if n["name"] == name]
        ok = len(hits) == 1 and (kind is None or hits[0]["kind"] == kind)
        return ok, (f"'{name}' is a {hits[0]['kind']}" if len(hits) == 1 else f"{len(hits)} nodes named '{name}'")
    return Check(f"has {name}", fn)


def node_at_least(name, w=0, h=0):
    """A node's laid-out rectangle is at least this large (a button big enough to hit)."""
    def fn(ctx):
        r = ctx.rect(name)
        if r is None:
            return False, "no layout from the engine"
        return r["w"] >= w and r["h"] >= h, f"'{name}' is {r['w']:.0f} x {r['h']:.0f} px (wanted at least {w} x {h})"
    return Check(f"size of {name}", fn)


def custom(name, fn):
    """fn(ctx) -> (ok, detail); ctx.ui, ctx.layout (the engine's rectangles, or None), ctx.rect(name)."""
    return Check(name, fn)


def _tree(ctx):
    bad = []
    for i, n in enumerate(ctx.ui.nodes):
        if n["kind"] not in KINDS:
            bad.append(f"node {i}: kind {n['kind']}")
        if n["parent"] >= i:
            bad.append(f"node {i}: its parent comes after it")
        if not 4 <= n["font_size"] <= 256:
            bad.append(f"node {i}: font size {n['font_size']} (the engine bakes 4 to 256)")
        for s in (n["name"], n["text"]):
            if '"' in s or "\\" in s or "\n" in s:
                bad.append(f"node {i}: a quote, backslash or newline in '{s}' does not survive the document")
            try:
                s.encode("latin-1")
            except UnicodeEncodeError:
                bad.append(f"node {i}: '{s}' has characters outside Latin-1; the engine draws them as '?'")
    names = [n["name"] for n in ctx.ui.nodes if n["name"]]
    dup = sorted({x for x in names if names.count(x) > 1})
    if dup:
        bad.append(f"names used twice: {dup}")
    unnamed = [n["text"] for n in ctx.ui.nodes if n["kind"] in ("button", "toggle", "slider") and not n["name"]]
    if unnamed:
        bad.append(f"controls without a name (game code cannot find them): {unnamed}")
    return not bad, "; ".join(bad) or f"{len(ctx.ui.nodes)} nodes, parents first, Latin-1 text, every control named"


def _own_roundtrip(ctx):
    ok, why = same(Ui.from_text(ctx.ui.to_text()), _in_order(ctx.ui))
    return ok, why or "the document parses back to the same tree"


def _in_order(ui):
    """The tree with its nodes renumbered the way the document numbers them."""
    order = ui.order()
    index = {old: new for new, old in enumerate(order)}
    out = Ui(ui.theme)
    for old in order:
        n = dict(ui.nodes[old])
        n["parent"] = index[n["parent"]] if n["parent"] >= 0 else -1
        out.nodes.append(n)
    return out


def _engine_roundtrip(ctx):
    if ctx.probe is None:
        return False, "not run: no cinder-probe"
    ok, why = same(Ui.from_text(ctx.probe["roundtrip"]), _in_order(ctx.ui))
    return ok, why or "Cinder read the document and wrote the same tree back (Ui.from_text, Ui.to_text)"


def _in_frame(ctx):
    if ctx.probe is None:
        return False, "not run: no cinder-probe"
    bad = []
    for n in ctx.probe["nodes"]:
        if n["visible"] and (n["x"] < 0 or n["y"] < 0 or n["x"] + n["w"] > FRAME[0] or n["y"] + n["h"] > FRAME[1]):
            bad.append(f"{n['kind']} '{n['name'] or n['text']}' at {n['x']:.0f},{n['y']:.0f} "
                       f"{n['w']:.0f}x{n['h']:.0f}")
    return not bad, ("outside the 1280 x 720 frame: " + "; ".join(bad)) if bad else \
        "every node lies inside the 1280 x 720 frame"


def _roots_apart(ctx):
    if ctx.probe is None:
        return False, "not run: no cinder-probe"
    order = ctx.ui.order()
    roots = [ctx.probe["nodes"][new] for new, old in enumerate(order)
             if ctx.ui.nodes[old]["parent"] < 0 and ctx.ui.nodes[old]["visible"]]
    for i, a in enumerate(roots):
        for b in roots[i + 1:]:
            if (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
                    and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]):
                return False, f"panels '{a['name']}' and '{b['name']}' overlap"
    return True, f"{len(roots)} root panel(s), none overlapping"


def static_checks():
    return [Check("name", _name_ok), Check("tree", _tree), Check("document", _own_roundtrip)]


def engine_checks():
    return [Check("engine round trip", _engine_roundtrip), Check("in frame", _in_frame),
            Check("panels apart", _roots_apart)]


# ---------------------------------------------------------------- build

def mojo_snippet(name, ui, rel="ui", font=None):
    lines = [f'# {name}: load the interface, then keep the ids of what the game drives',
             "from cinder.core.fs import read_text",
             "from cinder.ui import Ui, UiColor",
             f'app.ui = Ui.from_text(read_text(String("{rel}/{name}.ui.txt")))']
    if font:
        lines += [f"# set in the font {font}: in Game.start, before anything is drawn",
                  "from cinder.ui import Font, FontCache",
                  "app._ensure_ui_renderer()",
                  f'app.ui_renderer.value().fonts = FontCache(Font.from_file(app.lib.ptr(), String("fonts/{font}.ttf")))']
    lines += ui.theme.mojo()
    for n in ui.nodes:
        if n["name"]:
            lines.append(f'var {n["name"]} = app.ui.find(String("{n["name"]}"))   # {n["kind"]}')
    return "\n".join(lines)


def render_ui(path, frame, probe, title, lines, results, ready):
    """The engine's frame, and the same frame with every node's rectangle outlined and named."""
    W = 1600
    with Image.open(frame) as im:
        shot = im.convert("RGB")
    half = shot.resize((800, 450), Image.LANCZOS)
    marked = shot.copy()
    d = ImageDraw.Draw(marked)
    colours = dict(panel=(120, 200, 255), label=(150, 230, 150), button=(255, 190, 110),
                   toggle=(240, 140, 220), slider=(255, 240, 120))
    for n in probe["nodes"]:
        if n["visible"] and n["w"] > 0:
            d.rectangle([n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"]], outline=colours[n["kind"]], width=2)
            if n["name"]:
                d.text((n["x"] + 3, n["y"] - 15 if n["y"] > 16 else n["y"] + n["h"] + 2), n["name"],
                       fill=colours[n["kind"]], font=_font(13))
    sheet = Image.new("RGB", (W, 60 + 450 + 30 + 18 * (len(lines) + len(results) + 1)), BG)
    dd = ImageDraw.Draw(sheet)
    dd.text((16, 14), title, fill=INK, font=_font(26))
    dd.text((W - 190, 16), "ready YES" if ready else "ready NO", fill=OK if ready else BAD, font=_font(24))
    sheet.paste(half, (0, 60))
    sheet.paste(marked.resize((800, 450), Image.LANCZOS), (800, 60))
    dd.text((8, 64), "as Cinder draws it, 1280 x 720", fill=(255, 255, 255), font=_font(13))
    dd.text((808, 64), "the engine's layout: every node's rectangle", fill=(255, 255, 255), font=_font(13))
    ty = 60 + 450 + 12
    for line in lines:
        dd.text((12, ty), line, fill=INK, font=_font(13))
        ty += 18
    ty += 4
    for r in results:
        dd.text((12, ty), ("PASS  " if r["ok"] else "FAIL  ") + r["name"] + ": " + r["detail"][:170],
                fill=OK if r["ok"] else BAD, font=_font(13))
        ty += 18
    sheet.save(path)


def build_ui(path, mod, params, out_root, use_engine=True, quiet=False):
    t0 = time.time()
    path = Path(path)
    name = path.stem
    p = SimpleNamespace(**params)
    built = mod.build(p)
    if not isinstance(built, UiSet):
        raise SystemExit('a KIND = "ui" script must return cadkit.game.ui.UiSet from build(p)')
    ui = built.ui
    out = Path(out_root) / name
    out.mkdir(parents=True, exist_ok=True)
    doc = out / f"{name}.ui.txt"
    doc.write_text(ui.to_text(), encoding="utf-8", newline="\n")
    (out / f"{name}.theme.json").write_text(json.dumps(asdict(ui.theme), indent=1), encoding="utf-8")
    (out / f"{name}.mojo").write_text(mojo_snippet(name, ui, font=built.font) + "\n", encoding="utf-8")

    probe, problem = None, None
    frame = out / f"{name}_frame.png"
    font = None
    if built.font:
        font = Path(out_root) / built.font / f"{built.font}.ttf"
        if not font.exists():
            raise SystemExit(f"this interface is set in the font '{built.font}', which is not built: "
                             f"cad game build assets/{built.font}.py")
    if use_engine:
        probe, problem = E.probe_ui(doc, frame, font)
    layout = None
    if probe:
        order = ui.order()
        layout = {ui.nodes[old]["name"]: probe["nodes"][new] for new, old in enumerate(order) if ui.nodes[old]["name"]}
    ctx = SimpleNamespace(ui=ui, name=name, params=params, probe=probe, layout=layout,
                          rect=lambda n: (layout or {}).get(n))
    spec = mod.checks(p) if callable(getattr(mod, "checks", None)) else []
    checks = static_checks() + (engine_checks() if use_engine and probe else []) + list(spec)
    results = [c.run(ctx) for c in checks]
    blockers = [f"check {r['name']}: {r['detail']}" for r in results if not r["ok"]]
    steps = dict(static=dict(ok=not blockers, checks=results))
    if probe is None:
        blockers.append("not verified in Cinder: " + ("skipped (--no-engine)" if not use_engine else problem))
    else:
        steps["engine"] = dict(ok=probe["gpu_errors"] == 0, gpu_errors=probe["gpu_errors"], nodes=len(probe["nodes"]),
                               method="cinder-probe: Ui.from_text, layout, headless frame, Ui.to_text",
                               font=probe.get("font"))
        if probe["gpu_errors"]:
            blockers.append(f"engine: {probe['gpu_errors']} GPU validation errors")
    ready = not blockers
    kinds = {k: sum(1 for n in ui.nodes if n["kind"] == k) for k in KINDS}
    lines = [f"{name}  (ui)  {getattr(mod, 'DESCRIPTION', '')}",
             "nodes    " + ", ".join(f"{v} {k}{'s' if v != 1 else ''}" for k, v in kinds.items() if v)
             + f"; {sum(1 for n in ui.nodes if n['parent'] < 0)} root panel(s)",
             "named    " + ", ".join(n["name"] for n in ui.nodes if n["name"]),
             f"font     {built.font or 'the engine default (Roboto Medium)'}; sizes "
             + ", ".join(str(s) for s in sorted({n['font_size'] for n in ui.nodes}))]
    if probe:
        lines.append(f"engine   Cinder read, laid out and drew {len(probe['nodes'])} nodes with "
                     f"{probe['gpu_errors']} GPU errors, and wrote the document back")
    for r in results:
        lines.append(f"check    {'PASS' if r['ok'] else 'FAIL'}  {r['name']}: {r['detail']}")
    lines += ["BLOCKER  " + b for b in blockers]
    lines.append(f"ready    {'YES' if ready else 'NO'}")
    preview = out / f"{name}_preview.png"
    if probe:
        render_ui(preview, frame, probe, f"{name}: {getattr(mod, 'DESCRIPTION', '')}",
                  [l for l in lines if not l.startswith(("check", "BLOCKER", "ready"))], results, ready)
    build = dict(schema="cadkit-game-build/1", name=name, kind="ui", description=getattr(mod, "DESCRIPTION", ""),
                 params=params, ready=ready, blockers=blockers,
                 stats=dict(nodes=len(ui.nodes), kinds=kinds, names=[n["name"] for n in ui.nodes if n["name"]],
                            frame=list(FRAME), font=built.font, layout=layout),
                 use_snippet=mojo_snippet(name, ui, font=built.font), notes=built.notes,
                 files=dict(document=doc.name, theme=f"{name}.theme.json", mojo=f"{name}.mojo",
                            preview=preview.name if probe else None, sha256=outputs.sha256(doc)),
                 product=dict(getattr(mod, "PRODUCT", {}) or {}), source_sha256=outputs.sha256(path),
                 engine=E.probe_info(), steps=steps, report=lines, built_at=outputs.now_iso(),
                 seconds=round(time.time() - t0, 1), git=outputs.git_info())
    outputs.save_json(out / "build.json", build)
    outputs.save_json(out / "readiness.json", dict(ready=ready, blockers=blockers, steps=steps))
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    build["out"] = str(out)
    if not quiet:
        print("\n".join(lines))
        if probe:
            print(f"preview  {preview}")
    return build
