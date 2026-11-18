"""Starter slice of ash10's Fantasy RPG Pack: a furnished cottage in a forest clearing.

The environment half of the free starter slice (docs/game-asset-packs/fantasy-rpg-pack-plan.md,
section 11 step 2): one cottage with an interior, a clearing with a path to its door, the first
inventory items lying where they would be found, and three footstep families. No hero, monster
or dungeon yet, and nothing skinned is placed: the world kit of Cinder 0.1.1 draws no skinned
model.

It is judged the way the style test is: from the clearing (third person), from inside at eye
height (first person), and from above with the roof hidden (top-down).
"""
TITLE = "Fantasy RPG Pack: starter slice (cottage and clearing)"
DESCRIPTION = "a furnished cottage in a forest clearing, with items and footsteps: the environment half of the starter slice"
COLLECTION = ("frp_village", "frp_wilderness", "frp_interiors", "frp_items", "frp_weapons", "frp_interface", "frp_sounds")
LICENCE = "ash10 Fantasy RPG Pack licence (text pending)"
LEFT_OUT = {"nat_boulder_mossy": "uses two generated surfaces (frp_granite, frp_moss) that no person has cleared",
            "sfx_creature_growl_01": "a generated recording (frp_growl_01) that no person has cleared"}
DEMO = dict(seconds=2)
SHOTS = [dict(name="clearing", position=(4.2, 2.3, 14.0), target=(0.6, 1.9, 1.5), fov=50),
         dict(name="first_person", position=(-1.0, 1.6, 1.45), target=(0.9, 0.85, -0.7), fov=70),
         dict(name="hearth", position=(-0.9, 1.6, 0.9), target=(1.2, 0.7, -1.5), fov=55),
         dict(name="top_down", position=(0.3, 15.0, 3.2), target=(0.0, 0.0, 0.3), fov=40, hide=["roof_", "gable_"])]

FLOOR = 0.02                     # a ground floor sits 20 mm above the ground: never two surfaces in one plane
TABLE = FLOOR + 0.75


