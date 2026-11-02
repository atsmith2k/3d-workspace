"""Stitch engines: turn a Design (and its SVG) into an EmbPattern.

  inkstitch  runs the installed Ink/Stitch headlessly on the generated SVG, so the
             stitches are exactly what Ink/Stitch's Save As would produce. Found in the
             Inkscape user extensions folder, or set CAD_INKSTITCH to the executable.
  native     the built-in generator (cadkit.stitch.native); no Ink/Stitch needed.
"""
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import pyembroidery as pe

from . import native


def find_inkstitch():
    env = os.environ.get("CAD_INKSTITCH")
    if env:
        return Path(env) if Path(env).exists() else None
    home = Path.home()
    exe = "inkstitch.exe" if platform.system() == "Windows" else "inkstitch"
    roots = []
    if os.environ.get("APPDATA"):
        roots.append(Path(os.environ["APPDATA"]) / "inkscape" / "extensions")
    roots += [home / "Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions",
              home / ".config/inkscape/extensions",
              home / "snap/inkscape/current/.config/inkscape/extensions"]
    for r in roots:
        for cand in (r / "inkstitch" / "inkstitch" / "bin" / exe, r / "inkstitch" / "bin" / exe):
            if cand.exists():
                return cand
    return None


def inkstitch_version():
    exe = find_inkstitch()
    if not exe:
        return None
    for v in (exe.parent.parent / "VERSION", exe.parent.parent.parent / "VERSION"):
        if v.exists():
            return v.read_text(encoding="utf-8").strip()
    return "unknown"


def run_inkstitch(svg_path, timeout=600):
    """Ink/Stitch's own stitch plan for an SVG, as an EmbPattern (exact thread colours)."""
    exe = find_inkstitch()
    if exe is None:
        raise RuntimeError("Ink/Stitch not found; install it or set CAD_INKSTITCH")
    with tempfile.TemporaryDirectory() as tmp:
        csv = Path(tmp) / "plan.csv"
        with open(csv, "wb") as f:
            r = subprocess.run([str(exe), "--extension=output", "--format=csv", str(svg_path)],
                               stdout=f, stderr=subprocess.PIPE, timeout=timeout)
        err = r.stderr.decode("utf-8", "replace").strip()
        if r.returncode != 0 or csv.stat().st_size == 0:
            raise RuntimeError(f"Ink/Stitch failed (exit {r.returncode}): {err[-2000:]}")
        pat = pe.read(str(csv))
        if pat is None or not pat.stitches:
            raise RuntimeError(f"Ink/Stitch produced no stitches. {err[-2000:]}")
        return pat, err


def stitch(design, svg_path, engine="auto"):
    """(EmbPattern, engine_used, notes)."""
    notes = []
    if engine == "auto":
        engine = "inkstitch" if find_inkstitch() else "native"
    if engine == "inkstitch":
        pat, err = run_inkstitch(svg_path)
        if err:
            notes += [f"inkstitch: {line}" for line in err.splitlines()[-5:] if line.strip()]
        return pat, f"inkstitch {inkstitch_version()}", notes
    return native.build_pattern(design), "native", notes
