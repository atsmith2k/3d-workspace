"""DESCRIPTION_HERE

Spec (fill this in before writing build(); it is the contract the checks enforce):
  object:       what it is and what it is for
  overall:      W x D x H mm, which way is up when printed
  mates with:   anything it must fit (dowel 12.7 mm, M3 screws, a 60 mm jar...) and the
                exact dims used, including the clearance added
  orientation:  which face sits on the bed and why; supports expected: none
  must have:    the features the user asked for, each with a size
  tolerances:   sliding 0.2 mm/side, press 0.1 mm/side, holes +0.2 mm (print undersize)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from build123d import *

from cadkit.checks import *

DESCRIPTION = "DESCRIPTION_HERE"

# Optional, read by `cad publish`: how this model is sold. Every key is optional.
# category "molds" or "parts"; printers it is sliced for; sellable None = let the
# gate decide, True = sell despite caveats, False = never list it.
PRODUCT = dict(
    title=None,                 # default: the model name, title-cased
    category="parts",
    tags=[],
    printers=["a1", "a1mini"],
    cast_material=None,         # molds: "cement", "plaster", "resin"...
    post_processing=None,       # molds: replaces the default release/cure notes
    sellable=None,
)
# LICENSE_NOTES = "..."        # replaces the default licence text in the print notes;
#                              # cite any external design or dimension source here

# Every tunable dimension lives here so it can be changed with --set name=value.
PARAMS = dict(
    width=40.0,
    depth=30.0,
    height=20.0,
    corner_radius=3.0,
)


def checks(p):
    """Acceptance checks run by `cad build`; the build fails if any fails.
    Turn every line of the spec into one: dims, hole, solid/empty, thickness_at..."""
    return [
        dims(x=p.width, y=p.depth, z=p.height),
        flat_base(p.width * p.depth * 0.5),
        no_overhang(),
        single_body(),
    ]


def build(p):
    part = Box(p.width, p.depth, p.height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part = fillet(part.edges().filter_by(Axis.Z), p.corner_radius)
    return part
