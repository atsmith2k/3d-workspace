"""Game-asset silo (cadkit/game): primitives, textures, the GLB writer against two
independent readers, the checks, and the engine ladder when a Cinder package is installed."""
import json
import math
import textwrap
from types import SimpleNamespace

import numpy as np
import pytest

from cadkit.game import (Material, Model, box, cylinder, disc, fbm, flat, lathe, merge, noise,
                         normal_from_height, orm, seam_error, streaks, torus, volume)
from cadkit.game import build as B
from cadkit.game import checks as C
from cadkit.game import cli, engine as E, gltf

ENGINE = E.find()
needs_engine = pytest.mark.skipif(ENGINE is None, reason="no Cinder package (set CAD_CINDER)")


# ---------------------------------------------------------------- meshes

def test_primitives_wind_outward_with_unit_normals():
    for m, vol in ((box(1, 2, 3), 6.0), (cylinder(0.5, 2, 48), math.pi * 0.25 * 2),
                   (torus(1.0, 0.2, 48, 24), 2 * math.pi ** 2 * 1.0 * 0.04)):
        assert volume(m) == pytest.approx(vol, rel=0.02)
        assert np.allclose(np.linalg.norm(m.n, axis=1), 1, atol=1e-6)
        a, b, c = (m.v[m.f[:, k]] for k in range(3))
        assert ((np.cross(b - a, c - a) * m.n[m.f].sum(1)).sum(1) > 0).all()


def test_lathe_uv_and_axis_point():
    cone = lathe([(0.5, 0), (0.0, 1)], sides=12)                  # tip on the axis: no slivers
    a, b, c = (cone.v[cone.f[:, k]] for k in range(3))
    assert (np.linalg.norm(np.cross(b - a, c - a), axis=1) > 1e-9).all()
    side = lathe([(1, 0), (1, 2)], sides=8, u_repeat=3, v_range=(0, 0.5))
    assert side.uv[:, 0].max() == pytest.approx(3) and side.uv[:, 1].max() == pytest.approx(0.5)
    top = side.v[:, 1] == 2
    assert np.allclose(side.uv[top, 1], 0)                       # image top is model top


def test_transforms_keep_winding():
    m = box(1, 1, 1).scaled(-1, 1, 1).rotated(37, "x").moved(1, 2, 3)
    assert volume(m.moved(-1, -2, -3)) == pytest.approx(1.0)
    assert volume(flat(disc(1, 0, 16) + lathe([(0, -1), (1, 0)], 16))) > 0


# ---------------------------------------------------------------- textures

def test_procedural_textures_tile_and_are_seeded():
    for img in (noise(128, 8, 1), fbm(128, 4, 4, 2), streaks(128, "x", 32, 4, 3)):
        assert 0 <= img.min() and img.max() <= 1
        assert seam_error(img) < 1.2
    assert np.array_equal(fbm(64, seed=7), fbm(64, seed=7))
    assert not np.array_equal(fbm(64, seed=7), fbm(64, seed=8))
    assert seam_error(np.linspace(0, 1, 64)[None, :].repeat(64, 0)) > 10    # a ramp does not tile


def test_normal_map_is_unit_and_gltf_convention():
    h = np.zeros((32, 32))
    h[:, 16:] = 1.0                                               # a step up toward +u
    n = normal_from_height(h, 2) * 2 - 1
    assert np.allclose(np.linalg.norm(n, axis=2), 1, atol=1e-6)
    assert n[8, 16, 0] < 0 and n[..., 2].min() > 0                # leans away from the rise
    h = np.zeros((32, 32))
    h[:16] = 1.0                                                  # higher toward the image top
    assert (normal_from_height(h, 2) * 2 - 1)[16, 8, 1] < 0       # +Y is up the image


# ---------------------------------------------------------------- glTF

