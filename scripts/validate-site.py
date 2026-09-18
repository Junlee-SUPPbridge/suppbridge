#!/usr/bin/env python3
"""Validate the static site: internal links, required SEO metadata, structured
data, taxonomy coverage, and language-compliance rules (the claims we must
never make).

Usage: python3 scripts/validate-site.py
Exit code 0 = clean, 1 = problems found.

V2.2 additions
--------------
The site is now metadata-driven: build-blog.py emits articles and pillar
pages from content/taxonomy.py. That makes it possible to check things that
were previously only checked by eye:

  * every markdown article has an ARTICLE_META entry (no orphan content)
  * every emitted page carries the schema its type requires
  * FAQPage schema is only present when a visible FAQ is also present
  * canonical / title / description are unique across the site
  * breadcrumb depth is correct for the page's position in the IA
"""

import os
import re
import sys
import glob
from urllib.parse import urlparse, unquote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from content.taxonomy import VALID_SEARCH_INTENT, SITE_URL  # noqa: E402

# Files we do not validate as pages
SKIP_DIRS = {'.git', 'node_modules', '.workbuddy', 'scripts'}

# Phrases that must never appear (see brief §16 and V2.1 §9 / §13).
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

    # ── V2.1 §13 — no published low-cost services ──
    (r'\$\s?\d{2,4}\b[^.]{0,24}\b(supplier|factory|alibaba)\b[^.]{0,12}\b(check|review|audit|verification)\b',
     'published low-price service'),
    (r'\b(supplier|factory|alibaba)\b[^.]{0,12}\b(check|review|audit)\b[^.]{0,12}\$\s?\d{2,4}',
     'published low-price service'),
    (r'\b(cheap|budget|low-?cost)\b[^.]{0,20}\b(sourcing|supplier check|review package)\b',
     'low-cost package positioning'),

    # ── V2.1 §9 — no unverifiable scale claims ──
    (r'\b\d{2,}\+?\s*(?:pre-?vetted\s+|partner\s+|verified\s+)?(?:factories|manufacturers|plants|facilities|clients|brands)',
     'unverifiable scale claim'),
    (r'\b(?:hundreds|thousands)\s+of\s+(?:factories|manufacturers|clients|brands|plants)',
     'unverifiable scale claim'),
    (r'\bour\s+(?:own\s+)?(?:factories|factory|plants|manufacturing\s+facilities|production\s+lines)',
     'implies facility ownership'),

    # ── V2.1 §1 / §17 — CDMO framing stays off the site ──
    (r'nutraceutical\s+cdmo', 'CDMO framing'),
    (r'contract\s+manufactur\w*\s+organization', 'CDMO framing'),
    (r'contract\s+development\s+and\s+manufactur\w*', 'CDMO framing'),

    # ── V2.1 §4 — supplier review is not the product ──
    (r'before you send the deposit, send us the supplier', 'supplier review framed as the offer'),
    (r'request a supplier review\s*(→|-|>)', 'supplier review framed as the primary CTA'),

    # ── V2.3 §1 / §2 / §6 + P1.1 §3 — supplier claims must stay verifiable.
    # We never quantify a network, never claim absolute independence,
    # and never invent savings or guarantees.
    (r'\b(?:fully|completely|totally)\s+independent\b', 'absolute independence claim'),
    (r'\b(?:network|portfolio)\s+of\s+\d+', 'invented network scale'),
    (r'\b\d{2,}\+?\s*(?:suppliers|vendors|contract\s+manufacturers)', 'invented supplier count'),
    (r'\bacross\s+\d{2,}\s+countries\b', 'invented country count'),
    (r'\bwe\s+(?:only\s+work\s+with|work\s+exclusively\s+with)\b', 'exclusive-network claim'),
    (r'\bguarantee\s+(?:the\s+)?(?:lowest|best|cheapest)\s+(?:price|cost|quote)', 'absolute price guarantee'),
    (r'\b\d+\s*%\s+(?:cost\s+|price\s+)?savings\b', 'invented savings figure'),
    (r'\bsavings\s+of\s+\d+\s*%', 'invented savings figure'),
]

# Whole-file checks that need structural context rather than a phrase match.
# Applied to the PRIMARY pages only (homepage, landing pages, pillar hubs,
# thank-you). An individual article may legitimately target an Alibaba query —
# §4 keeps it as a channel — but it must never frame a primary page.
PILLAR_DIRS = {'product-development', 'ingredient-sourcing',
               'supplement-manufacturing', 'china-supplement-supply-chain',
               'supplement-industry-consulting'}

PRIMARY_PAGES = {'index.html', 'china-supplement-sourcing.html',
                 'product-formats.html', 'regulatory/index.html',
                 'thanks.html'} | {f'{d}/index.html' for d in PILLAR_DIRS}

