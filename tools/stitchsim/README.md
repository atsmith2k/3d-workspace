# stitchsim

A small, fast machine-embroidery simulator. Open a PES, PEC, DST, EXP, JEF, VP3, XXX or U01 file and
watch it sew stitch by stitch: thread drawn at its real width and shaded like round
thread, underlay going down before the top stitches cover it, jump threads, trims and
colour changes, and a machine-time estimate.

One native binary (about 5 MB, Rust + egui/glow). A 335,000-stitch file loads in
0.15 s and draws at about 3 ms a frame.

```bash
cargo build --release                         # once; or let `cad stitch sim` build it
target/release/stitchsim design.pes           # open a file (or drop one on the window)
target/release/stitchsim --info design.pes    # stats and problems, no window
target/release/stitchsim design.pes --screenshot frame.png --at 0.5 --zoom 30
target/release/stitchsim design.pes --screenshot cap.png --article cap --realistic
target/release/stitchsim design.pes --color 1=#8b1e2d --color 3=#c0c0c0   # try other threads
```

From the repo root, `cad stitch sim designs/<name>.py` opens a design's built PES.

| Key | Action |
|---|---|
| Space | play / pause (from the start once finished) |
| Left / Right | one stitch (Shift: 100) |
| Home / End | start / finished |
| PgUp / PgDn | previous / next colour block |
| + / - | double / halve the speed |
| F, double-click | fit the design |
| G | ghost: show what is still to sew, faintly |
| J | jump threads (red: left untrimmed, grey: trimmed) |
| R | machine time: 650 spm x multiplier, with 8 s trims and 30 s colour stops |
| L | realistic thread on / off |
| P | place mode: drag moves the design on the garment, scroll resizes it |
| [ / ] | rotate the design 5 deg |
| I | fit the garment |
| X | problem markers on / off |
| D | density heat map on / off |
| N / Shift+N | next / previous problem |

Drag to pan, scroll to zoom about the cursor. Clicking a thread in the side panel
jumps to the start of that colour; its checkbox hides it. Each thread's swatch is a
colour picker, and its **Brother** menu picks a spool from the 64-colour Brother
palette (hover for names); a changed thread shows the file's own colour with a reset,
and **Reset colours** puts them all back. Recolouring is for previewing only: the file
is not changed (rebuild the design with new colours to sew them). The timeline shows
the colour blocks and trims; click or drag it to scrub.

**Problems** (top bar, on by default) checks the file the way a machine would sew it
and puts a numbered marker on every problem area (red: error, orange: warning); hover a
marker for what it is and how to fix it, click it (or its row in the side panel, or
press N) to jump the timeline there and zoom in. Problems also show as ticks under
the timeline.

| Problem | Flagged when |
|---|---|
| stitch too long (error) / long stitch | stitches over 12.1 mm (most machines' limit) / over 7 mm (snags) |
| far too dense (error) / too dense | over 5 / over 3.5 thread layers per mm2 (fill ~1, satin ~1.7) |
| tiny stitches | 3+ stitches in a row under 0.3 mm away from a cut: thread breaks, nests |
| doubled stitch | a stitch onto the point the needle is already in: two penetrations in one hole |
| needle pile-up | 8+ penetrations (any colour) within 0.1 mm of one another: cuts a hole, shreds thread |
| coincident stitches (error at 9+) | the needle returns to one hole 7+ separate times in one colour (a bean or lock pass counts once): each return cuts the thread already there |
| stitch clump | 45+ penetrations of one colour within 1 mm: a knot builds up underneath and jams the needle plate |
| short stitches | over 10 % of stitches under 0.5 mm away from ties: they don't form a loop and fray the thread |
| stacked locks | two tie groups at one start or end of a run: knots, thread breaks, mistrims |
| untrimmed jump | thread carried over 3 mm with no trim: snip by hand |
| no tie-in / no tie-off | a run starting or ending at a trim with no lock stitches |
| too big for hoop (error) | the design is larger than the hoop picked in the side panel |
| off-centre | the design's centre is over 1 mm from the file origin (error over 10 mm; an SE600 resets) |
| too many stitches / too many colours (errors) | past the machine profile's stitch or colour-change limit |

Hits of one kind that touch are grouped into one marker. Lock stitches next to a trim
and lone short stitches at fill row ends are normal and not flagged. **Density** shows
the thread-layer heat map (green under 2.5, yellow 2.5, orange 3.5, red 5+); the
**Hoop** picker draws the hoop's sewing field around the design. A non-square hoop is
turned to the design's long side (**Turn: auto**, so a 159 x 120 mm design fits a 5x7 as
180 x 130 landscape); pin it with portrait / landscape, or `--hoop-turn` on the command line. The same checks print
from `--info`, so they can run in scripts (`cad stitch sim file.pes --info`).

