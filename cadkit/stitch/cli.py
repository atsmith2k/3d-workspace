"""`cad stitch ...`: build, inspect and list embroidery designs.

  cad stitch new <name> "<description>"      designs/<name>.py from the template
  cad stitch build designs/<name>.py [--set k=v] [--engine auto|inkstitch|native]
                   [--hoop 5x7] [--formats pes,dst,jef] [--compare]
  cad stitch inspect <file.pes|.dst|...> [--hoop 4x4]   stats + preview of any stitch file
  cad stitch list

build writes output/embroidery/<name>/: <name>.svg (Ink/Stitch-ready, open in Inkscape),
<name>.pes/.dst/.jef/.exp/.vp3/.xxx, <name>_preview.png, build.json, report.txt.
"""
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from .. import outputs
from . import checks as C
from . import engines, pattern as P
from .design import DEFAULT_HOOP, HOOPS
from .render import render_sheet
from .threads import thread_label
from .svg import to_svg

ROOT = Path(__file__).resolve().parent.parent.parent
DESIGNS = ROOT / "designs"
OUT = ROOT / "output" / "embroidery"


def plan_lines(plan, density, hoop_name, hoop_wh, engine):
    sw, sh = plan.size
    L = plan.stitch_lengths()
    g = density[0]
    long_n = int((L > 7.0).sum())
    short = float((L < 0.3).mean()) if len(L) else 0.0
    untrimmed = [np.linalg.norm(b - a) for _, a, b, t in plan.jumps if not t]
    upright = sw <= hoop_wh[0] and sh <= hoop_wh[1]
    turned = not upright and sh <= hoop_wh[0] and sw <= hoop_wh[1]    # machines rotate 90 deg
    fits = upright or turned
    lines = [
        f"engine   {engine}",
        f"size     {sw:.1f} x {sh:.1f} mm  (hoop {hoop_name} {hoop_wh[0]} x {hoop_wh[1]}: "
        f"{'fits' if upright else 'fits rotated 90 deg' if turned else 'DOES NOT FIT'})",
        f"stitches {plan.penetrations:,}   colours {len(plan.colors)}   trims {plan.trims}   "
        f"jumps {len(plan.jumps)} ({sum(1 for u in untrimmed if u > 3)} untrimmed over 3 mm)",
        f"thread   ~{plan.thread_length_m():.0f} m top thread; sew time ~{plan.sew_minutes():.0f} min at 650 spm",
        f"density  max {g.max():.2f} thread layers; {float((g > 3.0).sum()) * density[2] ** 2:.0f} mm2 over 3.0",
        f"lengths  {L.min() if len(L) else 0:.2f}..{L.max() if len(L) else 0:.2f} mm, "
        f"median {np.median(L) if len(L) else 0:.2f}; {long_n} over 7 mm; {short:.1%} under 0.3 mm",
    ]
    warns = []
    if not fits:
        warns.append(f"WARNING design {sw:.1f} x {sh:.1f} mm does not fit the {hoop_name} hoop")
    if g.max() > 3.5:
        iy, ix = np.unravel_index(np.argmax(g), g.shape)
        x, y = density[1][0] + (ix + 0.5) * density[2], density[1][1] + (iy + 0.5) * density[2]
        warns.append(f"WARNING dense: {g.max():.1f} thread layers near ({x:.0f}, {y:.0f}); "
                     "puckering / needle breaks. Lower the overlap or open the spacing")
    if long_n:
        warns.append(f"WARNING {long_n} stitches over 7 mm (snag risk): narrow the satin or use a fill")
    return lines, warns, fits


def _block_stitches(plan):
    out = [0] * len(plan.colors)
    for b, r in plan.runs:
        out[b] += len(r)
    return out


