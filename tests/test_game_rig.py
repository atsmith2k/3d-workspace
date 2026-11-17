"""Characters in the game-asset silo: rotations, forward kinematics, skin weights, CPU
skinning, skinned glTF read back independently, clip checks, and (with a Cinder package)
the cook's own .cskel / .cclip output and the visibility test."""
import textwrap
from types import SimpleNamespace

import numpy as np
import pytest

from cadkit.game import (Character, Clip, Material, Model, Skeleton, biped, box, euler, lathe, palette,
                         quat, swatch_uv)
from cadkit.game import build as B
from cadkit.game import checks as C
from cadkit.game import engine as E, gltf
from cadkit.game.rig import (bind_weights, bone_positions, contact_phase, deform, qmat, qmul, skin_matrices,
                             slerp, world_matrices)

ENGINE = E.find()
needs_engine = pytest.mark.skipif(ENGINE is None, reason="no Cinder package (set CAD_CINDER)")


def arm():
    """Two bones along +Y with a tube across the joint, and a 1 s clip that bends the elbow 90 degrees."""
    sk = Skeleton()
    sk.add("root", None, (0, 0, 0))
    sk.add("upper", "root", (0, 0, 0))
    sk.add("lower", "upper", (0, 1, 0), tail=(0, 2, 0))
    ch = Character(sk)
    tube = lathe([(0.1, 0.0), (0.1, 0.5), (0.1, 0.9), (0.1, 1.0), (0.1, 1.1), (0.1, 1.5), (0.1, 2.0)], 8)
    ch.add(tube, Material("m"), bind=["upper", "lower"], blend=0.08)
    ch.clips = [Clip.cycle("bend", 1.0, lambda ph: {"lower": quat(90 * np.sin(np.pi * ph), "x"),
                                                     "upper:move": (0, 0.1 * np.sin(2 * np.pi * ph), 0)}, keys=8)]
    return ch


def test_quaternions_rotate_the_right_way():
    assert np.allclose(qmat(quat(90, "x")) @ [0, 1, 0], [0, 0, 1])          # +Y turns to +Z about X
    assert np.allclose(qmat(quat(90, "y")) @ [0, 0, 1], [1, 0, 0])
    q = qmul(quat(90, "z"), quat(90, "x"))                                  # x first, then z
    assert np.allclose(qmat(q) @ [0, 1, 0], [0, 0, 1]) and np.allclose(qmat(q) @ [1, 0, 0], [0, 1, 0])
    assert np.allclose(euler(x=90, z=90), q)
    half = slerp(quat(0, "x"), quat(90, "x"), 0.5)
    assert np.allclose(half, quat(45, "x")) and np.isclose(np.linalg.norm(half), 1)


def test_forward_kinematics_and_bind_pose():
    ch = arm()
    sk = ch.skeleton
    rest = world_matrices(sk)
    assert np.allclose(rest[2][:3, 3], [0, 1, 0])
    assert all(np.allclose(m, np.eye(4)) for m in skin_matrices(sk))        # bind pose deforms nothing
    bent = world_matrices(sk, {"upper": quat(90, "x")})
    assert np.allclose(bent[2][:3, 3], [0, 0, 1])                           # the elbow swings to +Z
    pos = bone_positions(sk, ch.clips[0], 0.25)
    assert np.allclose(pos["upper"], [0, 0.1, 0], atol=1e-6)                # translation offset track


def test_weights_blend_across_a_joint_and_rigid_elsewhere():
    ch = arm()
    mesh, (j, w) = ch.parts[0][0], ch.skins[0]
    assert np.allclose(w.sum(1), 1) and (w >= 0).all()

    def weight_of(bone, y):
        rows = np.isclose(mesh.v[:, 1], y)
        return np.where(j[rows] == ch.skeleton.index(bone), w[rows], 0).sum(1).mean()

    assert weight_of("upper", 0.0) > 0.99 and weight_of("lower", 2.0) > 0.99
    assert weight_of("upper", 1.0) == pytest.approx(0.5, abs=0.02)          # the elbow ring is shared
    rigid_j, rigid_w = bind_weights(mesh, ch.skeleton, "lower")
    assert (rigid_j[:, 0] == 2).all() and (rigid_w[:, 0] == 1).all()


def test_cpu_skinning_follows_the_bones():
    ch = arm()
    mesh, (j, w) = ch.parts[0][0], ch.skins[0]
    same = deform(mesh, j, w, skin_matrices(ch.skeleton))
    assert np.allclose(same.v, mesh.v)
    posed = ch.posed(ch.clips[0], 0.5).parts[0][0]                          # elbow at 90 degrees, hips at rest
    tip = posed.v[np.isclose(mesh.v[:, 1], 2.0)].mean(0)
    assert np.allclose(tip, [0, 1, 1], atol=0.02)                           # the far end points along +Z
    assert np.allclose(np.linalg.norm(posed.n, axis=1), 1, atol=1e-6)
    row = ch.pose_row(ch.clips[0], poses=3)
    assert row.triangles == 3 * ch.triangles and not hasattr(row, "skeleton")


