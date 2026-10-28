"""Bambu Studio preset resolution: the CLI only gets files, so every system preset has
to arrive with its inherits chain and include templates already merged in."""
import json

from cadkit import slicer


def _write(root, kind, name, data):
    d = root / kind
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(dict(name=name, **data)), encoding="utf-8")


def test_flatten_merges_inherits_and_includes(tmp_path):
    _write(tmp_path, "machine", "common", dict(machine_start_gcode="G28", printable_area=["0x0", "200x200"],
                                               retraction_length=["0.8"]))
    _write(tmp_path, "machine", "A1 template start", dict(instantiation="false", machine_start_gcode=";A1 start"))
    _write(tmp_path, "machine", "A1", dict(inherits="common", include=["A1 template start"],
                                           printable_area=["0x0", "256x256"]))
    flat = slicer._flatten_preset(tmp_path, "machine", "A1")
    assert flat["machine_start_gcode"] == ";A1 start"           # include beats the parent
    assert flat["printable_area"] == ["0x0", "256x256"]          # own keys beat both
    assert flat["retraction_length"] == ["0.8"]                  # parent keys kept
    assert flat["name"] == "A1" and "inherits" not in flat and "include" not in flat


def test_flatten_filament_keeps_parent_limits(tmp_path):
    _write(tmp_path, "filament", "fdm_filament_common", dict(filament_max_volumetric_speed=["0"], filament_density=["0"]))
    _write(tmp_path, "filament", "PLA @base", dict(inherits="fdm_filament_common", filament_max_volumetric_speed=["21"],
                                                   filament_density=["1.26"]))
    _write(tmp_path, "filament", "PLA @A1", dict(inherits="PLA @base"))
    flat = slicer._flatten_preset(tmp_path, "filament", "PLA @A1")
    assert flat["filament_max_volumetric_speed"] == ["21"] and flat["filament_density"] == ["1.26"]
