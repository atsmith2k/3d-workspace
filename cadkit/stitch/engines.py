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


def _run_with_fallback(svg_path, notes, tries=8):
    """Run Ink/Stitch; when its auto-fill fails on an element ("Failed on ... (el123)"),
    switch that element to Ink/Stitch's legacy fill (simpler, handles odd geometry) in
    the SVG and try again. Each switch is reported in the notes."""
    import re
    svg_path = Path(svg_path)
    for _ in range(tries):
        try:
            return run_inkstitch(svg_path)
        except RuntimeError as e:
            m = re.search(r"Failed on .*?\((el\d+)\)", str(e))
            if not m or "autofill" not in str(e).lower():
                raise
            el = m.group(1)
            text = svg_path.read_text(encoding="utf-8")
            new = re.sub(rf'(<path id="{el}"[^>]*?inkstitch:fill_method=")auto_fill(")', r"\g<1>legacy_fill\g<2>", text)
            if new == text:
                raise
            svg_path.write_text(new, encoding="utf-8")
            notes.append(f"{el}: Ink/Stitch auto-fill failed, sewn with legacy fill instead")
    return run_inkstitch(svg_path)


def stitch(design, svg_path, engine="auto"):
    """(EmbPattern, engine_used, notes)."""
    notes = []
    if engine == "auto":
        engine = "inkstitch" if find_inkstitch() else "native"
    if engine == "inkstitch":
        pat, err = _run_with_fallback(svg_path, notes)
        reach = getattr(design, "sew_jumps_mm", None)
        if reach:
            from .pattern import sew_short_jumps
            n = sew_short_jumps(pat, reach)
            notes.append(f"{n} jumps of up to {reach:g} mm sewn as travel stitches (design.sew_jumps_mm)")
        if err:
            notes += [f"inkstitch: {line}" for line in err.splitlines()[-5:] if line.strip()]
        return _hide(design, pat, notes), f"inkstitch {inkstitch_version()}", notes
    return _hide(design, native.build_pattern(design), notes), "native", notes


def _hide(design, pat, notes):
    reach = getattr(design, "hide_jumps_mm", None)
    if reach:
        from .pattern import sew_hidden_jumps
        n = sew_hidden_jumps(pat, reach)
        notes.append(f"{n} jumps of up to {reach:g} mm under later stitching sewn as buried travel (design.hide_jumps_mm)")
    return pat
