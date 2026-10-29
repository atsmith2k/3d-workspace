# Fifth round: 15 more polymer-clay cutter sets (2026-10-28)

Follows `2026-10-clay-cutters.md` (round 3, 10 spring/boho sets) and
`2026-10-clay-cutters-holiday.md` (round 4, 10 winter/evergreen sets). That gives a
21-set baseline including the original pumpkin cutter. This round fills the seasons
and styles the catalogue still lacks: Valentine's, summer/beach and modern geometric.

## What the market showed

- **Valentine's is the next buying window** (clay-earring search interest peaked in
  February 2026). On Etsy, lips cutters sell at about $3.60 as Star Seller listings. 12 mm
  Valentine's mini stud sets sell at about $16, and paid STL series sell numbered
  "Valentine Heart" variants in 4-5 sizes. Our only heart so far was the open hoop.
- **Fruit and food novelty** shapes (cherries, strawberry with leaf, lemon) appear as
  single-shape listings and free Cults3D/MakerWorld files. Cherry cutters are scarce,
  which leaves an opening.
- **Beach/ocean sets** (shells, starfish, seahorse) sell as 12-shape physical sets with
  0.4 mm 3D-printed edges, so our 0.45 mm edge is on spec. Sun and cactus cutters sell
  both as earring cutters and as coaster/ring-dish sizes.
- **Geometric and organic series** are the steadiest paid STLs: numbered
  "Geometric 03/04/05/10" and "Organic Shape" cutters in 5-6 sizes, and "modern
  minimalist" sets. Sculpey's trend notes put bold geometric shapes on trend, and the
  scalloped U-arch sells at $3.90 each.

Sources: Etsy listings 1350074649 and 1328681713 (lips), 4348171950 (Valentine's mini set),
Thangs mf3ddesigns Valentine Heart / Geometric / Organic Shape / Unique Shape series, Cults3D
strawberry and starfish files, MakerWorld 1250949 (shell), Etsy 1138847469 (sun/cactus), Sculpey
color-block earrings.

## The 15 listings

All are generic motifs drawn here, each a 3-size set with a pusher per size, A1 and A1 mini.

| # | Model | Motif | Season | Sizes (mm) |
|---|---|---|---|---|
| 1 | `lips_clay_cutter` | lips, mouth-line imprint | Valentine's | 24 / 32 / 40 |
| 2 | `cherry_clay_cutter` | cherry pair, stem window | Valentine's / summer | 24 / 32 / 40 |
| 3 | `strawberry_clay_cutter` | strawberry, calyx imprint | Valentine's / summer | 22 / 30 / 38 |
| 4 | `scalloped_heart_clay_cutter` | scalloped heart donut | Valentine's | 22 / 30 / 38 |
| 5 | `love_letter_clay_cutter` | envelope, flap imprint, heart seal | Valentine's | 22 / 30 / 38 |
| 6 | `seashell_clay_cutter` | scallop shell, rib imprints | summer | 24 / 32 / 40 |
| 7 | `starfish_clay_cutter` | starfish, arm grooves | summer | 24 / 32 / 40 |
| 8 | `sun_clay_cutter` | sun, face-ring imprint | summer / celestial | 22 / 30 / 38 |
| 9 | `cactus_clay_cutter` | potted saguaro, ribs | summer / boho | 24 / 32 / 40 |
| 10 | `honeycomb_hexagon_clay_cutter` | hexagon donut | evergreen geometric | 22 / 30 / 38 |
| 11 | `organic_pebble_clay_cutter` | freeform pebble, organic window | evergreen modern | 24 / 32 / 40 |
| 12 | `scalloped_arch_clay_cutter` | scalloped U-arch, inner arch line | evergreen boho | 24 / 32 / 40 |
| 13 | `puffy_star_clay_cutter` | rounded star | celestial / Christmas / July 4 | 22 / 30 / 38 |
| 14 | `ginkgo_leaf_clay_cutter` | ginkgo leaf, veins | fall / botanical | 24 / 32 / 40 |
| 15 | `bumblebee_clay_cutter` | bee, wing windows, stripes | spring / summer | 22 / 30 / 38 |

Suggested price: $3.99 per set. Bundles: "Valentine's" (1-5) at $14.99, "Beach day" (6-9)
at $12.99, "Modern geometric" (10-13 + round 3's teardrop) at $14.99.

## Lessons for the next round

- A rounding pass (`grow(+r)` then `grow(-r)`) fills a narrow V-notch by r / sin(half-angle).
  The ginkgo's first 10-degree notch filled about 7 units, which left the centre vein as a
  loose second body at 40 mm. Keep notches at 30 degrees or wider, and run imprint lines
  past the outline so the helper's clip always joins them to the blade.
- Shapes whose stems or arms enclose a gap (cherries) need the gap as an explicit
  cutout. `cherry_clay_cutter` takes the outer contour and subtracts the shape.
- Imprints that don't reach the outline (sun ring) are held by a support bar crossing them.
