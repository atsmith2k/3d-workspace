"""Fabric profiles: how much a fabric pulls in under the thread, the compensation the
stitches get for it, and a model that predicts where the stitches end up once sewn.

Thread tension draws the fabric in along the stitch direction: a satin column comes
out narrower than drawn, fill rows come out shorter, and an outline sewn after a fill
can part from it. Digitising software compensates by sewing each stitch a little
longer (pull compensation) by an amount that depends on the fabric. A profile holds
that amount per object class:

    pull_fill     mm each fill row end pulls back along the row
    pull_satin    [(column width mm, pull mm per side), ...], interpolated (narrow
                  columns pull less in absolute terms)

The starting values are Wilcom's published auto-fabric guidelines (drill/woven 0.20,
T-shirt 0.35, fleece 0.40, lettering 0.2-0.3 mm). A sewn calibration card measured by
`cad stitch calibrate` replaces them with numbers for one machine, fabric and
stabiliser: cadkit/stitch/profiles/<fabric>.json, which `profile()` merges in and
whose provenance travels into every build report and product manifest.

    d.fabric = "knit"            # or FABRIC = "knit" in the design module
    apply(design, profile("knit"))   # done by the build: compensation per element
    predict(plan, profile("knit"))   # the plan as it will sit on the fabric
"""
import json
from datetime import date
from pathlib import Path

import numpy as np

PROFILE_DIR = Path(__file__).with_name("profiles")

# fabric -> profile. `stabiliser` and `topper` go into the buyer notes.
PROFILES = {
    "woven": dict(label="wovens (cotton, drill, canvas)", stabiliser="tear-away",
                  pull_fill=0.20, pull_satin=[(1.0, 0.10), (2.0, 0.15), (4.0, 0.20), (7.0, 0.20)]),
    "twill": dict(label="twill, caps and patch blanks", stabiliser="tear-away (cut-away on caps)",
                  pull_fill=0.25, pull_satin=[(1.0, 0.12), (2.0, 0.18), (4.0, 0.25), (7.0, 0.25)]),
    "apparel": dict(label="knits and wovens (t-shirts, sweatshirts, totes)",
                    stabiliser="cut-away on knits, tear-away on wovens",
                    pull_fill=0.30, pull_satin=[(1.0, 0.12), (2.0, 0.20), (4.0, 0.30), (7.0, 0.30)]),
    "knit": dict(label="knits (t-shirts, polos)", stabiliser="cut-away",
                 pull_fill=0.35, pull_satin=[(1.0, 0.15), (2.0, 0.22), (4.0, 0.35), (7.0, 0.35)]),
    "fleece": dict(label="fleece and jumpers", stabiliser="cut-away + water-soluble topper",
                   pull_fill=0.40, pull_satin=[(1.0, 0.15), (2.0, 0.25), (4.0, 0.40), (7.0, 0.40)]),
    "towel": dict(label="towels and terry", stabiliser="tear-away + water-soluble topper",
                  pull_fill=0.40, pull_satin=[(1.0, 0.15), (2.0, 0.25), (4.0, 0.40), (7.0, 0.40)]),
}
DEFAULT = "apparel"
SOURCE = "Wilcom EmbroideryStudio auto-fabric guidelines (uncalibrated)"


def names():
    return sorted(PROFILES)


def profile(name=None):
    """The named profile (DEFAULT when None), with a calibration merged in when
    cadkit/stitch/profiles/<name>.json exists. Adds `name`, `calibrated`, `source`."""
    name = name or DEFAULT
    if name not in PROFILES:
        raise ValueError(f"unknown fabric '{name}'; known: {', '.join(names())}")
    p = dict(PROFILES[name], name=name, calibrated=False, source=SOURCE)
    f = PROFILE_DIR / f"{name}.json"
    if f.exists():
        cal = json.loads(f.read_text(encoding="utf-8"))
        p.update({k: cal[k] for k in ("pull_fill", "pull_satin") if k in cal})
        p.update(calibrated=True, source=calibration_source(cal), calibration=cal)
    p["pull_satin"] = [tuple(map(float, wp)) for wp in p["pull_satin"]]
    return p


def calibration_source(cal):
    bits = [cal.get("machine"), cal.get("fabric_detail") or cal.get("profile"),
            cal.get("stabiliser"), cal.get("date")]
    if cal.get("card_version") is not None:
        bits.append(f"card v{cal['card_version']}")
    if cal.get("residual_mm") is not None:
        bits.append(f"residual {cal['residual_mm']:.2f} mm")
    return "calibrated: " + ", ".join(str(b) for b in bits if b)


def save_calibration(name, values):
    """Write a calibration for profile `name` (values from `cad stitch calibrate`)."""
    PROFILE_DIR.mkdir(exist_ok=True)
    values = dict(values, profile=name)
    values.setdefault("date", date.today().isoformat())
    path = PROFILE_DIR / f"{name}.json"
    path.write_text(json.dumps(values, indent=2) + "\n", encoding="utf-8")
    return path


