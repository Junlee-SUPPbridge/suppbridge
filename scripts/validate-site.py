#!/usr/bin/env python3
"""Validate the static site: internal links, required SEO metadata, and
language-compliance rules (the claims we must never make).

Usage: python3 scripts/validate-site.py
Exit code 0 = clean, 1 = problems found.
"""

import os
import re
import sys
import glob
from urllib.parse import urlparse, unquote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files we do not validate as pages
SKIP_DIRS = {'.git', 'node_modules', '.workbuddy', 'scripts'}

# Phrases that must never appear (see brief §16).
FORBIDDEN = [
    (r'alibaba is full of', 'unsupported claim about Alibaba'),
    (r'most alibaba suppliers are', 'unsupported claim about Alibaba'),
    (r'are scammers', 'unsupported claim'),
    (r'we guarantee authentic', 'absolute guarantee'),
    (r'guaranteed authentic', 'absolute guarantee'),
    (r'guarantee factory authenticity', 'absolute guarantee'),
    (r'we guarantee.{0,20}quality', 'absolute guarantee'),
    (r'100% verified', 'absolute guarantee'),
    (r'eliminate all sourcing risk', 'absolute guarantee'),
    (r'we eliminate.{0,15}risk', 'absolute guarantee'),
]

# Legacy relative stylesheet path that 404s from /blog/
BAD_CSS_PATHS = ['href="styles/main.css"']


def html_files():
    out = []
    for path in glob.glob(os.path.join(BASE_DIR, '**', '*.html'), recursive=True):
        rel = os.path.relpath(path, BASE_DIR)
        if any(part in SKIP_DIRS for part in rel.split(os.sep)):
            continue
        out.append((rel, path))
    return sorted(out)


def local_target_ok(href, page_rel):
    """Resolve an internal href/src and report whether it exists on disk."""
    path = href.split('#')[0].split('?')[0]
    if not path or path.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
        return True, None
    if path.startswith('//'):
        return True, None
    if path.startswith('/'):
        target = os.path.join(BASE_DIR, path.lstrip('/'))
    else:
        target = os.path.normpath(os.path.join(os.path.dirname(os.path.join(BASE_DIR, page_rel)), path))

    if os.path.isdir(target):
        for index in ('index.html',):
            if os.path.exists(os.path.join(target, index)):
                return True, None
        return False, path
    if os.path.exists(target):
        return True, None
    # allow extension-less directory-style links
    if os.path.exists(target + '.html'):
        return True, None
    return False, path


def main():
    problems = []
    warnings = []

    pages = html_files()
    all_ids = {}

    # Collect ids per page so we can validate #anchors
    for rel, path in pages:
        with open(path, encoding='utf-8') as f:
            html = f.read()
        all_ids[rel] = set(re.findall(r'\sid="([^"]+)"', html))

    for rel, path in pages:
        with open(path, encoding='utf-8') as f:
            html = f.read()

        # ── required SEO metadata ──
        if not re.search(r'<title>[^<]{10,}</title>', html):
            problems.append(f'{rel}: missing or too-short <title>')
        if not re.search(r'<meta name="description" content="[^"]{40,}"', html):
            problems.append(f'{rel}: missing or too-short meta description')
        if 'rel="canonical"' not in html:
            problems.append(f'{rel}: missing canonical')
        if 'og:title' not in html:
            problems.append(f'{rel}: missing og:title')
        if 'viewport' not in html:
            problems.append(f'{rel}: missing viewport meta')

        # ── stylesheet path ──
        for bad in BAD_CSS_PATHS:
            if bad in html:
                problems.append(f'{rel}: relative stylesheet path "{bad}" 404s from subdirectories')

        # ── forbidden claims ──
        low = html.lower()
        for pattern, label in FORBIDDEN:
            if re.search(pattern, low):
                problems.append(f'{rel}: forbidden wording ({label}) matched /{pattern}/')

        # ── broken icons / lost icon system ──
        if 'class="fas ' in html or "class='fas " in html:
            problems.append(f'{rel}: Font Awesome icon classes present but no icon library is loaded')

        # ── hrefs ──
        page_ids = all_ids[rel]
        for m in re.finditer(r'(?:href|src)="([^"]+)"', html):
            raw = m.group(1)
            if raw.startswith(('http://', 'https://')):
                continue
            ok, bad = local_target_ok(raw, rel)
            if not ok:
                problems.append(f'{rel}: broken internal link -> {raw}')
                continue
            # anchor-only or same-page anchor check
            if '#' in raw:
                frag = unquote(raw.split('#', 1)[1])
                if not frag:
                    continue
                base = raw.split('#')[0]
                if base in ('', rel) or base.endswith(rel.split('/')[-1]) or (base == '/' and rel == 'index.html'):
                    if frag not in page_ids:
                        problems.append(f'{rel}: dead anchor #{frag}')
                else:
                    # cross-page anchor: verify target page has the id
                    tgt = None
                    if base.startswith('/'):
                        cand = os.path.join(BASE_DIR, base.lstrip('/'))
                        for c in (cand, cand + '.html', os.path.join(cand, 'index.html')):
                            if os.path.isfile(c):
                                tgt = os.path.relpath(c, BASE_DIR)
                                break
                    if tgt and tgt in all_ids and frag not in all_ids[tgt]:
                        problems.append(f'{rel}: dead cross-page anchor {base}#{frag}')

        # ── images should carry dimensions (layout shift) except tiny inline use ──
        for m in re.finditer(r'<img\b[^>]*>', html):
            tag = m.group(0)
            src = re.search(r'src="([^"]+)"', tag)
            if not src or src.group(1).startswith('http'):
                continue
            if 'width=' not in tag or 'height=' not in tag:
                warnings.append(f'{rel}: <img> without width/height -> {src.group(1)}')

    # ── sitemap coverage ──
    with open(os.path.join(BASE_DIR, 'sitemap.xml'), encoding='utf-8') as f:
        root_sitemap = f.read()
    for rel, _ in pages:
        if rel == 'thanks.html' or rel.startswith('scripts'):
            continue
        if rel == 'index.html':
            url = 'https://suppbridge.com/'
        elif rel.endswith(os.sep + 'index.html'):
            url = 'https://suppbridge.com/' + rel.replace(os.sep + 'index.html', '/').replace(os.sep, '/')
        else:
            url = 'https://suppbridge.com/' + rel.replace(os.sep, '/')
        if url not in root_sitemap:
            warnings.append(f'sitemap.xml: {rel} not listed ({url})')

    # ── report ──
    print(f'Validated {len(pages)} HTML pages\n')
    if problems:
        print(f'PROBLEMS ({len(problems)}):')
        for p in problems:
            print(f'  x {p}')
        print()
    else:
        print('No problems found.\n')

    if warnings:
        print(f'WARNINGS ({len(warnings)}):')
        for w in warnings[:40]:
            print(f'  ! {w}')
        if len(warnings) > 40:
            print(f'  ... and {len(warnings) - 40} more')
        print()

    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