def cmd_build(args):
    from ..__main__ import load_model, parse_overrides
    path = Path(args.model).resolve()
    mod = load_model(path)
    p = parse_overrides(getattr(mod, "PARAMS", {}), args.set)
    suffix = "_".join(pair.partition("=")[2] for pair in args.set)
    name = args.name or path.stem + (f"_{suffix}" if suffix else "")
    name = "".join(c if c.isalnum() or c in "-_." else "-" for c in name)
    out = Path(args.out or OUT) / name
    out.mkdir(parents=True, exist_ok=True)
    ns = SimpleNamespace(**p)

    t0 = time.time()
    design = mod.design(ns)
    hoop_name = args.hoop or getattr(mod, "HOOP", None) or design.hoop or DEFAULT_HOOP
    if hoop_name not in HOOPS:
        sys.exit(f"unknown hoop '{hoop_name}'; known: {', '.join(HOOPS)}")
    design.hoop = hoop_name
    svg_path = out / f"{name}.svg"
    svg_path.write_text(to_svg(design, title=name), encoding="utf-8")
    print(f"designed {name}: {len(design.elements)} elements in {time.time() - t0:.1f}s -> {svg_path.name}")

    t1 = time.time()
    pat, engine, notes = engines.stitch(design, svg_path, args.engine)
    P.name_threads(pat, design.colors() if len(pat.threadlist) == len(design.colors()) else None)
    print(f"stitched with {engine} in {time.time() - t1:.1f}s")
    engine_plan = P.plan_of(pat)

    # write the machine files, then check and report on the file the user gets (the
    # writers add trims and split long stitches); formats without exact colours fall
    # back to the engine's plan
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    written = P.write_all(pat, out / name, formats)
    back = P.plan_of(P.read(written[formats[0]]))
    plan = back if formats[0] == "pes" else engine_plan
    density = C.density_grid(plan)
    rw, rh = back.size
    reread = (f"files    {', '.join(p.name for p in written.values())}; "
              f"{'checked' if plan is back else 're-read'}: {formats[0]} "
              f"({back.penetrations:,} stitches, {rw:.1f} x {rh:.1f} mm, {len(back.colors)} colours)")

    hoop_wh = HOOPS[hoop_name]
    lines, warns, fits = plan_lines(plan, density, hoop_name, hoop_wh, engine)
    if abs(rw - engine_plan.size[0]) > 1.0 or abs(rh - engine_plan.size[1]) > 1.0:
        warns.append(f"WARNING {formats[0]} re-read size {rw:.1f} x {rh:.1f} differs from the "
                     f"engine's {engine_plan.size[0]:.1f} x {engine_plan.size[1]:.1f}")
    thin = C.thin_features(design, 1.0)
    for nm, area, (x, y) in [t for t in thin if t[1] == 0.0 or t[1] > 3.0][:5]:
        warns.append(f"WARNING thin: {nm} has parts under 1 mm wide near ({x:.0f}, {y:.0f})"
                     + (f", {area:.1f} mm2" if area else ""))
    gaps = sorted(C.coverage_gaps(plan, design), key=lambda g: -g[1])
    worst = gaps[0] if gaps else ("", 0.0, (0, 0))
    lines.append(f"coverage largest bare patch {worst[1]:.1f} mm2" +
                 (f" ({worst[0]} near ({worst[2][0]:.0f}, {worst[2][1]:.0f}))" if worst[1] > 0.2 else ""))
    # pockets between elements are the coverage check's call (a design may allow them)
    for nm, area, (x, y) in [g for g in gaps if g[1] > 1.0 and not g[0].startswith("design (between")][:5]:
        warns.append(f"WARNING bare: {nm} leaves {area:.1f} mm2 of fabric showing near "
                     f"({x:.0f}, {y:.0f}): a break in a border or between fill sections")
    ctx = SimpleNamespace(plan=plan, design=design, params=ns, hoop=(hoop_name, hoop_wh),
                          density=density, name=name)
    spec = mod.checks(ns) if callable(getattr(mod, "checks", None)) else getattr(mod, "CHECKS", [])
    results = C.check_results(spec, ctx)
    check_lines = [C.format_check(r) for r in results]

    lines += [f"thread {i + 1}  {c}  {thread_label(c)}" for i, c in enumerate(plan.colors)]
    report = lines + [reread] + check_lines + [f"note     {n}" for n in notes] + warns
    ok = fits and all(r["ok"] for r in results)
    print()
    for line in report:
        print("  " + line)
    header = [f"# {name}", getattr(mod, "DESCRIPTION", "").strip(), "",
              "params: " + ", ".join(f"{k}={v}" for k, v in p.items()),
              f"hoop: {hoop_name} ({hoop_wh[0]} x {hoop_wh[1]} mm)", ""]
    if not args.no_render:
        png = out / f"{name}_preview.png"
        detail = getattr(args, "detail", None) or getattr(mod, "DETAIL", None)
        if isinstance(detail, str):
            detail = tuple(float(v) for v in detail.split(","))
        render_sheet(plan, density, png, f"{name}   {engine}", report, hoop_wh,
                     _block_stitches(plan), detail=detail)
        print(f"\n  preview  {png.relative_to(ROOT) if png.is_relative_to(ROOT) else png}")
    if args.compare:
        _compare(design, svg_path, engine, plan)
    build = dict(
        kind="embroidery", name=name,
        design=str(path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path),
        design_sha256=outputs.sha256(path), description=getattr(mod, "DESCRIPTION", "").strip(),
        params=p, hoop=hoop_name, engine=engine, ok=bool(ok), header_lines=header,
        parts={name: dict(lines=report, checks=results,
                          stitches=plan.penetrations, colors=plan.colors,
                          size=[round(v, 2) for v in plan.size], trims=plan.trims,
                          max_density=round(float(density[0].max()), 3),
                          files={k: v.name for k, v in written.items()}, svg=svg_path.name)},
        generated_at=outputs.now_iso(),
    )
    outputs.save_json(out / "build.json", build)
    outputs.write_report(out)
    args.build_data, args.plan = build, plan
    print(f"\n  {'OK' if ok else 'FAILED'}  {out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else out}")
    return 0 if ok else 1


