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


def bare_jump_pattern():
    """Two colours; the first in two pieces joined by a bare 30 mm jump, as Ink/Stitch
    leaves them (the PES writer cuts it, the other writers would not)."""
    pat = native.build_pattern(square_design())
    st, out, done = pat.stitches, [], False
    for x, y, c in st:
        if not done and (c & pe.COMMAND_MASK) == pe.TRIM:
            done = True                         # the cut between the pieces: make it bare
            continue
        out.append((x, y, c))
    pat.stitches = out
    pat2 = native.build_pattern(square_design())
    first = [s for s in pat2.stitches if (s[2] & pe.COMMAND_MASK) == pe.STITCH][:40]
    i = next(k for k, s in enumerate(out) if (s[2] & pe.COMMAND_MASK) == pe.COLOR_CHANGE)
    pat.stitches = (out[:i] + [(first[0][0] + 300, first[0][1], pe.JUMP)]
                    + [(x + 300, y, pe.STITCH) for x, y, _ in first] + out[i:])
    return pat


def test_prepare_cuts_jumps_and_drops_doubles():
    pat = pe.EmbPattern()
    pat.add_thread(pe.EmbThread("#ff0000"))
    for x, y in [(0, 0), (20.4, 0), (20.4, 0), (40, 0)]:             # a doubled point, floats
        pat.add_stitch_absolute(pe.STITCH, x, y)
    pat.add_stitch_absolute(pe.JUMP, 400, 0)                          # leaves sewn thread: cut
    for x in (400, 420):
        pat.add_stitch_absolute(pe.STITCH, x, 0)
    pat.add_command(pe.END)
    trims, dups = P.prepare(pat, "Mountain badge #2!")
    assert (trims, dups) == (1, 1)
    cmds = [c & pe.COMMAND_MASK for *_, c in pat.stitches]
    assert cmds.index(pe.TRIM) == cmds.index(pe.JUMP) - 1
    assert all(float(x).is_integer() and float(y).is_integer() for x, y, _ in pat.stitches)
    assert pat.extras["name"] == "Mountainbadge2"


def test_every_format_sews_what_the_design_says(tmp_path):
    """All eight shipped formats read back with the design's colours, size and path,
    every jump cut, no move written as a long stitch and no doubled penetration."""
    pat = bare_jump_pattern()
    assert any(not t for *_, t in P.plan_of(pat).jumps)
    formats = ("pes", "pec", "dst", "jef", "exp", "vp3", "xxx", "u01")
    written = P.write_all(pat, tmp_path / "two", formats)
    ref = P.plan_of(pat)
    assert P.verify_files(written, ref) == {f: [] for f in formats}


def test_verify_files_catches_a_bare_jump(tmp_path):
    pat = bare_jump_pattern()
    pe.write(pat, str(tmp_path / "raw.exp"))                         # no prepare: jump stays bare
    probs = P.verify_files({"exp": tmp_path / "raw.exp"}, P.plan_of(pat))["exp"]
    assert any("untrimmed" in p for p in probs), probs


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
@pytest.mark.parametrize("fmt", ["pes", "dst", "exp", "jef", "vp3", "xxx", "u01", "pec"])
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
    # written raw: write_all would tie the cuts this pattern leaves bare on purpose
    bad = tmp_path / "bad.pes"
    pe.write(bad_pattern(), str(bad), P.WRITE_SETTINGS["pes"])
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


def test_block_lettering_has_every_capital():
    from cadkit.stitch.lettering import block_text
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ.'-":
        g = block_text(ch, 10)
        assert g.is_valid and not g.is_empty and g.area > 3, ch
    word = block_text("TEXAS", 10, tracking=2.2)
    assert len(list(getattr(word, "geoms", [word]))) == 5       # letters never touch
    x0, y0, x1, y1 = block_text("OHIO", 12).bounds
    assert abs(y1 - y0 - 12) < 0.01


def test_hidden_jumps_are_buried_only_under_later_stitching():
    def pattern(cover):
        p = pe.EmbPattern()
        p.add_thread(pe.EmbThread("#c8102e"))
        for x in range(0, 31):                         # a run, then a 20 mm jump
            p.add_stitch_absolute(pe.STITCH, x * 10, 0)
        p.add_stitch_absolute(pe.JUMP, 500, 0)
        for x in range(50, 81):
            p.add_stitch_absolute(pe.STITCH, x * 10, 0)
        if cover:                                      # rows over the jump, sewn after it
            for r in range(-10, 11, 4):
                p.add_stitch_absolute(pe.STITCH, 0, r)
                p.add_stitch_absolute(pe.STITCH, 800, r)
        p.add_stitch_absolute(pe.END, 0, 0)
        return p
    covered, bare = pattern(True), pattern(False)
    assert P.sew_hidden_jumps(covered, 30) == 1
    assert not any((c & pe.COMMAND_MASK) == pe.JUMP for _, _, c in covered.stitches)
    assert P.sew_hidden_jumps(bare, 30) == 0


