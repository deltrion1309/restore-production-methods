#!/usr/bin/env python3
"""
Draw the Workshop thumbnail candidates for Restore Production Methods.

Paradox mods use a 512x512 thumbnail.png in the mod root. Everything here is
drawn from scratch - no game art, no Paradox marks - so the result is ours to
publish.

    python dev/make_thumbnail.py --out-dir build/thumbnails

Pick one and copy it to thumbnail.png in the repository root.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 512

PARCHMENT = (232, 221, 196)
PARCHMENT_DARK = (198, 182, 150)
INK = (38, 32, 26)
INK_SOFT = (78, 66, 54)
RULE_BLUE = (126, 140, 156)
OXBLOOD = (140, 47, 38)
BRASS = (185, 139, 58)
BRASS_DARK = (122, 88, 33)
SLATE = (32, 36, 42)
SLATE_LIGHT = (58, 65, 74)
GREEN = (74, 107, 70)

SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
BASKERVILLE = "/usr/share/fonts/truetype/baskerville/GFSBaskerville.otf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def centre_text(draw, y, text, fnt, fill, spacing=0):
    """Draw text centred horizontally, optionally letter-spaced."""
    if not spacing:
        w = draw.textlength(text, font=fnt)
        draw.text(((SIZE - w) / 2, y), text, font=fnt, fill=fill)
        return
    widths = [draw.textlength(c, font=fnt) for c in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = (SIZE - total) / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=fnt, fill=fill)
        x += w + spacing


def paper_background(seed: int = 7) -> Image.Image:
    """Aged paper: warm base, blotchy fibre, darkened edges."""
    rng = random.Random(seed)
    img = Image.new("RGB", (SIZE, SIZE), PARCHMENT)

    noise = Image.new("L", (SIZE // 2, SIZE // 2))
    noise.putdata([rng.randint(96, 160) for _ in range(noise.width * noise.height)])
    noise = noise.resize((SIZE, SIZE), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    stain = Image.new("RGB", (SIZE, SIZE), PARCHMENT_DARK)
    img = Image.composite(img, stain, noise.point(lambda v: 255 if v > 126 else 90))

    # vignette
    vign = Image.new("L", (SIZE, SIZE), 0)
    vd = ImageDraw.Draw(vign)
    for i in range(70):
        k = i * 3
        vd.rectangle([k, k, SIZE - k, SIZE - k], outline=255 - int(255 * i / 70))
    vign = vign.filter(ImageFilter.GaussianBlur(28))
    img = Image.composite(Image.new("RGB", (SIZE, SIZE), PARCHMENT_DARK), img, vign.point(lambda v: 255 - v))
    return img


def slate_background(seed: int = 11) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (SIZE, SIZE), SLATE)
    d = ImageDraw.Draw(img)
    for i in range(SIZE):
        t = i / SIZE
        shade = tuple(int(SLATE[c] + (SLATE_LIGHT[c] - SLATE[c]) * (1 - t) * 0.8) for c in range(3))
        d.line([(0, i), (SIZE, i)], fill=shade)
    grain = Image.new("L", (SIZE, SIZE))
    grain.putdata([rng.randint(0, 22) for _ in range(SIZE * SIZE)])
    img = Image.blend(img, Image.merge("RGB", (grain, grain, grain)), 0.10)
    return img


def gear(draw, cx, cy, r_outer, r_inner, teeth, fill, outline=None, width=3, phase=0.0):
    pts = []
    for i in range(teeth * 2):
        ang = phase + i * math.pi / teeth
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=fill, outline=outline)
    if outline:
        draw.line(pts + [pts[0]], fill=outline, width=width)
    hub = r_inner * 0.42
    draw.ellipse([cx - hub, cy - hub, cx + hub, cy + hub], fill=outline or fill)
    bore = r_inner * 0.20
    draw.ellipse([cx - bore, cy - bore, cx + bore, cy + bore], fill=(0, 0, 0, 0) if fill is None else PARCHMENT)


# --------------------------------------------------------------------------- #
# Variant A - the ledger
# --------------------------------------------------------------------------- #
def variant_ledger() -> Image.Image:
    img = paper_background()
    d = ImageDraw.Draw(img)

    # title block, clear of everything below it
    centre_text(d, 40, "RESTORE", font(SERIF_BOLD, 64), INK, spacing=4)
    centre_text(d, 114, "PRODUCTION  METHODS", font(SERIF_BOLD, 24), OXBLOOD, spacing=3)

    # header rules
    d.line([(44, 158), (SIZE - 44, 158)], fill=INK, width=3)
    d.line([(44, 166), (SIZE - 44, 166)], fill=INK, width=1)

    # ruled ledger body, stopping well above the footer
    rows = [
        ("Tooling Workshops", True),
        ("Textile Mills", True),
        ("Iron Mines", False),
        ("Barracks", True),
    ]
    top, step = 196, 56
    for i in range(len(rows) + 1):
        y = top + i * step + 34
        d.line([(44, y), (SIZE - 44, y)], fill=RULE_BLUE, width=1)
    d.line([(104, 170), (104, top + len(rows) * step + 34)], fill=OXBLOOD, width=2)

    small = font(SERIF, 23)
    for i, (label, restored) in enumerate(rows):
        y = top + i * step
        d.text((120, y), label, font=small, fill=INK_SOFT)
        if restored:
            w = d.textlength(label, font=small)
            d.line([(117, y + 15), (122 + w, y + 15)], fill=OXBLOOD, width=2)
            d.line([(SIZE - 106, y + 16), (SIZE - 97, y + 25)], fill=GREEN, width=5)
            d.line([(SIZE - 97, y + 25), (SIZE - 78, y + 3)], fill=GREEN, width=5)

    # footer, on clean paper
    d.line([(44, 452), (SIZE - 44, 452)], fill=INK, width=2)
    centre_text(d, 464, "after the rebellion, put the ledgers right", font(SERIF, 20), INK_SOFT)
    return img


# --------------------------------------------------------------------------- #
# Variant B - the machine
# --------------------------------------------------------------------------- #
def variant_gears() -> Image.Image:
    img = slate_background()
    d = ImageDraw.Draw(img)

    gear(d, 212, 208, 112, 87, 12, BRASS_DARK, outline=BRASS, width=4, phase=0.0)
    gear(d, 352, 288, 84, 64, 10, (96, 44, 38), outline=OXBLOOD, width=4, phase=0.26)

    # restore arrow sweeping back over the machine, clear of both gears
    pale = (232, 221, 196)
    d.arc([66, 82, 438, 426], start=198, end=14, fill=pale, width=11)
    d.polygon([(58, 198), (108, 170), (96, 226)], fill=pale)

    # title plate
    d.rectangle([0, 392, SIZE, SIZE], fill=(18, 21, 25))
    d.line([(0, 392), (SIZE, 392)], fill=BRASS, width=3)
    centre_text(d, 412, "RESTORE", font(SERIF_BOLD, 50), (240, 231, 210), spacing=6)
    centre_text(d, 472, "PRODUCTION  METHODS", font(SERIF_BOLD, 22), BRASS, spacing=3)
    return img


# --------------------------------------------------------------------------- #
# Variant C - the states
# --------------------------------------------------------------------------- #
def variant_states() -> Image.Image:
    img = paper_background(seed=3)
    d = ImageDraw.Draw(img)

    centre_text(d, 40, "RESTORE", font(SERIF_BOLD, 64), INK, spacing=4)
    centre_text(d, 114, "PRODUCTION  METHODS", font(SERIF_BOLD, 24), OXBLOOD, spacing=3)
    d.line([(44, 158), (SIZE - 44, 158)], fill=INK, width=3)
    d.line([(44, 166), (SIZE - 44, 166)], fill=INK, width=1)

    cols, rows = 4, 3
    gap = 14
    top, bottom = 192, 436
    cell = (bottom - top - gap * (rows - 1)) // rows
    pad = (SIZE - cols * cell - gap * (cols - 1)) // 2
    changed = {(0, 1), (1, 0), (2, 2), (3, 1), (1, 2)}
    restored = {(1, 0), (2, 2), (3, 1)}
    for r in range(rows):
        for c in range(cols):
            x0 = pad + c * (cell + gap)
            y0 = top + r * (cell + gap)
            rect = [x0, y0, x0 + cell, y0 + cell]
            if (c, r) in restored:
                d.rectangle(rect, fill=GREEN, outline=INK, width=2)
                cx, cy = x0 + cell / 2, y0 + cell / 2
                d.line([(cx - 13, cy + 1), (cx - 3, cy + 11)], fill=PARCHMENT, width=5)
                d.line([(cx - 3, cy + 11), (cx + 14, cy - 11)], fill=PARCHMENT, width=5)
            elif (c, r) in changed:
                d.rectangle(rect, fill=OXBLOOD, outline=INK, width=2)
            else:
                d.rectangle(rect, fill=PARCHMENT_DARK, outline=INK_SOFT, width=2)

    d.line([(44, 452), (SIZE - 44, 452)], fill=INK, width=2)
    centre_text(d, 464, "undo what the rebels rearranged", font(SERIF, 20), INK_SOFT)
    return img


VARIANTS = {
    "ledger": variant_ledger,
    "gears": variant_gears,
    "states": variant_states,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default="build/thumbnails")
    ap.add_argument("--only", choices=sorted(VARIANTS), help="draw just one variant")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    names = [args.only] if args.only else sorted(VARIANTS)
    for name in names:
        img = VARIANTS[name]()
        path = out / f"thumbnail-{name}.png"
        img.save(path, "PNG", optimize=True)
        print(f"{path}  {img.size[0]}x{img.size[1]}  {path.stat().st_size / 1024:.0f} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
