"""Sounds in the game-asset silo: synthesis helpers, the WAV writer against an independent
reader, the checks that stand in for ears, loops, and (with a Cinder package) the engine's
audio layer opening the file."""
import textwrap
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.io import wavfile

from cadkit.game import audio as A
from cadkit.game import build as B
from cadkit.game import engine as E
from cadkit.game import sound as S

ENGINE = E.find()
needs_engine = pytest.mark.skipif(ENGINE is None, reason="no Cinder package (set CAD_CINDER)")


def test_sources_and_envelopes():
    assert len(A.t(0.5)) == 24000 and A.n(0.001) == 48
    tone = A.osc(440, 1.0)
    assert A.centroid(tone) == pytest.approx(440, abs=2)
    assert A.band_share(tone, 400, 480) > 0.99
    up = A.osc(A.glide(200, 800, 0.5), 0)
    assert 200 < A.centroid(up) < 800
    for color, lo in (("white", 0.004), ("pink", 0.2), ("brown", 0.9)):
        x = A.noise(1.0, 3, color)
        assert abs(np.abs(x).max() - 1) < 1e-9 and A.band_share(x, 20, 200) > lo * 0.5
    assert np.array_equal(A.noise(0.1, 7), A.noise(0.1, 7)) and not np.array_equal(A.noise(0.1, 7), A.noise(0.1, 8))
    env = A.adsr(1.0, 0.01, 0.1, 0.5, 0.2)
    assert env[0] == 0 and env.max() == pytest.approx(1, abs=0.01) and env[-1] == 0 and len(env) == 48000
    assert A.decay(1.0, 0.5)[24000] == pytest.approx(1e-3, rel=0.01)       # 60 dB down after t60
    struck = A.modes([500, 1500], [0.3, 0.1], [1, 0.5], 0.4)
    assert np.abs(struck[:2400]).max() > 10 * np.abs(struck[-2400:]).max()


def test_filters_fades_and_levels():
    x = A.noise(1.0, 1)
    assert A.band_share(A.lowpass(x, 500, 4), 0, 600) > 0.9
    assert A.band_share(A.highpass(x, 4000, 4), 3500, 24000) > 0.9
    assert A.band_share(A.bandpass(x, 800, 1600, 4), 600, 2000) > 0.85
    swept = A.swept_bandpass(x[:9600], A.glide(500, 500, 0.2), 4)
    assert A.band_share(swept, 250, 1000) > 0.6
    f = A.fade(np.ones(4800), 2, 5)
    assert f[0] == 0 and f[-1] == 0 and f[2400] == 1
    y = A.normalize(np.sin(np.linspace(0, 60, 4800)) * 0.2 + 0.3, -6)
    assert A.db(np.abs(y).max()) == pytest.approx(-6, abs=0.01) and abs(y.mean()) < 1e-9
    st = A.stereo(np.ones(10), 0.0)
    assert st.shape == (10, 2) and np.allclose((st ** 2).sum(1), 1)       # equal power
    assert A.stereo(np.ones(4), -1.0)[0, 1] == pytest.approx(0, abs=1e-9)


def test_loop_tools_wrap():
    d = 1.0
    assert A.fit(73.42, 32.0) * 32.0 == round(73.42 * 32.0)
    tone = A.osc(A.fit(110.3, d), d)
    assert abs(tone[0] - (2 * tone[-1] - tone[-2])) < 1e-3              # continues into its own start
    buf = np.zeros(A.n(d))
    A.place(buf, np.ones(4800), 0.95, wrap=True)                          # runs past the end, back to the start
    assert buf[-2400:].sum() == 2400 and buf[:2400].sum() == 2400
    A.place(buf, np.ones(4800), 0.95)                                     # no wrap: clipped at the end
    assert buf[-1] == 2 and buf[2399] == 1
    click = np.zeros(A.n(d))
    click[100] = 1.0
    wet = A.reverb(click, 0.5, 1.0, seed=2, wrap=True)
    assert len(wet) == len(click)                                         # the tail folded round, not appended
    assert len(A.reverb(click, 0.5, 0.3, seed=2)) > len(click)
    blended = A.loop_blend(A.noise(1.0, 5), 80)
    assert len(blended) == A.n(1.0) - A.n(0.08)


