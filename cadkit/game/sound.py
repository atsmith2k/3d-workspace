"""Building one sound: WAV out, checks, the engine's audio layer, and a picture to judge by.

The ladder for a sound:
    static   format, level, clicks, DC, loop seam, mono/stereo rule, and the script's own checks
             (duration, where its energy sits), on the samples and on the WAV read back by
             scipy (the writer is the standard library's `wave`)
    engine   Cinder's audio engine opens the file (see Engine.opens_sound)
    look     <name>_preview.png: waveform and spectrogram. Nobody here can listen: the
             spectrogram, the band checks and the numbers are what a sound is judged by.

Writes output/game/<name>/: <name>.wav (48 kHz, 16-bit PCM), <name>_preview.png, build.json,
readiness.json, report.txt.
"""
import time
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw
from scipy import signal
from scipy.io import wavfile

from .. import outputs
from . import audio as A
from . import engine as E
from .checks import Check, _name_ok
from .render import BAD, BG, INK, MUTED, OK, _font


def write_wav(path, samples):
    """48 kHz 16-bit PCM. Returns the int16 array written."""
    x = np.clip(np.asarray(samples, float), -1.0, 1.0)
    pcm = np.round(x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1 if pcm.ndim == 1 else pcm.shape[1])
        w.setsampwidth(2)
        w.setframerate(A.SR)
        w.writeframes(pcm.tobytes())
    return pcm


# ---------------------------------------------------------------- checks a script can ask for

def duration(lo, hi=None):
    """Length in seconds: a (lo, hi) range, or a number +-5 %."""
    a, b = (lo, hi) if hi is not None else (lo * 0.95, lo * 1.05)

    def fn(ctx):
        d = ctx.sound.duration
        return a <= d <= b, f"{d:.3f} s (wanted {a:g}..{b:g})"
    return Check("duration", fn)


def band(lo, hi, at_least=None, at_most=None, name=None):
    """Share of the energy between lo and hi Hz: how a thud is told from a chime without ears."""
    def fn(ctx):
        s = A.band_share(ctx.sound.samples, lo, hi)
        ok = (at_least is None or s >= at_least) and (at_most is None or s <= at_most)
        want = " and ".join(x for x in (f">= {at_least:.1%}" if at_least is not None else "",
                                        f"<= {at_most:.1%}" if at_most is not None else "") if x)
        return ok, f"{s:.1%} of the energy in {lo:g}-{hi:g} Hz (wanted {want})"
    return Check(name or f"band {lo:g}-{hi:g} Hz", fn)


def peak(lo=-6.0, hi=-0.5):
    def fn(ctx):
        p = A.db(np.abs(ctx.sound.samples).max())
        return lo <= p <= hi, f"peak {p:.1f} dBFS (wanted {lo:g}..{hi:g})"
    return Check("peak", fn)


def custom(name, fn):
    """fn(ctx) -> (ok, detail); ctx.sound, ctx.read (sample rate and int16 data read back), ctx.params."""
    return Check(name, fn)


# ---------------------------------------------------------------- always run

def _format(ctx):
    sr, data = ctx.read
    s, bad = ctx.sound, []
    if sr != A.SR:
        bad.append(f"sample rate {sr}")
    if data.dtype != np.int16:
        bad.append(f"sample type {data.dtype}")
    ch = 1 if data.ndim == 1 else data.shape[1]
    if ch != s.channels or len(data) != len(s.samples):
        bad.append(f"file has {len(data)} frames x {ch} ch; built {len(s.samples)} x {s.channels}")
    elif np.abs(data / 32767.0 - np.clip(s.samples, -1, 1)).max() > 1.5 / 32767:
        bad.append("samples differ from what was built")
    return not bad, "; ".join(bad) or f"48 kHz, 16-bit PCM, {ch} ch, reads back as built (scipy)"