def demo(w):
    # late afternoon: a low warm sun and a cool, dim sky, so forms are modelled by light and shadow
    # (an even grey light flattens everything and no texture can rescue it)
    w.environment(zenith=(0.13, 0.20, 0.40), ground=(0.34, 0.24, 0.17), sun_intensity=0.6, ambient=0.65, exposure=1.1)
    w.add("low_sun", light=dict(kind="sun", direction=(-0.6, -0.5, -0.62), color=(1.0, 0.78, 0.55), intensity=3.4, shadows=True))
    # one round piece of ground with a bank at its rim, and a ring of forest standing on the bank:
    # the world ends in trees, not in a cut edge against the sky (and costs 3 samplers, not 36)
    w.place("nat_ground_clearing", (0, 0, 2), name="ground")
    w.place("nat_treeline", (0, 0, 2), name="forest")

    # ---- the cottage: four cells, walls on the lines x = +-2 and z = +-2, door in the south wall
    for x in (-1, 1):
        for z in (-1, 1):
            w.place("vil_floor", (x, FLOOR, z), name=f"floor_{x}_{z}")
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
    w.place("vil_door", (-1.58, 0, 2), yaw=-72, name="door")
    for x in (-1, 1):
        w.place("vil_roof_slope", (x, 0, -2), name=f"roof_n_{x}")
        w.place("vil_roof_slope", (x, 0, 2), yaw=180, name=f"roof_s_{x}")
    for x in (-2, 2):
        w.place("vil_gable", (x, 0, 0), yaw=90, name=f"gable_{x}")
    w.place("vil_chimney", (0.95, 0, -2.15), name="roof_chimney")       # outside the north wall, behind the hearth

    # ---- inside: hearth on the north wall, bed on the west, table and seats, a shelf on the east
    w.place("int_hearth", (0.95, FLOOR, -1.84), name="hearth")
    w.add("hearth_light", transform=dict(position=(0.95, FLOOR + 1.0, -0.55)),
          light=dict(kind="point", color=(1.0, 0.55, 0.22), intensity=38, range=7))
    w.place("int_bed_straw", (-1.33, FLOOR, -0.8), name="bed")
    w.place("int_table", (0.7, FLOOR, 0.62), name="table")
    w.place("int_bench", (0.7, FLOOR, 0.02), name="bench")
    w.place("int_stool", (0.45, FLOOR, 1.38), name="stool_table")
    w.place("int_stool", (-0.35, FLOOR, -0.95), yaw=40, name="stool_hearth")
    w.place("int_shelf", (1.67, FLOOR, -0.42), yaw=-90, name="shelf")
    # on the table
    w.place("itm_bread", (0.55, TABLE, 0.62), name="bread")
    w.place("itm_cheese", (0.9, TABLE, 0.45), yaw=25, name="cheese")
    w.place("itm_tankard", (1.05, TABLE, 0.8), yaw=200, name="tankard")
    w.place("itm_key_iron", (1.2, TABLE, 0.5), yaw=-30, name="key")
    w.place("itm_candle", (0.22, TABLE, 0.45), name="candle")
    w.add("candle_light", transform=dict(position=(0.22, TABLE + 0.2, 0.45)),
          light=dict(kind="point", color=(1.0, 0.6, 0.25), intensity=6, range=3))
    # on the shelf (its tops are 0.13, 0.55, 0.97 and 1.39 m above the floor)
    w.place("itm_health_potion", (1.66, FLOOR + 0.97, -0.62), name="potion_health")
    w.place("itm_mana_potion", (1.66, FLOOR + 0.97, -0.42), name="potion_mana")
    w.place("itm_coin_pouch", (1.66, FLOOR + 0.55, -0.25), name="pouch")
    w.place("itm_scroll", (1.66, FLOOR + 1.39, -0.4), yaw=80, name="scroll")
    w.place("wpn_longsword_iron", (-0.35, FLOOR, -1.72), name="sword")

    # ---- the clearing: a path from the door, trees round the edge, stones, undergrowth
    for i, z in enumerate((3, 5, 7, 9, 11)):
        w.place("nat_path", (-1, 0, z), name=f"path_{i}")
    w.place("nat_tree_autumn", (6.6, 0, 4.2), name="tree_east")
    w.place("nat_tree_autumn", (-5.6, 0, -4.2), yaw=140, name="tree_north_west")
    w.place("nat_tree_dead", (-5.2, 0, 7.6), yaw=60, name="tree_dead")
    w.place("nat_stump", (2.4, 0, 6.6), name="stump")
    w.place("nat_log", (3.4, 0, 9.0), yaw=30, name="log")
    w.place("nat_rock_cluster", (-3.6, 0, 4.4), yaw=20, name="rocks")
    w.place("nat_rock", (4.3, 0, 2.2), name="rock")
    for i, (x, z, yaw) in enumerate(((-3.6, -3.4, 0), (4.2, -3.8, 120), (6.2, 8.4, 250), (-6.4, 2.6, 70))):
        w.place("nat_bush", (x, 0, z), yaw=yaw, name=f"bush_{i}")
    for i, (x, z) in enumerate(((0.6, 3.4), (-2.4, 3.0), (1.6, 5.0), (-2.8, 6.4), (0.4, 7.6), (3.4, 3.8), (-4.4, 9.4), (5.0, 10.2),
                                (2.8, 2.6), (-2.3, 9.0))):
        w.place("nat_grass_clump", (x, 0, z), yaw=37 * i, name=f"grass_{i}")
    w.place("nat_leaf_litter", (6.2, 0, 4.6), name="litter_east")
    w.place("nat_leaf_litter", (4.2, 0, 6.4), yaw=140, name="litter_east_2")
    w.place("nat_leaf_litter", (-5.2, 0, -3.6), yaw=70, name="litter_north_west")
    w.place("nat_leaf_litter", (-0.6, 0, 3.2), yaw=200, name="litter_door")
    w.place("nat_mushrooms", (2.9, 0, 6.1), name="mushrooms_stump")
    w.place("nat_mushrooms", (3.0, 0, 9.5), yaw=160, name="mushrooms_log")
    # the ruler: a person-sized figure on the path
    w.add("figure", transform=dict(position=(-1.0, 0.9, 4.2)),
          shape=dict(kind="box", size=(0.45, 1.8, 0.25), color=(0.55, 0.27, 0.12), roughness=0.9))
