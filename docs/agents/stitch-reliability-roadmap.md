# Stitch reliability: research findings and roadmap (2026-11-03)

Goal: every design this workspace delivers is machine-ready in **every format it ships**,
with its problems found and fixed before delivery, so a design never needs a test
sew-out of its own.

Honest framing: no published or open-source tool predicts push/pull, pucker or
bird-nesting from a file (Wilcom, Hatch, Embrilliance all rely on fabric presets plus a
test sew). Bird-nests, flagging and most mechanical thread breaks come from tension,
hooping, needle and lint, which no file controls. The reachable bar is: **file validity
proven, every geometry rule enforced, distortion predicted from a model calibrated by one
sew-out per (machine, fabric, stabiliser) profile, never per design.**

## What the audit found (all 107 designs, 398 published size builds)

`stitchsim --info` reports `problems 0` on all 107 PES files. The trouble is in what it
never looks at:

| Finding | Scale | Root cause |
|---|---|---|
| DST, EXP, XXX, U01 carry untrimmed jumps | 352-364 of 398 files each, 3,600-4,400 jumps | The pattern holds JUMPs and relies on the PES writer turning every jump into a trim; the other writers keep them as jumps. Brother/most home machines don't trim jumps reliably themselves. |
| VP3 has stitches over 12.1 mm (up to 63 mm) | 338 of 398 files | VP3 has no jump command; pyembroidery skips the JUMP and the move becomes one long stitch, with no trim in front because the pattern had none. |
| JEF untrimmed jumps | 34 files | same as above |
| Zero-length stitches (two penetrations in one hole) | 89 of 107 designs, ~1,180 | `pattern.sew_short_jumps` appends the target point twice (confirmed); more from engine output. stitchsim drops moves under 1e-4 mm, so it never sees them. A Tajima-compatible machine froze on DST with ~30 (0,0) stitches (Ink/Stitch #1296). |
| Blank machine label | every DST/PEC | pattern has no name metadata; the `LA:` field is spaces |
| Only PES is verified | publish gate | `stitchsim_info` runs on the PES only; stitchsim cannot read VP3/XXX/U01; the round-trip test uses one square and compares counts, not stitches |
| Self-referential decoding | stitchsim | readers "follow pyembroidery's byte layouts", so a writer bug decodes as intended |
| No fabric model | 104 designs say fleece/knits | one default set for every design: fill pull compensation 0, satin 0.2 mm; no design sets `pull=`. Coverage is computed on ideal stitch positions, so it cannot see the registration gaps pull causes. |
| Short stitches under 0.4 mm away from locks | up to 2.6 % of a design | stitchsim only flags 3+ in a row under 0.3 mm |

## Rules from the research (sources in the 2026-11-03 session notes)

- Stitch length: 12.1 mm hard (DST/ternary), 7 mm satin split; floor 0.5 mm outside
  ties (1 mm safe zone). Satin width 1-10 mm (12 possible, 15 snags).
- Density: Brother warns at 3+ overlapping stitches per spot; Embrilliance red at 6
  layers. Separate **clump** check within one colour (~1 mm radius), as Embrilliance DRK.
- Pull compensation (Wilcom guide): woven/drill 0.20 mm, T-shirt 0.35, fleece/jumper
  0.40, lettering 0.2-0.3. Overlap between neighbours in sewing order should be at least
  the earlier object's pull + 0.3-0.5 mm.
- Lettering: caps >= 4 mm (satin), mixed >= 5-6 mm; Wilcom classifies by whether a
  2 mm / 4 mm circle fits the stroke.
- Ties: exactly one lock group at each start and trim; stacked locks cause breaks and mistrims.
- Format traps: PES v6 needs the addendum block; reserved Brother palette codes (64
  "Applique") trigger stops; DST header ST/CO/extents must match; machines trim DST on
  3+ consecutive jumps, so connectors must stay at 1-2 jumps; JEF rejected when colour
  or point counts mismatch; JEF lands off-centre; designs far from the origin reset an
  SE600. Ink/Stitch now writes through its `pystitch` fork, which carries fixes EmbroidePy
  lacks (we pin pyembroidery 1.5.1, which does include the #132 extents fix).

## Roadmap

**Phase 0: stop shipping bad files.** Done 2026-11-03 (items 1-3; item 4 is a local
rebuild, the shop re-ingest waits for a go-ahead).
1. Normalise the pattern before any writer: explicit TRIM before every jump that stays
   a jump; drop zero-length stitches (fix the `sew_short_jumps` duplicate); set the
   pattern name (8-char `[A-Za-z0-9]` label).
2. Gate every shipped format: read each file back, compare with the canonical plan
   (penetrations, trims, colours, extents, centring, max stitch length, untrimmed jumps)
   and fail the build on any difference beyond the format's documented loss.
3. Add VP3, XXX, U01 readers to stitchsim; run `--info` on all 8 formats in `publish`.
4. Rebuild and republish the 398 size builds (and the shop drafts) once green.

**Phase 1: an independent oracle.**
- Rewrite stitchsim readers from the format specs (edutechwiki PES/PEC/DST/JEF/VP3) rather
  than pyembroidery's code, and cross-check against libembroidery; any disagreement fails.
- Header and structure validators per format (PEC block + addendum, thumbnails, palette
  codes, DST header fields, JEF counts and hoop code).
- A corpus of known-bad files built from each bug report above, plus mutation tests: every
  analyser rule must catch its fixture and stay quiet on the clean set.
- Consider moving the writers to `pystitch` (Ink/Stitch's fork) after a diff of the two.

**Phase 2: analyser rules stitchsim lacks.** Zero-length and coincident penetrations
(>=3 = error), clumps within a colour, 0.5 mm floor outside ties, stacked locks, satin
width bands, lettering legibility, fill exit/entry placement (no travel across a finished
fill), converging-stitch centres, design centred on the origin, trims per 1,000 stitches,
and machine profiles (Brother PE/SE without jump trim, stitch and colour limits). Fix the
pile-up check's 0.2 mm cell aliasing (count a radius, not a grid cell).

**Phase 3: fabric profiles and a distortion model.**
- `FABRIC = "knit" | "fleece" | "woven" | "twill" | "towel" | "cap"` in the design drives
  pull compensation, underlay, spacing and stitch length per object class (fill, wide
  satin, narrow satin, lettering), with Wilcom's numbers as the starting values.
- stitchsim predicts pull: each stitch contracts the fabric across its direction by a
  per-fabric coefficient, accumulated in sewing order; coverage and a new
  **registration** check run on the distorted positions; the realistic render can show it.

**Phase 4: calibration, the step that replaces per-design test sews.**
- One calibration card per (machine, fabric, stabiliser): squares at 0/45/90 deg, satin
  bars 1-12 mm, an overlap ladder, a density ladder, a lettering ladder, ArUco markers.
- Sew it once, photograph it flat, `cad stitch calibrate photo.jpg` measures it and fits
  the profile's coefficients; the profile records which machine and card it came from.
- Field feedback: any real sew-out problem becomes a corpus case and, where it applies, a rule.

**Phase 5: one release gate.** `cad stitch verify` produces a per-format readiness report
(validity, rules, predicted registration, profile used); `publish` requires it for every
size and format; the selftest corpus keeps it honest.

## As delivered (2026-11-03)

| Phase | What is in the workspace |
|---|---|
| 0 | `pattern.prepare` (explicit TRIM before every jump left after sewn thread, doubled stitches dropped, 0.1 mm snap, design centred, machine label), JEF written with explicit trims, `pattern.verify_files` read-back of every format in every build, stitchsim readers for VP3/XXX/U01 |
| 1 | `cadkit/stitch/validate.py`: decoders for all 8 formats written from edutechwiki + libembroidery (no pyembroidery code), header/structure rules per format, `cross_check` against pyembroidery; `tests/test_validate.py` builds a corpus of known-bad files (issue 132 `FF FE`, palette, label, DST/JEF header mismatches, zero-length, uncentred...). Found and fixed: PEC palette codes 62-64 ("Applique Material") chosen for oranges/golds (`pattern.RESERVED_PEC`). pystitch 1.0.1 evaluated: byte-identical except the PEC first move; it predates its own PR 140, so no switch for now |
| 2 | stitchsim: radius-based pile-up, coincident hole visits (warn 7, error 9), clumps per colour (45 within 1 mm), short-stitch share (10 % under 0.5 mm away from ties), stacked locks, off-centre, machine profiles (`--machine`, `src/machines.rs`), trims/1k; thresholds set from the 398-build corpus. Python: stray thread over 3 mm (`checks.stray_stitches`), filled lettering under 6 mm. Fixed at the source: our tie-in added on top of Ink/Stitch's triangle lock (`pattern._is_lock`) |
| 3 | `cadkit/stitch/fabrics.py`: profiles woven/twill/apparel(default)/knit/fleece/towel from Wilcom's guideline pull values, applied per element (satin per side by width, fills by stretching the shape along the rows since Ink/Stitch 3.0 ignores fill pull compensation); `fabrics.predict` moves satin edges and fill row ends where the fabric pulls them; the build's registration check re-runs coverage (joins between elements included) on the predicted stitches |
| 4 | `designs/calibration_card.py` (fiducials, fill squares at 0/45/90, satin ladder 1-6 mm, thread-width lines, overlap ladder) and `cad stitch calibrate`: Otsu + fiducial homography + edge profiles, measured against a zero-pull render of the card's own PES so engine offsets cancel; recovers synthetic pull within 0.012 mm. Writes `cadkit/stitch/profiles/<fabric>.json` with provenance |
| 5 | `cadkit/stitch/verify.py`: `readiness.json` + `ready YES/NO` per build (read-back, independent structure check, stitchsim on all 8 formats, design checks and warnings, fabric profile and its calibration status); `publish` sells only ready sizes (`--require-calibration` optional); `cad stitch verify` re-checks built folders; `tests/test_stitch.py::test_release_gate_passes_reference_designs` keeps three reference designs ready |

What still needs a real machine once: sewing the calibration card per (machine, fabric,
stabiliser). Until then every profile says "uncalibrated" in reports and manifests.
