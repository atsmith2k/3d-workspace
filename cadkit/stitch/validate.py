"""An oracle for the machine files we ship that does not share pyembroidery's code.

The files are written by pyembroidery 1.5.1 and stitchsim's readers were transcribed
from pyembroidery's readers, so a writer bug reads back "as intended" and nothing
checked the bytes against what a machine expects. This module decodes every format
again from the published format descriptions, checks the header fields machines check
(a Brother refuses a PES whose PEC colour list disagrees with its body, a Janome
rejects a JEF whose counts are off, a Tajima-compatible machine trusts DST's ST/CO and
extents), and compares its decode with pyembroidery's.

Decoders and their sources (pyembroidery is never imported for decoding):
  PES  v6 header + thread list, PEC block, addendum:
       https://edutechwiki.unige.ch/en/Embroidery_format_PES
  PEC  https://edutechwiki.unige.ch/en/Embroidery_format_PEC
  DST  https://edutechwiki.unige.ch/en/Embroidery_format_DST (Tajima bit table)
  JEF  https://edutechwiki.unige.ch/en/Embroidery_format_JEF
  EXP  https://edutechwiki.unige.ch/en/Embroidery_format_EXP, plus libembroidery
       format-exp.c for 80 80 (the wiki calls it END; libembroidery and every writer
       we have use 80 80 07 00 as a trim)
  VP3  https://edutechwiki.unige.ch/en/Embroidery_format_VP3 (block layout) with
       libembroidery format-vp3.c for the thread record (wiki marks it unfinished)
  XXX  https://edutechwiki.unige.ch/en/Embroidery_format_XXX (header order, 7F codes)
       with libembroidery format-xxx.c for the header offsets 0x27 / 0xFC and 7D/7E
  U01  https://edutechwiki.unige.ch/en/Embroidery_format_U%3F%3F (control byte,
       header part B), libembroidery format-u01.c for the F8 end byte
libembroidery: https://github.com/Embroidermodder/libembroidery (zlib licence).

Coordinates come out absolute, in 0.1 mm, Y up. Commands: stitch (a penetration),
jump (frame moves, no penetration), trim, color (colour change / needle change), stop,
end. Where the documents leave something open the comment says which way we read it.
"""
from dataclasses import dataclass, field
from pathlib import Path
import struct

import numpy as np

STITCH, JUMP, TRIM, COLOR, STOP, END = "stitch", "jump", "trim", "color", "stop", "end"
LONG_MAX = 121          # 0.1 mm; the longest move a DST (ternary) machine makes in one step
CENTRE_TOL = 10         # 0.1 mm; machines position a design on its centre / origin
FORMATS = ("pes", "pec", "dst", "jef", "exp", "vp3", "xxx", "u01")

# PEC palette indices 62-64 are machine functions (Applique Material / Position /
# Applique), not threads: a Brother stops for an applique step on them.
# https://github.com/inkstitch/pystitch/pull/140 (tested on an SE700), edutechwiki PEC
# table; index 0 is not a palette entry at all.
PEC_RESERVED = {0, 62, 63, 64}
PEC_PALETTE_MAX = 64

# JEF hoop codes, edutechwiki JEF: code -> (width, height) in mm
JEF_HOOPS = {0: (110, 110), 1: (50, 50), 2: (140, 200), 3: (126, 110), 4: (200, 200)}


class FormatError(ValueError):
    pass


@dataclass
class Decoded:
    fmt: str
    records: list                   # [(x, y, cmd)], absolute 0.1 mm, Y up
    header: dict = field(default_factory=dict)
    colors: list = field(default_factory=list)
    problems: list = field(default_factory=list)   # structure faults found while decoding

    @property
    def penetrations(self):
        return np.array([(x, y) for x, y, c in self.records if c == STITCH], float).reshape(-1, 2)

    def extents(self):
        """(min_x, min_y, max_x, max_y) of the penetrations, 0.1 mm."""
        p = self.penetrations
        if not len(p):
            return (0, 0, 0, 0)
        return (p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max())

    def color_changes(self):
        return sum(1 for *_, c in self.records if c == COLOR)

    def trims(self):
        """Trims that cut sewn thread (repeats and trims before any stitch collapse)."""
        n, sewn = 0, False
        for *_, c in self.records:
            if c == STITCH:
                sewn = True
            elif c == TRIM and sewn:
                n, sewn = n + 1, False
            elif c == COLOR:
                sewn = False
        return n

    def cut_connectors(self):
        """Trims between two runs of one colour: the same in every format (a trim before
        a colour change or the end is implicit in some formats, explicit in others)."""
        n, sewn, cut = 0, False, False
        for *_, c in self.records:
            if c == STITCH:
                n += cut
                sewn, cut = True, False
            elif c == TRIM and sewn:
                cut = True
            elif c == COLOR:
                sewn, cut = False, False
        return n


def _s8(b):
    return b - 256 if b > 127 else b


def _s12(v):
    return v - 4096 if v > 2047 else v


class _Walker:
    """Accumulates relative moves into absolute records."""

    def __init__(self, x=0, y=0):
        self.x, self.y, self.out = x, y, []

    def move(self, dx, dy, cmd):
        self.x += dx
        self.y += dy
        self.out.append((self.x, self.y, cmd))

    def cmd(self, cmd):
        self.out.append((self.x, self.y, cmd))


# --------------------------------------------------------------------- PEC / PES