# ── V2.2 structured-data expectations ─────────────────────────────────────
# page kind -> schema @type values that must appear at least once
SCHEMA_REQUIRED = {
    'article': {'Article', 'BreadcrumbList'},
    'pillar': {'CollectionPage', 'BreadcrumbList'},
    # The homepage is the site root, so it carries the site-level identity
    # graph. No BreadcrumbList: a one-item trail is not a breadcrumb (§27).
    'home': {'Organization', 'Person', 'WebSite'},
}

# FAQPage may only be emitted on a page that also renders a visible FAQ.
# §23: "do not force FAQ schema onto every page." Any of these markers means
# a human can actually read the questions on the page.
FAQ_VISIBLE_MARKERS = ('class="faq-list"', 'class="faq-block"', 'class="faq-item"')

# ── V2.3 P1.1 §1 / §5 / §10 — homepage positioning regression guard ──────
# P1.1 settled the hierarchy: China is the core sourcing and manufacturing
# network (Level 1-2), the disciplines are what we do (Level 3), and other
# markets are an extended capability evaluated only when a project needs
# them (Level 4). These are the load-bearing sentences. Drop one and the
# homepage has drifted — either back to a China-only framing that loses the
# accountability line, or out to a global-network framing that buries the
# China core.
HOMEPAGE_REQUIRED = [
    'Supply Chain Advisor',
    'One accountable partner.',
    'China is our core sourcing and manufacturing network.',
    'The right supplier depends on the project.',
    'not tied to a single manufacturer, country or supplier',
    'Client confidentiality comes first.',
]

# The reverse guard, homepage-only. P1.1 deliberately deleted the standalone
# Global Supplier Network module and reduced the global capability to one
# auxiliary sentence. Naming the network as the positioning again — or
# leading with it — is the regression this catches. Articles may legitimately
# discuss sourcing in other markets, so this is NOT a site-wide rule.
HOMEPAGE_FORBIDDEN = [
    (r'global\s+supplier\s+network', 'global-network platform framing (P1.1 removed this module)'),
    (r'global\s+network\.\s*local\s+expertise', 'global-first headline (P1.1 removed this module)'),
    (r'\bglobal\s+sourcing\s+platform\b', 'global platform framing'),
    (r'\byour\s+global\s+(?:partner|network)\b', 'global-partner framing'),
]

# ── Identity naming — one role, three registers ──────────────────────────
# Before this pass the site carried four competing identities for the same
# thing: "China Supplement Industry Advisor & Supply Partner" (V2.1),
# "China Supplement Sourcing & Supply Chain Advisor" (P1), the nav label
# "Product & Supply Chain Advisor", and the visible founder role
# "China Supplement Industry Advisor". They are now ONE role in three
# registers, each doing a different job (§ brand → nav, schema → entity,
# SEO title → query surface):
#
#   Brand / nav label   Product & Supply Chain Advisor
#   Schema jobTitle /   Supplement Product & Supply Chain Advisor
#   visible role
#   SEO <title>         China Supplement Product & Supply Chain Advisor | SuppBridge
#
# Rationale (product decision, not taste): "Sourcing" is a service we sell,
# not who we are — leading with it narrows the identity to one deliverable
# and invites one-off supplier-check enquiries, which is the audience the
# funnel is designed to filter out. "Industry Advisor" and "Supply Partner"
# are retired V2.1 variants.
#
# Checked against lowercased HTML. Scoped to PRIMARY_PAGES: an article may
# quote an old label or discuss sourcing without redefining the brand.
IDENTITY_FORBIDDEN = [
    (r'sourcing\s*&(?:amp;)?\s*supply\s+chain\s+advisor',
     '"Sourcing & Supply Chain Advisor" (retired: sourcing is a service, not the role)'),
    (r'supplement\s+industry\s+advisor',
     '"China Supplement Industry Advisor" (retired V2.1 identity variant)'),
    (r'industry\s+advisor\s*&(?:amp;)?\s*supply\s+partner',
     '"Industry Advisor & Supply Partner" (retired V2.1 identity)'),
    (r'\bsourcing\s+advisor\b', '"Sourcing Advisor" (retired identity variant)'),
]

# The positive half of the same guard, homepage only: the approved SEO title
# must be present verbatim. Without this, deleting the wrong word still
# passes "no forbidden variant" while the title drifts by omission. Note the
# entity: this is matched against raw HTML, so "&" is written "&amp;".
IDENTITY_CANONICAL_TITLE = 'China Supplement Product &amp; Supply Chain Advisor | SuppBridge'


def page_kind(rel):
    if rel == 'index.html':
        return 'home'
    if rel.startswith('blog' + os.sep) and rel != os.path.join('blog', 'index.html'):
        return 'article'
    head = rel.split(os.sep)[0]
    if head in PILLAR_DIRS and rel.endswith('index.html'):
        return 'pillar'
    return 'page'


