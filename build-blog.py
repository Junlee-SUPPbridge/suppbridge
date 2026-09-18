#!/usr/bin/env python3
"""SuppBridge static site generator (V2.2 — metadata-first).

Usage: python3 build-blog.py

Reads
-----
content/taxonomy.py   all cluster / pillar / intent / FAQ metadata
blog/*.md             article content + frontmatter

Writes
------
blog/<slug>.html      article pages (breadcrumbs, schema, pillar block,
                      related reading, intent-scaled CTA)
blog/index.html       insights index grouped by pillar
blog/articles.json    machine-readable index for future SEO automation
<slug>/index.html     the five pillar pages
sitemap.xml           root sitemap (static pages + pillars + blog)
blog/sitemap.xml      blog-only sitemap

Design notes
------------
* Nothing here is CMS-shaped. Metadata is plain Python; output is plain
  HTML. `git push` still deploys.
* Blog pages use the same stylesheet as the rest of the site. Blog-specific
  rules are scoped under `body.page-blog` / `.page-pillar` so they can never
  leak into the homepage layout again.
* Adding an article = write the .md, add one ARTICLE_META entry, run this.
"""

import os
import re
import glob
import json
import subprocess
import html as html_lib
from datetime import datetime

from content.taxonomy import (
    SITE_URL, CONTACT, PILLARS, PILLAR_ORDER, ARTICLE_META, FAQ_DATA,
    ENTITIES, STATIC_PAGES, article_meta, articles_in_pillar,
)
from content.chrome import (
    nav_block, nav_html, footer_block, NAV_SCRIPT, NAV_SIMPLE,
    FOOTER_COMPANY, FOOTER_MORE, SPRITE_SYMBOLS,
)
from content.analytics import head_block as analytics_head
from content.redirects import redirect_pairs, netlify_format

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(BASE_DIR, "blog")
CSS_URL = "/styles/main.css"
OG_IMAGE = f"{SITE_URL}/images/blog-og.png"

# Commercial fallback destination when an article has no pillar block
DUE_DILIGENCE = "/china-supplement-sourcing.html"


# ══════════════════════════════════════════════════════════════════
# Markdown -> HTML (no external dependencies)
# ══════════════════════════════════════════════════════════════════

def md_to_html(md_text):
    lines = md_text.split('\n')
    result = []
    i = 0
    in_table = False
    table_lines = []

    def flush_table():
        nonlocal in_table, table_lines
        if not table_lines:
            return
        rows = []
        for idx, tl in enumerate(table_lines):
            cells = [c.strip() for c in tl.split('|') if c.strip()]
            tag = 'th' if idx == 0 else 'td'
            rows.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
        result.append('<table>' + ''.join(rows) + '</table>')
        in_table = False
        table_lines = []

    while i < len(lines):
        line = lines[i]

        if '|' in line and line.strip().startswith('|'):
            in_table = True
            if not re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                table_lines.append(line.strip())
            i += 1
            continue
        elif in_table:
            flush_table()

        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            result.append(f'<h{level}>{process_inline(m.group(2))}</h{level}>')
            i += 1
            continue

        if re.match(r'^[-*_]{3,}\s*$', line):
            result.append('<hr>')
            i += 1
            continue

        if line.startswith('> '):
            qlines = []
            while i < len(lines) and lines[i].startswith('> '):
                qlines.append(lines[i][2:])
                i += 1
            result.append('<blockquote>' + process_inline(' '.join(qlines)) + '</blockquote>')
            continue

        if re.match(r'^\s*[-*+]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\s*[-*+]\s+', lines[i]):
                items.append(re.sub(r'^\s*[-*+]\s+', '', lines[i]))
                i += 1
            result.append('<ul>' + ''.join(f'<li>{process_inline(it)}</li>' for it in items) + '</ul>')
            continue

        if re.match(r'^\s*\d+\.\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i]):
                items.append(re.sub(r'^\s*\d+\.\s+', '', lines[i]))
                i += 1
            result.append('<ol>' + ''.join(f'<li>{process_inline(it)}</li>' for it in items) + '</ol>')
            continue

        if line.strip() == '':
            i += 1
            continue

        plines = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6}\s|[|>\-*+]\s|\d+\.\s)', lines[i]):
            plines.append(lines[i])
            i += 1
        result.append('<p>' + process_inline(' '.join(plines)) + '</p>')

    if in_table:
        flush_table()

    return '\n'.join(result)


