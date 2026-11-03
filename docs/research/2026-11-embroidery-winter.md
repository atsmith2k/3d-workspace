# Frost & Fir: 15 Christmas / winter machine-embroidery designs (2026-11-02)

Follows the Harvest Hollow fall collection (`designs/_fall.py`, ten designs). Same
harness (`cad stitch`), same two shop sizes (4x4 at 95 mm, 5x7 at 160 mm), eight
machine formats plus the Ink/Stitch SVG. The shared module is `designs/_winter.py`:
one 19-thread Brother palette, a `product()` helper, `sew_bow` and `holly_sprig`.

## What the market showed

The sources are Etsy listing snapshots and blog trend round-ups. There are no hard
2026 sales figures, so review counts on long-running listings stand in for demand.

- **Character motifs lead the Christmas best-seller pages.** Gnomes (tomte), Santa,
  reindeer, snowmen and nutcrackers fill the first pages of Etsy's Christmas embroidery
  best-seller and top-selling searches.
- **Coquette bows were the 2025 breakout and are still running.** A coquette nativity
  file shows about 6.3k reviews, and coquette nutcracker and coquette tree shirt designs
  are everywhere. Retail trend pieces (Primark, Ideal Home's 2025 decor trends) carry the
  bow trend into Christmas decor.
- **Scandi and folk minimalism**: single-colour snowflakes, folk stars and knit-pattern
  mittens sell to the "winter, not just Christmas" buyer (December to March).
- **Retro / mid-century** trees and baubles, and **wreaths** used as monogram frames,
  sell steadily. So does **lettering** ("Merry & Bright", "Merry Christmas").
- **Multi-size sets are expected.** Listings commonly ship 4x4, 5x7 and 6x10 in one
  purchase. We ship 4x4 and 5x7, each re-stitched rather than scaled.
- **Prices:** singles list at $2.50-$4 and sit on sale at $1.50-$3. Bundles of 6-12 run
  $10-$25. We list at $3.99, with a $12.99 commercial licence, and the collection bundle
  is priced by `cad stitch bundle`.
- **Licensed characters sell hugely but are off-limits.** Griswold / Christmas Vacation
  designs show about 7.1k reviews and Grinch designs are common; none of that is ours to
  sell. The reindeer has a brown nose, so it is not a named character, and the
  nutcracker is a generic toy soldier.

## The fifteen

| # | Design | File | Trend it answers | Colours |
|---|---|---|---|---|
| 1 | Crystal Snowflake | `winter_crystal_snowflake` | Scandi minimal, all-winter | 3 |
| 2 | Nordic Folk Star | `winter_nordic_star` | folk / Christmas jumper | 3 |
| 3 | Holly Wreath | `winter_holly_wreath` | wreath, monogram frame | 4 |
| 4 | Crossed Candy Canes | `winter_candy_canes` | kids, sweets | 4 |
| 5 | Nordic Mittens | `winter_nordic_mittens` | cosy knit, all-winter | 3 |
| 6 | Coquette Bow Tree | `winter_coquette_tree` | coquette bows | 4 |
| 7 | Coquette Bow Ornament | `winter_coquette_ornament` | coquette bows, pearls | 5 |
| 8 | Christmas Gnome | `winter_gnome` | gnome / tomte (top seller) | 7 |
| 9 | Nutcracker Soldier | `winter_nutcracker` | nutcracker | 7 |
| 10 | Snowman | `winter_snowman` | snowman, kids | 6 |
| 11 | Woodland Reindeer | `winter_reindeer` | reindeer, kids | 7 |
| 12 | Cardinal on Holly | `winter_cardinal_holly` | cardinal / memorial bird | 6 |
| 13 | Retro Christmas Tree | `winter_retro_tree` | retro / mid-century | 6 |
| 14 | Gingerbread Man | `winter_gingerbread_man` | baking, kids | 6 |
| 15 | Merry & Bright | `winter_merry_bright` | lettering | 4 |

## Digitising notes from this round

- `shapes.mirror_x` returns the shape **plus** its mirror; for a mirrored copy use
  `scale(g, -1, 1)`. The first mittens build had a two-thumbed right mitten.
- Crossing shapes that both carry satin borders: knock the back one out by about
  1.1 x the border width so the two borders sit side by side rather than stacked
  (stacked, they reached 6.5 layers). Drop the slivers left between a bow and a crossing
  with `knockout(..., min_width=3)`, or their borders pile up into a knot.
- Snowflake side branches sewn as one V per pair (tip to root, root to tip), before the
  arms that cover their roots, cut 34 trims to 22.
- A deliberate open slot between separate elements (berries, branch, tail) can be
  allowed per design with `standard_checks(..., between_mm2=4.0)`.
- `Segoe Script Bold` lettering (as in `indiana_state`) reads at 20 mm cap height as a
  0.35 mm fill; much smaller needs satin lettering.

## Sources

- https://www.etsy.com/market/christmas_embroidery_best_seller
- https://www.etsy.com/market/top_selling_embroidery_design
- https://www.etsy.com/market/embroidery_designs_best_selling
- https://www.etsy.com/market/best_sellers_machine_embroidery
- https://www.etsy.com/market/christmas_embroidery
- https://www.etsy.com/market/machine_embroidered_gift_ideas
- https://www.etsy.com/market/christmas_vacation_machine_embroidery_designs (licensed, avoided)
- https://www.etsy.com/listing/250927371/holly-wreath-embroidery-design-file
- https://ignitewonder.patternbyetsy.com/listing/4413324323/mini-winter-holiday-bundle-embroidery
- https://mygirlfriendsquiltshoppe.com/products/a-very-merry-cupcake-collection-downloadable-machine-embroidery-bundle
- https://practicalembroidery.eu/on-trend-christmas-embroidery-designs-2024/
- https://hatchembroidery.com/resources/blog/snowman-themed-embroidery-project-ideas
- https://www.brooklynhaberdashery.com/blogs/project-ideas/winter-themed-embroidery
- https://cdn-tiapef.primark.com/en-us/a/inspiration/style-trends/bow-trend
- https://www.idealhome.co.uk/all-rooms/christmas-decor-trends-2025
- https://www.walmart.com/ip/16912364082
