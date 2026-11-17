"""The optional generative step: images and sounds from a generation service, as inputs.

Code comes first here; this is for the look a script cannot reach (painted artwork, organic
texture, a recorded-sounding effect). It is built so that using it stays honest:

- **A build never calls a service by itself.** `gen.image(...)` and `gen.sound(...)` read
  `assets/gen/<id>.png|.wav`. On a miss they stop with the command that would generate it:
  `cad game build <asset> --gen`. So an ordinary build is offline, free and repeatable, and
  services that have no seed (none of these do, reliably) cannot change an asset behind your back.
- **Everything generated has a record** beside it, `assets/gen/<id>.json`: prompt, provider,
  model, parameters, when, and `cleared: false`.
- **Nothing generated ships until a person clears it.** `cad game pack` refuses an asset with
  an uncleared input. `cad game gen clear <id> --by NAME --note "..."` records who checked the
  provider's terms and the image itself (a model can reproduce someone's work or a trademark).
- **Keys** are read from the environment or a git-ignored `.env` at the repository root:
  OPENAI_API_KEY (images), ELEVENLABS_API_KEY (sound). They are never written anywhere.

    art = gen.image("heraldic red dragon on a gold field, flat medieval tapestry, no text", name="dragon_banner")
    mat = gen.material(art, "tapestry", roughness=0.9)
"""
import base64
import hashlib
import io
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
GEN_DIR = ROOT / "assets" / "gen"
KEYS = dict(openai="OPENAI_API_KEY", elevenlabs="ELEVENLABS_API_KEY")
DEFAULT_MODEL = dict(openai="gpt-image-2", elevenlabs="eleven_text_to_sound_v2")   # gpt-image-1 was retired by 2026-11
TERMS = dict(openai="https://openai.com/policies/terms-of-use", elevenlabs="https://elevenlabs.io/terms-of-use")

_allow = False                      # set by `--gen`: a cache miss may call the service
_used = []                          # ids read during the current build


class NotGenerated(SystemExit):
    """A generated input is not in the cache and this build may not create it."""


def begin(allow=False):
    """Start a build: forget what the last one used; say whether misses may be generated."""
    global _allow
    _allow = allow
    _used.clear()


def used():
    """Records of the generated inputs the current build read, in order, without repeats."""
    return [record(i) for i in dict.fromkeys(_used)]


def key(provider):
    """The provider's API key from the environment or .env, or None. Never logged."""
    name = KEYS[provider]
    if os.environ.get(name):
        return os.environ[name]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name and v.strip():
                return v.strip().strip('"').strip("'")
    return None


def keys_present():
    return {p: key(p) is not None for p in KEYS}


def _id(kind, name, provider, model, prompt, params):
    if name:
        return name
    blob = json.dumps([kind, provider, model, prompt, params], sort_keys=True).encode()
    return f"{kind}_{hashlib.sha256(blob).hexdigest()[:12]}"


def record(gen_id):
    return json.loads((GEN_DIR / f"{gen_id}.json").read_text(encoding="utf-8"))


def records():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(GEN_DIR.glob("*.json"))] if GEN_DIR.exists() else []


def clear(gen_id, by, note):
    """Mark a generated input as checked by a person. Returns the record."""
    path = GEN_DIR / f"{gen_id}.json"
    if not path.exists():
        raise SystemExit(f"no generated input '{gen_id}' (cad game gen list)")
    if not by or not note:
        raise SystemExit("clearing needs --by (who checked) and --note (what was checked)")
    rec = json.loads(path.read_text(encoding="utf-8"))
    rec.update(cleared=True, cleared_by=by, cleared_note=note,
               cleared_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    path.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def _fetch(kind, ext, name, provider, model, prompt, params):
    """Path of the cached file for this request, generating it when allowed."""
    model = model or os.environ.get(f"CAD_GEN_{provider.upper()}_MODEL") or DEFAULT_MODEL.get(provider, provider)
    gen_id = _id(kind, name, provider, model, prompt, params)
    path, meta = GEN_DIR / f"{gen_id}.{ext}", GEN_DIR / f"{gen_id}.json"
    if path.exists() and meta.exists():
        rec = json.loads(meta.read_text(encoding="utf-8"))
        if rec["prompt"] != prompt or rec["params"] != params or rec["provider"] != provider:
            raise SystemExit(f"generated input '{gen_id}' was made from a different request (prompt, parameters or "
                             f"provider changed). Give it a new name, or delete assets/gen/{gen_id}.* to regenerate.")
        _used.append(gen_id)
        return path
    if not _allow:
        raise NotGenerated(f"generated input '{gen_id}' is not in assets/gen/. To create it (one paid call to "
                           f"{provider}): cad game build <asset> --gen   (needs {KEYS.get(provider, 'a key')})")
    if provider not in PROVIDERS:
        raise SystemExit(f"unknown provider '{provider}'; known: {', '.join(PROVIDERS)}")
    k = key(provider) if provider in KEYS else None
    if provider in KEYS and k is None:
        raise SystemExit(f"{KEYS[provider]} is not set (environment, or a line in the git-ignored .env at the repo root)")
    data, extra = PROVIDERS[provider](kind, prompt, model, params, k)
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    rec = dict(id=gen_id, kind=kind, file=path.name, provider=provider, model=model, prompt=prompt, params=params,
               created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
               sha256=hashlib.sha256(data).hexdigest(), terms=TERMS.get(provider, ""), response=extra,
               cleared=False, cleared_by=None, cleared_note=None, cleared_at=None)
    meta.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    _used.append(gen_id)
    return path


def image(prompt, name=None, size=(1024, 1024), provider="openai", model=None, quality="medium", **params):
    """A generated image as RGB floats in 0..1 (row 0 at the top). `name` is its id in
    assets/gen/ (snake_case); without one the id is a hash of the request."""
    req = dict(size=list(size), quality=quality, **params)
    path = _fetch("image", "png", name, provider, model, prompt, req)
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), float) / 255


