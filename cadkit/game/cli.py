"""`cad game ...`: game assets for the Cinder engine.

  cad game new <name> "<description>"     assets/<name>.py from the template
  cad game build assets/<name>.py [--set k=v] [--no-engine] [--json]
  cad game list [--json]
  cad game engine [--json]                which Cinder package verifies the builds
  cad game schema                         the contract, checks and conventions as JSON
  cad game pack packs/<name>.py [--refresh]   bundle a collection, play its demo world
  cad game install <name> --to <game dir> [--cook]

build writes output/game/<name>/: <name>.glb, <name>_preview.png (rendered by Cinder),
build.json, readiness.json, report.txt and cooked/. Exit status 0 only when `ready YES`.
"""
import json
import re
import sys
from pathlib import Path

from .. import outputs

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "assets"


def cmd_build(args):
    from . import build as B
    b = B.build_asset(ROOT / args.asset if not Path(args.asset).is_absolute() else args.asset,
                      args.set, use_engine=not args.no_engine, quiet=args.json, generate=args.gen)
    if args.json:
        print(json.dumps(b, indent=1))
    return 0 if b["ready"] else 1


def cmd_new(args):
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.name):
        sys.exit("name must be snake_case: it becomes the cook prefix and the file's base name")
    dst = ASSETS / f"{args.name}.py"
    if dst.exists():
        sys.exit(f"{dst} already exists")
    text = (ASSETS / "_template.py").read_text(encoding="utf-8")
    dst.write_text(text.replace("DESCRIPTION_HERE", args.description or args.name.replace("_", " ")),
                   encoding="utf-8")
    print(f"created {dst.relative_to(ROOT)}\nfill in the Spec, checks(p) and build(p), then: "
          f"cad game build assets/{args.name}.py")
    return 0


def _rows():
    from . import build as B
    rows = []
    for path in sorted(ASSETS.glob("*.py")):
        if path.name.startswith("_"):
            continue
        mod = B.load_asset(path)
        built = outputs.load_json(B.OUT / path.stem / "build.json", None)
        rows.append(dict(name=path.stem, kind=getattr(mod, "KIND", "prop"),
                         description=getattr(mod, "DESCRIPTION", ""),
                         built=bool(built), ready=bool(built and built.get("ready")),
                         triangles=built["stats"].get("triangles") if built else None))
    return rows


def cmd_list(args):
    rows = _rows()
    if args.json:
        print(json.dumps(rows, indent=1))
        return 0
    for r in rows:
        state = "ready" if r["ready"] else "built, NOT ready" if r["built"] else "not built"
        print(f"{r['name']:<28}{r['kind']:<13}{state:<18}{r['description']}")
    if not rows:
        print('no assets yet: cad game new <name> "<description>"')
    return 0


def cmd_engine(args):
    from . import engine as E
    eng = E.find()
    info = eng.info() if eng else dict(root=None, hint="set CAD_CINDER to a Cinder package folder "
                                       "(the one holding bin/cinder-play.exe)")
    if args.json:
        print(json.dumps(info, indent=1))
    elif eng:
        print(f"Cinder {eng.version} at {eng.root}\n  {eng.play_exe.name}, {eng.cook_exe.name}")
    else:
        print("no Cinder engine found: " + info["hint"])
    return 0 if eng else 1


