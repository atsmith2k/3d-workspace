"""cadkit command line.

  python -m cadkit build models/foo.py [--set name=value ...] [--fast] [--no-render] [--slice]
  python -m cadkit slice models/foo.py [--set ...] [--profile printer.ini] [--supports]
  python -m cadkit new foo "one-line description"
  python -m cadkit list
  python -m cadkit selftest

`build` runs the model's build(p), checks the result is printable, and writes
output/<model>/<model>.stl (+ .step for B-rep models), preview.png and report.txt.
`slice` runs PrusaSlicer headlessly on the built STL(s) and reports print time,
filament and whether supports were generated.
"""
import argparse
import importlib.util
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from . import checks as checksmod
from . import measure as measuremod
from . import mesh as meshmod
from . import printers
from . import slicer
from .render import render_sheet

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = ROOT / "tests" / "expected.json"


def load_model(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path[:0] = [str(path.parent), str(ROOT)]
    spec.loader.exec_module(mod)
    return mod


def parse_overrides(defaults, pairs):
    p = dict(defaults)
    for pair in pairs:
        key, _, raw = pair.partition("=")
        if key not in p:
            sys.exit(f"unknown parameter '{key}'; known: {', '.join(p)}")
        kind = type(p[key])
        if kind is bool:
            p[key] = raw.lower() in ("1", "true", "yes", "on")
        else:
            p[key] = kind(raw)
    return p


def parse_sections(specs):
    """--section y=10 --section x=0  ->  [(1, 10.0), (0, 0.0)]"""
    out = []
    for s in specs or []:
        axis, _, val = s.partition("=")
        if axis.lower() not in "xyz" or not val:
            sys.exit(f"--section wants x=<mm>, y=<mm> or z=<mm>, got '{s}'")
        out.append(("xyz".index(axis.lower()), float(val)))
    return out


def printer_of(args):
    """(key, definition, bed) for --printer, with --bed overriding the bed size."""
    key = getattr(args, "printer", None) or printers.DEFAULT
    pr = printers.get(key)
    bed = tuple(args.bed) if getattr(args, "bed", None) else pr["bed"]
    return key, pr, bed


def resolve_output(args):
    """Output folder name for a model + overrides: variants get their own folder,
    e.g. butterfly_paver_mold_square."""
    path = Path(args.model).resolve()
    suffix = "_".join(pair.partition("=")[2] for pair in args.set)
    name = args.name or path.stem + (f"_{suffix}" if suffix else "")
    name = "".join(c if c.isalnum() or c in "-_." else "-" for c in name)
    return path, name, Path(args.out or ROOT / "output") / name


def model_checks(mod, p, part_name, single):
    """CHECKS list / dict, or checks(p) function, resolved for one part."""
    spec = mod.checks(p) if callable(getattr(mod, "checks", None)) else getattr(mod, "CHECKS", None)
    if isinstance(spec, dict):
        return spec.get(part_name, []) if not single else next(iter(spec.values()), [])
    return spec or []


def export(part, name, out, args, title, checks=(), params=None):
    t0 = time.time()
    tol = 0.05 if args.fast else 0.01
    tm = meshmod.to_trimesh(part, tolerance=tol)
    stl = out / f"{name}.stl"
    tm.export(stl)
    files = [stl]
    if hasattr(part, "tessellate") and not args.fast:
        from build123d import export_step
        step = out / f"{name}.step"
        export_step(part, str(step))
        files.append(step)
    _, pr, bed = printer_of(args)
    rep = meshmod.check(tm, bed=bed, thickness_samples=2000 if args.fast else 4000, bed_name=pr["name"])
    rep.stl_bytes = stl.stat().st_size
    if rep.stl_bytes > meshmod.TINKERCAD_MAX_BYTES:
        rep.warnings.append("STL is over Tinkercad's 25 MB import limit; rebuild with --fast")
    ctx = SimpleNamespace(tm=tm, report=rep, params=params, name=name)
    rep.checks_ok, check_lines = checksmod.run_checks(checks, ctx)
    if not rep.checks_ok:
        failed = [l.split("FAIL ", 1)[1] for l in check_lines if "FAIL" in l]
        rep.warnings.append(f"{len(failed)} check{'s' if len(failed) > 1 else ''} failed: " + "; ".join(failed))
    lines = rep.lines() + check_lines
    if not args.no_render:
        png = out / f"{name}_preview.png"
        render_sheet(tm, png, title, lines, overhang_faces=rep.overhang_faces,
                     thin_faces=rep.thin_faces, sections=parse_sections(getattr(args, "section", None)))
        files.append(png)
    print(f"\n== {name} ({time.time() - t0:.1f}s export)")
    for line in lines:
        print("  " + line)
    for f in files:
        print(f"  -> {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}")
    return lines, rep


def cmd_build(args):
    path, name, out = resolve_output(args)
    mod = load_model(path)
    defaults = getattr(mod, "PARAMS", {})
    p = parse_overrides(defaults, args.set)
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    result = mod.build(SimpleNamespace(**p))
    print(f"built {name} in {time.time() - t0:.1f}s")
    parts = result if isinstance(result, dict) else {name: result}

    _, pr, bed = printer_of(args)
    report = [f"# {name}", getattr(mod, "DESCRIPTION", "").strip(), "",
              "params: " + ", ".join(f"{k}={v}" for k, v in p.items()),
              f"printer: {pr['name']}, bed {bed[0]:g} x {bed[1]:g} x {bed[2]:g} mm", ""]
    all_ok = True
    reports = {}
    for part_name, part in parts.items():
        fname = part_name if part_name == name else f"{name}-{part_name}"
        chk = model_checks(mod, SimpleNamespace(**p), part_name, not isinstance(result, dict))
        lines, rep = export(part, fname, out, args, fname, checks=chk, params=SimpleNamespace(**p))
        report += [f"## {fname}", *lines, ""]
        all_ok &= rep.ok and rep.checks_ok
        reports[fname] = rep
    (out / "report.txt").write_text("\n".join(report), encoding="utf-8")
    if getattr(args, "slice", False) and all_ok:
        slice_folder(out, name, args)
    args.reports = reports
    return 0 if all_ok else 1


def slice_folder(out, name, args):
    """Slice every STL in an output folder; append the numbers to report.txt."""
    stls = sorted(out.glob(f"{name}*.stl"))
    if not stls:
        sys.exit(f"nothing built in {out}; run build first")
    key, pr, _ = printer_of(args)
    if not slicer.find_slicer():
        print("  slice    skipped: no Bambu Studio or PrusaSlicer found (set CAD_BAMBU / CAD_SLICER)")
        return None
    report = (out / "report.txt").read_text(encoding="utf-8").split("\n") if (out / "report.txt").exists() else []
    report = [l for l in report if not l.startswith("## slice")]  # keep it idempotent
    results = []
    for stl in stls:
        t0 = time.time()
        try:
            res = slicer.slice_stl(stl, out, printer_key=key,
                                   layer_height=getattr(args, "layer_height", 0.2),
                                   infill=getattr(args, "infill", 15),
                                   supports=getattr(args, "supports", False),
                                   filament=getattr(args, "filament", None),
                                   profile=getattr(args, "profile", None),
                                   prefer=getattr(args, "slicer", "auto"))
        except Exception as e:
            print(f"  slice    FAILED for {stl.name}: {e}")
            continue
        lines = res.lines()
        print(f"\n== slice {stl.stem} with {res.slicer} ({time.time() - t0:.1f}s)")
        for line in lines:
            print("  " + line)
        f = res.project or res.gcode
        print(f"  -> {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}")
        report += [f"## slice {stl.stem} ({res.slicer})", *lines, ""]
        results.append(res)
    (out / "report.txt").write_text("\n".join(report), encoding="utf-8")
    return results


def cmd_slice(args):
    path, name, out = resolve_output(args)
    if not list(out.glob(f"{name}*.stl")):
        print(f"{name} not built yet; building first")
        args.fast, args.no_render, args.slice = False, False, False
        if cmd_build(args) != 0:
            return 1
    return 0 if slice_folder(out, name, args) else 1


def cmd_measure(args):
    """Numbers about a built part: size, bounds, volume, centroid, plus --probe points
    (inside? distance to surface? thickness?) and --hole diameter measurements."""
    import trimesh
    path, name, out = resolve_output(args)
    stls = sorted(out.glob(f"{name}*.stl"))
    if not stls:
        print(f"{name} not built yet; building first")
        args.fast, args.no_render, args.slice = True, True, False
        cmd_build(args)
        stls = sorted(out.glob(f"{name}*.stl"))
    for stl in stls:
        tm = trimesh.load(stl)
        print(f"== {stl.stem}")
        for line in measuremod.summary(tm):
            print("  " + line)
        for spec in args.probe or []:
            pt = [float(v) for v in spec.split(",")]
            r = measuremod.probe(tm, pt)
            print(f"  probe    {r['point']}: {'INSIDE' if r['inside'] else 'outside'}, "
                  f"{r['distance_to_surface']} mm to surface, thickness {r['thickness']} mm")
        for spec in args.hole or []:
            parts = spec.split(",")
            at = (float(parts[0]), float(parts[1]))
            axis = parts[2] if len(parts) > 2 else "z"
            mean_d, min_d = measuremod.hole_diameter(tm, at, axis)
            print(f"  hole     at {at} along {axis}: diameter {mean_d:.2f} mm (min {min_d:.2f})"
                  if mean_d else f"  hole     at {at} along {axis}: material there, no hole")
    return 0


def cmd_new(args):
    dest = ROOT / "models" / f"{args.name}.py"
    if dest.exists():
        sys.exit(f"{dest} already exists")
    text = (ROOT / "models" / "_template.py").read_text(encoding="utf-8")
    dest.write_text(text.replace("DESCRIPTION_HERE", args.description), encoding="utf-8")
    print(f"created {dest.relative_to(ROOT)}")


def cmd_list(args):
    models = sorted(p for p in (ROOT / "models").glob("*.py") if not p.name.startswith("_"))
    if not models:
        print("no models yet; start one with: new <name> \"<description>\"")
    for path in models:
        desc = getattr(load_model(path), "DESCRIPTION", "")
        built = (ROOT / "output" / path.stem / f"{path.stem}.stl").exists()
        print(f"{path.stem:28} {'built ' if built else '      '} {desc}")
    return 0


def cmd_selftest(args):
    """Regression suite: build every model listed in tests/expected.json (fast mode)
    into a temp folder and compare size, volume, body count and check results with
    the recorded values. `--update` re-records them. Slices the template too if a
    slicer is installed."""
    import json
    from importlib.metadata import version
    print(f"python {sys.version.split()[0]}, " + ", ".join(
        f"{pkg} {version(pkg)}" for pkg in ("build123d", "manifold3d", "trimesh", "rtree", "numpy", "pillow")))
    bambu, prusa = slicer.find_bambu(), slicer.find_prusa()
    print(f"slicers: Bambu Studio {bambu or 'not found'}; PrusaSlicer {prusa or 'not found'}")
    exe = bambu or prusa
    expected = json.loads(EXPECTED.read_text(encoding="utf-8")) if EXPECTED.exists() else {}
    if not expected:
        expected = {"_template": {"model": "_template.py", "set": []},
                    "butterfly_paver_mold": {"model": "butterfly_paver_mold.py", "set": []}}
    failures, recorded = [], {}
    with tempfile.TemporaryDirectory() as tmp:
        for key, exp in expected.items():
            ns = argparse.Namespace(model=str(ROOT / "models" / exp["model"]), set=exp.get("set", []),
                                    name=key, fast=True, no_render=False, bed=None, printer="a1", out=tmp,
                                    section=None, slice=False)
            try:
                rc = cmd_build(ns)
            except Exception as e:
                failures.append(f"{key}: {type(e).__name__}: {e}")
                continue
            if not list((Path(tmp) / key).glob("*_preview.png")):
                failures.append(f"{key}: no preview rendered")
            got = {}
            for part, rep in ns.reports.items():
                got[part] = dict(size=[round(float(v), 1) for v in rep.size],
                                 volume_cm3=round(rep.volume_cm3, 1), bodies=rep.bodies,
                                 watertight=rep.watertight, checks_ok=rep.checks_ok)
            recorded[key] = dict(exp, parts=got)
            if rc != 0:
                failures.append(f"{key}: build reported failure (see WARNING/FAIL lines above)")
            for part, want in exp.get("parts", {}).items():
                have = got.get(part)
                if have is None:
                    failures.append(f"{key}: part {part} missing")
                    continue
                if any(abs(a - b) > 0.5 for a, b in zip(have["size"], want["size"])):
                    failures.append(f"{key}/{part}: size {have['size']} != expected {want['size']}")
                if abs(have["volume_cm3"] - want["volume_cm3"]) > 0.02 * max(want["volume_cm3"], 0.1):
                    failures.append(f"{key}/{part}: volume {have['volume_cm3']} != expected {want['volume_cm3']} (+-2%)")
                if have["bodies"] != want["bodies"] or have["watertight"] != want["watertight"]:
                    failures.append(f"{key}/{part}: {have['bodies']} bodies, watertight={have['watertight']}; "
                                    f"expected {want['bodies']}, {want['watertight']}")
            if "parts" not in exp:
                print(f"  (no recorded expectation for {key} yet; run selftest --update)")
        if exe:
            ns = argparse.Namespace(model=str(ROOT / "models" / "_template.py"), set=[], name=None,
                                    out=tmp, profile=None, layer_height=0.2, infill=15, supports=False,
                                    printer="a1", bed=None, filament=None, slicer="auto")
            try:
                res = slice_folder(Path(tmp) / "_template", "_template", ns)
                if not res or not res[0].time_s:
                    failures.append("slice: no print time in G-code")
            except Exception as e:
                failures.append(f"slice: {type(e).__name__}: {e}")
    if getattr(args, "update", False):
        EXPECTED.parent.mkdir(exist_ok=True)
        EXPECTED.write_text(json.dumps(recorded, indent=2), encoding="utf-8")
        print(f"\nrecorded expectations for {len(recorded)} models in {EXPECTED.relative_to(ROOT)}")
    if failures:
        print("\nSELFTEST FAILED\n  " + "\n  ".join(failures))
        return 1
    print(f"\nSELFTEST OK: {len(expected)} models build, export, check and render as recorded"
          + (", and the slicer works" if exe else ""))
    return 0


def add_model_args(sp):
    sp.add_argument("model")
    sp.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    sp.add_argument("--name", help="output name (default: model name + override values)")
    sp.add_argument("--out", help="output root folder (default: output/)")
    sp.add_argument("--printer", default=printers.DEFAULT, choices=list(printers.PRINTERS),
                    help=f"target printer: sets the bed and the slicer presets (default {printers.DEFAULT})")
    sp.add_argument("--bed", type=float, nargs=3, default=None, metavar=("X", "Y", "Z"),
                    help="override the printer's bed size in mm")


def add_slice_args(sp):
    sp.add_argument("--layer-height", type=float, default=0.2,
                    help="0.08/0.12/0.16/0.20/0.24/0.28 pick the matching Bambu preset")
    sp.add_argument("--infill", type=int, default=15, help="percent")
    sp.add_argument("--supports", action="store_true", help="let the slicer add supports")
    sp.add_argument("--filament", help=f"Bambu filament preset, e.g. 'Bambu PETG Basic' (default {printers.DEFAULT_FILAMENT})")
    sp.add_argument("--slicer", default="auto", choices=["auto", "bambu", "prusa"])
    sp.add_argument("--profile", help="PrusaSlicer .ini to load (prusa backend only)")


def main():
    ap = argparse.ArgumentParser(prog="cadkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build, check, export and render a model")
    add_model_args(b)
    b.add_argument("--fast", action="store_true", help="coarser mesh, skip STEP")
    b.add_argument("--no-render", action="store_true")
    b.add_argument("--section", action="append", metavar="AXIS=MM",
                   help="where to cut the section views, e.g. y=10 (default: centre)")
    b.add_argument("--slice", action="store_true", help="also slice with PrusaSlicer")
    add_slice_args(b)
    s = sub.add_parser("slice", help="slice a built model: print time, filament, supports")
    add_model_args(s)
    add_slice_args(s)
    s.add_argument("--section", action="append", metavar="AXIS=MM", help=argparse.SUPPRESS)
    m = sub.add_parser("measure", help="numbers about a built part; probe points and holes")
    add_model_args(m)
    m.add_argument("--probe", action="append", metavar="X,Y,Z", help="inside? thickness? (repeatable)")
    m.add_argument("--hole", action="append", metavar="A,B[,AXIS]",
                   help="measure a hole through (A, B) along AXIS (default z)")
    m.add_argument("--section", action="append", help=argparse.SUPPRESS)
    n = sub.add_parser("new", help="start a model from the template")
    n.add_argument("name")
    n.add_argument("description", nargs="?", default="")
    sub.add_parser("list", help="list models and whether they have been built")
    t = sub.add_parser("selftest", help="regression suite: build every recorded model and compare")
    t.add_argument("--update", action="store_true", help="re-record tests/expected.json from this run")
    args = ap.parse_args()
    commands = dict(build=cmd_build, slice=cmd_slice, measure=cmd_measure, new=cmd_new,
                    list=cmd_list, selftest=cmd_selftest)
    sys.exit(commands[args.cmd](args))


if __name__ == "__main__":
    main()
