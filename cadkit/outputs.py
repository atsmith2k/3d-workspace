"""Structured build outputs: `build.json` and `slice.json` in every output folder,
and `report.txt` composed from them, so a rebuild keeps the slice sections and a
slice made from an older STL is visibly stale.

    output/<name>/build.json   what `cad build` measured (Report + checks + fit) plus
                               the exact report lines, so report.txt is byte-identical
    output/<name>/slice.json   one entry per sliced 3MF (key = 3MF stem, e.g.
                               butterfly_paver_mold_a1mini), each with the STL's sha256
    output/<name>/report.txt   header + part sections + fit + slice sections
"""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_info(root=ROOT):
    """{'commit': sha or None, 'dirty': bool} for the repo at root; no git, no crash."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                                text=True, timeout=10)
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root,
                                capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return dict(commit=None, dirty=False)
    if commit.returncode != 0:
        return dict(commit=None, dirty=False)
    return dict(commit=commit.stdout.strip() or None, dirty=bool(status.stdout.strip()))


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def slice_is_stale(entry, out):
    """A slice whose STL has changed since it was sliced (or is gone)."""
    stl = Path(out) / entry.get("stl", "")
    if not entry.get("stl") or not stl.exists():
        return True
    return entry.get("stl_sha256") != sha256(stl)


def compose_report(build, slices, out):
    """report.txt text from build.json + slice.json contents."""
    lines = list(build.get("header_lines", []))
    for part, data in build.get("parts", {}).items():
        lines += [f"## {part}", *data.get("lines", []), ""]
    fit = build.get("fit")
    if fit:
        lines += ["## fit", *fit.get("lines", []), ""]
    for stem, entry in slices.items():
        stale = slice_is_stale(entry, out)
        head = f"## slice {stem} ({entry.get('slicer', '?')})"
        if stale:
            head += "  STALE: the STL has changed since this slice"
        lines += [head, *entry.get("lines", []), ""]
    return "\n".join(lines)


def write_report(out):
    """(Re)write output/<name>/report.txt from build.json and slice.json."""
    out = Path(out)
    build = load_json(out / "build.json")
    slices = load_json(out / "slice.json")
    if not build and not slices:
        return None
    text = compose_report(build, slices, out)
    (out / "report.txt").write_text(text, encoding="utf-8")
    return text
