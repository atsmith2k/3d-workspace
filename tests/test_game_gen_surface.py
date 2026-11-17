"""Generated surfaces for baked models: de-lighting, the PBR set made from one picture,
triplanar projection onto a mesh's texels, detail normals. No service is called: the
"generated" picture here is synthetic."""
import numpy as np
import pytest

from cadkit.game import Mesh, box, fbm, noise
from cadkit.game import gen
from cadkit.game.mesh import wind_to_normals
from cadkit.game.texture import seam_error


def picture(n=256, lit=True):
    """A speckled grey 'photo', brighter toward one corner when `lit` (what generators return)."""
    g = 0.25 + 0.3 * noise(n, 48, 1) + 0.15 * fbm(n, 6, 3, 2)
    if lit:
        y, x = np.mgrid[0:n, 0:n] / n
        g = g * (0.6 + 0.8 * x * y)
    return np.clip(np.dstack([g, g * 0.97, g * 0.92]), 0, 1)


def test_delight_takes_the_lighting_out_and_keeps_the_grain():
    img = picture()
    flat = gen.delight(img, keep=0.0)
    assert gen.unevenness(img) > 0.12 and gen.unevenness(flat) < 0.05
    fine = lambda a: float(np.abs(np.diff(a.mean(2), axis=1)).mean())           # noqa: E731
    assert fine(flat) > 0.6 * fine(img)
    assert gen.unevenness(picture(lit=False)) < 0.06


def test_pbr_makes_a_tileable_power_of_two_surface():
    s = gen.pbr(picture(300), metres=1.5, rough=(0.6, 0.9))
    assert s.base.shape == (256, 256, 3) and s.height.shape == (256, 256) and s.rough.shape == (256, 256)
    assert seam_error(s.base) < 1.6
    assert 0 <= s.height.min() < 0.4 and 0.6 < s.height.max() <= 1
    assert 0.6 - 1e-9 <= s.rough.min() and s.rough.max() <= 0.9 + 1e-9
    assert np.corrcoef(s.height.ravel(), s.rough.ravel())[0, 1] < -0.5          # hollows are rougher
    m = s.material("frp_test")
    assert m.base.shape == (256, 256, 3) and m.normal.shape == (256, 256, 3) and m.metallic == 1.0
    n = m.normal * 2 - 1
    assert np.allclose(np.linalg.norm(n, axis=2), 1, atol=1e-6) and n[..., 2].min() > 0


def test_projection_depends_on_where_a_point_is_not_on_its_uv():
    s = gen.pbr(picture(), metres=1.0)
    rng = np.random.default_rng(0)
    pos = rng.uniform(-2, 2, (500, 3))
    up = np.tile([0.0, 1.0, 0.0], (500, 1))
    base, height, rough = s.sample(pos, up)
    assert base.shape == (500, 3) and height.shape == (500,) and rough.shape == (500,)
    again, _, _ = s.sample(pos + [0, 5.0, 0], up)                 # moving along the projection axis changes nothing
    assert np.allclose(base, again)
    wrapped, _, _ = s.sample(pos + [s.metres, 0, 0], up)          # one repeat on: the same texel
    assert np.allclose(base, wrapped, atol=1e-6)
    side, _, _ = s.sample(pos, np.tile([1.0, 0.0, 0.0], (500, 1)))
    assert not np.allclose(base, side, atol=0.02)                 # another face reads another part of the picture
    slant = np.tile([0.7071, 0.7071, 0.0], (500, 1))
    mixed, _, _ = s.sample(pos, slant)
    assert np.allclose(mixed, (base + side) / 2, atol=1e-6)       # a 45 degree face is the even blend


def test_detail_normals():
    flat = gen.slope_normal(np.full((32, 32), 0.3), 5.0)
    assert np.allclose(flat, [0.5, 0.5, 1.0])
    ramp = np.tile(np.linspace(0, 1, 32), (32, 1))               # rises toward +u
    n = gen.slope_normal(ramp, 31.0)[16, 16] * 2 - 1
    assert n[0] == pytest.approx(-0.7071, abs=1e-3) and abs(n[1]) < 1e-6        # a 45 degree slope leans back along -u
    baked = gen.slope_normal(fbm(64, 4, 3, 1), 20.0)
    assert np.allclose(gen.combine_normals(baked, np.zeros((64, 64, 3)) + [0.5, 0.5, 1.0]), baked, atol=1e-6)
    both = gen.combine_normals(baked, gen.slope_normal(noise(64, 30, 2), 6.0)) * 2 - 1
    assert np.allclose(np.linalg.norm(both, axis=2), 1, atol=1e-6)
    lean = lambda m: float(np.degrees(np.arccos(np.clip((np.asarray(m) * 2 - 1)[..., 2], -1, 1))).mean())   # noqa: E731
    assert lean(both * 0.5 + 0.5) > lean(baked)
    mask = np.zeros((32, 32), bool)
    mask[:, :16] = True
    step = np.where(mask, 0.2, 0.9)                              # the empty half must not make a cliff at the island's edge
    assert np.allclose(gen.slope_normal(step, 50.0, mask=mask)[:, :16], [0.5, 0.5, 1.0])


def test_texel_size_and_winding():
    cube = box(1.0, 1.0, 1.0)
    mask = np.zeros((100, 100), bool)
    mask[:60] = True                                              # 6000 texels for 6 m2
    assert gen.texel_metres(cube, mask) == pytest.approx(np.sqrt(6 / 6000))
    f = cube.f.copy()
    f[3] = f[3][[0, 2, 1]]
    fixed = wind_to_normals(Mesh(cube.v, f, cube.n, cube.uv))
    assert np.array_equal(fixed.f, cube.f) and wind_to_normals(cube) is cube


def test_a_surface_picture_is_never_fetched_by_a_plain_build():
    gen.begin(False)
    with pytest.raises(gen.NotGenerated) as e:
        gen.surface_image("a material that was never generated", "no_such_surface_for_tests")
    assert "--gen" in str(e.value)
    assert "seamless" in gen.SURFACE_PROMPT and "no text" in gen.SURFACE_PROMPT.lower()
