"""Two-part electronics enclosure: an open box with four M3 heat-set bosses and a lid
with an inner lip, screwed down from the top with countersunk M3 screws. Built from
cadkit.recipes; the lid prints upside down (top face on the bed) and `assembly()`
tells the build how it sits on the box so the fit check can measure the lip clearance.

Spec:
  object:       project box, lid on top
  overall:      width x depth x height outside, wall 2 mm, lid 3 mm
  mates with:   M3 heat-set inserts in the bosses, M3 countersunk screws through the lid
  orientation:  box open side up; lid flipped (top face on bed); no supports
  must have:    lip clearance 0.2 mm per side, boss height = inside height, holes align
  tolerances:   lip 0.2 mm/side sliding fit; holes from the hardware table

Units: mm. Z is up, both parts sit on z=0 in print pose.
"""
from cadkit.checks import *
from cadkit.hardware import clearance, head_pocket
from cadkit.recipes import *

DESCRIPTION = "Project box with M3 insert bosses and a countersunk, lipped lid (recipes demo)"

PARAMS = dict(
    width=80.0,
    depth=50.0,
    height=30.0,       # box outside height, without the lid
    wall=2.0,
    lid_t=3.0,
    lip_h=4.0,
    corner=4.0,
    screw="M3",
)


def _bosses(p):
    # inset past the wall AND the lid's lip (another wall thickness + clearance)
    from cadkit.hardware import insert
    inset = 2 * p.wall + 0.2 + insert(p.screw)["boss"] / 2 + 0.3
    return boss_corners(p.width, p.depth, p.wall, p.screw, inset=inset)


def checks(p):
    pts = _bosses(p)
    return {
        "base": [dims(x=p.width, y=p.depth, z=p.height), flat_base(p.width * p.depth * 0.8),
                 no_overhang(), single_body(),
                 solid((pts[0][0] + 3.0, pts[0][1], p.height - 1)),           # boss wall reaches the top
                 empty((0, 0, p.height / 2))],                                 # box is open inside
        "lid": [dims(x=p.width, y=p.depth, z=p.lid_t + p.lip_h), no_overhang(), single_body(),
                *[hole(clearance(p.screw), at=pt, span=(head_pocket(p.screw, "csk")[0] / 2 - 1.0, p.lid_t - 0.3),
                       csk=head_pocket(p.screw, "csk")[0], csk_from="bottom") for pt in pts]],
    }


def assembly(p):
    """Print pose -> assembled pose per part: (dx, dy, dz, rx, ry, rz), rotation about
    the part's own origin in degrees applied first. The lid flips over onto the box."""
    return {"lid": (0, 0, p.height + p.lid_t, 180, 0, 0)}


def build(p):
    pts = _bosses(p)
    base = shell_box(p.width, p.depth, p.height, wall=p.wall, r=p.corner)
    base = add_bosses(base, p.screw, pts, height=p.height, floor=p.wall)
    top = lid(p.width, p.depth, p.lid_t, r=p.corner, lip_h=p.lip_h, wall=p.wall)
    top = screw_holes(top, p.screw, pts, csk=True, from_top=False)
    return {"base": base, "lid": top}