def _model():
    g = fbm(64, seed=1)
    mat = Material("wood", base=np.dstack([g, g * 0.7, g * 0.4]) * 0.6 + 0.2, orm=orm(1, 0.6 + 0.2 * g, 0),
                   normal=normal_from_height(g, 2), metallic=1.0, roughness=1.0)
    glow = Material("glow", color=(1, 0.7, 0.4), emissive=(1, 0.5, 0.2), emissive_strength=4.0)
    return Model((box(0.8, 0.8, 0.8), mat), (box(0.2, 0.2, 0.2).moved(0, 0.5, 0), glow))


def test_glb_reads_back_through_two_independent_readers(tmp_path):
    model = _model()
    path = tmp_path / "thing.glb"
    assert gltf.write_glb(model, path, "thing") == path.stat().st_size
    s = gltf.summary(path)                                        # pygltflib
    assert (s["triangles"], s["vertices"], s["materials"]) == (24, 48, 2)
    assert s["modes"] == [4] and s["extensions"] == ["KHR_materials_emissive_strength"]
    assert len(s["images"]) == 3 and all(i["width"] == 64 for i in s["images"])
    assert np.allclose(s["bounds"], model.bounds, atol=1e-6)
    import trimesh                                                # a second reader
    scene = trimesh.load(path)
    assert sum(len(g.faces) for g in scene.geometry.values()) == 24
    assert np.allclose(scene.bounds, model.bounds, atol=1e-6)
    doc = json.loads(path.read_bytes()[20:20 + int.from_bytes(path.read_bytes()[12:16], "little")])
    wood = doc["materials"][0]
    assert wood["occlusionTexture"]["index"] == wood["pbrMetallicRoughness"]["metallicRoughnessTexture"]["index"]


def test_parts_sharing_a_material_merge_into_one_primitive(tmp_path):
    mat = Material("m")
    model = Model((box(1, 1, 1), mat), (box(1, 1, 1).moved(2, 0, 0), mat))
    gltf.write_glb(model, tmp_path / "two.glb")
    assert gltf.summary(tmp_path / "two.glb")["primitives"] == 1


# ---------------------------------------------------------------- checks

def _ctx(model, name="thing", budget=None, tmp=None):
    path = tmp / f"{name}.glb"
    gltf.write_glb(model, path, name)
    return SimpleNamespace(model=model, summary=gltf.summary(path), params={}, name=name, budget=budget)


def test_checks_pass_on_a_good_model_and_say_why_on_a_bad_one(tmp_path):
    ctx = _ctx(_model(), tmp=tmp_path)
    assert all(c.run(ctx)["ok"] for c in C.static_checks())
    assert C.size(x=0.8, z=0.8).run(ctx)["ok"]
    r = C.size(y=2.0).run(ctx)
    assert not r["ok"] and "y 1.000 not in" in r["detail"]
    assert not C.tris(max=10).run(ctx)["ok"] and C.materials(2).run(ctx)["ok"]
    assert not C.pivot("centre").run(ctx)["ok"]                   # the small box sits on top
    assert C.pivot("centre").run(_ctx(Model((box(1, 1, 1), Material())), tmp=tmp_path))["ok"]
    assert C.pivot("base").run(_ctx(Model((box(1, 1, 1).moved(0, 0.5, 0), Material())), tmp=tmp_path))["ok"]


def test_static_checks_catch_real_faults(tmp_path):
    def failing(model, **kw):
        ctx = _ctx(model, tmp=tmp_path, **kw)
        return {r["name"] for r in (c.run(ctx) for c in C.static_checks()) if not r["ok"]}

    assert failing(_model(), name="Bad Name") == {"name"}
    assert failing(_model(), budget=dict(tris=10)) == {"budget"}
    b = box(1, 1, 1)
    inside_out = Model((type(b)(b.v, b.f[:, ::-1], b.n, b.uv), Material()))
    assert failing(inside_out) == {"geometry"}
    odd = Material("odd", base=np.full((48, 48, 3), 0.5))         # not a power of two
    assert failing(Model((box(1, 1, 1), odd))) == {"textures"}
    black = Material("black", base=np.zeros((32, 32, 3)))
    assert failing(Model((box(1, 1, 1), black))) == {"textures"}
    factors = Material("f", orm=orm(1, 0.5, 0, size=32), roughness=0.5)
    assert failing(Model((box(1, 1, 1), factors))) == {"textures"}
    no_uv = box(1, 1, 1).with_uv(np.zeros((24, 2)))
    assert failing(Model((no_uv, Material("t", base=np.full((32, 32, 3), 0.5))))) == {"uvs"}


