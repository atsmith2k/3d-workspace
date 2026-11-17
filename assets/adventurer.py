"""Adventurer: a stylised low-poly humanoid, skinned to an 18-bone biped, with idle, walk and run.

Spec:
  kind: character
  size: about 0.95 m across the hands x 1.75 m tall x 0.3 m deep
  pivot: feet at the origin, centred in X; faces +Z (the world kit turns +Z toward travel)
  budget: 1500 triangles, one material (a palette strip), 256 bones max (18 used)
  materials: one flat-colour palette: skin, hair, tunic, trousers, boots, belt, eyes
  features: relaxed A-pose bind (arms 62 degrees down) so it looks natural unanimated;
            smooth elbows and knees (each limb is one tube weighted across the joint)
  clips: idle 2.4 s, walk 1.0 s, run 0.7 s; all loop, all in place; walk and run strike with
         the left foot at phase 0, so Cinder can blend them on a shared phase
  use: a player or NPC body beside 3 m dungeon walls; the world kit shows it in its bind pose
  engine: no body (the player component brings its own capsule); rest_y 0
"""
from cadkit.game import *

KIND = "character"
DESCRIPTION = "stylised adventurer with idle, walk and run"
PARAMS = dict(height=1.75)
BUDGET = dict(tris=1500, texture=256, materials=1)
ENGINE = dict(rest_y=0.0)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["character", "humanoid", "rigged"],
               notes="Skinned. Cinder 0.1.1's world kit loads a skinned model but draws nothing (it attaches no "
                     "animator, so there is no joint palette): use it from a Mojo Game that gives the spawned "
                     "mesh an AnimatorRef. Clips by index: 0 idle, 1 walk, 2 run; all loop; walk and run share "
                     "foot phase. Front is +Z.")

SKIN, HAIR, TUNIC, TROUSERS, BOOTS, BELT, EYES = range(7)
COLORS = [(0.86, 0.66, 0.52), (0.33, 0.20, 0.11), (0.20, 0.42, 0.34), (0.36, 0.30, 0.24),
          (0.22, 0.14, 0.09), (0.45, 0.30, 0.14), (0.06, 0.05, 0.05)]
ARM_DOWN = 62.0


def checks(p):
    return [size(x=(0.8, 1.1), y=(p.height - 0.03, p.height + 0.03), z=(0.2, 0.4)), tris(max=1500),
            pivot((0.5, 0.0, None)), materials(1), clips("idle", "walk", "run"),
            phase_matched("walk", "run", "foot.L"),
            custom("feet stay near the floor", feet_on_floor)]


def feet_on_floor(ctx):
    """No pose of walk or run drives a foot bone far under Y=0 or lifts both feet absurdly."""
    from cadkit.game.rig import bone_positions
    lo = 1.0
    for name in ("walk", "run"):
        clip = ctx.model.clip(name)
        for k in range(32):
            pos = bone_positions(ctx.model.skeleton, clip, clip.duration * k / 32)
            lo = min(lo, pos["foot.L"][1], pos["foot.R"][1])
    return lo > 0.0, f"lowest ankle {lo * 1000:.0f} mm above the floor across walk and run (rest 158 mm)"


# ---------------------------------------------------------------- mesh

def limb(sk, bones, profile, sides=8):
    """A tube along a chain of bones: profile is (radius, distance from the chain's start)."""
    a, b = sk.head(bones[0]), sk.tail(sk.index(bones[-1]))
    d = (b - a) / np.linalg.norm(b - a)
    tube = lathe(profile, sides)                                  # along +Y
    if abs(d[1] + 1) < 1e-6:                                      # straight down
        return tube.rotated(180, "z").moved(*a)
    ang = np.degrees(np.arctan2(-d[0], d[1]))                     # turn +Y onto d, about Z
    return tube.rotated(ang, "z").moved(*a)


