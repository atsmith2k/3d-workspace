"""The independent decoders and validators (cadkit/stitch/validate.py): clean files from
our writer pass in every format, and each known real-world defect, reproduced by
corrupting bytes of a clean file, is caught. No binary fixtures: every file is built
here."""
import struct

import numpy as np
import pyembroidery as pe
import pytest

from cadkit.stitch import Design, native, rect
from cadkit.stitch import pattern as P
from cadkit.stitch import validate as V

from conftest import ROOT


def centred_design(w=30, h=20):
    """A small two-colour design centred on the origin: a fill, then two runs that need
    a trim and a long travel between them."""
    d = Design()
    d.fill(rect(w, h), "#c8102e", angle=0)
    d.run(np.array([[-w / 2, -h / 2 - 3], [w / 2, -h / 2 - 3]]), "navy", bean=1)
    d.run(np.array([[-w / 2, h / 2 + 3], [w / 2, h / 2 + 3]]), "navy", bean=1)
    return d


def write(tmp_path, design=None, formats=V.FORMATS, name="x", shift=(0, 0)):
    pat = native.build_pattern(design or centred_design())
    if shift != (0, 0):
        pat.stitches = [(x + shift[0], y + shift[1], c) for x, y, c in pat.stitches]
    return P.write_all(pat, tmp_path / name, formats)


@pytest.fixture(scope="module")
def clean(tmp_path_factory):
    return write(tmp_path_factory.mktemp("clean"))


def corrupt(src, tmp_path, fn, name=None):
    data = bytearray(src.read_bytes())
    data = fn(data) or data
    out = tmp_path / (name or ("bad" + src.suffix))
    out.write_bytes(bytes(data))
    return out


def flagged(path, *words):
    probs = V.validate(path)
    text = " | ".join(probs).lower()
    assert probs, f"{path.name} validated clean"
    for w in words:
        assert w.lower() in text, f"expected '{w}' in: {probs}"
    return probs


# ------------------------------------------------------------------- clean files

@pytest.mark.parametrize("fmt", V.FORMATS)
def test_clean_files_validate_and_cross_check(clean, fmt):
    assert V.validate(clean[fmt]) == []
    assert V.cross_check(clean[fmt]) == []


def test_check_files_api(clean):
    out = V.check_files(clean)
    assert set(out) == set(V.FORMATS)
    assert all(v == [] for v in out.values()), out


def test_decoders_agree_with_each_other(clean):
    """Every format decodes to the same penetrations (VP3 has no jump: its long moves
    are sewn, so it carries one extra penetration per move)."""
    ref = V.decode(clean["pes"])
    for fmt in V.FORMATS:
        dec = V.decode(clean[fmt])
        assert dec.color_changes() == 1, fmt
        assert dec.cut_connectors() == ref.cut_connectors() == 1, fmt
        if fmt != "vp3":
            assert len(dec.penetrations) == len(ref.penetrations), fmt
        x0, y0, x1, y1 = dec.extents()
        assert abs((x1 - x0) - 300) <= 2 and abs((y1 - y0) - 260) <= 2, (fmt, dec.extents())


def test_decoded_orientation_is_y_up(clean):
    """The last run sewn is the top one (y = +13 mm) in every format."""
    for fmt in V.FORMATS:
        dec = V.decode(clean[fmt])
        assert dec.penetrations[-1][1] > 100, fmt


def test_validate_module_does_not_use_pyembroidery_to_decode():
    src = (ROOT / "cadkit" / "stitch" / "validate.py").read_text()
    import ast
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "cross_check":
            continue
        for sub in ast.iter_child_nodes(node):
            if isinstance(sub, ast.Import):
                assert all("pyembroidery" not in a.name for a in sub.names)
            if isinstance(sub, ast.ImportFrom) and not (isinstance(node, ast.FunctionDef)
                                                       and node.name == "cross_check"):
                assert "pyembroidery" not in (sub.module or "")
                assert sub.module not in ("pattern", "threads"), "decoders must not use pattern.py"


# ------------------------------------------------------- PES / PEC known defects

def _pec(data, fmt):
    return struct.unpack_from("<I", data, 8)[0] if fmt == "pes" else 8


@pytest.mark.parametrize("fmt", ["pes", "pec"])
def test_end_code_inside_first_stitch_extents(clean, tmp_path, fmt):
    """pyembroidery issue 132: the start move's bytes read FF FE, which the machine
    takes as END before the first stitch."""
    def f(d):
        p = _pec(d, fmt) + 0x210
        d[p:p + 2] = b"\xff\xfe"
    flagged(corrupt(clean[fmt], tmp_path, f), "graphic offset")


@pytest.mark.parametrize("fmt", ["pes", "pec"])
def test_wrong_pec_colour_count(clean, tmp_path, fmt):
    def f(d):
        d[_pec(d, fmt) + 0x30] = 2              # says 3 colours, body has 2
    flagged(corrupt(clean[fmt], tmp_path, f), "colour")


