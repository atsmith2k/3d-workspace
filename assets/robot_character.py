"""Robot character: a friendly rounded robot on the 18-bone biped, with idle and walk.

Spec:
  kind: character
  size: about 0.9 m across the hands x 1.70 m tall x 0.3 m deep
  pivot: feet at the origin, centred in X; faces +Z
  budget: 3000 triangles, two materials (sandbox atlas; visor glow), 18 bones
  materials: light grey body panels, orange accents (shoulders, hands, feet, chest plate, ears),
             dark joints, a cyan glowing visor
  features: round head with a visor, ears and an antenna; box torso and pelvis; tube limbs with
            ball joints at shoulder, elbow, hip and knee. Every part is rigid to one bone (it is
            a robot), and the balls hide the joints as they turn. Relaxed A-pose bind
  clips: idle 3.0 s (the head scans left and right), walk 1.0 s; both loop in place; walk strikes
         with the left foot at phase 0, like the adventurer's, so the two characters share clips' timing
  use: default player avatar or NPC of the builder; fits the 1.2 x 2.2 m dungeon doorway
  engine: no body (the player component brings its capsule); rest_y 0
"""
from _sandbox import *

KIND = "character"
DESCRIPTION = "friendly rounded robot with idle and walk"
PARAMS = dict(height=1.70)
BUDGET = dict(tris=3000, texture=512, materials=2)
ENGINE = dict(rest_y=0.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["character", "robot", "rigged", "player"],
               notes="Skinned. Cinder 0.1.1's world kit loads a skinned model but draws nothing (it attaches no "
                     "animator): use it from a Mojo Game that gives the spawned mesh an AnimatorRef. Clips by "
                     "index: 0 idle, 1 walk; both loop. Front is +Z. Two materials: the kit atlas and a glowing "
                     "visor (an emissive part needs its own material).")


def checks(p):
    def doorway(ctx):
        lo, hi = ctx.model.bounds
        return hi[0] - lo[0] <= 1.2 and hi[1] <= 2.2, f"{hi[0] - lo[0]:.2f} m wide, {hi[1]:.2f} m tall: fits 1.2 x 2.2"

    def feet(ctx):
        from cadkit.game.rig import bone_positions
        clip = ctx.model.clip("walk")
        low = min(min(bone_positions(ctx.model.skeleton, clip, clip.duration * k / 32)[f"foot.{s}"][1] for s in "LR")
                  for k in range(32))
        return low > 0.0, f"lowest ankle {low * 1000:.0f} mm above the floor through the walk"
    return [size(x=(0.75, 1.1), y=(p.height - 0.02, p.height + 0.02), z=(0.2, 0.4)), tris(max=3000),
            pivot((0.5, 0.0, None)), materials(2), clips("idle", "walk"), custom("fits the doorway", doorway),
            custom("feet stay above the floor", feet)]


def tube(a, b, r0, r1, sides=8):
    length = float(np.linalg.norm(np.asarray(b) - np.asarray(a)))
    m = merge(lathe([(r0, 0), (r1, length)], sides), disc(r0, 0, sides, up=False), disc(r1, length, sides))
    return along(m, a, b)


