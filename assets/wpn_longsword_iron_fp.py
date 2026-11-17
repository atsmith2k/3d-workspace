"""Iron longsword, first-person view model: the right arm and the sword as the player sees them.

A view model is not the world model seen close: it is a separate asset drawn by its own camera
at the player's eye, so the sword never clips into a wall and always sits where the hand would.
Its origin is the eye. The camera looks down -Z with +Y up, so the model lives in front of the
origin, low and to the right, and the arm runs out of the bottom of the frame.

Spec:
  kind: character
  size: about 0.5 x 1.1 x 0.75 m: forearm, hand and the 1.16 m sword
  pivot: the origin is the camera (the player's eye). View: 70 degrees vertical, 16:9
  budget: 8000 triangles, five materials (three are the sword's), 1024 px textures, 6 bones
  materials: the world sword's (steel blade, rusted guard, leather grip); undyed sleeve;
             dark leather glove and bracer
  features: sleeve to the elbow (which is out of frame), leather bracer, gloved hand closed
            round the grip with the thumb over it; the sword in socket_hand.R, blade up and
            leaning forward and in toward the middle of the view
  clips: idle 3.0 s (the blade sways, the hand breathes); swing 0.7 s (draw back to the right,
         lay the blade over and sweep it across the lower middle of the view to the left, recover). Both loop to the rest pose
  frame: at rest the sword and hand are inside the frame, between 3 and 25 % of it, and the
         arm leaves by the bottom or right edge; during the swing the blade sweeps across the centre line into the left half, low in the view
  use: first-person melee. A game draws it with a second camera at the eye (near plane 0.05 m)
       over the world, and plays `swing` on attack
  engine: no body. Cinder's world kit does not draw skinned models; the build writes
          `<name>_firstperson.png`, a plain projection of the rest pose and the swing
"""
from pathlib import Path

from PIL import Image, ImageDraw

from _frp import *
from _frp_body import Params, tube
from cadkit.game.rig import SOCKETS

import wpn_longsword_iron as sword

KIND = "character"
DESCRIPTION = "first-person view model: right arm holding the iron longsword"
PARAMS = dict(fov=70.0)
BUDGET = dict(tris=8000, texture=1024, materials=5)
ENGINE = dict(rest_y=0.6)
PRODUCT = product("weapons", "sword", "viewmodel", "first-person", gameplay=dict(
    camera="origin, looks -Z, +Y up", fov_deg=70, near_m=0.05, clips=dict(attack="swing", rest="idle"), world_model="wpn_longsword_iron"))

ELBOW = np.array([0.36, -0.50, -0.16])
WRIST = np.array([0.25, -0.27, -0.44])
BLADE = np.array([-0.26, 0.56, -0.78]) / np.linalg.norm([-0.26, 0.56, -0.78])
ASPECT = 16 / 9
OUT = Path(__file__).resolve().parent.parent / "output" / "game" / "wpn_longsword_iron_fp"


def project(v, fov):
    """Camera at the origin looking down -Z: (x, y) in -1..1 across the frame, and depth."""
    t = np.tan(np.radians(fov) / 2)
    depth = -v[:, 2]
    z = np.maximum(depth, 1e-6)
    return np.c_[v[:, 0] / z / (t * ASPECT), v[:, 1] / z / t], depth


def colour_of(mat):
    if getattr(mat, "base", None) is not None:
        return tuple(int(255 * c) for c in np.asarray(mat.base).reshape(-1, 3).mean(0))
    return tuple(int(255 * (c ** (1 / 2.2))) for c in mat.color[:3])


