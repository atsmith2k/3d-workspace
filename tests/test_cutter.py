from types import SimpleNamespace

from cadkit.cutter import CUTTER_PARAMS, Art, cutter_set
from cadkit.relief import circle


def test_hole_narrower_than_its_blade_still_builds():
    # at 20 mm the 1 mm hole is thinner than two inner-blade walls, so the blade's
    # hollow is empty; the cutter must come out as a solid punch, not an invalid mesh
    art = Art(outline=circle(0, 0, 10), cutouts=[circle(0, 0, 0.5)], bars_x=[0])
    p = SimpleNamespace(**dict(CUTTER_PARAMS, sizes=(20.0,)))
    parts = cutter_set(art, p)
    assert parts["cutter_20"].volume() > 0
    assert parts["cutter_20"].num_vert() > 0
