"""cadkit command line.

  python -m cadkit build models/foo.py [--set name=value ...] [--fast] [--no-render]
  python -m cadkit new foo "one-line description"
  python -m cadkit list
  python -m cadkit selftest

`build` runs the model's build(p), checks the result is printable, and writes
output/<model>/<model>.stl (+ .step for B-rep models), preview.png and report.txt.
"""
import argparse
import importlib.util
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from . import mesh as meshmod
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
    rep = meshmod.check(tm, bed=tuple(args.bed))
    rep.stl_bytes = stl.stat().st_size
    if rep.stl_bytes > meshmod.TINKERCAD_MAX_BYTES:
        rep.warnings.append("STL is over Tinkercad's 25 MB import limit; rebuild with --fast")
    lines = rep.lines()
    if not args.no_render:
        png = out / f"{name}_preview.png"
        render_sheet(tm, png, title, lines)
        files.append(png)
    print(f"\n== {name} ({time.time() - t0:.1f}s export)")
    for line in lines:
        print("  " + line)
    for f in files:
        print(f"  -> {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}")
    return lines, rep


def cmd_build(args):
    path = Path(args.model).resolve()
    mod = load_model(path)
    defaults = getattr(mod, "PARAMS", {})
    p = parse_overrides(defaults, args.set)
    # variants get their own output folder, e.g. butterfly_paver_mold_square
    suffix = "_".join(pair.partition("=")[2] for pair in args.set)
    name = args.name or path.stem + (f"_{suffix}" if suffix else "")
    name = "".join(c if c.isalnum() or c in "-_." else "-" for c in name)
    out = Path(args.out or ROOT / "output") / name
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
    return 0 if all_ok else 1


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
    folder and confirm both come out as single watertight solids with previews."""
    from importlib.metadata import version
    print(f"python {sys.version.split()[0]}, " + ", ".join(
        f"{pkg} {version(pkg)}" for pkg in ("build123d", "manifold3d", "trimesh", "numpy", "pillow")))
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for model in ("_template.py", "butterfly_paver_mold.py"):
            ns = argparse.Namespace(model=str(ROOT / "models" / model), set=[], name=None,
                                    fast=True, no_render=False, bed=[256, 256, 256], out=tmp)
            try:
                if cmd_build(ns) != 0:
                    failures.append(f"{model}: not a single watertight solid")
                elif not list(Path(tmp).rglob("*_preview.png")):
                    failures.append(f"{model}: no preview rendered")
            except Exception as e:
                failures.append(f"{model}: {type(e).__name__}: {e}")
    if failures:
        print("\nSELFTEST FAILED\n  " + "\n  ".join(failures))
        return 1
    print("\nSELFTEST OK: both CAD kernels build, export, check and render")
    return 0


def main():
    ap = argparse.ArgumentParser(prog="cadkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build, check, export and render a model")
    b.add_argument("model")
    b.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    b.add_argument("--name", help="output name (default: model name + override values)")
    b.add_argument("--fast", action="store_true", help="coarser mesh, skip STEP")
    b.add_argument("--no-render", action="store_true")
    b.add_argument("--bed", type=float, nargs=3, default=[256, 256, 256], metavar=("X", "Y", "Z"))
    b.add_argument("--out", help="output root folder (default: output/)")
    n = sub.add_parser("new", help="start a model from the template")
    n.add_argument("name")
    n.add_argument("description", nargs="?", default="")
    sub.add_parser("list", help="list models and whether they have been built")
    sub.add_parser("selftest", help="check the install works end to end")
    args = ap.parse_args()
    commands = dict(build=cmd_build, new=cmd_new, list=cmd_list, selftest=cmd_selftest)
    sys.exit(commands[args.cmd](args))


if __name__ == "__main__":
    main()
