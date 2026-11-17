"""UI documents and sprites in the game-asset silo: the document writer against text the
engine itself wrote, the checks, atlas packing, and (with the engine and cinder-probe) the
round trip through Cinder's own Ui.from_text and Ui.to_text."""
import json
import textwrap
from types import SimpleNamespace

import numpy as np
import pytest

from cadkit.game import build as B
from cadkit.game import engine as E
from cadkit.game import sprite as SP
from cadkit.game import ui as U

ENGINE = E.find()
PROBE = E.probe_state()[0]
needs_engine = pytest.mark.skipif(ENGINE is None, reason="no Cinder package (set CAD_CINDER)")
needs_probe = pytest.mark.skipif(PROBE is None, reason="no cinder-probe (cad game probe build)")

# Written by Cinder 0.1.1 (Ui.to_text, commit 5921045) for: a centred root "sample", two labels at
# 48 and 24 px, and a button at 18 px, all with the default theme.
ENGINE_TEXT = """cinder-scene 1
entity 0
  panel parent=#-1 name="sample" text="" visible=true enabled=true row=false align=0 padding=10.0 gap=6.0 min_size=[0.0,0.0] anchor=4 offset=[0.0,0.0] background=[18.0,20.0,28.0,224.0] text_color=[236.0,236.0,240.0,255.0] font_size=18 checked=false range=[0.0,0.0,1.0,0.05]
entity 1
  label parent=#0 name="" text="THE QUICK BROWN FOX 0123456789" visible=true enabled=true row=false align=0 padding=0.0 gap=6.0 min_size=[0.0,0.0] anchor=0 offset=[0.0,0.0] background=[0.0,0.0,0.0,0.0] text_color=[236.0,236.0,240.0,255.0] font_size=48 checked=false range=[0.0,0.0,1.0,0.05]
entity 2
  label parent=#0 name="" text="THE QUICK BROWN FOX 0123456789" visible=true enabled=true row=false align=0 padding=0.0 gap=6.0 min_size=[0.0,0.0] anchor=0 offset=[0.0,0.0] background=[0.0,0.0,0.0,0.0] text_color=[236.0,236.0,240.0,255.0] font_size=24 checked=false range=[0.0,0.0,1.0,0.05]
entity 3
  button parent=#0 name="" text="PLAY 0123456789" visible=true enabled=true row=false align=0 padding=10.0 gap=6.0 min_size=[0.0,0.0] anchor=0 offset=[0.0,0.0] background=[52.0,58.0,76.0,255.0] text_color=[236.0,236.0,240.0,255.0] font_size=18 checked=false range=[0.0,0.0,1.0,0.05]
"""


def sample():
    ui = U.Ui()
    root = ui.root("centre", "sample")
    ui.label(root, "THE QUICK BROWN FOX 0123456789", size=48)
    ui.label(root, "THE QUICK BROWN FOX 0123456789", size=24)
    ui.button(root, "PLAY 0123456789")
    return ui


def test_the_same_tree_built_here_writes_the_text_the_engine_wrote():
    assert sample().to_text() == ENGINE_TEXT                      # byte for byte, defaults included
    ok, why = U.same(U.Ui.from_text(ENGINE_TEXT), sample())
    assert ok, why


def test_constructors_mirror_the_engine_and_overrides_win():
    ui = U.Ui(U.Theme(padding=12.0, gap=8.0, control=(1, 2, 3, 255)))
    root = ui.root("top_right", "r", offset=(4, 5), padding=20.0)
    row = ui.panel(root, row=True)
    t = ui.toggle(row, "On", True, name="on")
    s = ui.slider(row, "Vol", 5, 0, 10, name="vol")
    assert ui[root]["anchor"] == 2 and ui[root]["padding"] == 20.0 and ui[root]["offset"] == [4.0, 5.0]
    assert ui[row]["row"] and ui[row]["align"] == 1 and ui[row]["padding"] == 0.0     # a row centres its children
    assert ui[t]["checked"] and ui[t]["background"] == [1.0, 2.0, 3.0, 255.0] and ui[t]["gap"] == 8.0
    assert ui[s]["range"] == [5.0, 0.0, 10.0, 0.5]                                    # step is a twentieth
    assert ui.find("vol") == s


def test_document_order_is_depth_first_and_parents_are_renumbered():
    ui = U.Ui()
    a = ui.root("top_left", "a")
    b = ui.root("bottom", "b")
    ui.label(a, "under a", name="a1")                             # created after b, written before it
    ui.label(b, "under b", name="b1")
    back = U.Ui.from_text(ui.to_text())
    assert [n["name"] for n in back.nodes] == ["a", "a1", "b", "b1"]
    assert [n["parent"] for n in back.nodes] == [-1, 0, -1, 2]
    with pytest.raises(ValueError):
        U.Ui.from_text("cinder-world 1\n")
    with pytest.raises(ValueError):
        U.Ui.from_text("cinder-scene 1\nentity 0\n  wheel parent=#-1\n")


