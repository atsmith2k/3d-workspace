"""Skeletons, skinning and clips for characters.

A Skeleton is a list of bones in parents-first order, each with a head position in the bind
pose. Rest rotations are identity, so a bone's local translation is its head minus its
parent's head, and a clip's rotation keys are simply the bone's local rotation.

    sk = biped(1.75)
    ch = Character(sk)
    ch.add(torso_mesh, skin, bind="chest")                              # rigid to one bone
    ch.add(arm_mesh, skin, bind=["upper_arm.L", "lower_arm.L"], blend=0.05)   # smooth elbow
    ch.clips = [walk_clip, run_clip]

Characters face +Z (the world kit turns a player model so +Z points where it walks), stand
with their feet at the origin, and animate in place.
"""
from dataclasses import dataclass, field

import numpy as np

from .model import Mesh, Model, merge

MAX_BONES, MAX_INFLUENCES = 256, 4


@dataclass
class Bone:
    name: str
    parent: int                      # index, -1 for the root
    head: np.ndarray                 # bind-pose position, metres
    tail: np.ndarray = None          # where the bone ends (default: its first child's head)


class Skeleton:
    def __init__(self):
        self.bones = []

    def add(self, name, parent, head, tail=None):
        if name in self.names:
            raise ValueError(f"bone '{name}' twice")
        p = -1 if parent is None else self.index(parent)
        self.bones.append(Bone(name, p, np.asarray(head, float), None if tail is None else np.asarray(tail, float)))
        return self

    @property
    def names(self):
        return [b.name for b in self.bones]

    def index(self, name):
        return self.names.index(name)

    def head(self, name):
        return self.bones[self.index(name)].head

    def tail(self, i):
        b = self.bones[i]
        if b.tail is not None:
            return b.tail
        kids = [c.head for c in self.bones if c.parent == i]
        return kids[0] if kids else b.head + [0, 0.05, 0]

    def local(self, i):
        b = self.bones[i]
        return b.head - (self.bones[b.parent].head if b.parent >= 0 else 0)

    def __len__(self):
        return len(self.bones)


# ---------------------------------------------------------------- rotations

def quat(deg, axis):
    """Unit quaternion (x, y, z, w) for a rotation of `deg` about an axis ("x", "y", "z" or a vector)."""
    v = dict(x=(1, 0, 0), y=(0, 1, 0), z=(0, 0, 1))[axis] if isinstance(axis, str) else axis
    v = np.asarray(v, float)
    v = v / np.linalg.norm(v)
    h = np.radians(deg) / 2
    return np.append(v * np.sin(h), np.cos(h))


def qmul(a, b):
    """Quaternion product: the rotation `a * b` applies b first, then a (like matrices)."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def euler(x=0.0, y=0.0, z=0.0):
    """Rotation by x, then y, then z degrees about the bone's parent axes."""
    return qmul(quat(z, "z"), qmul(quat(y, "y"), quat(x, "x")))


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def slerp(a, b, t):
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        q = a + t * (b - a)
        return q / np.linalg.norm(q)
    th = np.arccos(d)
    return (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)


# ---------------------------------------------------------------- clips

