"""Dimensions of the hardware parts print in and around, so a model never guesses them.

All values are nominal millimetres. Holes print about 0.2 mm undersize on the A1, so
the helper functions add `allowance` (default 0.2) to every hole and pocket diameter;
the raw tables do not. Fits: sliding 0.2 mm per side, press 0.1 mm per side.

    from cadkit.hardware import *
    d = clearance("M3")                 # 3.6 mm: normal clearance + print allowance
    h = insert("M3")                    # dict(hole=4.0, depth=6.2, boss=8.0, ...)
    af, t = nut_pocket("M3")            # hex across-flats and depth for a captive nut
    d, h = magnet_pocket(6, 3)          # press-fit pocket for a 6 x 3 disc magnet
    bore, od, w = bearing("608")
    size, holes, hole_d = board("pi4")  # outline, mounting hole centres, hole diameter

Threads, real screw and nut geometry and bearings come from bd_warehouse
(`from bd_warehouse.fastener import ...`, `from bd_warehouse.thread import IsoThread`);
this table is for the cutouts and pockets that hold them.
"""

ALLOWANCE = 0.2   # mm added to printed hole / pocket diameters

# brass heat-set inserts (McMaster 94459A / ruthex / CNC Kitchen sizes): hole to model,
# depth (insert length + 0.5), minimum boss outside diameter, insert length
HEAT_SET = {
    "M2":   dict(hole=3.2, depth=4.5,  boss=6.0,  insert_len=4.0),
    "M2.5": dict(hole=3.6, depth=5.5,  boss=7.0,  insert_len=5.0),
    "M3":   dict(hole=4.0, depth=6.2,  boss=8.0,  insert_len=5.7),
    "M4":   dict(hole=5.6, depth=8.7,  boss=10.5, insert_len=8.2),
    "M5":   dict(hole=6.4, depth=10.0, boss=12.0, insert_len=9.5),
    "M6":   dict(hole=8.0, depth=13.0, boss=14.0, insert_len=12.7),
}

# ISO 273 clearance holes: close, normal, loose
CLEARANCE = {
    "M2": (2.2, 2.4, 2.6), "M2.5": (2.7, 2.9, 3.1), "M3": (3.2, 3.4, 3.6),
    "M4": (4.3, 4.5, 4.8), "M5": (5.3, 5.5, 5.8), "M6": (6.4, 6.6, 7.0),
    "M8": (8.4, 9.0, 10.0), "M10": (10.5, 11.0, 12.0),
}
# pilot hole for a machine screw to form its own thread in PLA / PETG
SELF_TAP = {"M2": 1.7, "M2.5": 2.1, "M3": 2.6, "M4": 3.5, "M5": 4.4, "M6": 5.3}
# screw head: socket head cap (d, height), countersunk (d, 90 deg), pan head (d, height)
HEAD = {
    "M2":   dict(cap=(3.8, 2.0), csk=4.0, pan=(4.0, 1.6)),
    "M2.5": dict(cap=(4.5, 2.5), csk=5.0, pan=(5.0, 2.0)),
    "M3":   dict(cap=(5.5, 3.0), csk=6.0, pan=(5.6, 2.4)),
    "M4":   dict(cap=(7.0, 4.0), csk=8.0, pan=(8.0, 3.1)),
    "M5":   dict(cap=(8.5, 5.0), csk=10.0, pan=(9.5, 3.7)),
    "M6":   dict(cap=(10.0, 6.0), csk=12.0, pan=(12.0, 4.6)),
    "M8":   dict(cap=(13.0, 8.0), csk=16.0, pan=(16.0, 6.0)),
}
# ISO 4032 hex nuts: across flats, thickness
HEX_NUT = {"M2": (4.0, 1.6), "M2.5": (5.0, 2.0), "M3": (5.5, 2.4), "M4": (7.0, 3.2),
           "M5": (8.0, 4.7), "M6": (10.0, 5.2), "M8": (13.0, 6.8), "M10": (16.0, 8.4)}
# wood screws: shank (clearance) diameter, head diameter, 82 deg countersink
WOOD_SCREW = {"#4": (2.8, 5.5), "#6": (3.5, 6.8), "#8": (4.2, 8.2), "#10": (4.8, 9.5), "#12": (5.5, 10.8)}

# disc magnets commonly sold: (diameter, height)
MAGNETS = [(3, 2), (4, 2), (5, 2), (5, 3), (6, 2), (6, 3), (8, 3), (10, 2), (10, 3), (12, 3), (15, 3), (20, 3)]
# ball bearings: bore, outer diameter, width
BEARINGS = {"608": (8, 22, 7), "625": (5, 16, 5), "623": (3, 10, 4), "624": (4, 13, 5),
            "688": (8, 16, 5), "MR105": (5, 10, 4), "6000": (10, 26, 8), "6001": (12, 28, 8),
            "6002": (15, 32, 9), "6200": (10, 30, 9), "6201": (12, 32, 10)}

# imperial stock, in mm
DOWEL = {"1/8": 3.175, "3/16": 4.763, "1/4": 6.35, "5/16": 7.938, "3/8": 9.525, "1/2": 12.7,
         "5/8": 15.875, "3/4": 19.05, "7/8": 22.225, "1": 25.4, "1-1/4": 31.75}
LUMBER = {"1x2": (19, 38), "1x3": (19, 64), "1x4": (19, 89), "1x6": (19, 140), "2x2": (38, 38),
          "2x4": (38, 89), "2x6": (38, 140), "4x4": (89, 89)}   # actual (thickness, width)
PIPE_PVC_OD = {"1/2": 21.3, "3/4": 26.7, "1": 33.4, "1-1/4": 42.2, "1-1/2": 48.3, "2": 60.3}
METRIC_TUBE_OD = [6, 8, 10, 12, 16, 20, 25, 30, 32, 40, 50]