def test_theme_as_mojo():
    lines = U.Theme(accent=(1, 2, 3, 4), font_size=20).mojo("ui.theme")
    assert "ui.theme.font_size = 20" in lines and "ui.theme.accent = UiColor.rgba(1, 2, 3, 4)" in lines
    assert len(lines) == 11


def _static(ui, name="thing"):
    ctx = SimpleNamespace(ui=ui, name=name, params={}, probe=None, layout=None, rect=lambda n: None)
    return {r["name"]: r for r in (c.run(ctx) for c in U.static_checks())}


def test_ui_checks_catch_what_breaks_in_the_engine():
    good = U.Ui()
    r = good.root("centre", "menu")
    good.button(r, "Play", name="play")
    assert all(x["ok"] for x in _static(good).values())
    for text, why in (('say "hi"', "quote"), ("price: €5", "Latin-1"), ("two\nlines", "newline")):
        ui = U.Ui()
        ui.label(ui.root("centre", "m"), text)
        res = _static(ui)["tree"]
        assert not res["ok"] and why in res["detail"], res
    unnamed = U.Ui()
    unnamed.button(unnamed.root("centre", "m"), "Play")
    assert "without a name" in _static(unnamed)["tree"]["detail"]
    twice = U.Ui()
    r = twice.root("centre", "m")
    twice.button(r, "A", name="x")
    twice.button(r, "B", name="x")
    assert "used twice" in _static(twice)["tree"]["detail"]


# ---------------------------------------------------------------- sprites

def test_canvas_gives_straight_alpha_and_clean_edges():
    c = SP.Canvas(32)
    c.circle((16, 16), 10, fill=(255, 0, 0))
    img = c.image()
    assert img.shape == (32, 32, 4) and img[16, 16].tolist() == [1.0, 0.0, 0.0, 1.0] and img[0, 0, 3] == 0
    edge = img[(img[..., 3] > 0.05) & (img[..., 3] < 0.95)]
    assert len(edge) > 20 and np.allclose(edge[:, 0], 1.0, atol=0.02)      # partly covered texels keep the full colour


def _sheet(n=5, size=24, **kw):
    out = {}
    for i in range(n):
        c = SP.Canvas(size)
        c.rect((2, 2, size - 2, size - 2), radius=3, fill=(40 * i + 40, 120, 200))
        out[f"f{i}"] = c.image()
    return SP.SpriteSheet(out, **kw)


def test_pack_is_a_power_of_two_square_with_padding():
    sheet = _sheet(5)
    atlas, rects = SP.pack(sheet)
    n = atlas.shape[0]
    assert atlas.shape == (n, n, 4) and n & (n - 1) == 0 and n == 128      # five 24 px frames need three rows
    assert list(rects) == list(sheet.frames)
    for k, r in rects.items():
        assert np.array_equal(atlas[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]], sheet.frames[k])
    occupied = np.zeros((n, n), int)
    for r in rects.values():
        occupied[r["y"] - 1:r["y"] + r["h"] + 1, r["x"] - 1:r["x"] + r["w"] + 1] += 1
    assert occupied.max() == 1                                    # each frame keeps a 1 px margin: 2 px between any two


def test_quads_map_each_frame_and_ask_for_an_unlit_mask():
    sheet = _sheet(3)
    atlas, rects = SP.pack(sheet)
    model = SP.quads(sheet, atlas, rects)
    mesh, mat = model.parts[0]
    assert model.triangles == 6 and mat.alpha == "mask" and mat.color[:3] == (0.0, 0.0, 0.0) and mat.emissive == (1.0, 1.0, 1.0)
    r = rects["f0"]
    n = atlas.shape[0]
    assert np.allclose(sorted(set(mesh.uv[:4, 0])), [r["x"] / n, (r["x"] + r["w"]) / n])
    assert mesh.uv[0, 1] > mesh.uv[3, 1]                          # the quad's bottom is the frame's bottom row


def _sprite_ctx(sheet, tmp):
    from PIL import Image
    from cadkit.game.texture import to_u8
    atlas, rects = SP.pack(sheet)
    png, js = tmp / "s.png", tmp / "s.json"
    Image.fromarray(to_u8(atlas)).save(png)
    js.write_text(json.dumps(dict(frames=rects, size=[atlas.shape[1], atlas.shape[0]])), encoding="utf-8")
    return SimpleNamespace(sheet=sheet, atlas=atlas, rects=rects, params={}, name="s", png=png, json=js)


