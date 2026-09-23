#!/usr/bin/env python3
"""
Cover-image generator for blog posts — 1200x675 PNGs in the site's own style.

    python tools/make-cover.py <slug> "Title text" [LABEL]

Writes posts/images/<slug>.png and nothing else. Geometry and colours are
measured from the original covers, so new posts sit next to old ones without a
visible seam.

Fonts are not committed. Download the three variable fonts once into .fonts/
(or point the COVER_FONTS environment variable at them):

    fraunces.ttf    github.com/google/fonts/ofl/fraunces
    inter.ttf       github.com/google/fonts/ofl/inter
    jetbrains.ttf   github.com/google/fonts/ofl/jetbrainsmono
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.environ.get("COVER_FONTS", os.path.join(ROOT, ".fonts"))

W, H = 1200, 675
PAPER = (250, 248, 245)
INK = (22, 21, 26)
CORAL = (255, 90, 60)
LINE = (230, 226, 219)
MUTED = (166, 163, 157)
BLUSH_TR = (250, 234, 229)
BLUSH_BL = (250, 238, 233)

MARGIN = 80
RIGHT = 1120
TITLE_TOP = 242            # cap-height top of the first title line
TITLE_PITCH = 92           # baseline to baseline
TITLE_SIZE = 80
RULE_Y, RULE_X2 = 84, 140  # the little coral dash before the label
LABEL_X, LABEL_TOP = 156, 77
HAIRLINE_Y = 555
NAME_BASELINE, MONO_BASELINE = 611, 601
SS = 2                     # supersampling factor, for clean circle edges


def font(name, axes, size):
    f = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    try:
        f.set_variation_by_axes(axes)
    except Exception:                       # static fallback, if someone swaps fonts
        pass
    return f


def wrap(text, f, max_width):
    lines, words = [], text.split()
    while words:
        line = words.pop(0)
        while words and f.getlength(line + " " + words[0]) <= max_width:
            line += " " + words.pop(0)
        lines.append(line)
    return lines


def tracked(draw, xy, text, f, fill, spacing):
    """Draw text with extra letter spacing (variable fonts carry no tracking)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += f.getlength(ch) + spacing


def make(slug, title, label):
    img = Image.new("RGB", (W * SS, H * SS), PAPER)
    d = ImageDraw.Draw(img)
    for cx, cy, r, colour in ((1131, -16, 387, BLUSH_TR), (188, 637, 232, BLUSH_BL)):
        d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=colour)
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)

    f_label = font("inter.ttf", [32, 600], 19)
    f_name = font("inter.ttf", [32, 500], 30)
    f_mono = font("jetbrains.ttf", [400], 22)

    # eyebrow: coral dash + category
    d.rectangle([MARGIN, RULE_Y, RULE_X2, RULE_Y + 2], fill=CORAL)
    label_baseline = LABEL_TOP - f_label.getbbox("H", anchor="ls")[1]
    tracked(d, (LABEL_X, label_baseline), label.upper(), f_label, CORAL, 1.2)

    # title, shrinking a step at a time until it fits three lines
    size, lines, f_title = TITLE_SIZE, None, None
    while size >= 52:
        f_title = font("fraunces.ttf", [72, 700, 0, 0], size)
        lines = wrap(title, f_title, RIGHT - MARGIN)
        if len(lines) <= 3:
            break
        size -= 6
    pitch = TITLE_PITCH if size == TITLE_SIZE else int(size * 1.15)
    baseline = TITLE_TOP - f_title.getbbox("H", anchor="ls")[1]
    if len(lines) == 3:                      # three lines need to start higher
        baseline -= pitch // 2
    for line in lines:
        d.text((MARGIN, baseline), line, font=f_title, fill=INK, anchor="ls")
        baseline += pitch

    # footer
    d.rectangle([MARGIN, HAIRLINE_Y, RIGHT, HAIRLINE_Y], fill=LINE)
    d.text((MARGIN, NAME_BASELINE), "Abdul Manan", font=f_name, fill=INK, anchor="ls")
    d.text((RIGHT, MONO_BASELINE), "abdulmanan.tech", font=f_mono, fill=MUTED, anchor="rs")

    out = os.path.join(ROOT, "posts", "images", "%s.png" % slug)
    img.save(out, optimize=True)
    print("wrote posts/images/%s.png  (%d title lines at %dpx)" % (slug, len(lines), size))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    make(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "BLOG")
