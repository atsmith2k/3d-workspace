# AGENTS.md: working in this repo as a coding agent

This repo is a **generative design workspace**: an agent turns a plain-language request into
a finished, checked digital product, with no hand modelling or digitising. It makes two kinds
of product, and both can be sold in the shop at https://shop.ash10.dev (repo `ash10-dev-shop`):

| Product | Agent writes | Command | Ships |
|---|---|---|---|
| 3D print model | `models/<name>.py` | `cad build`, `cad slice`, `cad publish` | STL, STEP, sliced 3MF |
| Machine-embroidery design | `designs/<name>.py` | `cad stitch build`, `cad stitch publish` | PES PEC DST JEF EXP VP3 XXX U01 + Ink/Stitch SVG |

This file is tool-neutral: any coding agent (Claude Code, Codex, Cursor, Aider...) can follow
it. `CLAUDE.md` is the full reference (every helper, contract and gotcha). The playbooks in
`docs/agents/` hold what the 2026-11-02 sessions learned shipping 60+ embroidery designs and the
shop's embroidery line:

- [docs/agents/embroidery-playbook.md](docs/agents/embroidery-playbook.md): how to design
  embroidery that sews well and reads well, the failures we hit and their fixes.
- [docs/agents/shop-publishing.md](docs/agents/shop-publishing.md): design to live product,
  end to end, with the shop's production gotchas.

## Setup and the commands

- `py scripts/setup.py` on Windows, `python3 scripts/setup.py` elsewhere; wait for `READY`.
  Then `cad selftest` (regression suite) must pass.
- Run `cad` from the repo root: `cad.cmd` on Windows, `./cad` elsewhere (both wrap `.venv`).
- `cad list` (3D models), `cad stitch list` (embroidery designs, Ink/Stitch status).
- Tests: `.venv/Scripts/python -m pytest tests -q`. Run them, and `cad selftest`, after any
  change under `cadkit/`.
- Ink/Stitch 3 (in the Inkscape extensions folder, or `CAD_INKSTITCH`) is the default stitch
  engine; without it `cad stitch build` falls back to the built-in engine.
- `tools/stitchsim` (Rust) is the embroidery viewer and problem finder. Build it once with
  `cargo build --release` there, or let `cad stitch sim` build it. **In automation only ever
  call it with `--info` or `--screenshot`**: run any other way it opens a GUI window and your
  command never returns (it has no `--help`).

## The loop (both product kinds)

1. **Clarify only what changes the result** (size, what it attaches to or sews on, hoop,
   printer, colours). Pick sensible defaults for the rest and say what you picked.
2. **Spec before code.** The script's docstring has a `Spec:` block; turn every line of it
   into a check in `checks(p)`. The build fails when a check fails, which catches "the code
   ran but the shape is wrong" before anyone looks at a picture.
3. Build, then **look at the preview image yourself** (not just the stats). Iterate until it
   looks right and every check passes.
4. Measure instead of guessing: `cad measure` for models, `cad stitch sim <pes> --info` for
   embroidery (it lists problems; `problems 0` is the bar for anything sold).
5. Deliver the files plus a summary (size, time, materials or threads, anything to know).

## Hard rules

- Units mm. Models sit on Z=0 in print orientation; embroidery is centred on the origin, Y up.
- Never guess hardware dimensions: `cadkit.hardware` has them.
- Never resize a stitch file to make another size: re-stitch the design per size
  (`SIZES` in the design, `Design.scaled`). Density and pull compensation don't scale.
- Cite outside dimension sources and set `sellable=False` until their licence is checked.
- **Rights before sale.** A design digitised from someone's image needs the user's
  confirmation that they hold the rights before it goes on sale. Use no franchise, character,
  school, team, conference or brand names, marks or styles; collegiate-style designs use
  state and city names only. Fonts must be ours (`cadkit/stitch/lettering.py`) or licensed.
- **Every price, and every "go live", is the user's call.** Agents publish as drafts or
  "coming soon" and ask (see the shop playbook).
- Generated files go to `output/` (gitignored); commit the scripts in `models/`, `designs/`
  and `cadkit/`, never the output.

## Working alongside other agents

Several agent sessions often work in this one checkout at the same time. Learned the hard
way:

- **Commit only your own changes.** `git status` will show other sessions' uncommitted work
  (new designs, edits to shared files). Never commit, revert or "fix" it. When a shared file
  holds both your hunks and theirs, stage only yours (`git add -p`, or write the index blob
  directly) and check the commit on its own in a throwaway `git worktree` before committing.
- A shared file can be **mid-edit** by another session (it once left `cadkit/stitch/cli.py`
  unparseable for a few minutes). Don't touch it; wait and retry, or run the last committed
  version from a scratch copy.
- A scratch copy of a module resolves paths from *its own* location: pass output folders
  explicitly or your build lands somewhere unexpected (one build silently wrote to the temp
  folder).
- Before messaging "the session that made X", confirm who made it (search the session
  transcripts for a file it wrote). A wrong guess sends work to an agent that has no context.
- Harness changes reach every design. After changing `cadkit/stitch/`, rebuild a few existing
  designs and confirm `cad stitch sim --info` still reports `problems 0`.
- Each commit message ends with the attribution line your environment asks for.

## Where things are

```
models/  designs/          one script per product (commit these)
designs/_<collection>.py   shared palette + helpers for a collection (_fall, _winter, _realms...)
cadkit/                    the 3D harness;  cadkit/stitch/  the embroidery harness
tools/stitchsim/           Rust embroidery viewer, simulator and problem finder
docs/research/             market research that picked collection themes
docs/agents/               the playbooks above
output/                    generated (gitignored)
```