def test_pes_thread_list_disagrees_with_pec(clean, tmp_path):
    def f(d):
        p = _pec(d, "pes")
        d[p + 0x30] = 0                         # PEC: 1 colour; v6 list: 2 threads
    flagged(corrupt(clean["pes"], tmp_path, f), "v6 header lists 2 threads")


@pytest.mark.parametrize("index", [0, 62, 63, 64, 70])
def test_reserved_palette_index(clean, tmp_path, index):
    def f(d):
        d[_pec(d, "pes") + 0x31] = index
    flagged(corrupt(clean["pes"], tmp_path, f), "reserved")


def test_non_ascii_label(clean, tmp_path):
    def f(d):
        d[_pec(d, "pes") + 4] = 0xE9            # 'é' in latin-1
    flagged(corrupt(clean["pes"], tmp_path, f), "label")


def test_blank_label(clean, tmp_path):
    def f(d):
        p = _pec(d, "pec")
        d[p + 3:p + 19] = b" " * 16
    flagged(corrupt(clean["pec"], tmp_path, f), "blank")


def test_pec_graphic_offset_wrong(clean, tmp_path):
    def f(d):
        p = _pec(d, "pes") + 0x202
        d[p] = (d[p] + 7) & 0xFF
    flagged(corrupt(clean["pes"], tmp_path, f), "graphic offset")


def test_pec_thumbnails_truncated(clean, tmp_path):
    flagged(corrupt(clean["pec"], tmp_path, lambda d: d[:-100]), "thumbnails")


def test_pes_addendum_missing(clean, tmp_path):
    flagged(corrupt(clean["pes"], tmp_path, lambda d: d[:-130]), "addendum")


def test_pes_wrong_version(clean, tmp_path):
    def f(d):
        d[4:8] = b"0001"
    flagged(corrupt(clean["pes"], tmp_path, f), "version")


# -------------------------------------------------------------- DST known defects

def _dst_field(d, key, value):
    i = d.index(key.encode() + b":")
    j = d.index(b"\r", i)
    width = j - i - 3
    d[i + 3:j] = value.rjust(width).encode()


def test_dst_st_mismatch(clean, tmp_path):
    flagged(corrupt(clean["dst"], tmp_path, lambda d: _dst_field(d, "ST", "9999")), "ST")


def test_dst_co_mismatch(clean, tmp_path):
    flagged(corrupt(clean["dst"], tmp_path, lambda d: _dst_field(d, "CO", "3")), "CO")


@pytest.mark.parametrize("key", ["+X", "-X", "+Y", "-Y"])
def test_dst_extent_mismatch(clean, tmp_path, key):
    flagged(corrupt(clean["dst"], tmp_path, lambda d: _dst_field(d, key, "40")), "DST +")


def test_dst_missing_header_field(clean, tmp_path):
    def f(d):
        i = d.index(b"PD:")
        d[i:i + 3] = b"QQ:"
    flagged(corrupt(clean["dst"], tmp_path, f), "PD missing")


def test_dst_record_over_121(clean, tmp_path):
    """Every +bit set: a 121 x 121 move sewn as one 17 mm stitch."""
    def f(d):
        k = 512 + 3 * 40                        # a fill stitch
        d[k:k + 3] = bytes([0b10100101, 0b10100101, 0b00100111])
    flagged(corrupt(clean["dst"], tmp_path, f), "over 12.1 mm")


def test_dst_missing_end(clean, tmp_path):
    flagged(corrupt(clean["dst"], tmp_path, lambda d: d[:-3]), "end")


# -------------------------------------------------------------- JEF known defects

def test_jef_colour_count_mismatch(clean, tmp_path):
    def f(d):
        struct.pack_into("<i", d, 24, 3)
    flagged(corrupt(clean["jef"], tmp_path, f), "colours")


def test_jef_point_count_mismatch(clean, tmp_path):
    def f(d):
        n = struct.unpack_from("<i", d, 28)[0]
        struct.pack_into("<i", d, 28, n + 5)
    flagged(corrupt(clean["jef"], tmp_path, f), "point count")


def test_jef_unknown_hoop_code(clean, tmp_path):
    def f(d):
        struct.pack_into("<i", d, 32, 9)
    flagged(corrupt(clean["jef"], tmp_path, f), "hoop code 9")


def test_jef_hoop_too_small(tmp_path):
    big = write(tmp_path, centred_design(80, 60), formats=("jef",))["jef"]
    assert V.validate(big) == []

    def f(d):
        struct.pack_into("<i", d, 32, 1)        # 50 x 50 for an 80 x 66 design
    flagged(corrupt(big, tmp_path, f), "smaller than the design")