def _level(ctx):
    x = ctx.sound.samples
    pk, rms = np.abs(x).max(), np.sqrt((x ** 2).mean())
    bad = []
    if pk > 10 ** (-0.3 / 20):
        bad.append(f"peak {A.db(pk):.1f} dBFS: leave 0.3 dB or it clips in the mix")
    if pk < 10 ** (-12 / 20):
        bad.append(f"peak {A.db(pk):.1f} dBFS: too quiet (normalize to about -3)")
    dc = np.abs(x.mean(axis=0)).max()
    if dc > 0.005:
        bad.append(f"DC offset {dc:.3f}")
    if not np.isfinite(x).all():
        bad.append("non-finite samples")
    return not bad, "; ".join(bad) or f"peak {A.db(pk):.1f} dBFS, RMS {A.db(rms):.1f} dBFS, no DC offset"


def _edges(ctx):
    s = ctx.sound
    x = s.samples if s.samples.ndim == 1 else s.samples.mean(1)
    step = np.abs(np.diff(x))
    typical = max(float(np.percentile(step, 99.5)), 1e-4)
    if s.loop:
        seam = abs(x[0] - x[-1])
        slope = abs((x[1] - x[0]) - (x[-1] - x[-2]))
        ok = seam <= 1.5 * typical and slope <= 3 * typical
        return ok, (f"loop seam step {seam:.4f} (the sound's own largest steps are {typical:.4f})"
                    + ("" if ok else ": it will click every time it wraps"))
    head, tail = abs(x[0]), abs(x[-1])
    quiet = np.abs(x) > np.abs(x).max() * 10 ** (-60 / 20)        # 60 dB under its own peak
    trailing = (len(x) - 1 - np.nonzero(quiet)[0][-1]) / A.SR if quiet.any() else s.duration
    bad = []
    if head > 0.005 or tail > 0.005:
        bad.append(f"first sample {head:.3f}, last {tail:.3f}: fade it or it clicks")
    if trailing > 0.15:
        bad.append(f"{trailing * 1000:.0f} ms of silence at the end: trim it")
    return not bad, "; ".join(bad) or "starts and ends at zero, no trailing silence"


def _channels(ctx):
    s = ctx.sound
    if s.spatial and s.channels != 1:
        return False, "a spatial sound must be mono: Cinder places it in 3D"
    if s.channels > 2:
        return False, f"{s.channels} channels"
    return True, f"{'mono' if s.channels == 1 else 'stereo'}, {'spatial' if s.spatial else 'not spatial'}, bus {s.bus}"


def _budget(ctx):
    b = ctx.budget or {}
    bad = []
    if "seconds" in b and ctx.sound.duration > b["seconds"]:
        bad.append(f"{ctx.sound.duration:.2f} s over BUDGET {b['seconds']} s")
    if "kb" in b and ctx.bytes / 1024 > b["kb"]:
        bad.append(f"{ctx.bytes / 1024:.0f} kB over BUDGET {b['kb']} kB")
    return not bad, "; ".join(bad) or (f"within BUDGET {b}" if b else "no BUDGET declared")


def static_checks():
    return [Check("name", _name_ok), Check("format", _format), Check("level", _level),
            Check("edges", _edges), Check("channels", _channels), Check("budget", _budget)]


# ---------------------------------------------------------------- picture

def _ramp(v):
    """0..1 -> a dark-to-bright colour ramp (black, purple, orange, pale yellow)."""
    stops = np.array([[0, 0, 4], [60, 15, 100], [160, 45, 95], [240, 120, 40], [252, 230, 150]], float)
    x = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(x.astype(int), len(stops) - 2)
    f = (x - i)[..., None]
    return (stops[i] * (1 - f) + stops[i + 1] * f).astype(np.uint8)