def schema():
    from . import build as B, checks as C
    return dict(
        schema="cadkit-game/1",
        engine="Cinder 0.1 (https://cinder.ash10.dev)",
        conventions=dict(
            units="metres", up="+Y", forward="-Z", handedness="right", front_faces="counter-clockwise",
            pivot=dict(dynamic_prop="centre of bounds (the world kit centres box and sphere colliders "
                                    "on the entity)", static="base centre on Y=0", floor="top face centre",
                       wall_mounted="back face (+Z), hanging toward -Z", character="feet"),
            textures="row 0 is the top (v=0). base and emission sRGB; orm (occlusion R, roughness G, "
                     "metallic B) and normal (+Y, glTF) linear; power of two, at most 8192 px",
            names="snake_case, unique across a pack: cinder-cook derives the cook prefix from the base name"),
        kinds=dict(built=list(B.KINDS),
                   planned=["prefab"],
                   note="worlds are built by pack scripts (packs/<name>.py, demo(w))"),
        ui=dict(
            returns="cadkit.game.ui.UiSet(Ui)",
            build='Ui(Theme()); root(anchor, name, offset), panel(parent, row), label, button, toggle, slider',
            files="<name>.ui.txt (cinder-scene 1, what Ui.to_text writes), <name>.theme.json, <name>.mojo",
            checks={"has(name, kind)": "a named node exists", "node_at_least(name, w, h)": "laid-out size in px"},
            engine="cinder-probe: Ui.from_text, layout at 1280 x 720, headless frame, Ui.to_text compared",
            limits="no images, text fields, scrolling or wrapping in cinder.ui; the theme is not in the document"),
        fonts=dict(
            returns="cadkit.game.font.FontFace(glyphs, family, tracking)",
            glyphs="shapely shapes on a 10-unit cap grid, baseline y = 0; block_glyphs(stroke) is the owned block alphabet",
            files="<name>.ttf (1000 units per em, cap height 700), <name>.json",
            checks={"covers(chars)": "drawn, not a fallback", "stroke_at(px, min_px)": "thinnest stroke at a size",
                    "distinct(a, b)": "a confusable pair differs"},
            engine="cinder-probe: Font.from_file, bake at 24 px, text drawn at 48, 24 and 18 px; the engine's pixels "
                   "must overlap the glyph shapes by 70 %",
            limits="Cinder: code points 32..255, one font per interface, no kerning; no public UI font setting",
            ui='UiSet(ui, font="<font asset>") sets an interface in it'),
        sprites=dict(
            returns="cadkit.game.sprite.SpriteSheet(frames, animations, slices)",
            files="<name>.png + <name>.json (cadkit-sprites/1) + <name>_quads.glb (proof)",
            checks={"frames(*names)": "exact frame list", "frame_size(w, h)": "pixels",
                    "animation(name, count, fps)": "a frame animation", "nine_slice(name)": "stretchable borders"},
            engine="built ahead: no sprite renderer or UI images in Cinder 0.1.1; drawn on unlit quads, where "
                   "alpha mask is ignored by the engine today"),
        blender=dict(
            what="headless Blender as a kernel for high-resolution assets: sculpt a high-poly shape, derive a "
                 "light mesh, unwrap it, bake the detail into maps; the result is an ordinary Mesh and images",
            api="from cadkit.game import blender as B; s = B.Session(); s.add(mesh, name, emit=), s.modify(name, "
                "B.subsurf(n), B.displace(texture, scale, strength), B.inflate(d), B.bevel(), {raw modifier}), "
                "s.boolean(a, b), s.remesh(a, voxel), s.copy(a, name), s.decimate(a, tris), s.shade(a, sharp_angle), "
                "s.unwrap(a), s.bake(high, low, size, maps), s.weights(a, skeleton), s.get(a); r = s.run(); "
                "r.mesh(name), r.image(map), r.skin(name); B.bake_lowpoly(high, tris, size, maps)",
            maps=dict(normal="tangent space, glTF convention", ao="ambient occlusion", curvature="0.5 flat, bright "
                      "convex, dark concave", emit="emission of the high-poly materials: a mask of cut faces"),
            texturing="texel_maps(mesh, size) -> position, normal, mask per texel; noise3 / fbm3 for seam-free "
                      "world-space noise; fill_background(img, mask); check uv_unique()",
            run="blender -b --factory-startup --python tools/blender_bridge/bridge.py -- <job folder>; cached in "
                "output/game/.blender by a hash of steps, inputs, bridge and Blender version",
            find="CAD_BLENDER, else the newest under Program Files, else PATH; cad game blender"),
        generated=dict(
            api='from cadkit.game import gen; gen.image(prompt, name=, size=, provider="openai"); '
                'gen.sound(prompt, name=, seconds=, provider="elevenlabs"); gen.material(img, name); gen.tileable(img)',
            rule="a build reads assets/gen/ and never calls a service unless run with --gen",
            record="assets/gen/<id>.json: prompt, provider, model, parameters, cleared",
            shipping="cad game pack refuses an asset with an uncleared input; a person clears it with "
                     "cad game gen clear <id> --by NAME --note TEXT",
            keys="OPENAI_API_KEY, ELEVENLABS_API_KEY in the environment or the git-ignored .env"),
        sounds=dict(
            returns="cadkit.game.audio.Sound(samples, loop, bus, spatial, streamed)",
            format="WAV, 48 kHz, 16-bit PCM; one-shots mono and spatial; music stereo, not spatial, streamed",
            checks={"duration(lo, hi)": "seconds", "band(lo_hz, hi_hz, at_least, at_most)": "share of energy in a band",
                    "peak(lo_db, hi_db)": "peak level in dBFS"},
            always=["name", "format", "level", "edges", "channels", "budget"],
            engine="the sample game, headless, opens the file as its music (with a garbage-file control)",
            judge="waveform and spectrogram in <name>_preview.png; nobody can listen",
            sounddesc="cinder.audio SoundDesc(path, bus, streamed, looping, spatial)"),
        characters=dict(
            returns="cadkit.game.Character(skeleton)",
            skeleton="biped(height): 18 bones, root at the feet, A-pose, faces +Z; or Skeleton().add(name, parent, head)",
            bind='ch.add(mesh, material, bind="bone") rigid, or bind=[bones], blend=metres across joints',
            clips='Clip.cycle(name, seconds, pose_fn, keys); pose_fn(phase) -> {bone: euler(x, y, z), "bone:move": (dx, dy, dz)}',
            limits="256 bones, 4 influences, in-place clips, phase 0 = left foot strike",
            engine_note="Cinder 0.1.1's world kit does not draw skinned models; use them from a Mojo Game"),
        contract=dict(
            KIND="one of kinds.built", DESCRIPTION="one line",
            PARAMS="dict of tunables; types drive --set; include seed for anything random",
            BUDGET="dict(tris=, texture=, materials=): hard limits checked on every build",
            ENGINE='dict(body="dynamic"|"static"|"kinematic", collider="auto"|"box"|"sphere"|"mesh"): '
                   "how a world uses it; drives the physics test and the world snippet",
            checks="checks(p) -> list of checks", build="build(p) -> cadkit.game.Model(*(mesh, material))"),
        checks=dict(
            spec={"size(x, y, z, tol=0.01)": "overall size in metres; number +-tol or (lo, hi)",
                  "tris(max, min=0)": "triangle count", "materials(max)": "materials = draw calls",
                  "texture_size(max)": "largest texture side",
                  'pivot("centre"|"base"|"top"|"back"|(fx, fy, fz))': "where the origin is in the bounds",
                  "tiles(image_of)": "a texture repeats without a seam",
                  "clips(*names)": "a character has exactly these clips",
                  'phase_matched(a, b, bone="foot.L")': "two cycles strike at the same phase",
                  "custom(name, fn)": "fn(ctx) -> (ok, detail); ctx.model, ctx.summary, ctx.params"},
            always=[c.name for c in C.static_checks()]),
        ladder=["static: spec checks and the always checks, on the model and on the GLB read back",
                "cook: cinder-cook accepts it and writes one .cmesh per primitive, .cmat per material, "
                ".ktx2 per image",
                "engine: loads in cinder-play headless with no GPU errors and visibly changes the frame; "
                "a body is dropped 0.5 m and must rest where its bounds say; a character's cooked .cclip "
                "files are parsed back and compared",
                "look: <name>_preview.png rendered by Cinder; read it before delivering"],
        budgets=dict(small_prop="300-1500 triangles", hero_prop="5000-15000", character="8000-20000",
                     texel_density="512 px per metre (1024 for hero pieces)"),
        request=dict(kind="prop | environment | character | material | sound | font | ui | sprite | world",
                     name="snake_case", use="what it is for and what it stands next to",
                     size="metres for 3D, pixels for 2D, seconds for sound", style="look",
                     budget="optional", notes="optional"),
        packs=dict(script="packs/<name>.py: TITLE, DESCRIPTION, COLLECTION, LICENCE, DEMO, SHOTS, demo(w)",
                   command="cad game pack packs/<name>.py [--refresh]; cad game install <name> --to <dir> [--cook]",
                   manifest="output/game/packs/<name>/manifest.json, schema cadkit-game/1"),
        outputs="output/game/<name>/: <name>.glb, <name>_preview.png, build.json, readiness.json, "
                "report.txt, cooked/")