def test_skinned_glb_reads_back(tmp_path):
    ch = arm()
    path = tmp_path / "arm.glb"
    gltf.write_glb(ch, path, "arm")
    s = gltf.summary(path)
    assert s["skin"]["joints"] == 3 and s["skin"]["inverse_bind"] == 3
    assert s["skin"]["bones"] == ["root", "upper", "lower"]
    assert s["skin"]["weight_sum_error"] < 1e-5 and s["skin"]["joint_index_max"] <= 2
    assert {"JOINTS_0", "WEIGHTS_0"} <= set(s["attributes"])
    clip = s["clips"][0]
    assert (clip["name"], clip["duration"], clip["channels"]) == ("bend", 1.0, 2)
    assert clip["times_sorted"] and clip["quaternion_error"] < 1e-5
    import pygltflib                                                         # node layout Cinder needs
    g = pygltflib.GLTF2().load_binary(str(path))
    assert g.nodes[0].mesh == 0 and g.nodes[0].skin == 0 and g.scenes[0].nodes == [0, 1]
    assert g.nodes[3].translation == [0.0, 1.0, 0.0]                         # local = head - parent head
    paths = {ch_.target.path for ch_ in g.animations[0].channels}
    assert paths == {"rotation", "translation"}


def test_character_checks(tmp_path):
    ch = arm()
    path = tmp_path / "arm.glb"
    gltf.write_glb(ch, path, "arm")
    ctx = SimpleNamespace(model=ch, summary=gltf.summary(path), params={}, name="arm", budget=None)
    results = {c.name: c.run(ctx) for c in C.static_checks(ch)}
    assert {"skin", "clip data"} <= set(results) and all(r["ok"] for r in results.values()), results
    assert C.clips("bend").run(ctx)["ok"] and not C.clips("walk").run(ctx)["ok"]
    # a loop that does not return to its start is caught
    ch.clips = [Clip("pop", 1.0, rotations={"lower": [(0.0, quat(0, "x")), (1.0, quat(40, "x"))]})]
    gltf.write_glb(ch, path, "arm")
    ctx.summary = gltf.summary(path)
    r = {c.name: c.run(ctx) for c in C.static_checks(ch)}["clip data"]
    assert not r["ok"] and "does not end where it starts" in r["detail"]


def test_biped_template_and_phase():
    sk = biped(1.75)
    assert len(sk) == 18 and sk.names[0] == "root"
    assert all(b.parent < i for i, b in enumerate(sk.bones))
    assert sk.head("upper_arm.L")[0] > 0 > sk.head("upper_arm.R")[0]        # left is +X facing +Z
    assert sk.tail(sk.index("foot.L"))[2] > 0                                # toes point +Z
    stride = lambda off: Clip.cycle("c", 1.0, lambda ph: {                   # noqa: E731
        "upper_leg.L": euler(x=-30 * np.cos(2 * np.pi * (ph + off)))}, keys=16)
    assert contact_phase(sk, stride(0.0), "foot.L") == pytest.approx(0.0, abs=0.02)
    assert contact_phase(sk, stride(0.25), "foot.L") == pytest.approx(0.75, abs=0.02)


def test_palette_material_is_flat_and_passes_the_uv_check(tmp_path):
    pal = palette("p", [(1, 0, 0), (0, 1, 0), (0, 0, 1)])
    assert pal.base.shape == (16, 64, 3) and pal.flat_uv
    m = swatch_uv(box(1, 1, 1), 1, pal)
    assert np.allclose(m.uv, [0.375, 0.5])
    model = Model((m, pal))
    path = tmp_path / "p.glb"
    gltf.write_glb(model, path, "p")
    ctx = SimpleNamespace(model=model, summary=gltf.summary(path), params={}, name="p", budget=None)
    assert {c.name: c.run(ctx)["ok"] for c in C.static_checks()}["uvs"]


