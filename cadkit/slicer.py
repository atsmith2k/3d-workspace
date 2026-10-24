"""Headless slicing through PrusaSlicer's console binary: print time, filament, layers
and whether supports were actually generated. Optional; `cad slice` says so if no
slicer is installed. Point CAD_SLICER at the binary to use a different install."""
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

CANDIDATES = [
    r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe",
    "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
    "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
]


def find_slicer():
    env = os.environ.get("CAD_SLICER")
    if env and Path(env).exists():
        return env
    for name in ("prusa-slicer-console", "prusa-slicer", "PrusaSlicer"):
        if shutil.which(name):
            return shutil.which(name)
    for c in CANDIDATES:
        if Path(c).exists():
            return c
    return None


@dataclass
class SliceResult:
    gcode: Path
    time_text: str = "?"
    time_s: int = 0
    filament_mm: float = 0.0
    filament_g: float = 0.0
    cost: float = 0.0
    layers: int = 0
    supports_enabled: bool = False
    support_lines: int = 0
    settings: dict = field(default_factory=dict)

    def lines(self):
        if self.supports_enabled:
            sup = "yes, generated" if self.support_lines else "enabled, none needed"
        else:
            sup = "off"
        return [
            f"print    {self.time_text}  ({self.settings.get('layer_height', '?')} mm layers, "
            f"{self.settings.get('fill_density', '?')} infill, {self.layers} layers)",
            f"filament {self.filament_g:.0f} g, {self.filament_mm / 1000:.1f} m  (~${self.cost:.2f})",
            f"supports {sup}",
        ]


def slice_stl(stl, gcode, profile=None, layer_height=0.2, infill=15, supports=False,
              density=1.24, cost_per_kg=25.0, timeout=600):
    exe = find_slicer()
    if not exe:
        raise FileNotFoundError("no PrusaSlicer found; install it or set CAD_SLICER to the console binary")
    cmd = [exe]
    if profile:
        cmd += ["--load", str(profile)]
    cmd += ["--export-gcode", "--output", str(gcode),
            "--layer-height", str(layer_height), "--fill-density", f"{infill}%",
            "--filament-density", str(density), "--filament-cost", str(cost_per_kg),
            "--filament-diameter", "1.75"]
    if supports:
        cmd.append("--support-material")
    cmd.append(str(stl))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not Path(gcode).exists():
        raise RuntimeError(f"slicer failed ({r.returncode}):\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    return parse_gcode(gcode)


def parse_gcode(path):
    res = SliceResult(gcode=Path(path))
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    res.layers = text.count(";LAYER_CHANGE")
    res.support_lines = text.count(";TYPE:Support material")

    def grab(key, default=None):
        m = re.search(rf"^; {re.escape(key)} = (.+)$", text, re.M)
        return m.group(1).strip() if m else default
    res.time_text = grab("estimated printing time (normal mode)", "?")
    res.time_s = _seconds(res.time_text)
    res.filament_mm = float(grab("filament used [mm]", "0").split(",")[0] or 0)
    res.filament_g = float(grab("total filament used [g]", "0") or 0)
    res.cost = float(grab("total filament cost", "0") or 0)
    res.supports_enabled = grab("support_material", "0") == "1"
    res.settings = dict(layer_height=grab("layer_height"), fill_density=grab("fill_density"),
                        nozzle=grab("nozzle_diameter"), printer=grab("printer_model") or "generic")
    return res


def _seconds(text):
    total = 0
    for n, unit in re.findall(r"(\d+)([dhms])", text):
        total += int(n) * dict(d=86400, h=3600, m=60, s=1)[unit]
    return total