def cmd_schema(args):
    print(json.dumps(schema(), indent=1))
    return 0


def cmd_pack(args):
    from . import pack as P
    path = ROOT / args.pack if not Path(args.pack).is_absolute() else Path(args.pack)
    m = P.build_pack(path, refresh=args.refresh, quiet=args.json)
    if args.json:
        print(json.dumps(m, indent=1))
    return 0 if m["ready"] else 1


def cmd_install(args):
    from . import pack as P
    r = P.install(args.name, args.to, cook=args.cook)
    print(json.dumps(r, indent=1) if args.json else
          f"installed {r['assets']} assets to {r['installed']}"
          + (f"; cooked {r['cook']['outputs']}" if "cook" in r else ""))
    return 0 if r.get("cook", {}).get("ok", True) else 1


def cmd_gen(args):
    from . import gen
    if args.gen_cmd == "keys":
        have = gen.keys_present()
        print(json.dumps(have, indent=1) if args.json else "\n".join(
            f"{gen.KEYS[p]:<22}{'set' if ok else 'not set'}   ({p})" for p, ok in have.items()))
        return 0
    if args.gen_cmd == "clear":
        rec = gen.clear(args.id, args.by, args.note)
        print(f"{rec['id']} cleared by {rec['cleared_by']}: {rec['cleared_note']}")
        return 0
    recs = gen.records()
    if args.json:
        print(json.dumps(recs, indent=1))
    else:
        for r in recs:
            state = f"cleared by {r['cleared_by']}" if r["cleared"] else "NOT CLEARED"
            print(f"{r['id']:<28}{r['kind']:<7}{r['provider']:<12}{state:<28}{r['prompt'][:60]}")
        if not recs:
            print("no generated inputs (assets/gen/ is empty)")
    return 0


