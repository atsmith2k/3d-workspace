# Hearth & Snow: 20 more winter / holiday machine-embroidery designs (2026-11-02)

The second winter collection, after Frost & Fir (`docs/research/2026-11-embroidery-winter.md`,
15 designs). None of the twenty repeats a Frost & Fir motif. Same harness (`cad stitch`),
same two shop sizes (4x4 at 95 mm, 5x7 at 160 mm), eight machine formats plus the
Ink/Stitch SVG. The shared module is `designs/_hearth.py`: Frost & Fir's 19-thread Brother
palette plus Dark Gray and Orange, so one set of cones covers both collections. Every
design is submitted to the shop as a draft (`PRODUCT["draft"] = True`,
`publish-models.mts --draft`) for review in the admin's Draft Products queue.

## What the market showed

There are still no hard 2026 sales figures. Review counts on long-running Etsy listings
are the best demand signal; retailer "best seller" collections show what shops feature.

- **Christmas truck with a tree is the single strongest motif.** One "Christmas Truck"
  file shows about 13.3k reviews (4.9 stars, Star Seller); Embroidery Library carries
  retro truck variants ("Farm Fresh Christmas Trees"). -> `hearth_tree_truck`.
- **Christmas lights lettering is next.** A "Merry and Bright" lights file shows ~6.8k
  reviews and a "Merry Christmas" lights file ~6.6k. Frost & Fir already has Merry &
  Bright lettering, so this one is "Merry Christmas" under a string of C9 bulbs.
  -> `hearth_christmas_lights`.
- **Hot cocoa** is crowded but steady (mug files with 270-900 reviews); it sells on
  sweatshirts and mug rugs all winter. -> `hearth_hot_cocoa`.
- **Winter (not only Christmas) animals and activities** fill the winter best-seller
  collections at Embroidery Library, Urban Threads and on Etsy: polar bears in scarves,
  penguins in knit hats and skates, ice skates, sleds, snow globes, moose, owls. These
  sell December to March. -> `hearth_polar_bear`, `hearth_penguin`, `hearth_ice_skates`,
  `hearth_sled`, `hearth_snow_globe`, `hearth_moose`, `hearth_snowy_owl`.
- **Classic Christmas motifs** that Frost & Fir lacked: Santa, the stocking (a blank cuff
  for a name, since personalised stockings are a large sub-market), poinsettia (napkins
  and table linen), jingle bells, the gingerbread house. -> `hearth_santa`,
  `hearth_stocking`, `hearth_poinsettia`, `hearth_jingle_bells`,
  `hearth_gingerbread_house`.
- **Hanukkah** designs (menorah, dreidel, Star of David) are common in machine embroidery
  catalogues, for napkins and table runners. A shop with only Christmas designs misses
  that buyer. -> `hearth_menorah`.
- **Rustic / cabin / woodland and minimal winter**: pine boughs and pinecones, log cabins,
  modern pines under a moon. Printful's 2026 trend notes point at retro and quiet,
  tonal designs on sweatshirts. -> `hearth_pinecones`, `hearth_cabin`,
  `hearth_winter_pines`.
- **Winter lettering** that is not tied to Christmas: "Let it snow". -> `hearth_let_it_snow`.
- **Prices** as in Frost & Fir: singles $3.99, commercial licence $12.99.
- **Licensed characters stay out.** No named reindeer, no Grinch, no Christmas Vacation
  quotes; Santa is a generic vintage face.

## The twenty