def test_schema_is_json_and_lists_every_check():
    s = json.loads(json.dumps(cli.schema()))
    assert s["schema"] == "cadkit-game/1" and "prop" in s["kinds"]["built"]
    assert set(s["checks"]["always"]) == {c.name for c in C.static_checks()}


# ---------------------------------------------------------------- engine

def test_staging_world_stands_the_model_on_the_floor():
    text = E.staging_world("x/thing.glb", (np.array([-0.4, -0.2, -0.4]), np.array([0.4, 0.6, 0.4])),
                           body="dynamic", drop=0.5)
    assert text.startswith("cinder-world 1\n")
    assert "transform position=[0,0.7,0]" in text                 # 0.2 below the origin + 0.5 drop
    assert 'body motion="dynamic" collider="auto"' in text and "thing.glb" in text


@needs_engine
def test_staging_world_is_valid_for_the_engine(tmp_path):
    glb = tmp_path / "thing.glb"
    gltf.write_glb(_model(), glb, "thing")
    world = tmp_path / "s.world"
    world.write_text(E.staging_world(glb, _model().bounds, body="static"), encoding="utf-8")
    ok, out = ENGINE.check(world)
    assert ok, out


ASSET = '''
from cadkit.game import *
KIND = "prop"
DESCRIPTION = "test box"
PARAMS = dict(lift=0.0)
BUDGET = dict(tris=12, materials=1)
ENGINE = dict(body="dynamic", collider="box")
def checks(p):
    return [size(x=0.5, y=0.5, z=0.5)]
def build(p):
    g = fbm(32, seed=1)
    mat = Material("m", base=tint(g, (0.3, 0.3, 0.3), (0.7, 0.7, 0.7)))
    return Model((box(0.5, 0.5, 0.5).moved(0, p.lift, 0), mat))
'''


@needs_engine
def test_ladder_passes_a_good_prop_and_fails_an_off_centre_collider(tmp_path):
    src = tmp_path / "test_box.py"
    src.write_text(textwrap.dedent(ASSET), encoding="utf-8")
    good = B.build_asset(src, out_root=tmp_path / "out", quiet=True)
    assert good["ready"], good["blockers"]
    assert good["steps"]["cook"]["outputs"]["cmesh"] == 1 and good["steps"]["engine"]["frames"] == 4
    assert (tmp_path / "out" / "test_box" / "test_box_preview.png").stat().st_size > 20000
    assert "model path=" in good["world_snippet"]
    # origin at the base: the engine centres the box collider on the entity, so the visual
    # sinks half its height into the floor. The drop test must say so.
    bad = B.build_asset(src, ["lift=0.25"], out_root=tmp_path / "out", quiet=True)
    assert not bad["ready"]
    assert any(b.startswith("engine physics") for b in bad["blockers"]), bad["blockers"]


def test_without_an_engine_a_build_is_never_ready(tmp_path):
    src = tmp_path / "test_box.py"
    src.write_text(textwrap.dedent(ASSET), encoding="utf-8")
    b = B.build_asset(src, out_root=tmp_path / "out", use_engine=False, quiet=True)
    assert not b["ready"] and "not verified in Cinder" in b["blockers"][0]
    assert all(r["ok"] for r in b["steps"]["static"]["checks"])


# ---------------------------------------------------------------- phase 1: materials, worlds, packs

