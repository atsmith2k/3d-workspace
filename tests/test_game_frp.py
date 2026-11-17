"""The fantasy pack's shared systems: the humanoid skeleton and its sockets, held items, and
the style module (ruler, palette, materials, UV helpers, slots, sound names)."""
import sys
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from cadkit.game import Character, Material, along, box, euler, humanoid, SOCKETS
from cadkit.game import checks as C
from cadkit.game.rig import SHAPES, attach, biped, deform, skin_matrices
from cadkit.game.texture import seam_error

ASSETS = str(Path(__file__).resolve().parents[1] / "assets")
if ASSETS not in sys.path:
    sys.path.insert(0, ASSETS)
import _frp as F  # noqa: E402


@pytest.mark.parametrize("shape", list(SHAPES))
def test_humanoid_has_the_same_bones_in_every_shape(shape):
    sk = humanoid(shape)
    assert len(sk) == 35
    assert sk.names == humanoid("standard").names           # a clip made once plays on all four
    assert sk.names[:18] == biped(1.8).names                # biped clips still address it
    assert all(s in sk.names for s in SOCKETS)
    top = sk.head("socket_head")[1]
    assert SHAPES[shape]["height"] * 0.9 < top <= SHAPES[shape]["height"] + 0.01
    for i, b in enumerate(sk.bones):                        # parents first: glTF and Cinder want it
        assert b.parent is None or b.parent < i


def test_sockets_hang_from_the_bones_they_name_and_mirror():
    sk = humanoid()
    for name, spec in SOCKETS.items():
        assert sk.names[sk.bones[sk.index(name)].parent] == spec["parent"]
    left, right = sk.head("socket_hand.L"), sk.head("socket_hand.R")
    assert np.allclose(left * [-1, 1, 1], right, atol=1e-9) and left[0] > 0     # left is +X
    assert sk.head("socket_back")[2] < 0 < sk.head("eye.L")[2]                  # the figure faces +Z


def stick():
    """A held item to the convention: grip at the origin, 1 m along +Y."""
    return box(0.02, 1.0, 0.02).moved(0, 0.5, 0)


def test_attach_points_a_held_item_forward_and_it_follows_the_hand():
    sk = humanoid()
    ch = Character(sk)
    ch.add(box(0.1, 0.1, 0.1).moved(*sk.head("chest")), Material("m", color=(1, 1, 1)), bind="chest")
    attach(ch, [(stick(), Material("s", color=(1, 1, 1)))], "socket_hand.R")
    mesh, (joints, weights) = ch.parts[-1][0], ch.skins[-1]
    hand = sk.head("socket_hand.R")
    assert np.all(joints[:, 0] == sk.index("socket_hand.R")) and np.allclose(weights[:, 0], 1)
    assert mesh.v[:, 2].max() - hand[2] == pytest.approx(1.0, abs=1e-6)         # +Y became +Z
    assert abs(mesh.v[:, 1].mean() - hand[1]) < 0.02
    # raise the arm: the tip moves with it
    posed = deform(mesh, joints, weights, skin_matrices(sk, {"upper_arm.R": euler(x=-80)}))
    moved = np.linalg.norm(posed.v - mesh.v, axis=1)
    assert moved.min() > 0.05 and moved.max() > 0.5                              # the whole item swings, the tip furthest
    span = lambda v: np.linalg.norm(v - v[0], axis=1)                           # noqa: E731
    assert np.allclose(span(posed.v), span(mesh.v), atol=1e-6)                   # and stays rigid


def test_a_socket_with_nothing_on_it_is_not_an_idle_bone():
    sk = humanoid()
    ch = Character(sk)
    for name in sk.names:
        if name != "root" and not name.startswith("socket_"):
            ch.add(box(0.03, 0.03, 0.03).moved(*sk.head(name)), Material("m", color=(1, 1, 1)), bind=name)
    n = len(sk)
    ctx = SimpleNamespace(model=ch, summary=dict(skin=dict(joints=n, inverse_bind=n, weight_sum_error=0.0,
                                                           joint_index_max=n - 1)))
    ok, why = C._skin(ctx)
    assert ok, why
    bare = Character(sk)
    bare.add(box(0.1, 0.1, 0.1), Material("m", color=(1, 1, 1)), bind="hips")
    ok, why = C._skin(SimpleNamespace(model=bare, summary=ctx.summary))
    assert not ok and "jaw" in why and "socket_" not in why                      # real bones are still caught


def test_along_stands_a_mesh_between_two_points():
    a, b = np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 5.0])
    m = along(stick(), a, b)
    assert np.allclose(m.v.min(0), [0.99, 1.99, 3.0], atol=1e-6) and np.allclose(m.v.max(0), [1.01, 2.01, 4.0], atol=1e-6)
    down = along(stick(), (0, 0, 0), (0, -1, 0))
    assert down.v[:, 1].min() == pytest.approx(-1.0)
    assert np.allclose(np.linalg.norm(m.n, axis=1), 1)


def test_ruler_palette_and_budgets_hold_together():
    assert F.STOREY > F.DOOR_H > F.PERSON and F.DOOR_W < F.GRID
    assert F.WINDOW_SILL + F.WINDOW_H < F.DOOR_H + 0.01
    assert all(len(c) == 3 and all(0 <= v <= 1 for v in c) for c in F.PALETTE.values())
    lum = np.array([0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in F.PALETTE.values()])
    assert np.median(lum) < 0.3                                                 # weighted dark
    assert all({"tris", "texture", "materials"} <= set(b) for b in F.BUDGET_OF.values())
    p = F.product("village", "wall")
    assert p["collection"] == "frp_village" and "wall" in p["tags"] and p["licence"] == F.LICENCE
    assert len(set(F.PREFIX.values())) == len(F.PREFIX)


@pytest.mark.parametrize("make", ["stone", "timber", "plaster", "thatch", "ground", "boards"])
def test_materials_tile_and_stay_dark(make):
    m = getattr(F, make)(256)
    assert m.base.shape == (256, 256, 3)
    assert seam_error(m.base) < 1.6, f"{make} shows a seam"
    assert m.base.mean() < 0.55


def test_uv_helpers():
    post = F.block(0.2, 3.0, 0.2)
    flat, up = F.tiled(post).uv, F.grain_up(post).uv
    assert np.allclose(up, flat[:, ::-1])                                       # a quarter turn
    assert np.ptp(F.tiled(post, 4.0).uv, axis=0).max() == pytest.approx(np.ptp(flat, axis=0).max() / 2)
    slab = F.block(2.0, 0.05, 2.0)
    custom = np.zeros((len(slab.v), 2))
    mixed = F.directed_uv(slab, custom, "y").uv
    top = np.abs(slab.n[:, 1]) > 0.5
    assert np.allclose(mixed[top], 0) and np.ptp(mixed[~top], axis=0).max() > 0.01   # edges keep real UVs
    square = [(0, 0), (0, 1), (1, 1), (1, 0)]                                   # clockwise
    assert F.ccw(square) == square[::-1] and F.ccw(square[::-1]) == square[::-1]


def test_slots_and_sound_names():
    bones = set(n.split(".")[0] for n in humanoid().names)
    for slot, spec in F.SLOTS.items():
        assert set(spec["bones"]) <= bones, slot
        assert all(t in F.SLOTS for t in spec.get("takes", ()))
    assert F.sound_name("step", "stone", 3) == "sfx_step_stone_03"
    assert F.sound_name("music", "village_dusk") == "mus_village_dusk"
    assert all(-12 <= v <= -3 for v in F.SOUND_PEAK.values())
    with pytest.raises(AssertionError):
        F.sound_name("explosion", "x")
