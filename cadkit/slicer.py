"""Headless slicing, two backends:

  bambu  Bambu Studio's CLI with the printer's own system presets (A1, A1 mini).
         Produces a sliced project 3MF that opens straight in Bambu Studio, plus the
         print time, filament and layer count Bambu Studio itself would show.
  prusa  PrusaSlicer's console binary with its generic profile; used for the
         generic printer or when Bambu Studio is not installed.

Both are optional; `cad slice` says so if neither is found. Point CAD_BAMBU or
CAD_SLICER at the binaries for unusual installs.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import printers

PRUSA_CANDIDATES = [
    r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe",
    "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
    "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
]
BAMBU_CANDIDATES = [
    r"C:\Program Files\Bambu Studio\bambu-studio.exe",
    "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
]


def _find(env, names, candidates):
    v = os.environ.get(env)
    if v and Path(v).exists():
        return v
    for n in names:
        if shutil.which(n):
            return shutil.which(n)
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def find_prusa():
    return _find("CAD_SLICER", ("prusa-slicer-console", "prusa-slicer", "PrusaSlicer"), PRUSA_CANDIDATES)


def find_bambu():
    return _find("CAD_BAMBU", ("bambu-studio", "BambuStudio"), BAMBU_CANDIDATES)


def find_slicer():
    return find_bambu() or find_prusa()


def bambu_profiles(exe):
    """Folder holding Bambu Studio's system presets."""
    for p in (Path(exe).parent / "resources" / "profiles" / "BBL",
              Path(exe).parent.parent / "Resources" / "profiles" / "BBL"):
        if p.exists():
            return p
    return None


def backend_for(printer_key, prefer="auto"):
    """('bambu' | 'prusa' | None, exe) for this printer and preference."""
    pr = printers.get(printer_key)
    bambu, prusa = find_bambu(), find_prusa()
    if prefer == "bambu" or (prefer == "auto" and "machine" in pr and bambu):
        return ("bambu", bambu) if bambu else (None, None)
    if prusa:
        return "prusa", prusa
    return (("bambu", bambu) if bambu and "machine" in pr else (None, None))


@dataclass
class SliceResult:
    gcode: Path = None
    project: Path = None           # Bambu sliced 3MF, ready to open and print
    printer: str = "generic"
    printer_key: str = "generic"   # cadkit printer key (a1, a1mini, generic)
    slicer: str = ""
    material: str = ""             # PLA / PETG / ... as the slicer recorded it
    time_text: str = "?"
    time_s: int = 0
    filament_mm: float = 0.0
    filament_g: float = 0.0
    filament_name: str = ""
    cost: float = 0.0
    layers: int = 0
    supports_enabled: bool = False
    support_lines: int = 0
    settings: dict = field(default_factory=dict)

    def to_dict(self):
        """Plain JSON-able numbers for slice.json / manifest.json."""
        return dict(
            printer=self.printer_key,
            printer_name=self.printer,
            slicer=self.slicer,
            filament_preset=self.filament_name,
            material=self.material,
            layer_height_mm=_num(self.settings.get("layer_height")),
            infill_pct=_num(str(self.settings.get("fill_density", "")).rstrip("%")),
            process=self.settings.get("process", ""),
            supports=dict(enabled=bool(self.supports_enabled), generated=bool(self.support_lines)),
            print_time_s=int(self.time_s),
            print_time_text=self.time_text,
            layers=int(self.layers),
            filament_g=round(float(self.filament_g), 1),
            filament_m=round(float(self.filament_mm) / 1000, 2),
            cost=round(float(self.cost), 2),
            file=self.project.name if self.project else None,
            gcode=self.gcode.name if self.gcode else None,
            lines=self.lines(),
        )

    def lines(self):
        if self.supports_enabled:
            sup = "yes, generated" if self.support_lines else "enabled, none needed"
        else:
            sup = "off"
        out = [
            f"print    {self.time_text} on {self.printer} ({self.settings.get('process', '?')}, "
            f"{self.settings.get('fill_density', '?')} infill, {self.layers} layers)",
            f"filament {self.filament_g:.0f} g, {self.filament_mm / 1000:.1f} m {self.filament_name}".rstrip()
            + (f"  (~${self.cost:.2f})" if self.cost else ""),
            f"supports {sup}",
        ]
        if self.project:
            out.append(f"project  {self.project.name}  (open in Bambu Studio, it is already sliced)")
        return out


def slice_stl(stl, out_dir, printer_key=printers.DEFAULT, layer_height=0.2, infill=15,
              supports=False, filament=None, profile=None, prefer="auto", timeout=900):
    backend, exe = backend_for(printer_key, prefer)
    if backend is None:
        raise FileNotFoundError("no slicer found; install Bambu Studio or PrusaSlicer "
                                "(or set CAD_BAMBU / CAD_SLICER)")
    if backend == "bambu":
        return slice_bambu(exe, stl, out_dir, printer_key, layer_height, infill, supports, filament, timeout)
    return slice_prusa(exe, stl, out_dir, printer_key, layer_height, infill, supports, profile, timeout)


