# Shop expansion research: 10 new listings (2026-10-28)

Goal: grow shop.ash10.dev from 3 listings (all cement/plaster molds, $2.99) to 13.

## What we looked at

- Etsy search results (20 queries, read through the in-app browser on 2026-10-28; Etsy's
  bot wall started blocking after that, so listing-level sales counts were not collected).
- MakerWorld "concrete mold" search sorted by downloads (free-side demand).
- Secondary sources: seller blogs and keyword tools (weak, used only for context).

## Findings

**1. General STL categories are a race to the bottom.** Fidget toys, flexi/articulated
animals, planters, vases, desk organizers, wall art and Christmas ornaments are dominated by
mega-bundles: "4000+ Flexi Animals" for $2.75, "1200+ Christmas STL" for $6.67,
"200+ Planter STL" for $5.81, "1600TB Ultimate STL Bundle" for $16.25. Most carry
Bestseller / Popular-now badges. A single original file at $3-5 cannot win a search there.

**2. Casting molds are a less crowded niche with higher prices per file.** Digital mold
listings are few and individually priced:

| Listing (digital STL) | Price |
|---|---|
| Ceramic bowl / mug slip-casting mold STL | $10.50 - $14.99 |
| Modular ceramic mold / retro cup master | $16.57 - $20.79 |
| Christmas bell slip-casting master STL | $17.83 - $18.39 |
| Gargoyle silicone mold-making STL kit | $25.00 |
| Mold-master cylinder box pack (silicone housings) | $17.45 |
| Silicone mold for concrete candles (STL) | $5.81 |
| Modular plaster mold set STL | $4.76 |
| Deck block concrete mold STL | $6.18 |

Physical printed molds sell far higher (dog tessellation paver $24, cat paver $14,
menorah silicone molds $75-150), which says buyers value the cast object.

**3. MakerWorld downloads confirm the mold subjects people want** (downloads / boosts-ish
second number): concrete candle & plaster mold 2.5k, casting mold box 1.6k, deck block mold
1.5k, customizable silicone mold container 1.1k, twisted planter mold system 634,
tea light candle mold 534, flowerpot + saucer mold 236, soap dish 111, lamp base 131.

**4. Timing.** It is late October. Christmas listings are the ones flagged "Popular now"
across every query, and Hanukkah 2026 starts at sundown on 4 Dec. There is a clear gap for
a **menorah mold STL**: printed menorah STLs exist ($2-8), and physical silicone menorah
molds sell for $75-150, but no menorah casting-mold STL showed up.

**5. Concrete / Jesmonite homeware is steady**, with cement trays and cement decor called out
as rising Etsy searches (undated trend quote) and Jesmonite classes still common.

## Niche

**Print-ready casting molds for small cement, plaster and Jesmonite homeware.**
It extends the existing catalogue (3 molds), uses the toolchain's strength (drafted relief
molds, checked and test-sliced), avoids the bundle-saturated categories, and supports a
higher price than $2.99. Every mold prints in one piece on an A1 mini, opening up, no
supports, and the buyer pours straight into it (no silicone step needed).

## Shortlist: 10 listings

| # | Listing | Model file | Why |
|---|---|---|---|
| 1 | Fluted tealight holder mold | `candle_holder_mold` (shape=fluted) | tealight molds 534 dl; fluted is the current look |
| 2 | Faceted hex tealight holder mold | `candle_holder_mold` (shape=hex) | geometric concrete is evergreen |
| 3 | Taper candle holder mold | `candle_holder_mold` (candle=taper) | Christmas tables; same model |
| 4 | Hanukkah menorah mold | `menorah_mold` | clear gap, dated demand (4 Dec) |
| 5 | Faceted Christmas tree mold | `christmas_tree_mold` | Christmas is "Popular now" everywhere |
| 6 | Snowflake ornament mold (plaster) | `snowflake_ornament_mold` | ornament demand without bundle competition |
| 7 | Ribbed trinket tray / ring dish mold | `trinket_tray_mold` | cement trays called out as rising |
| 8 | Incense stick holder mold | `incense_holder_mold` | incense holders sell as STLs; cement version is new |
| 9 | Mini planter + saucer mold | `planter_mold` | flowerpot molds 236-634 dl |
| 10 | Hexagon coaster mold (Jesmonite/terrazzo) | `hex_coaster_mold` | pairs with the oak leaf coaster |

Suggested price: $3.99-5.99 single, and a "holiday casting set" bundle (1-6) once listed.

## Progress

| # | Model | Status | Mold size | A1 print, PLA |
|---|---|---|---|---|
| 1 | `candle_holder_mold` | built, sliced | 84 x 84 x 43 | 5h 37m, 49 g |
| 2 | `candle_holder_mold --set shape=hex` | built, sliced | 83 x 73 x 43 | 4h 54m, 43 g |
| 3 | `candle_holder_mold --set candle=taper` | built, sliced | 65 x 65 x 51 | 4h 11m, 37 g |
| 4 | `menorah_mold` | built, sliced (A1 + mini) | 177 x 39 x 41 | 7h 56m, 70 g |
| 5 | `christmas_tree_mold` | built, sliced | 66 x 66 x 103 | 4h 52m, 42 g |
| 6 | `snowflake_ornament_mold` (4 designs) | built, sliced | 142 x 142 x 9 | 8h 57m, 79 g |
| 7 | `trinket_tray_mold` | built, sliced | 107 x 107 x 23 | 5h 29m, 47 g |
| 8 | `incense_holder_mold` | built, sliced | 128 x 81 x 25 | 5h 15m, 46 g |
| 9 | `planter_mold` (cup + core) | built, sliced | 86 x 86 x 78 / 91 x 91 x 68 | 8h 11m + 7h 47m, 140 g |
| 10 | `hex_coaster_mold` | built, sliced | 121 x 107 x 13 | 3h 51m, 34 g |

All fit the A1 mini, print without supports, and are in `cad selftest`. None has been
test-cast yet. The planter shipped as fluted (with a saucer left for later), not plain.
