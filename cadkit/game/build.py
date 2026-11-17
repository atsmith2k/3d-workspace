"""Build one game asset and run the readiness ladder.

    static   spec checks + checks every model gets, on the model and on the GLB read back
    cook     cinder-cook accepts the GLB and writes what its contents predict
    engine   it loads and draws in cinder-play (no GPU errors); a solid prop is dropped onto
             a floor and must come to rest where its visual bounds say
    look     <name>_preview.png, rendered by Cinder, for the agent to read

Writes output/game/<name>/: <name>.glb, <name>_preview.png, build.json, readiness.json,
report.txt, cooked/ (a cache for this engine build only).
"""
import importlib.util
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from .. import outputs
from . import checks as C
from . import engine as E
from . import gltf
from .model import Model
from .render import render_sheet

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "output" / "game"
KINDS = ("prop", "environment", "character", "sound", "ui", "sprite", "font")                       # built today; see `cad game schema`
VIEWS = (("front right", 35), ("front left", -40), ("back left", 215), ("back right", 140))


def load_asset(path):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    for p in (str(path.parent), str(ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec.loader.exec_module(mod)
    return mod


def parse_overrides(defaults, pairs):
    p = dict(defaults)
    for pair in pairs or []:
        key, _, raw = pair.partition("=")
        if key not in p:
            raise SystemExit(f"unknown parameter '{key}'; known: {', '.join(p)}")
        kind = type(p[key])
        p[key] = raw.lower() in ("1", "true", "yes", "on") if kind is bool else kind(raw)
    return p


def rest_y(model, eng_cfg):
    """Height of the origin when the asset is in place on a floor at Y=0. ENGINE["rest_y"]
    overrides it (a floor tile's top is its origin: 0; a wall piece hangs where it is put)."""
    if "rest_y" in eng_cfg:
        return float(eng_cfg["rest_y"])
    return float(-model.bounds[0][1])


def snippet(name, model, eng_cfg, rel="assets"):
    """Paste-ready world-file lines that stand the asset on the floor at the origin."""
    lines = [f"entity {name}", f"  transform position=[0,{rest_y(model, eng_cfg):.4g},0]",
             f'  model path="{rel}/{name}.glb"']
    if eng_cfg.get("body"):
        lines.append(f'  body motion="{eng_cfg["body"]}" collider="{eng_cfg.get("collider", "auto")}"')
    return "\n".join(lines)


def _visibility(eng, glb, bounds, stage):
    """Share of the frame the asset changes: the same stage with and without it, compared.
    `ok` and a counted model do not prove anything was drawn (the world kit loads a skinned
    model and draws nothing), so the ladder looks."""
    from PIL import Image, ImageChops

    def shot(empty):
        world = stage / f"vis_{int(empty)}.world"
        world.write_text(E.staging_world(glb, bounds, 35, reference=False, empty=empty), encoding="utf-8")
        png = stage / f"vis_{int(empty)}.png"
        png.unlink(missing_ok=True)
        eng.play(world, frames=3, screenshot=png, width=480, height=270)
        return png

    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = pool.map(shot, (False, True))
    if not (a.exists() and b.exists()):
        return 0.0
    with Image.open(a) as ia, Image.open(b) as ib:
        diff = np.asarray(ImageChops.difference(ia.convert("RGB"), ib.convert("RGB"))).max(2)
    return float((diff > 12).mean())


def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def _engine_step(eng, glb, model, out, eng_cfg, name):
    """Turntable frames (in parallel: one world per process), a visibility test and the
    physics test. A skinned model is also shown as a static bake of its bind pose, because the
    world kit of Cinder 0.1.1 does not draw skinned meshes."""
    bounds = model.bounds
    stage = out / "staging"
    stage.mkdir(exist_ok=True)
    rigged = getattr(model, "skeleton", None) is not None
    seen = _visibility(eng, glb, bounds, stage)
    source = glb
    if rigged and seen < 0.002:
        glb = stage / f"{name}_bind.glb"                 # same mesh, no skin: what the bind pose looks like
        gltf.write_glb(Model(*model.parts), glb, name)

    def view(item):
        label, az = item
        world = stage / f"view_{az}.world"
        world.write_text(E.staging_world(glb, bounds, az, title=name), encoding="utf-8")
        shot = stage / f"view_{az}.png"
        shot.unlink(missing_ok=True)
        rep = eng.play(world, frames=3, screenshot=shot, width=960, height=540)
        return label, shot if shot.exists() else None, rep

    with ThreadPoolExecutor(max_workers=2) as pool:
        views = list(pool.map(view, VIEWS))
    problems = []
    for label, shot, rep in views:
        if not rep.get("ok"):
            problems.append(f"{label}: {rep.get('error', 'not ok')}")
        elif rep.get("run", {}).get("gpu_errors", 0):
            problems.append(f"{label}: {rep['run']['gpu_errors']} GPU validation errors")
        elif rep.get("world", {}).get("models") != 1:
            problems.append(f"{label}: the model was not counted")
        elif shot is None:
            problems.append(f"{label}: no frame written")
    step = dict(ok=not problems, problems=problems, frames=len([v for v in views if v[1]]),
                adapter=next((v[2].get("run", {}).get("adapter") for v in views if v[2].get("run")), None),
                visible_share=round(seen, 4), drawn=seen >= 0.002)
    if rigged:
        step["skinned_drawn_by_world_kit"] = seen >= 0.002
        step["frames_show"] = "the skinned model" if seen >= 0.002 else "a static bake of the bind pose"
        rep = eng.play(_write(stage / "skinned.world", E.staging_world(source, bounds, 35, reference=False)), frames=3)
        if not rep.get("ok") or rep.get("run", {}).get("gpu_errors", 0):
            problems.append("the skinned GLB does not load cleanly: " + str(rep.get("error", "GPU errors")))
            step["ok"] = False
    elif seen < 0.002:
        problems.append("nothing was drawn: the frame with the asset equals the frame without it")
        step["ok"] = False
    glb = source

    body = eng_cfg.get("body")
    if body:
        lo, hi = bounds
        drop = 0.5 if body == "dynamic" else 0.0
        world = stage / "physics.world"
        world.write_text(E.staging_world(glb, bounds, 35, body=body, drop=drop, reference=False,
                                         collider=eng_cfg.get("collider", "auto"), title=name),
                         encoding="utf-8")
        rep = eng.play(world, frames=240 if drop else 5)
        phys = dict(body=body, collider=eng_cfg.get("collider", "auto"), ok=bool(rep.get("ok")))
        if not rep.get("ok"):
            phys["detail"] = rep.get("error", "not ok")
        elif drop:
            pos = next(e["position"] for e in rep["result"]["entities"] if e["name"] == "asset")
            rest, height = -lo[1], hi[1] - lo[1]
            # Cinder 0.1.1 leaves any dropped body ~15 mm inside the floor (its own primitive
            # boxes too), so the floor of the tolerance sits above that.
            tol = max(0.03, 0.03 * height)
            dy, drift = pos[1] - rest, float(np.hypot(pos[0], pos[2]))
            phys.update(rest_y=round(pos[1], 4), expected_y=round(float(rest), 4), drift=round(drift, 4))
            phys["ok"] = bool(abs(dy) <= tol and drift <= max(0.1, 0.25 * height))
            phys["detail"] = (f"dropped 0.5 m: rests {dy * 1000:+.0f} mm from where its bounds say "
                              f"(tolerance {tol * 1000:.0f} mm), drifted {drift * 1000:.0f} mm")
        else:
            phys["detail"] = "static collider built and the world ran"
        step["physics"] = phys
        if not phys["ok"]:
            step["ok"] = False
            step["problems"].append("physics: " + phys["detail"])
    return step, [(label, shot) for label, shot, _ in views]


def _pose_strips(eng, model, out, name):
    """One engine frame per clip: five moments of the cycle side by side, skinned on the CPU
    and baked to a static GLB (the world kit cannot play a clip, so this is how a clip is seen)."""
    stage = out / "staging"
    stage.mkdir(exist_ok=True)

    def strip(clip):
        row = model.pose_row(clip, poses=5)
        glb = stage / f"{name}_{clip.name}_poses.glb"
        gltf.write_glb(row, glb, f"{name}_{clip.name}")
        world = stage / f"poses_{clip.name}.world"
        lo, hi = row.bounds                              # frame by height: the strip is a wide image
        world.write_text(E.staging_world(glb, row.bounds, 24, reference=False, title=clip.name,
                                         radius=0.62 * (hi[1] - lo[1])), encoding="utf-8")
        shot = stage / f"poses_{clip.name}.png"
        shot.unlink(missing_ok=True)
        rep = eng.play(world, frames=3, screenshot=shot, width=1600, height=400)
        return (f"{clip.name}: 5 moments of {clip.duration:g} s, left to right",
                shot if rep.get("ok") and shot.exists() else None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(strip, model.clips))


def build_asset(path, sets=(), out_root=None, use_engine=True, quiet=False, generate=False):
    """Build, verify and write one asset. Returns the build.json dict (also `ready`).

    Generated inputs (cadkit.game.gen) are read from assets/gen/; `generate=True` (`--gen`) lets a
    missing one be created by its service. Whatever the build read is recorded as `generated`, with
    `cleared` false while any of it has not been checked by a person: such an asset can be ready
    and still may not go into a pack."""
    from . import gen
    gen.begin(generate)
    b = _build_asset(path, sets, out_root, use_engine, quiet)
    inputs = gen.used()
    b["generated"] = [dict(id=r["id"], kind=r["kind"], provider=r["provider"], model=r["model"], prompt=r["prompt"],
                           cleared=r["cleared"], cleared_by=r["cleared_by"]) for r in inputs]
    b["cleared"] = all(r["cleared"] for r in inputs)
    if inputs:
        out = Path(b["out"])
        extra = [f"generated {r['id']}: {r['provider']} {r['model']}, \"{r['prompt'][:70]}\" "
                 + ("cleared by " + r["cleared_by"] if r["cleared"] else "NOT CLEARED: no pack will take this asset")
                 for r in inputs]
        b["report"] = b["report"][:-1] + extra + b["report"][-1:]
        saved = {k: v for k, v in b.items() if k != "out"}
        outputs.save_json(out / "build.json", saved)
        (out / "report.txt").write_text("\n".join(b["report"]) + "\n", encoding="utf-8")
        if not quiet:
            print("\n".join(extra))
    return b


def _build_asset(path, sets=(), out_root=None, use_engine=True, quiet=False):
    t0 = time.time()
    path = Path(path)
    mod = load_asset(path)
    name = path.stem
    kind = getattr(mod, "KIND", "prop")
    if kind not in KINDS:
        raise SystemExit(f"KIND '{kind}' is not built yet; this version builds: {', '.join(KINDS)}")
    params = parse_overrides(getattr(mod, "PARAMS", {}), sets)
    if kind == "sound":
        from .sound import build_sound
        return build_sound(path, mod, params, out_root or OUT, use_engine, quiet)
    if kind == "ui":
        from .ui import build_ui
        return build_ui(path, mod, params, out_root or OUT, use_engine, quiet)
    if kind == "sprite":
        from .sprite import build_sprite
        return build_sprite(path, mod, params, out_root or OUT, use_engine, quiet)
    if kind == "font":
        from .font import build_font
        return build_font(path, mod, params, out_root or OUT, use_engine, quiet)
    p = SimpleNamespace(**params)
    model = mod.build(p)
    if not isinstance(model, Model):
        raise SystemExit("build(p) must return a cadkit.game.Model")
    rigged = getattr(model, "skeleton", None) is not None
    eng_cfg = dict(getattr(mod, "ENGINE", {}) or {})
    out = Path(out_root or OUT) / name
    out.mkdir(parents=True, exist_ok=True)
    glb = out / f"{name}.glb"
    size_bytes = gltf.write_glb(model, glb, name)

    # ---- static
    ctx = SimpleNamespace(model=model, summary=gltf.summary(glb), params=params, name=name,
                          budget=getattr(mod, "BUDGET", None))
    spec = mod.checks(p) if callable(getattr(mod, "checks", None)) else []
    results = [c.run(ctx) for c in C.static_checks(model) + list(spec)]
    steps = dict(static=dict(ok=all(r["ok"] for r in results), checks=results))
    blockers = [f"check {r['name']}: {r['detail']}" for r in results if not r["ok"]]

    # ---- cook + engine
    eng = E.find() if use_engine else None
    shots = [(label, None) for label, _ in VIEWS]
    rows = []
    if eng is None:
        blockers.append("not verified in Cinder: " + ("skipped (--no-engine)" if not use_engine else
                        "no engine found; set CAD_CINDER to a Cinder package"))
    else:
        cooked = out / "cooked"
        shutil.rmtree(cooked, ignore_errors=True)
        ck = eng.cook(cooked, glb)
        want = dict(cmesh=ctx.summary["primitives"], cmat=ctx.summary["materials"],
                    ktx2=len(ctx.summary["images"]))
        if rigged:
            want.update(cskel=1, cclip=len(model.clips))
            cooked_clips = E.read_cooked_clips(cooked, name)
            ck["clips"] = cooked_clips
            by_name = {c["name"]: c for c in cooked_clips}
            for clip in model.clips:
                c = by_name.get(clip.name)
                tracks = len(clip.rotations) + len(clip.translations)
                if c is None:
                    blockers.append(f"cook: the engine wrote no clip named {clip.name}")
                elif (c["magic"] != "CCLP" or not c["consumed_all"] or abs(c["duration"] - clip.duration) > 1e-3
                      or c["channels"] != tracks):
                    blockers.append(f"cook: clip {clip.name} came out as {c['duration']} s with {c['channels']} "
                                    f"channels; built {clip.duration} s with {tracks}")
        short = [f"{k} {ck['outputs'].get(k, 0)}/{v}" for k, v in want.items() if ck["outputs"].get(k, 0) < v]
        ck["ok"] = ck["ok"] and not short
        ck["expected"] = want
        steps["cook"] = ck
        if not ck["ok"]:
            blockers.append("cook: " + (", ".join(short) or ck["text"][-200:]))
        steps["engine"], shots = _engine_step(eng, glb, model, out, eng_cfg, name)
        blockers += ["engine " + x for x in steps["engine"]["problems"]]
        if rigged:
            rows = _pose_strips(eng, model, out, name)
            missing = [label for label, png in rows if png is None]
            if missing:
                blockers.append("engine pose strip not rendered: " + ", ".join(missing))
    ready = not blockers

    lo, hi = model.bounds
    sz = hi - lo
    texs = [t for m in model.materials for t in m.textures().values()]
    lines = [
        f"{name}  ({kind})  {getattr(mod, 'DESCRIPTION', '')}",
        f"size     {sz[0]:.3f} x {sz[1]:.3f} x {sz[2]:.3f} m  (x, y up, z)",
        f"mesh     {model.triangles:,} triangles, {model.vertices:,} vertices, {len(model.parts)} primitive(s)"
        + (f"; nodes: {', '.join(n['name'] for n in ctx.summary['mesh_nodes'])}"
           if len(ctx.summary["mesh_nodes"]) > 1 else ""),
        f"textures {len(texs)}" + (f", largest {max(max(t.shape[:2]) for t in texs)} px" if texs else ""),
    ] + ([f"rig      {len(model.skeleton)} bones; clips " + ", ".join(
        f"{c.name} {c.duration:g} s" for c in model.clips)] if rigged else []) + [
        f"file     {glb.name} {size_bytes / 1024:.0f} kB",
    ]
    if any(m.alpha != "opaque" for m in model.materials):
        lines.append("alpha    this model uses alpha mask or blend: Cinder 0.1.1's colour pass draws both opaque "
                     "(forward shader bug), so transparent texels show the base colour")
    if "cook" in steps:
        lines.append("cook     " + ", ".join(f"{v} .{k}" for k, v in sorted(steps["cook"]["outputs"].items())
                                             if k != "root"))
    if "engine" in steps:
        e = steps["engine"]
        lines.append(f"engine   Cinder {eng.version} on {e.get('adapter')}: {e['frames']}/4 frames, "
                     + ("no problems" if not e["problems"] else f"{len(e['problems'])} problem(s)")
                     + f"; the asset covers {e['visible_share']:.1%} of a frame")
        if rigged and not e.get("skinned_drawn_by_world_kit"):
            lines.append("skinned  the world kit of this engine loads the skinned GLB but does not draw it (no "
                         "joint palette): frames show a static bake of the bind pose and of each clip")
        if rigged and steps["cook"].get("clips"):
            lines.append("cooked   " + "; ".join(
                f"{c['name']} {c['duration']:g} s, {c['channels']} channels, {c['keys']} keys"
                for c in steps["cook"]["clips"]) + "  (read back from the engine's .cclip files)")
        if "physics" in e:
            lines.append("physics  " + e["physics"]["detail"])
    for r in results:
        lines.append(f"check    {'PASS' if r['ok'] else 'FAIL'}  {r['name']}: {r['detail']}")
    for b in blockers:
        lines.append("BLOCKER  " + b)
    lines.append(f"ready    {'YES' if ready else 'NO'}")

    preview = out / f"{name}_preview.png"
    render_sheet(preview, shots, model, f"{name}: {getattr(mod, 'DESCRIPTION', '')}",
                 [l for l in lines if not l.startswith(("check", "BLOCKER", "ready"))], results, ready,
                 rows=rows)
    shutil.rmtree(out / "staging", ignore_errors=True)

    build = dict(
        schema="cadkit-game-build/1", name=name, kind=kind,
        description=getattr(mod, "DESCRIPTION", ""), params=params, ready=ready, blockers=blockers,
        stats=dict(size_m=[round(float(x), 4) for x in sz],
                   bounds=[[round(float(x), 4) for x in lo], [round(float(x), 4) for x in hi]],
                   triangles=model.triangles, vertices=model.vertices, materials=len(model.parts),
                   textures=[dict(material=m.name, slot=s, width=t.shape[1], height=t.shape[0])
                             for m in model.materials for s, t in m.textures().items()],
                   glb_bytes=size_bytes, nodes=ctx.summary["mesh_nodes"],
                   bones=len(model.skeleton) if rigged else 0,
                   clips=[dict(name=c.name, duration=c.duration, looping=c.looping) for c in model.clips]
                   if rigged else []),
        engine_use=eng_cfg, rest_y=round(rest_y(model, eng_cfg), 4),
        world_snippet=snippet(name, model, eng_cfg),
        product=dict(getattr(mod, "PRODUCT", {}) or {}), source_sha256=outputs.sha256(path),
        files=dict(glb=glb.name, preview=preview.name, sha256=outputs.sha256(glb)),
        engine=eng.info() if eng else None, steps=steps, report=lines,
        built_at=outputs.now_iso(), seconds=round(time.time() - t0, 1), git=outputs.git_info())
    outputs.save_json(out / "build.json", build)
    outputs.save_json(out / "readiness.json", dict(ready=ready, blockers=blockers, steps=steps,
                                                   engine=build["engine"]))
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    build["out"] = str(out)
    if not quiet:
        print("\n".join(lines))
        print(f"preview  {preview}")
    return build
