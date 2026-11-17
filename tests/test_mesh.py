import trimesh

from cadkit import mesh


def _thin_plate():
    # 40 x 40 mm, 0.6 mm thick: every wall sample is under the default 1.2 mm
    return trimesh.creation.box((40, 40, 0.6))


def test_thin_wall_warns_by_default():
    rep = mesh.check(_thin_plate(), thickness_samples=500)
    assert any("walls under 1.2 mm" in w for w in rep.warnings)


def test_model_min_wall_lowers_the_warning_threshold():
    rep = mesh.check(_thin_plate(), thickness_samples=500, min_wall=0.4)
    assert not any("walls under" in w for w in rep.warnings)
    assert rep.thin_fraction > 0.5          # still reported against 1.2 mm
    assert rep.to_dict()["min_wall_mm"] == 0.4
    rep = mesh.check(_thin_plate(), thickness_samples=500, min_wall=0.8)
    assert any("walls under 0.8 mm" in w for w in rep.warnings)


def test_build_sdf_snap_puts_vertices_on_the_surface():
    import numpy as np
    from cadkit.mesh import to_trimesh
    from cadkit.sdf import build_sdf

    def ball(x, y, z):
        return 10.0 - np.sqrt(x * x + y * y + (z - 12.0) ** 2)

    bounds = (-12, -12, 0, 12, 12, 24)
    for snap, limit in ((False, None), (True, 1e-3)):
        tm = to_trimesh(build_sdf(ball, bounds, edge=1.0, flat_bottom=False, snap=snap))
        err = np.abs(np.linalg.norm(tm.vertices - [0, 0, 12], axis=1) - 10.0)
        if snap:
            assert err.max() < limit and tm.is_watertight
        else:
            loose = err.max()
    assert loose > 10 * err.max()          # snapping is what made it exact


def test_slice_settings_merge_model_and_command_line(tmp_path):
    import argparse
    from cadkit.__main__ import slice_settings
    m = tmp_path / "m.py"
    m.write_text("SLICE = dict(supports=True, rotate=-90, process=dict(seam_position='back'))\n")
    cfg = slice_settings(argparse.Namespace(model=str(m), supports=False, process=["wall_loops=3"]))
    assert cfg == dict(supports=True, rotate=-90.0,
                       process=dict(seam_position="back", wall_loops="3"),
                       layer_height=0.2, infill=15, filament=None)
    none = slice_settings(argparse.Namespace(model=None, supports=False, process=[]))
    assert none == dict(supports=False, rotate=0.0, process={}, layer_height=0.2, infill=15,
                    filament=None)
    # SLICE may carry layer_height / infill (lithophanes); explicit CLI flags still win
    m.write_text("SLICE = dict(layer_height=0.12, infill=100, filament='Generic PETG')\n")
    lit = slice_settings(argparse.Namespace(model=str(m), supports=False, process=[],
                                            layer_height=None, infill=None))
    assert (lit["layer_height"], lit["infill"], lit["filament"]) == (0.12, 100, "Generic PETG")
    cli = slice_settings(argparse.Namespace(model=str(m), supports=False, process=[],
                                            layer_height=0.2, infill=20, filament="Bambu PLA Basic"))
    assert (cli["layer_height"], cli["infill"], cli["filament"]) == (0.2, 20, "Bambu PLA Basic")