def _pec_block(data, p, dec):
    """Decode a PEC block starting at byte `p` (the 'LA:' label) into `dec`."""
    if data[p:p + 3] != b"LA:":
        raise FormatError(f"PEC block at {p} does not start with 'LA:'")
    h = dec.header
    h["pec_start"] = p
    h["label"] = data[p + 3:p + 19]
    h["label_cr"] = data[p + 0x13]
    h["thumb_w"], h["thumb_h"] = data[p + 0x22], data[p + 0x23]
    n = data[p + 0x30]
    ncol = 0 if n == 0xFF else n + 1
    h["pec_colors"] = ncol
    h["palette"] = list(data[p + 0x31:p + 0x31 + ncol])
    s = p + 0x200
    # 0x202: offset of the thumbnails from PEC+512 (the wiki calls it u16 followed by a
    # fixed 00; read as 24-bit, which is the same for every file under 16 MB)
    h["graphic_offset"] = data[s + 2] | data[s + 3] << 8 | data[s + 4] << 16
    h["pec_width"], h["pec_height"] = struct.unpack_from("<hh", data, s + 8)
    i = s + 0x10                # first pair: move from the origin to the first stitch
    w = _Walker()
    changes = []
    end = None
    while i < len(data):
        b = data[i]
        if b == 0xFF:
            end = i
            break
        if b == 0xFE and i + 1 < len(data) and data[i + 1] == 0xB0:
            changes.append(data[i + 2])
            w.cmd(COLOR)
            i += 3
            continue
        vals, flags = [], 0
        for _ in range(2):
            b = data[i]
            if b & 0x80:        # long form: 1 fff vvvv vvvvvvvv, f = 0x20 trim, 0x10 jump
                flags |= b & 0x70
                vals.append(_s12(((b & 0x0F) << 8) | data[i + 1]))
                i += 2
            else:               # short form: 7-bit two's complement
                vals.append(b - 128 if b > 63 else b)
                i += 1
        if flags & 0x20:
            cmd = TRIM
        elif flags & 0x10:
            cmd = JUMP
        else:
            cmd = STITCH
        if cmd == TRIM:         # a trim flag on a move: the frame moves, thread is cut
            w.cmd(TRIM)
            cmd = JUMP
        w.move(vals[0], -vals[1], cmd)      # PEC y grows downward
    if end is None:
        dec.problems.append("PEC stitch list has no 0xFF end marker")
        end = len(data) - 1
    w.cmd(END)
    h["pec_end"] = end
    h["pec_color_bytes"] = changes
    dec.records = w.out
    thumbs = s + h["graphic_offset"]
    h["thumb_start"] = thumbs
    h["thumb_bytes"] = h["thumb_w"] * h["thumb_h"] * (ncol + 1)
    return thumbs + h["thumb_bytes"]


def _pstr(data, i):
    n = data[i]
    return data[i + 1:i + 1 + n], i + 1 + n


def decode_pes(data):
    dec = Decoded("pes", [])
    h = dec.header
    if data[:4] != b"#PES":
        raise FormatError("not a PES file (no #PES magic)")
    h["version"] = data[4:8].decode("latin-1")
    pec = struct.unpack_from("<I", data, 8)[0]
    h["pec_offset"] = pec
    if not 12 <= pec < len(data):
        raise FormatError(f"PEC offset {pec} is outside the file ({len(data)} bytes)")
    if h["version"] == "0060":
        # v6 header field order from the edutechwiki PES table
        i = 16                                          # hoop indicator u16, subversion 2 chars
        for _ in range(5):                              # design, category, author, keywords, comments
            _, i = _pstr(data, i)
        i += 2 * 2                                      # optimize hoop change, custom page
        h["hoop_w"], h["hoop_h"] = struct.unpack_from("<HH", data, i)
        i += 4 + 2                                      # hoop, hoop rotation
        i += 13 * 2                                     # design / page sizes ... optimize entry/exit
        _, i = _pstr(data, i)                           # image file name
        i += 24                                         # image affine
        counts = struct.unpack_from("<HHH", data, i)    # fill patterns, motifs, feathers
        i += 6
        if any(counts):
            dec.problems.append(f"v6 header has pattern/motif/feather records {counts}; "
                                "thread list not checked")
        else:
            nth = struct.unpack_from("<H", data, i)[0]
            i += 2
            threads = []
            for _ in range(nth):
                code, i = _pstr(data, i)
                r, g, b = data[i:i + 3]
                i += 4                                  # rgb + padding
                kind = struct.unpack_from("<I", data, i)[0]
                i += 4
                name, i = _pstr(data, i)
                _, i = _pstr(data, i)                   # brand
                _, i = _pstr(data, i)                   # chart
                threads.append(dict(code=code, rgb="#%02x%02x%02x" % (r, g, b), type=kind,
                                    name=name.decode("latin-1")))
            h["threads"] = threads
            dec.colors = [t["rgb"] for t in threads]
            if i > pec:
                dec.problems.append("v6 thread list runs into the PEC block")
    after = _pec_block(data, pec, dec)
    h["after_thumbs"] = after
    return dec


def decode_pec(data):
    if data[:8] != b"#PEC0001":
        raise FormatError("not a PEC file (no #PEC0001 magic)")
    dec = Decoded("pec", [])
    dec.header["after_thumbs"] = _pec_block(data, 8, dec)
    return dec


# --------------------------------------------------------------------------- DST

# Tajima bit table (edutechwiki DST): byte -> [(bit, dx, dy)]
_DST = (
    ((7, 0, 1), (6, 0, -1), (5, 0, 9), (4, 0, -9), (3, -9, 0), (2, 9, 0), (1, -1, 0), (0, 1, 0)),
    ((7, 0, 3), (6, 0, -3), (5, 0, 27), (4, 0, -27), (3, -27, 0), (2, 27, 0), (1, -3, 0), (0, 3, 0)),
    ((5, 0, 81), (4, 0, -81), (3, -81, 0), (2, 81, 0)),
)