def test_wav_reads_back_through_scipy(tmp_path):
    x = A.normalize(A.osc(440, 0.25), -3)
    pcm = S.write_wav(tmp_path / "a.wav", x)
    sr, data = wavfile.read(tmp_path / "a.wav")
    assert sr == 48000 and data.dtype == np.int16 and np.array_equal(data, pcm)
    S.write_wav(tmp_path / "st.wav", A.stereo(x, 0.3))
    assert wavfile.read(tmp_path / "st.wav")[1].shape == (12000, 2)


def _ctx(sound, tmp, name="thing", budget=None):
    wav = tmp / f"{name}.wav"
    S.write_wav(wav, sound.samples)
    return SimpleNamespace(sound=sound, read=wavfile.read(wav), params={}, name=name, budget=budget,
                           bytes=wav.stat().st_size)


def _failing(sound, tmp, **kw):
    ctx = _ctx(sound, tmp, **kw)
    return {r["name"] for r in (c.run(ctx) for c in S.static_checks()) if not r["ok"]}


def test_static_checks_catch_real_faults(tmp_path):
    good = A.Sound(A.normalize(A.fade(A.osc(440, 0.3) * A.decay(0.3, 0.2), 1, 20), -3))
    assert _failing(good, tmp_path) == set()
    assert _failing(A.Sound(A.osc(440, 0.3, phase=0.25) * 0.7), tmp_path) == {"edges"}            # starts at full level
    assert _failing(A.Sound(good.samples * 0.05), tmp_path) == {"level"}                         # too quiet
    assert _failing(A.Sound(np.clip(good.samples * 3, -1, 1)), tmp_path) == {"level"}            # clipped
    assert _failing(A.Sound(A.fade(good.samples * 0.5 + 0.1, 1, 20)), tmp_path) == {"level"}     # DC offset
    tail = np.concatenate([good.samples, np.zeros(A.n(0.4))])
    assert _failing(A.Sound(tail), tmp_path) == {"edges"}                                        # trailing silence
    assert _failing(A.Sound(A.stereo(good.samples), spatial=True), tmp_path) == {"channels"}     # spatial must be mono
    assert _failing(A.Sound(A.stereo(good.samples), spatial=False), tmp_path) == set()
    assert _failing(good, tmp_path, budget=dict(seconds=0.1)) == {"budget"}
    assert _failing(good, tmp_path, name="Bad Name") == {"name"}


def test_loop_seam_check(tmp_path):
    d = 1.0
    seamless = A.Sound(A.normalize(A.osc(A.fit(220.4, d), d), -6), loop=True)
    assert _failing(seamless, tmp_path) == set()
    popping = A.Sound(A.normalize(A.osc(220.4, d), -6), loop=True)       # 0.4 of a cycle left over
    assert _failing(popping, tmp_path) == {"edges"}


def test_spec_checks_describe_the_sound(tmp_path):
    thud = A.Sound(A.normalize(A.fade(A.modes([80, 130], [0.2, 0.1], [1, 0.5], 0.3), 1, 20), -3))
    ctx = _ctx(thud, tmp_path)
    assert S.band(40, 300, at_least=0.9).run(ctx)["ok"] and not S.band(1000, 8000, at_least=0.5).run(ctx)["ok"]
    assert S.band(1000, 8000, at_most=0.05).run(ctx)["ok"]
    assert S.duration(0.25, 0.35).run(ctx)["ok"] and S.duration(0.3).run(ctx)["ok"] and not S.duration(1.0).run(ctx)["ok"]
    assert S.peak(-4, -2).run(ctx)["ok"] and not S.peak(-12, -6).run(ctx)["ok"]


