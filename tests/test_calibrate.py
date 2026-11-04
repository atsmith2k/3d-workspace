"""cad stitch calibrate on synthetic photos: the built calibration card file (Ink/Stitch
when installed, else the native engine), displaced by a KNOWN pull profile
(fabrics.predict), rendered as dark thread on light fabric, then rotated, put in mild
perspective, unevenly lit, blurred and noised. measure + fit must recover the profile
against the zero-pull baseline of the same file."""
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFilter

from cadkit.stitch import calibrate as CAL
from cadkit.stitch import cli, engines
from cadkit.stitch import fabrics as F
from cadkit.stitch import pattern as P

from conftest import ROOT

TRUE = dict(name="synthetic", pull_fill=0.33,
            pull_satin=[(1.0, 0.12), (2.0, 0.20), (4.0, 0.30), (6.0, 0.31)])
THREAD = 0.45
PHOTO_RES = 13    # px/mm the card lands at in the "photo"
TOL = 0.02


def _render(plan, erase=()):
    return CAL.render_plan(plan, PHOTO_RES, THREAD, erase=erase)


def _perspective_coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output (dst) points to input (src)."""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float))


def _photo(card_img, path, angle=7.0, seed=1):
    rng = np.random.default_rng(seed)
    W, H = 2000, 2000
    n = card_img.size[0]
    src = np.array([(0, 0), (n, 0), (n, n), (0, n)], float)
    c = src - n / 2
    a = np.radians(angle)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    dst = c @ R.T + (W / 2, H / 2)
    # mild perspective: the far edge a little narrower
    dst[:2, 0] += np.array([25, -25])
    dst[:2, 1] += 12
    dst += rng.normal(0, 3, dst.shape)
    out = card_img.transform((W, H), Image.PERSPECTIVE, tuple(_perspective_coeffs(dst, src)),
                             Image.BICUBIC, fillcolor=232)
    out = out.filter(ImageFilter.GaussianBlur(1.0))
    g = np.asarray(out, float)
    yy, xx = np.mgrid[0:H, 0:W]
    light = 0.78 + 0.25 * xx / W + 0.05 * np.sin(yy / H * 3)       # uneven lighting
    g = g * light + rng.normal(0, 3, g.shape)
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).save(path, quality=92)
    return path


@pytest.fixture(scope="module")
def card():
    return CAL.load_card(ROOT / "designs" / "calibration_card.py")


@pytest.fixture(scope="module")
def card_pes(tmp_path_factory):
    """The card built the way the user builds it (cad stitch build), into a temp dir."""
    out = tmp_path_factory.mktemp("card")
    engine = "inkstitch" if engines.find_inkstitch() else "native"
    args = SimpleNamespace(model=str(ROOT / "designs" / "calibration_card.py"), set=[], name=None,
                           out=str(out), engine=engine, hoop=None, formats="pes",
                           no_render=True, compare=False)
    assert cli.cmd_build(args) == 0
    return out / "calibration_card" / "calibration_card.pes"


@pytest.fixture(scope="module")
def plan(card_pes):
    return F.predict(P.plan_of(P.read(str(card_pes))), TRUE)


def test_recovers_known_pull(card, card_pes, plan, tmp_path):
    photo = _photo(_render(plan), tmp_path / "card.jpg")
    m = CAL.measure(photo, card, card_pes)
    r = CAL.fit(m)
    assert abs(m["thread_mm"] - THREAD) < 0.06, m["gauges"]
    assert m["card_pes_sha256"] == CAL._sha256(card_pes)
    assert abs(r["pull_fill"] - TRUE["pull_fill"]) <= TOL, r
    for w, p in r["pull_satin"]:
        # displace pulls by the stitch length (= width + a 0.2 mm advance), interpolated
        want = F.satin_pull(TRUE, np.hypot(w, 0.2))
        assert abs(p - want) <= TOL, (w, p, want, r)
    assert r["residual_mm"] < 0.05
    assert r["n"] == 4 + 10


def test_rotated_further_still_reads(card, card_pes, plan, tmp_path):
    photo = _photo(_render(plan), tmp_path / "card.png", angle=-130.0, seed=3)
    r = CAL.fit(CAL.measure(photo, card, card_pes))
    assert abs(r["pull_fill"] - TRUE["pull_fill"]) <= TOL, r


def test_refuses_photo_without_fiducials(card, card_pes, plan, tmp_path):
    # plain fabric with a few dark blobs
    im = Image.new("L", (1200, 1000), 225)
    dr = ImageDraw.Draw(im)
    for x, y, s in ((200, 200, 60), (700, 300, 90), (400, 700, 40)):
        dr.ellipse([x, y, x + s, y + s], fill=30)
    im.save(tmp_path / "blank.png")
    with pytest.raises(CAL.CalibrationError, match="not found"):
        CAL.measure(tmp_path / "blank.png", card, card_pes)
    # the card with one corner square missing
    f = card.LAYOUT["fid_br"]["bbox"]
    photo = _photo(_render(plan, erase=[(f[0] - 1, f[1] - 1, f[2] + 1, f[3] + 1)]),
                   tmp_path / "corner.png")
    with pytest.raises(CAL.CalibrationError):
        CAL.measure(photo, card, card_pes)


def test_refuses_without_card_file(card, plan, tmp_path):
    photo = _photo(_render(plan), tmp_path / "card.png")
    with pytest.raises(CAL.CalibrationError, match="build the card first"):
        CAL.measure(photo, card, tmp_path / "missing.pes")


def test_cli_dry_run(card, card_pes, plan, tmp_path, capsys):
    import argparse
    photo = _photo(_render(plan), tmp_path / "card.jpg", seed=5)
    p = CAL.add_arguments(argparse.ArgumentParser())
    args = p.parse_args([str(photo), "--fabric", "knit", "--machine", "Test", "--stabiliser",
                         "cut-away", "--dry-run", "--out", str(tmp_path),
                         "--card-pes", str(card_pes)])
    assert CAL.cmd_calibrate(args) == 0
    out = capsys.readouterr().out
    assert "pull_fill" in out and "dry run" in out
    assert CAL._sha256(card_pes) in out
    assert (tmp_path / "card_rectified.png").exists()