def _before(out):
    return (out[-1][0], out[-1][1]) if out else (0, 0)


def decode_dst(data):
    dec = Decoded("dst", [])
    h = dec.header
    if len(data) < 512:
        raise FormatError("DST shorter than its 512-byte header")
    head = data[:512].split(b"\x1a")[0]
    for line in head.split(b"\r"):
        if len(line) >= 3 and line[2:3] == b":":
            h[line[:2].decode("latin-1")] = line[3:].decode("latin-1")
    w = _Walker()
    body = data[512:]
    h["tail"] = len(body) % 3
    for k in range(0, len(body) - 2, 3):
        rec = body[k:k + 3]
        if rec == b"\x00\x00\xf3":
            w.cmd(END)
            h["end_at"] = 512 + k
            break
        dx = dy = 0
        for byte, table in zip(rec, _DST):
            for bit, ax, ay in table:
                if byte >> bit & 1:
                    dx, dy = dx + ax, dy + ay
        if (rec[2] & 3) != 3:
            dec.problems.append(f"DST record at {512 + k} lacks the always-set bits 0,1 of byte 3")
        flag = rec[2] & 0xC0
        if flag == 0xC0:                    # colour change (or stop), may carry a move
            if dx or dy:
                w.move(dx, dy, JUMP)
            w.cmd(COLOR)
        elif flag == 0x80:
            w.move(dx, dy, JUMP)
        elif flag == 0x40:                  # sequin mode toggle; we never write it
            w.move(dx, dy, JUMP)
            dec.problems.append(f"DST sequin record at {512 + k}")
        else:
            w.move(dx, dy, STITCH)
    else:
        dec.problems.append("DST body has no 00 00 F3 end record")
    # DST has no trim code: a run of 3+ jumps is how it says trim (edutechwiki DST, TRIM;
    # Tajima-compatible machines cut there)
    out, run, h["trim_jumps"] = [], [], 0
    for r in w.out + [(0, 0, None)]:
        if r[2] == JUMP:
            run.append(r)
            continue
        if len(run) >= 3:
            out.append((*_before(out), TRIM))
            h["trim_jumps"] += len(run)
        out += run
        run = []
        if r[2] is not None:
            out.append(r)
    w.out = out
    dec.records = w.out
    return dec


# --------------------------------------------------------------------------- JEF

def decode_jef(data):
    dec = Decoded("jef", [])
    h = dec.header
    off, _, = struct.unpack_from("<II", data, 0)
    h["stitch_offset"] = off
    h["date"] = data[8:22]
    h["colors"], h["points"], h["hoop"] = struct.unpack_from("<iii", data, 24)
    h["extents"] = struct.unpack_from("<4i", data, 36)          # left, top, right, bottom
    h["hoop_edges"] = [struct.unpack_from("<4i", data, 52 + 16 * k) for k in range(4)]
    n = max(0, min(h["colors"], 256))
    h["palette"] = list(struct.unpack_from(f"<{n}i", data, 116)) if 116 + 4 * n <= len(data) else []
    h["thread_types"] = (list(struct.unpack_from(f"<{n}i", data, 116 + 4 * n))
                         if 116 + 8 * n <= len(data) else [])
    w = _Walker()
    i = off
    h["end_at"] = None
    while i + 1 < len(data):
        b0, b1 = data[i], data[i + 1]
        if b0 == 0x80:
            if b1 == 0x10:
                w.cmd(END)
                h["end_at"] = i
                i += 2
                break
            dx, dy = _s8(data[i + 2]), _s8(data[i + 3])
            i += 4
            if b1 == 0x01:
                w.move(dx, dy, JUMP)
                w.cmd(COLOR)
            elif b1 == 0x02:
                if dx == 0 and dy == 0:     # zero jump = trim (edutechwiki JEF)
                    w.cmd(TRIM)
                else:
                    w.move(dx, dy, JUMP)
            else:
                dec.problems.append(f"JEF unknown command 80 {b1:02x} at {i - 4}")
            continue
        w.move(_s8(b0), _s8(b1), STITCH)
        i += 2
    if h["end_at"] is None:
        dec.problems.append("JEF has no 80 10 end command")
    h["stitch_bytes"] = i - off
    dec.records = w.out
    return dec


# --------------------------------------------------------------------------- EXP

def decode_exp(data):
    dec = Decoded("exp", [])
    w = _Walker()
    i = 0
    while i + 1 < len(data):
        b0, b1 = data[i], data[i + 1]
        if b0 == 0x80:
            if i + 3 >= len(data):
                dec.problems.append("EXP ends inside a command")
                break
            dx, dy = _s8(data[i + 2]), _s8(data[i + 3])
            i += 4
            if b1 == 0x01:
                w.move(dx, dy, JUMP)
                w.cmd(COLOR)
            elif b1 == 0x02:
                w.move(dx, dy, STITCH)
            elif b1 == 0x04:
                w.move(dx, dy, JUMP)
            elif b1 == 0x80:            # 80 80 07 00: trim (libembroidery format-exp.c)
                w.cmd(TRIM)
            else:
                dec.problems.append(f"EXP unknown command 80 {b1:02x} at {i - 4}")
            continue
        w.move(_s8(b0), _s8(b1), STITCH)
        i += 2
    if i < len(data):
        dec.problems.append("EXP has an odd trailing byte")
    w.cmd(END)                          # EXP has no end code: the file just stops
    dec.records = w.out
    return dec


# --------------------------------------------------------------------------- VP3

