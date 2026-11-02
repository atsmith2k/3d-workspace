"""Embroidery harness: shapes, the native stitch engine, the SVG writer, the stitch-plan
reader and a full `cad stitch build` of the example designs (native engine; the
Ink/Stitch engine too when it is installed)."""
import xml.etree.ElementTree as ET
from types import SimpleNamespace

import numpy as np
import pyembroidery as pe
import pytest

from cadkit.stitch import Design, circle, heart, knockout, rect, text_shape
from cadkit.stitch import checks as C
from cadkit.stitch import cli, engines, native, pattern as P
from cadkit.stitch.design import _resample, ring_rails, split_corners
from cadkit.stitch.svg import to_svg

from conftest import ROOT


def square_design():
    d = Design()
    d.fill(rect(30, 20), "#c8102e", angle=0)
    d.run(np.array([[-15, -15], [15, -15]]), "navy", bean=1)
    return d


def test_native_fill_stays_inside_and_short():
    d = Design()
    d.fill(rect(30, 20), "#c8102e", angle=30)
    plan = P.plan_of(native.build_pattern(d), recenter=False)
    pts = plan.points
    assert pts[:, 0].min() >= -15.3 and pts[:, 0].max() <= 15.3
    assert pts[:, 1].min() >= -10.3 and pts[:, 1].max() <= 10.3
    assert plan.stitch_lengths().max() <= 3.0 + 1e-6
    assert abs(plan.size[0] - 30) < 0.6 and abs(plan.size[1] - 20) < 0.6
    g = C.density_grid(plan)[0]
    assert 0.6 < np.median(g[g > 0.3]) < 1.6        # one fill layer + underlay


def test_fill_with_hole_leaves_hole_empty():
    d = Design()
    d.fill(circle(0, 0, 20) - circle(0, 0, 8), "#2e8b3a")
    plan = P.plan_of(native.build_pattern(d), recenter=False)
    _, a, b = plan.segments()
    mid = (a + b) / 2
    assert (np.linalg.norm(mid, axis=1) < 7.0).sum() == 0


def test_colour_changes_and_trims_round_trip(tmp_path):
    pat = native.build_pattern(square_design())
    plan = P.plan_of(pat)
    assert plan.colors == ["#c8102e", "#1f2a5a"]
    out = P.write_all(pat, tmp_path / "sq", ("pes", "dst", "jef"))
    back = P.plan_of(P.read(out["pes"]))
    assert len(back.colors) == 2
    assert abs(back.size[0] - plan.size[0]) < 0.3
    assert back.colors[0] == "#c8102e"               # PES v6 keeps the exact RGB


def test_plan_reader_counts_jumps_and_trims():
    pat = pe.EmbPattern()
    pat.add_thread(pe.EmbThread("#ff0000"))
    for x in (0, 20, 40):
        pat.add_stitch_absolute(pe.STITCH, x, 0)
    pat.add_stitch_absolute(pe.TRIM, 40, 0)
    pat.add_stitch_absolute(pe.JUMP, 400, 0)
    for x in (400, 420):
        pat.add_stitch_absolute(pe.STITCH, x, 0)
    pat.add_stitch_absolute(pe.JUMP, 600, 0)
    pat.add_stitch_absolute(pe.STITCH, 600, 0)
    pat.add_command(pe.END)
    plan = P.plan_of(pat, recenter=False)
    assert plan.penetrations == 6 and plan.trims == 1
    assert [t for *_, t in plan.jumps] == [True, False]
    assert len(plan.runs) == 3


def test_satin_border_split_at_sharp_corners():
    ring = np.asarray(heart(60).exterior.coords)
    assert len(split_corners(ring, 50)) == 2          # notch and tip
    assert len(split_corners(np.asarray(circle(0, 0, 20).exterior.coords), 50)) == 1


def test_knockout_leaves_no_slivers():
    disc = circle(0, 0, 40)
    hill = rect(100, 40, 0, -20) & disc
    sky = knockout(disc, hill)
    d = Design()
    d.fill(sky, "sky")
    assert C.thin_features(d, 1.0) == []
    assert sky.intersection(hill).area > 0            # it still tucks under the hill


def test_text_shape_keeps_counters():
    o = text_shape("O", 20)
    assert len(o.interiors if o.geom_type == "Polygon" else o.geoms[0].interiors) == 1


def test_svg_has_inkstitch_params():
    d = square_design()
    d.satin(np.array([[-10, 12], [10, 12]]), 3.0, "black")
    root = ET.fromstring(to_svg(d).encode())
    ns = "{http://inkstitch.org/namespace}"
    paths = root.findall(".//{http://www.w3.org/2000/svg}path")
    assert [p.get(ns + "fill_method") for p in paths][0] == "auto_fill"
    assert paths[1].get(ns + "stroke_method") == "running_stitch"
    assert paths[1].get(ns + "bean_stitch_repeats") == "1"
    assert paths[2].get(ns + "satin_column") == "True"
    assert paths[2].get("d").count("M") == 2          # two rails


