"""The preview contact sheet: Cinder's own frames of the asset, its texture maps, its UV
layout and the numbers."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .texture import to_u8

BG, INK, MUTED, OK, BAD = (24, 24, 27), (236, 236, 232), (150, 150, 150), (120, 200, 130), (240, 110, 100)


def _font(size):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _uv_tile(model, size):
    img = Image.new("RGB", (size, size), (34, 34, 38))
    d = ImageDraw.Draw(img)
    uv = np.vstack([m.uv for m, _ in model.parts])
    lo, hi = uv.min(0), uv.max(0)
    span = max((hi - lo).max(), 1e-6)
    colours = [(110, 190, 255), (255, 190, 110), (150, 230, 150), (240, 140, 220)]
    for k, (m, _) in enumerate(model.parts):
        p = (m.uv - lo) / span * (size - 9) + 4
        step = max(1, len(m.f) // 4000)
        for a, b, c in m.f[::step]:
            d.polygon([tuple(p[a]), tuple(p[b]), tuple(p[c])], outline=colours[k % 4])
    d.text((6, size - 18), f"uv {lo[0]:.2f}..{hi[0]:.2f}, {lo[1]:.2f}..{hi[1]:.2f}", fill=INK, font=_font(12))
    return img


def render_sheet(path, shots, model, title, lines, results, ready, rows=()):
    """shots: list of (label, png path or None)."""
    W, cell_w, cell_h, pad = 1600, 800, 450, 0
    strip = 300
    text_h = 26 + 18 * (len(lines) + len(results) + 1)
    row_h = 400
    base_h = 60 + 2 * cell_h + strip + max(0, text_h - strip) + 20
    sheet = Image.new("RGB", (W, base_h + len(rows) * row_h), BG)
    d = ImageDraw.Draw(sheet)
    d.text((16, 14), title, fill=INK, font=_font(26))
    verdict = "ready YES" if ready else "ready NO"
    d.text((W - 190, 16), verdict, fill=OK if ready else BAD, font=_font(24))
    for i, (label, shot) in enumerate(shots[:4]):
        x, y = (i % 2) * cell_w, 60 + (i // 2) * cell_h
        if shot:
            with Image.open(shot) as im:
                sheet.paste(im.convert("RGB").resize((cell_w - pad, cell_h - pad), Image.LANCZOS), (x, y))
        else:
            d.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(60, 60, 60))
            d.text((x + 20, y + 20), "no engine frame", fill=BAD, font=_font(18))
        d.text((x + 10, y + 8), label, fill=(255, 255, 255), font=_font(14))
    y0 = 60 + 2 * cell_h + 10
    x, tile = 10, 216
    tiles = [("uv layout", _uv_tile(model, tile))]
    for mat in model.materials:
        for slot, img in mat.textures().items():
            a = to_u8(img)
            if a.ndim == 2:
                a = np.dstack([a] * 3)
            tiles.append((f"{mat.name}.{slot} {img.shape[1]}x{img.shape[0]}",
                          Image.fromarray(a[..., :3]).resize((tile, tile), Image.LANCZOS)))
    for label, im in tiles[:4]:
        sheet.paste(im, (x, y0))
        d.text((x, y0 + tile + 4), label, fill=MUTED, font=_font(13))
        x += tile + 12
    tx, ty, f = x + 8, y0, _font(13)
    for line in lines:
        d.text((tx, ty), line, fill=INK, font=f)
        ty += 18
    ty += 6
    for r in results:
        d.text((tx, ty), ("PASS  " if r["ok"] else "FAIL  ") + r["name"] + ("" if r["ok"] else ": " + r["detail"][:70]), fill=OK if r["ok"] else BAD, font=f)
        ty += 18
    for i, (label, png) in enumerate(rows):                 # e.g. a pose strip per clip
        y = base_h + i * row_h
        if png:
            with Image.open(png) as im:
                im = im.convert("RGB")
                w = int(im.width * row_h / im.height)
                sheet.paste(im.resize((w, row_h), Image.LANCZOS), ((W - w) // 2, y))
        d.text((12, y + 8), label, fill=(255, 255, 255), font=_font(15))
    sheet.save(path)
    return path