@dataclass
class Clip:
    """Keyframes per bone. rotations[bone] and translations[bone] are lists of (time, value):
    a quaternion (x, y, z, w), or an offset in metres added to the bone's rest translation."""
    name: str
    duration: float
    rotations: dict = field(default_factory=dict)
    translations: dict = field(default_factory=dict)
    looping: bool = True

    @staticmethod
    def cycle(name, duration, pose, keys=16, looping=True):
        """Sample pose(phase) -> {bone: quaternion | ("move", (x, y, z))} at keys+1 evenly spaced
        phases in 0..1 (the last key repeats the first, so the clip loops)."""
        clip = Clip(name, duration, looping=looping)
        for k in range(keys + 1):
            ph = k / keys
            t = ph * duration
            for bone, val in pose(ph % 1.0 if looping else ph).items():
                if bone.endswith(":move"):
                    clip.translations.setdefault(bone[:-5], []).append((t, np.asarray(val, float)))
                else:
                    clip.rotations.setdefault(bone, []).append((t, np.asarray(val, float)))
        return clip

    def _sample(self, keys, t, rot):
        times = [k[0] for k in keys]
        if t <= times[0]:
            return keys[0][1]
        if t >= times[-1]:
            return keys[-1][1]
        i = int(np.searchsorted(times, t, side="right")) - 1
        f = (t - times[i]) / (times[i + 1] - times[i])
        a, b = keys[i][1], keys[i + 1][1]
        return slerp(a, b, f) if rot else a + f * (b - a)

    def pose(self, t):
        """({bone: quaternion}, {bone: offset}) at time t, interpolated as the engine does."""
        return ({b: self._sample(k, t, True) for b, k in self.rotations.items()},
                {b: self._sample(k, t, False) for b, k in self.translations.items()})


def world_matrices(sk, rot=None, move=None):
    """4x4 world matrix of every bone for local rotations `rot` and translation offsets `move`."""
    rot, move = rot or {}, move or {}
    out = []
    for i, b in enumerate(sk.bones):
        m = np.eye(4)
        if b.name in rot:
            m[:3, :3] = qmat(rot[b.name])
        m[:3, 3] = sk.local(i) + move.get(b.name, 0)
        out.append(m if b.parent < 0 else out[b.parent] @ m)
    return out


def skin_matrices(sk, rot=None, move=None):
    """World matrix times inverse bind (a translation by -head) per bone."""
    out = []
    for b, m in zip(sk.bones, world_matrices(sk, rot, move)):
        inv = np.eye(4)
        inv[:3, 3] = -b.head
        out.append(m @ inv)
    return out


def bone_positions(sk, clip, t):
    rot, move = clip.pose(t)
    return {b.name: m[:3, 3] for b, m in zip(sk.bones, world_matrices(sk, rot, move))}


# ---------------------------------------------------------------- skinning

def bind_weights(mesh, sk, bind, blend=0.05):
    """(joints Nx4, weights Nx4). `bind` is one bone name (rigid) or a list of bones: each
    vertex is weighted by how close it lies to each listed bone's segment, falling off over
    `blend` metres past the nearest, so a tube across a joint bends smoothly."""
    n = len(mesh.v)
    joints, weights = np.zeros((n, 4), np.int64), np.zeros((n, 4))
    names = [bind] if isinstance(bind, str) else list(bind)
    idx = [sk.index(b) for b in names]
    if len(idx) == 1:
        joints[:, 0], weights[:, 0] = idx[0], 1.0
        return joints, weights
    d = np.zeros((n, len(idx)))
    for k, i in enumerate(idx):
        a, b = sk.bones[i].head, sk.tail(i)
        ab = b - a
        t = np.clip(((mesh.v - a) @ ab) / max(float(ab @ ab), 1e-12), 0, 1)
        d[:, k] = np.linalg.norm(mesh.v - (a + t[:, None] * ab), axis=1)
    w = np.exp(-((d - d.min(1, keepdims=True)) / blend) ** 2)
    order = np.argsort(-w, axis=1)[:, :4]
    for c in range(order.shape[1]):
        joints[:, c] = np.array(idx)[order[:, c]]
        weights[:, c] = np.take_along_axis(w, order[:, c:c + 1], 1)[:, 0]
    weights[weights < 0.01] = 0
    weights /= weights.sum(1, keepdims=True)
    joints[weights == 0] = 0
    return joints, weights


def deform(mesh, joints, weights, mats):
    """Linear blend skinning on the CPU: the mesh in the pose given by skin matrices."""
    M = np.array(mats)
    v4 = np.c_[mesh.v, np.ones(len(mesh.v))]
    v, n = np.zeros((len(mesh.v), 3)), np.zeros((len(mesh.v), 3))
    for c in range(4):
        m = M[joints[:, c]]
        w = weights[:, c:c + 1]
        v += w * np.einsum("nij,nj->ni", m, v4)[:, :3]
        n += w * np.einsum("nij,nj->ni", m[:, :3, :3], mesh.n)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    return Mesh(v, mesh.f, n, mesh.uv)


