"""Packs: a set of ready assets delivered as one self-describing folder.

A pack script (`packs/<name>.py`) says what is in it and builds its demo world:

    TITLE = "Dungeon Kit"
    DESCRIPTION = "one line"
    COLLECTION = "dungeon_kit"            # every asset whose PRODUCT["collection"] matches (or a tuple of them)
    LICENCE = "CC0-1.0"
    LEFT_OUT = {"wall_tapestry": "its picture is not cleared"}   # members of the collection this pack does not
                                                                 # ship, each with the reason; listed in the manifest
    DEMO = dict(seconds=30, autopilot=True, expect_won=True,
                settle=dict(max_move=0.3, free=["bouncer"]))      # dynamic bodies must end where they were put
    SHOTS = [dict(name="hall", position=(0, 1.7, 0.4), target=(0, 1.2, -5),   # beauty frames;
                  hide=["roof_"])]                                             # hide= drops entities by name prefix
    def demo(w): ...                       # w is a cadkit.game.world.World that knows the assets

`build_pack` (re)builds any member that is missing, stale or not ready, refuses a pack with
a member that is not ready, and writes output/game/packs/<name>/:

    assets/<asset>.glb        sources (the deliverable)
    previews/<asset>.png      each asset's engine-rendered sheet
    worlds/demo.world         the demo; run it with the pack folder as working directory
    <name>_demo.png, <name>_overview.png, <name>_contents.png
    manifest.json             schema cadkit-game/1
    AGENTS.md                 how an agent uses the pack: one world-file snippet per asset
    ATTRIBUTION.md            licence and provenance
"""
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

from .. import outputs
from . import build as B
from . import engine as E
from .render import BG, INK, _font
from .world import World

SAMPLER_BUDGET = 245                  # of Cinder 0.1.1's 256-slot sampler pool; the engine uses a few itself
ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "assets"
PACKS_OUT = B.OUT / "packs"
LICENCES = {"CC0-1.0": "CC0 1.0 Universal: public domain dedication. Use, change and ship these "
                       "assets in any project, commercial or not, with no attribution required. "
                       "https://creativecommons.org/publicdomain/zero/1.0/"}


def members(collection, left_out=()):
    out = []
    for path in sorted(ASSETS.glob("*.py")):
        if path.name.startswith("_") or path.stem in left_out:
            continue
        prod = getattr(B.load_asset(path), "PRODUCT", None) or {}
        wanted = (collection,) if isinstance(collection, str) else tuple(collection)
        if prod.get("collection") in wanted:
            out.append(path)
    return out


def _fresh(path, refresh):
    """The asset's build.json, rebuilding when it is missing, stale or was not ready."""
    out = B.OUT / path.stem
    b = outputs.load_json(out / "build.json", None)
    stale = (b is None or not b.get("ready") or b.get("source_sha256") != outputs.sha256(path)
             or not (out / next((b["files"][k] for k in ("glb", "wav", "document", "png", "ttf") if b["files"].get(k)),
                                  "missing")).exists())
    if refresh or stale:
        print(f"building {path.stem} ...")
        b = B.build_asset(path, quiet=True)
        b.pop("out", None)
    return b


def sound_entry(b, licence):
    name, s = b["name"], b["stats"]
    return dict(
        id=name, kind="sound", description=b["description"], file=f"audio/{name}.wav",
        sha256=b["files"]["sha256"], preview=f"previews/{name}.png",
        seconds=s["seconds"], channels=s["channels"], sample_rate=s["sample_rate"], peak_db=s["peak_db"],
        rms_db=s["rms_db"], centroid_hz=s["centroid_hz"], loop=s["loop"], bus=s["bus"], spatial=s["spatial"],
        streamed=s["streamed"], bytes=s["wav_bytes"],
        use_snippet=b["use_snippet"], tags=b.get("product", {}).get("tags", []),
        notes=b.get("product", {}).get("notes", ""),
        licence=b.get("product", {}).get("licence", licence),
        provenance="procedural (cadkit.game.audio synthesis), no samples, no generative inputs",
        ready=b["ready"], verified_engine=(b.get("engine") or {}).get("version"))


