"""Style test for ash10's Fantasy RPG Pack: one timber-framed hut on open ground, seen the three
ways the pack must work: from the street (third person), from inside at eye height (first
person), and from above with the roof hidden (top-down).

It is not a product. It is the scene the style guide is judged by: the ruler (a 1.8 m figure
by a 1.2 x 2.2 m doorway under a 3 m storey), the palette and materials (stained plaster, dark
timber, old thatch, dying grass), and the building grammar (walls on cell edges, a post on
every corner, a roof of separate pieces). Every dynamic rule of a real pack still applies:
each member must be ready, and the scene must load every model with no GPU errors.
"""
TITLE = "Fantasy RPG Pack: style test"
DESCRIPTION = "the pack's ruler, palette, materials and building grammar in one small scene"
COLLECTION = ("frp_village", "frp_wilderness", "frp_weapons", "frp_items", "frp_interface")
LICENCE = "ash10 Fantasy RPG Pack licence (text pending)"
LEFT_OUT = {"nat_boulder_mossy": "uses two generated surfaces (frp_granite, frp_moss) that no person has cleared"}
DEMO = dict(seconds=2)
SHOTS = [dict(name="third_person", position=(6.5, 2.6, 8.0), target=(-0.3, 1.6, 0.5), fov=45),
         dict(name="first_person", position=(1.1, 1.6, -1.3), target=(-1.3, 1.25, 2.0), fov=70),
         dict(name="top_down", position=(0.3, 15.0, 3.2), target=(0.0, 0.0, 0.3), fov=40, hide=["roof_", "gable_"])]

G = 2.0


def demo(w):
    w.environment(zenith=(0.16, 0.19, 0.27), ground=(0.07, 0.07, 0.07), sun_intensity=0.6, ambient=0.75, exposure=1.15)
    w.add("low_sun", light=dict(kind="sun", direction=(-0.55, -0.6, -0.6), color=(1.0, 0.82, 0.62), intensity=2.4, shadows=True))
    # open ground: four 8 m tiles (a world holds about 250 textures counting every copy, so ground is
    # laid large), two 2 m tiles to show they meet, and a bank of slope tiles along the north edge
    for i, (x, z) in enumerate(((-4, 0), (4, 0), (-4, 8), (4, 8))):
        w.place("nat_ground_8m", (x, 0, z), name=f"ground_{i}")
    for ix in range(-3, 3):
        w.place("nat_ground_slope", (ix * G + 1, 0, -5), name=f"bank_{ix + 3}")
    w.place("nat_ground", (-7, 1.0, -7), name="upper_ground_a")
    w.place("nat_ground", (-5, 1.0, -7), name="upper_ground_b")
    # the hut: four cells, walls on the lines x = +-2 and z = +-2
    for x in (-1, 1):
        for z in (-1, 1):
            w.place("vil_floor", (x, 0.02, z), name=f"floor_{x}_{z}")     # 20 mm proud of the ground
    w.place("vil_wall_door", (-1, 0, 2), name="wall_s_door")
    w.place("vil_wall_window", (1, 0, 2), name="wall_s_window")
    w.place("vil_wall", (-1, 0, -2), name="wall_n_1")
    w.place("vil_wall", (1, 0, -2), name="wall_n_2")
    w.place("vil_wall", (-2, 0, -1), yaw=90, name="wall_w_1")
    w.place("vil_wall_window", (-2, 0, 1), yaw=90, name="wall_w_window")
    w.place("vil_wall", (2, 0, -1), yaw=90, name="wall_e_1")
    w.place("vil_wall", (2, 0, 1), yaw=90, name="wall_e_2")
    for x in (-2, 2):
        for z in (-2, 2):
            w.place("vil_corner", (x, 0, z), name=f"corner_{x}_{z}")
    w.place("vil_door", (-1.58, 0, 2), yaw=-72, name="door")              # hinged at the left jamb, standing ajar
    # the roof: separate entities, so a top-down view can leave them out
    for x in (-1, 1):
        w.place("vil_roof_slope", (x, 0, -2), name=f"roof_n_{x}")
        w.place("vil_roof_slope", (x, 0, 2), yaw=180, name=f"roof_s_{x}")
    for x in (-2, 2):
        w.place("vil_gable", (x, 0, 0), yaw=90, name=f"gable_{x}")
    # inside: a draught on the floor by the wall, a sword stood in the corner, a hearth-coloured light
    w.place("itm_health_potion", (-1.2, 0, -1.5), name="potion")
    w.place("wpn_longsword_iron", (1.55, 0, -1.6), name="sword")
    w.add("hearth_light", transform=dict(position=(0.4, 1.4, -0.6)),
          light=dict(kind="point", color=(1.0, 0.55, 0.22), intensity=45, range=7))
    # the ruler: a person-sized figure by the door
    w.add("figure", transform=dict(position=(0.4, 0.9, 3.4)),
          shape=dict(kind="box", size=(0.45, 1.8, 0.25), color=(0.55, 0.27, 0.12), roughness=0.9))