def _build(model, tmp_path, engine):
    args = SimpleNamespace(model=str(ROOT / "designs" / f"{model}.py"), set=[], name=None,
                           out=str(tmp_path), engine=engine, hoop=None,
                           formats="pes,dst", no_render=True, compare=False)
    return cli.cmd_build(args), args


@pytest.mark.parametrize("model", ["mountain_badge", "monogram_patch"])
def test_example_designs_build_native(model, tmp_path):
    rc, args = _build(model, tmp_path, "native")
    assert rc == 0, args.build_data["parts"][model]["lines"]
    assert (tmp_path / model / f"{model}.pes").exists()
    assert (tmp_path / model / f"{model}.svg").exists()


@pytest.mark.skipif(engines.find_inkstitch() is None, reason="Ink/Stitch not installed")
def test_inkstitch_engine(tmp_path):
    rc, args = _build("monogram_patch", tmp_path, "inkstitch")
    assert rc == 0, args.build_data["parts"]["monogram_patch"]["lines"]
    assert args.build_data["engine"].startswith("inkstitch")


def test_outline_is_one_continuous_ring():
    d = Design()
    d.outline(heart(60), "black", width=2.5)
    assert len(d.elements) == 1                        # not split at the tip and notch
    left, right = d.elements[0].geom
    assert np.allclose(left[0], left[-1]) and len(left) == len(right)
    w = np.linalg.norm(left - right, axis=1)
    assert w.min() > 1.0 and w.max() < 2.5 * 1.7       # mitres and fans stay sane
    plan = P.plan_of(native.build_pattern(d), recenter=False)
    assert plan.trims == 1 and len(plan.runs) == 1     # one start, one tie-off


def test_coverage_catches_broken_border_and_pulled_fill():
    shape = heart(60)
    def gaps(d):
        return max(a for _, a, _ in C.coverage_gaps(P.plan_of(native.build_pattern(d)), d))
    ok = Design()
    ok.fill(C.S.tuck(shape, 2.5), "#c8102e")
    ok.outline(shape, "black", width=2.5)
    assert gaps(ok) < 1.0
    plan = P.plan_of(native.build_pattern(ok))         # a 3 mm break in the border
    tip = np.array([0.0, -26.5]) + (np.array(plan.bounds[:2]) + plan.bounds[2:]) / 2
    runs = []
    for b, r in plan.runs:                             # block 1 is the border
        keep = np.linalg.norm(r - tip, axis=1) > 1.5 if b == 1 else np.ones(len(r), bool)
        idx = np.split(np.arange(len(r)), np.nonzero(np.diff(keep))[0] + 1)
        runs += [(b, r[i]) for i in idx if keep[i[0]] and len(i) > 1]
    plan.runs = runs
    assert max(a for _, a, _ in C.coverage_gaps(plan, ok)) > 1.0
    pulled = Design()                                  # fill stops short of the border
    pulled.fill(shape.buffer(-3), "#c8102e")
    pulled.outline(shape, "black", width=2.5)
    assert gaps(pulled) > 1.0


def test_native_travel_makes_no_tiny_stitches():
    d = Design()
    d.fill(circle(0, 0, 25) - rect(30, 4), "#2e8b3a")  # two islands of rows, edge travel
    L = P.plan_of(native.build_pattern(d)).stitch_lengths()
    assert (L < 0.3).mean() < 0.03


def test_ring_satin_svg_is_two_open_halves():
    d = Design()
    d.outline(heart(60), "black", width=2.5)
    root = ET.fromstring(to_svg(d).encode())
    paths = root.findall(".//{http://www.w3.org/2000/svg}path")
    assert [p.get("id") for p in paths] == ["el001a", "el001b"]
    assert all("Z" not in p.get("d") for p in paths)   # Ink/Stitch mis-sews closed rails


@pytest.mark.skipif(engines.find_inkstitch() is None, reason="Ink/Stitch not installed")
def test_inkstitch_sews_ring_border_cleanly(tmp_path):
    d = Design()
    d.hoop = "4x4"
    d.outline(heart(60), "black", width=2.5)
    svg = tmp_path / "ring.svg"
    svg.write_text(to_svg(d), encoding="utf-8")
    plan = P.plan_of(engines.run_inkstitch(svg)[0])
    assert plan.stitch_lengths().max() < 7.0
    assert C.coverage_gaps(plan, d)[0][1] < 1.0


@pytest.mark.skipif(cli.sim_binary(build=False) is None, reason="stitchsim not built")
@pytest.mark.parametrize("fmt", ["pes", "dst", "exp", "jef"])
def test_stitchsim_reads_what_we_write(tmp_path, fmt):
    """The Rust simulator decodes every format we write the same way pyembroidery does."""
    import subprocess
    out = P.write_all(native.build_pattern(square_design()), tmp_path / "sq", (fmt,))[fmt]
    info = subprocess.run([str(cli.sim_binary(build=False)), "--info", str(out)],
                          capture_output=True, text=True, check=True).stdout
    got = dict(line.split(None, 1) for line in info.splitlines() if line.strip())
    plan = P.plan_of(P.read(out))
    assert int(got["stitches"]) == plan.penetrations
    assert int(got["colours"].split()[0]) == len(plan.colors)
    w, h = (float(v) for v in got["size"].replace(" mm", "").split(" x "))
    assert abs(w - plan.size[0]) < 0.11 and abs(h - plan.size[1]) < 0.11
    if fmt == "pes":
        assert "#c8102e" in info                      # exact RGB from the PES v6 header