def sound(prompt, name=None, seconds=None, provider="elevenlabs", model=None, influence=0.3, loop=False):
    """A generated sound as mono float samples at 48 kHz."""
    from scipy.io import wavfile
    req = dict(seconds=seconds, influence=influence, loop=loop)
    path = _fetch("sound", "wav", name, provider, model, prompt, req)
    sr, data = wavfile.read(path)
    x = data.astype(float) / (32768.0 if data.dtype == np.int16 else 1.0)
    if x.ndim == 2:
        x = x.mean(1)
    if sr != 48000:
        from scipy.signal import resample_poly
        x = resample_poly(x, 48000, sr)
    return x


# ---------------------------------------------------------------- providers

def _post(url, headers, body, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "cadkit-gen", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"the generation service answered {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"could not reach the generation service: {e.reason}")


def _openai(kind, prompt, model, params, k):
    if kind != "image":
        raise SystemExit("the openai provider makes images")
    w, h = params["size"]
    body = dict(model=model, prompt=prompt, n=1, size=f"{w}x{h}", quality=params.get("quality", "medium"))
    if params.get("background"):
        body["background"] = params["background"]
    raw, _ = _post("https://api.openai.com/v1/images/generations", {"Authorization": f"Bearer {k}"}, body)
    doc = json.loads(raw)
    item = doc["data"][0]
    if item.get("b64_json"):
        data = base64.b64decode(item["b64_json"])
    else:
        with urllib.request.urlopen(item["url"], timeout=180) as r:
            data = r.read()
    buf = io.BytesIO()
    Image.open(io.BytesIO(data)).save(buf, "PNG")                 # whatever came back, the cache is PNG
    return buf.getvalue(), dict(created=doc.get("created"), usage=doc.get("usage"), revised_prompt=item.get("revised_prompt"))


def _elevenlabs(kind, prompt, model, params, k):
    if kind != "sound":
        raise SystemExit("the elevenlabs provider makes sounds")
    body = dict(text=prompt, prompt_influence=params.get("influence", 0.3), loop=bool(params.get("loop")), model_id=model)
    if params.get("seconds"):
        body["duration_seconds"] = float(params["seconds"])
    raw, headers = _post("https://api.elevenlabs.io/v1/sound-generation?output_format=wav_48000", {"xi-api-key": k}, body)
    return raw, dict(request_id=headers.get("request-id"), character_cost=headers.get("character-cost"))


PROVIDERS = dict(openai=_openai, elevenlabs=_elevenlabs)


# ---------------------------------------------------------------- making a generated image usable

def tileable(img, blend=0.12):
    """Make an image repeat without a seam: each edge is cross-faded with the opposite one over
    `blend` of the size. Costs a little of the picture at the edges."""
    a = np.asarray(img, float)
    for axis in (0, 1):
        n = a.shape[axis]
        k = max(1, int(n * blend))
        w = np.linspace(0, 1, k)
        w = w.reshape((-1, 1, 1) if axis == 0 else (1, -1, 1))
        head = np.take(a, range(k), axis)
        tail = np.take(a, range(n - k, n), axis)
        mix = head * w + tail * (1 - w)
        idx = [slice(None)] * 3
        idx[axis] = slice(0, k)
        a = a.copy()
        a[tuple(idx)] = mix
        idx[axis] = slice(0, n - k)
        a = a[tuple(idx)]
    return a


def square_pow2(img, size=None):
    """Resize to a power-of-two square (the nearest below, or `size`): what a texture must be."""
    a = np.asarray(img, float)
    n = size or 2 ** int(np.floor(np.log2(min(a.shape[:2]))))
    im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((n, n), Image.LANCZOS)
    return np.asarray(im, float) / 255


def material(img, name, roughness=0.8, metallic=0.0, relief=2.0, size=None):
    """A PBR Material from a picture: the picture as base colour, a normal map from its
    brightness (so brush strokes and weave catch the light), and flat roughness."""
    from .model import Material
    from .texture import blur, normal_from_height, orm
    base = square_pow2(img, size)
    lum = blur(base.mean(2), 1)
    return Material(name, base=base, orm=orm(1.0, roughness, metallic, size=base.shape[0]),
                    normal=normal_from_height(lum, relief), metallic=1.0, roughness=1.0)
