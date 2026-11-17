"""cadkit.lithophane: tone mapping, mesh validity per shape, relief filter, calibration."""
import math

import numpy as np
import pytest
from PIL import Image

from cadkit import mesh as meshmod
from cadkit.lithophane import (Lithophane, fit_transmittance, inverse_lightness, lightness,
                               printable_relief)


@pytest.fixture(scope="module")
def photo(tmp_path_factory):
    """Small synthetic photo: horizontal gradient plus a dark disc, 4:3."""
    w, h = 160, 120
    x = np.linspace(0, 255, w)[None, :].repeat(h, 0)
    yy, xx = np.mgrid[0:h, 0:w]
    x[(xx - 50) ** 2 + (yy - 60) ** 2 < 25 ** 2] = 10
    path = tmp_path_factory.mktemp("litho") / "photo.png"
    Image.fromarray(x.astype(np.uint8)).convert("RGB").save(path)
    return path


@pytest.mark.parametrize("model", ["perceptual", "transmittance", "linear"])
def test_thickness_endpoints_and_monotonic(photo, model):
    L = Lithophane(photo, width=40, res=0.5, model=model)
    y = np.linspace(0, 1, 101)
    t = L.thickness_of(y)
    assert t[0] == pytest.approx(L.max_t, abs=1e-6)        # black = thickest
    assert t[-1] == pytest.approx(L.min_t, abs=1e-6)       # white = thinnest
    assert np.all(np.diff(t) <= 1e-9)


def test_transmittance_model_is_curas_formula(photo):
    L = Lithophane(photo, width=40, res=0.5, model="transmittance", transmittance=0.4,
                   min_t=0.8, max_t=3.2)
    y = np.array([0.0, 0.1, 0.5, 0.9, 1.0])
    # Cura ImageReader: divisor = 1/log(T1mm); min_luminance = T1mm ** (peak - base)
    min_lum = 0.4 ** (3.2 - 0.8)
    cura = 0.8 + np.log(min_lum + (1 - min_lum) * y) / math.log(0.4)
    assert np.allclose(L.thickness_of(y), cura)
    # and the light that comes through is the target luminance, rescaled
    lit = 0.4 ** (L.thickness_of(y) - 0.8)
    assert np.allclose(lit, min_lum + (1 - min_lum) * y)


def test_perceptual_spreads_shadows(photo):
    """Dark tone steps stay further apart than under Cura's linear squeeze."""
    P = Lithophane(photo, width=40, res=0.5, model="perceptual")
    T = Lithophane(photo, width=40, res=0.5, model="transmittance")
    steps = np.array([0.0, 0.02, 0.05])
    lp = lightness(P.tau ** (P.thickness_of(steps) - P.min_t))
    lt = lightness(T.tau ** (T.thickness_of(steps) - T.min_t))
    assert np.diff(lp).min() > 1.5 * np.diff(lt).min()
    assert inverse_lightness(lightness(0.3)) == pytest.approx(0.3)


@pytest.mark.parametrize("kw", [dict(shape="flat"), dict(shape="arc", curve=90),
                                dict(shape="cylinder"), dict(shape="flat", outline="heart"),
                                dict(shape="flat", outline="oval", stand=20)])
def test_solid_is_one_watertight_body(photo, kw):
    L = Lithophane(photo, width=60, res=0.5, **kw)
    tm = meshmod.to_trimesh(L.solid())
    assert tm.is_watertight
    assert len(tm.split(only_watertight=False)) == 1
    assert tm.bounds[0][2] == pytest.approx(0, abs=1e-3)          # sits on the bed
    assert tm.bounds[1][2] == pytest.approx(L.height, abs=0.05)
    if kw["shape"] == "cylinder":
        d = tm.bounds[1][0] - tm.bounds[0][0]
        assert d == pytest.approx(60 / math.pi, abs=0.3)


def test_picture_keeps_its_aspect_and_frame(photo):
    L = Lithophane(photo, width=100, res=0.5, border=3)
    l, r, b, t = L.pad
    assert (L.nx - l - r) / (L.ny - b - t) == pytest.approx(4 / 3, rel=0.03)
    assert L.t[0, L.nx // 2] == pytest.approx(L.frame_t)          # bottom band
    assert L.t[-1, L.nx // 2] == pytest.approx(L.frame_t)         # top of the chamfered band
    # the top band never steps up faster than 1:1.2 going upward (printable underside)
    col = L.t[:, L.nx // 2]
    assert np.max(np.diff(col[L.ny - t - 1:])) <= L.res / 1.2 + 1e-6


def test_printable_relief_removes_sub_nozzle_ridges():
    a = np.zeros((12, 12))
    a[5, :] = 2.0              # 1 cell ridge: narrower than the nozzle
    a[:, 7:9] = 3.0            # 2 cell ridge: printable
    b = printable_relief(a, 2)
    assert b[5, 2] == 0.0
    assert np.all(b[:, 7:9] == 3.0)


def test_mirror_flips_left_right(photo):
    A = Lithophane(photo, width=40, res=0.5, border=0, sharpen=0, levels=0)
    B = Lithophane(photo, width=40, res=0.5, border=0, sharpen=0, levels=0, mirror=True)
    assert np.allclose(A.target, B.target[:, ::-1], atol=0.02)


def test_fit_transmittance_recovers_tau(tmp_path):
    steps = (0.6, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4)
    tau = 0.45
    lin = np.repeat([[0.9 * tau ** (t - 0.6) for t in steps]], 40, axis=0).repeat(30, axis=1)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    path = tmp_path / "wedge.png"
    Image.fromarray((srgb * 255).round().astype(np.uint8)).convert("RGB").save(path)
    got, vals, fit, ok = fit_transmittance(path, steps)
    assert got == pytest.approx(tau, abs=0.01)
    assert ok.all()


def test_soft_detail_keeps_fine_features_open_removes_them(photo):
    """A 1-cell dark line (an eye on a small face) survives detail="soft" (rounded off)
    but is flattened by the grey opening of detail="open"."""
    base = dict(width=40, res=0.5, border=0, sharpen=0, levels=0, nozzle=1.0)
    O = Lithophane(photo, detail="open", **base)
    S = Lithophane(photo, detail="soft", **base)
    t = np.full((20, 20), O.min_t)           # white background
    t[:, 10] = O.max_t                       # one-cell dark ridge, narrower than the nozzle
    from cadkit.lithophane import printable_relief, _gauss
    opened = printable_relief(t, 2)
    soft = _gauss(t, S.nozzle / 4 / S.res)
    assert (opened[:, 10] - opened[:, 8]).max() < 0.05
    assert (soft[:, 10] - soft[:, 8]).min() > 0.5
    with pytest.raises(ValueError):
        Lithophane(photo, width=40, res=0.5, detail="bogus")