def decode_vp3(data):
    dec = Decoded("vp3", [])
    h = dec.header
    if data[:6] != b"%vsm%\x00":
        raise FormatError("not a VP3 file (no %vsm% magic)")
    i = 6
    n = struct.unpack_from(">H", data, i)[0]
    i += 2 + n
    if data[i:i + 3] != b"\x00\x02\x00":
        raise FormatError("VP3 file-data tag 00 02 00 missing")
    i += 3
    h["to_eof"] = struct.unpack_from(">I", data, i)[0]
    i += 4
    h["eof_ok"] = i + h["to_eof"] == len(data)
    n = struct.unpack_from(">H", data, i)[0]
    i += 2 + n
    # extents in microns (Right, -Top, Left, -Bottom with Y down = maxX, maxY, minX, minY Y up)
    h["extents"] = struct.unpack_from(">4i", data, i)
    i += 16
    i += 4                              # stitch count (not in the wiki; not checked)
    h["count_threads"] = data[i + 1]
    h["count_designs"] = data[i + 4]
    i += 5
    if data[i:i + 3] != b"\x00\x03\x00":
        raise FormatError("VP3 design tag 00 03 00 missing")
    i += 3
    h["design_bytes"] = struct.unpack_from(">I", data, i)[0]
    h["design_end_ok"] = i + 4 + h["design_bytes"] == len(data)
    i += 4
    cx, ncy = struct.unpack_from(">ii", data, i)
    h["center"] = (cx, ncy)             # microns; "-center_y" of a Y-down centre = Y up
    i += 8 + 3
    h["half"] = struct.unpack_from(">4i", data, i)
    j = data.find(b"xxPP\x01\x00", i)
    if j < 0:
        raise FormatError("VP3 xxPP marker missing")
    i = j + 6
    n = struct.unpack_from(">H", data, i)[0]
    i += 2 + n
    ncol = struct.unpack_from(">H", data, i)[0]
    i += 2
    h["colors"] = ncol
    w = _Walker()
    for k in range(ncol):
        if data[i:i + 3] != b"\x00\x05\x00":
            dec.problems.append(f"VP3 colour block {k + 1} tag 00 05 00 missing at {i}")
            break
        i += 3
        nxt = i + 4 + struct.unpack_from(">I", data, i)[0]
        i += 4
        sx, sy = struct.unpack_from(">ii", data, i)
        i += 8
        # block start relative to the design centre; start and shift fields are Y up,
        # the stitch bytes below Y down (checked against the PES of the same design)
        start = ((cx + sx) / 100, (ncy + sy) / 100)
        if k == 0:
            w.x, w.y = start
        elif max(abs(start[0] - w.x), abs(start[1] - w.y)) > 1.0:
            dec.problems.append(f"VP3 colour block {k + 1} starts {start}, previous ended "
                                f"({w.x:.0f}, {w.y:.0f})")
        tsize = data[i]
        rgb = data[i + 2:i + 5]
        i += 4 + 6 * tsize              # thread table (libembroidery format-vp3.c)
        dec.colors.append("#%02x%02x%02x" % tuple(rgb))
        for _ in range(3):              # catalogue, description, brand
            n = struct.unpack_from(">H", data, i)[0]
            i += 2 + n
        shift = struct.unpack_from(">ii", data, i)
        i += 8
        if data[i:i + 3] != b"\x00\x01\x00":
            dec.problems.append(f"VP3 stitch tag missing in block {k + 1}")
            break
        i += 3
        send = i + 4 + struct.unpack_from(">I", data, i)[0]
        i += 4
        if data[i:i + 3] != b"\x0a\xf6\x00":
            dec.problems.append(f"VP3 stitch start marker 0A F6 00 missing in block {k + 1}")
        i += 3
        if k:
            w.cmd(COLOR)
        x0, y0 = w.x, w.y
        while i < send - 1:
            b0, b1 = data[i], data[i + 1]
            if b0 == 0x80:
                if b1 == 0x01:          # long form: s16 x, s16 y, then 80 02. VP3 has no
                    dx, dy = struct.unpack_from(">hh", data, i + 2)   # jump: it is sewn
                    i += 8
                    w.move(dx, -dy, STITCH)
                    continue
                if b1 == 0x03:          # the wiki calls 80 03 end-of-block, libembroidery
                    w.cmd(TRIM)         # skips it; Husqvarna/Pfaff machines cut on it
                    i += 2
                    continue
                if b1 == 0x02:
                    i += 2
                    continue
                dec.problems.append(f"VP3 unknown command 80 {b1:02x} at {i}")
                i += 2
                continue
            w.move(_s8(b0), -_s8(b1), STITCH)
            i += 2
        if i != send - 1 and i != send:
            dec.problems.append(f"VP3 block {k + 1} stitch data length off by {i - send}")
        got = ((w.x - x0) * 100, (w.y - y0) * 100)
        if max(abs(got[0] - shift[0]), abs(got[1] - shift[1])) > 100:
            dec.problems.append(f"VP3 block {k + 1} shift field {shift} microns, stitches move "
                                f"({got[0]:.0f}, {got[1]:.0f})")
        i = nxt
    w.cmd(END)
    dec.records = w.out
    return dec


# --------------------------------------------------------------------------- XXX