def satin_pull(prof, width):
    """Pull per side for a satin column `width` mm wide (stitch length ~ width)."""
    w, p = np.array(prof["pull_satin"]).T
    return float(np.interp(width, w, p))


# ------------------------------------------------------------------ compensation

def apply(design, prof):
    """Set each element's pull compensation from the profile, in place, unless the
    design set `pull=` on that element itself. Fills compensate along the row
    direction (svg/native stretch the shape), satins per side by column width."""
    for el in design.elements:
        if "pull" in getattr(el, "fixed", ()):
            continue
        if el.kind == "fill":
            el.params["pull"] = prof["pull_fill"]
        elif el.kind == "satin":
            w = el.params.get("width_body") if el.params.get("taper") else el.params["width"]
            el.params["pull"] = round(satin_pull(prof, w), 3)
    design.fabric = prof["name"]
    return design


def stretch(shape, angle, mm):
    """`shape` grown by `mm` at both ends of rows running at `angle` degrees: the
    Minkowski sum with a segment along the row direction (holes shrink the same way).
    This is how a fill gets pull compensation (Ink/Stitch 3.0 ignores
    pull_compensation_mm on fills)."""
    if not mm:
        return shape
    from shapely import affinity
    from shapely.ops import unary_union
    a = np.radians(angle)
    d = np.array([np.cos(a), np.sin(a)])
    n = max(2, int(np.ceil(2 * mm / 0.05)))
    out = unary_union([affinity.translate(shape, *(d * t)) for t in np.linspace(-mm, mm, n + 1)])
    return out.buffer(0)


# ------------------------------------------------------------------ prediction

def _pulls(prof, L):
    """Pull per stitch end for stitches of length L: satins by width, capped at the
    fill value for long stitches."""
    w, p = np.array(prof["pull_satin"]).T
    return np.interp(L, w, p)


def displace(points, prof, scale=1.0):
    """Where the penetrations of one continuous run land once the fabric pulls in.

    Tension pulls the ends of a sewn line together. Along a straight line the stitches
    either side of a point pull it both ways and cancel; at a turn-round they don't and
    the end moves back along its line. So the run is split into straight chains
    (stitches within 25 deg of each other) and every chain end that turns round into
    an opposite-running chain (directly, or across a connector under 1.2 mm: the step
    between fill rows) moves inward along its chain: a one-stitch chain is a satin
    stitch and moves by the profile's pull for that width, a longer chain is a fill
    row and moves by pull_fill. A point shared by two chain ends (a satin edge) takes
    the mean of the two. `scale` multiplies the effect (0 = no pull)."""
    P = np.asarray(points, float)
    n = len(P)
    if n < 3 or not scale:
        return P.copy()
    v = np.diff(P, axis=0)
    L = np.linalg.norm(v, axis=1)
    u = v / np.maximum(L, 1e-9)[:, None]
    # chains: [first stitch, last stitch] of each straight stretch
    chains, s0 = [], 0
    for k in range(1, len(v) + 1):
        if k == len(v) or L[k] < 1e-6 or u[k] @ u[k - 1] < np.cos(np.radians(25)):
            chains.append((s0, k - 1))
            s0 = k
    length = [float(L[a:b + 1].sum()) for a, b in chains]
    dirs = []
    for (a, b), ln in zip(chains, length):
        d = P[b + 1] - P[a]
        dirs.append(d / (np.linalg.norm(d) + 1e-9))

    def pull(c):
        a, b = chains[c]
        return _pulls(prof, length[c]) if a == b else prof["pull_fill"]

    def turns(c, step):
        """True when chain c meets an opposite-running chain at its end in `step`
        direction (+1 its end, -1 its start), directly or across a short connector."""
        j, gap = c + step, 0.0
        while 0 <= j < len(chains):
            if dirs[j] @ dirs[c] < -0.7 and length[j] >= 0.8:
                return True
            gap += length[j]
            if gap > 1.2:
                return False
            j += step
        return False

    acc = np.zeros_like(P)
    cnt = np.zeros(n)
    for c, (a, b) in enumerate(chains):
        if length[c] < 0.8:
            continue
        mag = min(pull(c), 0.45 * length[c]) * scale
        if turns(c, -1):
            acc[a] += dirs[c] * mag
            cnt[a] += 1
        if turns(c, +1):
            acc[b + 1] -= dirs[c] * mag
            cnt[b + 1] += 1
    hit = cnt > 0
    out = P.copy()
    out[hit] += acc[hit] / cnt[hit][:, None]
    return out


def predict(plan, prof, scale=1.0):
    """A copy of the StitchPlan with every run displaced as sewn on `prof`'s fabric."""
    from .pattern import StitchPlan
    runs = [(b, displace(r, prof, scale)) for b, r in plan.runs]
    return StitchPlan(runs, list(plan.jumps), list(plan.colors), plan.penetrations, plan.trims,
                      list(plan.names))
