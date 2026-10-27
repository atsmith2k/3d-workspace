"""Unit tests for the publish pipeline: manifest composition and validation, the
sellable gate, Spec parsing of the real mold models, print notes, and report.txt
composition across rebuilds. No CAD kernels or slicers are needed: the build and
slice data are synthetic JSON in tmp_path."""
import hashlib
import json
import re
from pathlib import Path

import pytest

from cadkit import outputs, publish

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
GIT = dict(commit="a" * 40, dirty=False)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _write(path, data):
    path.write_bytes(data)
    return _sha(data)


def make_folder(tmp_path, name="d20_paver_mold", printers=("a1", "a1mini"), parts=None,
                warnings=(), check_fail=False, notes=True, product_png=True, stale=()):
    """A synthetic output folder: STL/3MF/PNG/TXT files with real bytes, a build dict
    and a slice dict shaped like build.json / slice.json. Returns (out, build, slices)."""
    out = tmp_path / name
    out.mkdir(parents=True)
    parts = parts or [name]
    build_parts = {}
    for part in parts:
        fname = name if part == name else f"{name}-{part}"
        stl_sha = _write(out / f"{fname}.stl", f"solid {fname}\nendsolid\n".encode())
        checks = [dict(name="dims", ok=True, detail="x=136.3 z=24.0"),
                  dict(name="no_overhang", ok=not check_fail, detail="0 mm2 overhang")]
        build_parts[fname] = dict(
            part=part, size_mm=[136.3, 136.3, 24.0], size_in=[5.366, 5.366, 0.945],
            volume_cm3=124.3, est_grams_pla=154.1, triangles=19562, watertight=True, bodies=1, voids=0,
            flat_base_mm2=18533.0, overhang_mm2=0.0, overhang_minor_mm2=0.0, thinnest_wall_mm=1.6,
            wall_median_mm=4.6, thin_fraction=0.001, thin_points=[], stl_bytes=1000,
            warnings=list(warnings), checks=checks, checks_ok=not check_fail,
            lines=["size     136.3 x 136.3 x 24.0 mm", "check    PASS dims: x=136.3 z=24.0"],
            stl=f"{fname}.stl", stl_sha256=stl_sha, step=None)
    build = dict(name=name, model=f"models/{name}.py", model_sha256="b" * 64,
                 description="5 in square cement paver mold with a raised D20 dice relief",
                 params=dict(size=127.0, thickness=19.0), printer="a1", printer_name="Bambu Lab A1",
                 bed=[256.0, 256.0, 256.0], fast=False, ok=not check_fail,
                 header_lines=[f"# {name}", "desc", "", "params: size=127.0", "printer: Bambu Lab A1", ""],
                 parts=build_parts, fit=None, generated_at="2026-10-27T00:00:00Z", cadkit_version="0.2.0")
    slices = {}
    for fname, data in build_parts.items():
        for key in printers:
            stem = f"{fname}_{key}"
            _write(out / f"{stem}.3mf", b"PK3mf " + stem.encode())
            _write(out / f"{stem}_plate.png", b"\x89PNG plate")
            slices[stem] = dict(
                printer=key, printer_name="Bambu Lab A1" if key == "a1" else "Bambu Lab A1 mini",
                slicer="Bambu Studio", filament_preset="Bambu PLA Basic", material="PLA",
                layer_height_mm=0.2, infill_pct=15.0, process="0.2 mm Standard",
                supports=dict(enabled=False, generated=False), print_time_s=32571,
                print_time_text="9h 2m 51s", layers=120, filament_g=80.9, filament_m=26.68, cost=0.0,
                file=f"{stem}.3mf", gcode=None, lines=[f"print    9h 2m 51s on {key}"],
                stl=data["stl"], stl_sha256=("0" * 64) if stem in stale else data["stl_sha256"],
                sliced_at="2026-10-27T00:00:00Z")
    if product_png:
        _write(out / f"{name}_product.png", b"\x89PNG product")
        _write(out / f"{name}_hero.png", b"\x89PNG hero")
    _write(out / f"{name}_preview.png", b"\x89PNG sheet")
    _write(out / "report.txt", b"not a deliverable")
    _write(out / f"{name}.gcode", b"; not a deliverable")
    _write(out / "zoom.png", b"\x89PNG ad hoc")
    if notes:
        _write(out / f"{name}_print_notes.txt", b"notes placeholder")
    return out, build, slices


INFO = dict(name="d20_paver_mold", model="d20_paver_mold.py", model_sha256="b" * 64,
            summary="5 in square cement paver mold with a raised D20 dice relief",
            description="A mold.", spec=dict(orientation="flat base on the bed"),
            product=dict(title="D20 Paver Mold", category="molds", tags=["mold", "dice"],
                         printers=["a1", "a1mini"], cast_material="cement"),
            license_notes=None)