# ---------------------------------------------------------------- Bambu Studio

def _preset_density(profiles, name, kind="filament"):
    """Walk a preset's `inherits` chain for filament_density (g/cm3)."""
    seen = set()
    while name and name not in seen:
        seen.add(name)
        f = profiles / kind / f"{name}.json"
        if not f.exists():
            break
        d = json.loads(f.read_text(encoding="utf-8"))
        if "filament_density" in d:
            v = d["filament_density"]
            return float(v[0] if isinstance(v, list) else v)
        name = d.get("inherits")
    return 1.24


def _flatten_preset(profiles, kind, name):
    """A system preset with its whole `inherits` chain merged in, child keys winning.
    The CLI only applies the named parent's own keys when a user preset inherits, so
    overrides have to ride on a fully resolved copy."""
    chain = []
    seen = set()
    while name and name not in seen:
        seen.add(name)
        f = profiles / kind / f"{name}.json"
        if not f.exists():
            break
        d = json.loads(f.read_text(encoding="utf-8"))
        chain.append(d)
        name = d.get("inherits")
    merged = {}
    for d in reversed(chain):
        merged.update(d)
    merged.pop("inherits", None)
    return merged


def slice_bambu(exe, stl, out_dir, printer_key, layer_height, infill, supports, filament, timeout):
    pr = printers.get(printer_key)
    if "machine" not in pr:
        raise ValueError(f"printer '{printer_key}' has no Bambu Studio preset")
    profiles = bambu_profiles(exe)
    if not profiles:
        raise FileNotFoundError(f"Bambu Studio presets not found next to {exe}")
    stl = Path(stl)
    filament = filament or printers.DEFAULT_FILAMENT
    filament_name = f"{filament} {pr['filament_suffix']}"
    filament_json = profiles / "filament" / f"{filament_name}.json"
    if not filament_json.exists():
        raise FileNotFoundError(f"no Bambu filament preset '{filament_name}'; see {profiles / 'filament'}")
    base_h = min(printers.BAMBU_PROCESS, key=lambda h: abs(h - layer_height))
    process_name = f"{printers.BAMBU_PROCESS[base_h]} {pr['process_suffix']}"
    machine_json = profiles / "machine" / f"{pr['machine']}.json"

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        override = _flatten_preset(profiles, "process", process_name)
        override.update({"name": f"cadkit {pr['process_suffix']}", "from": "User",
                         "compatible_printers": [pr["machine"]],
                         "layer_height": f"{layer_height:g}",
                         "sparse_infill_density": f"{infill}%",
                         "enable_support": "1" if supports else "0"})
        process_json = tmp / "process.json"
        process_json.write_text(json.dumps(override), encoding="utf-8")
        cmd = [exe, "--load-settings", f"{machine_json};{process_json}",
               "--load-filaments", str(filament_json),
               "--slice", "0", "--export-3mf", "out.3mf", "--outputdir", str(tmp), str(stl)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=tmp)
        result = tmp / "result.json"
        info = json.loads(result.read_text(encoding="utf-8")) if result.exists() else {}
        if info.get("return_code", r.returncode) != 0 or not (tmp / "out.3mf").exists():
            raise RuntimeError(f"Bambu Studio failed: {info.get('error_string', r.stderr[-500:] or 'unknown')}")
        res = SliceResult(printer=pr["name"], printer_key=printer_key, slicer="Bambu Studio",
                          filament_name=filament)
        res.project = Path(out_dir) / f"{stl.stem}_{printer_key}.3mf"
        shutil.move(tmp / "out.3mf", res.project)
        gcode = next(tmp.glob("plate_*.gcode"), None)
        text = gcode.read_text(encoding="utf-8", errors="replace") if gcode else ""

    plate = (info.get("sliced_plates") or [{}])[0]
    res.time_s = int(plate.get("main_predication", 0))
    res.time_text = _hms(res.time_s) if res.time_s else (_grab(text, "model printing time", "?").split(";")[0])
    res.layers = int(_grab(text, "total layer number", "0") or 0)
    res.supports_enabled = supports
    res.support_lines = text.count(";TYPE:Support") + text.count("; FEATURE: Support")
    slice_info = _slice_info(res.project)
    m = re.search(r'used_m="([\d.]+)"', slice_info)
    res.filament_mm = float(m.group(1)) * 1000 if m else 0.0
    res.material = material_of(slice_info, filament)
    dens = _preset_density(profiles, filament_name)
    res.filament_g = res.filament_mm / 10 * 3.14159 * (1.75 / 20) ** 2 * dens   # cm3 * g/cm3
    used_h = _grab(text, "layer_height", f"{layer_height:g}")
    res.settings = dict(process=f"{used_h} mm {printers.BAMBU_PROCESS[base_h].split(' ', 1)[1]}",
                        fill_density=_grab(text, "sparse_infill_density", f"{infill}%"),
                        layer_height=used_h, printer=pr["name"])
    return res