**Machine** (side panel, or `--machine NAME`) picks the limits the file is checked
against; stitch too long uses the profile's maximum stitch:

| Profile | Max stitch | Stitches | Colour changes |
|---|---|---|---|
| `brother-home` (default) | 12.1 mm | 500,000 | 127 |
| `janome` | 12.7 mm | 500,000 | 99 |
| `tajima` | 12.1 mm | 1,000,000 | 999 |
| `bernina` | 12.7 mm | 500,000 | 99 |

Brother's 500,000 stitches is from its manuals and 12.1 mm is DST's encoding limit; the
other numbers are conservative assumptions (see `src/machines.rs`). `--info` also prints
`centre`, `trims/1k` (trims per 1,000 stitches), `doubled` (zero-length stitches) and
`short<0.5` (stitches under 0.5 mm away from ties, with their share) for scripts;
`--metrics FILE...` prints the raw measures the thresholds were calibrated with.

**Realistic** (top bar, off by default) draws every stitch as textured thread: a ply
twist, round-thread shading with a specular streak, soft anti-aliased edges, darker
ends where the needle goes in, a soft shadow on whatever is underneath, and a sheen
that depends on the stitch direction against the light (stitches lying across the
light shine, ones along it go dull), which is what makes satins and fills read as
real embroidery.

**Stage on** (side panel) puts the design on a plain background, a t-shirt (jersey
knit), jeans (denim, gold topstitching, rivets), a structured six-panel baseball cap
seen three-quarter on (twill, panel seams, metal eyelets, button, a curved stitched
brim) or a tote bag (canvas, straps with box-X stitching), all drawn at real size with
their own colour picker. Flat-laid garments have soft folds lit from the upper left
and their fabric's grain at garment scale; on the cap the design wraps round the
crown. The stitches take the garment's light where they sit, and in Realistic mode
the fabric round the embroidery shows slight puckering (`src/drape.rs`). Each article opens with the design at its
usual spot and size (left chest, right thigh, cap front, bag centre); move it with
the x/y fields or place mode, set its width, rotate it, or Reset. Showing a stitch
file more than 10% off its sewn size gets a warning: density and pull compensation
don't scale, so rebuild the design at that size before sewing it.

How it stays light: stitches are decoded once into a flat timeline, thread is a mesh of
one shaded quad per stitch built in chunks of 4,096, finished chunks are cached until
the view changes, so a frame during playback only rebuilds the chunk being sewn.
Garments are drawn once on the CPU (fill, pillow shading, folds, grain, seams,
topstitching, shadow; the cap ray cast on 8 threads) into one texture, tinted for
recolouring (the cap and jeans are baked in their colour), with a small repeating
weave tile over the outline for close-ups. The puckering is one texture per design,
laid as a grid through the same warp as the stitches.

Format notes: PES v5-v10, VP3 and XXX give exact thread RGB (otherwise the Brother PEC
palette), JEF uses the Janome palette, DST, EXP and U01 carry no colours (default colours
shown). DST and JEF have no trim command, so trims are inferred from jump runs as
pyembroidery does. Palettes and byte layouts follow pyembroidery (MIT).
