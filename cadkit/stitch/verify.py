"""Machine readiness: one verdict per build on whether every file the buyer gets can go
straight to a machine without a test sew-out.

A build is ready when, for every format written:
  - the file reads back and sews what the design says (pattern.verify_files: colours,
    size, sewn path, no stitch over 12.1 mm, no uncut jump, no doubled penetration);
  - its structure is what machines expect, checked by decoders that share no code
    with the writer (validate.check_files: headers, counts, palette codes, centring);
  - stitchsim, reading it as the machine would, reports no problems;
and for the design: every check PASS, no WARNING line (density, coverage, registration
once the fabric pulls in, thin features), on a named fabric profile.

The profile's calibration status is reported, not required: an uncalibrated profile
uses published guideline pull values; `cad stitch calibrate` measures the real ones from
one sewn card. `require_calibration=True` (publish --require-calibration) makes it a
condition.

    r = readiness(written, ref_plan, results, warns, prof, sim_exe)
    r["ready"], r["formats"]["dst"]["problems"], r["blockers"]
"""
import json
import subprocess
from pathlib import Path

from . import pattern as P

try:                                  # independent decoders (Phase 1); optional so a
    from . import validate as V       # partial checkout still builds
except ImportError:                   # pragma: no cover
    V = None


def stitchsim(exe, path, machine=None):
    """(problem count or -1 when unreadable, problem lines) from `stitchsim --info`."""
    cmd = [str(exe), "--info", str(path)] + (["--machine", machine] if machine else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    lines = [l.strip() for l in r.stdout.splitlines() if l.startswith(("  ERROR", "  warn"))]
    for l in r.stdout.splitlines():
        if l.startswith("problems"):
            try:
                return int(l.split()[1]), lines
            except (IndexError, ValueError):
                break
    return -1, [r.stderr.strip()[-300:] or "stitchsim could not read the file"]


def file_problems(written, ref, sim_exe=None):
    """{fmt: {"problems": [...], "checked": [...]}} for every written file."""
    back = P.verify_files(written, ref)
    indep = V.check_files(written) if V is not None else {}
    out = {}
    for fmt, path in written.items():
        probs = [f"read back: {p}" for p in back.get(fmt, [])]
        probs += [f"structure: {p}" for p in indep.get(fmt, [])]
        checked = ["read back"] + (["structure"] if V is not None else [])
        if sim_exe:
            n, lines = stitchsim(sim_exe, path)
            checked.append("stitchsim")
            if n < 0:
                probs.append("stitchsim: could not read it")
            elif n:
                probs += [f"stitchsim: {l}" for l in lines] or [f"stitchsim: {n} problem(s)"]
        out[fmt] = dict(file=Path(path).name, problems=probs, checked=checked)
    return out


def readiness(written, ref, results, warns, prof, sim_exe=None, require_calibration=False):
    """The verdict for one build (see module docstring)."""
    formats = file_problems(written, ref, sim_exe)
    blockers = []
    for fmt, f in formats.items():
        blockers += [f"{fmt}: {p}" for p in f["problems"]]
    blockers += [f"check {r['name']}: {r.get('detail', '')}" for r in results if not r["ok"]]
    blockers += [w for w in warns]
    if not sim_exe:
        blockers.append("stitchsim not available: files not read as a machine would")
    if V is None:
        blockers.append("cadkit.stitch.validate missing: no independent structure check")
    if require_calibration and not prof["calibrated"]:
        blockers.append(f"fabric profile {prof['name']} is not calibrated (cad stitch calibrate)")
    notes = [] if prof["calibrated"] else [
        f"fabric profile {prof['name']} uses guideline pull values ({prof['source']}); "
        "sew and measure a calibration card to replace them"]
    return dict(ready=not blockers, blockers=blockers, notes=notes, formats=formats,
                fabric=dict(name=prof["name"], calibrated=prof["calibrated"], source=prof["source"]))


def lines_of(r):
    """Report lines for a readiness verdict."""
    ok = [f for f, v in r["formats"].items() if not v["problems"]]
    out = [f"ready    {'YES' if r['ready'] else 'NO'}: {len(ok)}/{len(r['formats'])} formats clean "
           f"({', '.join(ok) or 'none'}); checked by {', '.join(next(iter(r['formats'].values()))['checked']) if r['formats'] else '-'}"]
    out += [f"blocker  {b}" for b in r["blockers"][:12]]
    if len(r["blockers"]) > 12:
        out.append(f"blocker  ... {len(r['blockers']) - 12} more (readiness.json)")
    out += [f"note     {n}" for n in r["notes"]]
    return out


def save(r, out_dir):
    path = Path(out_dir) / "readiness.json"
    path.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    return path


def verify_dir(build_dir, sim_exe=None):
    """Re-check a finished build folder without rebuilding: every machine file in
    build.json against the PES (the reference the build itself used is not stored),
    the structure checks and stitchsim. Returns a readiness dict (design checks are
    taken from build.json)."""
    build_dir = Path(build_dir)
    data = json.loads((build_dir / "build.json").read_text(encoding="utf-8"))
    (name, part), = data["parts"].items()
    written = {fmt: build_dir / fn for fmt, fn in part["files"].items()}
    ref = P.plan_of(P.read(written["pes"])) if "pes" in written else P.plan_of(P.read(next(iter(written.values()))))
    from . import fabrics as F
    fab = data.get("fabric") or {}
    prof = F.profile(fab.get("name"))
    warns = [l for l in part["lines"] if l.startswith("WARNING") and not l.startswith(
        tuple(f"WARNING {f}:" for f in written))]       # file warnings are re-derived here
    return readiness(written, ref, part["checks"], warns, prof, sim_exe)
