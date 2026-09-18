#!/usr/bin/env python3
"""Build one social-share card (Open Graph image) per page.

Usage: python3 scripts/build-og.py

Why this exists
---------------
Every page used to share a single hand-made image: dark green, the retired
"Wellness Innovation Insights" line, and a "图片由AI生成" watermark baked
into the corner. It was both off-brand and off-message, and it carried no
information about the page being shared.

This renders 1200x630 cards from the brand kit instead: ink background,
the S-loop mark, and the page's own <h1>, so a shared article link says
what it is. Output lands in images/og/<name>.png and build-blog.py points
og:image at it.

Run it AFTER build-blog.py and sync-chrome.py: titles come from the built
HTML, so re-run whenever copy changes.

The mark and wordmark are pasted from images/brand/*-dark.png (the tone
built for dark backgrounds) rather than redrawn, so the card cannot drift
from the logo.
"""

import glob
import html
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from content.taxonomy import ARTICLE_META, PILLARS  # noqa: E402

W, H = 1200, 630
PAD = 84
INK = (18, 16, 14)
IVORY = (247, 244, 238)
GOLD = (176, 141, 87)
MUTED = (138, 130, 121)

BRAND = os.path.join(BASE_DIR, "images", "brand")
OUT = os.path.join(BASE_DIR, "images", "og")
FONT_CACHE = "/tmp/suppbridge-inter"

# Footer line: the canonical identity. Kept identical on every card so a
# shared link always says what the company does, not just what the page is.
TAGLINE = "China Supplement Product & Supply Chain Advisor"


def font(weight, size):
    """Inter static instance at `weight`, cached under /tmp.

    The site loads Inter from Google Fonts; the cards must match it, and
    PIL cannot read a variable font at a chosen weight, so the variable
    font is instanced once with fontTools and reused.
    """
    os.makedirs(FONT_CACHE, exist_ok=True)
    path = os.path.join(FONT_CACHE, f"Inter-{weight}.ttf")
    if not os.path.exists(path):
        var = "/tmp/inter-var.ttf"
        if not os.path.exists(var):
            import urllib.request
            url = ("https://github.com/google/fonts/raw/main/ofl/inter/"
                   "Inter%5Bopsz%2Cwght%5D.ttf")
            urllib.request.urlretrieve(url, var)
        from fontTools import ttLib
        from fontTools.varLib import instancer
        f = ttLib.TTFont(var)
        instancer.instantiateVariableFont(f, {"wght": weight, "opsz": 28},
                                          inplace=True)
        f.save(path)
    return ImageFont.truetype(path, size)


def text_width(draw, s, f, tracking=0):
    if not tracking:
        return draw.textlength(s, font=f)
    return sum(draw.textlength(c, font=f) + tracking for c in s) - tracking


def draw_tracked(draw, xy, s, f, fill, tracking):
    """Letter-spaced text, character by character.

    PIL has no letter-spacing, and the eyebrow style depends on it.
    """
    x, y = xy
    for c in s:
        draw.text((x, y), c, font=f, fill=fill)
        x += draw.textlength(c, font=f) + tracking