def cmd_blender(args):
    from . import blender as BL
    i = BL.info()
    if args.json:
        print(json.dumps(i, indent=1))
    elif i["blender"]:
        print(f"Blender {i['version']} at {i['blender']}")
        print(f"  bridge {BL.BRIDGE}")
        print(f"  cache  {BL.CACHE}")
    else:
        print("no Blender found: " + i["hint"])
    return 0 if i["blender"] else 1


def cmd_probe(args):
    from . import engine as E
    if args.probe_cmd == "build":
        ok, text = E.probe_build()
        print(text)
        return 0 if ok else 1
    info = E.probe_info()
    print(json.dumps(info, indent=1))
    return 0 if info.get("probe") else 1


def add_parser(sub):
    g = sub.add_parser("game", help="game assets for the Cinder engine (glTF, verified in-engine)")
    gs = g.add_subparsers(dest="game_cmd", required=True)
    b = gs.add_parser("build", help="build, verify in Cinder and render an asset")
    b.add_argument("asset")
    b.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    b.add_argument("--no-engine", action="store_true", help="skip cook and engine (never ready)")
    b.add_argument("--json", action="store_true", help="print build.json instead of the report")
    b.add_argument("--gen", action="store_true",
                   help="let a generated input that is not in assets/gen/ be created (a paid call to its service)")
    n = gs.add_parser("new", help="start an asset from the template")
    n.add_argument("name")
    n.add_argument("description", nargs="?", default="")
    li = gs.add_parser("list", help="assets and whether they are built and ready")
    li.add_argument("--json", action="store_true")
    e = gs.add_parser("engine", help="the Cinder package used for verification")
    e.add_argument("--json", action="store_true")
    gs.add_parser("schema", help="contract, checks and conventions as JSON")
    ge = gs.add_parser("gen", help="generated inputs: list them, see which keys are set, clear one for shipping")
    ges = ge.add_subparsers(dest="gen_cmd", required=True)
    for name in ("list", "keys"):
        x = ges.add_parser(name)
        x.add_argument("--json", action="store_true")
    gc = ges.add_parser("clear", help="record that a person checked a generated input and it may ship")
    gc.add_argument("id")
    gc.add_argument("--by", required=True, help="who checked it")
    gc.add_argument("--note", required=True, help="what was checked (terms, no trademark or likeness, ...)")
    bl = gs.add_parser("blender", help="the Blender used for high-poly sculpting and baking")
    bl.add_argument("--json", action="store_true")
    pr = gs.add_parser("probe", help="cinder-probe: our Mojo program that asks the engine about UI and fonts")
    pr.add_argument("probe_cmd", choices=["build", "status"])
    pk = gs.add_parser("pack", help="bundle a collection into a self-describing pack and play its demo world")
    pk.add_argument("pack", help="packs/<name>.py")
    pk.add_argument("--refresh", action="store_true", help="rebuild every member first")
    pk.add_argument("--json", action="store_true")
    ins = gs.add_parser("install", help="copy a built pack into a game folder")
    ins.add_argument("name")
    ins.add_argument("--to", required=True, help="game folder; the pack lands in <to>/<name>")
    ins.add_argument("--cook", action="store_true", help="also cinder-cook it into <to>/<name>/cooked")
    ins.add_argument("--json", action="store_true")


def run(args):
    return dict(build=cmd_build, new=cmd_new, list=cmd_list, engine=cmd_engine, schema=cmd_schema,
                pack=cmd_pack, install=cmd_install, probe=cmd_probe, gen=cmd_gen,
                blender=cmd_blender)[args.game_cmd](args)
