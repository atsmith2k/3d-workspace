"""Blender in the loop (cadkit.game.blender): the bridge's steps, the frame conversion, baking,
the cache, automatic skin weights, and the texturing helpers a baked asset uses.
Tests that start Blender are skipped when it is not installed."""
import numpy as np
import pytest

from cadkit.game import blender as B
from cadkit.game import (Material, Model, Skeleton, box, disc, fbm3, fill_background, lathe, merge, noise3,
                         texel_maps, wedge)
from cadkit.game import checks as C
from cadkit.game.mesh import volume
from cadkit.game.texture import uv_overlap

needs_blender = pytest.mark.skipif(B.find() is None, reason="Blender is not installed (set CAD_BLENDER)")


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "CACHE", tmp_path / "blender")
    return tmp_path / "blender"


def ball(r=0.5, sides=12, rings=8):
    prof = [(r * np.sin(t), -r * np.cos(t)) for t in np.linspace(0, np.pi, rings + 1)]
    prof[0], prof[-1] = (0.0, -r), (0.0, r)
    return lathe(prof, sides)


# ---------------------------------------------------------------- no Blender needed

def test_missing_blender_says_how_to_get_it(monkeypatch):
    monkeypatch.setattr(B, "find", lambda: None)
    s = B.Session()
    s.get(s.add(box(1, 1, 1), "a"))
    with pytest.raises(B.BlenderMissing) as e:
        s.run()
    assert "CAD_BLENDER" in str(e.value) and B.info()["blender"] is None


def test_session_records_steps_in_order():
    s = B.Session()
    hi = s.add(box(1, 1, 1), "high", emit=1.0)
    s.modify(hi, B.subsurf(3), B.displace("VORONOI", scale=0.2, strength=0.05), B.inflate(-0.01))
    lo = s.copy(hi, "low")
    s.decimate(lo, 500)
    s.unwrap(lo)
    s.bake(hi, lo, size=256, maps=("normal", "emit"))
    assert [st["op"] for st in s.steps] == ["load", "modify", "copy", "decimate", "triangulate", "unwrap", "bake"]
    assert s.steps[0]["emit"] == 1.0 and s.steps[-1]["high"] == ["high"] and s.outputs == ["low"]
    stack = s.steps[1]["stack"]
    assert stack[0] == dict(type="SUBSURF", levels=3, render_levels=3, subdivision_type="CATMULL_CLARK")
    assert stack[1]["texture"] == dict(type="VORONOI", noise_scale=0.2) and stack[2]["mid_level"] == 0.0


def test_texel_maps_place_every_texel_on_the_mesh():
    m = box(2, 1, 1)                                             # every face spans 0..1: all texels covered
    quad = m.f[:2]                                               # one face: +X
    one = type(m)(m.v, quad, m.n, m.uv)
    pos, nrm, mask = texel_maps(one, 32)
    assert mask.all() and np.allclose(pos[..., 0], 1.0) and np.allclose(nrm[..., 0], 1.0)
    assert pos[..., 1].min() < -0.4 and pos[..., 1].max() > 0.4
    assert uv_overlap(one) == 0.0 and uv_overlap(m) > 0.9         # six faces stacked on the same square overlap


def test_noise3_is_seamless_seeded_and_bounded():
    p = np.random.default_rng(0).random((2000, 3)) * 5
    a = fbm3(p, 0.5, seed=1)
    assert 0 <= a.min() and a.max() <= 1 and 0.4 < a.mean() < 0.6
    assert np.array_equal(a, fbm3(p, 0.5, seed=1)) and not np.array_equal(a, fbm3(p, 0.5, seed=2))
    line = np.c_[np.linspace(0, 1, 500), np.zeros(500), np.zeros(500)]
    assert np.abs(np.diff(noise3(line, 0.25))).max() < 0.05      # continuous: no jumps along a line


def test_fill_background_carries_island_colour_outward():
    img = np.zeros((16, 16, 3))
    mask = np.zeros((16, 16), bool)
    mask[4:8, 4:8] = True
    img[mask] = [0.2, 0.6, 0.9]
    out = fill_background(img, mask)
    assert np.allclose(out, [0.2, 0.6, 0.9])


def test_uv_unique_check(tmp_path):
    from types import SimpleNamespace
    ctx = SimpleNamespace(model=Model((box(1, 1, 1), Material())))
    r = C.uv_unique().run(ctx)
    assert not r["ok"] and "more than one face" in r["detail"]


# ---------------------------------------------------------------- with Blender

@needs_blender
def test_a_mesh_survives_the_trip_and_keeps_its_frame(cache):
    ramp = wedge(2, 1, 3)                                        # asymmetric on every axis
    s = B.Session()
    s.get(s.add(ramp, "ramp"))
    r = s.run()
    back = r.mesh("ramp")
    assert back.triangles == 8 and np.allclose(back.bounds, ramp.bounds, atol=1e-5)
    assert volume(back) == pytest.approx(volume(ramp), rel=1e-4)                    # not mirrored, not inside out
    assert np.allclose(back.v[back.v[:, 1] > 0.99][:, 2], -1.5, atol=1e-5)          # the high edge is still at -Z
    assert np.allclose(np.linalg.norm(back.n, axis=1), 1, atol=1e-4)
    assert r.info["blender"].startswith(("4.", "5.")) and not r.cached


