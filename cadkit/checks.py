"""Acceptance checks a model script declares so `cad build` can confirm the geometry
matches the request, not just that the code ran.

In a model:

    from cadkit.checks import *

    CHECKS = [
        dims(x=120, y=120, z=(29, 31)),      # number = +-0.5 mm, tuple = (lo, hi)
        hole(6.4, at=(10, 10)),               # through hole along z at x=10, y=10
        hole(3.2, at=(0, 20), axis="y", span=(0, 8)),   # blind, 8 mm deep from y=0
        solid((0, 0, 2)), empty((0, 0, 20)),  # material where there should be, air elsewhere
        thickness_at((0, 0, 2.5), 5),         # floor at least 5 mm here
        flat_base(2000), no_overhang(), single_body(), wall_min(1.2), fits_bed(),
        custom("lid clears base", lambda c: c.tm.extents[0] < 50),
    ]

or, when the expected values depend on parameters:

    def checks(p):
        return [dims(z=p.floor + p.thickness), ...]

For a multi-part model (build returns a dict), CHECKS may be a dict of part name to
list; a plain list is applied to every part. Each check gets a context with
`tm` (the part's trimesh), `report` (the printability Report), `params` and `name`.
"""
import numpy as np

from . import measure as M

__all__ = ["dims", "volume", "hole", "solid", "empty", "thickness_at", "wall_min",
           "flat_base", "no_overhang", "single_body", "fits_bed", "custom", "run_checks"]


class Check:
    def __init__(self, name, fn):
        self.name, self.fn = name, fn

    def run(self, ctx):
        try:
            res = self.fn(ctx)
        except Exception as e:
            return False, f"{self.name}: error {type(e).__name__}: {e}"
        ok, detail = res if isinstance(res, tuple) else (bool(res), "")
        return bool(ok), f"{self.name}{': ' + detail if detail else ''}"


def _range(spec, tol):
    if isinstance(spec, (tuple, list)):
        return float(spec[0]), float(spec[1])
    return float(spec) - tol, float(spec) + tol


def dims(x=None, y=None, z=None, tol=0.5):
    """Overall size along each given axis: a number (+-tol) or a (lo, hi) range."""
    want = {k: v for k, v in dict(x=x, y=y, z=z).items() if v is not None}

    def fn(c):
        size = c.tm.extents
        bad, got = [], []
        for k, spec in want.items():
            lo, hi = _range(spec, tol)
            v = size[M.AXIS[k]]
            got.append(f"{k}={v:.1f}")
            if not lo <= v <= hi:
                bad.append(f"{k}={v:.1f} not in {lo:.1f}..{hi:.1f}")
        return (not bad), (", ".join(bad) if bad else " ".join(got))
    return Check("dims", fn)


def volume(lo, hi):
    """Volume in cm3 within [lo, hi]."""
    def fn(c):
        v = abs(c.tm.volume) / 1000
        return lo <= v <= hi, f"{v:.1f} cm3" + ("" if lo <= v <= hi else f" not in {lo}..{hi}")
    return Check("volume", fn)