def process_inline(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    return text


def parse_frontmatter(md_text):
    if not md_text.startswith('---'):
        return {}, md_text
    parts = md_text.split('---', 2)
    if len(parts) < 3:
        return {}, md_text
    fm = {}
    for line in parts[1].strip().split('\n'):
        m = re.match(r'^(\w+):\s*(.+)$', line.strip())
        if m:
            key, val = m.group(1), m.group(2).strip().strip('"')
            if key == 'tags':
                val = [t.strip().strip('"').strip("'") for t in val.strip('[]').split(',')]
            fm[key] = val
    return fm, parts[2].strip()


def json_esc(text):
    """Escape a string for safe embedding inside a JSON string literal."""
    return (text or '').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')


def e(text):
    return html_lib.escape(text or '', quote=True)


def reading_time(body_md):
    words = len(re.findall(r'\S+', re.sub(r'[#*>`\[\]()]', ' ', body_md)))
    return max(2, round(words / 220))


def pretty_date(iso):
    try:
        d = datetime.strptime(iso, '%Y-%m-%d')
        return d.strftime('%d %B %Y').lstrip('0')
    except ValueError:
        return iso


# Shared chrome lives in content/chrome.py (single source of truth).


def page_head(title, description, canonical, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:site_name" content="SuppBridge">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" type="image/svg+xml" href="/images/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/images/favicon.png">
<link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
<link rel="stylesheet" href="{CSS_URL}">
<link rel="preload" href="{CSS_URL}" as="style">{extra_head}{analytics_head()}"""


def breadcrumb_html(trail):
    """trail = [(label, href|None), ...]"""
    parts = []
    for i, (label, href) in enumerate(trail):
        if href:
            parts.append(f'<a href="{href}">{e(label)}</a>')
        else:
            parts.append(f'<span aria-current="page">{e(label)}</span>')
        if i < len(trail) - 1:
            parts.append('<span class="crumb-sep" aria-hidden="true">/</span>')
    return f'<nav class="crumbs" aria-label="Breadcrumb">{"".join(parts)}</nav>'


def breadcrumb_schema(trail):
    items = ",\n".join(
        f'    {{ "@type": "ListItem", "position": {i + 1}, "name": "{json_esc(label)}", "item": "{href}" }}'
        for i, (label, href) in enumerate(trail)
    )
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
{items}
  ]
}}
</script>"""


def faq_items_for(key):
    """FAQ content for a page key.

    `index` → FAQ_DATA['index']. `pillar:<k>` → the pillar's own FAQ list.
    Returns [] when the page genuinely has no FAQ — in which case NO
    FAQPage schema is emitted (§23: never invent FAQ for SEO's sake).
    """
    if key.startswith('pillar:'):
        return PILLARS[key.split(':', 1)[1]].get('faq') or []
    return FAQ_DATA.get(key) or []


def faq_block_html(key, heading="Frequently Asked"):
    """Visible FAQ + matching FAQPage schema. Both or neither."""
    items = faq_items_for(key)
    if not items:
        return "", ""
    body = "\n".join(
        f'<details><summary>{e(q)}<span class="sr-only"> — toggle answer</span></summary>'
        f'<div class="faq-body">{"".join(f"<p>{e(p)}</p>" for p in paras)}</div></details>'
        for q, paras in items
    )
    visible = f"""<section class="faq-block">
<h2>{e(heading)}</h2>
{body}
</section>"""
    schema_items = ",\n".join(
        '    {\n'
        '      "@type": "Question",\n'
        f'      "name": "{json_esc(q)}",\n'
        '      "acceptedAnswer": { "@type": "Answer", "text": "'
        + json_esc(' '.join(paras)) + '" }\n'
        '    }'
        for q, paras in items
    )
    schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{schema_items}
  ]
}}
</script>"""
    return visible, schema


# ══════════════════════════════════════════════════════════════════
# CTA — scales with commercial intent
# ══════════════════════════════════════════════════════════════════

def article_cta(intent, cluster_title):
    if intent == "low":
        return f"""<div class="article-cta article-cta--low">