def decode_xxx(data):
    dec = Decoded("xxx", [])
    h = dec.header
    h["count_minus_one"] = struct.unpack_from("<I", data, 0x17)[0]
    h["colors"] = struct.unpack_from("<H", data, 0x27)[0]
    h["width"], h["height"], h["last_x"], h["last_y"] = struct.unpack_from("<hhhh", data, 0x2D)
    pal = struct.unpack_from("<I", data, 0xFC)[0]
    h["palette_offset"] = pal
    w = _Walker()
    i, n, ended = 0x100, 0, False
    while i + 1 < min(pal, len(data)):
        b0, b1 = data[i], data[i + 1]
        if b0 in (0x7D, 0x7E):          # big move: s16 dx, s16 dy
            dx, dy = struct.unpack_from("<hh", data, i + 1)
            i += 5
            n += 1
            w.cmd(TRIM)
            w.move(dx, dy, JUMP)
            continue
        if b0 == 0x7F:
            dx, dy = _s8(data[i + 2]), _s8(data[i + 3])
            i += 4
            n += 1
            if b1 == 0x7F:
                w.cmd(END)
                ended = True
                break
            if b1 == 0x01:
                w.move(dx, dy, JUMP)
            elif b1 == 0x03:
                w.cmd(TRIM)
                if dx or dy:
                    w.move(dx, dy, JUMP)
            elif b1 >= 0x08:
                if dx or dy:
                    w.move(dx, dy, JUMP)
                w.cmd(COLOR)
            else:
                dec.problems.append(f"XXX unknown command 7F {b1:02x} at {i - 4}")
            continue
        w.move(_s8(b0), _s8(b1), STITCH)
        i += 2
        n += 1
    if not ended and data[pal:pal + 2] == b"\x7f\x7f":
        w.cmd(END)                      # the palette offset points at the 7F 7F end code
        ended = True
        n += 1
    if not ended:
        dec.problems.append("XXX has no 7F 7F end command")
        w.cmd(END)
    h["records"] = n
    h["body_end"] = i
    dec.colors = ["#%02x%02x%02x" % tuple(data[pal + 7 + 4 * k:pal + 10 + 4 * k])
                  for k in range(h["colors"]) if pal + 10 + 4 * k <= len(data)]
    dec.records = w.out
    return dec


# --------------------------------------------------------------------------- U01

def decode_u01(data):
    dec = Decoded("u01", [])
    h = dec.header
    h["extents"] = struct.unpack_from("<4h", data, 0x80)        # left, bottom, right, top
    # the wiki types 0x88 and the count as u32 but sizes them 2; real files hold
    # u32 0 at 0x88, u32 count at 0x8C and the final position at 0x90
    h["count"] = struct.unpack_from("<I", data, 0x8C)[0]
    h["final"] = struct.unpack_from("<hh", data, 0x90)
    w = _Walker()
    i, n, ended, needle = 0x100, 0, False, None
    while i + 2 < len(data) + 0:
        c, by, bx = data[i], data[i + 1], data[i + 2]
        i += 3
        n += 1
        cmd = c & 0x1F
        dx = -bx if c & 0x20 else bx
        dy = -by if c & 0x40 else by
        if cmd == 0x18 or c == 0xF8:    # end (libembroidery reads F8; the wiki table says 18)
            w.cmd(END)
            ended = True
            break
        if cmd in (0, 2, 4):
            w.move(dx, dy, STITCH)
        elif cmd in (1, 3, 5):
            w.move(dx, dy, JUMP)
        elif cmd in (6, 7):
            if dx or dy:
                w.move(dx, dy, JUMP)
            w.cmd(TRIM)
        elif cmd == 8:
            w.cmd(STOP)
        elif 9 <= cmd <= 17:            # needle 1-9: a colour change unless it is the first
            if dx or dy:
                w.move(dx, dy, JUMP)
            if needle is not None:
                w.cmd(COLOR)
            needle = cmd - 8
        else:
            dec.problems.append(f"U01 control {cmd} at {i - 3}")
    if not ended:
        dec.problems.append("U01 has no end command")
        w.cmd(END)
    h["records"] = n
    dec.records = w.out
    return dec


DECODERS = dict(pes=decode_pes, pec=decode_pec, dst=decode_dst, jef=decode_jef,
                exp=decode_exp, vp3=decode_vp3, xxx=decode_xxx, u01=decode_u01)


def _fmt(path):
    return Path(path).suffix.lower().lstrip(".")


def decode(path):
    fmt = _fmt(path)
    if fmt not in DECODERS:
        raise FormatError(f"no independent decoder for .{fmt}")
    return DECODERS[fmt](Path(path).read_bytes())


# -------------------------------------------------------------------- validators

UNTRIMMED = 30         # 0.1 mm; pattern.SHORT_JUMP: shorter connectors are sewn on purpose


def _untrimmed(dec):
    """Lengths of moves between two penetrations made by jumps with no trim between."""
    out, last, moved, cut = [], None, False, False
    for x, y, c in dec.records:
        if c == STITCH:
            if moved and not cut and last is not None:
                d = float(np.hypot(x - last[0], y - last[1]))
                if d > UNTRIMMED:
                    out.append(d)
            last, moved, cut = (x, y), False, False
        elif c == JUMP:
            moved = True
        elif c in (TRIM, COLOR):
            cut = True
    return out


def _common(dec, centred=True):
    """Rules for every format, on the decoded stitches."""
    probs = []
    zero, long_, prev, last_pen = 0, [], None, None
    for x, y, c in dec.records:
        if c == STITCH:
            if prev == STITCH and last_pen == (x, y):
                zero += 1           # two penetrations in one hole: machines have frozen on them
            elif prev == STITCH and last_pen is not None:
                d = float(np.hypot(x - last_pen[0], y - last_pen[1]))
                if d > LONG_MAX + 0.5:
                    long_.append(d)     # over 12.1 mm: a move written as a stitch
            last_pen = (x, y)
        if c != END:
            prev = c
    if zero:
        probs.append(f"{zero} zero-length stitches (doubled penetrations)")
    unt = _untrimmed(dec)
    if unt:
        probs.append(f"{len(unt)} jumps over {UNTRIMMED / 10} mm with no trim, up to "
                     f"{max(unt) / 10:.1f} mm (thread dragged across the design)")
    if long_:
        probs.append(f"{len(long_)} sewn stitches over {LONG_MAX / 10} mm, up to "
                     f"{max(long_) / 10:.1f} mm")
    if centred and len(dec.penetrations):
        x0, y0, x1, y1 = dec.extents()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if max(abs(cx), abs(cy)) > CENTRE_TOL:
            probs.append(f"design centre at ({cx / 10:.1f}, {cy / 10:.1f}) mm, not on the origin")
    if not dec.records or dec.records[-1][2] != END:
        probs.append("no end command")
    return probs


