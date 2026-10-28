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