<p class="ac-kicker">Working on something in {e(cluster_title)}?</p>
<h3>Send us the brief and we will tell you what is realistic.</h3>
<p>No pitch deck, no discovery call script — a straight read on specification, supply and timeline.</p>
<div class="ac-actions">
<a class="ac-btn" href="{CONTACT}">Discuss Your Project →</a>
</div>
</div>"""
    if intent == "medium":
        return f"""<div class="article-cta article-cta--medium">
<p class="ac-kicker">Next step</p>
<h3>If you are making this decision now, we can look at it with you.</h3>
<p>Formulation, ingredients, manufacturer selection, sampling, production and supply-chain setup — reviewed by someone on your side of the table. Send the brief, the formula or the quotation and we will tell you what is realistic and what needs checking first.</p>
<div class="ac-actions">
<a class="ac-btn" href="{CONTACT}">Discuss Your Project →</a>
</div>
</div>"""
    return f"""<div class="article-cta">
<p class="ac-kicker">Project enquiry</p>
<h3>If you are building or sourcing a supplement in China, we can look at the whole project.</h3>
<p>Formulation, ingredients, manufacturer selection, sampling, production and supply-chain setup — reviewed by someone on your side of the table. Send the brief, the formula or the quotation and we will tell you what is realistic and what needs checking first.</p>
<div class="ac-actions">
<a class="ac-btn" href="{CONTACT}">Discuss Your Project →</a>
<a class="ac-btn ac-btn--ghost" href="/china-supplement-sourcing.html">Supplier due diligence</a>
</div>
</div>"""


# ══════════════════════════════════════════════════════════════════
# Related-article engine
#
# Priority: same cluster → shared cluster overlap → shared entities →
# same pillar, most commercially relevant first. Never random.
# ══════════════════════════════════════════════════════════════════

def related_articles(current, all_articles, limit=3):
    cur_cluster = current['cluster']
    cur_secondary = set(current.get('secondary') or [])
    cur_entities = set(current.get('entities') or [])
    intent_rank = {'high': 3, 'medium': 2, 'low': 1}

    scored = []
    for other in all_articles:
        if other['slug'] == current['slug']:
            continue
        score = 0
        other_secondary = set(other.get('secondary') or [])
        shared_entities = cur_entities & set(other.get('entities') or [])
        score += 3 * len(shared_entities)
        if other['cluster'] == cur_cluster:
            score += 5
        if other['cluster'] in cur_secondary or cur_cluster in other_secondary:
            score += 3
        score += len(other_secondary & cur_secondary)
        score += 0.4 * intent_rank.get(other.get('commercial_intent', 'low'), 1)
        if score > 0:
            scored.append((score, other['date'], other['slug'], other['title']))

    scored.sort(key=lambda x: (-x[0], x[1]), reverse=False)
    scored.sort(key=lambda x: -x[0])
    return [(s, t) for _, _, s, t in scored[:limit]]


# ══════════════════════════════════════════════════════════════════
# Build
# ══════════════════════════════════════════════════════════════════

def load_articles():
    articles = []
    warnings = []
    for md_path in sorted(glob.glob(os.path.join(BLOG_DIR, "*.md"))):
        with open(md_path, encoding='utf-8') as f:
            md_text = f.read()
        fm, body = parse_frontmatter(md_text)
        slug = fm.get('slug', os.path.splitext(os.path.basename(md_path))[0])
        meta = article_meta(slug)
        if meta is None:
            warnings.append(f"{slug}.md has no ARTICLE_META entry — falling back to 'consulting'/low")
            meta = {
                'cluster': 'consulting', 'commercial_intent': 'low',
                'secondary': [], 'entities': [], 'featured': False,
                'search_intent': ['informational'],
            }
        cluster = meta['cluster']
        if cluster not in PILLARS:
            warnings.append(f"{slug}: unknown cluster '{cluster}' — falling back to 'consulting'")
            cluster = 'consulting'
        articles.append({
            'slug': slug,
            'title': fm.get('title', slug),
            'date': fm.get('date', '2026-01-01'),
            'updated': fm.get('updated', ''),
            'tags': fm.get('tags', []),
            'description': fm.get('description', ''),
            'body_md': body,
            'body_html': md_to_html(body),
            'og_image': fm.get('og_image', OG_IMAGE),
            'cluster': cluster,
            'secondary': meta.get('secondary', []),
            'commercial_intent': meta.get('commercial_intent', 'low'),
            'search_intent': meta.get('search_intent', ['informational']),
            'entities': meta.get('entities', []),
            'featured': meta.get('featured', False),
            'minutes': reading_time(body),
        })
    articles.sort(key=lambda a: a['date'], reverse=True)
    return articles, warnings


def build_articles(articles):
    for art in articles:
        k = art['cluster']
        pillar = PILLARS[k]
        trail = [("Home", "/"), ("Insights", "/blog/"),
                 (pillar['nav_title'], pillar['url']),
                 (art['title'], None)]
        canonical = f"{SITE_URL}/blog/{art['slug']}.html"

        related = related_articles(art, articles)
        related_html = "\n".join(
            f'<li><a href="/blog/{s}.html">{e(t)}</a></li>' for s, t in related
        ) or '<li><a href="/blog/">Browse all insights</a></li>'

        # Other articles in the same cluster, surfaced as the pillar block.
        siblings = [
            o for o in articles
            if o['slug'] != art['slug'] and (o['cluster'] == k or k in (o.get('secondary') or []))
        ]
        sibling_links = "\n".join(
            f'<li><a href="/blog/{o["slug"]}.html">{e(o["title"])}</a></li>'
            for o in siblings[:4]
        )
        pillar_block = f"""<aside class="pillar-block">
