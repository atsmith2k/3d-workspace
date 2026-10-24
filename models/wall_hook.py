"""Wall hook for a 1/2 in dowel: a screw-on back plate with a round boss that the
dowel pushes into. Rated for ~2 kg hanging on a 150 mm dowel.

Spec:
  object:       wall-mounted holder for a 1/2 in (12.7 mm) wooden dowel, 2 kg load
  overall:      40 x 70 mm plate, 5 mm thick, boss 20 mm dia x 30 mm sticking out
  mates with:   1/2 in dowel, sliding fit: socket 13.3 mm (table) x 22 mm deep;
                two #8 wood screws, 4.4 mm clearance, 82 deg countersink
  orientation:  plate flat on the bed, boss pointing up; socket opens upward
                (it faces outward on the wall); no overhangs
  must have:    socket depth >= 20 mm, boss wall >= 3 mm, screws clear of the boss
  tolerances:   sliding fit on the dowel (0.2 mm/side + print allowance)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from build123d import *

from cadkit.checks import *
from cadkit.hardware import WOOD_SCREW, dowel_hole

DESCRIPTION = "Wall hook for a 1/2 in dowel, two #8 screws"

PARAMS = dict(
    plate_w=40.0,
    plate_h=70.0,
    plate_t=5.0,
    boss_len=30.0,      # how far the boss stands off the plate
    boss_wall=3.5,
    socket_depth=22.0,
    screw="#8",
    screw_spacing=50.0,
    corner=4.0,
    dowel="1/2",
)


def _dims(p):
    socket_d = dowel_hole(p.dowel, fit="sliding")
    boss_d = socket_d + 2 * p.boss_wall
    screw_d = WOOD_SCREW[p.screw][0] + 0.2
    return socket_d, boss_d, screw_d


def checks(p):
    socket_d, boss_d, screw_d = _dims(p)
    top = p.plate_t + p.boss_len
    return [
        dims(x=p.plate_w, y=p.plate_h, z=top),
        hole(socket_d, at=(0, 0), span=(top - p.socket_depth + 0.3, top - 0.3)),
        hole(screw_d, at=(0, p.screw_spacing / 2), span=(0.3, p.plate_t - 2.5),
             csk=WOOD_SCREW[p.screw][1] + 0.4, csk_from="top", csk_face=p.plate_t),
        hole(screw_d, at=(0, -p.screw_spacing / 2), span=(0.3, p.plate_t - 2.5),
             csk=WOOD_SCREW[p.screw][1] + 0.4, csk_from="top", csk_face=p.plate_t),
        solid((0, 0, p.plate_t + 1)),                               # boss is solid below the socket
        thickness_at((boss_d / 2 - 0.1, 0, top - 5), p.boss_wall - 0.2, direction=(1, 0, 0)),
        flat_base(p.plate_w * p.plate_h * 0.8),
        no_overhang(),
        single_body(),
    ]


def build(p):
    socket_d, boss_d, screw_d = _dims(p)
    plate = Box(p.plate_w, p.plate_h, p.plate_t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate = fillet(plate.edges().filter_by(Axis.Z), p.corner)
    boss = Cylinder(boss_d / 2, p.boss_len + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
        .moved(Location((0, 0, p.plate_t - 0.1)))
    part = plate + boss
    # fillet where the boss meets the plate (the edge at z = plate_t with the boss radius)
    try:
        part = fillet(part.edges().filter_by(GeomType.CIRCLE).filter_by(lambda e: abs(e.center().Z - p.plate_t) < 0.01), 2.0)
    except Exception:
        pass
    top = p.plate_t + p.boss_len
    part -= Cylinder(socket_d / 2, p.socket_depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
        .moved(Location((0, 0, top - p.socket_depth)))
    head_d = WOOD_SCREW[p.screw][1] + 0.4
    for y in (p.screw_spacing / 2, -p.screw_spacing / 2):
        part -= Cylinder(screw_d / 2, p.plate_t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((0, y, -1)))
        # 82 deg countersink: Cone(bottom_radius, top_radius, height): shank-sized at
        # the bottom, head-sized at the top face
        csk_depth = (head_d - screw_d) / 2 / 0.87
        part -= Cone(screw_d / 2, head_d / 2 + 0.01, csk_depth + 0.01, align=(Align.CENTER, Align.CENTER, Align.MAX)) \
            .moved(Location((0, y, p.plate_t + 0.01)))
    return part