def bad_pattern():
    """A stitch file with one of every problem stitchsim flags (0.1 mm units, Y down)."""
    pat = pe.EmbPattern()
    pat.add_thread(pe.EmbThread("#c8102e"))
    pat.add_thread(pe.EmbThread("#1f5fbf"))
    s = lambda x, y: pat.add_stitch_absolute(pe.STITCH, x, y)
    for x, y in [(0, 0), (4, 0), (0, 0), (4, 0)]:                    # tie-in
        s(x, y)
    for i in range(30):                                               # long satin: 10 mm, then 14 mm
        s(i * 4, 0 if i % 2 else (100 if i < 15 else 140))
    for layer in range(8):                                            # 8 stacked fills: far too dense
        for row in range(50):
            y = 300 + row * 4
            for x in (range(0, 200, 25) if row % 2 == 0 else range(200, 0, -25)):
                s(x, y)
    for i in range(4):                                                # tiny stitches in a row, mid-run
        s(200 + (i % 2) * 2, 520)
    s(240, 520)
    for i in range(10):                                               # needle pile-up on one point
        s(300, 520)
        s(300 + (30 if i % 2 else -30), 540)
    s(300, 520)
    pat.add_stitch_absolute(pe.JUMP, 700, 520)                        # untrimmed 40 mm jump
    for x in range(700, 900, 25):
        s(x, 520)
    pat.add_stitch_absolute(pe.TRIM, 900, 520)                        # ends with no tie-off
    pat.add_command(pe.COLOR_CHANGE)
    pat.add_stitch_absolute(pe.JUMP, 0, 900)
    for x in range(0, 300, 25):                                       # starts with no tie-in
        s(x, 900)
    pat.add_command(pe.END)
    return pat


@pytest.mark.skipif(cli.sim_binary(build=False) is None, reason="stitchsim not built")
def test_stitchsim_flags_problems(tmp_path):
    import subprocess
    exe = str(cli.sim_binary(build=False))
    bad = P.write_all(bad_pattern(), tmp_path / "bad", ("pes",))["pes"]
    info = subprocess.run([exe, "--info", str(bad)], capture_output=True, text=True, check=True).stdout
    for kind in ("stitch too long", "far too dense", "tiny stitches", "needle pile-up", "no tie-off", "no tie-in"):
        assert kind in info, (kind, info)
    # PES turns every jump into a trim; EXP keeps the jump untrimmed
    exp = P.write_all(bad_pattern(), tmp_path / "bad", ("exp",))["exp"]
    info = subprocess.run([exe, "--info", str(exp)], capture_output=True, text=True, check=True).stdout
    assert "untrimmed jump" in info, info
    good = P.write_all(native.build_pattern(square_design()), tmp_path / "ok", ("pes",))["pes"]
    clean = subprocess.run([exe, "--info", str(good)], capture_output=True, text=True, check=True).stdout
    assert "problems    0" in clean, clean


def test_scaled_design_restitches_at_size():
    d = Design()
    d.fill(rect(30, 20), "#c8102e", angle=0)
    d.satin(np.array([[-10, 14], [10, 14]]), 2.0, "black")
    big = d.scaled(1.5, 5.0, 0.0)
    p0 = P.plan_of(native.build_pattern(d), recenter=False)
    p1 = P.plan_of(native.build_pattern(big), recenter=False)
    assert abs(p1.size[0] / p0.size[0] - 1.5) < 0.05           # bigger, not a resized file:
    assert p1.penetrations > 1.8 * p0.penetrations              # rows keep their 0.4 mm spacing
    assert abs(big.elements[1].params["width"] - 3.0) < 1e-6
    assert abs(np.mean(p1.points[:, 0]) - np.mean(p0.points[:, 0]) * 1.5 - 5.0) < 1.0


def test_hoop_check_accepts_a_rotated_design():
    ctx = SimpleNamespace(plan=SimpleNamespace(size=(160.0, 86.0)), hoop=("5x7", (130, 180)))
    ok, detail = C.hoop().fn(ctx)
    assert ok and "rotated" in detail
    ctx.plan.size = (190.0, 86.0)
    assert not C.hoop().fn(ctx)[0]


def test_motifs_are_valid_shapes():
    from cadkit.stitch import motifs as M
    shapes = [M.maple_leaf(60), M.oak_leaf(40, 4), M.leaf(20, 8, 0.3), *M.acorn(20)[:2],
              *[s for _, s in M.pumpkin(60, 44, 2)[0]], *[s for _, s in M.maple_sectors(60)],
              *M.wheat(50, 7, 5)[1], *M.petal_ring(12, 8, 12, 5, jitter=4)]
    for s in shapes:
        assert s.is_valid and not s.is_empty and s.area > 1
    assert abs(sum(s.area for _, s in M.maple_sectors(60)) - M.maple_leaf(60).area) < 1.0