def is_redirect_stub(html):
    """Generated alias pages carry meta-refresh + noindex by design.

    They deliberately have no description/OG/schema — the destination page is
    the indexable entity. scripts/validate-site.py checks them for a working
    canonical target instead of the full page contract.
    """
    return 'http-equiv="refresh"' in html


def validate_redirect_stub(rel, html, problems):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if not m:
        problems.append(f'{rel}: redirect stub has no canonical')
        return
    dest = m.group(1)
    if not dest.startswith(SITE_URL):
        problems.append(f'{rel}: redirect canonical is not on {SITE_URL}: {dest}')
        return
    if 'noindex' not in html:
        problems.append(f'{rel}: redirect stub must carry noindex')
    # The destination must be a real page on disk.
    rel_dest = unquote(urlparse(dest).path).lstrip('/')
    if rel_dest in ('', '/'):
        return
    cand = os.path.join(BASE_DIR, rel_dest)
    if not (os.path.isfile(cand)
            or os.path.isfile(cand + '.html')
            or os.path.isfile(os.path.join(cand, 'index.html'))):
        problems.append(f'{rel}: redirect destination does not exist -> {dest}')


def jsonld_types(html):
    """Every @type declared in every ld+json block on the page.

    Handles both the scalar form `"@type": "Article"` and the array form
    `"@type": ["Article", "BlogPosting"]` — build-blog.py emits the latter for
    articles so the page satisfies readers looking for either type name.
    """
    found = set()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        for raw in re.findall(r'"@type"\s*:\s*(\[[^\]]*\]|"[^"]+")', block):
            found.update(re.findall(r'"([^"]+)"', raw))
    return found