def compose(tmp_path, **kw):
    out, build, slices = make_folder(tmp_path, **kw)
    return publish.compose_manifest(out, build, slices, INFO, git=GIT, generated_at="2026-10-27T00:00:00Z")


# ---------------------------------------------------------------- manifest

def test_manifest_is_valid_and_sellable(tmp_path):
    m = compose(tmp_path)
    assert publish.validate_manifest(m) == []
    assert m["schema"] == "cadkit-product/1"
    assert m["slug"] == "d20-paver-mold"
    assert m["title"] == "D20 Paver Mold"
    assert m["category"] == "molds"
    assert m["printers_supported"] == ["a1", "a1mini"]
    assert m["sellable"] is True and m["reasons"] == []
    assert m["git_commit"] == "a" * 40 and m["git_dirty"] is False
    assert m["model_sha256"] == "b" * 64
    assert m["spec"]["orientation"] == "flat base on the bed"
    assert m["params"] == dict(size=127.0, thickness=19.0)
    part = m["parts"][0]
    assert part["size_mm"] == [136.3, 136.3, 24.0] and part["est_grams_pla"] == 154.1
    assert [c["name"] for c in part["checks"]] == ["dims", "no_overhang"]


def test_files_whitelist_roles_and_hashes(tmp_path):
    m = compose(tmp_path)
    paths = {f["path"]: f for f in m["files"]}
    assert set(paths) == {"d20_paver_mold.stl", "d20_paver_mold_a1.3mf", "d20_paver_mold_a1mini.3mf",
                          "d20_paver_mold_product.png", "d20_paver_mold_hero.png", "d20_paver_mold_preview.png",
                          "d20_paver_mold_a1_plate.png", "d20_paver_mold_a1mini_plate.png",
                          "d20_paver_mold_print_notes.txt"}
    assert "zoom.png" not in paths and "report.txt" not in paths and "d20_paver_mold.gcode" not in paths
    assert paths["d20_paver_mold.stl"]["role"] == "stl" and paths["d20_paver_mold.stl"]["part"] == "d20_paver_mold"
    assert paths["d20_paver_mold_a1mini.3mf"]["role"] == "3mf" and paths["d20_paver_mold_a1mini.3mf"]["printer"] == "a1mini"
    assert paths["d20_paver_mold_print_notes.txt"]["role"] == "txt"
    f = paths["d20_paver_mold.stl"]
    assert f["bytes"] == len(b"solid d20_paver_mold\nendsolid\n")
    assert f["sha256"] == _sha(b"solid d20_paver_mold\nendsolid\n")
    assert m["images"] == dict(product="d20_paver_mold_product.png", hero="d20_paver_mold_hero.png",
                               check_sheet="d20_paver_mold_preview.png",
                               thumbnails=["d20_paver_mold_a1_plate.png", "d20_paver_mold_a1mini_plate.png"])


def test_slices_per_printer(tmp_path):
    m = compose(tmp_path)
    assert [s["printer"] for s in m["slices"]] == ["a1", "a1mini"]
    s = m["slices"][0]
    assert s["file"] == "d20_paver_mold_a1.3mf" and s["print_time_s"] == 32571
    assert s["material"] == "PLA" and s["filament_g"] == 80.9 and s["layers"] == 120


def test_stale_slice_is_excluded_and_blocks(tmp_path):
    m = compose(tmp_path, stale=("d20_paver_mold_a1mini",))
    assert [s["printer"] for s in m["slices"]] == ["a1"]
    assert m["sellable"] is False
    assert any("no fresh slice for a1mini" in r for r in m["reasons"])


def test_manifest_round_trips_through_json(tmp_path):
    m = compose(tmp_path)
    outputs.save_json(tmp_path / "manifest.json", m)
    again = outputs.load_json(tmp_path / "manifest.json")
    assert again == m
    assert publish.validate_manifest(again) == []


def test_validate_catches_broken_manifests(tmp_path):
    m = compose(tmp_path)
    bad = json.loads(json.dumps(m))
    bad["schema"] = "cadkit-product/0"
    bad["slug"] = "D20_paver"
    bad["files"][0]["sha256"] = "nope"
    bad["slices"][0]["file"] = "missing.3mf"
    del bad["parts"][0]["checks_ok"]
    problems = publish.validate_manifest(bad)
    assert any("schema" in p for p in problems)
    assert any("slug" in p for p in problems)
    assert any("sha256" in p for p in problems)
    assert any("missing.3mf" in p for p in problems)
    assert any("checks_ok" in p for p in problems)


# ---------------------------------------------------------------- gate