def test_use_snippet_matches_cinders_sounddesc_order():
    """cinder.audio SoundDesc(path, bus, streamed, looping, spatial): streamed comes before looping."""
    music = A.Sound(np.zeros((10, 2)), loop=True, bus="music", spatial=False, streamed=True)
    assert 'SoundDesc(String("audio/m.wav"), music_bus, True, True, False)' in S.use_snippet("m", music)
    loop = A.Sound(np.zeros(10), loop=True)
    assert "sfx_bus, False, True, True)" in S.use_snippet("l", loop)     # not streamed, looping, spatial
    assert "streamed, looping, spatial" in S.use_snippet("l", loop)


SOUND = '''
from cadkit.game.audio import *
from cadkit.game.sound import band, duration
KIND = "sound"
DESCRIPTION = "test beep"
PARAMS = dict(freq=660.0)
BUDGET = dict(seconds=0.5)
PRODUCT = dict(collection="sound_test", licence="CC0-1.0")
def checks(p):
    return [duration(0.2, 0.3), band(500, 900, at_least=0.9)]
def build(p):
    return Sound(normalize(fade(osc(p.freq, 0.25) * decay(0.25, 0.2), 1, 20), -3))
'''


def test_sound_build_without_an_engine_is_never_ready(tmp_path):
    src = tmp_path / "test_beep.py"
    src.write_text(textwrap.dedent(SOUND), encoding="utf-8")
    b = B.build_asset(src, out_root=tmp_path / "out", use_engine=False, quiet=True)
    assert b["kind"] == "sound" and not b["ready"] and "not verified in Cinder" in b["blockers"][0]
    assert all(r["ok"] for r in b["steps"]["static"]["checks"])
    out = tmp_path / "out" / "test_beep"
    assert (out / "test_beep.wav").exists() and (out / "test_beep_preview.png").stat().st_size > 10000
    assert b["stats"]["seconds"] == 0.25 and b["stats"]["channels"] == 1 and 600 < b["stats"]["centroid_hz"] < 720
    bad = B.build_asset(src, ["freq=3000"], out_root=tmp_path / "out", use_engine=False, quiet=True)
    assert any("band 500-900 Hz" in x for x in bad["blockers"])


@needs_engine
def test_engine_opens_a_good_sound_and_refuses_garbage(tmp_path):
    src = tmp_path / "test_beep.py"
    src.write_text(textwrap.dedent(SOUND), encoding="utf-8")
    b = B.build_asset(src, out_root=tmp_path / "out", quiet=True)
    assert b["ready"], b["blockers"]
    assert b["steps"]["engine"]["ok"] and "opened" in b["steps"]["engine"]["detail"]
    junk = tmp_path / "junk.wav"
    junk.write_bytes(bytes(range(256)) * 20)
    r = ENGINE.opens_sound(junk)
    assert not r["ok"] and "could not load" in r["detail"]


@needs_engine
def test_pack_carries_sounds(tmp_path, monkeypatch):
    from cadkit.game import pack as P
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "test_beep.py").write_text(textwrap.dedent(SOUND), encoding="utf-8")
    script = tmp_path / "sound_test.py"
    script.write_text('TITLE = "Sound Test"\nDESCRIPTION = "one beep"\nCOLLECTION = "sound_test"\n', encoding="utf-8")
    monkeypatch.setattr(P, "ASSETS", assets)
    monkeypatch.setattr(B, "OUT", tmp_path / "out")
    monkeypatch.setattr(P, "PACKS_OUT", tmp_path / "out" / "packs")
    m = P.build_pack(script, quiet=True)
    assert m["ready"], m["problems"]
    e = m["assets"][0]
    assert (e["kind"], e["file"], e["seconds"], e["loop"], e["bus"]) == ("sound", "audio/test_beep.wav", 0.25, False, "sfx")
    assert m["totals"]["sounds"] == 1 and m["totals"]["models"] == 0
    out = tmp_path / "out" / "packs" / "sound_test"
    assert (out / "audio" / "test_beep.wav").exists() and (out / "previews" / "test_beep.png").exists()
    assert "## Sounds" in (out / "AGENTS.md").read_text(encoding="utf-8")
