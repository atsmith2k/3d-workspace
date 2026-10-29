# Third round: polymer-clay earring cutter sets (2026-10-28)

The first two rounds (`2026-10-shop-expansion.md`, `2026-10-opportunity-areas.md`) were
all casting molds: cement and plaster molds, silicone masters, slip-casting masters and
thermoform bucks. This round deliberately moves to a different buyer group: **polymer-clay
earring makers** (area 6 in the opportunity doc).

## Why this niche

- Repeat demand: earring makers need new shapes every season, and they buy sets.
  MakerWorld "polymer clay cutter" 999+ models (Petal cutters 2k, Daisy donut set 1.8k,
  Heart cutter stamp 1.7k); Etsy sets of 3-6 sizes sell at $4-7 next to $11-23 bundles.
- Low IP risk: all ten shapes are generic motifs drawn here, no characters or brands.
- Toolchain fit: one shared helper (`cadkit/cutter.py`) gives every design the same
  checked blade profile (1.35 / 0.9 mm walls tapering to a 0.45 mm edge), recessed
  imprint blades, support bars and a matching pusher, with a fit check per size.
- Cheap to print: each cutter is ~2-6 g and well under 30 minutes; every part fits the
  A1 mini.

## The 10 listings

| # | Model | Motif | Season | Sizes (mm) |
|---|---|---|---|---|
| 1 | `heart_hoop_clay_cutter` | open heart | Valentine's | 20 / 28 / 36 |
| 2 | `rainbow_arch_clay_cutter` | arch + band imprints | evergreen boho | 20 / 28 / 36 |
| 3 | `daisy_clay_cutter` | daisy donut | spring | 22 / 30 / 38 |
| 4 | `tulip_clay_cutter` | tulip + petal imprints | spring / Easter | 20 / 28 / 36 |
| 5 | `easter_egg_clay_cutter` | egg + zigzag band | Easter | 22 / 30 / 38 |
| 6 | `monstera_leaf_clay_cutter` | split leaf + midrib | evergreen boho | 24 / 32 / 40 |
| 7 | `crescent_moon_clay_cutter` | crescent + star window | evergreen celestial | 24 / 32 / 40 |
| 8 | `teardrop_clay_cutter` | open teardrop | evergreen minimal | 24 / 32 / 40 |
| 9 | `citrus_slice_clay_cutter` | rind + segment imprints | summer | 22 / 30 / 38 |
| 10 | `butterfly_clay_cutter` | butterfly + wing windows | spring | 24 / 32 / 40 |

Suggested price: $3.99 per 3-size set; a "Valentine + spring" bundle (1, 3, 4, 5, 10) at
$12.99. Timing: Valentine's sets live by early January, Easter by mid-February.

## Before listing

- Press a test set in real clay (Sculpey/Fimo, 2-3 mm sheet) and photograph the pieces;
  the harness checks geometry, not how cleanly clay releases.
- The shop maps any category other than `molds` to `parts`; a "Clay cutters" collection
  in ash10-dev-shop (`publish-lib.mts`) would group these properly.