def test_gate_blocks_on_warning_and_failed_check(tmp_path):
    m = compose(tmp_path, warnings=["walls under 1.2 mm (yellow in preview) near (0, 0, 1) 0.5 mm"])
    assert m["sellable"] is False and any("walls under" in r for r in m["reasons"])
    m = compose(tmp_path / "b", check_fail=True)
    assert m["sellable"] is False and any("checks failed (no_overhang)" in r for r in m["reasons"])


def test_gate_needs_render_notes_and_every_printer(tmp_path):
    m = compose(tmp_path, notes=False, product_png=False)
    assert m["sellable"] is False
    assert "no product render" in m["reasons"] and "no print notes" in m["reasons"]
    m = compose(tmp_path / "b", printers=("a1",))
    assert m["sellable"] is False
    assert any("no fresh slice for a1mini" in r for r in m["reasons"])
    assert any("no a1mini 3MF" in r for r in m["reasons"])


def test_gate_dirty_tree_is_a_reason_not_a_block(tmp_path):
    out, build, slices = make_folder(tmp_path)
    m = publish.compose_manifest(out, build, slices, INFO, git=dict(commit="c" * 40, dirty=True))
    assert m["sellable"] is True
    assert m["reasons"] == ["built from an uncommitted working tree"]


def test_gate_override_true_sells_with_caveats_and_false_blocks(tmp_path):
    out, build, slices = make_folder(tmp_path, warnings=["overhangs present; needs supports"])
    info = dict(INFO, product=dict(INFO["product"], sellable=True))
    m = publish.compose_manifest(out, build, slices, info, git=GIT)
    assert m["sellable"] is True and m["sellable_override"] is True
    assert any("overhangs" in r for r in m["reasons"])
    info = dict(INFO, product=dict(INFO["product"], sellable=False))
    m = publish.compose_manifest(out, build, slices, info, git=GIT)
    assert m["sellable"] is False and m["sellable_override"] is False
    assert m["reasons"][0] == "PRODUCT sellable=False"
    assert publish.validate_manifest(m) == []


def test_gate_skips_printers_the_part_does_not_fit(tmp_path):
    out, build, slices = make_folder(tmp_path, printers=("a1",))
    for part in build["parts"].values():
        part["size_mm"] = [200.0, 150.0, 24.0]
    m = publish.compose_manifest(out, build, slices, INFO, git=GIT)
    assert m["printers_supported"] == ["a1"] and m["printers_requested"] == ["a1", "a1mini"]
    assert m["sellable"] is True


def test_multi_part_fit_interference_blocks(tmp_path):
    out, build, slices = make_folder(tmp_path, name="box", parts=["lid", "base"])
    build["fit"] = dict(ok=False, lines=["fit      lid vs base: INTERFERE by 12.0 mm3"],
                        pairs=[dict(a="box-lid", b="box-base", interference_mm3=12.0, clearance_mm=0.0, ok=False)])
    info = dict(INFO, name="box", product=dict(title="Box", category="parts"))
    m = publish.compose_manifest(out, build, slices, info, git=GIT)
    assert publish.validate_manifest(m) == []
    assert [p["part"] for p in m["parts"]] == ["lid", "base"]
    assert {(s["part"], s["printer"]) for s in m["slices"]} == {("box-lid", "a1"), ("box-lid", "a1mini"),
                                                               ("box-base", "a1"), ("box-base", "a1mini")}
    assert m["sellable"] is False and any("fit: box-lid vs box-base" in r for r in m["reasons"])


# ---------------------------------------------------------------- spec parsing

def _doc(model):
    import ast
    return ast.get_docstring(ast.parse((MODELS / model).read_text(encoding="utf-8")))


def test_parse_spec_d20():
    description, spec = publish.parse_spec(_doc("d20_paver_mold.py"))
    assert description.startswith("5 in square cement paver mold")
    assert "Spec" not in description
    assert set(spec) >= {"object", "overall", "casting", "orientation", "must_have", "tolerances"}
    assert spec["orientation"].startswith("flat base on the bed")
    assert "icosahedron" in spec["must_have"]            # continuation lines joined
    assert spec["tolerances"] == "none (no mating parts)"


def test_parse_spec_oak_leaf():
    description, spec = publish.parse_spec(_doc("oak_leaf_coaster_mold.py"))
    assert "cast face-down" in description
    assert spec["object"].startswith("mold for a 4 in")
    assert spec["orientation"] == "opening up, flat floor on the bed, no overhangs"
    assert "2 deg draft" in spec["must_have"]


def test_parse_spec_butterfly():
    description, spec = publish.parse_spec(_doc("butterfly_paver_mold.py"))
    assert "style=shaped" in description
    assert spec["orientation"].startswith("flat base on the bed")
    assert "webbed over" in spec["must_have"]
    assert "127 mm wide" in spec["casting"]


def test_parse_spec_without_block():
    description, spec = publish.parse_spec("Just a cube.\n\nNothing else.")
    assert description == "Just a cube.\n\nNothing else." and spec == {}


