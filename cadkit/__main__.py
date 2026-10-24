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

from . import mesh as meshmod
from . import slicer
from .render import render_sheet

ROOT = Path(__file__).resolve().parent.parent


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


def resolve_output(args):
    """Output folder name for a model + overrides: variants get their own folder,
    e.g. butterfly_paver_mold_square."""
    path = Path(args.model).resolve()
    suffix = "_".join(pair.partition("=")[2] for pair in args.set)
    name = args.name or path.stem + (f"_{suffix}" if suffix else "")
    name = "".join(c if c.isalnum() or c in "-_." else "-" for c in name)
    return path, name, Path(args.out or ROOT / "output") / name


def export(part, name, out, args, title):
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
    rep = meshmod.check(tm, bed=tuple(args.bed), thickness_samples=2000 if args.fast else 4000)
    rep.stl_bytes = stl.stat().st_size
    if rep.stl_bytes > meshmod.TINKERCAD_MAX_BYTES:
        rep.warnings.append("STL is over Tinkercad's 25 MB import limit; rebuild with --fast")
    lines = rep.lines()
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

    report = [f"# {name}", getattr(mod, "DESCRIPTION", "").strip(), "",
              "params: " + ", ".join(f"{k}={v}" for k, v in p.items()), ""]
    all_ok = True
    for part_name, part in parts.items():
        fname = part_name if part_name == name else f"{name}-{part_name}"
        lines, rep = export(part, fname, out, args, fname)
        report += [f"## {fname}", *lines, ""]
        all_ok &= rep.ok
    (out / "report.txt").write_text("\n".join(report), encoding="utf-8")
    if getattr(args, "slice", False) and all_ok:
        slice_folder(out, name, args)
    return 0 if all_ok else 1


def slice_folder(out, name, args):
    """Slice every STL in an output folder; append the numbers to report.txt."""
    stls = sorted(out.glob(f"{name}*.stl"))
    if not stls:
        sys.exit(f"nothing built in {out}; run build first")
    if not slicer.find_slicer():
        print("  slice    skipped: no PrusaSlicer found (set CAD_SLICER to the console binary)")
        return None
    report = (out / "report.txt").read_text(encoding="utf-8").split("\n") if (out / "report.txt").exists() else []
    report = [l for l in report if not l.startswith("## slice")]  # keep it idempotent
    results = []
    for stl in stls:
        t0 = time.time()
        gcode = stl.with_suffix(".gcode")
        try:
            res = slicer.slice_stl(stl, gcode, profile=getattr(args, "profile", None),
                                   layer_height=getattr(args, "layer_height", 0.2),
                                   infill=getattr(args, "infill", 15),
                                   supports=getattr(args, "supports", False))
        except Exception as e:
            print(f"  slice    FAILED for {stl.name}: {e}")
            continue
        lines = res.lines()
        print(f"\n== slice {stl.stem} ({time.time() - t0:.1f}s)")
        for line in lines:
            print("  " + line)
        print(f"  -> {gcode.relative_to(ROOT) if gcode.is_relative_to(ROOT) else gcode}")
        report += [f"## slice {stl.stem}", *lines, ""]
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
    """Build the template (build123d) and the butterfly mold (manifold3d) into a temp
    folder and confirm both come out as single watertight solids with previews.
    Slices the template too if a slicer is installed."""
    from importlib.metadata import version
    print(f"python {sys.version.split()[0]}, " + ", ".join(
        f"{pkg} {version(pkg)}" for pkg in ("build123d", "manifold3d", "trimesh", "rtree", "numpy", "pillow")))
    exe = slicer.find_slicer()
    print(f"slicer {exe or 'not found (cad slice will be unavailable)'}")
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for model in ("_template.py", "butterfly_paver_mold.py"):
            ns = argparse.Namespace(model=str(ROOT / "models" / model), set=[], name=None,
                                    fast=True, no_render=False, bed=[256, 256, 256], out=tmp,
                                    section=None, slice=False)
            try:
                if cmd_build(ns) != 0:
                    failures.append(f"{model}: not a single watertight solid")
                elif not list(Path(tmp).rglob("*_preview.png")):
                    failures.append(f"{model}: no preview rendered")
            except Exception as e:
                failures.append(f"{model}: {type(e).__name__}: {e}")
        if exe:
            ns = argparse.Namespace(model=str(ROOT / "models" / "_template.py"), set=[], name=None,
                                    out=tmp, profile=None, layer_height=0.2, infill=15, supports=False)
            try:
                res = slice_folder(Path(tmp) / "_template", "_template", ns)
                if not res or not res[0].time_s:
                    failures.append("slice: no print time in G-code")
            except Exception as e:
                failures.append(f"slice: {type(e).__name__}: {e}")
    if failures:
        print("\nSELFTEST FAILED\n  " + "\n  ".join(failures))
        return 1
    print("\nSELFTEST OK: both CAD kernels build, export, check and render"
          + (", and the slicer works" if exe else ""))
    return 0


def add_model_args(sp):
    sp.add_argument("model")
    sp.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    sp.add_argument("--name", help="output name (default: model name + override values)")
    sp.add_argument("--out", help="output root folder (default: output/)")


def add_slice_args(sp):
    sp.add_argument("--profile", help="PrusaSlicer .ini (printer/filament/print) to load")
    sp.add_argument("--layer-height", type=float, default=0.2)
    sp.add_argument("--infill", type=int, default=15, help="percent")
    sp.add_argument("--supports", action="store_true", help="let the slicer add supports")


def main():
    ap = argparse.ArgumentParser(prog="cadkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build, check, export and render a model")
    add_model_args(b)
    b.add_argument("--fast", action="store_true", help="coarser mesh, skip STEP")
    b.add_argument("--no-render", action="store_true")
    b.add_argument("--bed", type=float, nargs=3, default=[256, 256, 256], metavar=("X", "Y", "Z"))
    b.add_argument("--section", action="append", metavar="AXIS=MM",
                   help="where to cut the section views, e.g. y=10 (default: centre)")
    b.add_argument("--slice", action="store_true", help="also slice with PrusaSlicer")
    add_slice_args(b)
    s = sub.add_parser("slice", help="slice a built model: print time, filament, supports")
    add_model_args(s)
    add_slice_args(s)
    s.add_argument("--bed", type=float, nargs=3, default=[256, 256, 256], metavar=("X", "Y", "Z"))
    s.add_argument("--section", action="append", metavar="AXIS=MM", help=argparse.SUPPRESS)
    n = sub.add_parser("new", help="start a model from the template")
    n.add_argument("name")
    n.add_argument("description", nargs="?", default="")
    sub.add_parser("list", help="list models and whether they have been built")
    sub.add_parser("selftest", help="check the install works end to end")
    args = ap.parse_args()
    commands = dict(build=cmd_build, slice=cmd_slice, new=cmd_new, list=cmd_list, selftest=cmd_selftest)
    sys.exit(commands[args.cmd](args))


if __name__ == "__main__":
    main()