| # | Design | File | Trend it answers | Colours |
|---|---|---|---|---|
| 1 | Christmas Tree Truck | `hearth_tree_truck` | red truck (top seller) | 6 |
| 2 | Christmas Lights Merry Christmas | `hearth_christmas_lights` | lights lettering | 5 |
| 3 | Hot Cocoa Mug | `hearth_hot_cocoa` | cocoa, mug rugs | 4 |
| 4 | Snow Globe | `hearth_snow_globe` | snow globe | 6 |
| 5 | Polar Bear Cub | `hearth_polar_bear` | winter animal, kids | 6 |
| 6 | Ice Skating Penguin | `hearth_penguin` | winter animal, kids | 6 |
| 7 | Hanging Ice Skates | `hearth_ice_skates` | skating, all-winter | 3 |
| 8 | Vintage Santa Face | `hearth_santa` | Santa | 6 |
| 9 | Christmas Stocking | `hearth_stocking` | personalised stocking | 5 |
| 10 | Poinsettia | `hearth_poinsettia` | floral, table linen | 5 |
| 11 | Hanukkah Menorah | `hearth_menorah` | Hanukkah | 4 |
| 12 | Vintage Sled with Gifts | `hearth_sled` | sled, snow day | 5 |
| 13 | Merry Moose | `hearth_moose` | woodland, cabin | 7 |
| 14 | Pinecones and Pine Bough | `hearth_pinecones` | rustic, farmhouse | 4 |
| 15 | Winter Log Cabin | `hearth_cabin` | cabin, cosy winter | 7 |
| 16 | Gingerbread House | `hearth_gingerbread_house` | baking, kids | 7 |
| 17 | Winter Pines and Moon | `hearth_winter_pines` | minimal, all-winter | 6 |
| 18 | Let It Snow | `hearth_let_it_snow` | winter lettering | 3 |
| 19 | Jingle Bells | `hearth_jingle_bells` | bells, stockings | 6 |
| 20 | Snowy Owl | `hearth_snowy_owl` | winter bird | 7 |

## Digitising notes from this round

- `knockout(fur, scarf)` and then `outline()` of the result runs the satin border round
  the scarf too, on top of the red (3.7-4.0 layers at 5x7). Outline the whole silhouette
  instead and sew the scarf and hat over it (polar bear, Santa's beard).
- Decorations sewn on top of a fill still stack where a satin edge crosses them: knock
  the wall out under eave icing and under window frames (`grow(window, 0.6)`), not just
  under the shape itself (gingerbread house).
- A filled shape's pointed ends (a mug's cocoa rim, an ellipse ending on the mug side)
  pile up where they meet other edges; pull them inside or drop them.
- `motifs.leaf` starts at the origin and points along +Y; turn it by `deg - 90` to aim
  it at `deg`.
- Bows (`motifs.bow`) leave small bare wedges between the loops and the tails; put
  something behind them (bell tops, a holly leaf) or the coverage check flags it.
- Pine needles as one forward zigzag bean run per side of a bough (root, tip, next root),
  broken where they would run under a bow or a bird: cheap, and never back over its
  holes.
- Script lettering at 11 mm cap height came out with hairlines under 1 mm; the house
  `block_text` at 6.5 mm reads cleanly (menorah).
- Several designs passed at 4x4 and failed only at 5x7, where small overlaps scale into
  1-5 mm2 patches over 3.5 layers. Build `--set size=160 --hoop 5x7` before publishing.

## Sources

- https://www.etsy.com/listing/919801369/christmas-truck-machine-embroidery
- https://www.etsy.com/listing/1606118785/christmas-lights-embroidery-design-merry
- https://www.etsy.com/listing/1564724805/merry-christmas-embroidery-design
- https://www.etsy.com/market/hot_cocoa_embroidery
- https://www.etsy.com/listing/4356974409/christmas-hot-cocoa-machine-embroidery
- https://emblibrary.com/collections/winter-bestseller-embroidery-designs
- https://emblibrary.com/design/christmas-trees-retro-truck-stamp-esp85722-1
- https://urbanthreads.com/collections/bestselling-embroidery-designs
- https://urbanthreads.com/products/penguin-in-winter-skating
- https://emblibrary.com/products/snow-day-polar-bear
- https://machineembroiderygeek.com/product/winter-classics-applique-and-embroidery-design-set/
- https://ignitewonder.patternbyetsy.com/listing/4413322601/ice-skates-embroidery-file-digital
- https://royal-present.com/Winter-embroidery-designs-c41322037/
- https://mygirlfriendsquiltshoppe.com/products/festival-of-lights-hanukkah-border-downloadable-machine-embroidery-pattern
- https://www.qualitysewing.com/products/oesd-freestanding-hanukkah-wreaths-embroidery-collection
- https://www.printful.com/blog/christmas-sweatshirt-and-hoodie-design-ideas
- https://practicalembroidery.eu/on-trend-christmas-embroidery-designs-2024/