def test_template_spec_header_variant():
    description, spec = publish.parse_spec(_doc("_template.py"))
    assert "object" in spec and "mates_with" in spec and "tolerances" in spec


def test_model_info_reads_product_and_license():
    import importlib.util
    import sys
    path = MODELS / "sequoia_ashtray_bin.py"
    sys.path[:0] = [str(MODELS), str(ROOT)]
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    info = publish.model_info(mod, path)
    assert info["product"]["sellable"] is False
    assert "1163944" in info["license_notes"]
    assert info["model_sha256"] == outputs.sha256(path)


# ---------------------------------------------------------------- print notes

def test_print_notes_sections_and_determinism(tmp_path):
    m = compose(tmp_path)
    text = publish.print_notes_text(m)
    for section in ("PRINTING", "USING THE MOLD", "NOTES", "LICENSE"):
        assert f"\n{section}\n" in text
    assert text.startswith("D20 Paver Mold\n")
    assert "Bambu Lab A1 mini: 9h 2m, 81 g / 26.7 m PLA, 120 layers" in text
    assert "136.3 x 136.3 x 24.0 mm (5.37 x 5.37 x 0.94 in)" in text
    assert "cast material: cement" in text
    assert "release agent" in text
    assert publish.DEFAULT_LICENSE.split(".")[0] in text.replace("\n  ", " ")
    assert "no print notes" not in text and "uncommitted" not in text
    assert not re.search(r"\d{4}-\d{2}-\d{2}T", text), "no timestamps in the notes"
    later = dict(m, generated_at="2030-01-01T00:00:00Z")
    assert publish.print_notes_text(later) == text


def test_print_notes_custom_license_and_warnings(tmp_path):
    out, build, slices = make_folder(tmp_path, warnings=["overhangs present; needs supports"])
    info = dict(INFO, license_notes="Dimensions from MakerWorld 1163944; not for resale.",
                product=dict(INFO["product"], post_processing="Sand the rim."))
    m = publish.compose_manifest(out, build, slices, info, git=GIT)
    text = publish.print_notes_text(m)
    assert "MakerWorld 1163944" in text and publish.DEFAULT_LICENSE[:30] not in text
    assert "Sand the rim." in text and "release agent" not in text
    assert "- overhangs present; needs supports" in text
    assert m["license_custom"] is True


# ---------------------------------------------------------------- report composition

def test_write_report_keeps_slices_across_rebuild_and_flags_stale(tmp_path):
    out, build, slices = make_folder(tmp_path)
    outputs.save_json(out / "build.json", build)
    outputs.save_json(out / "slice.json", slices)
    text = outputs.write_report(out)
    assert text.startswith("# d20_paver_mold\n")
    assert "## d20_paver_mold\nsize     136.3" in text
    assert "## slice d20_paver_mold_a1 (Bambu Studio)\n" in text
    assert "## slice d20_paver_mold_a1mini (Bambu Studio)\n" in text
    assert "STALE" not in text
    # a rebuild: build.json rewritten with a changed STL, slice.json untouched
    new_sha = _write(out / "d20_paver_mold.stl", b"solid rebuilt\nendsolid\n")
    build["parts"]["d20_paver_mold"]["stl_sha256"] = new_sha
    build["parts"]["d20_paver_mold"]["lines"][0] = "size     140.0 x 140.0 x 24.0 mm"
    outputs.save_json(out / "build.json", build)
    text = outputs.write_report(out)
    assert "size     140.0" in text
    assert text.count("## slice") == 2, "slice sections survive the rebuild"
    assert "## slice d20_paver_mold_a1 (Bambu Studio)  STALE" in text
    assert (out / "report.txt").read_text(encoding="utf-8") == text
    # and the manifest leaves the stale slices out
    m = publish.compose_manifest(out, build, outputs.load_json(out / "slice.json"), INFO, git=GIT)
    assert m["slices"] == [] and m["sellable"] is False


def test_write_report_without_slices_matches_lines_exactly(tmp_path):
    out, build, _ = make_folder(tmp_path)
    outputs.save_json(out / "build.json", build)
    text = outputs.write_report(out)
    expected = "\n".join(build["header_lines"] + ["## d20_paver_mold", *build["parts"]["d20_paver_mold"]["lines"], ""])
    assert text == expected


def test_material_of_prefers_preset_when_slicer_mislabels():
    from cadkit import slicer
    info = '<filament id="1" type="PLA" color="#00AE42" used_m="29.23"/>'
    assert slicer.material_of(info, "Bambu PLA Basic") == "PLA"
    assert slicer.material_of(info, "Bambu PETG Basic") == "PETG"
    assert slicer.material_of("", "Bambu TPU 95A") == "TPU"
    assert slicer.material_of(info, "Generic") == "PLA"
    assert slicer.material_of("", "") == ""
