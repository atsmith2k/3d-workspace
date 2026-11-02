# stitchsim

A small, fast machine-embroidery simulator. Open a PES, PEC, DST, EXP or JEF file and
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
| needle pile-up | 8+ penetrations in one 0.2 mm spot: cuts a hole, shreds thread |
| untrimmed jump | thread carried over 3 mm with no trim: snip by hand |
| no tie-in / no tie-off | a run starting or ending at a trim with no lock stitches |
| too big for hoop (error) | the design is larger than the hoop picked in the side panel |

Hits of one kind that touch are grouped into one marker. Lock stitches next to a trim
and lone short stitches at fill row ends are normal and not flagged. **Density** shows
the thread-layer heat map (green under 2.5, yellow 2.5, orange 3.5, red 5+); the
**Hoop** picker draws the hoop's sewing field around the design. The same checks print
from `--info`, so they can run in scripts (`cad stitch sim file.pes --info`).

**Realistic** (top bar, off by default) draws every stitch as textured thread: a ply
twist, round-thread shading with a specular streak, soft anti-aliased edges, darker
ends where the needle goes in, a soft shadow on whatever is underneath, and a sheen
that depends on the stitch direction against the light (stitches lying across the
light shine, ones along it go dull), which is what makes satins and fills read as
real embroidery.

**Stage on** (side panel) puts the design on a plain background, a t-shirt (jersey
knit), jeans (denim, gold topstitching, rivets), a baseball cap front (twill, eyelets,
button, stitched brim) or a tote bag (canvas, straps with box-X stitching), all drawn
at real size with their own colour picker. Each article opens with the design at its
usual spot and size (left chest, right thigh, cap front, bag centre); move it with
the x/y fields or place mode, set its width, rotate it, or Reset. Showing a stitch
file more than 10% off its sewn size gets a warning: density and pull compensation
don't scale, so rebuild the design at that size before sewing it.

How it stays light: stitches are decoded once into a flat timeline, thread is a mesh of
one shaded quad per stitch built in chunks of 4,096, finished chunks are cached until
the view changes, so a frame during playback only rebuilds the chunk being sewn.
Garments are drawn once on the CPU (fill, pillow shading, seams, topstitching, shadow)
into one texture, tinted for recolouring, with a small repeating weave tile over the
outline for close-ups.

Format notes: PES v5-v10 headers give exact thread RGB (otherwise the Brother PEC
palette), JEF uses the Janome palette, DST and EXP carry no colours (default colours
shown). DST and JEF have no trim command, so trims are inferred from jump runs as
pyembroidery does. Palettes and byte layouts follow pyembroidery (MIT).
