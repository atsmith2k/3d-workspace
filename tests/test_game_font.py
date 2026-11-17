"""Fonts in the game-asset silo: glyph construction, the TrueType writer read back by fontTools
and by FreeType, the checks, and (with cinder-probe) the engine parsing, baking and drawing it."""
import textwrap
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import ImageFont
from shapely.geometry import box

from cadkit.game import build as B
from cadkit.game import engine as E
from cadkit.game import font as F

PROBE = E.probe_state()[0]
needs_probe = pytest.mark.skipif(PROBE is None, reason="no cinder-probe (cad game probe build)")
DRAWN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;!?'\"-+=/\\()[]%#*<>_"


@pytest.fixture(scope="module")
def face():
    return F.FontFace(F.block_glyphs(2.0), family="Test Block")


@pytest.fixture(scope="module")
def ttf(face, tmp_path_factory):
    path = tmp_path_factory.mktemp("font") / "test_block.ttf"
    F.write_ttf(face, path, "test_block")
    return path


def test_every_drawn_glyph_is_a_valid_shape_on_the_line(face):
    assert set(DRAWN) <= set(face.glyphs)
    for ch, (shape, width) in face.glyphs.items():
        assert shape.is_valid and not shape.is_empty and width > 0, ch
        x0, y0, x1, y1 = shape.bounds
        assert -0.5 <= x0 and x1 <= width + 0.5 and -2.1 <= y0 and y1 <= F.H + 0.01, (ch, shape.bounds)
    caps = [face.glyphs[c][0].bounds for c in "HEB08"]
    assert all(abs(b[1]) < 0.01 and abs(b[3] - F.H) < 0.01 for b in caps)      # capitals and digits share a height
    assert face.glyphs[","][0].bounds[1] < -1 and face.glyphs["_"][0].bounds[3] < 0      # descenders go below


def test_fallbacks_map_lowercase_and_accents(face):
    cmap = face.cmap()
    assert cmap[ord("a")] == "A" and cmap[ord("z")] == "Z"
    assert cmap[ord("É")] == "E" and cmap[ord("é")] == "E" and cmap[ord("ñ")] == "N"
    assert ord("@") not in cmap and ord("$") not in cmap                       # honest: no glyph, so the hollow box
    strict = F.FontFace(face.glyphs, unicase=False, fold_accents=False).cmap()
    assert ord("a") not in strict and ord("É") not in strict


def test_ttf_reads_back_through_fonttools(face, ttf):
    from fontTools.ttLib import TTFont
    f = TTFont(str(ttf))
    assert f["head"].unitsPerEm == 1000 and f["OS/2"].sCapHeight == 700
    assert f["hhea"].ascent == 800 and f["hhea"].descent == -200
    cmap = f.getBestCmap()
    assert cmap[ord("A")] == cmap[ord("a")] == "uni0041" and cmap[ord("7")] == "uni0037" and cmap[32] == "space"
    adv, _ = f["hmtx"]["uni0048"]
    assert adv == round((face.glyphs["H"][1] + face.tracking) * 70)
    glyph = f["glyf"]["uni0041"]
    assert glyph.numberOfContours >= 2                                         # the A has a counter
    assert glyph.yMax == 700 and glyph.yMin == 0
    assert f["name"].getDebugName(1) == "Test Block"


def test_freetype_agrees_on_advances_and_renders_every_glyph(face, ttf):
    f = ImageFont.truetype(str(ttf), 1000)
    for text in ("HELLO 0123", "SCORE: 12,450", "A/B (C) [D]"):
        assert abs(f.getlength(text) - F.advance_units(face, text)) <= 2, text
    assert abs(f.getlength("hello") - f.getlength("HELLO")) < 1                 # lowercase is the capitals
    for ch in DRAWN:
        b = f.getbbox(ch)
        assert b[2] - b[0] > 0 and b[3] - b[1] > 0, ch
    assert f.getname() == ("Test Block", "Regular")


def test_thinnest_and_the_checks_that_use_it(face, ttf):
    assert F._thinnest(box(0, 0, 2, 10)) == pytest.approx(2.0, abs=0.05)
    assert F._thinnest(box(0, 0, 10, 10).difference(box(1, 1, 9, 9))) == pytest.approx(1.0, abs=0.05)
    ctx = SimpleNamespace(face=face, ttf=ttf, params={}, name="test_block", probe=None, shot=None)
    assert F.stroke_at(18, 1.5).run(ctx)["ok"]
    thin = SimpleNamespace(face=F.FontFace(F.block_glyphs(0.8)), ttf=ttf, params={}, name="t", probe=None, shot=None)
    assert not F.stroke_at(18, 1.5).run(thin)["ok"]
    assert F.covers("ABC019").run(ctx)["ok"] and not F.covers("AB@").run(ctx)["ok"]
    assert all(c.run(ctx)["ok"] for c in F.static_checks())


def test_distinct_catches_a_zero_that_is_an_o(face, tmp_path):
    ctx = SimpleNamespace(face=face, ttf=None, params={}, name="t", probe=None, shot=None)
    ctx.ttf = tmp_path / "ok.ttf"
    F.write_ttf(face, ctx.ttf, "ok")
    assert F.distinct("0", "O").run(ctx)["ok"] and F.distinct("8", "B").run(ctx)["ok"]
    same = dict(face.glyphs)
    same["0"] = same["O"]
    lazy = F.FontFace(same)
    ctx2 = SimpleNamespace(face=lazy, ttf=tmp_path / "lazy.ttf", params={}, name="t", probe=None, shot=None)
    F.write_ttf(lazy, ctx2.ttf, "lazy")
    r = F.distinct("0", "O").run(ctx2)
    assert not r["ok"] and "differ over 0%" in r["detail"]