def ui_entry(b, licence):
    name, s = b["name"], b["stats"]
    return dict(
        id=name, kind="ui", description=b["description"], file=f"ui/{name}.ui.txt",
        files=[f"ui/{name}.ui.txt", f"ui/{name}.theme.json", f"ui/{name}.mojo"],
        sha256=b["files"]["sha256"], preview=f"previews/{name}.png",
        nodes=s["nodes"], node_kinds=s["kinds"], names=s["names"], frame=s["frame"], font=s["font"],
        layout=s["layout"], use_snippet=b["use_snippet"], notes=b.get("notes", ""),
        tags=b.get("product", {}).get("tags", []), licence=b.get("product", {}).get("licence", licence),
        provenance="procedural (cadkit.game.ui), no generative inputs",
        ready=b["ready"], verified_engine=(b.get("engine") or {}).get("commit"))


def font_entry(b, licence):
    name, s = b["name"], b["stats"]
    return dict(
        id=name, kind="font", description=b["description"], file=f"fonts/{name}.ttf",
        files=[f"fonts/{name}.ttf", f"fonts/{name}.json"], sha256=b["files"]["sha256"], preview=f"previews/{name}.png",
        family=s["family"], glyphs="".join(s["glyphs"]), code_points=s["code_points"], unicase=s["unicase"],
        units_per_em=s["units_per_em"], cap_height=s["cap_height"], bytes=s["ttf_bytes"],
        use_snippet=b["use_snippet"], notes=b.get("notes", ""),
        tags=b.get("product", {}).get("tags", []), licence=b.get("product", {}).get("licence", licence),
        provenance="drawn by code (cadkit.game.font, from cadkit.stitch.lettering); no third-party typeface",
        ready=b["ready"], verified_engine=(b.get("engine") or {}).get("commit"))


def sprite_entry(b, licence):
    name, s = b["name"], b["stats"]
    return dict(
        id=name, kind="sprite", description=b["description"], file=f"sprites/{name}.png",
        files=[f"sprites/{name}.png", f"sprites/{name}.json"],
        sha256=b["files"]["sha256"], preview=f"previews/{name}.png",
        atlas=s["atlas"], frames=s["frames"], animations=s["animations"], slices=s["slices"], bytes=s["png_bytes"],
        tags=b.get("product", {}).get("tags", []), licence=b.get("product", {}).get("licence", licence),
        notes="Built ahead: Cinder 0.1.1 has no sprite renderer and its UI draws no images. "
              "PNG + JSON (schema cadkit-sprites/1): straight alpha, origin top-left, frames in pixels.",
        provenance="procedural (cadkit.game.sprite vector drawing), no generative inputs",
        ready=b["ready"], verified_engine=(b.get("engine") or {}).get("version"))


def entry(b, licence):
    """One asset's manifest record, from its build.json."""
    if b["kind"] == "sound":
        return sound_entry(b, licence)
    if b["kind"] == "ui":
        return ui_entry(b, licence)
    if b["kind"] == "sprite":
        return sprite_entry(b, licence)
    if b["kind"] == "font":
        return font_entry(b, licence)
    name = b["name"]
    n_img = len(b["stats"]["textures"])
    return dict(
        id=name, kind=b["kind"], description=b["description"], file=f"assets/{name}.glb",
        sha256=b["files"]["sha256"], preview=f"previews/{name}.png",
        size_m=b["stats"]["size_m"], bounds=b["stats"]["bounds"], triangles=b["stats"]["triangles"],
        materials=b["stats"]["materials"], textures=b["stats"]["textures"],
        engine_use=b["engine_use"], rest_y=b["rest_y"],
        world_snippet=b["world_snippet"], tags=b.get("product", {}).get("tags", []),
        notes=b.get("product", {}).get("notes", ""), gameplay=b.get("product", {}).get("gameplay", {}),
        nodes=[nd["name"] for nd in b["stats"].get("nodes", [])], bones=b["stats"].get("bones", 0),
        clips=b["stats"].get("clips", []),
        licence=b.get("product", {}).get("licence", licence), provenance="procedural (cadkit.game), no generative inputs",
        cook=dict(prefix=name, skeletons=[f"{name}#skeleton0"] if b["stats"].get("bones") else [],
                  clips=[f"{name}#anim{i}" for i in range(len(b["stats"].get("clips", [])))],
                  meshes=[f"{name}#mesh{mi}/prim{pi}" for mi, nd in enumerate(
                      b["stats"].get("nodes") or [dict(primitives=b["stats"]["materials"])])
                      for pi in range(nd["primitives"])],
                  materials=[f"{name}#material{i}" for i in range(b["stats"]["materials"])],
                  images=[f"{name}#image{i}" for i in range(n_img)]),
        ready=b["ready"], verified_engine=(b.get("engine") or {}).get("version"))


