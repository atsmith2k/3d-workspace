"""Dungeon Kit: modular stone dungeon pieces on a 2 m grid, with props, a door, a pressure
plate, a pickup and a goal, and a demo world that plays through all of it.

Demo: two rooms divided by a wall with a doorway. The player collects a gem, steps on the
pressure plate (a second gem floats over it), which latches the door open, walks through,
takes the third gem and reaches the chest. The autopilot walks straight lines, so the route
runs down X=0 and the dressing stays off it.
"""
TITLE = "Dungeon Kit"
DESCRIPTION = ("A dungeon for Cinder: sixteen models (floor, walls, doorway, corner pier, pillar, stairs, "
               "door, pressure plate, wall torch, chest, gem, crate, barrel, lantern and a rigged adventurer), "
               "ten sound effects, a seamless music loop, a HUD and pause menu, and three sprite sheets")
COLLECTION = "dungeon_kit"
LICENCE = "CC0-1.0"
DEMO = dict(seconds=12, autopilot=True, expect_won=True, settle=dict(max_move=0.25))
SHOTS = [dict(name="hall", position=(1.0, 1.75, 0.3), target=(-0.3, 1.1, -5)),
         dict(name="vault", position=(-1.6, 1.7, -5.9), target=(0.8, 0.5, -8.4)),
         dict(name="props", position=(0.6, 1.5, -2.6), target=(-2.3, 0.6, -0.2))]

XS, ZS = (-2, 0, 2), (0, -2, -4, -6, -8)          # cell centres
WEST, EAST, SOUTH, NORTH, DIVIDER = -3, 3, 1, -9, -5


def demo(w):
    w.environment(zenith=(0.03, 0.04, 0.09), ground=(0.02, 0.02, 0.02), sun_intensity=0.2,
                  ambient=0.55, exposure=1.15)
    w.add("moon", light=dict(kind="sun", direction=(0.35, -1, -0.25), color=(0.55, 0.65, 1.0),
                             intensity=0.9, shadows=True))
    for x in XS:
        for z in ZS:
            w.place("dungeon_floor", (x, 0, z))
    # outer walls: south and north run along X, west and east along Z (turned 90)
    for x in XS:
        w.place("dungeon_wall", (x, 0, SOUTH))
    w.place("dungeon_wall", (0, 0, NORTH))
    w.place("dungeon_wall", (2, 0, NORTH))
    for x in (-2.5, -1.5):                        # two halves stand in for one full run
        w.place("dungeon_wall_half", (x, 0, NORTH))
    for z in ZS:
        w.place("dungeon_wall", (WEST, 0, z), yaw=90)
        w.place("dungeon_wall", (EAST, 0, z), yaw=90)
    # the divider: wall, doorway, wall
    w.place("dungeon_wall", (-2, 0, DIVIDER))
    w.place("dungeon_wall", (2, 0, DIVIDER))
    w.place("dungeon_doorway", (0, 0, DIVIDER))
    for x in (WEST, EAST):
        for z in (SOUTH, DIVIDER, NORTH):
            w.place("dungeon_corner", (x, 0, z))
    # the mechanism
    w.place("pressure_plate", (0, 0, -3), name="plate", trigger=dict(shape="box", size=(1, 2, 1)))
    w.place("dungeon_door", (0, 0, DIVIDER), name="gate",
            door=dict(triggers=["plate"], mode="latch", move=(1.25, 0, 0), speed=1.5))
    for i, z in enumerate((-1, -3, -7)):
        w.place("gem", (0, 0, z), name=f"gem_{i + 1}", spin=dict(speed=120), pickup=dict(radius=1, points=10))
    w.place("treasure_chest", (0, 0, -8.2), yaw=180, goal=dict(radius=1.5, requires_pickups=True))
    # dressing, off the route down X=0
    for x in (-1.7, 1.7):
        w.place("dungeon_pillar", (x, 0, -2))
    w.place("dungeon_stairs", (2, 0, -8))
    w.place("wooden_crate", (-2.2, 0, -0.1), yaw=12)
    w.place("wooden_crate", (-2.15, 0.8, -0.15), yaw=-20)
    w.place("wooden_crate", (-2.2, 0, -3.9), yaw=40)
    w.place("oak_barrel", (2.3, 0, -0.2))
    w.place("oak_barrel", (-2.3, 0, -6.0))
    w.place("iron_lantern", (2.3, 0.87, -0.2), body=False)
    w.add("lantern_light", transform=dict(position=(2.3, 1.1, -0.2)),
          light=dict(kind="point", color=(1.0, 0.6, 0.3), intensity=25, range=5))
    # torches hang toward -Z; turn them to face into the room, with a light in front of each
    for i, z in enumerate((-2, -7)):
        for side, x, yaw in (("w", WEST + 0.2, -90), ("e", EAST - 0.2, 90)):
            w.place("wall_torch", (x, 0, z), yaw=yaw, name=f"torch_{side}{i + 1}")
            w.add(f"torch_light_{side}{i + 1}", transform=dict(position=(x * 0.86, 2.15, z)),
                  light=dict(kind="point", color=(1.0, 0.55, 0.22), intensity=70, range=9))
    w.add("hero", transform=dict(position=(0, 0.1, 0.2)), player=dict(speed=4, jump=5))
