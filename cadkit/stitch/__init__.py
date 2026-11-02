"""Generative embroidery: a design script builds a Design (fills, satin columns,
running stitches) from shapely shapes; `cad stitch build` writes an Ink/Stitch-ready
SVG, stitches it (Ink/Stitch headless, or the built-in engine), checks the stitch plan
and writes PES/DST/JEF/EXP/VP3/XXX plus a preview. In a design:

    from cadkit.stitch import *
"""
from .checks import *          # noqa: F401,F403
from .design import Design, HOOPS, DEFAULT_HOOP  # noqa: F401
from .shapes import *          # noqa: F401,F403
from .threads import resolve_color, nearest_brother  # noqa: F401
