#!/usr/bin/env python3
"""Optimize site imagery.

Converts the oversized source PNGs into reasonably sized WebP siblings and
rewrites the Open Graph image to the 1200x630 standard.

Usage: python3 scripts/optimize-images.py

The original PNG/JPG files are deliberately KEPT — pages use <picture> with the
WebP as the preferred source and the original as the fallback.
"""

import os
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install Pillow")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# source file -> (target width, target height or None=keep ratio, webp quality)
JOBS = [
    # Format tiles render at ~96px tall in a 4-col grid -> 480px is >2x for retina.
    ("images/formats/capsules.png",                 480, 480, 82),
    ("images/formats/dual-chamber-capsules.png",    480, 480, 82),
    ("images/formats/functional-shots.png",         480, 480, 82),
    ("images/formats/gummies.png",                  480, 480, 82),
    ("images/formats/jelly-systems.png",            480, 480, 82),
    ("images/formats/liquid-solid-systems.png",     480, 480, 82),
    ("images/formats/multi-phase-systems.png",      480, 480, 82),
    ("images/formats/oral-films.png",               480, 480, 82),
    ("images/formats/powders.png",                  480, 480, 82),
    ("images/formats/sachets.png",                  480, 480, 82),
    ("images/formats/stick-packs.png",              480, 480, 82),
    ("images/formats/sustained-release-pellets.png", 480, 480, 82),
    # Founder portrait renders at max ~420px wide in the split layout.
    ("images/founder.jpg",                          900, None, 80),
    # Open Graph cards are not listed here: scripts/build-og.py renders them
    # at exactly 1200x630, and social scrapers do not read WebP siblings.
]


def kb(path):
    return os.path.getsize(path) / 1024


def main():
    total_before = total_after = 0
    print(f"{'source':<46}{'webp':>12}{'orig':>10}{'saved':>9}")
    print("-" * 77)

    for rel, w, h, q in JOBS:
        src = os.path.join(BASE_DIR, rel)
        if not os.path.exists(src):
            print(f"  ! missing {rel}")
            continue

        before = kb(src)
        with Image.open(src) as im:
            im = im.convert("RGB" if not im.has_transparency_data else "RGBA") \
                if im.mode not in ("RGB", "RGBA") else im

            # Resize (crop-to-fill when an exact box is requested)
            if w:
                if h:
                    ratio = max(w / im.width, h / im.height)
                    im = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.LANCZOS)
                    left = (im.width - w) // 2
                    top = (im.height - h) // 2
                    im = im.crop((left, top, left + w, top + h))
                elif im.width > w:
                    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)

            # WebP sibling, kept alongside the PNG/JPG for <picture> use.
            out = os.path.splitext(src)[0] + ".webp"
            im.save(out, "WEBP", quality=q, method=6)

        after = kb(out)
        total_before += before
        total_after += after
        print(f"{rel:<46}{after:>11.0f}K{before:>9.0f}K{100 - after / before * 100:>8.0f}%")

    print("-" * 77)
    print(f"{'TOTAL':<46}{total_after:>11.0f}K{total_before:>9.0f}K"
          f"{100 - total_after / total_before * 100:>8.0f}%")
    print("\nOriginal PNG/JPG sources kept as <picture> fallbacks.")


if __name__ == "__main__":
    main()