FORBIDDEN_IN_HEADING = [
    (r'<h1[^>]*>(?:(?!</h1>).)*?alibaba', 'Alibaba in an H1 of a primary page (must not be the core narrative)'),
    (r'<title>(?:(?!</title>).)*?alibaba', 'Alibaba in <title> of a primary page'),
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
    seen_canonical = {}
    seen_title = {}
    seen_desc = {}
    redirect_stubs = []

    # Collect ids per page so we can validate #anchors
    for rel, path in pages:
        with open(path, encoding='utf-8') as f:
            html = f.read()
        all_ids[rel] = set(re.findall(r'\sid="([^"]+)"', html))

    for rel, path in pages:
        with open(path, encoding='utf-8') as f:
            html = f.read()

        kind = page_kind(rel)

        # Redirect stubs are a different contract — check them and move on.
        if is_redirect_stub(html):
            redirect_stubs.append(rel)
            validate_redirect_stub(rel, html, problems)
            continue

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
        if 'twitter:card' not in html:
            warnings.append(f'{rel}: no twitter:card')

        # ── canonical / title / description uniqueness ──
        for label, rx, bucket in (
            ('canonical', r'rel="canonical" href="([^"]+)"', seen_canonical),
            ('title', r'<title>([^<]+)</title>', seen_title),
            ('description', r'<meta name="description" content="([^"]+)"', seen_desc),
        ):
            m = re.search(rx, html)
            if not m:
                continue
            val = m.group(1)
            if val in bucket:
                problems.append(f'{rel}: duplicate {label} shared with {bucket[val]}')
            else:
                bucket[val] = rel

        # ── structured data expectations per page kind ──
        types = jsonld_types(html)
        for required in SCHEMA_REQUIRED.get(kind, set()):
            if required not in types:
                problems.append(f'{rel}: missing {required} schema (page kind: {kind})')

        # ── FAQ schema only where a visible FAQ exists (§23) ──
        has_faq_schema = 'FAQPage' in types
        has_faq_visible = any(mk in html for mk in FAQ_VISIBLE_MARKERS)
        if has_faq_schema and not has_faq_visible:
            problems.append(f'{rel}: FAQPage schema without a visible FAQ')
        if has_faq_visible and not has_faq_schema and kind in ('article', 'page'):
            warnings.append(f'{rel}: visible FAQ but no FAQPage schema')

        # ── breadcrumb depth (Home > Insights > Pillar > Article) ──
        if kind == 'article':
            crumbs = re.search(r'<nav class="crumbs"[^>]*>(.*?)</nav>', html, re.S)
            if not crumbs:
                problems.append(f'{rel}: article has no breadcrumb trail in markup')
            else:
                depth = len(re.findall(r'<a\b|<span\b', crumbs.group(1)))
                if depth < 4:
                    problems.append(f'{rel}: article breadcrumb depth {depth} (expected Home > Insights > Pillar > Article)')

        # ── stylesheet path ──
        for bad in BAD_CSS_PATHS:
            if bad in html:
                problems.append(f'{rel}: relative stylesheet path "{bad}" 404s from subdirectories')

        # ── forbidden claims ──
        low = html.lower()
        for pattern, label in FORBIDDEN:
            if re.search(pattern, low):
                problems.append(f'{rel}: forbidden wording ({label}) matched /{pattern}/')

        # ── V2.3 §1 — homepage must still carry the core positioning ──
        if rel == 'index.html':
            for needle in HOMEPAGE_REQUIRED:
                if needle not in html:
                    problems.append(f'{rel}: positioning statement missing -> "{needle}"')
            for pattern, label in HOMEPAGE_FORBIDDEN:
                if re.search(pattern, low):
                    problems.append(f'{rel}: forbidden homepage wording ({label})')
            # identity anchor — the approved SEO title, verbatim
            if IDENTITY_CANONICAL_TITLE not in html:
                problems.append(
                    f'{rel}: canonical identity title missing -> "{IDENTITY_CANONICAL_TITLE}"')

        # ── forbidden in headings / title (positioning guardrails, primary pages only) ──
        if rel in PRIMARY_PAGES:
            for pattern, label in FORBIDDEN_IN_HEADING:
                if re.search(pattern, low, re.S):
                    problems.append(f'{rel}: forbidden wording ({label})')

            # ── identity naming — retired role variants must not return ──
            for pattern, label in IDENTITY_FORBIDDEN:
                if re.search(pattern, low):
                    problems.append(f'{rel}: retired identity wording ({label})')

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
        # Redirect stubs must NOT be in the sitemap — they are noindex aliases.
        if rel in redirect_stubs:
            continue
        if rel == 'index.html':
            url = 'https://suppbridge.com/'
        elif rel.endswith(os.sep + 'index.html'):
            url = 'https://suppbridge.com/' + rel.replace(os.sep + 'index.html', '/').replace(os.sep, '/')
        else:
            url = 'https://suppbridge.com/' + rel.replace(os.sep, '/')
        if url not in root_sitemap:
            warnings.append(f'sitemap.xml: {rel} not listed ({url})')

    # Noindex stubs in the sitemap would be a contradictory signal.
    for rel in redirect_stubs:
        path = '/' + rel.replace(os.sep, '/')
        if path.replace('/index.html', '/') in root_sitemap:
            problems.append(f'{rel}: noindex redirect stub is listed in sitemap.xml')

    # ── taxonomy coverage: no orphan content ──
    # §18/§19 — an article added to blog/*.md without an ARTICLE_META entry
    # would silently lose its cluster, pillar, breadcrumb and related links.
    try:
        from content.taxonomy import ARTICLE_META, PILLARS, PILLAR_ORDER, article_meta
    except Exception as exc:  # pragma: no cover
        problems.append(f'content/taxonomy.py could not be imported: {exc}')
    else:
        md_slugs = {
            os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(BASE_DIR, 'blog', '*.md'))
        }
        for slug in sorted(md_slugs):
            if slug not in ARTICLE_META:
                problems.append(f'blog/{slug}.md: no ARTICLE_META entry (orphan article — no cluster/pillar/CTA)')

        valid_pillar_urls = {PILLARS[k]['url'] for k in PILLAR_ORDER}
        for slug in sorted(ARTICLE_META):
            meta = article_meta(slug)
            for field in ('cluster', 'pillar', 'commercial_intent', 'search_intent', 'entities'):
                if not meta.get(field):
                    problems.append(f'ARTICLE_META["{slug}"]: resolved "{field}" is empty')
            if meta['pillar'] not in valid_pillar_urls:
                problems.append(f'ARTICLE_META["{slug}"]: pillar "{meta["pillar"]}" not in PILLARS')
            if meta['commercial_intent'] not in ('low', 'medium', 'high'):
                problems.append(f'ARTICLE_META["{slug}"]: invalid commercial_intent')
            for si in meta['search_intent']:
                if si not in VALID_SEARCH_INTENT:
                    problems.append(f'ARTICLE_META["{slug}"]: invalid search_intent "{si}"')
            if slug not in md_slugs:
                warnings.append(f'ARTICLE_META["{slug}"]: entry has no blog/{slug}.md on disk')

        # every pillar must resolve to a generated page on disk
        for key in PILLAR_ORDER:
            url = PILLARS[key]['url'].strip('/')
            if not os.path.exists(os.path.join(BASE_DIR, url, 'index.html')):
                problems.append(f'pillar {key}: {PILLARS[key]["url"]} has no generated index.html')

    # ── report ──
    indexable = len(pages) - len(redirect_stubs)
    print(f'Validated {len(pages)} HTML pages '
          f'({indexable} indexable, {len(redirect_stubs)} redirect stubs)\n')
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
