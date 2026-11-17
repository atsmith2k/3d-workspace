"""The one glTF writer, and an independent reader for checking what it wrote.

`write_glb` emits only what Cinder 0.1 reads: triangle primitives with POSITION, NORMAL and
TEXCOORD_0, metallic-roughness materials with up to five texture slots, alpha modes,
double-sided, and KHR_materials_emissive_strength. Tangents are left to the engine
(MikkTSpace on import), LODs too.

`summary` reads a GLB back through pygltflib and Pillow, sharing no code with the writer.
"""
import io
import json
import struct

import numpy as np
from PIL import Image

from .texture import to_u8

SUPPORTED_EXTENSIONS = {"KHR_texture_transform", "KHR_materials_emissive_strength"}
SUPPORTED_ATTRIBUTES = {"POSITION", "NORMAL", "TANGENT", "TEXCOORD_0", "TEXCOORD_1",
                        "JOINTS_0", "WEIGHTS_0"}


def _png(img):
    a = to_u8(img)
    buf = io.BytesIO()
    Image.fromarray(a).save(buf, "PNG", optimize=True)
    return buf.getvalue()


class _Bin:
    def __init__(self):
        self.data = bytearray()
        self.views = []

    def add(self, raw, target=None):
        while len(self.data) % 4:
            self.data.append(0)
        view = dict(buffer=0, byteOffset=len(self.data), byteLength=len(raw))
        if target:
            view["target"] = target
        self.data += raw
        self.views.append(view)
        return len(self.views) - 1