def wrap(draw, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_width(draw, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def paste(img, path, height, xy):
    art = Image.open(path).convert("RGBA")
    ratio = height / art.height
    art = art.resize((max(1, round(art.width * ratio)), height), Image.LANCZOS)
    img.alpha_composite(art, xy)
    return art.width


def card(title, eyebrow, out_name):
    """Compose one card: lockup, section eyebrow, headline, footer rule.

    The lockup is the full horizontal logo rather than the bare mark, so a
    card always carries the name — a shared link should not rely on the
    reader already knowing the company.
    """
    img = Image.new("RGBA", (W, H), INK + (255,))
    d = ImageDraw.Draw(img)

    # Header lockup, top-left.
    paste(img, os.path.join(BRAND, "logo-horizontal-dark.png"), 70,
          (PAD, PAD - 4))

    # Section eyebrow, on its own line under the lockup.
    ey = PAD + 70 + 34
    draw_tracked(d, (PAD, ey), eyebrow.upper(), font(600, 23), GOLD, 3.0)

    # Headline. Capped at 66px so three lines always clear the footer rule,
    # then shrunk further until the longest line fits the column.
    max_w, band_top, band_h = W - PAD * 2, ey + 46, 246
    for size in range(66, 33, -2):
        f = font(600, size)
        lines = wrap(d, title, f, max_w)
        leading = round(size * 1.2)
        if len(lines) <= 3 and len(lines) * leading <= band_h:
            break
    block_h = leading * len(lines)
    top = band_top + (band_h - block_h) // 2
    for i, line in enumerate(lines):
        d.text((PAD, top + i * leading), line, font=f, fill=IVORY)

    # Footer: hairline, then identity left and domain right.
    rule_y = H - 118
    d.line([(PAD, rule_y), (W - PAD, rule_y)], fill=(58, 51, 43), width=1)
    d.text((PAD, rule_y + 32), TAGLINE, font=font(500, 25), fill=MUTED)
    dom = "suppbridge.com"
    df = font(600, 25)
    d.text((W - PAD - d.textlength(dom, font=df), rule_y + 32), dom,
           font=df, fill=GOLD)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, out_name + ".png")
    img.convert("RGB").save(path, optimize=True)
    return path


def h1_of(rel):
    """The page's own headline — the most honest title for a share card."""
    path = os.path.join(BASE_DIR, rel)
    if not os.path.exists(path):
        return None
    src = open(path, encoding="utf-8").read()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    if not m:
        return None
    txt = re.sub(r"<[^>]+>", "", m.group(1))
    return html.unescape(re.sub(r"\s+", " ", txt)).strip()


def main():
    pillar_by_dir = {p["url"].strip("/"): k for k, p in PILLARS.items()}
    jobs = []

    # Homepage, insights index, and the hand-authored pages.
    manual = {
        # Homepage: the eyebrow carries the disciplines instead of repeating
        # the name that the lockup above it already spells out.
        "index.html": ("home", "Product Development · Sourcing · Manufacturing",
                       "China Supplement Product & Supply Chain Advisor"),
        "blog/index.html": ("insights", "Insights", None),
        "china-supplement-sourcing.html": ("china-supplement-sourcing",
                                           "Sourcing", None),
        "product-formats.html": ("product-formats", "Formats", None),
        "regulatory/index.html": ("regulatory", "Regulatory", None),
        "thanks.html": ("thanks", "SuppBridge", None),
    }
    done = set()
    for rel, (name, eyebrow, fixed_title) in manual.items():
        title = fixed_title or h1_of(rel)
        if title:
            jobs.append((rel, name, eyebrow, title))
            done.add(os.path.dirname(rel) or rel)

    # Pillar pages: section label comes from the taxonomy, not from guesswork.
    # regulatory/ is hand-authored and already mapped above, so skip any
    # directory that has been claimed.
    for rel in sorted(glob.glob(os.path.join(BASE_DIR, "*", "index.html"))):
        rel = os.path.relpath(rel, BASE_DIR)
        if rel.startswith(("blog/", ".")) or os.path.dirname(rel) in done:
            continue
        key = pillar_by_dir.get(os.path.dirname(rel))
        eyebrow = PILLARS[key]["nav_title"] if key else "SuppBridge"
        title = h1_of(rel)
        if title:
            jobs.append((rel, os.path.dirname(rel), eyebrow, title))

    # Articles.
    for rel in sorted(glob.glob(os.path.join(BASE_DIR, "blog", "*.html"))):
        rel = os.path.relpath(rel, BASE_DIR)
        slug = os.path.basename(rel)[:-5]
        if slug == "index":
            continue
        cluster = (ARTICLE_META.get(slug) or {}).get("cluster")
        eyebrow = PILLARS[cluster]["nav_title"] if cluster in PILLARS else "Insights"
        title = h1_of(rel) or (ARTICLE_META.get(slug) or {}).get("title", slug)
        jobs.append((rel, slug, eyebrow, title))

    for rel, name, eyebrow, title in jobs:
        path = card(title, eyebrow, name)
        print(f"  {name:<32} {os.path.getsize(path) // 1024:>4} KB  {title[:56]}")

    # A generic card for places with no page of their own: email signature,
    # LinkedIn company page, decks.
    path = card("Supplement Product Development, Sourcing & Supply Chain",
                "SuppBridge", "default")
    print(f"  {'default':<32} {os.path.getsize(path) // 1024:>4} KB  (generic)")
    print(f"\n{len(jobs) + 1} cards -> images/og/")


if __name__ == "__main__":
    main()