<span class="pb-kicker">Part of · {e(pillar['nav_title'])}</span>
<h3><a href="{pillar['url']}">{e(pillar['title'])}</a></h3>
<p>{e(pillar['lede'])}</p>
<ul class="pb-links">{sibling_links}</ul>
</aside>"""

        cta = article_cta(art['commercial_intent'], pillar['nav_title'])

        article_schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": ["Article", "BlogPosting"],
  "headline": "{json_esc(art['title'])}",
  "description": "{json_esc(art['description'])}",
  "datePublished": "{art['date']}",
  "dateModified": "{art['updated'] or art['date']}",
  "url": "{canonical}",
  "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{canonical}" }},
  "image": "{art['og_image']}",
  "articleSection": "{json_esc(pillar['nav_title'])}",
  "keywords": "{json_esc(', '.join(art['entities']) or pillar['nav_title'])}",
  "wordCount": {len(re.findall(r'\S+', art['body_md']))},
  "author": {{
    "@type": "Person",
    "name": "Jun Lee",
    "jobTitle": "Supplement Product & Supply Chain Strategist",
    "url": "{SITE_URL}/#founder",
    "worksFor": {{ "@type": "Organization", "name": "SuppBridge", "url": "{SITE_URL}" }}
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "SuppBridge",
    "url": "{SITE_URL}",
    "logo": {{ "@type": "ImageObject", "url": "{SITE_URL}/images/logo.png" }}
  }}
}}
</script>"""

        html = f"""{page_head(f"{art['title']} — SuppBridge Insights", art['description'], canonical)}
{article_schema}
{breadcrumb_schema(trail)}
</head>
<body class="page-blog">
{nav_html()}
<article>
<header class="article-hero">
<div class="container">
{breadcrumb_html(trail)}
<span class="tag tag-{k}">{e(pillar['nav_title'])}</span>
<h1>{e(art['title'])}</h1>
<div class="meta">
<span>{pretty_date(art['date'])}</span>
<span class="meta-dot" aria-hidden="true">·</span>
<span>{art['minutes']} min read</span>
<span class="meta-dot" aria-hidden="true">·</span>
<span>Jun Lee</span>
</div>
<p class="excerpt">{e(art['description'])}</p>
</div>
</header>
<div class="article-body">
<div class="container">
{art['body_html']}
{cta}
{pillar_block}
<div class="related-reading">
<h3>Related Reading</h3>
<ul>
{related_html}
</ul>
</div>
</div>
</div>
</article>
{footer_block()}
{NAV_SCRIPT}
</body>
</html>"""

        with open(os.path.join(BLOG_DIR, f"{art['slug']}.html"), 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  + blog/{art['slug']}.html  [{k}/{art['commercial_intent']}]")


def build_blog_index(articles):
    groups = []
    for k in PILLAR_ORDER:
        p = PILLARS[k]
        items = [a for a in articles if a['cluster'] == k or k in (a.get('secondary') or [])]
        if not items:
            continue
        cards = "\n".join(f"""<a class="blog-card" href="/blog/{a['slug']}.html">
<div class="blog-card-head"><span class="tag tag-{a['cluster']}">{e(PILLARS[a['cluster']]['nav_title'])}</span></div>
<h3>{e(a['title'])}</h3>
<p class="desc">{e(a['description'])}</p>
<p class="meta">{pretty_date(a['date'])} · {a['minutes']} min read</p>
</a>""" for a in items)
        groups.append(f"""<section class="pillar-group">
<div class="pg-head">
<h2><a href="{p['url']}">{e(p['nav_title'])}</a></h2>
<span class="pg-count">{len(items)} article{'s' if len(items) != 1 else ''}</span>
</div>
<p class="pg-intro">{e(p['lede'])}</p>
{cards}
</section>""")

    desc = ("Practical guides on supplement product development, ingredient sourcing, "
            "manufacturing and China supply-chain management — written from the buyer's side "
            "of the table, not the factory's.")
    canonical = f"{SITE_URL}/blog/"
    blog_schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "SuppBridge Insights",
  "description": "{json_esc(desc)}",
  "url": "{canonical}",
  "publisher": {{ "@type": "Organization", "name": "SuppBridge", "url": "{SITE_URL}" }},
  "author": {{ "@type": "Person", "name": "Jun Lee", "url": "{SITE_URL}/#founder" }},
  "blogPost": [
{chr(10).join(f'    {{ "@type": "BlogPosting", "headline": "{json_esc(a["title"])}", "url": "{SITE_URL}/blog/{a["slug"]}.html", "datePublished": "{a["date"]}" }}{"," if i < len(articles) - 1 else ""}' for i, a in enumerate(articles))}
  ]
}}
</script>"""

    html = f"""{page_head("Insights — Building Supplements in China | SuppBridge", desc, canonical)}
{blog_schema}
{breadcrumb_schema([("Home", "/"), ("Insights", None)])}
</head>
<body class="page-blog">
{nav_html()}
<header class="blog-hero">
<div class="container">
{breadcrumb_html([("Home", "/"), ("Insights", None)])}
<span class="eyebrow">Industry Knowledge Base</span>
<h1>Building Supplements in China — Notes From Inside the Industry</h1>
<p>Practical guides on product development, ingredient sourcing, manufacturing and supply-chain management. Organised by discipline, written for brand owners rather than procurement departments.</p>
<div class="blog-hero-cta"><a href="{CONTACT}" class="btn btn--primary">Discuss Your Project →</a></div>
</div>
</header>
<div class="blog-list">
<div class="container">
<div class="blog-cta-band">
<h2>Working on a product in China?</h2>
<p>Tell us what you are trying to build. We will tell you what is realistic, what it takes and where the risks sit.</p>
<a href="{CONTACT}" class="btn btn--onlight">Discuss Your Project →</a>
</div>
{''.join(groups)}
</div>
</div>
{footer_block()}
{NAV_SCRIPT}
</body>
</html>"""

    with open(os.path.join(BLOG_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  + blog/index.html ({len(articles)} articles in {len(groups)} pillars)")


def build_pillars(articles):
    for idx, k in enumerate(PILLAR_ORDER):
        p = PILLARS[k]
        canonical = f"{SITE_URL}{p['url']}"
        own = [a for a in articles if a['cluster'] == k]
        also = [a for a in articles if a['cluster'] != k and k in (a.get('secondary') or [])]
        items = own + also

        if items:
            listing = "\n".join(f"""<a class="blog-card" href="/blog/{a['slug']}.html">