def hole(d, at, axis="z", span=None, tol=0.2, csk=None, csk_from="top", csk_face=None):
    """A round hole of diameter `d` (+-tol) whose axis is parallel to `axis` and passes
    through `at` = the two other coordinates. `span` = (lo, hi) along the axis the hole
    must be clear over (default: the whole part, i.e. a through hole).
    `csk` = head diameter of a countersink or counterbore that must open at the
    `csk_from` ("top" or "bottom") end: the mouth is checked to be clear and the
    material just below the head depth to be solid, which catches an inverted cone.
    `csk_face` = the axis coordinate of that face when it is not the part's extreme
    (a plate with a boss standing on it)."""
    ax = M.AXIS[axis]
    others = [i for i in range(3) if i != ax]

    def fn(c):
        lo, hi, _ = M.extents(c.tm)
        z0, z1 = span if span else (lo[ax] + 0.3, hi[ax] - 0.3)
        hs = np.linspace(z0, z1, 7)
        angs = np.linspace(0, 2 * np.pi, 8, endpoint=False)

        def ring(r, heights=None):
            heights = hs if heights is None else heights
            pts = np.zeros((len(heights) * len(angs), 3))
            k = 0
            for h in heights:
                for a in angs:
                    pts[k, ax] = h
                    pts[k, others[0]] = at[0] + r * np.cos(a)
                    pts[k, others[1]] = at[1] + r * np.sin(a)
                    k += 1
            return pts
        if csk:
            face = csk_face if csk_face is not None else (hi[ax] if csk_from == "top" else lo[ax])
            sgn = -1 if csk_from == "top" else 1
            mouth = ring(csk / 2 - 0.6, [face + sgn * 0.3])
            if M.contains(c.tm, mouth).any():
                return False, (f"{csk:.1f} mm head opening at {at} is blocked at the {csk_from} face "
                               f"(countersink inverted or missing?)")
            below = ring(csk / 2 - 0.3, [face + sgn * ((csk - d) / 2 + 0.8)])
            if not M.contains(c.tm, below).all():
                return False, f"material missing under the {csk:.1f} mm head at {at}: pocket too deep or undercut"
        blocked = M.contains(c.tm, ring(max(d / 2 - tol, 0.1)))
        if blocked.any():
            mean_d, _ = M.hole_diameter(c.tm, at, axis, height=(z0 + z1) / 2)
            found = f"; a {mean_d:.2f} mm opening is there" if 0 < mean_d < d else ""
            return False, f"material inside the {d} mm hole at {at} ({blocked.mean() * 100:.0f}% of probes{found})"
        around = M.contains(c.tm, ring(d / 2 + tol + 0.3))
        if around.mean() < 0.5:
            return False, f"no wall around the {d} mm hole at {at}: hole too big or missing"
        mean_d, min_d = M.hole_diameter(c.tm, at, axis, height=(z0 + z1) / 2)
        ok = abs(mean_d - d) <= tol + 0.05
        return ok, f"{d} mm at {at}: measured {mean_d:.2f} mm" + ("" if ok else f" (wanted {d}+-{tol})")
    return Check("hole", fn)


def solid(*points):
    """Material at every point."""
    def fn(c):
        inside = M.contains(c.tm, points)
        missing = [tuple(points[i]) for i in np.flatnonzero(~inside)]
        return not missing, (f"no material at {missing}" if missing else f"{len(points)} points solid")
    return Check("solid", fn)


def empty(*points):
    """Air at every point."""
    def fn(c):
        inside = M.contains(c.tm, points)
        hit = [tuple(points[i]) for i in np.flatnonzero(inside)]
        return not hit, (f"material at {hit}" if hit else f"{len(points)} points empty")
    return Check("empty", fn)


def thickness_at(point, min_mm, direction=None, max_mm=None):
    """Material thickness at a point (inside or on the surface) at least `min_mm`."""
    def fn(c):
        t = M.thickness_at(c.tm, point, direction)
        ok = t >= min_mm and (max_mm is None or t <= max_mm)
        return ok, f"{t:.2f} mm at {tuple(point)}" + ("" if ok else f" (wanted >= {min_mm})")
    return Check("thickness", fn)


def wall_min(mm=1.2):
    """Thinnest ~1% of the surface is at least `mm` thick."""
    def fn(c):
        t = c.report.wall_thin_mm
        return t >= mm, f"thinnest ~{t:.1f} mm" + ("" if t >= mm else f" (wanted >= {mm})")
    return Check("wall_min", fn)


def flat_base(min_area_mm2=100):
    def fn(c):
        a = c.report.base_area_mm2
        return a >= min_area_mm2, f"{a:.0f} mm2 on the bed" + ("" if a >= min_area_mm2 else f" (wanted >= {min_area_mm2})")
    return Check("flat_base", fn)


def no_overhang(max_mm2=1.0):
    def fn(c):
        a = c.report.overhang_area_mm2
        return a <= max_mm2, f"{a:.0f} mm2 overhang"
    return Check("no_overhang", fn)


def single_body():
    def fn(c):
        return c.report.bodies == 1 and c.report.watertight, \
            f"{c.report.bodies} body, {'watertight' if c.report.watertight else 'NOT watertight'}"
    return Check("single_body", fn)


def fits_bed():
    def fn(c):
        bad = [w for w in c.report.warnings if "larger than" in w]
        return not bad, (bad[0] if bad else "fits")
    return Check("fits_bed", fn)


def custom(name, fn):
    """fn(ctx) -> bool or (bool, detail)."""
    return Check(name, fn)


def run_checks(checks, ctx):
    """Returns (all_ok, lines) with one 'check    PASS/FAIL name: detail' line each."""
    lines, ok = [], True
    for chk in checks or []:
        passed, text = chk.run(ctx)
        ok &= passed
        lines.append(f"check    {'PASS' if passed else 'FAIL'} {text}")
    return ok, lines