def _v_pec(dec, data):
    h, probs = dec.header, []
    p = h["pec_start"]
    # LA: 16 printable ASCII characters, then CR (edutechwiki PEC header; non-ASCII has
    # corrupted machine screens and file lists)
    lab = h["label"]
    if len(lab) != 16 or any(not 0x20 <= ch < 0x7F for ch in lab):
        probs.append(f"PEC label {lab!r} is not 16 printable ASCII characters")
    if not lab.strip():
        probs.append("PEC label is blank (the machine shows no name)")
    if h["label_cr"] != 0x0D:
        probs.append("PEC label not terminated by 0x0D")
    if (h["thumb_w"], h["thumb_h"]) != (6, 38):
        probs.append(f"PEC thumbnail {h['thumb_w'] * 8}x{h['thumb_h']}, machines expect 48x38")
    ncol = h["pec_colors"]
    # colour list count = colour changes + 1 (edutechwiki PEC: N = colours - 1)
    nchg = len(h["pec_color_bytes"])
    if ncol != nchg + 1:
        probs.append(f"PEC header lists {ncol} colours, stitch list has {nchg} colour changes")
    bad = [k for k in h["palette"] if k in PEC_RESERVED or k > PEC_PALETTE_MAX]
    if bad:
        # https://github.com/inkstitch/pystitch/pull/140: 62-64 are applique functions
        probs.append(f"PEC palette uses reserved/out-of-range indices {sorted(set(bad))}")
    # FE B0 xx: xx alternates 2, 1, 2, ... (edutechwiki PEC, colour change)
    want = [2 if k % 2 == 0 else 1 for k in range(nchg)]
    if h["pec_color_bytes"] != want:
        probs.append(f"PEC colour-change bytes {h['pec_color_bytes']} should alternate 2,1")
    # stitch block length: the graphic offset must land right after the 0xFF end
    if h["thumb_start"] != h["pec_end"] + 1:
        probs.append(f"PEC graphic offset {h['graphic_offset']} does not point past the end "
                     f"marker (stitch list ends {h['pec_end'] + 1 - p - 0x200})")
    if h["thumb_start"] + h["thumb_bytes"] > len(data):
        probs.append(f"PEC thumbnails ({ncol + 1} x 228 bytes) run past the end of the file")
    x0, y0, x1, y1 = dec.extents()
    if abs(h["pec_width"] - (x1 - x0)) > 1 or abs(h["pec_height"] - (y1 - y0)) > 1:
        probs.append(f"PEC size field {h['pec_width']}x{h['pec_height']}, stitches span "
                     f"{x1 - x0:.0f}x{y1 - y0:.0f}")
    # END 0xFF inside the first stitch's coordinates: a 12-bit move whose bytes read FF FE
    # makes the machine stop there (pyembroidery issue 132). Caught as the list ending
    # early: the end marker would then not be followed by the thumbnails.
    return probs


def validate(path):
    """Structure problems a machine would trip on: [] when the file is fine."""
    path = Path(path)
    fmt = _fmt(path)
    data = path.read_bytes()
    try:
        dec = DECODERS[fmt](data)
    except (FormatError, struct.error, IndexError) as e:
        return [f"cannot decode: {e}"]
    probs = list(dec.problems)
    h = dec.header
    if fmt in ("pes", "pec"):
        probs += _v_pec(dec, data)
        probs += _common(dec, centred=False)    # the machine centres PEC on its extents
    if fmt == "pes":
        if h["version"] != "0060":
            probs.append(f"PES version {h['version']}, we write 0060 (v6: exact RGB)")
        th = h.get("threads")
        if th is not None and len(th) != h["pec_colors"]:
            # v6 colour list = PEC colour changes + 1 (edutechwiki PES colour subsection)
            probs.append(f"PES v6 header lists {len(th)} threads, PEC has {h['pec_colors']} colours")
        # v4-v6 addendum after the PEC thumbnails: 128-byte index block, then 144 bytes and
        # an RGB triple per colour, then 00 00 for v6. "For a successful write of V6 it
        # must be included." (edutechwiki PES). A blank block (FF + 127 spaces) is valid.
        a = h["after_thumbs"]
        rest = data[a:]
        if len(rest) < 130:
            probs.append(f"PES v6 addendum missing ({len(rest)} bytes after the thumbnails)")
        else:
            n = rest[0]
            na = 0 if n == 0xFF else n + 1
            if na and na != h["pec_colors"]:
                probs.append(f"PES addendum lists {na} colours, PEC has {h['pec_colors']}")
            if na and list(rest[1:1 + na]) != h["palette"]:
                probs.append("PES addendum palette indices differ from the PEC header")
            size = 128 + 147 * na + 2
            if len(rest) != size:
                probs.append(f"PES addendum is {len(rest)} bytes, {na} colours need {size}")
            elif rest[-2:] != b"\x00\x00":
                probs.append("PES v6 addendum lacks the 00 00 trailer")
    elif fmt == "dst":
        probs += _v_dst(dec, data)
        probs += _common(dec)
    elif fmt == "jef":
        probs += _v_jef(dec, data)
        probs += _common(dec)
    elif fmt == "exp":
        probs += _common(dec)
    elif fmt == "vp3":
        probs += _v_vp3(dec)
        probs += _common(dec)
    elif fmt == "xxx":
        probs += _v_xxx(dec)
        probs += _common(dec)
    elif fmt == "u01":
        probs += _v_u01(dec)
        probs += _common(dec)
    return probs