def build(p):
    h = p.height / 1.75
    sk = biped(p.height)
    ch = Character(sk)
    mat = atlas()
    glow = Material("robot_visor", color=(0.1, 0.8, 1.0), roughness=0.3, emissive=(0.1, 0.85, 1.0),
                    emissive_strength=1.6)

    def add(mesh, t, bone):
        ch.add(tile(mesh, t), mat, bind=bone)

    def at(name):
        return sk.head(name)

    hips, chest_y = at("hips"), (at("spine")[1] + at("neck")[1]) / 2
    add(bevel_box(0.30 * h, 0.17 * h, 0.21 * h, 0.03).moved(0, hips[1] - 0.01, 0), T.DARK, "hips")
    add(bevel_box(0.41 * h, 0.47 * h, 0.27 * h, 0.05).moved(0, chest_y, 0), T.GREY, "chest")
    add(box(0.19 * h, 0.13 * h, 0.02).moved(0, chest_y + 0.07 * h, 0.137 * h), T.ORANGE, "chest")
    add(tube((0, at("neck")[1] - 0.02, 0), (0, at("head")[1] + 0.02, 0), 0.045 * h, 0.045 * h), T.DARK, "neck")
    head_y = at("head")[1] + 0.105 * h
    add(ball(0.155 * h, 10, 6).scaled(1, 0.92, 1).moved(0, head_y, 0), T.GREY, "head")
    for x in (-1, 1):
        add(box(0.035 * h, 0.08 * h, 0.08 * h).moved(x * 0.158 * h, head_y, 0), T.ORANGE, "head")
    top = head_y + 0.155 * h * 0.92
    add(tube((0, top - 0.01, 0), (0, p.height - 0.03 * h, 0), 0.008, 0.008, 6), T.DARK, "head")
    add(ball(0.016 * h, 6, 3).moved(0, p.height - 0.016 * h, 0), T.ORANGE, "head")
    ch.add(box(0.21 * h, 0.055 * h, 0.03).moved(0, head_y + 0.015 * h, 0.14 * h), glow, bind="head")
    for s in ("L", "R"):
        sh, el, wr = at(f"upper_arm.{s}"), at(f"lower_arm.{s}"), at(f"hand.{s}")
        tip = sk.tail(sk.index(f"hand.{s}"))
        add(ball(0.082 * h).moved(*sh), T.ORANGE, f"upper_arm.{s}")
        add(tube(sh, el, 0.056 * h, 0.056 * h), T.GREY, f"upper_arm.{s}")
        add(ball(0.072 * h).moved(*el), T.DARK, f"lower_arm.{s}")
        add(tube(el, wr, 0.06 * h, 0.05 * h), T.GREY, f"lower_arm.{s}")
        add(ball(0.072 * h).moved(*(wr + (tip - wr) * 0.35)), T.ORANGE, f"hand.{s}")
        hp, kn, an = at(f"upper_leg.{s}"), at(f"lower_leg.{s}"), at(f"foot.{s}")
        add(ball(0.086 * h).moved(*hp), T.DARK, f"upper_leg.{s}")
        add(tube(hp, kn, 0.075 * h, 0.068 * h), T.GREY, f"upper_leg.{s}")
        add(ball(0.083 * h).moved(*kn), T.DARK, f"lower_leg.{s}")
        add(tube(kn, an, 0.068 * h, 0.058 * h), T.GREY, f"lower_leg.{s}")
        add(bevel_box(0.115 * h, 0.085 * h, 0.25 * h, 0.02).moved(an[0], 0.0425 * h, 0.05 * h), T.ORANGE, f"foot.{s}")
    ch.clips = [idle(), walk()]
    return ch


def walk():
    return Clip.cycle("walk", 1.0, lambda ph: biped_gait(ph, stride=24, knee=50, arm=22, elbow=18, lean=3,
                                                          bob=0.010, twist=4), keys=16)


def idle():
    def pose(ph):
        s = np.sin(2 * np.pi * ph)
        out = {"hips:move": (0, -0.004 - 0.004 * np.sin(4 * np.pi * ph), 0),
               "chest": euler(x=1.0 * np.sin(4 * np.pi * ph)),
               "head": euler(y=14 * s),                              # scanning left and right
               "upper_leg.L": euler(x=-1.5), "upper_leg.R": euler(x=-1.5),
               "lower_leg.L": euler(x=3.0), "lower_leg.R": euler(x=3.0)}
        for side, sign in (("L", 1.0), ("R", -1.0)):
            out[f"upper_arm.{side}"] = euler(x=1.5 * s, z=-sign * 22)
            out[f"lower_arm.{side}"] = euler(x=-14)
        return out
    return Clip.cycle("idle", 3.0, pose, keys=12)
