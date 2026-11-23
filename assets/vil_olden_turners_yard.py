"""Turner's Yard, an outdoor pole-lathe workshop on four concentric terraces.

Spec:
    The floor spans 40 by 36 m with 0.12 m steps. Eight turning benches
    fit the authored collision boxes and leave the center approach open.
    Opaque PBR maps fit 512 px and the mesh fits 30000 triangles.
"""

from _frp import custom, materials, size, texture_size, tris
from _olden_ladder_workyards import fixture_bounds, TURNERS_FIXTURES, TURNERS_FLOORS, turners_yard

KIND = "environment"
DESCRIPTION = "Dressed concentric terraces with timber sheds and turning benches"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=30000, materials=8, texture=512)
PRODUCT = dict(collection="olden_times", gameplay=dict(
    map_id="turners_yard",
    floor_patches=TURNERS_FLOORS,
    obstacle_boxes=TURNERS_FIXTURES,
    visual_only=True,
))


def build(p):
    return turners_yard()


def checks(p):
    def terraces(ctx):
        expected = [(0, .36), (7, .24), (12, .12), (16, 0)]
        bounds = [part.bounds for part in ctx.model.walkable]
        for (edge, height), (low, high) in zip(reversed(expected), bounds):
            if abs(high[1] - height) > .002 or high[0] < edge:
                return False, f"Incorrect terrace at {height:g} m"
        center_is_clear = not any(
            low[0] <= .70 and high[0] >= -.70 and low[1] < 2.6
            and low[2] <= 9 and high[2] >= -9
            for low, high in ctx.model.obstacles
        )
        return center_is_clear, "Four authoritative floor levels and a clear 1.4 m central passage"

    def collision(ctx):
        return fixture_bounds(ctx.model, TURNERS_FIXTURES, 20, 18)

    return [size(x=40, y=(3.9, 4.3), z=36, tol=.002), tris(max=30000),
            materials(8), texture_size(512), custom("dressing versus collision", collision), custom("terrace heights and clear center", terraces)]