<div class="blog-card-head"><span class="tag tag-{a['cluster']}">{e(PILLARS[a['cluster']]['nav_title'])}</span></div>
<h3>{e(a['title'])}</h3>
<p class="desc">{e(a['description'])}</p>
<p class="meta">{pretty_date(a['date'])} · {a['minutes']} min read</p>
</a>""" for a in items)
        else:
            listing = ('<p class="pillar-empty">Guides in this discipline are in preparation. '
                       'In the meantime, <a href="/#start-project">tell us what you are working on</a> '
                       'and we will answer the specific question directly.</p>')

        faq_visible, faq_schema = faq_block_html(f"pillar:{k}", "Questions we get asked")
        topics = "".join(f"<li>{e(t)}</li>" for t in p['topics'])
        intro = "".join(f"<p>{e(par)}</p>" for par in p['intro'])

        trail = [("Home", "/"), (p['nav_title'], None)]
        siblings = "".join(
            f'<a class="pillar-sibling" href="{PILLARS[o]["url"]}">'
            f'<span class="ps-t">{e(PILLARS[o]["nav_title"])}</span>'
            f'<span class="ps-d">{e(PILLARS[o]["nav_desc"])}</span></a>'
            for o in PILLAR_ORDER if o != k
        )

        collection_schema = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "{json_esc(p['title'])}",
  "description": "{json_esc(p['lede'])}",
  "url": "{canonical}",
  "isPartOf": {{ "@type": "WebSite", "name": "SuppBridge", "url": "{SITE_URL}" }},
  "author": {{ "@type": "Person", "name": "Jun Lee", "url": "{SITE_URL}/#founder" }},
  "publisher": {{ "@type": "Organization", "name": "SuppBridge", "url": "{SITE_URL}" }},
  "hasPart": [
{chr(10).join(f'    {{ "@type": "Article", "headline": "{json_esc(a["title"])}", "url": "{SITE_URL}/blog/{a["slug"]}.html" }}{"," if i < len(items) - 1 else ""}' for i, a in enumerate(items)) or "  "}
  ]
}}
</script>"""

        html = f"""{page_head(f"{p['title']} | SuppBridge", p['lede'], canonical)}
{collection_schema}
{breadcrumb_schema([("Home", SITE_URL + "/"), (p['nav_title'], canonical)])}
{faq_schema}
</head>
<body class="page-pillar">
{nav_html()}
<header class="pillar-hero">
<div class="container">
{breadcrumb_html(trail)}
<span class="eyebrow">{e(p['num'])} — Expertise</span>
<h1>{e(p['h1'])}</h1>
<p class="pillar-lede">{e(p['lede'])}</p>
<ul class="pillar-topics">{topics}</ul>
</div>
</header>
<div class="pillar-body">
<div class="container">
<div class="pillar-intro">{intro}</div>
<div class="pillar-articles">
<h2>Guides in this discipline</h2>
{listing}
</div>
{faq_visible}
<div class="pillar-next">
<h3>Working on a project in this area?</h3>
<p>Send us the brief, the formula or the quotation. We will tell you what is realistic, what it costs to get wrong, and what needs checking before you commit.</p>
<a href="{CONTACT}" class="btn btn--primary">Discuss Your Project →</a>
</div>
</div>
</div>
<section class="section section--soft">
<div class="container">
<div class="section-header section-header--left">
<span class="eyebrow">Other disciplines</span>
<h2>Where else we work</h2>
</div>
<div class="pillar-siblings">{siblings}</div>
</div>
</section>
{footer_block()}
{NAV_SCRIPT}
</body>
</html>"""

        out_dir = os.path.join(BASE_DIR, p['slug'])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  + {p['slug']}/index.html ({len(items)} articles)")


