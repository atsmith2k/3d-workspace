"""Draw models/images/litho_test_card.png: the lithophane regression image.

Everything on it is generated here (no photo, no licence question): a smooth gradient,
11 grey steps, a shaded sphere (continuous tone), a Siemens star and fine lines
(resolution) and lettering. Run: .venv/Scripts/python scripts/make_litho_test_card.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 900
OUT = Path(__file__).resolve().parent.parent / "models" / "images" / "litho_test_card.png"


def main():
    a = np.full((H, W), 235.0)
    yy, xx = np.mgrid[0:H, 0:W]
    # smooth gradient band, black to white
    a[40:150, 40:W - 40] = np.linspace(0, 255, W - 80)[None, :]
    # shaded sphere, light from the upper left
    cx, cy, r = 300, 520, 230
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    inside = d2 < r * r
    nz = np.sqrt(np.clip(1 - d2 / r ** 2, 0, 1))
    nx, ny = (xx - cx) / r, (yy - cy) / r
    light = np.clip(-0.5 * nx - 0.5 * ny + 0.7 * nz, 0, 1)
    a[inside] = 20 + 225 * light[inside]
    # Siemens star
    sx, sy, sr = 860, 470, 170
    ang = np.arctan2(yy - sy, xx - sx)
    star = ((xx - sx) ** 2 + (yy - sy) ** 2 < sr * sr) & (np.sin(18 * ang) > 0)
    a[star] = 15
    im = Image.fromarray(a.astype(np.uint8))
    dr = ImageDraw.Draw(im)
    # 11 grey steps
    for i in range(11):
        x0 = 40 + i * (W - 80) / 11
        dr.rectangle([x0, 170, x0 + (W - 80) / 11, 250], fill=int(255 * i / 10))
    # line pairs 1..4 px wide (0.08-0.33 mm at 100 mm wide)
    x = 640
    for w in (1, 2, 3, 4):
        for k in range(5):
            dr.rectangle([x, 690, x + w - 1, 760], fill=0)
            x += 2 * w
        x += 30
    try:
        font = ImageFont.truetype("arialbd.ttf", 64)
    except OSError:
        font = ImageFont.load_default()
    dr.text((620, 780), "cadkit litho", fill=10, font=font)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
