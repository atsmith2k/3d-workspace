"""The Cinder engine as verifier and preview renderer.

Finds a Cinder package (CAD_CINDER, else ../cinder/dist/cinder-windows-x64 beside this repo,
else a Linux checkout's .cache/bin), runs `cinder-play` headless on generated world files
and `cinder-cook` on sources, and returns their reports as dicts.
"""
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_PROBE_OK = None                      # set once: the audio probe rejects garbage on this engine


@dataclass
class Engine:
    root: Path
    play_exe: Path
    cook_exe: Path
    version: str

    def _run(self, exe, args, timeout, cwd=None):
        env = dict(os.environ, CINDER_ROOT=str(self.root) + os.sep)
        return subprocess.run([str(exe), *map(str, args)], cwd=cwd or self.root, env=env,
                              capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace")

    def play(self, world, frames=5, screenshot=None, width=1280, height=720, overview=False,
             timeout=120, seconds=None, autopilot=False, script=None, cwd=None):
        """Run a world headless. Returns the report dict; `ok` False carries `error`.
        `cwd` is the folder the world's relative model paths are resolved against."""
        args = [world, "--headless", "--width", width, "--height", height]
        args += ["--seconds", seconds] if seconds else ["--frames", frames]
        if screenshot:
            args += ["--screenshot", screenshot]
        if overview:
            args.append("--overview")
        if autopilot:
            args.append("--autopilot")
        if script:
            args += ["--script", script]
        try:
            r = self._run(self.play_exe, args, timeout, cwd)
        except subprocess.TimeoutExpired:
            return dict(ok=False, error=f"cinder-play timed out after {timeout} s")
        for line in reversed(r.stdout.strip().splitlines()):
            if line.startswith("{"):
                try:
                    rep = json.loads(line)
                    rep["exit"] = r.returncode
                    return rep
                except json.JSONDecodeError:
                    break
        return dict(ok=False, exit=r.returncode,
                    error=(r.stderr or r.stdout).strip()[-400:] or "no report from cinder-play")

    def check(self, world, cwd=None):
        r = self._run(self.play_exe, [world, "--check"], 60, cwd)
        return r.returncode == 0, r.stdout.strip()

    def cook(self, out_dir, *sources, timeout=300):
        """cinder-cook the sources. Returns dict(ok, outputs={ext: count}, text)."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            r = self._run(self.cook_exe, [out_dir, *sources], timeout)
        except subprocess.TimeoutExpired:
            return dict(ok=False, outputs={}, text=f"cinder-cook timed out after {timeout} s")
        outputs = {}
        for f in out_dir.iterdir():
            if f.suffix and f.name != "manifest.txt":
                outputs[f.suffix[1:]] = outputs.get(f.suffix[1:], 0) + 1
        return dict(ok=r.returncode == 0, outputs=outputs,
                    text=(r.stdout + r.stderr).strip()[-600:])

    def opens_sound(self, wav):
        """Does Cinder's audio engine (miniaudio) open this file?

        There is no audio in the world kit, so the sample game is used as the probe: run headless
        from a scratch folder, it opens `assets/game/audio/music_level.wav` as a streamed sound
        before anything else, and stops with `audio: could not load` when it cannot. The file
        under test stands in for that one. A random-bytes control is run once per process to
        prove this engine build's probe tells a good file from a bad one."""
        import shutil
        import tempfile
        sample = self.play_exe.with_name("sample" + self.play_exe.suffix)
        if not sample.exists():
            return dict(ok=False, detail="no sample game beside cinder-play to open the sound with")

        def refused(src_bytes=None, src=None):
            with tempfile.TemporaryDirectory() as tmp:
                dst = Path(tmp) / "assets" / "game" / "audio"
                dst.mkdir(parents=True)
                if src is not None:
                    shutil.copyfile(src, dst / "music_level.wav")
                else:
                    (dst / "music_level.wav").write_bytes(src_bytes)
                try:
                    r = self._run(sample, ["--headless", "--autopilot", "--frames", 2], 120, cwd=tmp)
                except subprocess.TimeoutExpired:
                    return None, "the sample game timed out"
                text = r.stdout + r.stderr
                return "audio: could not load" in text, text.strip().splitlines()[-1][-160:] if text.strip() else ""

        global _PROBE_OK
        if _PROBE_OK is None:
            bad, _ = refused(src_bytes=os.urandom(4096))
            _PROBE_OK = bad is True
        if not _PROBE_OK:
            return dict(ok=False, detail="the audio probe does not reject a garbage file on this engine build, "
                                         "so it cannot vouch for a good one")
        bad, last = refused(src=wav)
        if bad is None:
            return dict(ok=False, detail=last)
        return dict(ok=not bad, method="sample game, headless, file as its streamed music",
                    detail=("the audio engine opened it (streamed)" if not bad else
                            "the audio engine could not load it: " + last))

    def info(self):
        return dict(root=str(self.root), version=self.version, play=str(self.play_exe),
                    cook=str(self.cook_exe))


def _version(root):
    for name in ("AGENTS.md", "README.md"):
        f = root / name
        if f.exists():
            m = re.search(r"Cinder (\d+\.\d+\.\d+)", f.read_text(encoding="utf-8", errors="replace"))
            if m:
                return m.group(1)
    for z in root.parent.glob("cinder-*-windows-x64.zip"):
        m = re.search(r"cinder-(\d+\.\d+\.\d+)-", z.name)
        if m:
            return m.group(1)
    return "unknown"


def find():
    """The Engine to verify against, or None when no Cinder package is installed."""
    roots = []
    if os.environ.get("CAD_CINDER"):
        roots.append(Path(os.environ["CAD_CINDER"]))
    roots += [ROOT.parent / "cinder" / "dist" / "cinder-windows-x64", ROOT.parent / "cinder"]
    for root in roots:
        for sub, ext in (("bin", ".exe"), (".cache/bin", "")):
            play, cook = root / sub / f"cinder-play{ext}", root / sub / f"cinder-cook{ext}"
            if play.exists() and cook.exists() and (ext == ".exe") == (sys.platform == "win32"):
                return Engine(root, play, cook, _version(root))
    return None


# ---------------------------------------------------------------- world files

def _v(seq):
    return "[" + ",".join(f"{float(x):.4g}" for x in seq) + "]"


def camera_orbit(centre, radius, azimuth, elevation=22.0, fov=40.0, fill=0.8):
    """Camera position looking at `centre` so a sphere of `radius` fills `fill` of the frame
    height. azimuth 0 looks from +Z (the model's back is -Z forward)."""
    dist = radius / math.sin(math.radians(fov / 2)) / fill
    a, e = math.radians(azimuth), math.radians(elevation)
    return (centre[0] + dist * math.cos(e) * math.sin(a), centre[1] + dist * math.sin(e),
            centre[2] + dist * math.cos(e) * math.cos(a))


def staging_world(model_path, bounds, azimuth=35.0, body=None, collider="auto", drop=0.0,
                  reference=True, title="staging", empty=False, radius=None):
    """A world that shows one model standing on a floor, lit by a sun, beside a 1.8 m figure.

    The model's lowest point rests on Y=0 (plus `drop` metres). With `body`, the entity is
    solid, which is how the drop test checks the collider against the visual bounds.
    """
    lo, hi = bounds
    size = [hi[i] - lo[i] for i in range(3)]
    centre = [(hi[i] + lo[i]) / 2 for i in range(3)]
    y = -lo[1] + drop
    radius = radius or max(0.5 * math.sqrt(sum(s * s for s in size)), 0.05)
    look = (centre[0], centre[1] + y - drop, centre[2])
    cam = camera_orbit(look, radius, azimuth)
    floor = max(40.0, radius * 20)
    lines = [
        "cinder-world 1",
        f'world title="{title}"',
        "environment exposure=1.0 sun_intensity=1 ambient=1",
        "entity sun",
        '  light kind="sun" direction=[-0.45,-1,-0.55] intensity=3.2 shadows=true',
        "entity floor",
        "  transform position=[0,-0.5,0]",
        f'  shape kind="box" size={_v((floor, 1, floor))} color=[0.42,0.43,0.45] roughness=0.9',
        '  body motion="static"',
    ]
    if not empty:                                  # `empty` gives the same stage without the asset
        lines += ["entity asset", f"  transform position={_v((0, y, 0))}",
                  f'  model path="{Path(model_path).resolve().as_posix()}"']
    if body and not empty:
        lines.append(f'  body motion="{body}" collider="{collider}"')
    if reference:
        x = hi[0] + 0.6 + radius * 0.6
        lines += ["entity figure",
                  f"  transform position={_v((x, 0.9, centre[2]))}",
                  '  shape kind="box" size=[0.45,1.8,0.25] color=[0.85,0.45,0.2] roughness=0.8']
    lines += ["entity view",
              f"  transform position={_v(cam)}",
              f"  camera fov=40 target={_v(look)}"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- reading the cook back

def read_cooked_clips(cook_dir, prefix):
    """The `.cclip` files cinder-cook wrote for `prefix`, parsed from the documented layout
    (magic CCLP, u32 version, string name, f32 duration, u32 channels, then per channel six
    u32 and the key times and values). This is what the engine's own importer made of the
    animations: name, duration, channel count and key count per clip."""
    import struct
    cook_dir = Path(cook_dir)
    out = []
    manifest = cook_dir / "manifest.txt"
    if not manifest.exists():
        return out
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 3 or not parts[0].startswith(prefix + "#anim"):
            continue
        raw = (cook_dir / parts[2]).read_bytes()
        magic, version, n = struct.unpack_from("<4sII", raw, 0)
        off = 12
        name = raw[off:off + n].decode("utf-8")
        off += n
        duration, channels = struct.unpack_from("<fI", raw, off)
        off += 8
        keys, paths = [], []
        for _ in range(channels):
            node, path, interp, comps, key_count, value_count = struct.unpack_from("<6I", raw, off)
            off += 24 + 4 * key_count + 4 * value_count
            keys.append(key_count)
            paths.append(path)
        out.append(dict(logical=parts[0], magic=magic.decode("ascii", "replace"), version=version, name=name,
                        duration=round(duration, 4), channels=channels, keys=sorted(set(keys)),
                        rotation_channels=paths.count(1), translation_channels=paths.count(0),
                        consumed_all=off == len(raw)))
    return out


# ---------------------------------------------------------------- cinder-probe
#
# The world kit cannot show a UI tree or a font. tools/cinder_probe/cinder_probe.mojo is a small
# program of ours, compiled against the engine's source in its Windows toolchain container, that
# asks the engine directly. It needs a Cinder checkout (source, shaders, DLLs), not just a package.

PROBE_SOURCE = ROOT / "tools" / "cinder_probe" / "cinder_probe.mojo"


def cinder_checkout():
    """The Cinder source checkout the probe is built against: CAD_CINDER_SRC, else ../cinder."""
    root = Path(os.environ.get("CAD_CINDER_SRC") or ROOT.parent / "cinder")
    return root if (root / "tools" / "windows" / "build.sh").exists() else None


def _probe_paths():
    src = cinder_checkout()
    if src is None:
        return None, None, None
    d = src / ".cache" / "probe"                      # .cache is git-ignored in the engine repository
    return src, d / "cinder-probe.exe", d / "source.sha256"


def _sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe_state():
    """(exe or None, why not). The probe is usable when it was built from the current source."""
    src, exe, stamp = _probe_paths()
    if src is None:
        return None, "no Cinder source checkout (set CAD_CINDER_SRC); the probe is built against the engine"
    if not exe.exists():
        return None, "cinder-probe is not built: run `cad game probe build`"
    if not stamp.exists() or stamp.read_text().strip() != _sha(PROBE_SOURCE):
        return None, "cinder-probe is older than its source: run `cad game probe build`"
    return exe, ""


def probe_build(timeout=900):
    """Compile the probe for Windows in the engine's toolchain container. Returns (ok, text)."""
    import shutil
    src, exe, stamp = _probe_paths()
    if src is None:
        return False, "no Cinder source checkout (set CAD_CINDER_SRC)"
    exe.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROBE_SOURCE, exe.parent / "cinder_probe.mojo")
    bash = shutil.which("bash")
    if bash is None:
        return False, "bash (Git for Windows) is needed to run the engine's build script"
    exe.unlink(missing_ok=True)
    try:
        r = subprocess.run([bash, "tools/windows/in_container.sh", "tools/windows/build.sh", "-o",
                            ".cache/probe/cinder-probe.exe", ".cache/probe/cinder_probe.mojo"],
                           cwd=src, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, f"the build timed out after {timeout} s"
    text = (r.stdout + r.stderr).strip()
    if r.returncode != 0 or not exe.exists():
        return False, text[-1500:] or "the build produced no executable"
    stamp.write_text(_sha(PROBE_SOURCE))
    return True, f"built {exe}"


def probe_info():
    src, exe, _ = _probe_paths()
    usable, why = probe_state()
    info = dict(probe=str(exe) if usable else None, checkout=str(src) if src else None)
    if src:
        try:
            info["commit"] = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=src, capture_output=True,
                                            text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    if not usable:
        info["why_not"] = why
    return info


def _probe(args, timeout=120):
    """Run the probe. Returns (report dict or None, problem)."""
    exe, why = probe_state()
    if exe is None:
        return None, why
    src = cinder_checkout()
    env = dict(os.environ, CINDER_ROOT=str(src) + os.sep)
    try:
        r = subprocess.run([str(exe), *map(str, args)], cwd=src, env=env, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return None, f"cinder-probe timed out after {timeout} s"
    for line in reversed(r.stdout.strip().splitlines()):
        if line.startswith("{"):
            try:
                return json.loads(line), ""
            except json.JSONDecodeError:
                break
    err = (r.stderr or r.stdout).strip().splitlines()
    msg = next((ln for ln in reversed(err) if "exception" in ln.lower() or "error" in ln.lower()), err[-1] if err else "")
    return None, "the engine rejected it: " + msg[-300:]


def probe_ui(document, png, font=None):
    """Have Cinder read a UI document, lay it out, draw it to `png` and write it back."""
    args = ["ui", Path(document).resolve(), Path(png).resolve()]
    if font:
        args.append(Path(font).resolve())
    return _probe(args)


def probe_font(ttf, png):
    """Have Cinder parse a font, bake its atlas at 24 px and draw sample text in it to `png`."""
    return _probe(["font", Path(ttf).resolve(), Path(png).resolve()])