class Character(Model):
    """A skinned model: parts bound to a Skeleton, and clips."""

    def __init__(self, skeleton):
        super().__init__()
        self.skeleton = skeleton
        self.skins = []                           # (joints, weights) per part, aligned with parts
        self.clips = []

    def add(self, mesh, material, bind="root", blend=0.05):
        j, w = bind_weights(mesh, self.skeleton, bind, blend)
        for i, (m, mat) in enumerate(self.parts):
            if mat is material:
                self.parts[i] = (merge(m, mesh), mat)
                self.skins[i] = (np.vstack([self.skins[i][0], j]), np.vstack([self.skins[i][1], w]))
                return self
        self.parts.append((mesh, material))
        self.nodes.append(None)
        self.skins.append((j, w))
        return self

    def add_skinned(self, mesh, material, joints, weights):
        """A part whose skin weights were computed elsewhere (Blender's automatic weights:
        `blender.Session.weights`, then `Result.skin`). joints and weights are Nx4, one row per
        vertex; rows are renormalised to sum to 1."""
        j, w = np.asarray(joints, np.int64), np.asarray(weights, float)
        if j.shape != (len(mesh.v), 4) or w.shape != j.shape:
            raise ValueError(f"joints and weights must be {len(mesh.v)} x 4, got {j.shape} and {w.shape}")
        total = w.sum(1, keepdims=True)
        if (total <= 0).any():
            raise ValueError(f"{int((total <= 0).sum())} vertices have no bone at all")
        self.parts.append((mesh, material))
        self.nodes.append(None)
        self.skins.append((j, w / total))
        return self

    def clip(self, name):
        return next(c for c in self.clips if c.name == name)

    def posed(self, clip, t):
        """A static Model of the character at time t of a clip (for pose strips)."""
        rot, move = clip.pose(t)
        mats = skin_matrices(self.skeleton, rot, move)
        return Model(*[(deform(m, j, w, mats), mat) for (m, mat), (j, w) in zip(self.parts, self.skins)])

    def pose_row(self, clip, poses=5, spacing=None):
        """`poses` moments of a clip side by side along X, as one static Model."""
        lo, hi = self.bounds
        step = spacing or (hi[0] - lo[0]) * 1.15
        row = Model()
        for k in range(poses):
            t = clip.duration * k / poses
            for m, mat in self.posed(clip, t).parts:
                row.add(m.moved((k - (poses - 1) / 2) * step, 0, 0), mat)
        return row


# ---------------------------------------------------------------- templates

def biped(height=1.75, shoulder=0.19, hip=0.095, arm_down=62.0):
    """A humanoid skeleton of the given height standing on Y=0, facing +Z, arms out and down
    by `arm_down` degrees from horizontal (a relaxed A-pose, so it looks natural unanimated).
    18 bones; `root` at the feet is bone 0 (root motion, if a game enables it, acts on it)."""
    h = height / 1.75
    sk = Skeleton()
    sk.add("root", None, (0, 0, 0))
    sk.add("hips", "root", (0, 0.94 * h, 0))
    sk.add("spine", "hips", (0, 1.08 * h, 0))
    sk.add("chest", "spine", (0, 1.24 * h, 0))
    sk.add("neck", "chest", (0, 1.44 * h, 0))
    sk.add("head", "neck", (0, 1.50 * h, 0), tail=(0, 1.75 * h, 0))
    a = np.radians(arm_down)
    for s, side in ((1, "L"), (-1, "R")):                    # the character's left is +X when it faces +Z
        sh = np.array([s * shoulder * h, 1.40 * h, 0])
        d = np.array([s * np.cos(a), -np.sin(a), 0])
        sk.add(f"upper_arm.{side}", "chest", sh)
        sk.add(f"lower_arm.{side}", f"upper_arm.{side}", sh + d * 0.27 * h)
        sk.add(f"hand.{side}", f"lower_arm.{side}", sh + d * 0.52 * h, tail=sh + d * 0.66 * h)
    for s, side in ((1, "L"), (-1, "R")):
        x = s * hip * h
        sk.add(f"upper_leg.{side}", "hips", (x, 0.90 * h, 0))
        sk.add(f"lower_leg.{side}", f"upper_leg.{side}", (x, 0.50 * h, 0))
        sk.add(f"foot.{side}", f"lower_leg.{side}", (x, 0.09 * h, 0), tail=(x, 0.02 * h, 0.16 * h))
    return sk


