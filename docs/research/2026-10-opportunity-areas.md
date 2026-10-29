# Opportunity areas for the next listings (2026-10-28)

Follow-up to `2026-10-shop-expansion.md` (which picked cement/plaster casting molds and
built 10 of them). This round widens the search: where does paid STL/3MF demand outrun
good supply, and what can this toolchain make and check well?

## Method and what could not be read

All observations are from **2026-10-28**.

| Source | What was read | Status |
|---|---|---|
| MakerWorld | ~35 keyword searches sorted by all-time downloads (plus one sorted by trending), in the in-app browser | Loaded fine. Numbers below are *downloads / boosts-or-likes* as shown on the card |
| Etsy | 13 searches (digital-download STL listings, prices, badges) | Loaded fine this time. Stopped at 13 to stay polite; no listing-level sales counts were collected |
| Printables | `printables.com/model?q=...` | **Blocked**: Cloudflare "Performing security verification" page. Not retried |
| Cults3D | `cults3d.com/en/search?...` | **Blocked**: same Cloudflare challenge. Not retried |
| Reddit | `old.reddit.com` | The browser pane refuses reddit.com; web search did not surface Reddit threads. Forum signal comes from other forums instead (BassResource, Ceramic Arts Daily, maker blogs) |
| Google Trends | not reachable without an interactive session | Skipped; no trend numbers in this doc |

So: MakerWorld = free-side demand (what people download), Etsy = paid-side supply and
price. There is no direct paid-sales data here; treat every "demand" claim as "people
download this a lot for free and several shops charge $X for it".

MakerWorld search links (all sorted by downloads unless noted):
`https://makerworld.com/en/search/models?keyword=<term>&orderBy=downloadCount`.
Etsy links: `https://www.etsy.com/search?q=<term>`. The specific terms are given per area.

## The ranked shortlist

| Rank | Area | Paid price band seen | Competition | IP risk | Toolchain fit |
|---|---|---|---|---|---|
| 1 | Silicone-mold masters for candle and wax makers | $6-24 single | Moderate, single shops, few bundles | Low (avoid character freshies) | Excellent |
| 2 | Soft-plastic fishing bait molds (open pour) | $9-23 single | Thin on Etsy, good free supply | Medium (named commercial baits) | Good, needs a test pour |
| 3 | Ceramic slip-casting masters | $10.50-20.79 single | Thin; MakerWorld almost empty | Low | Good (multi-part fit is a strength) |
| 4 | Seasonal casting molds: Valentine's, Easter, Mother's Day | $4-7 (cement molds, last round) | Thin for molds; bundles for printed decor | Low | Excellent (existing pipeline) |
| 5 | Thermoforming (vacuum-forming) bucks | ~$2 (one Etsy listing) | Free side busy, paid side empty | Low | Excellent, but low price |
| 6 | Polymer-clay cutter sets (seasonal, original motifs) | $4-23 per set | Crowded, mixed singles and bundles | Low (avoid characters) | Excellent (pumpkin cutter exists) |
| 7 | Fingerboard deck molds and shapers (watch) | $6.60-8.99 | Thin | Low | Good |

Rejected after looking (details at the end): Gridfinity, brand-specific tool storage
(Packout), board-game inserts, texture rollers, functional replacement parts, tabletop
terrain, aquarium/garden/beekeeping accessories, purge-waste ("poop") molds.

---

### 1. Silicone-mold masters and housings for candle, wax-melt and resin makers

Buyers print a master (the positive) and a housing, pour silicone, and then make candles
or wax melts to sell. The same people buy physical silicone candle molds for $11-39.

**Evidence of demand**
- MakerWorld "silicone mold master": 260 models. Adjustable Silicone Mold Casing Kit 2.7k /
  2.1k, Silicone Mold Box Configurable 1.5k / 976, Customizable Silicone Mold Container
  1.1k / 1.1k, Master mold for geometric candles 925 / 1.5k (likes > downloads: people
  save it).
- MakerWorld "candle mold": 712 models. Candle Mold Customizable 7.5k / 7.8k, Mold for
  Twisted Candle 1.3k, Mold for christmas tree candle 1.3k, Mold for Wax Candle 1k.
- Etsy "candle mold stl" shows physical silicone pillar molds at $11.90-39 with a
  Bestseller badge on a $39 one, which is what a candle maker would otherwise pay.

**Supply and price (Etsy, digital)**
- "silicone mold master stl": Mold Master Cylinder Box pack $17.46 (ThinkerSupply, also
  advertised), Complete Cylinder Mold Housing bundle $23.99, Mold Master Box $7.21,
  Alphabet master $5.21, Faceted candle-jar master with core $6.99, Spanish intention
  candle masters (10) $10.48, Bubble alphabet masters $12.51.