def test_jef_extents_wrong(clean, tmp_path):
    def f(d):
        struct.pack_into("<i", d, 36, 10)
    flagged(corrupt(clean["jef"], tmp_path, f), "extents")


def test_jef_untrimmed_jumps(clean, tmp_path):
    """A JEF whose trims (80 02 00 00) were left out: the thread is dragged across."""
    def f(d):
        off = struct.unpack_from("<I", d, 0)[0]
        body = bytes(d[off:]).replace(b"\x80\x02\x00\x00", b"")
        d[off:] = body
        struct.pack_into("<i", d, 28, len(body) // 2)
    flagged(corrupt(clean["jef"], tmp_path, f), "no trim")


# ---------------------------------------------------------- every-format defects

def test_zero_length_stitches_dst(clean, tmp_path):
    def f(d):
        k = 512 + 3 * 40
        d[k:k] = b"\x00\x00\x03" * 4            # four penetrations in one hole
    flagged(corrupt(clean["dst"], tmp_path, f), "zero-length")


def test_zero_length_stitches_jef(clean, tmp_path):
    def f(d):
        off = struct.unpack_from("<I", d, 0)[0]
        k = off + 60
        d[k:k] = b"\x00\x00" * 3
        n = struct.unpack_from("<i", d, 28)[0]
        struct.pack_into("<i", d, 28, n + 3)
    probs = flagged(corrupt(clean["jef"], tmp_path, f), "zero-length")
    assert not any("point count" in p for p in probs)


def test_zero_length_stitches_exp(clean, tmp_path):
    def f(d):
        d[80:80] = b"\x00\x00" * 2
    flagged(corrupt(clean["exp"], tmp_path, f), "zero-length")


@pytest.mark.parametrize("fmt", ["dst", "jef", "exp", "vp3", "xxx", "u01"])
def test_uncentred_design(tmp_path, fmt):
    """A design written 5 mm off the origin lands off-centre (JEF) or far from the
    origin (DST/EXP), which has reset machines."""
    # written raw: write_all (pattern.prepare) centres every design, which is the fix
    pat = native.build_pattern(centred_design())
    P.prepare(pat)
    pat.stitches = [(x + 50, y, c) for x, y, c in pat.stitches]
    path = tmp_path / f"off.{fmt}"
    pe.write(pat, str(path), P.WRITE_SETTINGS.get(fmt, {}))
    flagged(path, "centre")


def test_vp3_length_field_wrong(clean, tmp_path):
    def f(d):
        i = d.index(b"\x00\x02\x00", 6) + 3
        n = struct.unpack_from(">I", d, i)[0]
        struct.pack_into(">I", d, i, n + 9)
    flagged(corrupt(clean["vp3"], tmp_path, f), "EOF")


def test_xxx_colour_count_wrong(clean, tmp_path):
    def f(d):
        struct.pack_into("<H", d, 0x27, 5)
    flagged(corrupt(clean["xxx"], tmp_path, f), "colours")


def test_u01_extents_wrong(clean, tmp_path):
    def f(d):
        struct.pack_into("<h", d, 0x84, 999)
    flagged(corrupt(clean["u01"], tmp_path, f), "extents")


def test_cross_check_reports_disagreements(clean, monkeypatch):
    """cross_check compares penetrations, trims and colour blocks with pyembroidery's
    reading: make our decoder lose a stitch, gain a trim and move a point."""
    real = V.DECODERS["dst"]

    def off(data):
        dec = real(data)
        recs = list(dec.records)
        k = next(i for i, r in enumerate(recs) if r[2] == V.STITCH)
        del recs[k + 5]
        recs.insert(k + 10, (recs[k + 10][0], recs[k + 10][1], V.TRIM))
        dec.records = recs
        return dec
    monkeypatch.setitem(V.DECODERS, "dst", off)
    probs = " | ".join(V.cross_check(clean["dst"]))
    assert "penetrations" in probs and "trims" in probs

    def moved(data):
        dec = real(data)
        dec.records = [(x + 3, y, c) if i > 100 else (x, y, c)
                       for i, (x, y, c) in enumerate(dec.records)]
        return dec
    monkeypatch.setitem(V.DECODERS, "dst", moved)
    assert "differ by up to 0.30 mm" in " ".join(V.cross_check(clean["dst"]))


# --------------------------------------------------------- shipped design files

COLORADO = ROOT / "output" / "embroidery" / "gameday_banner_colorado_gold_black"


@pytest.mark.skipif(not COLORADO.exists(), reason="Colorado banner not built")
@pytest.mark.parametrize("label", ["4x4", "5x7"])
def test_colorado_size_builds_validate(label):
    d = COLORADO / "sizes" / f"{COLORADO.name}_{label}"
    files = {f.suffix[1:]: f for f in d.iterdir() if f.suffix[1:] in V.FORMATS}
    assert set(files) == set(V.FORMATS)
    out = V.check_files(files)
    assert all(v == [] for v in out.values()), out