RIGGED = '''
from cadkit.game import *
KIND = "character"
DESCRIPTION = "test arm"
PARAMS = dict()
ENGINE = dict(rest_y=0.0)
def checks(p):
    return [clips("bend")]
def build(p):
    sk = Skeleton()
    sk.add("root", None, (0, 0, 0))
    sk.add("upper", "root", (0, 0, 0))
    sk.add("lower", "upper", (0, 1, 0), tail=(0, 2, 0))
    ch = Character(sk)
    pal = palette("pal", [(0.8, 0.3, 0.2)])
    tube = lathe([(0.15, 0.0), (0.15, 0.9), (0.15, 1.0), (0.15, 1.1), (0.15, 2.0)], 8)
    ch.add(swatch_uv(tube, 0, pal), pal, bind=["upper", "lower"], blend=0.08)
    ch.clips = [Clip.cycle("bend", 1.0, lambda ph: {"lower": quat(60 * np.sin(np.pi * ph), "x")}, keys=8)]
    return ch
'''


@needs_engine
def test_character_cooks_to_a_skeleton_and_clips_the_engine_reads_back(tmp_path):
    src = tmp_path / "test_arm.py"
    src.write_text(textwrap.dedent(RIGGED), encoding="utf-8")
    b = B.build_asset(src, out_root=tmp_path / "out", quiet=True)
    assert b["ready"], b["blockers"]
    cook = b["steps"]["cook"]
    assert cook["outputs"]["cskel"] == 1 and cook["outputs"]["cclip"] == 1
    clip = cook["clips"][0]                                                  # parsed from the engine's .cclip
    assert (clip["magic"], clip["name"], clip["duration"], clip["channels"]) == ("CCLP", "bend", 1.0, 1)
    assert clip["keys"] == [9] and clip["consumed_all"]
    eng = b["steps"]["engine"]
    assert eng["frames"] == 4 and "skinned_drawn_by_world_kit" in eng
    assert b["stats"]["bones"] == 3 and b["stats"]["clips"][0]["name"] == "bend"


@needs_engine
def test_visibility_tells_a_drawn_model_from_an_undrawn_one(tmp_path):
    stage = tmp_path / "stage"
    stage.mkdir()
    solid = Model((box(0.5, 0.5, 0.5), Material("m", color=(0.8, 0.2, 0.2))))
    glb = tmp_path / "solid.glb"
    gltf.write_glb(solid, glb, "solid")
    assert B._visibility(ENGINE, glb, solid.bounds, stage) > 0.01
    speck = Model((box(1e-4, 1e-4, 1e-4), Material("m")))                    # loads, but covers no pixel
    glb2 = tmp_path / "speck.glb"
    gltf.write_glb(speck, glb2, "speck")
    big = (np.array([-0.25, -0.25, -0.25]), np.array([0.25, 0.25, 0.25]))
    assert B._visibility(ENGINE, glb2, big, stage) < 0.002


def test_ball_and_capsule_are_closed_and_span_their_points():
    from cadkit.game import ball, capsule, volume
    b = ball(0.5, 24, 16)
    assert volume(b) == pytest.approx(4 / 3 * np.pi * 0.125, rel=0.03)
    c = capsule((1, 0, 0), (1, 0, 2), 0.2, 0.1, sides=16)
    lo, hi = c.bounds
    assert np.allclose(lo, [0.8, -0.2, -0.2], atol=0.01) and np.allclose(hi, [1.2, 0.2, 2.1], atol=0.01)
    assert volume(c) > 0                                                      # faces outward after the turn
    down = capsule((0, 1, 0), (0, 0, 0), 0.1)                                 # straight down: the degenerate turn
    assert np.allclose(down.bounds[0], [-0.1, -0.1, -0.1], atol=0.01) and volume(down) > 0


def test_pre_skinned_parts_and_the_deformation_check():
    ch = arm()
    mesh, (j, w) = ch.parts[0][0], ch.skins[0]
    good = Character(ch.skeleton)
    good.add_skinned(mesh, Material("m"), j, w * 3)                           # rows are renormalised
    good.clips = ch.clips
    assert np.allclose(good.skins[0][1].sum(1), 1)
    ctx = SimpleNamespace(model=good, params={}, name="arm", budget=None)
    assert C.deforms_cleanly().run(ctx)["ok"]
    # one ring of the upper arm bound to the forearm: its edges stretch when the elbow bends
    bad_j, bad_w = j.copy(), w.copy()
    rows = np.isclose(mesh.v[:, 1], 0.0)
    bad_j[rows], bad_w[rows] = [2, 0, 0, 0], [1.0, 0, 0, 0]
    bad = Character(ch.skeleton)
    bad.add_skinned(mesh, Material("m"), bad_j, bad_w)
    bad.clips = ch.clips
    ctx.model = bad
    r = C.deforms_cleanly().run(ctx)
    assert not r["ok"] and "wrong bone" in r["detail"]
    with pytest.raises(ValueError):
        Character(ch.skeleton).add_skinned(mesh, Material("m"), j[:-1], w[:-1])
    with pytest.raises(ValueError):
        Character(ch.skeleton).add_skinned(mesh, Material("m"), j, w * 0)