- "freshie mold stl": housings $6-12 single, a $70 "lifetime access" housing library, a
  Bestseller "custom STL from your SVG" at $4.50. Many freshie listings are characters
  (Grinch bundles, "Green Guy inspired") — IP that we stay away from.
- Takeaway: housings are becoming bundled ($10-24 for dozens); **masters of attractive
  candle shapes are still sold one by one at $6-14**, and few shops offer a matched
  master + housing + pour guide.

**IP risk**: low for geometric/botanical candle shapes and blank housings. High for
freshies of characters, sports logos and car brands (most of that market): skip those.

**Toolchain fit**: excellent. Masters are revolved or drafted solids (build123d or
manifold `tapered`), housings are `shell_box`-type parts with registration keys, and the
multi-part `assembly` check reports the master-to-housing gap. Masters print upright on
their base, housings print open-side up: no supports. Checks: `dims`, a gap check
(silicone wall thickness ≥ 8 mm everywhere), `flat_base`. A `casting(p)` render of the
candle sells the listing, as with the cement molds. Fits the A1 mini.
Caveat: layer lines transfer into silicone. Offer a 0.12 mm "Fine" 3MF alongside the
0.20 mm one and say so in the print notes.

**First products**
1. Ribbed pillar candle master + 2-part housing: candle 70 mm dia x 90 mm, 24 ribs,
   housing leaves 10 mm silicone wall.
2. Bubble cube candle master (3x3 spheres) + housing: 60 mm cube.
3. Twisted taper candle master: 22 mm base, 250 mm long, split in two for the mini.
4. Geometric (faceted) pillar trio: 50/60/70 mm dia, one housing that adjusts.
5. Wax-melt clamshell master: 6-cavity tray, 30 x 30 x 15 mm cavities, botanical
   reliefs — fits the relief toolchain exactly.

---

### 2. Soft-plastic fishing bait molds (open pour)

**Evidence of demand**
- MakerWorld "soft bait mold": 351 models. Power-bait Mold Customizable 3k / 1.9k,
  Soft Lure Shad Mold 2.6k / 1.7k, Nays VNM Style 12 cm 1.8k / 2k (also in the "mold"
  trending list), Double tail twister 1.7k, 15 cm Open Pour Swim Bait 1.7k, Kraken Shad
  1.2k / 1k, plus a dozen more at 600-1,000. It surfaced unprompted in a generic
  "slip casting mold" search, ahead of most casting molds.