def test_library_materials_tile_and_are_shared():
    from cadkit.game import flagstones, iron, planks, stone_blocks
    for mat in (stone_blocks(256, 4, 2, seed=1), flagstones(256), planks(256), iron(128)):
        for slot, img in mat.textures().items():
            assert seam_error(img) < 1.6, (mat.name, slot)
        assert mat.metallic == 1.0 and mat.roughness == 1.0        # factors left for the orm map
    assert stone_blocks(256, 4, 2, seed=1) is stone_blocks(256, 4, 2, seed=1)   # one object, one draw call


def test_prism_and_block():
    from cadkit.game import block, prism
    tri = prism([(0, 0), (2, 0), (0, 1)], 3)                      # counter-clockwise seen from +Z
    assert volume(tri) == pytest.approx(3.0)
    assert np.allclose(tri.bounds, ([0, 0, -1.5], [2, 1, 1.5]))
    b = block(1, 2, 3, x=5, y=1, z=-2)
    assert np.allclose(b.bounds, ([4.5, 1, -3.5], [5.5, 3, -0.5]))


def test_pivot_anchors(tmp_path):
    from cadkit.game import block
    floor = _ctx(Model((block(2, 0.2, 2, y=-0.2), Material())), tmp=tmp_path)
    assert C.pivot("top").run(floor)["ok"] and not C.pivot("base").run(floor)["ok"]
    hung = _ctx(Model((box(0.2, 0.4, 0.3).moved(0, 0.1, -0.15), Material())), tmp=tmp_path)
    assert C.pivot((0.5, None, 1.0)).run(hung)["ok"]              # back face centred, height free
    assert not C.pivot("back").run(hung)["ok"]


def test_world_writer_values_and_place():
    from cadkit.game.world import World, value
    assert value(True) == "true" and value("box") == '"box"' and value(3) == "3"
    assert value((0, 1.5, -2)) == "[0,1.5,-2]" and value(["plate_a", "plate_b"]) == "[plate_a,plate_b]"
    assets = dict(crate=dict(file="assets/crate.glb", rest_y=0.4, engine_use=dict(body="dynamic", collider="box")),
                  gem=dict(file="assets/gem.glb", rest_y=1.0, engine_use={}))
    w = World("t", assets=assets)
    w.environment(exposure=1.1)
    w.place("crate", (1, 0, -2), yaw=30)
    w.place("crate", (1, 0.8, -2))
    w.place("gem", (0, 0, -3), name="ruby", pickup=dict(points=10))
    w.add("gate", door=dict(triggers=["plate"], mode="latch"))
    text = w.text()
    assert text.splitlines()[:3] == ["cinder-world 1", 'world title="t"', "environment exposure=1.1"]
    assert "entity crate\n  transform position=[1,0.4,-2] rotation=[0,30,0]\n  model path=\"assets/crate.glb\"\n" \
           '  body motion="dynamic" collider="box"' in text
    assert "entity crate_2\n  transform position=[1,1.2,-2]" in text
    assert "entity ruby\n  transform position=[0,1,-3]\n  model path=\"assets/gem.glb\"\n  pickup points=10" in text
    assert 'door triggers=[plate] mode="latch"' in text
    with pytest.raises(ValueError):
        w.add("gate")


PACK = '''
TITLE = "Test Pack"
DESCRIPTION = "two boxes"
COLLECTION = "test_pack"
DEMO = dict(seconds=6, autopilot=True, expect_won=True)
SHOTS = [dict(name="view", position=(2, 1.5, 3), target=(0, 0.3, -2))]
def demo(w):
    w.add("sun", light=dict(kind="sun", direction=(-0.4, -1, -0.3), intensity=3, shadows=True))
    w.add("floor", transform=dict(position=(0, -0.5, 0)), shape=dict(kind="box", size=(20, 1, 20)),
          body=dict(motion="static"))
    w.place("test_box", (1.5, 0, -2))
    w.place("test_box", (1.5, 0.5, -2))
    w.place("test_goal", (0, 0, -4), body=False, goal=dict(radius=1.5))
    w.add("hero", transform=dict(position=(0, 0.1, 0)), player=dict(speed=4))
'''


