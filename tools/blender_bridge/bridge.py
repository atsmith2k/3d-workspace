"""The half of cadkit.game.blender that runs inside Blender.

    blender -b --factory-startup --python bridge.py -- <job folder>

Reads <job>/job.json (a list of steps), meshes as .npz, and writes meshes as .npz, baked maps
as .png and <job>/result.json. It knows nothing about cadkit: arrays in, arrays out.

Meshes cross in cadkit's frame (metres, Y up, -Z forward, v=0 at the top of the image) and are
turned to Blender's (Z up, v=0 at the bottom) on the way in and back on the way out.
"""
import json
import math
import sys
import time
from pathlib import Path

import bmesh
import bpy
import numpy as np

JOB = Path(sys.argv[sys.argv.index("--") + 1])
LOG = []


def log(msg):
    LOG.append(msg)
    print("BRIDGE", msg, flush=True)


def to_blender(v):
    return np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)


def from_blender(v):
    return np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)


def activate(obj, also=()):
    bpy.ops.object.select_all(action="DESELECT")
    for o in also:
        o.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def tris_of(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


OBJ = {}


def get(name):
    if name not in OBJ:
        raise KeyError(f"no object named '{name}' in this job (have: {sorted(OBJ)})")
    return OBJ[name]


# ---------------------------------------------------------------- steps

def op_load(file, name, weld=True, emit=0.0, color=(0.8, 0.8, 0.8)):
    """A mesh from an .npz (v, f, optional uv). weld joins vertices that share a position,
    which a hard-edged game mesh needs before it can be subdivided as one surface."""
    d = np.load(JOB / file)
    v, f = to_blender(d["v"].astype(float)), d["f"].astype(int)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], f.tolist())
    if "uv" in d.files:
        layer = me.uv_layers.new(name="UVMap")
        uv = d["uv"].astype(float)[f.reshape(-1)]
        uv[:, 1] = 1 - uv[:, 1]
        layer.data.foreach_set("uv", uv.reshape(-1))
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    if weld:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    if emit:
        bsdf.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = float(emit)
    me.materials.append(mat)
    OBJ[name] = obj
    return dict(triangles=tris_of(obj), vertices=len(me.vertices))


def _texture(spec, name):
    tex = bpy.data.textures.new(name, spec.get("type", "CLOUDS"))
    for k, val in spec.items():
        if k != "type":
            setattr(tex, k, val)
    return tex


def op_modify(target, stack):
    """Add Blender modifiers and apply them, in order. Each is {"type": "SUBSURF", ...props};
    a "texture" prop is a texture spec {"type": "VORONOI", "noise_scale": 0.2}; an "object"
    prop names another object of the job."""
    obj = get(target)
    activate(obj)
    for i, spec in enumerate(stack):
        spec = dict(spec)
        m = obj.modifiers.new(f"m{i}", spec.pop("type"))
        for k, val in spec.items():
            if k == "texture":
                m.texture = _texture(val, f"{target}_t{i}")
            elif k in ("object", "mirror_object", "offset_object"):
                setattr(m, k, get(val))
            else:
                setattr(m, k, val)
        bpy.ops.object.modifier_apply(modifier=m.name)
    return dict(triangles=tris_of(obj))


def op_boolean(target, other, operation="DIFFERENCE", solver="EXACT", materials="TRANSFER"):
    """Cut `other` out of `target` (or UNION / INTERSECT). With materials="TRANSFER" the faces
    the cut makes carry the cutter's material, which is how a carved region can be baked as a
    mask; with "INDEX" they take the target's own material of the same slot."""
    obj = get(target)
    activate(obj)
    m = obj.modifiers.new("bool", "BOOLEAN")
    m.object = get(other)
    m.operation = operation
    for k, val in (("solver", solver), ("material_mode", materials)):
        try:
            setattr(m, k, val)
        except (AttributeError, TypeError):
            pass
    bpy.ops.object.modifier_apply(modifier=m.name)
    get(other).hide_render = True
    return dict(triangles=tris_of(obj))


def op_join(target, others):
    obj = get(target)
    activate(obj, [get(o) for o in others])
    bpy.ops.object.join()
    for o in others:
        OBJ.pop(o)
    return dict(triangles=tris_of(obj))


def op_copy(source, name):
    src = get(source)
    obj = src.copy()
    obj.data = src.data.copy()
    obj.name = name
    bpy.context.scene.collection.objects.link(obj)
    OBJ[name] = obj
    return dict(triangles=tris_of(obj))


