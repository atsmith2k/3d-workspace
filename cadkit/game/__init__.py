"""Game assets for the Cinder engine: `from cadkit.game import *` in an asset script.

Metres, Y up, -Z forward. See `cad game schema` for the contract and conventions, and
docs/agents/game-assets-playbook.md for judgement.
"""
import numpy as np                                                    # noqa: F401

from .model import Mesh, Material, Model, merge                       # noqa: F401
from .mesh import (box, block, bevel_box, wedge, prism, lathe, disc, cylinder, torus,   # noqa: F401
                   flat, box_uv, to_game, volume, ball, along, capsule)
from .texture import (noise, fbm, streaks, blur, normal_from_height,  # noqa: F401
                      occlusion_from_height, orm, tint, seam_error, noise3, fbm3,
                      texel_maps, fill_background)
from .checks import (size, tris, materials, texture_size, pivot, tiles, custom, uv_unique,   # noqa: F401
                     clips, phase_matched, deforms_cleanly)
from .rig import Skeleton, Clip, Character, biped, humanoid, SOCKETS, biped_gait, quat, euler, qmul   # noqa: F401
from .matlib import stone_blocks, flagstones, planks, iron, palette, swatch_uv           # noqa: F401

# What `from cadkit.game import *` gives an asset script: names, not submodules. Without this a
# script that defines no checks() would pick up the `checks` module and the build would call it.
__all__ = [n for n, v in list(globals().items())
           if not n.startswith("_") and not isinstance(v, type(np)) or n == "np"]