def frame(model, fov, size=(640, 360), back=(38, 40, 46)):
    """A plain picture of what the camera at the origin sees: flat-shaded triangles, far to
    near. Returns (image, mask of covered pixels). Not the engine's render: it is here to prove
    where the model sits in the frame."""
    w, h = size
    img, mask = Image.new("RGB", size, back), Image.new("L", size, 0)
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mask)
    tris = []
    light = np.array([0.3, 0.8, 0.5]) / np.linalg.norm([0.3, 0.8, 0.5])
    for mesh, mat in model.parts:
        xy, depth = project(mesh.v, fov)
        col = np.array(colour_of(mat))
        for f in mesh.f:
            if depth[f].min() < 0.05:                         # behind the near plane
                continue
            nrm = np.cross(mesh.v[f[1]] - mesh.v[f[0]], mesh.v[f[2]] - mesh.v[f[0]])
            ln = np.linalg.norm(nrm)
            if ln < 1e-12 or nrm @ mesh.v[f[0]] > 0:          # faces away from the eye
                continue
            shade = 0.45 + 0.55 * max(0.0, float(nrm @ light) / ln)
            pts = [((x + 1) / 2 * w, (1 - y) / 2 * h) for x, y in xy[f]]
            tris.append((depth[f].mean(), pts, tuple(int(c * shade) for c in col)))
    for _, pts, col in sorted(tris, key=lambda q: -q[0]):
        d.polygon(pts, fill=col)
        dm.polygon(pts, fill=255)
    return img, np.asarray(mask) > 0