FONT = '''
from cadkit.game.font import *
KIND = "font"
DESCRIPTION = "test block"
PARAMS = dict(stroke=2.0)
PRODUCT = dict(collection="font_test", licence="CC0-1.0")
def checks(p):
    return [covers("ABC0123"), stroke_at(18, 1.5), distinct("0", "O")]
def build(p):
    return FontFace(block_glyphs(p.stroke), family="Test Block")
'''
UI = '''
from cadkit.game.ui import *
KIND = "ui"
DESCRIPTION = "test title"
PARAMS = dict()
PRODUCT = dict(collection="COLLECTION", licence="CC0-1.0")
def build(p):
    ui = Ui()
    r = ui.root("centre", "menu")
    ui.label(r, "SCORE 0123", name="score", size=48)
    return UiSet(ui, font="test_block")
'''


@needs_probe
def test_cinder_parses_bakes_and_draws_the_font(tmp_path):
    src = tmp_path / "test_block.py"
    src.write_text(textwrap.dedent(FONT), encoding="utf-8")
    b = B.build_asset(src, out_root=tmp_path / "out", quiet=True)
    assert b["ready"], b["blockers"]
    eng = b["steps"]["engine"]["font"]
    assert eng["glyphs"] == 224 and eng["line_height"] == 24
    by_name = {r["name"]: r for r in b["steps"]["static"]["checks"]}
    assert by_name["engine"]["ok"] and by_name["engine draws it"]["ok"]
    out = tmp_path / "out" / "test_block"
    for f in ("test_block.ttf", "test_block.json", "test_block_preview.png", "test_block_in_engine.png"):
        assert (out / f).exists(), f
    assert "_ensure_ui_renderer" in b["use_snippet"] and "fonts/test_block.ttf" in b["use_snippet"]


@needs_probe
def test_pixel_match_tells_this_font_from_another(ttf, tmp_path):
    report, problem = E.probe_font(ttf, tmp_path / "right.png")
    assert report is not None, problem
    label = next(n for n in report["nodes"] if n["kind"] == "label" and n["h"] == 48)
    assert F.ink_match(tmp_path / "right.png", label, ttf, label["text"]) > 0.7
    roboto = E.cinder_checkout() / "cinder" / "ui" / "fonts" / "Roboto-Medium.ttf"
    other, _ = E.probe_font(roboto, tmp_path / "other.png")                    # the engine draws its own font
    label2 = next(n for n in other["nodes"] if n["kind"] == "label" and n["h"] == 48)
    assert F.ink_match(tmp_path / "other.png", label2, ttf, label2["text"]) < 0.6


@needs_probe
def test_an_interface_is_drawn_in_its_font_and_a_pack_needs_that_font(tmp_path, monkeypatch):
    from cadkit.game import pack as P
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "test_block.py").write_text(textwrap.dedent(FONT), encoding="utf-8")
    (assets / "test_title.py").write_text(textwrap.dedent(UI).replace("COLLECTION", "font_test"), encoding="utf-8")
    monkeypatch.setattr(P, "ASSETS", assets)
    monkeypatch.setattr(B, "OUT", tmp_path / "out")
    monkeypatch.setattr(P, "PACKS_OUT", tmp_path / "out" / "packs")
    with pytest.raises(SystemExit) as e:                                       # the font is not built yet
        B.build_asset(assets / "test_title.py", quiet=True)
    assert "is not built" in str(e.value)
    B.build_asset(assets / "test_block.py", quiet=True)
    ui = B.build_asset(assets / "test_title.py", quiet=True)
    assert ui["ready"], ui["blockers"]
    score = ui["stats"]["layout"]["score"]
    frame = tmp_path / "out" / "test_title" / "test_title_frame.png"
    assert F.ink_match(frame, score, tmp_path / "out" / "test_block" / "test_block.ttf", "SCORE 0123") > 0.7
    assert "fonts/test_block.ttf" in ui["use_snippet"]
    script = tmp_path / "font_test.py"
    script.write_text("\n".join(['TITLE = "Font Test"', 'DESCRIPTION = "font and title"', 'COLLECTION = "font_test"', ""]),
                      encoding="utf-8")
    m = P.build_pack(script, quiet=True)
    assert m["ready"] and m["totals"]["fonts"] == 1 and m["totals"]["interfaces"] == 1
    assert (tmp_path / "out" / "packs" / "font_test" / "fonts" / "test_block.ttf").exists()
    assert "## Fonts" in (tmp_path / "out" / "packs" / "font_test" / "AGENTS.md").read_text(encoding="utf-8")
    (assets / "test_block.py").write_text(textwrap.dedent(FONT).replace("font_test", "elsewhere"), encoding="utf-8")
    B.build_asset(assets / "test_block.py", quiet=True)
    with pytest.raises(SystemExit) as e:                                       # the title's font left the collection
        P.build_pack(script, quiet=True)
    assert "font that is not in this collection" in str(e.value)