def render_sound(path, sound, title, lines, results, ready):
    W, wave_h, spec_h = 1600, 260, 420
    x = sound.samples if sound.samples.ndim == 1 else sound.samples.mean(1)
    sheet = Image.new("RGB", (W, 60 + wave_h + spec_h + 60 + 18 * (len(lines) + (len(results) + 1) // 2)), BG)
    d = ImageDraw.Draw(sheet)
    d.text((16, 14), title, fill=INK, font=_font(26))
    d.text((W - 190, 16), "ready YES" if ready else "ready NO", fill=OK if ready else BAD, font=_font(24))
    # waveform: min and max per column
    y0, mid = 60, 60 + wave_h // 2
    d.rectangle([0, y0, W, y0 + wave_h], fill=(30, 30, 34))
    cols = np.array_split(x, W)
    for i, c in enumerate(cols):
        if len(c):
            d.line([(i, mid - c.max() * (wave_h / 2 - 6)), (i, mid - c.min() * (wave_h / 2 - 6))], fill=(120, 200, 255))
    d.line([(0, mid), (W, mid)], fill=(70, 70, 76))
    d.text((8, y0 + 4), f"waveform, {sound.duration:.2f} s" + ("  (loops: the right edge runs into the left)"
                                                                 if sound.loop else ""), fill=MUTED, font=_font(13))
    # spectrogram: log frequency 40 Hz .. 20 kHz
    nper = 2048 if len(x) > 8192 else 512
    f, tt, z = signal.stft(x, A.SR, nperseg=min(nper, len(x)), noverlap=min(nper, len(x)) * 3 // 4)
    mag = 20 * np.log10(np.abs(z) + 1e-7)
    mag = np.clip((mag - mag.max() + 80) / 80, 0, 1)
    rows = np.geomspace(40, 20000, spec_h)
    fi = np.clip(np.searchsorted(f, rows), 0, len(f) - 1)
    ti = np.clip((np.arange(W) * mag.shape[1] / W).astype(int), 0, mag.shape[1] - 1)
    img = _ramp(mag[fi][:, ti][::-1])
    y1 = y0 + wave_h + 8
    sheet.paste(Image.fromarray(img), (0, y1))
    for hz in (100, 1000, 10000):
        yy = y1 + spec_h - 1 - int(np.searchsorted(rows, hz))
        d.line([(0, yy), (26, yy)], fill=(255, 255, 255))
        d.text((30, yy - 8), f"{hz:g} Hz", fill=(255, 255, 255), font=_font(12))
    d.text((W - 330, y1 + 4), "spectrogram, 40 Hz to 20 kHz, 80 dB range", fill=(255, 255, 255), font=_font(13))
    ty = y1 + spec_h + 10
    for line in lines:
        d.text((12, ty), line, fill=INK, font=_font(13))
        ty += 18
    ty += 4
    for i, r in enumerate(results):
        col, row = i % 2, i // 2
        d.text((12 + col * 780, ty + row * 18), ("PASS  " if r["ok"] else "FAIL  ") + r["name"] + ": " + r["detail"][:88],
               fill=OK if r["ok"] else BAD, font=_font(13))
    sheet.save(path)


# ---------------------------------------------------------------- build

def use_snippet(name, s, rel="audio"):
    """How a Cinder game loads it: cinder.audio SoundDesc(path, bus, streamed, looping, spatial)."""
    flags = ", ".join("True" if v else "False" for v in (s.streamed, s.loop, s.spatial))
    return (f'var {name} = app.audio.value().load(SoundDesc(String("{rel}/{name}.wav"), {s.bus}_bus, {flags}))'
            f'   # streamed, looping, spatial')


def build_sound(path, mod, params, out_root, use_engine=True, quiet=False):
    t0 = time.time()
    name = Path(path).stem
    p = SimpleNamespace(**params)
    sound = mod.build(p)
    if not isinstance(sound, A.Sound):
        raise SystemExit('a KIND = "sound" script must return cadkit.game.audio.Sound from build(p)')
    out = Path(out_root) / name
    out.mkdir(parents=True, exist_ok=True)
    wav = out / f"{name}.wav"
    write_wav(wav, sound.samples)
    ctx = SimpleNamespace(sound=sound, read=wavfile.read(wav), params=params, name=name,
                          budget=getattr(mod, "BUDGET", None), bytes=wav.stat().st_size)
    spec = mod.checks(p) if callable(getattr(mod, "checks", None)) else []
    results = [c.run(ctx) for c in static_checks() + list(spec)]
    steps = dict(static=dict(ok=all(r["ok"] for r in results), checks=results))
    blockers = [f"check {r['name']}: {r['detail']}" for r in results if not r["ok"]]

    eng = E.find() if use_engine else None
    if eng is None:
        blockers.append("not verified in Cinder: " + ("skipped (--no-engine)" if not use_engine else
                        "no engine found; set CAD_CINDER to a Cinder package"))
    else:
        steps["engine"] = eng.opens_sound(wav)
        if not steps["engine"]["ok"]:
            blockers.append("engine: " + steps["engine"]["detail"])
    ready = not blockers

    x = sound.samples
    pk, rms = np.abs(x).max(), np.sqrt((x ** 2).mean())
    stats = dict(seconds=round(sound.duration, 4), channels=sound.channels, sample_rate=A.SR,
                 peak_db=round(A.db(pk), 2), rms_db=round(A.db(rms), 2), centroid_hz=round(A.centroid(x)),
                 loop=sound.loop, bus=sound.bus, spatial=sound.spatial, streamed=sound.streamed,
                 wav_bytes=ctx.bytes)
    kind = "loop" if sound.loop else "one-shot"
    lines = [
        f"{name}  (sound, {kind})  {getattr(mod, 'DESCRIPTION', '')}",
        f"length   {sound.duration:.3f} s, {'mono' if sound.channels == 1 else 'stereo'}, 48 kHz 16-bit PCM, "
        f"{ctx.bytes / 1024:.0f} kB",
        f"level    peak {stats['peak_db']:.1f} dBFS, RMS {stats['rms_db']:.1f} dBFS, brightness (centroid) "
        f"{stats['centroid_hz']} Hz",
        f"use      bus {sound.bus}, {'spatial' if sound.spatial else 'not spatial'}, "
        f"{'streamed' if sound.streamed else 'decoded at load'}",
    ]
    if "engine" in steps:
        lines.append(f"engine   Cinder {eng.version}: " + steps["engine"]["detail"])
    for r in results:
        lines.append(f"check    {'PASS' if r['ok'] else 'FAIL'}  {r['name']}: {r['detail']}")
    lines += ["BLOCKER  " + b for b in blockers]
    lines.append(f"ready    {'YES' if ready else 'NO'}")
    preview = out / f"{name}_preview.png"
    render_sound(preview, sound, f"{name}: {getattr(mod, 'DESCRIPTION', '')}",
                 [l for l in lines if not l.startswith(("check", "BLOCKER", "ready"))], results, ready)
    build = dict(schema="cadkit-game-build/1", name=name, kind="sound",
                 description=getattr(mod, "DESCRIPTION", ""), params=params, ready=ready, blockers=blockers,
                 stats=stats, use_snippet=use_snippet(name, sound),
                 files=dict(wav=wav.name, preview=preview.name, sha256=outputs.sha256(wav)),
                 product=dict(getattr(mod, "PRODUCT", {}) or {}), source_sha256=outputs.sha256(path),
                 engine=eng.info() if eng else None, steps=steps, report=lines,
                 built_at=outputs.now_iso(), seconds=round(time.time() - t0, 1), git=outputs.git_info())
    outputs.save_json(out / "build.json", build)
    outputs.save_json(out / "readiness.json", dict(ready=ready, blockers=blockers, steps=steps,
                                                   engine=build["engine"]))
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    build["out"] = str(out)
    if not quiet:
        print("\n".join(lines))
        print(f"preview  {preview}")
    return build
