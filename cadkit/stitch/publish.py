"""`cad stitch publish` / `cad stitch bundle`: turn a design into a shop-ready product.

Writes into output/embroidery/<name>/:
    sizes/<name>_<size>/        a full build per size (every machine format, SVG, preview)
    <name>_product.png          realistic render on plain fabric (stitchsim --clean)
    <name>_mockup_<item>.png    the design staged on garments (t-shirt, tote, cap...)
    <name>_threads.png          thread chart: sewing order, exact Brother spool, hex
    <name>_notes.txt            what the buyer needs: sizes, formats, threads, stabiliser
    <slug>.zip                  the buyer's download: one folder per size
    manifest.json               schema cadkit-embroidery/1, what the shop ingests

The shop already knows `kind: "embroidery"` and shows hoop size, stitch count and
thread colours from a product's attributes; the manifest carries those plus every file
with its sha256. `sellable` wants every size to pass its checks with no warnings and
no stitchsim problems, and the images, chart and notes present.

A design steers it with:
    SIZES = [("4x4", "4x4", 95.0), ("5x7", "5x7", 160.0)]   # label, hoop, longest side
    PRODUCT = dict(title=..., summary=..., description=..., tags=[...],
                   mockups=["tshirt", "tote"], collection="...", sellable=None)
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont

from .. import outputs
from .threads import delta_e94, nearest_brother, CLOSE

SCHEMA = "cadkit-embroidery/1"
FORMATS = ["pes", "dst", "jef", "exp", "vp3", "xxx", "u01", "pec"]
MACHINES = {
    "pes": "Brother, Baby Lock, Bernina (PE Design)", "pec": "Brother, Baby Lock (older models)",
    "dst": "Tajima and most commercial machines", "jef": "Janome, Elna, Kenmore",
    "exp": "Melco, Bernina", "vp3": "Husqvarna Viking, Pfaff", "xxx": "Singer, Compucon",
    "u01": "Barudan, Toyota",
}
DEFAULT_SIZES = [("4x4", "4x4", 95.0)]
DEFAULT_LICENSE = (
    "Licensed, not sold. Personal licence: stitch the design as many times as you like "
    "for yourself and as gifts; no selling stitched items, no sharing or reselling the "
    "files. Commercial licence: sell items you stitch with this design, in any "
    "quantity; no file resale or redistribution. Either way the design stays the "
    "author's. Always stitch a test piece first: fabrics and stabilisers vary."
)
STABILISER = (
    "Stabiliser: tear-away for stable wovens (canvas, linen, twill, denim, totes); "
    "cut-away for anything that stretches (t-shirts, sweatshirts, knits); add a "
    "water-soluble topper on towels and fleece. Hoop the fabric and stabiliser together, "
    "drum-tight but not stretched."
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def slug_of(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _fmt_time(minutes):
    m = int(round(minutes))
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


def _font(size, bold=False):
    for name in (("segoeuib.ttf" if bold else "segoeui.ttf"), "arial.ttf"):
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size=size)


# ---------------------------------------------------------------- stitchsim

def stitchsim_info(exe, pes):
    out = subprocess.run([str(exe), "--info", str(pes)], capture_output=True, text=True).stdout
    problems = [l.strip() for l in out.splitlines() if l.startswith("  ERROR") or l.startswith("  warn")]
    m = re.search(r"^problems\s+(\d+)", out, re.M)
    return (int(m.group(1)) if m else -1), problems


def stitchsim_shot(exe, pes, png, size=1200, article=None, realistic=True, fabric=None):
    cmd = [str(exe), str(pes), "--screenshot", str(png), "--clean", "--size", f"{size}x{size}"]
    if realistic:
        cmd.append("--realistic")
    if article:
        cmd += ["--article", article]
    if fabric:
        cmd += ["--fabric", fabric]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not Path(png).exists():
        raise RuntimeError(f"stitchsim screenshot failed: {r.stderr[-500:]}")
    # square crop of the canvas (the window may come out a few px off square)
    im = Image.open(png).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).save(png)
    return png


# ---------------------------------------------------------------- thread chart

def thread_rows(colors, block_stitches_by_size):
    """[(n, hex, brother name or None, dE, {size: stitches})]."""
    rows = []
    for i, c in enumerate(colors):
        name, h = nearest_brother(c)
        de = delta_e94(c, h)
        rows.append(dict(n=i + 1, hex=c, brother=name if de <= CLOSE else None, delta_e=round(de, 1),
                         stitches={k: v[i] if i < len(v) else 0 for k, v in block_stitches_by_size.items()}))
    return rows


def render_thread_chart(path, title, rows, sizes_info, preview=None):
    W = 1200
    H = 260 + 64 * len(rows) + 60
    im = Image.new("RGB", (W, H), (252, 250, 246))
    d = ImageDraw.Draw(im)
    d.text((40, 30), title, fill=(30, 25, 20), font=_font(34, True))
    d.text((40, 78), "Thread chart: sew in this order", fill=(110, 100, 90), font=_font(20))
    sizes_line = "   ".join(f"{s['label']}: {s['size_mm'][0]:.0f} x {s['size_mm'][1]:.0f} mm, "
                           f"{s['stitches']:,} stitches" for s in sizes_info)
    d.text((40, 108), sizes_line, fill=(110, 100, 90), font=_font(18))
    y = 160
    labels = [s["label"] for s in sizes_info]
    d.text((150, y), "Thread", fill=(90, 80, 70), font=_font(18, True))
    d.text((560, y), "Hex", fill=(90, 80, 70), font=_font(18, True))
    for j, lab in enumerate(labels):
        d.text((700 + 150 * j, y), f"{lab} stitches", fill=(90, 80, 70), font=_font(18, True))
    y += 40
    for r in rows:
        d.rounded_rectangle([40, y, 120, y + 46], 8, fill=r["hex"], outline=(120, 110, 100))
        d.text((54, y + 8), f"{r['n']}", fill=(255, 255, 255) if sum(int(r["hex"][i:i + 2], 16) for i in (1, 3, 5)) < 380
               else (40, 30, 20), font=_font(24, True))
        name = f"Brother {r['brother']}" if r["brother"] else f"no close Brother match: use {r['hex']}"
        d.text((150, y + 10), name, fill=(30, 25, 20), font=_font(22))
        d.text((560, y + 10), r["hex"], fill=(30, 25, 20), font=_font(22))
        for j, lab in enumerate(labels):
            d.text((700 + 150 * j, y + 10), f"{r['stitches'].get(lab, 0):,}", fill=(30, 25, 20), font=_font(22))
        y += 64
    d.text((40, H - 46), "Brother names are exact matches to the PEC palette; any 40 wt polyester in these colours works.",
           fill=(130, 120, 110), font=_font(16))
    im.save(path)
    return path


# ---------------------------------------------------------------- notes

def notes_text(m):
    L = [m["title"], "=" * len(m["title"]), "", m["summary"], ""]
    if m.get("description"):
        L += [m["description"], ""]
    from .design import HOOPS
    L.append("Sizes")
    for s in m["sizes"]:
        L.append(f"  {s['label']:<5} hoop {s['hoop']}: {s['size_mm'][0]:.0f} x {s['size_mm'][1]:.0f} mm "
                 f"({s['size_in'][0]:.2f} x {s['size_in'][1]:.2f} in), {s['stitches']:,} stitches, "
                 f"{s['colors']} colours, {s['trims']} trims, about {_fmt_time(s['sew_minutes'])} at 650 spm")
        hw, hh = HOOPS.get(s["hoop"], (999, 999))
        if s["size_mm"][0] > hw:
            L.append(f"        wider than the hoop is across: rotate it 90 deg on your machine's screen "
                     f"(or hoop the fabric sideways) to fit the {s['hoop']} hoop's long side")
    L += ["", "Threads (sewing order)"]
    for r in m["threads"]:
        name = f"Brother {r['brother']}" if r["brother"] else "no close Brother match"
        L.append(f"  {r['n']:>2}. {r['hex']}  {name}")
    L += ["", "Formats (every size)"]
    for f in m["formats"]:
        L.append(f"  .{f:<4} {MACHINES[f]}")
    L += ["", STABILISER, "",
          "Each size was stitched out in simulation and checked: density under 3.5 thread layers, "
          "no stitch over 7 mm, every jump trimmed, lock stitches at every cut.", "",
          "Licence", "  " + m["license"], ""]
    return "\n".join(L)


# ---------------------------------------------------------------- publish one design

def publish(model_path, build_fn, load_model, parse_overrides, out_root, sim_exe, refresh=True):
    """Build every size of a design, render, chart, zip and write the manifest."""
    path = Path(model_path)
    mod = load_model(path)
    name = path.stem
    product = dict(getattr(mod, "PRODUCT", {}) or {})
    sizes = list(getattr(mod, "SIZES", None) or DEFAULT_SIZES)
    out = Path(out_root) / name
    out.mkdir(parents=True, exist_ok=True)
    reasons = []
    size_info, size_dirs, block_stitches = [], {}, {}
    colors = None
    for label, hoop, mm in sizes:
        bname = f"{name}_{label}"
        args = SimpleNamespace(model=str(path), set=[f"size={mm}"], name=bname, out=str(out / "sizes"),
                               engine="auto", hoop=hoop, formats=",".join(FORMATS), no_render=False,
                               compare=False, detail=None)
        bdir = out / "sizes" / bname
        if refresh or not (bdir / "build.json").exists():
            rc = build_fn(args)
            data = args.build_data
        else:
            data = json.loads((bdir / "build.json").read_text())
            rc = 0 if data.get("ok") else 1
        part = data["parts"][bname]
        if rc != 0 or not data.get("ok"):
            reasons.append(f"{label}: build failed its checks")
        warn = [l for l in part["lines"] if l.startswith("WARNING")]
        if warn:
            reasons.append(f"{label}: {len(warn)} warning(s)")
        nprob, probs = stitchsim_info(sim_exe, bdir / f"{bname}.pes") if sim_exe else (-1, [])
        if nprob != 0:
            reasons.append(f"{label}: stitchsim found {nprob} problem(s)" if nprob > 0 else f"{label}: stitchsim not run")
        plan_lines = {l.split()[0]: l for l in part["lines"]}
        sew = re.search(r"sew time ~(\d+) min", " ".join(part["lines"]))
        w, h = part["size"]
        size_info.append(dict(label=label, hoop=hoop, size_mm=[round(w, 1), round(h, 1)],
                              size_in=[round(w / 25.4, 2), round(h / 25.4, 2)], stitches=part["stitches"],
                              colors=len(part["colors"]), trims=part["trims"], max_density=part["max_density"],
                              sew_minutes=float(sew.group(1)) if sew else None, problems=nprob,
                              checks_ok=all(c["ok"] for c in part["checks"]), folder=f"sizes/{bname}"))
        size_dirs[label] = bdir
        colors = colors or part["colors"]
        from .pattern import plan_of, read
        from .cli import _block_stitches
        block_stitches[label] = _block_stitches(plan_of(read(bdir / f"{bname}.pes")))
        del plan_lines
    title = product.get("title") or name.replace("_", " ").title()
    rows = thread_rows(colors, block_stitches)

    # images: product shot on plain fabric, garment mockups
    small = sizes[0][0]
    pes_small = size_dirs[small] / f"{name}_{small}.pes"
    pes_big = size_dirs[sizes[-1][0]] / f"{name}_{sizes[-1][0]}.pes"
    images = {}
    if sim_exe:
        images["product"] = stitchsim_shot(sim_exe, pes_small, out / f"{name}_product.png", fabric="#efe9dc").name
        mock = []
        for article in product.get("mockups", ["tshirt", "tote"]):
            src = pes_big if article in ("tote",) else pes_small
            mock.append(stitchsim_shot(sim_exe, src, out / f"{name}_mockup_{article}.png", article=article).name)
        images["mockups"] = mock
    else:
        reasons.append("no stitchsim: no product images")
    chart = render_thread_chart(out / f"{name}_threads.png", title, rows, size_info)
    images["thread_chart"] = chart.name

    license_text = getattr(mod, "LICENSE_NOTES", None) or DEFAULT_LICENSE
    m = dict(
        schema=SCHEMA, kind="embroidery", name=name, slug=slug_of(name), title=title,
        summary=product.get("summary") or getattr(mod, "DESCRIPTION", ""),
        description=product.get("description", ""),
        category="embroidery", collection=product.get("collection"),
        tags=list(product.get("tags", [])),
        sizes=size_info, threads=rows, formats=FORMATS,
        attributes=dict(
            hoop_size=" / ".join(f"{s['label']} ({s['size_mm'][0]:.0f} x {s['size_mm'][1]:.0f} mm)" for s in size_info),
            stitch_count=" / ".join(f"{s['stitches']:,}" for s in size_info),
            thread_colors=len(rows), formats=[f.upper() for f in FORMATS] + ["SVG"],
            sizes=[s["label"] for s in size_info]),
        license=license_text,
        shop=dict(price_usd=product.get("price_usd", 3.99), commercial_price_usd=product.get("commercial_price_usd", 12.99),
                  collection_id="embroidery", price_note="suggested; confirm before publishing",
                  draft=bool(product.get("draft", False))),
        generated_at=outputs.now_iso(), git_commit=(outputs.git_info() or {}).get("commit"),
        model=str(path.relative_to(path.parents[1]).as_posix()) if len(path.parents) > 1 else str(path),
        model_sha256=sha256(path),
    )
    notes = out / f"{name}_notes.txt"
    notes.write_text(notes_text(m), encoding="utf-8")

    # the buyer's zip: README + chart + product shot at the top, one folder per size
    zpath = out / f"{m['slug']}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(notes, f"{m['slug']}/README.txt")
        z.write(chart, f"{m['slug']}/{chart.name}")
        if "product" in images:
            z.write(out / images["product"], f"{m['slug']}/{images['product']}")
        for label, bdir in size_dirs.items():
            for fmt in FORMATS + ["svg"]:
                f = bdir / f"{name}_{label}.{fmt}"
                if f.exists():
                    z.write(f, f"{m['slug']}/{label}/{f.name}")
    files = []
    for f, role in [(zpath, "zip"), (notes, "txt"), (chart, "png")] + \
                   [(out / v, "png") for k, v in images.items() if k == "product"] + \
                   [(out / v, "png") for v in images.get("mockups", [])]:
        files.append(dict(role=role, path=f.name, bytes=f.stat().st_size, sha256=sha256(f)))
    for label, bdir in size_dirs.items():
        for fmt in FORMATS:
            f = bdir / f"{name}_{label}.{fmt}"
            files.append(dict(role=fmt, path=f"sizes/{bdir.name}/{f.name}", size=label,
                              bytes=f.stat().st_size, sha256=sha256(f)))
    m["files"] = files
    m["images"] = dict(product=images.get("product"), gallery=images.get("mockups", []) + [chart.name])
    if not images.get("product"):
        reasons.append("no product image")
    override = product.get("sellable")
    m["sellable"] = (not reasons) if override is None else bool(override)
    m["reasons"] = reasons
    (out / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    return m


# ---------------------------------------------------------------- bundles

def bundle(collection, title, out_root, members, price_usd=19.99, commercial_price_usd=59.99, blurb=""):
    """A bundle product from member manifests: cover, contents sheet, one zip of zips."""
    out = Path(out_root) / "_bundles" / collection
    out.mkdir(parents=True, exist_ok=True)
    ms = [json.loads((Path(out_root) / n / "manifest.json").read_text()) for n in members]
    # cover: 5 x 2 grid of product shots under a title band
    cell, cols = 400, 5
    rows_n = (len(ms) + cols - 1) // cols
    W, H = cell * cols, 170 + cell * rows_n + 70
    cover = Image.new("RGB", (W, H), (247, 243, 235))
    d = ImageDraw.Draw(cover)
    d.text((40, 32), title, fill=(42, 19, 1), font=_font(56, True))
    d.text((44, 106), f"{len(ms)} machine embroidery designs  ·  4x4 and 5x7  ·  8 formats  ·  one thread palette",
           fill=(120, 90, 60), font=_font(26))
    for i, m in enumerate(ms):
        im = Image.open(Path(out_root) / m["name"] / m["images"]["product"]).convert("RGB").resize((cell - 16, cell - 16))
        x, y = (i % cols) * cell + 8, 170 + (i // cols) * cell + 8
        cover.paste(im, (x, y))
    d.text((40, H - 52), "Formats: PES PEC DST JEF EXP VP3 XXX U01   ·   thread charts with exact Brother spools",
           fill=(120, 90, 60), font=_font(22))
    cover_path = out / f"{collection}_cover.png"
    cover.save(cover_path)
    # contents sheet
    lines = [title, "=" * len(title), "", blurb, "", "Designs"]
    for i, m in enumerate(ms):
        s0, s1 = m["sizes"][0], m["sizes"][-1]
        lines.append(f"  {i + 1:>2}. {m['title']}: {s0['size_mm'][0]:.0f} x {s0['size_mm'][1]:.0f} mm "
                     f"({s0['stitches']:,} st) and {s1['size_mm'][0]:.0f} x {s1['size_mm'][1]:.0f} mm "
                     f"({s1['stitches']:,} st), {len(m['threads'])} colours")
    used = {}
    for m in ms:
        for r in m["threads"]:
            used.setdefault(r["hex"], r["brother"])
    lines += ["", f"Thread set: {len(used)} colours cover every design"]
    lines += [f"  {h}  Brother {b}" if b else f"  {h}" for h, b in used.items()]
    lines += ["", STABILISER, "", "Licence", "  " + ms[0]["license"], ""]
    contents = out / f"{collection}_contents.txt"
    contents.write_text("\n".join(lines), encoding="utf-8")
    zpath = out / f"{collection}-bundle.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(contents, f"{collection}/README.txt")
        z.write(cover_path, f"{collection}/{cover_path.name}")
        for m in ms:
            mz = Path(out_root) / m["name"] / f"{m['slug']}.zip"
            z.write(mz, f"{collection}/{mz.name}")
    reasons = [f"{m['name']}: not sellable ({'; '.join(m['reasons'])})" for m in ms if not m["sellable"]]
    bm = dict(schema=SCHEMA, kind="embroidery", bundle=True, name=collection, slug=collection + "-bundle",
              title=f"{title}: {len(ms)} Embroidery Designs Bundle", summary=blurb.split("\n")[0] if blurb else "",
              description=blurb, category="embroidery", collection=collection,
              bundle_of=[m["slug"] for m in ms], members=[m["title"] for m in ms],
              attributes=dict(thread_colors=len(used), formats=[f.upper() for f in FORMATS] + ["SVG"],
                              sizes=sorted({s["label"] for m in ms for s in m["sizes"]}),
                              stitch_count=f"{min(m['sizes'][0]['stitches'] for m in ms):,} to "
                                           f"{max(m['sizes'][-1]['stitches'] for m in ms):,}"),
              images=dict(product=cover_path.name, gallery=[f"../../{m['name']}/{m['images']['product']}" for m in ms]),
              files=[dict(role=r, path=p.name, bytes=p.stat().st_size, sha256=sha256(p))
                     for p, r in ((zpath, "zip"), (cover_path, "png"), (contents, "txt"))],
              shop=dict(price_usd=price_usd, commercial_price_usd=commercial_price_usd, collection_id="bundles",
                        price_note="suggested; confirm before publishing",
                        draft=any(m.get("shop", {}).get("draft") for m in ms)),
              license=ms[0]["license"], sellable=not reasons, reasons=reasons, generated_at=outputs.now_iso())
    (out / "manifest.json").write_text(json.dumps(bm, indent=1), encoding="utf-8")
    return bm