def abutting_fills(pull=None):
    """Two fills that just touch along x = 0, rows running across the join."""
    d = Design()
    d.fill(rect(20, 20, -10, 0), "#c8102e", angle=0, underlay=False, pull=pull)
    d.fill(rect(20, 20, 10, 0), "#1f5fbf", angle=0, underlay=False, pull=pull)
    return d


def test_fabric_profile_sets_compensation():
    from cadkit.stitch import fabrics as F
    d = Design()
    d.fill(rect(20, 20), "#c8102e")
    d.satin(np.array([[0, 0], [30, 0]]), 4.0, "navy")
    d.satin(np.array([[0, 5], [30, 5]]), 4.0, "navy", pull=0.05)          # its own: kept
    F.apply(d, F.profile("knit"))
    assert d.elements[0].params["pull"] == 0.35
    assert d.elements[1].params["pull"] == 0.35
    assert d.elements[2].params["pull"] == 0.05
    # fill compensation is in the geometry: rows sewn 0.35 mm longer at both ends
    pat = native.build_pattern(abutting_fills(pull=0.35))
    w = P.plan_of(pat).size[0]
    assert 40.5 < w < 41.0, w


def test_pull_model_moves_satin_edges_and_row_ends():
    from cadkit.stitch import fabrics as F
    prof = F.profile("knit")
    zig = np.array([[x * 0.4, 4.0 * (x % 2)] for x in range(40)])         # a 4 mm satin
    out = F.displace(zig, prof)
    assert abs(np.ptp(out[5:-5, 1]) - (4.0 - 2 * 0.35)) < 0.02
    rows = np.array([[0, 0], [3, 0], [6, 0], [9, 0], [9, 0.4], [6, 0.4], [3, 0.4], [0, 0.4]])
    out = F.displace(rows, prof)
    assert abs(out[3, 0] - (9 - 0.35)) < 1e-6 and abs(out[4, 0] - (9 - 0.35)) < 1e-6
    assert np.allclose(out[1:3], rows[1:3])                               # mid-row stays


def test_registration_flags_fills_that_part_once_sewn():
    from cadkit.stitch import fabrics as F
    prof = F.profile("fleece")              # 0.4 mm a side: a 0.35 mm line of fabric opens
    raw = abutting_fills(pull=0.0)
    gaps = cli.registration_gaps(P.plan_of(native.build_pattern(raw)), raw, prof)
    assert gaps and gaps[0][1] > 5, gaps
    comp = F.apply(abutting_fills(), prof)
    assert cli.registration_gaps(P.plan_of(native.build_pattern(comp)), comp, prof) == []


def test_stray_thread_across_another_colour_is_flagged():
    d = Design()
    d.fill(rect(10, 10, 0, 0), "#1f5fbf", angle=0)        # sewn first, in the middle
    d.fill(rect(10, 10, -15, 0), "#c8102e", angle=0)
    d.fill(rect(10, 10, 15, 0), "#c8102e", angle=0)
    plan = P.plan_of(native.build_pattern(d))
    assert C.stray_stitches(plan, d) == []
    # the red pieces joined by travel straight over the finished blue square
    red = [i for i, (b, _) in enumerate(plan.runs) if b == 1]
    a, b = plan.runs[red[0]][1], plan.runs[red[-1]][1]
    travel = np.linspace(a[-1], b[0], 12)[1:-1]
    plan.runs[red[0]] = (1, np.vstack([a, travel, b]))
    del plan.runs[red[-1]]
    bad = C.stray_stitches(plan, d)
    assert bad and bad[0][0] == 1 and bad[0][1] > 8, bad


def test_small_filled_lettering_is_flagged():
    d = Design()
    d.text("ABC", 4.0, "navy")
    assert C.small_lettering(d) == [("text ABC", 4.0)]
    assert C.small_lettering(d.scaled(2.0)) == []                         # 8 mm once scaled


@pytest.mark.skipif(engines.find_inkstitch() is None or cli.sim_binary(build=False) is None,
                    reason="needs Ink/Stitch and stitchsim")
@pytest.mark.parametrize("model", ["monogram_patch", "indiana_state", "gameday_banner_colorado_gold_black"])
def test_release_gate_passes_reference_designs(model, tmp_path):
    """The whole release gate on designs that span the techniques (lettering, a map
    border over a tucked fill, block letters on a plate with buried travel): every one
    of the eight formats ready, the design's checks and warnings clean."""
    args = SimpleNamespace(model=str(ROOT / "designs" / f"{model}.py"), set=[], name=None,
                           out=str(tmp_path), engine="inkstitch", hoop=None,
                           formats="pes,pec,dst,jef,exp,vp3,xxx,u01", no_render=True, compare=False)
    assert cli.cmd_build(args) == 0, args.build_data["parts"][model]["lines"]
    ready = __import__("json").loads((tmp_path / model / "readiness.json").read_text())
    assert ready["ready"], ready["blockers"]
    assert sorted(ready["formats"]) == sorted(args.formats.split(","))
