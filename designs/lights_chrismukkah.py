"""Merry Chrismukkah: a green Christmas tree topped with a gold Star of David, hung with
blue and silver baubles, over "MERRY CHRISMUKKAH".

Spec:
  object:       interfaith holiday design for sweatshirts, pyjamas, totes, tea towels, pillows
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      ginger (trunk), green (tree), sky (baubles), silver (baubles), gold
                (Star of David topper, garlands), navy (lettering): 6 colours
  must have:    a three-tier green tree 50 mm wide and 46 mm tall on a 7 mm trunk; a gold
                six-pointed Star of David topper 16 mm across in place of a star; three
                sky-blue and three silver 6.4 mm baubles; two 1.4 mm gold satin
                garlands sagging between them, ending 2 mm inside the edge; "MERRY" (7.5 mm
                cap) over "CHRISMUKKAH" (8 mm cap) in the house block lettering, 0.35 mm rows
  density:      baubles and the star knock out the tree; the garlands lie on the tree (2.7
                layers); max 3.5
"""
from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Christmas tree topped with a gold Star of David over Merry Chrismukkah"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Merry Chrismukkah Embroidery Design",
    "A Christmas tree topped with a gold Star of David and \"Merry Chrismukkah\"",
    ["chrismukkah", "merry chrismukkah", "interfaith holiday", "christmas tree",
     "star of david", "hanukkah christmas", "interfaith family"],
    "A little green Christmas tree hung with blue and silver baubles and topped with a gold "
    "Star of David instead of a star, over \"Merry Chrismukkah\" in navy block letters: one "
    "design for households that celebrate both.\n\nGreat on sweatshirts, family pyjamas, "
    "totes, tea towels and pillows.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 12000)


# tiers: (top y, bottom y, half width at the bottom)
TIERS = [(36.0, 18.0, 14.0), (26.0, 6.0, 19.5), (14.0, -8.0, 25.0)]


def art():
    d = Design()
    tiers = []
    for top, bot, hw in TIERS:
        tiers.append(poly([(0, top), (hw, bot), (hw * 0.55, bot + 1.8), (-hw * 0.55, bot + 1.8),
                           (-hw, bot)]))
    tree = union(*tiers).buffer(-1.2).buffer(1.2)
    trunk = rect(7, 7, 0, -10.5)
    sx, sy = 0.0, 40.5
    star_ = star(6, 8.0, 8.0 / 3 ** 0.5, sx, sy).buffer(-0.3).buffer(0.3)
    sky = [(-7.5, 20.5), (9.5, 8.5), (-14.0, -2.5)]
    silver = [(5.0, 21.0), (-8.5, 8.0), (13.5, -3.0)]
    baubles = [(circle(x, y, 3.2), "sky") for x, y in sky] + [(circle(x, y, 3.2), "silver") for x, y in silver]
    merry = move(centered(block_text("MERRY", cap=7.5, stroke=2.4)), 0, -24)
    chris = move(centered(block_text("CHRISMUKKAH", cap=8.0, stroke=2.4)), 0, -38)
    over = union(star_, *[b for b, _ in baubles])
    d.fill(knockout(trunk, tree), C_["ginger"], angle=90, name="trunk")
    d.fill(knockout(tree, over), C_["green"], angle=60, name="tree")
    for c in ("sky", "silver"):
        for b, bc in baubles:
            if bc == c:
                d.fill(b, C_[c], angle=45 if c == "sky" else 135, name=f"{c} bauble")
    for (y, hw, sag) in ((14.5, 9.6, 2.6), (2.0, 11.4, 3.0)):
        d.satin(bezier((-hw, y), (-hw / 3, y - sag), (hw / 3, y - sag), (hw, y), 24), 1.4,
                C_["gold"], name="garland", trim_after=True)
    d.fill(star_, C_["gold"], angle=0, name="Star of David")
    d.fill(merry, C_["navy"], angle=0, spacing=0.35, name="Merry")
    d.fill(chris, C_["navy"], angle=0, spacing=0.35, name="Chrismukkah")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