def contents_sheet(path, entries, title, cols=5):
    """A grid of every asset's first engine frame."""
    cw, ch = 400, 225
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, 50 + rows * (ch + 24)), BG)
    d = ImageDraw.Draw(sheet)
    d.text((12, 12), title, fill=INK, font=_font(22))
    for i, e in enumerate(entries):
        x, y = (i % cols) * cw, 50 + (i // cols) * (ch + 24)
        with Image.open(B.OUT / e["id"] / f"{e['id']}_preview.png") as im:
            sheet.paste(im.crop((0, 60, 800, 510)).resize((cw, ch), Image.LANCZOS), (x, y))
        d.text((x + 6, y + ch + 3), f"{e['id']}  {e['triangles']} tris  "
               f"{e['size_m'][0]:g} x {e['size_m'][1]:g} x {e['size_m'][2]:g} m", fill=INK, font=_font(12))
    sheet.save(path)


def agents_md(title, description, entries, demo, eng):
    lines = [f"# {title}: using this pack as an agent", "", description, "",
             "Everything here is plain data. `manifest.json` (schema `cadkit-game/1`) has every number "
             "below in structured form.", "",
             "## Conventions", "",
             "- Metres, Y up, -Z forward. A 2 m grid; floors have their walking surface at Y=0.",
             "- Paths in the snippets are relative to this folder: run `cinder-play` with this folder as "
             "the working directory, or rewrite the paths.",
             "- `transform position` in a snippet stands the asset on a floor at the origin. Add your X "
             "and Z, and your floor height to Y; turn it with `rotation=[0,<yaw>,0]`.",
             "- Sources (`assets/*.glb`) are the deliverable. Cook them with `cinder-cook <out> assets/*.glb` "
             "for your engine build; the cook prefix of each file is its base name, so the logical paths are "
             "`<name>#mesh0/prim<i>`, `<name>#material<i>`, `<name>#image<n>`.", "",
             "## Assets", ""]
    for e in entries:
        s = e["size_m"]
        lines += [f"### `{e['id']}`", "", f"{e['description']}. {s[0]:g} x {s[1]:g} x {s[2]:g} m, "
                  f"{e['triangles']} triangles, {e['materials']} material(s), {len(e['textures'])} texture(s).",
                  "", "```", e["world_snippet"].replace(f'assets/{e["id"]}.glb', e["file"]), "```", ""]
        if e.get("clips"):
            lines += [f"Rig: {e['bones']} bones. Clips: " + ", ".join(
                f"{i} `{c['name']}` {c['duration']:g} s" for i, c in enumerate(e["clips"])) + ".", ""]
        if len(e.get("nodes", [])) > 1:
            lines += ["Mesh nodes (each spawns as its own entity from Mojo; the world kit draws the file as "
                      "one): " + ", ".join(f"`{nd}`" for nd in e["nodes"]) + ".", ""]
        if e.get("gameplay"):
            lines += ["Gameplay: `" + json.dumps(e["gameplay"]) + "`", ""]
        if e.get("notes"):
            lines += [e["notes"], ""]
    if demo:
        lines += ["## Demo world", "", "```",
                  "cinder-play worlds/demo.world --headless --seconds "
                  f"{demo['seconds']:g}{' --autopilot' if demo.get('autopilot') else ''} "
                  "--screenshot out.png --report out.json", "```", "",
                  f"Verified on Cinder {eng}: " + demo["summary"], ""]
    return "\n".join(lines)


def sounds_md(sounds):
    if not sounds:
        return ""
    lines = ["", "## Sounds", "",
             "WAV, 48 kHz, 16-bit PCM. One-shots are mono and spatial; loops are the whole file (Cinder "
             "has no loop points) and wrap without a click. The world kit has no audio components yet, so "
             "sounds are played from a Mojo `Game` through `cinder.audio`. `SoundDesc(path, bus, streamed, "
             "looping, spatial)`; create the buses once with `app.audio.value().create_bus(String(\"sfx\"))`.",
             "", "| Sound | Length | Channels | Loop | Peak | Bus | What it is |", "|---|---|---|---|---|---|---|"]
    for e in sounds:
        lines.append(f"| `{e['file']}` | {e['seconds']:g} s | {'mono' if e['channels'] == 1 else 'stereo'} | "
                     f"{'yes' if e['loop'] else 'no'} | {e['peak_db']:g} dBFS | {e['bus']} | {e['description']} |")
    lines += ["", "```mojo"] + [e["use_snippet"] for e in sounds] + ["```", ""]
    return "\n".join(lines)


def ui_md(uis):
    if not uis:
        return ""
    lines = ["", "## Interfaces", "",
             "Each is a `cinder-scene 1` UI document: load it with `Ui.from_text`, then `find` the named nodes. "
             "Cinder read every one of these, laid it out at 1280 x 720, drew it and wrote the same tree back. "
             "The theme (hover, pressed, accent and focus colours) is not part of a document: the `.mojo` file "
             "beside it sets it. No images, text fields, scrolling or wrapping exist in cinder.ui yet.", ""]
    for e in uis:
        kinds = ", ".join(f"{v} {k}{'s' if v != 1 else ''}" for k, v in e["node_kinds"].items() if v)
        lines += [f"### `{e['id']}`", "", f"{e['description']}. {kinds}. Named nodes: "
                  + ", ".join(f"`{n}`" for n in e["names"]) + ".", "", "```mojo", e["use_snippet"], "```", ""]
        if e.get("notes"):
            lines += [e["notes"], ""]
    return "\n".join(lines)


def fonts_md(fonts):
    if not fonts:
        return ""
    lines = ["", "## Fonts", "",
             "TrueType, drawn by code, with no third-party typeface involved. Cinder parsed each, baked its "
             "atlas and drew text in it. `cinder.ui` uses one font for the whole interface and has no public "
             "setting for it in 0.1.1: install it in `Game.start`, before anything is drawn (the renderer "
             "uploads a glyph atlas once per size; a font swapped in later is laid out right and drawn wrong).", ""]
    for e in fonts:
        lines += [f"### `{e['id']}`", "", f"{e['description']}. Family \"{e['family']}\". Draws `{e['glyphs']}`; "
                  + ("lowercase letters use the capitals; " if e["unicase"] else "")
                  + "accented Latin-1 letters use their base letter; anything else is a hollow box. No kerning.",
                  "", "```mojo", e["use_snippet"], "```", ""]
    return "\n".join(lines)


def sprites_md(sprites):
    if not sprites:
        return ""
    lines = ["", "## Sprites (built ahead)", "",
             "PNG atlas + JSON (`cadkit-sprites/1`): `frames` maps a name to `x, y, w, h` in pixels from the top "
             "left, `animations` to a frame list with `fps`, `slices` to 9-slice borders. Straight alpha. Cinder "
             "0.1.1 has no sprite renderer and `cinder.ui` draws no images, so nothing in the engine reads these "
             "yet; each was drawn in Cinder on unlit quads to prove the art loads.", "",
             "| Sheet | Atlas | Frames | Animations | 9-slice |", "|---|---|---|---|---|"]
    for e in sprites:
        lines.append(f"| `{e['file']}` | {e['atlas'][0]} x {e['atlas'][1]} | {', '.join(e['frames'])} | "
                     + (", ".join(f"{k} ({len(a['frames'])} @ {a.get('fps')} fps)" for k, a in e["animations"].items()) or "-")
                     + " | " + (", ".join(e["slices"]) or "-") + " |")
    return "\n".join(lines) + "\n"


def build_pack(script, refresh=False, quiet=False):
    script = Path(script)
    mod = B.load_asset(script)
    name = script.stem
    licence = getattr(mod, "LICENCE", "CC0-1.0")
    left_out = dict(getattr(mod, "LEFT_OUT", {}) or {})
    unknown = [n for n in left_out if not (ASSETS / f"{n}.py").exists()]
    if unknown or not all(isinstance(r, str) and r.strip() for r in left_out.values()):
        raise SystemExit("LEFT_OUT names an asset and gives the reason it is not shipped; "
                         + (f"no such asset: {', '.join(unknown)}" if unknown else "a reason is empty"))
    paths = members(mod.COLLECTION, left_out)
    if not paths:
        raise SystemExit(f"no asset has PRODUCT['collection'] == '{mod.COLLECTION}'")
    builds = [_fresh(p, refresh) for p in paths]
    not_ready = [b["name"] for b in builds if not b["ready"]]
    if not_ready:
        raise SystemExit("pack refused, not ready: " + ", ".join(not_ready) + " (cad game build each to see why)")
    from . import gen
    uncleared = []
    for b in builds:                                  # clearance is read now, not from when the asset was built
        for g in b.get("generated", []):
            rec = gen.record(g["id"])
            g.update(cleared=rec["cleared"], cleared_by=rec["cleared_by"], cleared_note=rec.get("cleared_note"),
                     terms=rec.get("terms"))
            if not rec["cleared"]:
                uncleared.append(f"{b['name']} uses {g['id']} ({g['provider']})")
    if uncleared:
        raise SystemExit("pack refused, generated inputs not cleared by a person: " + "; ".join(uncleared)
                         + "\n  look at each (assets/gen/<id>.*), check the provider's terms, then: "
                           "cad game gen clear <id> --by NAME --note \"what you checked\"")
    entries = [entry(b, licence) for b in builds]
    for e, b in zip(entries, builds):
        if b.get("generated"):
            e["generated_inputs"] = b["generated"]
            e["provenance"] = "procedural, with generated inputs: " + "; ".join(
                f"{g['id']} ({g['provider']} {g['model']}, cleared by {g['cleared_by']})" for g in b["generated"])

    out = PACKS_OUT / name
    shutil.rmtree(out, ignore_errors=True)
    for sub in ("assets", "audio", "ui", "sprites", "fonts", "previews", "worlds"):
        (out / sub).mkdir(parents=True)
    for e in entries:
        for f in e.get("files", [e["file"]]):
            shutil.copy2(B.OUT / e["id"] / Path(f).name, out / f)
        shutil.copy2(B.OUT / e["id"] / f"{e['id']}_preview.png", out / e["preview"])
    models = [e for e in entries if e["kind"] not in ("sound", "ui", "sprite", "font")]
    fonts = [e for e in entries if e["kind"] == "font"]
    missing_fonts = sorted({e["font"] for e in entries if e["kind"] == "ui" and e.get("font")} - {f["id"] for f in fonts})
    if missing_fonts:
        raise SystemExit("pack refused: an interface is set in a font that is not in this collection: "
                         + ", ".join(missing_fonts))
    sounds = [e for e in entries if e["kind"] == "sound"]
    uis = [e for e in entries if e["kind"] == "ui"]
    sprites = [e for e in entries if e["kind"] == "sprite"]
    for sub, have in (("audio", sounds), ("ui", uis), ("sprites", sprites), ("fonts", fonts)):
        if not have:
            (out / sub).rmdir()
    contents_sheet(out / f"{name}_contents.png", models, f"{mod.TITLE}: {len(models)} models"
                   + (f" (+ {len(sounds)} sounds)" if sounds else ""))

    eng = E.find()
    demo, problems = None, []
    if hasattr(mod, "demo"):
        cfg = dict(seconds=20, autopilot=False, expect_won=False, settle=None)
        cfg.update(getattr(mod, "DEMO", {}) or {})
        w = World(f"{mod.TITLE} demo", assets={e["id"]: e for e in models})
        mod.demo(w)
        world = out / "worlds" / "demo.world"
        world.write_text(w.text(), encoding="utf-8")
        placed = sum(1 for _, comps in w.entities if "model" in comps)
        used = sorted({comps["model"]["path"].split("/")[-1][:-4] for _, comps in w.entities if "model" in comps})
        demo = dict(world="worlds/demo.world", seconds=cfg["seconds"], autopilot=cfg["autopilot"],
                    entities=len(w.entities), models=placed, assets_used=used)
        # Cinder's sampler pool holds 256, and the world kit makes one sampler per texture for every
        # placed copy of a model (copies of one file share nothing). Count before the engine refuses.
        by_file = {e["file"]: len(e.get("textures", [])) for e in models}
        samplers = sum(by_file.get(comps["model"]["path"], 0) for _, comps in w.entities if "model" in comps)
        demo["samplers"] = samplers
        if samplers > SAMPLER_BUDGET:
            problems.append(f"demo world needs {samplers} texture samplers and Cinder 0.1.1 has {SAMPLER_BUDGET} to give "
                            "(256, less its own): every placed copy of a model counts each of its textures. Use "
                            "larger pieces, fewer textured materials per piece, or fewer copies")
        if eng is None:
            problems.append("demo not run: no Cinder engine found (set CAD_CINDER)")
        else:
            ok, text = eng.check("worlds/demo.world", cwd=out)
            if samplers > SAMPLER_BUDGET:
                pass                                          # reported above; the engine would only say "Pool is full"
            elif not ok:
                problems.append("demo.world fails --check: " + text[-600:])
            else:
                rep = eng.play("worlds/demo.world", seconds=cfg["seconds"], autopilot=cfg["autopilot"],
                               screenshot=f"{name}_demo.png", cwd=out, timeout=300)
                over = eng.play("worlds/demo.world", frames=3, overview=True,
                                screenshot=f"{name}_overview.png", cwd=out, timeout=300)
                res, run = rep.get("result", {}), rep.get("run", {})
                demo.update(ok=bool(rep.get("ok")), won=res.get("won"), won_at=res.get("won_at"),
                            score=res.get("score"), pickups=f"{res.get('pickups_collected')}/{res.get('pickups_total')}",
                            falls=res.get("falls"), gpu_errors=run.get("gpu_errors"),
                            events=res.get("events", []), adapter=run.get("adapter"))
                if not rep.get("ok"):
                    problems.append("demo run: " + str(rep.get("error", "not ok")))
                if run.get("gpu_errors"):
                    problems.append(f"demo run: {run['gpu_errors']} GPU validation errors")
                if rep.get("world", {}).get("models") != placed:
                    problems.append(f"demo run: {rep.get('world', {}).get('models')} of {placed} models loaded")
                if cfg["expect_won"] and not res.get("won"):
                    problems.append(f"demo run: not won in {cfg['seconds']} s (pickups {demo['pickups']}, "
                                    f"falls {res.get('falls')}, player at {res.get('player', {}).get('position')})")
                if not over.get("ok"):
                    problems.append("demo overview: " + str(over.get("error", "not ok")))
                # stacks must stand: every dynamic body ends the run near where it was placed
                final = {e["name"]: e["position"] for e in res.get("entities", [])}
                moved = []
                for ent, comps in w.entities:
                    if comps.get("body", {}).get("motion") == "dynamic" and ent in final:
                        at = comps.get("transform", {}).get("position", (0, 0, 0))
                        dist = sum((float(a) - float(b)) ** 2 for a, b in zip(at, final[ent])) ** 0.5
                        moved.append(dict(entity=ent, placed=[round(float(x), 3) for x in at],
                                          final=[round(float(x), 3) for x in final[ent]], moved_m=round(dist, 3)))
                demo["dynamic_bodies"] = moved
                settle = cfg.get("settle")
                if settle:
                    for mv in moved:
                        if mv["moved_m"] > settle.get("max_move", 0.3) and mv["entity"] not in settle.get("free", []):
                            problems.append(f"demo run: {mv['entity']} ended {mv['moved_m']} m from where it was "
                                            f"placed ({mv['placed']} -> {mv['final']}): the stack did not stand")
                # beauty frames: the same world without its player, seen from a placed camera
                demo["shots"] = []
                for shot in getattr(mod, "SHOTS", []) or []:
                    sw = World(w.title, assets=w.assets)
                    sw.settings = list(w.settings)
                    hide = tuple(shot.get("hide", ()))             # entity name prefixes left out of this frame
                    sw.entities = [(n, c) for n, c in w.entities if "player" not in c and "camera" not in c
                                   and not (hide and n.startswith(hide))]
                    sw.add("shot_camera", transform=dict(position=shot["position"]),
                           camera=dict(fov=shot.get("fov", 55), target=shot["target"]))
                    sworld = out / "worlds" / f"shot_{shot['name']}.world"
                    sworld.write_text(sw.text(), encoding="utf-8")
                    png = f"{name}_{shot['name']}.png"
                    r = eng.play(f"worlds/{sworld.name}", frames=3, screenshot=png, cwd=out, timeout=300)
                    sworld.unlink()
                    if not r.get("ok"):
                        problems.append(f"shot {shot['name']}: " + str(r.get("error", "not ok")))
                    demo["shots"].append(png)
                demo["summary"] = (f"{placed} models of {len(used)} assets load with {run.get('gpu_errors')} GPU errors"
                                   + (f"; the autopilot wins it in {res.get('won_at')} s with {demo['pickups']} pickups"
                                      if res.get("won") else "; not won"))
    ready = not problems
    manifest = dict(schema="cadkit-game/1", kind="game-asset-pack", name=name, title=mod.TITLE,
                    description=mod.DESCRIPTION, licence=licence, ready=ready, problems=problems,
                    left_out=[dict(id=n, reason=r) for n, r in sorted(left_out.items())],
                    assets=entries, demo=demo, engine=eng.info() if eng else None,
                    totals=dict(assets=len(entries), models=len(models), sounds=len(sounds),
                                interfaces=len(uis), sprite_sheets=len(sprites), fonts=len(fonts),
                                sound_seconds=round(sum(e["seconds"] for e in sounds), 2),
                                triangles=sum(e["triangles"] for e in models),
                                bytes=sum((out / f).stat().st_size for e in entries
                                          for f in e.get("files", [e["file"]]))),
                    built_at=outputs.now_iso(), git=outputs.git_info())
    outputs.save_json(out / "manifest.json", manifest)
    (out / "AGENTS.md").write_text(
        agents_md(mod.TITLE, mod.DESCRIPTION, models, demo if demo and "summary" in demo else None,
                  eng.version if eng else "?") + sounds_md(sounds) + ui_md(uis) + fonts_md(fonts)
        + sprites_md(sprites),
        encoding="utf-8")
    (out / "ATTRIBUTION.md").write_text(
        f"# {mod.TITLE}\n\nLicence: {licence}. {LICENCES.get(licence, '')}\n\n"
        "Every asset was generated by code in the cadkit workspace (meshes and textures are "
        "procedural, sounds are synthesised); no third-party samples were used.\n\n"
        + ("Generative-model inputs, each checked by a person before this pack was made:\n\n" + "\n".join(
            f"- `{e['id']}` uses `{g['id']}`: {g['provider']} {g['model']}, prompt \"{g['prompt']}\". "
            f"Cleared by {g['cleared_by']}: {g.get('cleared_note')}. Terms: {g.get('terms')}"
            for e in entries for g in e.get("generated_inputs", [])) + "\n"
           if any(e.get("generated_inputs") for e in entries) else "No generative-model inputs were used.\n"),
        encoding="utf-8")
    manifest["out"] = str(out)
    if not quiet:
        t = manifest["totals"]
        print(f"{mod.TITLE}: {t['models']} models ({t['triangles']:,} triangles), {t['sounds']} sounds "
              f"({t['sound_seconds']:g} s), {t['interfaces']} interfaces, {t['fonts']} fonts, "
              f"{t['sprite_sheets']} sprite sheets, "
              f"{t['bytes'] / 1e6:.1f} MB")
        if demo and "summary" in demo:
            print("demo     " + demo["summary"])
        for p in problems:
            print("PROBLEM  " + p)
        print(f"ready    {'YES' if ready else 'NO'}\npack     {out}")
    return manifest


def install(name, dest, cook=False):
    """Copy a built pack into a game folder as <dest>/<name>; optionally cook it there."""
    src = PACKS_OUT / name
    m = outputs.load_json(src / "manifest.json", None)
    if m is None:
        raise SystemExit(f"no built pack '{name}': cad game pack packs/{name}.py")
    if not m["ready"]:
        raise SystemExit(f"pack '{name}' is not ready: " + "; ".join(m["problems"]))
    dst = Path(dest) / name
    shutil.copytree(src, dst, dirs_exist_ok=True)
    result = dict(installed=str(dst), assets=len(m["assets"]))
    if cook:
        eng = E.find()
        if eng is None:
            raise SystemExit("--cook needs a Cinder engine (set CAD_CINDER)")
        ck = eng.cook(dst / "cooked", *sorted((dst / "assets").glob("*.glb")), timeout=900)   # models only
        result["cook"] = dict(ok=ck["ok"], outputs=ck["outputs"])
    return result