def contact_phase(sk, clip, bone, samples=64):
    """Phase (0..1) at which a bone is furthest forward (+Z): for a foot, where it strikes."""
    z = [bone_positions(sk, clip, clip.duration * k / samples)[bone][2] for k in range(samples)]
    return int(np.argmax(z)) / samples


def biped_gait(ph, stride, knee, arm, elbow, lean, bob, twist, drop=24.0):
    """One pose of a walk or run for a `biped` skeleton at phase 0..1, as Clip.cycle wants it.
    Phase 0 is the left foot's strike, whatever the amplitudes, so every gait made from this
    function blends with every other on a shared phase. Degrees and metres: `stride` swings the
    thighs, `knee` bends the swinging leg, `arm` swings the arms against the legs, `elbow` bends
    them, `lean` tips the body forward, `bob` drops the hips at each strike, `twist` counter-
    rotates hips and chest, `drop` brings the A-pose arms down to the sides."""
    w = 2 * np.pi * ph
    c = np.cos(w)
    pose = {"hips:move": (0, -bob * np.cos(2 * w) - bob * 0.6, 0),
            "hips": euler(x=lean * 0.4, y=twist * c),
            "spine": euler(x=lean * 0.3, y=-twist * 0.6 * c),
            "chest": euler(x=lean * 0.3, y=-twist * 0.9 * c),
            "head": euler(x=-lean * 0.6, y=twist * 0.5 * c)}
    for side, sign, off in (("L", 1.0, 0.0), ("R", -1.0, 0.5)):
        cc = np.cos(2 * np.pi * (ph + off))
        swing = np.sin(2 * np.pi * (ph + off - 0.5))              # > 0 while this leg swings forward
        bend = knee * max(0.0, swing) ** 0.8 + knee * 0.12 * max(0.0, -swing)
        pose[f"upper_leg.{side}"] = euler(x=-stride * cc - bend * 0.35)
        pose[f"lower_leg.{side}"] = euler(x=bend)
        pose[f"foot.{side}"] = euler(x=-0.5 * bend * 0.3 + stride * 0.25 * cc)
        pose[f"upper_arm.{side}"] = euler(x=arm * cc, z=-sign * drop)
        pose[f"lower_arm.{side}"] = euler(x=-elbow - elbow * 0.25 * cc)
    return pose


# The shared humanoid: one skeleton for heroes, townsfolk and humanoid monsters, so armour,
# weapons and clips made for one fit all. Body shapes change proportions, never bone names.
SHAPES = dict(standard=dict(height=1.80, width=1.00), stout=dict(height=1.35, width=1.30),
              slight=dict(height=1.10, width=0.92), tall=dict(height=2.05, width=1.16))