def _num(s):
    try:
        return int(s.replace(" ", "").replace("+", ""))
    except (ValueError, AttributeError):
        return None


def _v_dst(dec, data):
    h, probs = dec.header, []
    # edutechwiki DST header: LA ST CO +X -X +Y -Y AX AY MX MY PD
    for key in ("LA", "ST", "CO", "+X", "-X", "+Y", "-Y", "AX", "AY", "MX", "MY", "PD"):
        if key not in h:
            probs.append(f"DST header field {key} missing")
    if probs:
        return probs
    if not h["LA"].strip():
        probs.append("DST label LA is blank")
    if h["tail"] != 0:
        probs.append(f"DST body is not whole 3-byte records ({h['tail']} spare bytes)")
    end = h.get("end_at")
    if end is not None and end + 3 != len(data):
        probs.append(f"DST has {len(data) - end - 3} bytes after the 00 00 F3 end record")
    nrec = (h.get("end_at", len(data)) - 512) // 3 + 1
    # ST: every record including jumps, colour changes and the end record, as written by
    # Tajima-compatible software (edutechwiki: "including color changes, jumps")
    # ST: edutechwiki counts every record (jumps, colour changes, end); other software
    # counts fewer (pyembroidery leaves out the jumps that spell a trim). Accept anything
    # from the penetration count to the record count; outside that the header lies.
    st = _num(h["ST"])
    if st is None or not len(dec.penetrations) <= st <= nrec:
        probs.append(f"DST header ST {st}, body has {len(dec.penetrations)} stitches in "
                     f"{nrec} records")
    co = _num(h["CO"])
    if co != dec.color_changes():
        probs.append(f"DST header CO {co}, body has {dec.color_changes()} colour changes")
    # extents of the penetrations, 0.1 mm (the +-2 wiggle that spells a trim can poke
    # past them). edutechwiki's table says cm but its example values are 0.1 mm, which
    # is what every reader uses.
    pts = dec.penetrations if len(dec.penetrations) else np.zeros((1, 2))
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    px, nx, py, ny = (_num(h[k]) for k in ("+X", "-X", "+Y", "-Y"))
    if (px, nx) != (round(x1), round(-x0)):
        probs.append(f"DST +X/-X {px}/{nx}, body spans {x1:.0f}/{-x0:.0f}")
    # +Y/-Y: pyembroidery and libembroidery both write +Y as the downward extent (their
    # internal Y grows down); the wiki does not say which. Accept either order.
    if sorted((py, ny)) != sorted((round(y1), round(-y0))):
        probs.append(f"DST +Y/-Y {py}/{ny}, body spans {y1:.0f}/{-y0:.0f}")
    last = dec.records[-1]
    ax, ay = _num(h["AX"]), _num(h["AY"])
    if (ax, abs(ay)) != (round(last[0]), abs(round(last[1]))):
        probs.append(f"DST AX/AY {ax}/{ay}, design ends at ({last[0]:.0f}, {last[1]:.0f})")
    # every record moves at most 121 (1+3+9+27+81) per axis: the bit table cannot hold more
    allp = np.array([(x, y) for x, y, c in dec.records], float)
    rel = np.diff(np.vstack([[0, 0], allp]), axis=0)
    if len(rel) and np.abs(rel).max() > LONG_MAX:
        probs.append(f"DST record moves {np.abs(rel).max():.0f} > 121 in one step")
    if data[-3:] != b"\x00\x00\xf3":
        probs.append("DST does not end with 00 00 F3")
    return probs


def _v_jef(dec, data):
    h, probs = dec.header, []
    ncol = h["colors"]
    # header colour count = colour changes + 1, stitch offset = 0x74 + 8 x colours
    # (edutechwiki JEF); Janome machines reject files where they disagree
    if ncol != dec.color_changes() + 1:
        probs.append(f"JEF header lists {ncol} colours, body has {dec.color_changes()} changes")
    if h["stitch_offset"] != 0x74 + 8 * ncol:
        probs.append(f"JEF stitch offset {h['stitch_offset']}, {ncol} colours put it at "
                     f"{0x74 + 8 * ncol}")
    # point count: stitch-data bytes / 2, end command included ("points length / 2")
    if h["points"] * 2 != h["stitch_bytes"]:
        probs.append(f"JEF point count {h['points']}, stitch data is {h['stitch_bytes'] // 2}")
    if h["end_at"] is not None and h["end_at"] + 2 != len(data):
        probs.append(f"JEF has {len(data) - h['end_at'] - 2} bytes after the end command")
    x0, y0, x1, y1 = dec.extents()
    ext = h["extents"]                      # left, top, right, bottom from the hoop centre
    want = (round(-x0), round(y1), round(x1), round(-y0))
    if max(abs(a - b) for a, b in zip(ext, want)) > 1:
        probs.append(f"JEF extents {ext}, stitches give {want}")
    hoop = h["hoop"]
    if hoop not in JEF_HOOPS:
        probs.append(f"JEF hoop code {hoop} unknown")
    else:
        W, H = JEF_HOOPS[hoop]
        w, ht = (x1 - x0) / 10, (y1 - y0) / 10
        if w > W or ht > H:
            probs.append(f"JEF hoop code {hoop} ({W}x{H}) is smaller than the design "
                         f"{w:.1f}x{ht:.1f} mm (the machine refuses or clips it)")
        # per-hoop edge distances: hoop half size minus extent, -1 when it does not fit
        for code, ed in zip((0, 1, 2), h["hoop_edges"][:3]):
            hw, hh = JEF_HOOPS[code][0] * 5, JEF_HOOPS[code][1] * 5
            exp = (hw - ext[0], hh - ext[1], hw - ext[2], hh - ext[3])
            if min(exp) < 0:
                exp = (-1, -1, -1, -1)
            if max(abs(a - b) for a, b in zip(ed, exp)) > 1:
                probs.append(f"JEF edge distances for the {JEF_HOOPS[code]} hoop {ed}, "
                             f"expected {exp}")
    # design centred: Janome places a JEF on the hoop centre by these extents
    if abs(ext[0] - ext[2]) > 2 * CENTRE_TOL or abs(ext[1] - ext[3]) > 2 * CENTRE_TOL:
        probs.append(f"JEF extents {ext} are not centred on the hoop")
    return probs


