# Fourth round: holiday + evergreen polymer-clay cutter sets (2026-10-28)

Follows `2026-10-clay-cutters.md` (round 3: spring, Easter, boho and celestial sets).
Same buyer group, same `cadkit/cutter.py` blade/pusher system, ten new shapes.

## What the market showed

- **Holiday shapes are the biggest seasonal sellers** and earring makers buy them
  6-8 weeks ahead, so late October is the right time to list for Christmas. Paid STL
  listings on Thangs offer a gingerbread man in 4 sizes and a Christmas tree in 5 sizes.
  Etsy sells 3-size gingerbread-house sets, and Printables has free tree and ornament
  cutters for necklaces and earrings. A MakerWorld 19-cutter Christmas set (snowman,
  sock, wreath) advertises 0.4 mm edges, the same blade-edge spec as ours.
- **Snowflakes** sell as physical plunger/stamp sets (PME 3-pack, MyClayCo snowflake
  wreath). Few printable 3-size snowflake sets exist, which leaves an opening.
- **Evergreen shapes** still dominate Etsy listings: arches and half-circles, circles and
  scallops, florals and leaves, and novelty/kawaii shapes. Sculpey's own trend notes
  call bold geometric shapes "on trend". Scalloped U-arches sell at about $3.90 each.
- Amazon search volume for "polymer clay cutters" ran at about 2.2k a week in July
  2026, and earring search interest peaks in February.

Sources: Etsy listings 1565543962 and 1346873721 (gingerbread house sets), Thangs mf3ddesigns
tree/gingerbread STLs, Printables models 667756 and 661487, MakerWorld 1930550, MyClayCo
snowflake wreath, Sculpey Soufflé color-block earrings, asinsight polymer-clay-cutters report.

## The 10 listings

All are generic motifs drawn here (no characters, brands or copied outlines), each a
3-size set with a pusher per size, A1 and A1 mini.

| # | Model | Motif | Season | Sizes (mm) |
|---|---|---|---|---|
| 1 | `christmas_tree_clay_cutter` | 3-tier tree, garland imprints | Christmas | 24 / 32 / 40 |
| 2 | `snowflake_clay_cutter` | branched snowflake, hex window | winter | 24 / 32 / 40 |
| 3 | `gingerbread_house_clay_cutter` | house, 3 windows, icing + door imprints | Christmas | 24 / 32 / 40 |
| 4 | `ornament_bauble_clay_cutter` | bauble, punched jump-ring hole, zigzag bands | Christmas | 22 / 30 / 38 |
| 5 | `mitten_clay_cutter` | mitten, ribbed cuff | winter | 22 / 30 / 38 |
| 6 | `candy_cane_clay_cutter` | cane, stripe imprints | Christmas | 24 / 32 / 40 |
| 7 | `holly_leaf_clay_cutter` | spiky leaf, midrib + veins | Christmas | 24 / 32 / 40 |
| 8 | `scalloped_circle_clay_cutter` | 12-scallop donut | evergreen | 22 / 30 / 38 |
| 9 | `cloud_clay_cutter` | 4-puff cloud | evergreen kawaii | 22 / 30 / 38 |
| 10 | `mushroom_clay_cutter` | toadstool, 3 spot windows, gill line | fall / cottagecore | 22 / 30 / 38 |

Suggested price: $3.99 per set. Bundle ideas: a "Christmas" bundle (1, 3, 4, 6, 7) at $12.99 and
a "Winter" bundle (2, 5 + round 3's crescent moon) at $8.99. List the holiday sets now,
then switch the featured slot to the Valentine/spring sets from round 3 in early January.

## Before listing

- Press a test set in real clay; check the bauble's 22 mm hole punch releases its plug
  (at that size the hole is about 2.4 mm, nearly a solid pin) and that the mitten's cuff ribs
  don't tear thin clay.
- The new `prism()` guard in `cadkit/cutter.py` turns a hole narrower than its blade into a
  solid punch instead of an invalid mesh.
