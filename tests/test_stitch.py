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
from cadkit.stitch.design import split_corners
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