def _v_vp3(dec):
    h, probs = dec.header, []
    if not h["eof_ok"]:
        probs.append("VP3 'bytes to EOF' field does not match the file length")
    if not h["design_end_ok"]:
        probs.append("VP3 design block length does not reach the end of the file")
    if h["colors"] != dec.color_changes() + 1:
        probs.append(f"VP3 lists {h['colors']} colour blocks, decoded {dec.color_changes() + 1}")
    if h["count_threads"] != h["colors"]:
        probs.append(f"VP3 file-info thread count {h['count_threads']}, design has {h['colors']}")
    x0, y0, x1, y1 = dec.extents()
    e = [v / 100 for v in h["extents"]]        # maxX, maxY, minX, minY in 0.1 mm
    if max(abs(a - b) for a, b in zip(e, (x1, y1, x0, y0))) > 1.5:
        probs.append(f"VP3 extents {tuple(round(v) for v in e)}, stitches give "
                     f"{(round(x1), round(y1), round(x0), round(y0))}")
    return probs


def _v_xxx(dec):
    h, probs = dec.header, []
    if h["colors"] != dec.color_changes() + 1:
        probs.append(f"XXX header lists {h['colors']} colours, body has {dec.color_changes()} changes")
    x0, y0, x1, y1 = dec.extents()
    if abs(h["width"] - (x1 - x0)) > 1 or abs(h["height"] - (y1 - y0)) > 1:
        probs.append(f"XXX size {h['width']}x{h['height']}, stitches span {x1 - x0:.0f}x{y1 - y0:.0f}")
    if h["body_end"] > h["palette_offset"]:
        probs.append("XXX stitches run into the palette")
    # stitch count field: records - 1 (edutechwiki XXX "stitch length minus one")
    if abs(h["count_minus_one"] - (h["records"] - 1)) > 1:
        probs.append(f"XXX stitch count field {h['count_minus_one'] + 1}, body has {h['records']}")
    return probs


def _v_u01(dec):
    h, probs = dec.header, []
    x0, y0, x1, y1 = dec.extents()
    l, b, r, t = h["extents"]
    if max(abs(l - x0), abs(r - x1), abs(b - y0), abs(t - y1)) > 1:
        probs.append(f"U01 extents {h['extents']}, stitches give "
                     f"{(round(x0), round(y0), round(x1), round(y1))}")
    if abs(h["count"] - h["records"]) > 1:
        probs.append(f"U01 command count {h['count']}, body has {h['records']} records")
    return probs


# ------------------------------------------------------------------- cross-check

def cross_check(path):
    """Differences between this decoder and pyembroidery's reading of the same file:
    penetrations (beyond 0.1 mm rounding), trims, colour blocks. [] when they agree."""
    import pyembroidery as pe
    from .pattern import plan_of, read

    path = Path(path)
    try:
        dec = decode(path)
    except (FormatError, struct.error, IndexError) as e:
        return [f"independent decoder failed: {e}"]
    try:
        pat = read(path)
    except Exception as e:                      # noqa: BLE001
        return [f"pyembroidery cannot read it: {e}"]
    theirs = np.array([(x, -y) for x, y, c in pat.stitches
                       if c & pe.COMMAND_MASK == pe.STITCH], float).reshape(-1, 2)
    ours = dec.penetrations
    probs = []
    if len(ours) != len(theirs):
        probs.append(f"penetrations: {len(ours)} decoded here, {len(theirs)} by pyembroidery")
    else:
        if len(ours):
            # both absolute, 0.1 mm Y up; only VP3 readers may put the origin elsewhere
            # (block starts are relative to a centre field), so align VP3 on its first
            if _fmt(path) == "vp3":
                ours, theirs = ours - ours[0], theirs - theirs[0]
            d = np.abs(ours - theirs).max()
            if d > 1.0 + 1e-6:
                probs.append(f"penetrations differ by up to {d / 10:.2f} mm")
    plan = plan_of(pat)
    if dec.trims() != plan.trims:
        probs.append(f"trims: {dec.trims()} decoded here, {plan.trims} by pyembroidery")
    blocks = dec.color_changes() + 1
    if blocks != len(plan.colors):
        probs.append(f"colour blocks: {blocks} decoded here, {len(plan.colors)} by pyembroidery")
    return probs


def check_files(written):
    """validate + cross_check per file: {fmt: [problem, ...]}; the build calls this."""
    out = {}
    for fmt, path in written.items():
        if _fmt(path) not in DECODERS:
            out[fmt] = []
            continue
        out[fmt] = validate(path) + [f"cross-check: {p}" for p in cross_check(path)]
    return out