@needs_blender
def test_sculpt_decimate_unwrap_and_bake(cache):
    s = B.Session()
    hi = s.add(ball(), "high")
    s.modify(hi, B.subsurf(4), B.displace("VORONOI", scale=0.2, strength=0.06))
    lo = s.copy(hi, "low")
    cut = s.add(box(0.25, 0.25, 0.4).moved(0, 0, -0.62), "cut", emit=1.0)           # a square pit 80 mm deep in the -Z side: inside the ray distance
    s.boolean(hi, cut)
    s.decimate(lo, 400)
    s.shade(lo, sharp_angle=60)
    s.unwrap(lo)
    s.bake([hi], lo, size=256, maps=("normal", "ao", "curvature", "emit"), cage=0.05, ray=0.25, samples=8)
    r = s.run()
    low = r.mesh(lo)
    assert r.step("modify")["triangles"] > 20_000 and low.triangles <= 400
    assert 0 <= low.uv.min() and low.uv.max() <= 1 and uv_overlap(low) < 0.01
    pos, nrm, mask = texel_maps(low, 256)
    normal = r.image("normal")[mask] * 2 - 1
    assert np.abs(np.linalg.norm(normal, axis=1) - 1).mean() < 0.05
    assert normal[:, 2].mean() > 0.8                                                # tangent space: mostly straight out
    assert 2 < np.degrees(np.arccos(np.clip(normal[:, 2], -1, 1))).mean() < 40      # and carrying the bumps
    ao = r.image("ao")[mask]
    assert 0.3 < ao.mean() < 0.999 and ao.std() > 0.01                              # a bumpy ball is nearly unoccluded
    # the emissive cutter's faces bake as a mask, even though the curvature bake came first
    emit = r.image("emit")
    lit = (emit > 0.5) & mask
    assert 0.002 < lit.sum() / mask.sum() < 0.2
    assert pos[lit][:, 2].mean() < -0.25                                            # and it is where the hole was cut
    assert abs(r.image("curvature")[mask].mean() - 0.5) < 0.15


@needs_blender
def test_results_are_cached_and_a_changed_step_is_not(cache):
    def job(strength):
        s = B.Session()
        a = s.add(ball(), "a")
        s.modify(a, B.subsurf(2), B.displace("CLOUDS", scale=0.3, strength=strength))
        s.get(a)
        return s
    first = job(0.05).run()
    again = job(0.05).run()
    other = job(0.10).run()
    assert not first.cached and again.cached and not other.cached
    assert np.array_equal(first.mesh("a").v, again.mesh("a").v)
    assert not np.allclose(first.mesh("a").bounds, other.mesh("a").bounds)
    assert len(list(cache.iterdir())) == 2


@needs_blender
def test_a_failing_step_names_itself(cache):
    s = B.Session()
    a = s.add(box(1, 1, 1), "a")
    s.modify(a, dict(type="NO_SUCH_MODIFIER"))
    s.get(a)
    with pytest.raises(SystemExit) as e:
        s.run()
    assert "step 1 (modify)" in str(e.value)


@needs_blender
def test_automatic_weights_follow_the_bones(cache):
    sk = Skeleton()
    sk.add("root", None, (0, 0, 0))
    sk.add("upper", "root", (0, 0, 0))
    sk.add("lower", "upper", (0, 1, 0), tail=(0, 2, 0))
    tube = merge(lathe([(0.1, y) for y in np.linspace(0, 2, 11)], 8), disc(0.1, 0, 8, up=False), disc(0.1, 2, 8))
    s = B.Session()
    s.weights(s.add(tube, "arm"), sk)
    r = s.run()
    mesh = r.mesh("arm")
    joints, weights = r.skin("arm")
    assert joints.shape == (len(mesh.v), 4) and np.allclose(weights.sum(1), 1, atol=1e-5)

    def share(bone, lo, hi):
        rows = (mesh.v[:, 1] >= lo) & (mesh.v[:, 1] <= hi)
        return np.where(joints[rows] == sk.index(bone), weights[rows], 0).sum(1).mean()
    assert share("upper", 0.0, 0.3) > 0.8 and share("lower", 1.7, 2.0) > 0.8        # each end belongs to its bone
    assert 0.2 < share("upper", 0.95, 1.05) < 0.8                                   # the joint is shared


@needs_blender
def test_bake_lowpoly_in_one_call(cache):
    rough = merge(lathe([(0.3, 0), (0.35, 0.5), (0.2, 1.0), (0.0, 1.2)], 8), disc(0.3, 0, 8, up=False))
    low, maps, r = B.bake_lowpoly(rough, tris=300, size=128, maps=("normal", "ao"), samples=4,
                                  prepare=lambda s, name: s.modify(name, B.subsurf(4), B.displace("CLOUDS", 0.2, 0.05)))
    assert low.triangles <= 300 and set(maps) == {"normal", "ao"} and maps["normal"].shape == (128, 128, 3)
    assert maps["ao"].shape == (128, 128) and uv_overlap(low) < 0.01
    assert r.step("modify")["triangles"] > 10_000