# Attachment points. A socket is a bone that moves nothing by itself: a game parents an item to
# it, and a build binds an item to it rigidly. `turn` is how an item made to the held-item
# convention (grip at its origin, blade or shaft along +Y) is turned to sit in the socket at
# rest: (degrees, axis) pairs applied in order.
SOCKETS = {
    "socket_hand.R": dict(parent="hand.R", use="main-hand weapon or tool", turn=((90, "x"),)),
    "socket_hand.L": dict(parent="hand.L", use="off-hand weapon, torch, focus", turn=((90, "x"),)),
    "socket_shield": dict(parent="lower_arm.L", use="shield strap, on the outside of the forearm", turn=()),
    "socket_back": dict(parent="chest", use="two-handed weapon, bow or staff carried on the back", turn=((180, "z"), (20, "z"))),
    "socket_quiver": dict(parent="chest", use="quiver, behind the right shoulder", turn=((160, "z"),)),
    "socket_hip.L": dict(parent="hips", use="sheathed sword, left hip", turn=((180, "z"), (-25, "x"))),
    "socket_hip.R": dict(parent="hips", use="dagger, pouch or potion, right hip", turn=((180, "z"), (-25, "x"))),
    "socket_head": dict(parent="head", use="helmet, hat, crown: the top of the skull", turn=()),
}


def humanoid(shape="standard", arm_down=62.0):
    """The pack's humanoid skeleton in one of four body shapes: the 18 bones of `biped`, plus a
    jaw, eyes, a thumb and a finger group per hand, toes, and eight sockets. 35 bones."""
    spec = SHAPES[shape]
    h = spec["height"] / 1.75
    sk = biped(spec["height"], shoulder=0.19 * spec["width"], hip=0.095 * spec["width"], arm_down=arm_down)
    head, top = sk.head("head"), sk.tail(sk.index("head"))
    sk.add("jaw", "head", head + [0, 0.035 * h, 0.03 * h], tail=head + [0, 0.0, 0.10 * h])
    for s, side in ((1, "L"), (-1, "R")):
        sk.add(f"eye.{side}", "head", head + [s * 0.035 * h, 0.12 * h, 0.085 * h], tail=head + [s * 0.035 * h, 0.12 * h, 0.11 * h])
    for s, side in ((1, "L"), (-1, "R")):
        wrist, tip = sk.head(f"hand.{side}"), sk.tail(sk.index(f"hand.{side}"))
        d = (tip - wrist) / np.linalg.norm(tip - wrist)
        sk.add(f"fingers.{side}", f"hand.{side}", wrist + d * 0.07 * h, tail=wrist + d * 0.15 * h)
        sk.add(f"thumb.{side}", f"hand.{side}", wrist + d * 0.03 * h + [0, 0, 0.03 * h], tail=wrist + d * 0.07 * h + [0, 0, 0.06 * h])
        sk.add(f"socket_hand.{side}", f"hand.{side}", wrist + d * 0.075 * h + [0, 0, 0.012 * h])
        ankle = sk.head(f"foot.{side}")
        sk.add(f"toe.{side}", f"foot.{side}", [ankle[0], 0.02 * h, 0.11 * h], tail=[ankle[0], 0.02 * h, 0.2 * h])
    elbow, wrist = sk.head("lower_arm.L"), sk.head("hand.L")
    sk.add("socket_shield", "lower_arm.L", (elbow + wrist) / 2 + [0.05 * h * spec["width"], 0, 0])
    chest, hips = sk.head("chest"), sk.head("hips")
    sk.add("socket_back", "chest", chest + [0, 0.10 * h, -0.14 * h * spec["width"]])
    sk.add("socket_quiver", "chest", chest + [-0.09 * h * spec["width"], 0.14 * h, -0.13 * h * spec["width"]])
    for s, side in ((1, "L"), (-1, "R")):
        sk.add(f"socket_hip.{side}", "hips", hips + [s * 0.15 * h * spec["width"], 0.0, 0.0])
    sk.add("socket_head", "head", top)
    return sk


def attach(character, parts, socket):
    """Bind an item (a list of (mesh, material) made to the held-item convention) to a socket of
    a Character built on `humanoid`, turned as the socket says. Returns the character."""
    at = character.skeleton.head(socket)
    for mesh, material in parts:
        for deg, axis in SOCKETS[socket]["turn"]:
            mesh = mesh.rotated(deg, axis)
        character.add(mesh.moved(*at), material, bind=socket)
    return character
