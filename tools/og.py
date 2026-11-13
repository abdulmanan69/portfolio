"""
Open Graph cards (1200x630 PNG) for generated pages, in the same style as the
blog covers from tools/make-cover.py.

Needs Pillow (already required by make-cover.py) and three OFL fonts. The
fonts are looked up in $COVER_FONTS, then .fonts/, then .cache/fonts/, and
downloaded from github.com/google/fonts into .cache/fonts/ if none of those
has them. Cards are only redrawn when their text changes.
"""

import hashlib
import json
import os
import urllib.request

from common import ROOT, BuildError

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:                                   # pragma: no cover
    raise BuildError("Pillow is required for Open Graph images: pip install pillow")

VERSION = "1"                  # bump to force every card to redraw
W, H, SS = 1200, 630, 2
PAPER, INK, SOFT = (250, 248, 245), (22, 21, 26), (75, 74, 82)
CORAL, LINE, MUTED = (255, 90, 60), (230, 226, 219), (138, 135, 128)
BLUSH_TR, BLUSH_BL = (250, 234, 229), (250, 238, 233)
MARGIN, RIGHT = 80, 1120
HAIRLINE_Y, NAME_BASELINE, MONO_BASELINE = 520, 576, 566

GOOGLE_FONTS = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONTS = {
    "fraunces.ttf": "fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf",
    "inter.ttf": "inter/Inter%5Bopsz,wght%5D.ttf",
    "jetbrains.ttf": "jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}
MANIFEST = os.path.join(ROOT, ".cache", "og.json")


def _font_dir():
    for d in (os.environ.get("COVER_FONTS"), os.path.join(ROOT, ".fonts"),
              os.path.join(ROOT, ".cache", "fonts")):
        if d and all(os.path.exists(os.path.join(d, f)) for f in FONTS):
            return d
    d = os.path.join(ROOT, ".cache", "fonts")
    os.makedirs(d, exist_ok=True)
    for name, path in FONTS.items():
        print("  downloading font %s" % name)
        try:
            with urllib.request.urlopen(GOOGLE_FONTS + path, timeout=60) as r:
                data = r.read()
        except OSError as err:
            raise BuildError("could not download %s for OG images (%s). Put fraunces.ttf, "
                             "inter.ttf and jetbrains.ttf in .fonts/ by hand." % (name, err))
        with open(os.path.join(d, name), "wb") as f:
            f.write(data)
    return d


_fonts = {}


def _font(name, axes, size):
    """Variable font at fixed axes. Axis order is the font's own:
    fraunces [opsz, wght, SOFT, WONK], inter [opsz, wght], jetbrains [wght]."""
    key = (name, tuple(axes), size)
    if key not in _fonts:
        f = ImageFont.truetype(os.path.join(_font_dir(), name), size)
        f.set_variation_by_axes(axes)
        _fonts[key] = f
    return _fonts[key]


def _printable(text):
    """Drop characters the fonts don't cover (emoji, non-Latin scripts)."""
    text = "".join(c for c in (text or "") if ord(c) < 0x250 or c in "—–…·’‘“”•")
    return " ".join(text.split())


def _wrap(text, f, width, max_lines):
    lines, words = [], text.split()
    while words and len(lines) < max_lines:
        line = words.pop(0)
        while words and f.getlength(line + " " + words[0]) <= width:
            line += " " + words.pop(0)
        lines.append(line)
    if words:                                          # ran out of lines: ellipsis
        last = lines[-1]
        while last and f.getlength(last + "…") > width:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        lines[-1] = last.rstrip(",;:—– ") + "…"
    return lines


def _tracked(d, xy, text, f, fill, spacing):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += f.getlength(ch) + spacing


def _draw(label, title, subtitle):
    img = Image.new("RGB", (W * SS, H * SS), PAPER)
    d = ImageDraw.Draw(img)
    for cx, cy, r, colour in ((1131, -16, 387, BLUSH_TR), (188, 600, 232, BLUSH_BL)):
        d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=colour)
    img = img.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(img)

    f_label = _font("inter.ttf", [32, 600], 19)
    d.rectangle([MARGIN, 84, 140, 86], fill=CORAL)
    _tracked(d, (156, 92), _printable(label).upper(), f_label, CORAL, 1.2)

    size, lines = 84, []
    while size >= 52:
        f_title = _font("fraunces.ttf", [72, 700, 0, 0], size)
        lines = _wrap(_printable(title), f_title, RIGHT - MARGIN, 3)
        if len(lines) <= 2 or (size <= 64 and len(lines) <= 3):
            break
        size -= 6
    pitch = int(size * 1.08)
    y = 150 + size
    for line in lines:
        d.text((MARGIN, y), line, font=f_title, fill=INK, anchor="ls")
        y += pitch

    sub = _printable(subtitle)
    if sub:
        f_sub = _font("inter.ttf", [32, 400], 30)
        y += 4
        room = max(1, min(3, (HAIRLINE_Y - 30 - y) // 42 + 1))
        for line in _wrap(sub, f_sub, RIGHT - MARGIN, room):
            d.text((MARGIN, y), line, font=f_sub, fill=SOFT, anchor="ls")
            y += 42

    d.rectangle([MARGIN, HAIRLINE_Y, RIGHT, HAIRLINE_Y], fill=LINE)
    d.text((MARGIN, NAME_BASELINE), "Abdul Manan", font=_font("inter.ttf", [32, 500], 30),
           fill=INK, anchor="ls")
    d.text((RIGHT, MONO_BASELINE), "abdulmanan.tech", font=_font("jetbrains.ttf", [400], 22),
           fill=MUTED, anchor="rs")
    return img.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


_manifest = None


def _load_manifest():
    global _manifest
    if _manifest is None:
        _manifest = {}
        if os.path.exists(MANIFEST):
            with open(MANIFEST, encoding="utf-8") as f:
                _manifest = json.load(f)
    return _manifest


def save_manifest():
    if _manifest is not None:
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(_manifest, f, indent=1, sort_keys=True)


def card(rel_path, label, title, subtitle=""):
    """Make sure /<rel_path> holds a card for this text. Returns (url_path, w, h)."""
    manifest = _load_manifest()
    digest = hashlib.sha1("\0".join([VERSION, label, title, subtitle]).encode("utf-8")).hexdigest()
    out = os.path.join(ROOT, *rel_path.split("/"))
    if manifest.get(rel_path) != digest or not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        _draw(label, title, subtitle).save(out, optimize=True)
        print("  drew %s" % rel_path)
        manifest[rel_path] = digest
    return ("/" + rel_path, W, H)


def prune(folder, keep):
    """Delete og/<folder>/*.png cards whose slug isn't in keep."""
    base = os.path.join(ROOT, "og", folder)
    if not os.path.isdir(base):
        return
    for name in sorted(os.listdir(base)):
        if name.endswith(".png") and name[:-4] not in keep:
            os.remove(os.path.join(base, name))
            print("  removed stale og/%s/%s" % (folder, name))