def op_remesh(target, voxel_size, smooth=True):
    """Rebuild the surface as one skin at a voxel size: fuses overlapping parts, loses UVs."""
    obj = get(target)
    activate(obj)
    obj.data.remesh_voxel_size = voxel_size
    bpy.ops.object.voxel_remesh()
    if smooth:
        bpy.ops.object.shade_smooth()
    return dict(triangles=tris_of(obj))


def op_decimate(target, tris):
    obj = get(target)
    activate(obj)
    now = tris_of(obj)
    if now > tris:
        m = obj.modifiers.new("dec", "DECIMATE")
        m.ratio = tris / now
        bpy.ops.object.modifier_apply(modifier=m.name)
    return dict(triangles=tris_of(obj), was=now)


def op_shade(target, smooth=True, sharp_angle=None):
    """Smooth shading, with edges sharper than sharp_angle (degrees) kept hard."""
    obj = get(target)
    activate(obj)
    if smooth:
        bpy.ops.object.shade_smooth()
        if sharp_angle is not None:
            obj.data.set_sharp_from_angle(angle=math.radians(sharp_angle))
    else:
        bpy.ops.object.shade_flat()
    return {}


def op_triangulate(target):
    obj = get(target)
    activate(obj)
    m = obj.modifiers.new("tri", "TRIANGULATE")
    m.quad_method = "BEAUTY"
    bpy.ops.object.modifier_apply(modifier=m.name)
    return dict(triangles=tris_of(obj))


