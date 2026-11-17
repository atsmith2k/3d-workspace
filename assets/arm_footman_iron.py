"""Footman's iron harness: a full set of plate, fitted to all four body shapes by the build.

The armour-slot system in one asset. Seven slots are filled (head, shoulders, chest, arms,
hands, legs, feet); each piece is drawn from the joints of the skeleton it is built for, bound
to its slot's bones, and the body under it is left out of the model, so nothing shows through
when a joint bends.

Spec:
  kind: character
  size: 1.80 m to the crown in the standard shape plus the helm (about 1.84); 1.35 stout,
        1.10 slight, 2.05 tall (each a few cm more with the helm)
  pivot: feet at the origin; faces +Z
  budget: 9000 triangles, four materials, 512 px textures, 35 bones
  materials: worn grey steel plate with hammer marks and spots of rust (faceted, box-mapped, three repeats per metre); dull bronze trim
             (belt, gorget, elbow and knee cops, cuffs, nasal); the dummy's pale wood and dark
             joints where no slot covers it (face, neck, shoulder joints)
  features: kettle helm with brim and nasal; breast and back with a waist band and gorget;
            pauldrons; rerebraces, elbow cops, vambraces; cuffed mitten gauntlets; fauld skirt
            with belt, cuisses, knee cops, greaves; sabatons. `--set slots=head,chest` wears
            only some, and the body shows again where a slot is empty
  clips: idle 3.0 s, walk 1.0 s (the mannequin's): the harness is judged moving
  use: the armour sub-pack's reference set and the test that slots, hiding and fitting work
  engine: no body; rest_y 0. Cinder's world kit does not draw skinned models
"""
from _frp import *
from _frp_body import HIDES, armour, body, dress, idle_clip, walk_clip
from cadkit.game.rig import SHAPES

KIND = "character"
DESCRIPTION = "footman's iron plate harness on the pack's humanoid, fitted to four body shapes"
PARAMS = dict(shape="standard", slots="head,shoulders,chest,arms,hands,legs,feet")
BUDGET = dict(tris=9000, texture=512, materials=4)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("armour", "plate", "iron", "footman", "set")


def worn_slots(p):
    return tuple(s for s in p.slots.split(",") if s)


def checks(p):
    height = SHAPES[p.shape]["height"]
    slots = worn_slots(p)

    def slot_bones(ctx):
        sk = ctx.model.skeleton
        bad = []
        for piece in armour(sk, p.shape, slots):
            if piece.bone.split(".")[0] not in SLOTS[piece.slot]["bones"]:
                bad.append(f"{piece.slot} piece on {piece.bone}")
        return not bad, "; ".join(bad) or f"every piece of {len(slots)} slots is bound to its slot's bones"

    def covered(ctx):
        """What the armour hides, it encloses: no hidden body vertex lies outside the bounds of
        the pieces on the same bone (so leaving the body out removes nothing that would show)."""
        sk = ctx.model.skeleton
        worn = armour(sk, p.shape, slots)
        hidden = {r for piece in worn for r in HIDES[piece.slot]}
        worst, where, count = 0.0, "", 0
        for part in body(sk, p.shape):
            if part.region not in hidden:
                continue
            count += 1
            over = [w.mesh.v for w in worn if w.bone == part.bone or w.bone.split(".")[0] in ("chest", "hips")
                    and part.bone.split(".")[0] in ("spine", "chest", "hips", "upper_leg")]
            v = np.vstack(over)
            out = np.maximum(np.maximum(v.min(0) - part.mesh.v, part.mesh.v - v.max(0)), 0).max()
            if out > worst:
                worst, where = float(out), part.bone
        return worst < 0.004, (f"{count} body parts left out; none reaches outside its armour"
                               if worst < 0.004 else f"the body at {where} sticks {worst * 1000:.0f} mm out of its armour")

    def stands_off(ctx):
        """Plate over the limbs clears the body under it."""
        sk = ctx.model.skeleton
        gaps = []
        limb = {part.bone: part for part in body(sk, p.shape) if part.region in ("arms", "legs") and part.mat == "wood"}
        for piece in armour(sk, p.shape, slots):
            if piece.mat == "plate" and piece.bone in limb and piece.slot in ("arms", "legs") and piece.bone != "hips":
                a = sk.head(piece.bone)
                b = sk.tail(sk.index(piece.bone))
                d = (b - a) / np.linalg.norm(b - a)

                def radius(v):
                    rel = v - a
                    return np.linalg.norm(rel - np.outer(rel @ d, d), axis=1).max()
                gaps.append(radius(piece.mesh.v) - radius(limb[piece.bone].mesh.v))
        if not gaps:
            return True, "no limb plates worn"
        return min(gaps) > 0.006, f"limb plates stand {min(gaps) * 1000:.0f}-{max(gaps) * 1000:.0f} mm off the body"
    return [size(y=(height, height + 0.09)) if "head" in slots else size(y=(height - 0.03, height + 0.03)),
            tris(max=9000), pivot((0.5, 0.0, None), tol=0.02), materials(4),
            clips("idle", "walk"), deforms_cleanly(), custom("slots", slot_bones), custom("covers what it hides", covered),
            custom("plate stands off the body", stands_off)]


def build(p):
    sk = humanoid(p.shape)
    ch = Character(sk)
    mats = dict(wood=flat_material("frp_mannequin_wood", "wood_pale", roughness=0.7),
                joint=flat_material("frp_mannequin_joint", "wood_dark", roughness=0.8),
                plate=plate_worn(),
                trim=flat_material("frp_trim_bronze", "bronze", roughness=0.45, metallic=0.9))
    dress(ch, sk, p.shape, mats, armour(sk, p.shape, worn_slots(p)))
    ch.clips = [idle_clip(), walk_clip()]
    return ch
