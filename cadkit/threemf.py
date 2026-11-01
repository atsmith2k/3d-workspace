"""A plain, unsliced 3MF of a mesh: the model in millimetres and nothing printer-specific, so it
opens in any slicer. Written by hand rather than
through trimesh, whose 3MF exporter needs networkx; the bytes are deterministic (fixed zip
timestamps, fixed number formatting), so the same mesh always gives the same file and sha256."""
from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import trimesh

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)
RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>"
)
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def _num(v: float) -> str:
    s = f"{v:.5f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def model_xml(mesh: trimesh.Trimesh, name: str) -> str:
    v = np.asarray(mesh.vertices, dtype=float)
    f = np.asarray(mesh.faces, dtype=np.int64)
    verts = "".join(f'<vertex x="{_num(x)}" y="{_num(y)}" z="{_num(z)}"/>' for x, y, z in v)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
    safe = name.replace("&", "and").replace("<", "").replace(">", "").replace('"', "")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{safe}</metadata>'
        f'<resources><object id="1" name="{safe}" type="model"><mesh><vertices>{verts}</vertices>'
        f"<triangles>{tris}</triangles></mesh></object></resources>"
        '<build><item objectid="1"/></build></model>'
    )


def write_3mf(mesh: trimesh.Trimesh, path: Path, name: str) -> Path:
    path = Path(path)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for arc, text in (("[Content_Types].xml", CONTENT_TYPES), ("_rels/.rels", RELS), ("3D/3dmodel.model", model_xml(mesh, name))):
            info = zipfile.ZipInfo(arc, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, text)
    return path


def stl_to_3mf(stl: Path, out: Path | None = None) -> Path:
    """`<stem>.3mf` beside the STL (or at `out`), from the STL's mesh."""
    stl = Path(stl)
    mesh = trimesh.load(stl, force="mesh")
    return write_3mf(mesh, out or stl.with_suffix(".3mf"), stl.stem)