MATERIALS = ("PLA", "PETG", "TPU", "ABS", "ASA", "PA", "PC", "PVA", "PET", "HIPS")


def material_of(slice_info, preset_name=""):
    """Filament material: the `type=` the slicer wrote into slice_info.config, unless
    the preset name clearly says otherwise (Bambu Studio's CLI has written PLA into
    a PETG project), else the preset name, else ''."""
    m = re.search(r'<filament [^>]*\btype="([^"]+)"', slice_info or "")
    recorded = m.group(1).strip() if m else ""
    named = next((t for t in MATERIALS if re.search(rf"\b{t}\b", preset_name or "", re.I)), "")
    if named and recorded and named.upper() != recorded.upper():
        return named
    return recorded or named


def extract_plate_png(project, dest, which="plate_1.png"):
    """Copy the slicer's rendered plate picture out of a sliced 3MF to `dest`.
    Returns dest, or None when the project has no such picture."""
    import zipfile
    try:
        with zipfile.ZipFile(project) as z:
            data = z.read(f"Metadata/{which}")
    except (KeyError, OSError, zipfile.BadZipFile):
        return None
    Path(dest).write_bytes(data)
    return Path(dest)


def _num(v):
    try:
        return float(v) if v not in (None, "", "?") else None
    except (TypeError, ValueError):
        return None


def _slice_info(project):
    import zipfile
    try:
        with zipfile.ZipFile(project) as z:
            return z.read("Metadata/slice_info.config").decode("utf-8", "replace")
    except Exception:
        return ""


# ---------------------------------------------------------------- PrusaSlicer

def slice_prusa(exe, stl, out_dir, printer_key, layer_height, infill, supports, profile, timeout,
                density=1.24, cost_per_kg=25.0):
    pr = printers.get(printer_key)
    stl = Path(stl)
    gcode = Path(out_dir) / f"{stl.stem}.gcode"
    cmd = [exe]
    if profile:
        cmd += ["--load", str(profile)]
    cmd += ["--export-gcode", "--output", str(gcode),
            "--layer-height", str(layer_height), "--fill-density", f"{infill}%",
            "--filament-density", str(density), "--filament-cost", str(cost_per_kg),
            "--filament-diameter", "1.75", "--nozzle-diameter", str(pr["nozzle"]),
            "--bed-shape", f"0x0,{pr['bed'][0]:g}x0,{pr['bed'][0]:g}x{pr['bed'][1]:g},0x{pr['bed'][1]:g}",
            "--max-print-height", f"{pr['bed'][2]:g}"]
    if supports:
        cmd.append("--support-material")
    cmd.append(str(stl))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not gcode.exists():
        raise RuntimeError(f"PrusaSlicer failed ({r.returncode}):\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    res = parse_prusa_gcode(gcode)
    res.printer, res.slicer = pr["name"] + " (PrusaSlicer generic profile)", "PrusaSlicer"
    res.printer_key = printer_key
    res.material = "PLA"   # the generic profile's filament
    res.settings["process"] = f"{layer_height} mm layers"
    return res


def parse_prusa_gcode(path):
    res = SliceResult(gcode=Path(path))
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    res.layers = text.count(";LAYER_CHANGE")
    res.support_lines = text.count(";TYPE:Support material")
    res.time_text = _grab(text, "estimated printing time (normal mode)", "?")
    res.time_s = _seconds(res.time_text)
    res.filament_mm = float(_grab(text, "filament used [mm]", "0").split(",")[0] or 0)
    res.filament_g = float(_grab(text, "total filament used [g]", "0") or 0)
    res.cost = float(_grab(text, "total filament cost", "0") or 0)
    res.supports_enabled = _grab(text, "support_material", "0") == "1"
    res.settings = dict(layer_height=_grab(text, "layer_height"), fill_density=_grab(text, "fill_density"),
                        nozzle=_grab(text, "nozzle_diameter"))
    return res


def _grab(text, key, default=None):
    m = re.search(rf"^; {re.escape(key)}\s*[=:]\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else default


def _seconds(text):
    total = 0
    for n, unit in re.findall(r"(\d+)([dhms])", text):
        total += int(n) * dict(d=86400, h=3600, m=60, s=1)[unit]
    return total


def _hms(s):
    h, rem = divmod(int(s), 3600)
    m, s = divmod(rem, 60)
    return (f"{h}h " if h else "") + f"{m}m {s}s"