@needs_engine
def test_pack_builds_plays_its_demo_and_installs(tmp_path, monkeypatch):
    from cadkit.game import pack as P
    assets = tmp_path / "assets"
    assets.mkdir()
    src = textwrap.dedent(ASSET) + 'PRODUCT = dict(collection="test_pack", licence="CC0-1.0")\n'
    (assets / "test_box.py").write_text(src, encoding="utf-8")
    (assets / "test_goal.py").write_text(src.replace('ENGINE = dict(body="dynamic", collider="box")',
                                                     "ENGINE = dict(rest_y=0.25)"), encoding="utf-8")
    (assets / "other.py").write_text(textwrap.dedent(ASSET), encoding="utf-8")          # not in the pack
    script = tmp_path / "test_pack.py"
    script.write_text(textwrap.dedent(PACK), encoding="utf-8")
    monkeypatch.setattr(P, "ASSETS", assets)
    monkeypatch.setattr(B, "OUT", tmp_path / "out")
    monkeypatch.setattr(P, "PACKS_OUT", tmp_path / "out" / "packs")

    m = P.build_pack(script, quiet=True)
    assert m["ready"], m["problems"]
    assert [a["id"] for a in m["assets"]] == ["test_box", "test_goal"]
    assert m["demo"]["won"] and m["demo"]["models"] == 3 and m["demo"]["gpu_errors"] == 0
    out = tmp_path / "out" / "packs" / "test_pack"
    for f in ("assets/test_box.glb", "previews/test_goal.png", "worlds/demo.world", "manifest.json",
              "AGENTS.md", "ATTRIBUTION.md", "test_pack_contents.png", "test_pack_view.png"):
        assert (out / f).exists(), f
    a = m["assets"][0]
    assert a["cook"]["meshes"] == ["test_box#mesh0/prim0"] and a["rest_y"] == 0.25 and a["licence"] == "CC0-1.0"
    assert 'model path="assets/test_box.glb"' in (out / "AGENTS.md").read_text(encoding="utf-8")
    # unchanged members are not rebuilt; an edited one is
    stamp = (tmp_path / "out" / "test_box" / "build.json").stat().st_mtime_ns
    P.build_pack(script, quiet=True)
    assert (tmp_path / "out" / "test_box" / "build.json").stat().st_mtime_ns == stamp
    r = P.install("test_pack", tmp_path / "game", cook=True)
    assert r["cook"]["ok"] and r["cook"]["outputs"]["cmesh"] == 2
    assert (tmp_path / "game" / "test_pack" / "cooked" / "manifest.txt").exists()


# ---------------------------------------------------------------- sandbox round: nodes, bevels, ramps

def test_bevel_box_keeps_full_size_faces_and_wedge_climbs_forward():
    from cadkit.game import bevel_box, wedge
    b = bevel_box(1, 2, 3, 0.05)
    assert b.triangles == 44 and np.allclose(b.bounds, ([-0.5, -1, -1.5], [0.5, 1, 1.5]))
    assert 5.9 < volume(b) < 6.0                                  # a little off each edge, nothing more
    top = b.v[np.isclose(b.v[:, 1], 1.0)]
    assert np.allclose(np.abs(top[:, 0]).max(), 0.45)             # the flat top stops a bevel short of the edge
    assert 0 <= b.uv.min() and b.uv.max() <= 1
    w = wedge(2, 1, 2)
    assert volume(w) == pytest.approx(2.0) and np.allclose(w.bounds, ([-1, 0, -1], [1, 1, 1]))
    assert np.allclose(w.v[w.v[:, 1] > 0.99][:, 2], -1)           # the high edge is at -Z: it climbs forward


def test_star_prism_caps_fan_from_a_centre():
    from cadkit.game import prism
    star = [(np.cos(a) * (1 if i % 2 == 0 else 0.4), np.sin(a) * (1 if i % 2 == 0 else 0.4))
            for i, a in enumerate(np.linspace(0, 2 * np.pi, 10, endpoint=False))]
    area = 0.5 * abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(star, star[1:] + star[:1])))
    assert volume(prism(star, 0.5, centre=(0, 0))) == pytest.approx(area * 0.5)
    assert volume(prism(star, 0.5)) != pytest.approx(area * 0.5)   # a plain fan is wrong for a concave outline