def _compare(design, svg_path, used, plan):
    other = "native" if used.startswith("inkstitch") else "inkstitch"
    if other == "inkstitch" and not engines.find_inkstitch():
        print("  compare  Ink/Stitch not installed")
        return
    pat, eng, _ = engines.stitch(design, svg_path, other)
    o = P.plan_of(pat)
    print(f"\n  compare  {used:>18}: {plan.penetrations:6,} st, {plan.size[0]:.1f} x {plan.size[1]:.1f} mm, "
          f"{plan.trims} trims, {len(plan.jumps)} jumps")
    print(f"           {eng:>18}: {o.penetrations:6,} st, {o.size[0]:.1f} x {o.size[1]:.1f} mm, "
          f"{o.trims} trims, {len(o.jumps)} jumps")


def cmd_inspect(args):
    path = Path(args.file).resolve()
    plan = P.plan_of(P.read(path))
    density = C.density_grid(plan)
    hoop_name = args.hoop
    lines, warns, _ = plan_lines(plan, density, hoop_name, HOOPS[hoop_name], f"file {path.name}")
    for line in lines + warns:
        print("  " + line)
    for i, (c, n) in enumerate(zip(plan.colors, plan.names)):
        print(f"  colour   {i + 1}. {c} {n}")
    png = Path(args.out) if args.out else path.with_name(path.stem + "_inspect.png")
    render_sheet(plan, density, png, path.name, lines + warns, HOOPS[hoop_name], _block_stitches(plan))
    print(f"  preview  {png}")
    return 0


def cmd_new(args):
    dest = DESIGNS / f"{args.name}.py"
    if dest.exists():
        sys.exit(f"{dest} already exists")
    text = (DESIGNS / "_template.py").read_text(encoding="utf-8")
    dest.write_text(text.replace("DESCRIPTION_HERE", args.description), encoding="utf-8")
    print(f"created {dest.relative_to(ROOT)}")
    return 0


def cmd_list(args):
    from ..__main__ import load_model
    found = sorted(p for p in DESIGNS.glob("*.py") if not p.name.startswith("_"))
    if not found:
        print('no designs yet; start one with: stitch new <name> "<description>"')
    for path in found:
        desc = getattr(load_model(path), "DESCRIPTION", "")
        built = (OUT / path.stem / f"{path.stem}.pes").exists()
        print(f"{path.stem:28} {'built ' if built else '      '} {desc}")
    ink = engines.find_inkstitch()
    print(f"\nInk/Stitch: {engines.inkstitch_version() + ' at ' + str(ink) if ink else 'not found (native engine only)'}")
    return 0


SIM_DIR = ROOT / "tools" / "stitchsim"


def sim_binary(build=True):
    """Path to the stitchsim simulator, building it with cargo the first time."""
    import shutil
    import subprocess
    exe = SIM_DIR / "target" / "release" / ("stitchsim.exe" if sys.platform == "win32" else "stitchsim")
    if exe.exists() or not build:
        return exe if exe.exists() else None
    if shutil.which("cargo") is None:
        sys.exit("stitchsim is not built and cargo was not found: install Rust (rustup.rs), "
                 "then run `cargo build --release` in tools/stitchsim")
    print("building stitchsim (first run, ~1 min)...")
    subprocess.run(["cargo", "build", "--release"], cwd=SIM_DIR, check=True)
    return exe


def cmd_sim(args):
    """Open a stitch file, or a design's built PES, in the stitchsim simulator."""
    import subprocess
    path = Path(args.file)
    if path.suffix == ".py":                     # a design: its built PES
        path = OUT / path.stem / f"{path.stem}.pes"
        if not path.exists():
            sys.exit(f"{path} not built yet: run `cad stitch build {args.file}` first")
    if not path.exists():
        sys.exit(f"no such file: {path}")
    exe = sim_binary()
    cmd = [str(exe), str(path.resolve())]
    if args.screenshot:
        cmd += ["--screenshot", str(Path(args.screenshot).resolve()), "--at", str(args.at)]
        return subprocess.run(cmd).returncode
    if args.info:
        return subprocess.run([str(exe), "--info", str(path.resolve())]).returncode
    subprocess.Popen(cmd)
    print(f"stitchsim: {path.name}  (Space play, arrows step, PgUp/PgDn colours, F fit)")
    return 0