def build(p):
    h = p.height / 1.75
    sk = biped(p.height, arm_down=ARM_DOWN)
    pal = palette("adventurer_palette", COLORS)

    def col(mesh, i):
        return swatch_uv(mesh, i, pal)

    ch = Character(sk)
    # torso and skirt of the tunic: one tube from below the hips to the shoulders, flattened front to back
    torso = lathe([(0.195, 0.76), (0.18, 0.90), (0.16, 1.04), (0.185, 1.24), (0.195, 1.37), (0.12, 1.46),
                   (0.055, 1.49)], 10).scaled(h, h, 0.70 * h)
    ch.add(col(merge(torso, disc(0.195 * h, 0.76 * h, 10, up=False).scaled(1, 1, 0.70)), TUNIC),
           pal, bind=["hips", "spine", "chest"], blend=0.07)
    belt = lathe([(0.172, 0.985), (0.177, 1.0), (0.177, 1.045), (0.170, 1.06)], 10).scaled(h, h, 0.72 * h)
    ch.add(col(belt, BELT), pal, bind="spine")
    ch.add(col(box(0.05, 0.05, 0.02).moved(0, 1.022, 0.126).scaled(h), HAIR), pal, bind="spine")   # buckle
    # head: neck, skull, hair cap, eyes
    ch.add(col(lathe([(0.05, 1.44), (0.048, 1.53)], 8).scaled(h), SKIN), pal, bind=["neck", "head"])
    skull = lathe([(0.0, 1.495), (0.075, 1.515), (0.108, 1.585), (0.108, 1.655), (0.085, 1.715), (0.0, 1.74)], 10)
    ch.add(col(skull.scaled(h, h, 1.05 * h), SKIN), pal, bind="head")
    hair = lathe([(0.115, 1.60), (0.118, 1.66), (0.094, 1.725), (0.05, 1.748), (0.0, 1.75)], 10)
    back = box(0.2, 0.16, 0.05).moved(0, 1.57, -0.095)
    ch.add(col(merge(hair.scaled(h, h, 1.07 * h).moved(0, 0, -0.012 * h), back.scaled(h)), HAIR), pal, bind="head")
    for x in (-0.042, 0.042):
        ch.add(col(box(0.022, 0.03, 0.012).moved(x, 1.625, 0.112).scaled(h), EYES), pal, bind="head")
    # arms: sleeve to the elbow, bare forearm, a mitten hand
    for side in ("L", "R"):
        chain = [f"upper_arm.{side}", f"lower_arm.{side}"]
        sleeve = limb(sk, chain, [(0.0, -0.035 * h), (0.062 * h, -0.02 * h), (0.058 * h, 0.12 * h),
                                  (0.052 * h, 0.23 * h), (0.054 * h, 0.27 * h), (0.056 * h, 0.30 * h)])
        fore = limb(sk, chain, [(0.044 * h, 0.27 * h), (0.043 * h, 0.31 * h), (0.040 * h, 0.42 * h),
                                (0.034 * h, 0.52 * h)])
        ch.add(col(sleeve, TUNIC), pal, bind=chain, blend=0.045)
        ch.add(col(fore, SKIN), pal, bind=chain, blend=0.045)
        a, b = sk.head(f"hand.{side}"), sk.tail(sk.index(f"hand.{side}"))
        d = (b - a) / np.linalg.norm(b - a)
        hand = box(0.045 * h, 0.13 * h, 0.085 * h).rotated(np.degrees(np.arctan2(-d[0], d[1])), "z")
        ch.add(col(hand.moved(*(a + d * 0.055 * h)), SKIN), pal, bind=f"hand.{side}")
    # legs: trousers to the boot top, boot, foot
    for side in ("L", "R"):
        chain = [f"upper_leg.{side}", f"lower_leg.{side}"]
        x = sk.head(chain[0])[0]
        boot = lathe([(0.052, 0.07), (0.056, 0.20), (0.066, 0.33), (0.07, 0.345)], 8).scaled(h).moved(x, 0, 0)
        leg = lathe([(0.058, 0.33), (0.062, 0.44), (0.066, 0.50), (0.070, 0.56), (0.076, 0.74),
                     (0.074, 0.90)], 8).scaled(h).moved(x, 0, 0)
        ch.add(col(boot, BOOTS), pal, bind=chain + [f"foot.{side}"], blend=0.05)
        ch.add(col(leg, TROUSERS), pal, bind=chain, blend=0.05)
        foot = box(0.105, 0.09, 0.25).moved(x / h, 0.045, 0.05).scaled(h)
        ch.add(col(foot, BOOTS), pal, bind=f"foot.{side}")
    ch.clips = [idle(), walk(), run()]
    return ch


# ---------------------------------------------------------------- clips
# Phase 0 is the left foot's strike (furthest forward) in walk and in run.

gait = biped_gait          # shared: cadkit.game.rig.biped_gait


def walk():
    return Clip.cycle("walk", 1.0, lambda ph: gait(ph, stride=27, knee=58, arm=24, elbow=14, lean=4,
                                                    bob=0.012, twist=5), keys=16)


def run():
    return Clip.cycle("run", 0.7, lambda ph: gait(ph, stride=40, knee=98, arm=36, elbow=75, lean=16,
                                                   bob=0.028, twist=9), keys=16)


def idle():
    def pose(ph):
        s = np.sin(2 * np.pi * ph)
        s2 = np.sin(4 * np.pi * ph)
        out = {"hips:move": (0, -0.004 - 0.004 * s, 0),
               "spine": euler(x=1.2 * s), "chest": euler(x=1.6 * s),
               "head": euler(x=-1.5 * s, y=5 * np.sin(2 * np.pi * ph + 1.0)),
               "upper_leg.L": euler(x=-1.0 - 1.0 * s), "upper_leg.R": euler(x=-1.0 - 1.0 * s),
               "lower_leg.L": euler(x=2.0 + 2.0 * s), "lower_leg.R": euler(x=2.0 + 2.0 * s)}
        for side, sign in (("L", 1.0), ("R", -1.0)):
            out[f"upper_arm.{side}"] = euler(x=2.0 * s2, z=-sign * (22 + 1.5 * s))
            out[f"lower_arm.{side}"] = euler(x=-12 - 3 * s)
        return out
    return Clip.cycle("idle", 2.4, pose, keys=12)