def op_unwrap(target, angle=66.0, margin=0.01):
    """Smart UV project, then pack: every face gets its own place in 0..1."""
    obj = get(target)
    activate(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin)
    bpy.ops.uv.pack_islands(margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")
    return dict(uv_layers=len(obj.data.uv_layers))


def _bake_image(low, name, size):
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color"
    mat = low.data.materials[0]
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    for n in mat.node_tree.nodes:
        n.select = False
    node.select = True
    mat.node_tree.nodes.active = node
    return img


def _pointiness_material():
    mat = bpy.data.materials.new("curvature")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    emit = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(geo.outputs["Pointiness"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def op_bake(high, low, size=1024, maps=("normal", "ao"), cage=0.02, ray=0.1, samples=32, margin=8, prefix="bake"):
    """Bake the high objects onto the low one (which must be unwrapped and triangulated).
    maps: normal (tangent space, +Y: glTF's), ao, curvature (0.5 flat, bright on convex
    edges, dark in creases), emit (the emission of the high objects' materials: a mask)."""
    lo = get(low)
    his = [get(h) for h in high]
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.cage_extrusion = cage
    bake.max_ray_distance = ray
    bake.margin = margin
    out = {}
    saved = None
    for kind in maps:
        t = time.time()
        img = _bake_image(lo, f"{prefix}_{kind}", size)
        if kind == "curvature":
            # swap the material in every slot and put it back afterwards: clearing the slots
            # would reset each face's material index, and a later "emit" bake would see nothing
            saved = [[s.material for s in h.material_slots] for h in his]
            cm = _pointiness_material()
            for h in his:
                for slot in h.material_slots:
                    slot.material = cm
        activate(lo, his)
        scene.cycles.samples = samples if kind == "ao" else 4
        bpy.ops.object.bake(type=dict(normal="NORMAL", ao="AO", curvature="EMIT", emit="EMIT")[kind],
                            use_selected_to_active=True, cage_extrusion=cage, max_ray_distance=ray, margin=margin)
        if kind == "curvature":
            for h, mats in zip(his, saved):
                for slot, m in zip(h.material_slots, mats):
                    slot.material = m
        file = f"{prefix}_{kind}.png"
        img.filepath_raw = str(JOB / file)
        img.file_format = "PNG"
        img.save()
        out[kind] = dict(file=file, seconds=round(time.time() - t, 2))
    return dict(maps=out, size=size)


def op_weights(target, bones):
    """Automatic (bone heat) skin weights. bones: [{name, parent, head, tail}] in cadkit's frame."""
    obj = get(target)
    arm = bpy.data.armatures.new("rig")
    rig = bpy.data.objects.new("rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    activate(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    made = {}
    for b in bones:
        eb = arm.edit_bones.new(b["name"])
        head, tail = to_blender(np.array([b["head"], b["tail"]], float))
        if np.linalg.norm(tail - head) < 1e-4:
            tail = head + [0, 0, 0.02]
        eb.head, eb.tail = head.tolist(), tail.tolist()
        if b.get("parent"):
            eb.parent = made[b["parent"]]
        eb.use_deform = bool(b.get("deform", True))
        made[b["name"]] = eb
    bpy.ops.object.mode_set(mode="OBJECT")
    activate(rig, [obj])
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    obj["bone_order"] = [b["name"] for b in bones]
    grouped = sum(1 for v in obj.data.vertices if any(g.weight > 0 for g in v.groups))
    total = len(obj.data.vertices)
    if grouped < total:
        # Bone heat gives up silently on meshes it cannot solve (parts that cross each other,
        # holes): nothing is weighted. Better an error than a character that does not move.
        raise RuntimeError(f"automatic weights reached {grouped} of {total} vertices; the mesh must be one "
                           "closed skin (remesh it) and every part must be near a bone")
    return dict(vertices=total, weighted=grouped)


def op_save(target, file):
    """The mesh as triangles with split normals and UVs: one output vertex per distinct
    (position, normal, uv), which is what a GPU and glTF want."""
    obj = get(target)
    if any(len(p.vertices) != 3 for p in obj.data.polygons):
        op_triangulate(target)
    me = obj.data
    nl = len(me.loops)
    vi = np.empty(nl, np.int32)
    me.loops.foreach_get("vertex_index", vi)
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    pos = from_blender(co.reshape(-1, 3)[vi])
    nrm = np.empty(nl * 3)
    me.corner_normals.foreach_get("vector", nrm)
    nrm = from_blender(nrm.reshape(-1, 3))
    if me.uv_layers.active:
        uv = np.empty(nl * 2)
        me.uv_layers.active.data.foreach_get("uv", uv)
        uv = uv.reshape(-1, 2)
        uv[:, 1] = 1 - uv[:, 1]
    else:
        uv = np.zeros((nl, 2))
    rows = np.round(np.hstack([pos, nrm, uv]), 6)
    uniq, first, inverse = np.unique(rows, axis=0, return_index=True, return_inverse=True)
    arrays = dict(v=uniq[:, :3], n=uniq[:, 3:6], uv=uniq[:, 6:8], f=inverse.reshape(-1, 3).astype(np.int32))
    order = obj.get("bone_order")
    if order:
        index = {name: i for i, name in enumerate(order)}
        groups = {g.index: index[g.name] for g in obj.vertex_groups if g.name in index}
        src = vi[first]
        joints = np.zeros((len(src), 4), np.int32)
        weights = np.zeros((len(src), 4))
        for k, v_index in enumerate(src):
            ws = sorted(((g.weight, groups[g.group]) for g in me.vertices[v_index].groups if g.group in groups),
                        reverse=True)
            # Four influences per vertex, cut smoothly: take the fifth-largest weight off all of
            # them. Keeping the top four as they are drops a different bone on neighbouring
            # vertices (hips here, an arm there) and the skin tears between them when it moves.
            floor = ws[4][0] if len(ws) > 4 else 0.0
            ws = [(wt - floor, j) for wt, j in ws[:4]]
            total = sum(w for w, _ in ws)
            for c, (wt, j) in enumerate(ws):
                joints[k, c], weights[k, c] = j, wt / total if total > 0 else 0.0
        arrays.update(joints=joints, weights=weights)
    np.savez(JOB / file, **arrays)
    return dict(triangles=len(arrays["f"]), vertices=len(uniq), has_uv=bool(me.uv_layers.active))


OPS = dict(load=op_load, modify=op_modify, boolean=op_boolean, join=op_join, copy=op_copy, remesh=op_remesh,
           decimate=op_decimate, shade=op_shade, triangulate=op_triangulate, unwrap=op_unwrap, bake=op_bake,
           weights=op_weights, save=op_save)


def main():
    job = json.loads((JOB / "job.json").read_text(encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    result = dict(blender=bpy.app.version_string, steps=[], ok=False)
    t0 = time.time()
    try:
        for i, step in enumerate(job["steps"]):
            step = dict(step)
            name = step.pop("op")
            t = time.time()
            info = OPS[name](**step)
            info.update(op=name, seconds=round(time.time() - t, 2))
            result["steps"].append(info)
            log(f"{i} {name} {info}")
        result["ok"] = True
    except Exception as e:                                  # report it; the host raises
        import traceback
        result["error"] = f"step {len(result['steps'])} ({name}): {type(e).__name__}: {e}"
        result["trace"] = traceback.format_exc()[-1500:]
    result["seconds"] = round(time.time() - t0, 2)
    (JOB / "result.json").write_text(json.dumps(result, indent=1), encoding="utf-8")


main()