def write_glb(model, path, name="asset"):
    """Write a Model as a binary glTF. Returns the number of bytes written."""
    b = _Bin()
    accessors, images, textures, materials, primitives = [], [], [], [], []
    used_ext = set()
    tex_of = {}                                   # id(array) -> texture index
    skeleton = getattr(model, "skeleton", None)

    def accessor(arr, ctype, kind, target, minmax=False):
        a = dict(bufferView=b.add(np.ascontiguousarray(arr).tobytes(), target), componentType=ctype,
                 count=len(arr) if kind != "SCALAR" else arr.size, type=kind)
        if minmax:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
        accessors.append(a)
        return len(accessors) - 1

    def texture(img, label):
        if id(img) not in tex_of:
            images.append(dict(bufferView=b.add(_png(img)), mimeType="image/png", name=label))
            textures.append(dict(source=len(images) - 1, sampler=0))
            tex_of[id(img)] = len(textures) - 1
        return dict(index=tex_of[id(img)])

    prim_node = []                                # node name of each primitive, in order
    for (mesh, mat), node_name in zip(model.parts, getattr(model, "nodes", None) or [None] * len(model.parts)):
        prim_node.append(node_name)
        pbr = dict(baseColorFactor=[float(c) for c in (tuple(mat.color) + (1.0,))[:4]],
                   metallicFactor=float(mat.metallic), roughnessFactor=float(mat.roughness))
        m = dict(name=mat.name, pbrMetallicRoughness=pbr)
        if mat.base is not None:
            pbr["baseColorTexture"] = texture(mat.base, mat.name + "_base")
        if mat.orm is not None:
            t = texture(mat.orm, mat.name + "_orm")
            pbr["metallicRoughnessTexture"] = t
            m["occlusionTexture"] = dict(t)
        if mat.normal is not None:
            m["normalTexture"] = texture(mat.normal, mat.name + "_normal")
        if mat.emission is not None:
            m["emissiveTexture"] = texture(mat.emission, mat.name + "_emissive")
        if any(mat.emissive):
            m["emissiveFactor"] = [float(c) for c in mat.emissive]
            if mat.emissive_strength != 1.0:
                m["extensions"] = {"KHR_materials_emissive_strength":
                                   {"emissiveStrength": float(mat.emissive_strength)}}
                used_ext.add("KHR_materials_emissive_strength")
        if mat.alpha != "opaque":
            m["alphaMode"] = mat.alpha.upper()
            if mat.alpha == "mask":
                m["alphaCutoff"] = float(mat.alpha_cutoff)
        if mat.double_sided:
            m["doubleSided"] = True
        materials.append(m)

        idx = mesh.f.astype(np.uint16 if len(mesh.v) < 65536 else np.uint32).reshape(-1)
        attrs = dict(
            POSITION=accessor(mesh.v.astype(np.float32), 5126, "VEC3", 34962, minmax=True),
            NORMAL=accessor(mesh.n.astype(np.float32), 5126, "VEC3", 34962),
            TEXCOORD_0=accessor(mesh.uv.astype(np.float32), 5126, "VEC2", 34962))
        if skeleton is not None:
            j, w = model.skins[len(primitives)]
            attrs["JOINTS_0"] = accessor(j.astype(np.uint16), 5123, "VEC4", 34962)
            attrs["WEIGHTS_0"] = accessor(w.astype(np.float32), 5126, "VEC4", 34962)
        primitives.append(dict(
            attributes=attrs,
            indices=accessor(idx, 5123 if idx.dtype == np.uint16 else 5125, "SCALAR", 34963),
            material=len(materials) - 1, mode=4))

    # meshes: the asset's own node first, then one per named node
    order = []
    for nn in prim_node:
        if nn not in order:
            order.append(nn)
    order.sort(key=lambda nn: nn is not None)
    meshes = [dict(name=name if nn is None else nn, primitives=[p for p, pn in zip(primitives, prim_node) if pn == nn])
              for nn in order]
    nodes = [dict(mesh=i, name=m["name"]) for i, m in enumerate(meshes)]
    roots, extra = list(range(len(nodes))), {}
    first_bone = len(nodes)
    if skeleton is not None:
        # node 0 carries the mesh and the skin; bone i is node first_bone + i
        for i, bone in enumerate(skeleton.bones):
            node = dict(name=bone.name, translation=[float(x) for x in skeleton.local(i)])
            kids = [k + first_bone for k, c in enumerate(skeleton.bones) if c.parent == i]
            if kids:
                node["children"] = kids
            nodes.append(node)
            if bone.parent < 0:
                roots.append(i + first_bone)
        ibm = np.tile(np.eye(4, dtype=np.float32), (len(skeleton), 1, 1))
        for i, bone in enumerate(skeleton.bones):
            ibm[i, 3, :3] = -bone.head                      # column-major: translation in the last column
        nodes[0]["skin"] = 0
        extra["skins"] = [dict(joints=list(range(first_bone, first_bone + len(skeleton))), skeleton=roots[-1],
                               inverseBindMatrices=accessor(ibm.reshape(-1, 16), 5126, "MAT4", None))]
        anims = []
        for clip in model.clips:
            samplers, channels = [], []
            for target, tracks, kind in (("rotation", clip.rotations, "VEC4"), ("translation", clip.translations, "VEC3")):
                for bone, keys in tracks.items():
                    i = skeleton.index(bone)
                    times = np.array([k[0] for k in keys], np.float32)
                    vals = np.array([k[1] for k in keys], np.float32)
                    if target == "translation":
                        vals = vals + skeleton.local(i).astype(np.float32)
                    t_acc = accessor(times, 5126, "SCALAR", None)
                    accessors[t_acc]["min"], accessors[t_acc]["max"] = [float(times.min())], [float(times.max())]
                    samplers.append(dict(input=t_acc, output=accessor(vals, 5126, kind, None),
                                         interpolation="LINEAR"))
                    channels.append(dict(sampler=len(samplers) - 1, target=dict(node=i + first_bone, path=target)))
            anims.append(dict(name=clip.name, samplers=samplers, channels=channels))
        if anims:
            extra["animations"] = anims

    doc = dict(asset=dict(version="2.0", generator="cadkit.game"),
               scene=0, scenes=[dict(nodes=roots)], nodes=nodes,
               meshes=meshes, materials=materials,
               accessors=accessors, bufferViews=b.views, **extra)
    if textures:
        doc.update(images=images, textures=textures,
                   samplers=[dict(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)])
    if used_ext:
        doc["extensionsUsed"] = sorted(used_ext)
    while len(b.data) % 4:
        b.data.append(0)
    doc["buffers"] = [dict(byteLength=len(b.data))]
    js = json.dumps(doc, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    total = 12 + 8 + len(js) + 8 + len(b.data)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<4sII", b"glTF", 2, total))
        fh.write(struct.pack("<I4s", len(js), b"JSON") + js)
        fh.write(struct.pack("<I4s", len(b.data), b"BIN\0") + bytes(b.data))
    return total


def summary(path):
    """Read a GLB back with pygltflib: counts, bounds, features, texture sizes. Raises on a
    file pygltflib cannot parse."""
    import pygltflib
    g = pygltflib.GLTF2().load_binary(str(path))
    blob = g.binary_blob() or b""
    tris = verts = 0
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    attributes, modes = set(), set()
    for mesh in g.meshes:
        for prim in mesh.primitives:
            modes.add(4 if prim.mode is None else prim.mode)
            attrs = {k: v for k, v in vars(prim.attributes).items() if v is not None}
            attributes |= set(attrs)
            pos = g.accessors[attrs["POSITION"]]
            verts += pos.count
            lo, hi = np.minimum(lo, pos.min), np.maximum(hi, pos.max)
            tris += (g.accessors[prim.indices].count if prim.indices is not None else pos.count) // 3
    images = []
    for im in g.images:
        view = g.bufferViews[im.bufferView]
        off = view.byteOffset or 0
        with Image.open(io.BytesIO(blob[off:off + view.byteLength])) as pic:
            images.append(dict(name=im.name, width=pic.width, height=pic.height, mode=pic.mode))
    comp = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
    width = dict(SCALAR=1, VEC2=2, VEC3=3, VEC4=4, MAT4=16)

    def data(i):
        a = g.accessors[i]
        view = g.bufferViews[a.bufferView]
        off = (view.byteOffset or 0) + (a.byteOffset or 0)
        return np.frombuffer(blob, comp[a.componentType], a.count * width[a.type], off).reshape(a.count, width[a.type])

    skin = None
    if g.skins:
        sk = g.skins[0]
        weight_err, joint_max = 0.0, 0
        for mesh in g.meshes:
            for prim in mesh.primitives:
                if prim.attributes.WEIGHTS_0 is not None:
                    weight_err = max(weight_err, float(np.abs(data(prim.attributes.WEIGHTS_0).sum(1) - 1).max()))
                    joint_max = max(joint_max, int(data(prim.attributes.JOINTS_0).max()))
        skin = dict(joints=len(sk.joints), inverse_bind=g.accessors[sk.inverseBindMatrices].count,
                    weight_sum_error=weight_err, joint_index_max=joint_max,
                    bones=[g.nodes[j].name for j in sk.joints])
    clips = []
    for an in g.animations:
        t_end, sorted_ok, unit_err = 0.0, True, 0.0
        for ch in an.channels:
            smp = an.samplers[ch.sampler]
            times = data(smp.input)[:, 0]
            t_end = max(t_end, float(times.max()))
            sorted_ok = sorted_ok and bool((np.diff(times) > 0).all())
            if ch.target.path == "rotation":
                unit_err = max(unit_err, float(np.abs(np.linalg.norm(data(smp.output), axis=1) - 1).max()))
        clips.append(dict(name=an.name, duration=round(t_end, 4), channels=len(an.channels),
                          times_sorted=sorted_ok, quaternion_error=unit_err))

    return dict(
        skin=skin, clips=clips,
        mesh_nodes=[dict(name=nd.name, primitives=len(g.meshes[nd.mesh].primitives))
                    for nd in g.nodes if nd.mesh is not None],
        triangles=int(tris), vertices=int(verts), primitives=sum(len(m.primitives) for m in g.meshes),
        materials=len(g.materials), textures=len(g.textures), images=images,
        bounds=[lo.tolist(), hi.tolist()], attributes=sorted(attributes), modes=sorted(modes),
        extensions=sorted(g.extensionsUsed or []), skins=len(g.skins), animations=len(g.animations),
        bytes=len(blob))