def cmd_publish(args):
    """Every size, images, thread chart, notes, zip and manifest for a design."""
    from ..__main__ import load_model, parse_overrides
    from . import publish as PUB
    exe = sim_binary()
    rc = 0
    for model in args.models:
        m = PUB.publish(model, cmd_build, load_model, parse_overrides, Path(args.out or OUT), exe,
                        refresh=not args.no_refresh)
        state = "SELLABLE" if m["sellable"] else "NOT sellable: " + "; ".join(m["reasons"])
        print(f"\n  {m['title']}  [{state}]")
        for s in m["sizes"]:
            print(f"    {s['label']:<4} {s['size_mm'][0]:.0f} x {s['size_mm'][1]:.0f} mm  {s['stitches']:,} st  "
                  f"{s['colors']} colours  ~{s['sew_minutes']:.0f} min  problems {s['problems']}")
        rc |= 0 if m["sellable"] else 1
    return rc


def cmd_bundle(args):
    """A bundle product from every published design in a collection."""
    from ..__main__ import load_model
    from . import publish as PUB
    members = []
    for path in sorted((ROOT / "designs").glob("*.py")):
        if path.name.startswith("_"):
            continue
        prod = getattr(load_model(path), "PRODUCT", {}) or {}
        if prod.get("collection") == args.collection:
            members.append(path.stem)
    if not members:
        sys.exit(f"no designs with PRODUCT collection '{args.collection}'")
    missing = [m for m in members if not (Path(args.out or OUT) / m / "manifest.json").exists()]
    if missing:
        sys.exit(f"publish these first: {', '.join(missing)}")
    bm = PUB.bundle(args.collection, args.title or args.collection.replace("-", " ").title(), Path(args.out or OUT),
                    members, args.price, args.commercial_price, args.blurb or "")
    print(f"  {bm['title']}: {len(members)} designs  [{'SELLABLE' if bm['sellable'] else 'NOT sellable'}]")
    print(f"  {Path(args.out or OUT) / '_bundles' / args.collection}")
    return 0 if bm["sellable"] else 1


def add_parser(sub):
    st = sub.add_parser("stitch", help="embroidery designs: build, inspect, sim, new, list")
    ss = st.add_subparsers(dest="stitch_cmd", required=True)
    b = ss.add_parser("build", help="design -> SVG + PES/DST/JEF..., checks, preview")
    b.add_argument("model")
    b.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    b.add_argument("--name")
    b.add_argument("--out", help="output root (default output/embroidery/)")
    b.add_argument("--engine", default="auto", choices=["auto", "inkstitch", "native"])
    b.add_argument("--hoop", help=f"sewing field: {', '.join(HOOPS)} (default: the design's HOOP)")
    b.add_argument("--formats", default=",".join(P.FORMATS), help="comma-separated, first is re-read to verify")
    b.add_argument("--no-render", action="store_true")
    b.add_argument("--compare", action="store_true", help="also stitch with the other engine and compare")
    b.add_argument("--detail", metavar="X,Y", help="centre of the preview detail tile, mm (default: densest spot)")
    i = ss.add_parser("inspect", help="stats and preview of any stitch file (PES, DST, JEF, EXP, VP3...)")
    i.add_argument("file")
    i.add_argument("--hoop", default=DEFAULT_HOOP, choices=list(HOOPS))
    i.add_argument("--out")
    n = ss.add_parser("new", help="start a design from designs/_template.py")
    n.add_argument("name")
    n.add_argument("description", nargs="?", default="")
    ss.add_parser("list", help="designs and whether they are built; Ink/Stitch status")
    pb = ss.add_parser("publish", help="every size, product images, thread chart, notes, zip, manifest")
    pb.add_argument("models", nargs="+")
    pb.add_argument("--out")
    pb.add_argument("--no-refresh", action="store_true", help="reuse existing size builds")
    bd = ss.add_parser("bundle", help="a bundle product from a collection's published designs")
    bd.add_argument("collection")
    bd.add_argument("--title")
    bd.add_argument("--blurb")
    bd.add_argument("--price", type=float, default=19.99)
    bd.add_argument("--commercial-price", type=float, default=59.99)
    bd.add_argument("--out")
    m = ss.add_parser("sim", help="watch a stitch file (or a design's PES) sew in the stitchsim viewer")
    m.add_argument("file", help="PES/PEC/DST/EXP/JEF file, or designs/<name>.py")
    m.add_argument("--info", action="store_true", help="print the simulator's stats instead of opening it")
    m.add_argument("--screenshot", metavar="PNG", help="render one frame to a PNG and exit")
    m.add_argument("--at", default="1.0", help="with --screenshot: share sewn (0..1) or stitch count")
    return st


def run(args):
    return dict(build=cmd_build, inspect=cmd_inspect, new=cmd_new, list=cmd_list,
                sim=cmd_sim, publish=cmd_publish, bundle=cmd_bundle)[args.stitch_cmd](args)