def test_named_nodes_become_separate_mesh_nodes(tmp_path):
    steel = Material("steel")
    model = Model((box(1, 0.3, 1), steel), (box(0.2, 0.3, 0.2).moved(0, 0.3, 0), steel, "spikes"),
                  (box(0.1, 0.1, 0.1), steel))                    # merges into the unnamed node
    assert model.nodes == [None, "spikes"] and model.node_names == [None, "spikes"]
    path = tmp_path / "trap.glb"
    gltf.write_glb(model, path, "trap")
    s = gltf.summary(path)
    assert s["mesh_nodes"] == [dict(name="trap", primitives=1), dict(name="spikes", primitives=1)]
    assert s["triangles"] == 36 and s["materials"] == 2
    import trimesh
    assert len(trimesh.load(path).geometry) == 2
    plain = tmp_path / "plain.glb"
    gltf.write_glb(Model((box(1, 1, 1), steel)), plain, "plain")
    assert gltf.summary(plain)["mesh_nodes"] == [dict(name="plain", primitives=1)]


def test_sandbox_atlas_tiles(tmp_path):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "assets"))
    import _sandbox as SB
    mat = SB.atlas()
    assert mat.base.shape == (512, 512, 3) and mat is SB.atlas()
    m = SB.tile(box(1, 1, 1), SB.T.RED)                           # tile 6: column 2, row 1
    assert 0.5 < m.uv[:, 0].min() and m.uv[:, 0].max() < 0.75 and 0.25 < m.uv[:, 1].min() and m.uv[:, 1].max() < 0.5
    red = mat.base[128 + 64, 256 + 64]
    assert red[0] > 0.6 and red[1] < 0.25
    assert mat.orm[64, 384 + 64, 2] == 0 and mat.orm[256 + 64, 64, 2] == 1      # grey is not metal, steel is
    up = SB.along(lathe([(0.1, 0), (0.1, 1)], 6), (0, 0, 0), (1, 0, 0))
    assert np.allclose(up.bounds[1][0], 1.0) and abs(up.bounds[1][1]) < 0.11


@needs_engine
def test_pack_settle_check_catches_a_stack_that_falls(tmp_path, monkeypatch):
    from cadkit.game import pack as P
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "test_box.py").write_text(textwrap.dedent(ASSET) + 'PRODUCT = dict(collection="settle")\n', encoding="utf-8")
    script = tmp_path / "settle.py"
    body = '''
TITLE = "Settle"
DESCRIPTION = "boxes"
COLLECTION = "settle"
DEMO = dict(seconds=4, settle=dict(max_move=0.25))
def demo(w):
    w.add("sun", light=dict(kind="sun", direction=(-0.4, -1, -0.3), intensity=3))
    w.add("floor", transform=dict(position=(0, -0.5, 0)), shape=dict(kind="box", size=(20, 1, 20)),
          body=dict(motion="static"))
    w.place("test_box", (0, 0.02, 0))
    w.place("test_box", (0, HEIGHT, 0))
'''
    monkeypatch.setattr(P, "ASSETS", assets)
    monkeypatch.setattr(B, "OUT", tmp_path / "out")
    monkeypatch.setattr(P, "PACKS_OUT", tmp_path / "out" / "packs")
    script.write_text(textwrap.dedent(body).replace("HEIGHT", "0.54"), encoding="utf-8")
    good = P.build_pack(script, quiet=True)
    assert good["ready"], good["problems"]
    assert max(m["moved_m"] for m in good["demo"]["dynamic_bodies"]) < 0.1
    script.write_text(textwrap.dedent(body).replace("HEIGHT", "3.0"), encoding="utf-8")     # dropped from 3 m
    bad = P.build_pack(script, quiet=True)
    assert not bad["ready"] and any("did not stand" in p for p in bad["problems"])
