# Embroidery playbook

What the 2026-11-02 sessions learned building the `cad stitch` harness and about 60 designs
with it (Indiana, the grizzly, Harvest Hollow, Frost & Fir, Realms & Relics, Arcana & Ink,
Game Day States, Hearth). API details are in `CLAUDE.md` ("Embroidery designs"); this file
is the judgement that goes with them.

## The bar a design must clear

- Every `check` line PASS, no WARNING lines, at **every** size you ship (4x4 and 5x7 are the
  usual pair; each size is re-stitched, never scaled).
- `cad stitch sim <pes> --info` reports `problems 0` (no long or tiny stitch runs, density
  over 3.5, needle pile-ups, untrimmed jumps, missing tie-ins/offs, hoop overflow).
- You looked at the preview sheet **and** a stitchsim realistic render, and it reads at
  actual size. At 100 mm a 0.5 mm detail is invisible; a dark line is the strongest detail
  you have.
- Always include `coverage(1.0)` in `checks`: it fails on bare fabric inside an element or
  in a narrow slot between elements.

## Seeing the design

- Preview sheet: the sewn render (does it read?), the 24 mm **detail** tile at thread scale
  (row texture, satin edges, corners; point it with `--detail x,y` or `DETAIL = (x, y)`),
  sewing order (red dashes are untrimmed jumps), density map.
- `cad stitch sim <pes> --screenshot out.png --realistic` renders thread with sheen and
  shadow; `--zoom 20 --at 0.9999` for a close-up, `--article tote|tshirt|cap|pants` to stage
  it on a garment, `--clean` for a product shot without the viewer UI.
- **Judge the stitch, not the render.** Several "defects" turned out to be render or check
  artifacts (below). Before fixing something, look at the actual stitches around the spot at
  high zoom.

## Construction that works

- Sewing order is element order: background fills, then details, then outlines and
  lettering. Group by colour; every colour change costs the operator a stop.
- Never stack fills: `knockout(lower, *upper)`. A fill under a satin border stops under it:
  `fill(tuck(shape, border_width))` (0.6 mm overlap).
- Borders: `outline(shape, color, width=)` sews **one continuous satin ring**. Never border a
  shape with separate satin pieces: the first Indiana build had 21 pieces with a visible
  break, a tie-off and a trim at every corner.
- Satin 1-7 mm wide; nothing under 1 mm in a fill. For a column that comes to a point on
  purpose (claws, thorns, leaf tips) use `d.satin(..., taper=True)`: one crescent tapering
  to 0.3 mm reads far better than a 1 mm bar with a stitched point on the end.
- Vary fill angles between neighbouring areas so they read apart; run fur, grass and grain
  fills *along* the direction they grow.
- Leave 1.5 mm between an inner shape and its parent's edge (thinner rims are dropped by
  knockout). Keep runs 2 mm inside an outline.
- Satin veins and stems start clear of where other columns meet (five columns into one hole
  is a needle pile-up). Never route a bean run back over its own holes (out and back piles
  9 penetrations): zigzag forward, or draw grass blades as slim Vs.
- Collections: one palette of exact Brother threads in `designs/_<collection>.py`, drawn once
  in a 100 mm space with `fit()` and rebuilt per size; reusable shapes in
  `cadkit/stitch/motifs.py`; our own block lettering in `cadkit/stitch/lettering.py`.

## Realistic subjects: digitise from a reference, don't draw coordinates

Hand-placed coordinates gave a cartoon bear however long we iterated (three rounds of
"still looks cartoonish"). What worked, in `designs/grizzly_salmon.py`:

1. `Artwork(reference, width).tones(k)` (`cadkit/stitch/artwork.py`): cut the subject out
   (transparency, plus a mask for ground shadows), k-means the colours into thread tones,
   merge specks and sub-`min_width` slivers into neighbours, vectorise each tone.
2. Fill each tone in patches along the hair direction read from the image
   (`art.by_flow`, `art.angle_in`; a structure tensor). A change of stitch direction reads
   as a change of shade in thread, so **4 tones in ~10 mm patches looked like the 8-tone
   version at 30 % fewer stitches** (25,303 -> 17,623; trims 209 -> 115; sew time 73 -> 47 min).
3. Place what the image doesn't give you cleanly by hand from the reference's pixel
   coordinates: eyes (amber iris + catchlight), claws, the props.
4. Correct the reference where it's wrong. The illustration drew six claws on one paw; bears
   have five. Small, dark, high-contrast features (eyes, claws, nose) decide the likeness.
5. Compare side by side with the reference (`compare_*.png`) after every change.

Overlap tones one way only (each tone tucks 0.25 mm under the tones sewn after it), knock
fur and shadows out under claws, and clip creek lines and ripples at busy spots, or density
climbs past 3.5 where three layers meet.

## Machine efficiency

- Trims are the expensive part of sew time (about 8 s each here). The PES/DST writers trim
  **every** jump, so: the SVG asks Ink/Stitch for lock stitches only where the thread is
  cut; `pattern.sew_short_jumps` sews jumps up to 3 mm as travel (raise it with
  `design.sew_jumps_mm`, 8 for many touching fur patches) and locks both ends of every jump
  that stays; `design.hide_jumps_mm` buries longer same-colour travel under later stitching.
- Design for few trims: chain same-colour pieces nearest-first, and lay a piece sewn later
  over the gaps (one plate under all the letters instead of an outline per letter took Game
  Day from 30-47 trims to 8-15).
- Bigger fill patches mean longer rows and fewer stitches (row ends dominate small
  patches); long silky fur stitches (4 mm), lighter mid-tone spacing (0.48) and underlay
  only on pieces over ~150 mm2 all cut stitches without losing coverage.
- After any efficiency change run `cad stitch sim --info`: one round of "ties only at cuts"
  left 51 thread ends unlocked until the writer learned to lock forced trims.

## Ink/Stitch quirks

- It mis-sews **closed** satin rails: the SVG writer sends a ring as two open columns that
  meet at corners, with rungs.
- Its auto-fill can crash on odd geometry (tiny holes, slivers). The writer fills holes under
  2 mm2, and the engine retries a crashing element with `legacy_fill` (noted in the report).
- Extra keywords on `d.fill(...)` pass straight through as `inkstitch:*` attributes, so use
  Ink/Stitch's own parameter names (`fill_underlay_row_spacing_mm`, not `underlay_spacing`).
  `expand_mm` made coverage worse on fur pieces; don't reach for it.
- Its default half-stitch locks are ~0.2 mm and get merged away by the 0.4 mm minimum stitch
  length; the SVG uses triangle locks at 1 mm.

## Artifacts that looked like defects

- **Patchy fill in the preview**: PIL draws diagonal lines up to 30 % thin, so the fabric
  showed through as moire. Fixed by per-stitch width correction (render and coverage both).
- **Pale streaks between rows**: machine files snap to 0.1 mm, so 0.4 mm rows sit 0.35-0.5
  apart; real thread (~0.45 mm) closes them. Coverage ignores bare patches thinner than 0.3 mm.
- **"Bare" patch under a darker tone**: coverage now counts stitches sewn later as cover.
- **Narrow wedge between legs flagged as a slot**: real negative space with a sharp tip;
  close tips under ~2.6 mm with the shadow tone rather than loosening the check.

## Delivering

Send the PES (or the user's format), the SVG (opens in Inkscape + Ink/Stitch for hand
tweaks) and the preview, and state the size, hoop, stitch count, threads in sewing order
with the nearest Brother spool (or the hex when none is close), sew time and stabiliser.
Selling it: see [shop-publishing.md](shop-publishing.md).
