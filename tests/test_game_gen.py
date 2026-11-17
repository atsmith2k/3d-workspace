"""The optional generative step: cache-first, a record per input, nothing ships uncleared.
No test calls a real service: providers are faked or their HTTP layer is replaced."""
import base64
import io
import json
import textwrap

import numpy as np
import pytest
from PIL import Image

from cadkit.game import build as B
from cadkit.game import engine as E
from cadkit.game import gen
from cadkit.game.texture import seam_error

ENGINE = E.find()
needs_engine = pytest.mark.skipif(ENGINE is None, reason="no Cinder package (set CAD_CINDER)")


def _png(size=64, seed=0):
    rng = np.random.default_rng(seed)
    img = (np.clip(rng.random((size, size, 3)) * 0.5 + 0.25, 0, 1) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def fake(tmp_path, monkeypatch):
    """A provider that needs no key and counts its calls, and an empty cache folder."""
    calls = []

    def provider(kind, prompt, model, params, key):
        calls.append(prompt)
        return _png(seed=len(calls)), dict(note="fake")
    monkeypatch.setattr(gen, "GEN_DIR", tmp_path / "gen")
    monkeypatch.setitem(gen.PROVIDERS, "fake", provider)
    gen.begin(False)
    return calls


def test_a_build_never_generates_unless_asked(fake):
    with pytest.raises(gen.NotGenerated) as e:
        gen.image("a red dragon", name="dragon", provider="fake")
    assert "--gen" in str(e.value) and fake == []
    gen.begin(True)
    img = gen.image("a red dragon", name="dragon", provider="fake")
    assert img.shape == (64, 64, 3) and fake == ["a red dragon"]
    rec = gen.record("dragon")
    assert (rec["provider"], rec["prompt"], rec["cleared"], rec["kind"]) == ("fake", "a red dragon", False, "image")
    assert rec["sha256"] and rec["created_at"].endswith("Z")
    gen.begin(False)                                              # from the cache: offline, same pixels, no call
    again = gen.image("a red dragon", name="dragon", provider="fake")
    assert np.array_equal(img, again) and len(fake) == 1
    assert [r["id"] for r in gen.used()] == ["dragon"]


def test_a_changed_request_does_not_silently_reuse_an_old_picture(fake):
    gen.begin(True)
    gen.image("a red dragon", name="dragon", provider="fake")
    with pytest.raises(SystemExit) as e:
        gen.image("a blue dragon", name="dragon", provider="fake")
    assert "different request" in str(e.value) and len(fake) == 1
    a = gen.image("a red dragon", provider="fake")               # unnamed: the id is a hash of the request
    b = gen.image("a green dragon", provider="fake")
    assert len(gen.records()) == 3 and not np.array_equal(a, b)


def test_clearing_needs_a_person_and_a_reason(fake):
    gen.begin(True)
    gen.image("x", name="thing", provider="fake")
    with pytest.raises(SystemExit):
        gen.clear("thing", "", "")
    with pytest.raises(SystemExit):
        gen.clear("nothing", "A", "b")
    rec = gen.clear("thing", "A. Person", "provider terms read; no trademark, no likeness")
    assert rec["cleared"] and rec["cleared_by"] == "A. Person" and gen.record("thing")["cleared_at"]


def test_keys_come_from_the_environment_or_dot_env_and_nowhere_else(tmp_path, monkeypatch):
    monkeypatch.setattr(gen, "ROOT", tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert gen.keys_present() == dict(openai=False, elevenlabs=False)
    (tmp_path / ".env").write_text('# keys\nOPENAI_API_KEY="sk-test"\nOTHER=1\n', encoding="utf-8")
    assert gen.key("openai") == "sk-test" and gen.key("elevenlabs") is None
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    assert gen.key("openai") == "sk-env"                          # the environment wins


def test_a_missing_key_stops_before_any_request(tmp_path, monkeypatch):
    monkeypatch.setattr(gen, "GEN_DIR", tmp_path / "gen")
    monkeypatch.setattr(gen, "ROOT", tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(gen, "_post", lambda *a, **k: pytest.fail("a request was made without a key"))
    gen.begin(True)
    with pytest.raises(SystemExit) as e:
        gen.image("x", name="y")
    assert "OPENAI_API_KEY is not set" in str(e.value)


def test_openai_request_and_response(tmp_path, monkeypatch):
    sent = {}

    def post(url, headers, body, timeout=180):
        sent.update(url=url, headers=headers, body=body)
        return json.dumps(dict(created=1, data=[dict(b64_json=base64.b64encode(_png(32)).decode())])).encode(), {}
    monkeypatch.setattr(gen, "GEN_DIR", tmp_path / "gen")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(gen, "_post", post)
    gen.begin(True)
    img = gen.image("a banner", name="banner", size=(1024, 1536), quality="high")
    assert img.shape == (32, 32, 3)
    assert sent["url"] == "https://api.openai.com/v1/images/generations"
    assert sent["headers"] == {"Authorization": "Bearer sk-test"}
    assert sent["body"] == dict(model="gpt-image-2", prompt="a banner", n=1, size="1024x1536", quality="high")
    rec = json.loads((tmp_path / "gen" / "banner.json").read_text(encoding="utf-8"))
    assert "sk-test" not in json.dumps(rec)                       # the key is never written down
    assert rec["terms"].startswith("https://openai.com")


def test_elevenlabs_request_and_response(tmp_path, monkeypatch):
    from scipy.io import wavfile
    sent = {}

    def post(url, headers, body, timeout=180):
        sent.update(url=url, headers=headers, body=body)
        buf = io.BytesIO()
        wavfile.write(buf, 48000, (np.sin(np.linspace(0, 200, 4800)) * 20000).astype(np.int16))
        return buf.getvalue(), {"request-id": "r1"}
    monkeypatch.setattr(gen, "GEN_DIR", tmp_path / "gen")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "xi-test")
    monkeypatch.setattr(gen, "_post", post)
    gen.begin(True)
    x = gen.sound("a heavy door slams", name="slam", seconds=1.5)
    assert len(x) == 4800 and 0.5 < np.abs(x).max() < 0.7
    assert sent["url"] == "https://api.elevenlabs.io/v1/sound-generation?output_format=wav_48000"
    assert sent["headers"] == {"xi-api-key": "xi-test"}
    assert sent["body"] == dict(text="a heavy door slams", prompt_influence=0.3, loop=False,
                                model_id="eleven_text_to_sound_v2", duration_seconds=1.5)


def test_tileable_and_material():
    y, x = np.mgrid[:128, :128] / 128
    ramp = np.dstack([x, y, 0.5 * np.ones_like(x)])               # does not tile at all
    assert seam_error(ramp) > 20
    t = gen.tileable(ramp, 0.2)
    assert t.shape[0] == t.shape[1] and t.shape[0] < 128 and seam_error(t) < 3
    mat = gen.material(np.random.default_rng(1).random((300, 200, 3)) * 0.5 + 0.25, "m")
    assert mat.base.shape == (128, 128, 3) and mat.normal.shape == (128, 128, 3) and mat.orm.shape == (128, 128, 3)
    assert mat.metallic == 1.0 and mat.roughness == 1.0


ASSET = '''
from cadkit.game import *
from cadkit.game import gen
KIND = "prop"
DESCRIPTION = "test sign"
PARAMS = dict()
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = dict(collection="gen_test", licence="CC0-1.0")
def build(p):
    art = gen.image("a painted sign", name="sign_art", provider="fake")
    return Model((box(0.5, 0.5, 0.5), gen.material(art, "sign", size=64)))
'''


def test_an_asset_records_what_it_was_made_from(fake, tmp_path):
    src = tmp_path / "test_sign.py"
    src.write_text(textwrap.dedent(ASSET), encoding="utf-8")
    with pytest.raises(gen.NotGenerated):
        B.build_asset(src, out_root=tmp_path / "out", use_engine=False, quiet=True)
    b = B.build_asset(src, out_root=tmp_path / "out", use_engine=False, quiet=True, generate=True)
    assert b["generated"] == [dict(id="sign_art", kind="image", provider="fake", model="fake",
                                   prompt="a painted sign", cleared=False, cleared_by=None)]
    assert b["cleared"] is False
    saved = json.loads((tmp_path / "out" / "test_sign" / "build.json").read_text(encoding="utf-8"))
    assert saved["generated"][0]["id"] == "sign_art"
    assert "NOT CLEARED" in (tmp_path / "out" / "test_sign" / "report.txt").read_text(encoding="utf-8")
    plain = tmp_path / "plain.py"
    plain.write_text(textwrap.dedent(ASSET).replace('gen.image("a painted sign", name="sign_art", provider="fake")',
                                                    "np.full((64, 64, 3), 0.5)"), encoding="utf-8")
    c = B.build_asset(plain, out_root=tmp_path / "out", use_engine=False, quiet=True)
    assert c["generated"] == [] and c["cleared"] is True


@needs_engine
def test_a_pack_refuses_an_uncleared_input_and_takes_it_once_cleared(fake, tmp_path, monkeypatch):
    from cadkit.game import pack as P
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "test_sign.py").write_text(textwrap.dedent(ASSET), encoding="utf-8")
    script = tmp_path / "gen_test.py"
    script.write_text('TITLE = "Gen Test"\nDESCRIPTION = "one sign"\nCOLLECTION = "gen_test"\n', encoding="utf-8")
    monkeypatch.setattr(P, "ASSETS", assets)
    monkeypatch.setattr(B, "OUT", tmp_path / "out")
    monkeypatch.setattr(P, "PACKS_OUT", tmp_path / "out" / "packs")
    built = B.build_asset(assets / "test_sign.py", quiet=True, generate=True)
    assert built["ready"] and not built["cleared"]               # it works in the engine; it still may not ship
    with pytest.raises(SystemExit) as e:
        P.build_pack(script, quiet=True)
    assert "not cleared by a person" in str(e.value) and "sign_art" in str(e.value)
    gen.clear("sign_art", "A. Person", "terms read; original picture, no marks")
    m = P.build_pack(script, quiet=True)                          # no rebuild needed: clearance is read at pack time
    assert m["ready"], m["problems"]
    entry = m["assets"][0]
    assert entry["generated_inputs"][0]["cleared_by"] == "A. Person" and "generated inputs" in entry["provenance"]
    text = (tmp_path / "out" / "packs" / "gen_test" / "ATTRIBUTION.md").read_text(encoding="utf-8")
    assert "sign_art" in text and "A. Person" in text and "a painted sign" in text