def test_sprite_checks(tmp_path):
    def failing(sheet):
        ctx = _sprite_ctx(sheet, tmp_path)
        return {r["name"] for r in (c.run(ctx) for c in SP.static_checks()) if not r["ok"]}

    assert failing(_sheet(4)) == set()
    assert failing(_sheet(4, padding=1)) == {"atlas"}             # frames would bleed into each other
    empty = _sheet(2)
    empty.frames["blank"] = np.zeros((24, 24, 4))
    assert failing(empty) == {"frames valid"}
    assert failing(_sheet(2, animations=dict(run=dict(frames=["f0", "nope"], fps=10)))) == {"frames valid"}
    ctx = _sprite_ctx(_sheet(3, animations=dict(run=dict(frames=["f0", "f1", "f2"], fps=10)),
                             slices=dict(f0=(8, 8, 8, 8), f1=(11, 11, 11, 11))), tmp_path)
    assert SP.animation("run", 3, 10).run(ctx)["ok"] and not SP.animation("run", 4).run(ctx)["ok"]
    assert SP.nine_slice("f0").run(ctx)["ok"] and not SP.nine_slice("f1").run(ctx)["ok"]      # 2 px centre is too small
    assert SP.frames("f0", "f1", "f2").run(ctx)["ok"] and SP.frame_size(24).run(ctx)["ok"]


# ---------------------------------------------------------------- engine

@needs_probe
def test_cinder_reads_lays_out_draws_and_writes_back_a_document(tmp_path):
    ui = sample()
    doc = tmp_path / "s.ui.txt"
    doc.write_text(ui.to_text(), encoding="utf-8", newline="\n")
    report, problem = E.probe_ui(doc, tmp_path / "s.png")
    assert report is not None, problem
    assert report["gpu_errors"] == 0 and len(report["nodes"]) == 4
    assert U.same(U.Ui.from_text(report["roundtrip"]), ui)[0]
    panel, big, small, button = report["nodes"]
    assert abs(panel["x"] + panel["w"] / 2 - 640) <= 1 and abs(panel["y"] + panel["h"] / 2 - 360) <= 1    # centred
    assert big["h"] == 48 and small["h"] == 24 and big["w"] == pytest.approx(2 * small["w"], abs=4)
    assert (tmp_path / "s.png").stat().st_size > 5000
    bad = tmp_path / "bad.ui.txt"
    bad.write_text("cinder-scene 1\nentity 0\n  wheel parent=#-1\n", encoding="utf-8")
    report, problem = E.probe_ui(bad, tmp_path / "bad.png")
    assert report is None and "rejected" in problem


UI = '''
from cadkit.game.ui import *
KIND = "ui"
DESCRIPTION = "test menu"
PARAMS = dict(offset=0)
def checks(p):
    return [has("play", "button"), node_at_least("play", 100, 30)]
def build(p):
    ui = Ui()
    m = ui.root("centre", "menu", offset=(p.offset, 0))
    ui.button(m, "Play", name="play", min_size=(120, 36))
    return UiSet(ui)
'''


@needs_probe
def test_ui_build_is_ready_and_fails_when_a_panel_leaves_the_frame(tmp_path):
    src = tmp_path / "test_menu.py"
    src.write_text(textwrap.dedent(UI), encoding="utf-8")
    good = B.build_asset(src, out_root=tmp_path / "out", quiet=True)
    assert good["ready"], good["blockers"]
    assert good["stats"]["layout"]["play"]["w"] >= 120
    for f in ("test_menu.ui.txt", "test_menu.theme.json", "test_menu.mojo", "test_menu_preview.png"):
        assert (tmp_path / "out" / "test_menu" / f).exists(), f
    bad = B.build_asset(src, ["offset=900"], out_root=tmp_path / "out", quiet=True)
    assert not bad["ready"] and any("in frame" in b for b in bad["blockers"])


SPRITE = '''
from cadkit.game.sprite import *
KIND = "sprite"
DESCRIPTION = "test dots"
PARAMS = dict()
def checks(p):
    return [frames("red", "blue"), frame_size(32)]
def build(p):
    out = {}
    for name, col in (("red", (220, 40, 40)), ("blue", (40, 80, 220))):
        c = Canvas(32)
        c.circle((16, 16), 12, fill=col)
        out[name] = c.image()
    return SpriteSheet(out)
'''


@needs_engine
def test_sprite_build_writes_an_atlas_and_proves_it_on_quads(tmp_path):
    src = tmp_path / "test_dots.py"
    src.write_text(textwrap.dedent(SPRITE), encoding="utf-8")
    b = B.build_asset(src, out_root=tmp_path / "out", quiet=True)
    assert b["ready"], b["blockers"]
    out = tmp_path / "out" / "test_dots"
    doc = json.loads((out / "test_dots.json").read_text(encoding="utf-8"))
    assert doc["schema"] == "cadkit-sprites/1" and set(doc["frames"]) == {"red", "blue"} and doc["alpha"] == "straight"
    assert b["steps"]["engine"]["visible_share"] > 0.002 and b["steps"]["engine"]["cook"]["ktx2"] == 2
    assert (out / "test_dots_quads.glb").exists() and (out / "test_dots_in_engine.png").exists()