# connector bodies (w x h) and a cutout that clears them with 0.5 mm per side
PORTS = {
    "usb_c":      dict(body=(9.0, 3.3),  cutout=(10.0, 4.3)),
    "usb_a":      dict(body=(13.2, 5.7), cutout=(14.2, 6.7)),
    "micro_usb":  dict(body=(8.0, 3.0),  cutout=(9.0, 4.0)),
    "hdmi":       dict(body=(15.0, 6.0), cutout=(16.0, 7.0)),
    "micro_hdmi": dict(body=(7.0, 3.0),  cutout=(8.0, 4.0)),
    "rj45":       dict(body=(16.0, 13.5), cutout=(17.0, 14.5)),
    "micro_sd":   dict(body=(12.0, 2.2), cutout=(13.0, 3.2)),
    "jack_3_5":   dict(hole=6.5),
    "barrel_5_5": dict(hole=8.5),
    "sd":         dict(body=(24.5, 2.5), cutout=(25.5, 3.5)),
}

# boards: outline (x, y), mounting hole centres from the bottom-left corner, hole diameter
BOARDS = {
    "pi4":     dict(size=(85.0, 56.0), holes=[(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)], hole=2.7, screw="M2.5"),
    "pi5":     dict(size=(85.0, 56.0), holes=[(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)], hole=2.7, screw="M2.5"),
    "pi3":     dict(size=(85.0, 56.0), holes=[(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)], hole=2.7, screw="M2.5"),
    "pi_zero": dict(size=(65.0, 30.0), holes=[(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)], hole=2.7, screw="M2.5"),
    "pico":    dict(size=(51.0, 21.0), holes=[(2.0, 4.8), (49.0, 4.8), (2.0, 16.2), (49.0, 16.2)], hole=2.1, screw="M2"),
    "uno":     dict(size=(68.6, 53.3), holes=[(14.0, 2.5), (15.3, 50.7), (66.1, 7.6), (66.1, 35.5)], hole=3.2, screw="M3"),
    "nano":    dict(size=(45.0, 18.0), holes=[(1.3, 1.3), (43.7, 1.3), (1.3, 16.7), (43.7, 16.7)], hole=1.8, screw="M1.6"),
    "esp32_devkit": dict(size=(55.0, 28.0), holes=[], hole=0, screw=None),
}

# batteries: (diameter, length) or (w, h, l)
BATTERIES = {"AA": (14.5, 50.5), "AAA": (10.5, 44.5), "C": (26.2, 50.0), "D": (34.2, 61.5),
             "18650": (18.5, 65.2), "21700": (21.2, 70.5), "CR2032": (20.0, 3.2), "9V": (26.5, 17.5, 48.5)}

FIT_SLIDING = 0.2   # per side
FIT_PRESS = 0.1     # per side


# ---------------------------------------------------------------- helpers

def _norm(size):
    s = str(size).upper().replace(" ", "")
    return s if s.startswith("M") else "M" + s


def clearance(size, fit="normal", allowance=ALLOWANCE):
    """Printed clearance hole diameter for a metric screw."""
    close, normal, loose = CLEARANCE[_norm(size)]
    return round(dict(close=close, normal=normal, loose=loose)[fit] + allowance, 2)


def self_tap(size, allowance=0.0):
    """Pilot hole for a screw that forms its own thread in plastic (no allowance: it
    should be snug)."""
    return SELF_TAP[_norm(size)] + allowance


def insert(size, allowance=0.0):
    """Heat-set insert pocket: hole diameter (no allowance: the insert melts in),
    depth, minimum boss diameter."""
    d = dict(HEAT_SET[_norm(size)])
    d["hole"] += allowance
    return d


def nut_pocket(size, clearance_per_side=0.15):
    """(across_flats, depth) for a captive hex nut pocket."""
    af, t = HEX_NUT[_norm(size)]
    return round(af + 2 * clearance_per_side, 2), round(t + 2 * clearance_per_side, 2)


def head_pocket(size, kind="cap", allowance=ALLOWANCE):
    """Counterbore (diameter, depth) for 'cap' or 'pan' heads; (diameter, 90) for 'csk'."""
    h = HEAD[_norm(size)][kind]
    if kind == "csk":
        return h + allowance, 90
    return h[0] + allowance, h[1] + 0.3


def magnet_pocket(d, h, fit="press"):
    """(diameter, depth) pocket for a disc magnet; press holds it, sliding needs glue."""
    extra = FIT_PRESS if fit == "press" else FIT_SLIDING
    return round(d + 2 * extra + ALLOWANCE - 0.1, 2), round(h + 0.2, 2)


def bearing(name, fit="press"):
    """(bore, outer_pocket_diameter, width): the pocket holds the outer race."""
    bore, od, w = BEARINGS[name]
    extra = FIT_PRESS if fit == "press" else FIT_SLIDING
    return bore, round(od + 2 * extra + ALLOWANCE - 0.1, 2), w


def dowel_hole(fraction, fit="sliding"):
    """Hole for an imperial dowel ('1/2' etc.)."""
    extra = FIT_PRESS if fit == "press" else FIT_SLIDING
    return round(DOWEL[fraction] + 2 * extra + ALLOWANCE, 2)


def board(name):
    """(size, hole_centres, hole_diameter) for a dev board, printed allowance included."""
    b = BOARDS[name]
    return b["size"], b["holes"], (b["hole"] + ALLOWANCE if b["hole"] else 0)


def port(name):
    """(w, h) cutout for a connector, or a hole diameter for round jacks."""
    p = PORTS[name]
    return p.get("cutout") or p["hole"]
