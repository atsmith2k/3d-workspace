"""Sandbox Kit: the builder props the Hive asked for (thread 900b4a1e, suggestions by stanley):
six building blocks, a bounce pad, an explosive barrel, a coin, a checkpoint flag, a finish
gate, a spike trap, a moving platform, a tree and a robot character.

Demo: a small obstacle course on a green field, played by the autopilot. From the checkpoint
flag the player takes three coins down the middle and walks through the finish gate. Beside
the route: stacks of blocks dropped from just above the ground (they must settle), a ramp up
to a plate, a moving platform on a patrol, a spike trap working as a timed hazard, a bounce
pad with a crate dropped on it, explosive barrels and trees. The robot is not placed: the
world kit does not draw skinned models.
"""
TITLE = "Sandbox Kit"
DESCRIPTION = ("Builder props for the CinderCore sandbox: six building blocks on a 1 m / 2 m grid, bounce pad, "
               "explosive barrel, coin, checkpoint flag, finish gate, spike trap, moving platform, tree and "
               "a rigged robot, all on one shared 512 px atlas")
COLLECTION = "sandbox_kit"
LICENCE = "CC0-1.0"
DEMO = dict(seconds=14, autopilot=True, expect_won=True, settle=dict(max_move=0.25, free=["bouncer"]))
SHOTS = [dict(name="course", position=(5.5, 3.2, 5.5), target=(-0.5, 0.8, -6)),
         dict(name="blocks", position=(-1.5, 2.2, -1.0), target=(-6, 1.0, -5)),
         dict(name="hazards", position=(1.0, 2.0, -4.5), target=(6, 0.5, -9))]


def demo(w):
    w.environment(exposure=1.0, ambient=1.0)
    w.add("sun", light=dict(kind="sun", direction=(-0.4, -1, -0.5), intensity=3.2, shadows=True))
    w.add("field", transform=dict(position=(0, -0.5, -8)), shape=dict(kind="box", size=(40, 1, 44), color=(0.36, 0.55, 0.30),
                                                                        roughness=0.95), body=dict(motion="static"))
    # the route, down X=0 toward -Z
    w.place("checkpoint_flag", (-1.2, 0, 0.5))
    for i, z in enumerate((-3, -7, -11)):
        w.place("coin", (0, 0, z), name=f"coin_{i + 1}", spin=dict(speed=120), pickup=dict(radius=1, points=5))
    w.place("finish_gate", (0, 0, -15), goal=dict(radius=1.6, requires_pickups=True))
    # blocks, west of the route: every dynamic piece starts 2 cm up and must settle into a stack
    w.place("block_cube_2m", (-6, 0.02, -4))
    w.place("block_cube_1m", (-6.4, 2.04, -4.3))
    w.place("block_cube_1m", (-5.4, 2.04, -3.7), yaw=20)
    w.place("block_cylinder", (-3.6, 0.02, -4.2))
    w.place("block_cube_1m", (-3.6, 1.04, -4.2), yaw=45)
    w.place("block_plate", (-6, 0.02, -8.5))
    w.place("block_plate", (-6, 0.24, -8.5), yaw=90)
    w.place("block_beam", (-6, 0.46, -8.0))
    w.place("block_beam", (-6, 0.46, -9.0))
    w.place("block_ramp", (-3.4, 0, -8.5), yaw=90)                    # climbs toward -X, up to the plates
    # hazards and movers, east of the route
    w.place("spike_trap", (4, 0, -5), hazard=dict(radius=0.8, period=4, on=2))
    w.place("moving_platform", (5.5, 0.9, -9), patrol=dict(points=(3.5, 1.0, -9, 7.5, 1.0, -9), speed=1.5))
    w.place("bounce_pad", (4, 0, -12), body=False, name="bounce_pad")
    w.add("pad_body", transform=dict(position=(4, 0.125, -12)),
          shape=dict(kind="box", size=(1, 0.24, 1), color=(0.1, 0.1, 0.1)), body=dict(motion="static", restitution=0.95))
    w.place("block_cube_1m", (4, 2.5, -12), name="bouncer", body=False)
    w.entities[-1][1]["body"] = dict(motion="dynamic", collider="box", restitution=0.9)
    for i, (x, z) in enumerate(((6.5, -2.5), (7.3, -2.9), (6.9, -3.6))):
        w.place("explosive_barrel", (x, 0.02, z), yaw=40 * i)
    w.place("explosive_barrel", (6.9, 0.94, -3.0), yaw=15)
    for x, z in ((-9, -1), (9, -6), (-9, -12), (8, -15), (-4, -16)):
        w.place("round_tree", (x, 0, z), yaw=(x * 37) % 360)
    w.add("hero", transform=dict(position=(0, 0.1, 1.5)), player=dict(speed=4, jump=5))