# ══════════════════════════════════════════════════════════════════
# Sitemap date provenance (V2.3 §18)
# ══════════════════════════════════════════════════════════════════

_GIT_DATE_CACHE = {}


def git_last_commit_date(rel_path):
    """Committer date (YYYY-MM-DD) of the last commit touching `rel_path`.

    Returns None when git is unavailable, the path is not tracked, or the
    repository simply has no history for it. Callers then omit <lastmod>
    rather than inventing a date.
    """
    if rel_path in _GIT_DATE_CACHE:
        return _GIT_DATE_CACHE[rel_path]
    result = None
    try:
        proc = subprocess.run(
            ['git', 'log', '-1', '--format=%cs', '--', rel_path],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=15,
        )
        stamp = (proc.stdout or '').strip()
        if proc.returncode == 0 and re.fullmatch(r'\d{4}-\d{2}-\d{2}', stamp):
            result = stamp
    except (OSError, subprocess.SubprocessError):
        result = None
    _GIT_DATE_CACHE[rel_path] = result
    return result


def article_lastmod(art):
    """Explicit article date first, git source date second, otherwise None."""
    explicit = (art.get('updated') or art.get('date') or '').strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', explicit):
        return explicit
    return git_last_commit_date(os.path.join('blog', art['slug'] + '.md'))