def checks(p):
    def in_frame(ctx):
        m = ctx.model
        _, mask = frame(m, p.fov)
        share = float(mask.mean())
        blade = m.parts[0][0].v                               # the sword's blade is the first part
        xy, depth = project(blade, p.fov)
        inside = bool((np.abs(xy) <= 1).all() and (depth > 0.05).all())
        edge = bool(mask[-1].any() or mask[:, -1].any())      # the arm runs off the bottom or the right
        floats = bool(mask[0].any() or mask[:, 0].any())
        ok = inside and edge and not floats and 0.03 < share < 0.25
        return ok, (f"the model covers {share:.0%} of the frame; the whole blade is {'in' if inside else 'OUT OF'} view; "
                    f"the arm {'leaves by the bottom or right edge' if edge else 'ENDS IN VIEW'}"
                    + ("; it touches the top or left edge" if floats else ""))

    def swing_crosses(ctx):
        m = ctx.model
        clip = m.clip("swing")
        best, most = 9.0, 0.0
        for k in range(24):
            posed = m.posed(clip, clip.duration * k / 24)
            xy, depth = project(posed.parts[0][0].v, p.fov)
            vis = xy[depth > 0.05]
            seen = vis[(np.abs(vis[:, 1]) < 1)]
            if len(seen):
                best = min(best, float(seen[:, 0].min()))        # how far left the blade reaches while in the frame
            most = max(most, float(np.abs(posed.parts[0][0].v - m.parts[0][0].v).max()))
        return best < -0.25 and most > 0.4, (f"in the swing the blade reaches {best:+.2f} across the frame (0 is the centre line, "
                                              f"-1 the left edge) and its tip travels {most:.2f} m")

    def picture(ctx):
        m = ctx.model
        clip = m.clip("swing")
        tiles = [frame(m, p.fov)[0]] + [frame(m.posed(clip, clip.duration * t), p.fov)[0] for t in (0.18, 0.32, 0.45)]
        sheet = Image.new("RGB", (1280, 720))
        for i, im in enumerate(tiles):
            sheet.paste(im, (640 * (i % 2), 360 * (i // 2)))
        OUT.mkdir(parents=True, exist_ok=True)
        sheet.save(OUT / "wpn_longsword_iron_fp_firstperson.png")
        return True, "wrote wpn_longsword_iron_fp_firstperson.png: rest, drawn back, mid-cut, follow-through"

    def near(ctx):
        z = max(float(m.v[:, 2].max()) for m, _ in ctx.model.parts)
        return z < -0.05, f"the nearest point is {-z * 100:.0f} cm in front of the eye (near plane 5 cm)"
    return [tris(max=8000), materials(5), clips("idle", "swing"), deforms_cleanly(),
            custom("in front of the eye", near), custom("in frame at rest", in_frame),
            custom("swing crosses the view", swing_crosses), custom("first-person picture", picture)]


def rig():
    d = (WRIST - ELBOW) / np.linalg.norm(WRIST - ELBOW)
    sk = Skeleton()
    sk.add("root", None, (0, 0, 0))
    sk.add("lower_arm.R", "root", ELBOW)
    sk.add("hand.R", "lower_arm.R", WRIST, tail=WRIST + d * 0.10)
    grip = WRIST + d * 0.075 + [0, 0.012, 0]
    sk.add("fingers.R", "hand.R", grip + [-0.03, 0, 0], tail=grip + [-0.05, -0.02, 0.02])
    sk.add("thumb.R", "hand.R", grip + BLADE * 0.035 + [0.01, 0, 0.03], tail=grip + BLADE * 0.05 + [-0.03, 0, 0.035])
    sk.add("socket_hand.R", "hand.R", grip)
    return sk, d, grip


def build(p):
    sk, d, grip = rig()
    ch = Character(sk)
    # the sword first (the checks find the blade as part 0), in the socket, blade along BLADE
    for mesh, mat in sword.build(Params(**sword.PARAMS)).parts:
        ch.add(along(mesh, grip, grip + BLADE), mat, bind="socket_hand.R")
    sleeve = flat_material("frp_sleeve_undyed", "cloth_undyed", roughness=0.9)
    glove = flat_material("frp_glove_leather", "leather", roughness=0.8)
    ch.add(tube(ELBOW, WRIST - d * 0.13, 0.062, 0.048, 12), sleeve, bind="lower_arm.R")     # the elbow end is below the frame
    ch.add(tube(WRIST - d * 0.14, WRIST - d * 0.01, 0.052, 0.044, 12), glove, bind="lower_arm.R")      # bracer
    ch.add(ball(0.046, 10, 5).scaled(1.0, 0.8, 1.0).moved(*(WRIST + d * 0.045)), glove, bind="hand.R")
    side = np.cross(BLADE, [0, 0, 1.0])
    side /= np.linalg.norm(side)
    for k in range(4):                                         # four fingers wrapped round the grip, toward the eye side
        at = grip + BLADE * (0.045 - 0.028 * k)
        ch.add(tube(at - side * 0.03 + [0, 0, 0.022], at + side * 0.022 + [0, 0, 0.03], 0.0125, 0.011, 6), glove, bind="fingers.R")
    ch.add(tube(sk.head("thumb.R"), sk.tail(sk.index("thumb.R")), 0.014, 0.011, 6), glove, bind="thumb.R")
    ch.clips = [idle(), swing()]
    return ch


def idle():
    def pose(ph):
        s, c = np.sin(2 * np.pi * ph), np.cos(2 * np.pi * ph)
        return {"lower_arm.R": euler(x=0.8 * s, z=1.2 * c), "hand.R": euler(z=1.0 * s), "fingers.R": euler(x=1.5 * s),
                "thumb.R": euler(x=1.0 * c), "root:move": (0, -0.004 * (1 - c) / 2, 0)}
    return Clip.cycle("idle", 3.0, pose, keys=12)


def swing():
    # time, yaw of the forearm (y: + sweeps the tip to the left), roll in the view plane (z: + lays the blade over to
    # the left), pitch (x: - tips it forward), wrist roll
    keys = np.array([[0.00, 0, 0, 0, 0, 0], [0.18, -16, -4, 4, -20, 0.02], [0.26, -8, 0, 0, -6, 0.03],
                     [0.34, 8, 4, -3, 42, 0.06], [0.45, 18, 6, -4, 82, 0.09], [0.62, 13, 4, -3, 54, 0.06],
                     [0.82, 4, 1, -1, 14, 0.02], [1.00, 0, 0, 0, 0, 0]])

    def pose(ph):
        y, z, x, wz, lift = (float(np.interp(ph, keys[:, 0], keys[:, i])) for i in (1, 2, 3, 4, 5))
        return {"lower_arm.R": euler(x=x, y=y, z=z), "hand.R": euler(z=wz), "fingers.R": euler(x=0.0), "thumb.R": euler(x=0.0),
                "root:move": (0.0, lift, -lift)}                       # up and away as it cuts, so the hand stays in view
    return Clip.cycle("swing", 0.7, pose, keys=20)