- Forums: BassResource has long threads on 3D-printed lures and molds
  ([127634](https://bassresource.com/bass-fishing-forums/topic/127634-3d-printing-lures),
  [223363](https://bassresource.com/bass-fishing-forums/topic/223363-3d-printing-and-fishing)).
- Physical molds sell high: aluminium/printed bait molds on Etsy at $35-375, a
  Bestseller urchin mold at $40.

**Supply and price (Etsy "soft bait mold stl")**: digital molds at $9.26, $9.90, $10,
$10, $13.50, $20, $23.28; one outlier at $157 and one at $4.99. About a dozen distinct
shops, almost all single files. That is thin supply at a healthy price.

**IP risk: medium, manageable.** Many popular files are copies of named commercial baits
("Nays VNM style", "Ricky style", "Senko 6 inch", "Coike style"). Senko is a Gary
Yamamoto trademark and the shapes are their products. We would sell only generic forms
(paddle-tail shad, curly-tail grub, stick worm, craw, tube) with our own proportions,
never "X-style" names.

**Toolchain fit**: good. An open-pour mold is a flat block with cavities on top: prints
cavity-up, no supports, flat base, and `empty()` / `solid()` checks confirm each cavity
and the wall between them. Cavities are sized by the bait (the toolchain can model the
bait first and subtract it, then render the bait as the `casting`).
Risks to state plainly in the listing and notes:
- Plastisol pours at ~150-175 °C. Makers report PLA molds work if left to cool between
  pours ([plasticranger](https://plasticranger.com/how-to-make-soft-plastic-lure-molds/),
  [MakerWorld 2326149](https://makerworld.com/models/2326149) recommends resin or ASA
  for heavy use). Ship a PETG 3MF (`--filament "Bambu PETG Basic"`) and say "let it cool".
- Detail like scales or gill lines is at the edge of FDM; keep features ≥ 0.8 mm and
  sell the smooth look.
- **We have not poured one.** Do one test pour before listing.
- Timing: anglers buy for spring; list by February.

**First products**
1. Paddle-tail shad, 75 mm (3 in), 5 cavities, open pour: ~120 x 90 x 15 mm block.
2. Curly-tail grub, 65 mm (2.5 in), 6 cavities: ~110 x 80 x 12 mm.
3. Stick worm, 125 mm (5 in), 4 cavities: ~150 x 70 x 15 mm.
4. Micro shad set, 35/42/50 mm, 5 cavities each (panfish/LRF): one plate per size.
5. Two-part (clamshell) paddle tail 100 mm with pour channel and alignment pins — a
   second step, once the open pour is tested.

---

### 3. Ceramic slip-casting masters (for plaster molds)

The buyer prints a positive and a mold frame, casts plaster around it, then slip-casts
ceramics in the plaster. Higher skill, higher price.

**Evidence**
- Etsy "slip casting mold stl": coffee mug $14.99, prism cup $16.90, band cup $12.81,
  ceramic bowl $10.50 (from $15), Christmas bauble $17.83, retro tapered cup 3-part
  $20.79, modular mold $16.57, low stackable mug 3-part $18.00, mug $10.49, sinuous bowl
  $13.97, Christmas bell $18.39, 2-valve Christmas ball $19.79. About ten distinct shops,
  all single files at $10-21. Custom design services at $84-450 and several Fiverr gigs
  for 3D-printable plaster molds show people pay to have this designed.
- MakerWorld "slip cast" returns 150 models, almost none relevant, most under 500
  downloads (Slip cast pot 426, "slip casting mold" 54, Round Plate Master Mold 25). The
  best is Old Forge Creations' bauble moulds (848 and 628 downloads). **Free supply is
  nearly empty**, so a buyer who wants one has to pay.
- Practice notes (Ceramic Arts Daily
  [topic 37386](https://community.ceramicartsdaily.org/topic/37386-3d-printing-for-plaster-molds/),
  [topic 12384](https://community.ceramicartsdaily.org/topic/12384-3d-printer-to-make-master-mould/)):
  PLA releases from plaster; layer lines transfer, so masters are printed so the lines
  run around the form and are then sanded.

**IP risk**: low (generic vessel forms).

**Toolchain fit**: good, and a differentiator. build123d revolves give exact profiles;
the parting line, natches (keys), spare (pour reservoir) and mold frame are exactly the
multi-part fit work the harness checks (`assembly` gap/interference). A `shrinkage`
parameter (typ. 10-14 %) scales the master so the fired piece hits the size on the
label. Masters print upright, no supports. Size: a 300 ml mug master is ~90 x 90 x 110 mm,
fine on the mini. Not checkable automatically: how well it casts. Sell to people who
already slip-cast and write a short, accurate pour guide.

**First products**
1. Straight-sided mug master, 300 ml fired, 3-part mold frame with natches and spare.
2. Bud vase master, 140 mm fired, 2-part.
3. Ribbed tumbler/cup set, 3 heights (fits the "fluted" look that sold the candle molds).
4. Small bowl master, 120 mm dia, 1-part drop-out mold (easiest first cast).
5. Ornament bauble master, 70 mm, 2-part — for next Christmas, listed by September.

---

### 4. Seasonal casting molds for the next 3-6 months

Extends the catalogue that already exists, using the same pipeline and listing style.

**Dates**: Valentine's Day Sun 14 Feb 2027; Easter Sun 28 Mar 2027; US Mother's Day
Sun 9 May 2027; graduation season May-June. Makers buy molds 4-8 weeks earlier, so
Valentine's molds should be live by early January, Easter by mid-February.

**Evidence**
- Seasonal free demand is huge but is printed decor, not molds: MakerWorld "valentine"
  top items 23k-70k downloads (articulated heart, roses); "easter" 27k-107k; "mother's
  day" 20k-66k. Etsy "valentine mold stl" is the same bundle pattern ("300+ Valentine
  STL" $12.08, "20+ Valentines" $3.96) — avoid printed decor.
- Molds for the same holidays are thin: MakerWorld "heart mold" (762) is mostly cookie
  cutters; the casting entries are Molds for Casting 2k, Mini Hearts Silicone Mold 696,
  Bath Bomb Heart 621. "egg mold" (443): Mold for Easter Egg Candle 344, Dragon Egg
  Chocolate Mold 323. No cement heart dish or egg planter molds near the top.
- Etsy Mother's Day mold listings found: a "40 mama freshie molds" bundle at $20 —
  freshie, not cement.

**IP risk**: low. Hearts, eggs, bunnies, florals; no characters.

**Toolchain fit**: excellent; same as the 10 molds already built (manifold relief,
`tapered` walls, `cast_of` render, A1 mini).

**First products**
1. Heart trinket dish mold (cement/Jesmonite): dish 100 x 90 x 22 mm.
2. Heart tealight holder mold: a `candle_holder_mold --set shape=heart` variant.
3. Easter egg planter mold (cup + core like `planter_mold`): egg 80 x 105 mm, flat base.
4. Bunny-ear trinket tray mold: 110 x 80 mm.
5. Mother's Day botanical coaster mold: a pressed-flower relief variant of `hex_coaster_mold`.

---

### 5. Thermoforming (vacuum-forming) bucks

People print a buck, vacuum-form PETG/PS sheet over it (with a printed or Mayku-type
former) and get light, clear or coloured shells: ornaments, treat boxes, egg halves.

**Evidence**
- MakerWorld "thermoforming": 518 models. MIHAI_T's Thermoformed happy ghosts 11k / 6.6k,
  flexible hearts 8.4k / 6.3k, Christmas tree bauble 7.3k / 5.6k, Easter eggs 3.5k / 3.5k;
  Thermoformed Apple (teacher appreciation) 7k / 4.3k; 3D Printable Vacuum Former 3.7k /
  6.4k. In the generic "mold" search sorted by **trending**, Candy Box & Thermoforming
  Mold, Thermoformed Christmas baubles and Thermoformed Flexible Butterfly are all in
  the top 7. Rising, and seasonal.
- Etsy "vacuum forming mold stl": the only thermoforming buck found was a bat for $2.00.
  The paid side is close to empty.

**Competition**: one prolific free creator (MIHAI_T) dominates. Whether anyone pays is
unproven, so price low and use it as a cheap seasonal add-on.

**IP risk**: low (avoid the Grinch-type subjects seen in the free list).

**Toolchain fit**: excellent: solid bucks, every wall drafted ≥ 3°, no undercuts (the
existing `no_overhang` and draft checks already enforce what thermoforming needs), flat
base, optional vent holes. Tiny print times.

**First products**
1. Heart treat box buck pair (box + lid), 80 x 75 x 30 mm — Valentine's.
2. Easter egg halves buck, 90 mm egg, two sizes.
3. Faceted gem ornament bucks, 3 shapes, 60 mm.
4. Spring flower petals buck set for layered paper/plastic flowers.

---

### 6. Polymer-clay cutter sets (original seasonal motifs)

**Evidence**: MakerWorld "polymer clay cutter": 999+ models; Petal cutters 2k / 1.5k,
Daisy donut cutter set 1.8k, Heart cutter stamp 1.7k, Micro shapes 29 pcs 1.3k.
"clay stamp": Customizable Text Stamp 11.3k / 8.8k, Maker's Mark seal 5k.
Etsy "polymer clay cutter stl": Christmas stud cutters $22.99, 37-design bundle $11.75,
40-design Christmas bundle $18.74, landscape set $4.37, snowflake (3 sizes) $6.30,
moose (6 sizes) $6.99, gnome $3.96, depth-guide Bestseller $2.40 (from $6).
**Supply**: crowded and bundling, but sets of 3-6 sizes at $4-7 still sell next to bundles.
Earring makers need new seasonal shapes every season, so this is repeat demand.

**IP risk**: low for original motifs; many top sellers use characters — skip.

**Toolchain fit**: excellent — `pumpkin_clay_cutter` already has blade profiles at
nozzle multiples, imprint blades and a pusher. A new motif is mostly new art.

**First products** (each in 6 sizes, 15-40 mm, with pusher): Valentine heart-and-arch
set; Easter egg with imprint pattern; spring tulip with leaf imprints; Mother's Day
pressed-flower set.

---

### 7. Watch list: fingerboard deck molds and shapers

MakerWorld: Fingerboard 32x96mm Mold + Shaper + Wheels 695 downloads, and "fingerboard
mold" shows up as a related search on nearly every mold query. Etsy digital: $6.60,
$8.25, $8.99; physical aluminium molds $260; an 11-piece obstacle mold bundle at $99.99.
Supply is thin and buyers are hobbyists who pay. Fit is good (build123d: a two-part press
with concave and kick curves, checked with `assembly` for the 7-ply veneer gap), but it
is a small audience. Do one listing if the bait molds prove the "hobby tool" buyer.

---

## Looked at and rejected

| Area | Why not (2026-10-28 evidence) |
|---|---|
| Gridfinity | Enormous free demand (Superlight Baseplates 94.5k, Ultimate Bins Collection 50.4k) **and** enormous free supply, plus MakerWorld's own "Parametric Model Maker" promoted in the results. Etsy is bundles: 80 kitchen bins $4.94, 1200+ functional files $1.95 "Popular now". |
| Brand tool storage (Milwaukee Packout etc.) | Strong free demand (Packout inserts 4.5k, cleats 3.8-4.4k) but every title leans on the Milwaukee trademark, and fit dimensions come from someone else's product or model. |
| Board-game inserts | Demand is real (Catan 4.4k, SETI 4.1k, Wingspan 1.9k) but each depends on a named game's trademark and exact box/component dimensions we can't verify without the game. Free supply is good. |
| Pottery texture rollers | Free demand strong (TheBreadman rollers 1.3-2.7k each), but Etsy is wall-to-wall 150-250-roller bundles at $5-11. |
| Functional replacement parts (knobs, appliance parts) | Free culture (Stove knob GE replacement 1.2k, Hob Knob 3.6k) and per-product fit data we can't measure; brand names in titles. |
| Tabletop terrain / minis | Dominated by large Patreon studios and free creators (everythingDND terrain 4.8-6.1k); minis need resin detail that FDM checks can't sell. |
| Aquarium, garden, beekeeping, bird feeders | Demand is free downloads of utility items (Barb Union Tube 17.3k, Modern Bird Feeder 17.3k, Bee Waterer 3.6k); no paid signal seen. |
| Purge-waste ("poop") compression molds | Trending on MakerWorld (Recycled Poop Heart Mold 852 dl / 2.8k, Poker Chip Mold 1.5k / 3.8k, Modular compression molding system V2 398 / 2.8k), and the audience is exactly A1 owners. But the culture is free, and it needs heat-resistant tooling we can't check. Revisit only as a free lead magnet. |
| Bath-bomb molds | Some $18 single listings, but also $4-5 generic sphere/square sets; press-fit molds are simple enough that the free versions are fine. |

---

## Recommendation: the next 10 listings

Mix: two new buyer groups with good paid signal (candle/wax makers, anglers), one
higher-priced craft (slip casting), and dated seasonal products on the pipeline we
already have.

| # | Listing | Area | Price to test | Ready by |
|---|---|---|---|---|
| 1 | Ribbed pillar candle master + housing (70 x 90 mm candle) | 1 | $6.99 | Dec |
| 2 | Bubble cube candle master + housing (60 mm) | 1 | $6.99 | Dec |
| 3 | Wax-melt clamshell master, 6 botanical cavities | 1 | $5.99 | Dec |
| 4 | Paddle-tail shad open-pour mold, 75 mm x 5 | 2 | $7.99 | Feb (after a test pour) |
| 5 | Curly-tail grub open-pour mold, 65 mm x 6 | 2 | $7.99 | Feb |
| 6 | Straight mug slip-casting master + 3-part frame, 300 ml fired | 3 | $12.99 | Jan |
| 7 | Heart trinket dish cement mold (100 x 90 mm) | 4 | $4.99 | early Jan |
| 8 | Easter egg planter mold, cup + core (80 x 105 mm) | 4 | $5.99 | mid Feb |
| 9 | Heart treat-box thermoforming bucks (box + lid) | 5 | $2.99 | early Jan |
| 10 | Valentine heart clay cutter set, 6 sizes + pusher | 6 | $3.99 | early Jan |

**Price points to test**
- Hobby tools and masters (1-5): $5.99-7.99. Etsy single files in these groups sit at
  $6-14 and $9-23, so this undercuts the band while staying above the $2.99 default.
  Try $7.99 vs $9.99 on the two bait molds (split by listing).
- Slip-casting master: $12.99 (band $10.50-20.79). Raise to $14.99 if it sells.
- Seasonal casting molds: $4.99-5.99, as recommended last round for single molds.
- Low-ticket seasonal add-ons (9-10): $2.99-3.99, then a "Valentine's maker set"
  bundle of 7 + 9 + 10 at $8.99.
- **Licence wording matters more than price here.** These buyers make things to sell
  (candles, baits, castings). Competitors say so on the listing ("Mold + Commercial
  license", "you may sell your printed creations"). Recommend the personal licence
  explicitly allows selling what you *cast* or *pour* with the mold, with the $11.99
  commercial tier for selling the printed molds themselves. Otherwise the $2.99/$11.99
  split pushes most of these buyers to the higher tier or to a competitor.

**Before listing**
- Do one real pour each for the bait mold (plastisol, PETG print) and the candle master
  (silicone), and photograph the result; neither can be checked by the harness alone.
- Nothing in this batch copies another designer's file or uses a trademark: bait shapes
  are generic types under our own names, the mug and vessel forms are our own profiles,
  and no characters appear anywhere.