def build_sitemaps(articles):
    """Sitemaps with honest <lastmod> values (V2.3 §18).

    Order of preference, per URL:
      1. an explicit date we actually hold — an article's front-matter
         `updated`, else its `date`;
      2. otherwise the git committer date of the source file that produces
         the page;
      3. otherwise **omit** <lastmod> entirely.
    Never falls back to "today": stamping every URL with the build date
    tells a crawler that the whole site changed on every deploy, which is
    less informative than saying nothing at all.
    """
    def url(loc, freq, pri, lastmod=None):
        out = (f"  <url>\n    <loc>{loc}</loc>\n    <changefreq>{freq}</changefreq>\n"
               f"    <priority>{pri}</priority>\n")
        if lastmod:
            out += f"    <lastmod>{lastmod}</lastmod>\n"
        return out + "  </url>\n"

    root = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for rel, freq, pri in STATIC_PAGES:
        if rel == 'index.html':
            loc = f"{SITE_URL}/"
        elif rel.endswith('/index.html'):
            loc = f"{SITE_URL}/{rel[:-len('index.html')]}"
        else:
            loc = f"{SITE_URL}/{rel}"
        root += url(loc, freq, pri, git_last_commit_date(rel))
    for k in PILLAR_ORDER:
        out_rel = PILLARS[k]['url'].strip('/') + '/index.html'
        root += url(f"{SITE_URL}{PILLARS[k]['url']}", "weekly", "0.9",
                    git_last_commit_date(out_rel))
    root += url(f"{SITE_URL}/blog/", "weekly", "0.8",
                git_last_commit_date(os.path.join('blog', 'index.html')))
    for a in articles:
        root += url(f"{SITE_URL}/blog/{a['slug']}.html", "monthly", "0.7",
                    article_lastmod(a))
    root += '</urlset>'
    with open(os.path.join(BASE_DIR, "sitemap.xml"), 'w', encoding='utf-8') as f:
        f.write(root)
    print("  + sitemap.xml")

    blog = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    blog += url(f"{SITE_URL}/blog/", "weekly", "0.8",
                git_last_commit_date(os.path.join('blog', 'index.html')))
    for a in articles:
        blog += url(f"{SITE_URL}/blog/{a['slug']}.html", "monthly", "0.7",
                    article_lastmod(a))
    blog += '</urlset>'
    with open(os.path.join(BLOG_DIR, "sitemap.xml"), 'w', encoding='utf-8') as f:
        f.write(blog)
    print("  + blog/sitemap.xml")


