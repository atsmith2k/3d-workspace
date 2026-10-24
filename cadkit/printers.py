"""The printers this workspace targets. `cad build --printer a1mini` picks one; the
default is the Bambu Lab A1. Bed sizes drive the fits-the-bed check, and the Bambu
preset names drive `cad slice` when Bambu Studio is installed.

Design notes for the Bambu A1 series (0.4 mm nozzle, Bambu Studio defaults):
  - line width 0.42 mm: walls print cleanest at multiples (0.84, 1.26, 1.68, 2.10 mm)
  - layer height 0.20 mm standard (0.08-0.28 available): make heights multiples of 0.2
    and put fine horizontal detail on the top, not the bottom
  - textured PEI plate: the bottom face comes out matte with a fine texture, flat
    faces on the bed release easily, elephant's foot compensation 0.075 mm is on
  - no enclosure: PLA, PETG and TPU print fine, ABS/ASA warp on parts over ~100 mm
  - sparse infill 15% by default; use --infill for strength parts
"""

PRINTERS = {
    "a1": dict(
        name="Bambu Lab A1",
        bed=(256.0, 256.0, 256.0),
        nozzle=0.4,
        line_width=0.42,
        machine="Bambu Lab A1 0.4 nozzle",
        process_suffix="@BBL A1",
        filament_suffix="@BBL A1",
    ),
    "a1mini": dict(
        name="Bambu Lab A1 mini",
        bed=(180.0, 180.0, 180.0),
        nozzle=0.4,
        line_width=0.42,
        machine="Bambu Lab A1 mini 0.4 nozzle",
        process_suffix="@BBL A1M",
        filament_suffix="@BBL A1M",
    ),
    "generic": dict(
        name="generic 256 mm printer",
        bed=(256.0, 256.0, 256.0),
        nozzle=0.4,
        line_width=0.42,
    ),
}
DEFAULT = "a1"

# Bambu Studio's process presets, by layer height. "Strength" is 0.20 with more walls.
BAMBU_PROCESS = {0.08: "0.08mm Extra Fine", 0.12: "0.12mm Fine", 0.16: "0.16mm Optimal",
                 0.20: "0.20mm Standard", 0.24: "0.24mm Draft", 0.28: "0.28mm Extra Draft"}
DEFAULT_FILAMENT = "Bambu PLA Basic"


def get(key):
    try:
        return PRINTERS[key.lower().replace("-", "").replace("_", "").replace(" ", "")]
    except KeyError:
        raise SystemExit(f"unknown printer '{key}'; known: {', '.join(PRINTERS)}")