def build_articles_json(articles):
    """Machine-readable index — the hook for future Search Console work (§30):
    query · page · impressions · clicks · ctr · position · cluster · intent."""
    out = [{
        'slug': a['slug'],
        'url': f"/blog/{a['slug']}.html",
        'title': a['title'],
        'description': a['description'],
        'date': a['date'],
        'minutes': a['minutes'],
        'cluster': a['cluster'],
        'secondary_clusters': a['secondary'],
        'pillar': PILLARS[a['cluster']]['url'],
        'commercial_intent': a['commercial_intent'],
        'search_intent': a['search_intent'],
        'entities': a['entities'],
        'featured': a['featured'],
    } for a in articles]
    with open(os.path.join(BLOG_DIR, "articles.json"), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("  + blog/articles.json")


def build_redirects():
    """Emit real HTML redirect pages + a host redirects file from one map.

    GitHub Pages ignores `_redirects`, so an alias declared only there 404s.
    A static page carrying meta-refresh + canonical works everywhere, and the
    canonical tag is what tells a crawler which URL to actually index.

    Two output shapes, matching how the source path would be requested:
      /formats            -> formats/index.html
      /product-formats.html -> product-formats.html  (overwrites nothing;
                               skipped if a real page already owns the path)
    """
    written = 0
    skipped = []
    for src, dst in redirect_pairs():
        rel = src.strip('/')
        dest_url = f"{SITE_URL}{dst}"

        if rel.endswith('.html'):
            out_path = os.path.join(BASE_DIR, rel)
        else:
            out_path = os.path.join(BASE_DIR, rel, 'index.html')

        # Never shadow a real page: if a genuine page already lives here, the
        # alias is redundant and generating over it would break the site.
        if os.path.exists(out_path):
            skipped.append(src)
            continue

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Redirecting — SuppBridge</title>
<link rel="canonical" href="{dest_url}">
<meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0; url={dest_url}">
<script>location.replace("{dest_url}");</script>
</head>
<body>
<p>This page has moved to <a href="{dest_url}">{dest_url}</a>.</p>
</body>
</html>
"""
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(page)
        written += 1

    with open(os.path.join(BASE_DIR, '_redirects'), 'w', encoding='utf-8') as f:
        f.write(netlify_format())

    print(f"  + {written} redirect pages + _redirects")
    if skipped:
        print(f"    (skipped {len(skipped)} that a real page already owns: {', '.join(skipped)})")


def build():
    print("Reading content/taxonomy.py + blog/*.md …\n")

    articles, warnings = load_articles()

    print("Articles:")
    build_articles(articles)
    build_blog_index(articles)

    print("\nPillar pages:")
    build_pillars(articles)

    print("\nIndex files:")
    build_sitemaps(articles)
    build_articles_json(articles)

    print("\nRedirects:")
    build_redirects()

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")

    # Coverage summary — metadata gaps should be obvious, not silent.
    print("\nCluster coverage:")
    for k in PILLAR_ORDER:
        own = len([a for a in articles if a['cluster'] == k])
        also = len([a for a in articles if a['cluster'] != k and k in (a.get('secondary') or [])])
        print(f"  {PILLARS[k]['num']} {PILLARS[k]['nav_title']:<24} {own} primary, {also} secondary")

    print(f"\nDone: {len(articles)} articles, {len(PILLAR_ORDER)} pillar pages.")
    print("Deploy step: git push (GitHub Pages serves the repo as-is).")


if __name__ == '__main__':
    build()
