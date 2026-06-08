#!/usr/bin/env python3
"""Build static blog HTML pages from Markdown files.

Usage: python3 build-blog.py
Reads blog/*.md → generates blog/*.html + blog/index.html + sitemap.xml
"""

import os, re, glob, json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(BASE_DIR, "blog")
SITE_URL = "https://suppbridge.com"

# Site-wide CSS (matching index.html palette)
SITE_CSS = """<style>
:root { --ink:#0E1922; --teal:#0C6259; --teal-deep:#0A4A43; --mint:#4DB89E; --mint-soft:#EDF8F4; --muted:#5C7688; --line:#DDE4EA; --bg:#F6F9FB; --white:#fff; --navy:#1B3A4B; --radius:12px; --radius-sm:8px; --radius-lg:20px; --shadow:0 4px 24px rgba(0,0,0,.06); --shadow-sm:0 2px 8px rgba(0,0,0,.04); }
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--ink);background:var(--bg);line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:var(--teal);text-decoration:none}
a:hover{color:var(--teal-deep)}
img{max-width:100%;height:auto}
.container{max-width:820px;margin:0 auto;padding:0 24px}

/* Nav */
.nav{background:rgba(255,255,255,.92);backdrop-filter:blur(16px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:100}
.nav-inner{max-width:1160px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:56px}
.nav-brand{display:flex;align-items:center;gap:10px;text-decoration:none}
.nav-brand img{height:26px;width:auto}
.nav-brand span{font-size:.76rem;font-weight:600;color:var(--muted);letter-spacing:.03em}
.nav-links{display:flex;align-items:center;gap:20px;list-style:none}
.nav-links a{font-size:.82rem;font-weight:500;color:var(--ink);transition:color .2s}
.nav-links a:hover{color:var(--teal)}

/* Article Page */
.article-hero{padding:56px 0 28px;background:var(--white);border-bottom:1px solid var(--line)}
.article-hero .tag{display:inline-block;padding:4px 12px;border-radius:100px;font-size:.72rem;font-weight:600;letter-spacing:.03em;margin-bottom:14px}
.tag-delivery{background:#EAF7F4;color:var(--teal)}
.tag-regulatory{background:#FDF2E9;color:#B86B20}
.tag-formulation{background:#EDE7F6;color:#5B3E96}
.tag-market{background:#E8F0FE;color:#1A5FB4}
.tag-pet{background:#FDE8E8;color:#B91C1C}
.article-hero h1{font-size:2.2rem;font-weight:800;line-height:1.25;letter-spacing:-.02em;margin-bottom:12px}
.article-hero .meta{font-size:.82rem;color:var(--muted);margin-bottom:8px}
.article-hero .excerpt{font-size:1.05rem;color:var(--muted);line-height:1.6;max-width:680px}

.article-body{padding:40px 0 64px;background:var(--white)}
.article-body .container{max-width:740px}
.article-body h2{font-size:1.45rem;font-weight:700;margin:36px 0 14px;color:var(--ink);letter-spacing:-.01em}
.article-body h3{font-size:1.15rem;font-weight:650;margin:28px 0 10px;color:var(--ink)}
.article-body p{margin-bottom:16px;font-size:.97rem;line-height:1.78;color:rgba(14,25,34,.82)}
.article-body ul,.article-body ol{padding-left:22px;margin-bottom:18px}
.article-body li{margin-bottom:8px;font-size:.95rem;line-height:1.7;color:rgba(14,25,34,.82)}
.article-body table{width:100%;border-collapse:collapse;margin:20px 0 28px;font-size:.88rem}
.article-body th{background:var(--bg);text-align:left;padding:10px 14px;font-weight:650;color:var(--ink);border-bottom:2px solid var(--line)}
.article-body td{padding:9px 14px;border-bottom:1px solid var(--line);color:rgba(14,25,34,.82)}
.article-body tr:nth-child(even) td{background:var(--mint-soft)}
.article-body blockquote{border-left:3px solid var(--mint);padding:12px 18px;margin:20px 0;background:var(--mint-soft);border-radius:0 var(--radius-sm) var(--radius-sm) 0;font-size:.92rem;color:var(--muted)}
.article-body code{background:var(--bg);padding:2px 6px;border-radius:4px;font-size:.85em}
.article-body strong{color:var(--ink);font-weight:650}
.article-body hr{border:none;border-top:1px solid var(--line);margin:36px 0}
.article-body em{color:var(--muted)}

.article-cta{margin-top:40px;padding:28px 0;border-top:1px solid var(--line)}
.article-cta a{display:inline-block;padding:12px 28px;background:var(--teal);color:#fff;border-radius:100px;font-weight:600;font-size:.9rem;transition:all .2s;text-decoration:none}
.article-cta a:hover{background:var(--teal-deep);transform:translateY(-1px);box-shadow:0 6px 20px rgba(12,98,89,.25)}

/* Blog Index */
.blog-hero{padding:64px 0 36px;text-align:center;background:var(--white);border-bottom:1px solid var(--line)}
.blog-hero h1{font-size:2.2rem;font-weight:800;letter-spacing:-.02em;margin-bottom:10px}
.blog-hero p{color:var(--muted);font-size:1.05rem;max-width:560px;margin:0 auto}
.blog-list{padding:40px 0 64px;max-width:820px;margin:0 auto}
.blog-card{background:var(--white);border:1px solid var(--line);border-radius:var(--radius);padding:28px 32px;margin-bottom:18px;transition:all .25s}
.blog-card:hover{border-color:var(--teal);transform:translateX(4px);box-shadow:var(--shadow)}
.blog-card .tag{display:inline-block;padding:3px 10px;border-radius:100px;font-size:.68rem;font-weight:600;letter-spacing:.03em;margin-bottom:10px}
.blog-card h2{font-size:1.2rem;font-weight:700;margin-bottom:8px;letter-spacing:-.01em}
.blog-card h2 a{color:var(--ink);text-decoration:none}
.blog-card h2 a:hover{color:var(--teal)}
.blog-card .desc{color:var(--muted);font-size:.9rem;line-height:1.55}
.blog-card .meta{font-size:.78rem;color:var(--muted);margin-top:10px}

/* Footer */
.blog-footer{background:var(--ink);color:rgba(255,255,255,.65);padding:24px 0;text-align:center;font-size:.82rem}
.blog-footer a{color:var(--mint)}
@media (max-width:700px) {
  .article-hero h1,.blog-hero h1{font-size:1.6rem}
  .nav-links{display:none}
  .blog-card{padding:20px 18px}
}
</style>"""

# ── Markdown → HTML Converter (no external deps) ──

def md_to_html(md_text):
    """Convert basic Markdown to HTML fragments."""
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

        # Table detection
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
            if not re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                table_lines.append(line.strip())
            i += 1
            continue
        else:
            if in_table:
                flush_table()

        # Headers
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            result.append(f'<h{level}>{process_inline(m.group(2))}</h{level}>')
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line):
            result.append('<hr>')
            i += 1
            continue

        # Blockquote
        if line.startswith('> '):
            qlines = []
            while i < len(lines) and lines[i].startswith('> '):
                qlines.append(lines[i][2:])
                i += 1
            result.append('<blockquote>' + process_inline(' '.join(qlines)) + '</blockquote>')
            continue

        # Unordered list (multi-line)
        if re.match(r'^\s*[-*+]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\s*[-*+]\s+', lines[i]):
                items.append(re.sub(r'^\s*[-*+]\s+', '', lines[i]))
                i += 1
            result.append('<ul>' + ''.join(f'<li>{process_inline(it)}</li>' for it in items) + '</ul>')
            continue

        # Ordered list (multi-line)
        if re.match(r'^\s*\d+\.\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i]):
                items.append(re.sub(r'^\s*\d+\.\s+', '', lines[i]))
                i += 1
            result.append('<ol>' + ''.join(f'<li>{process_inline(it)}</li>' for it in items) + '</ol>')
            continue

        # Blank line → close paragraph
        if line.strip() == '':
            i += 1
            continue

        # Paragraph
        plines = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6}\s|[|>\-*+]\s|\d+\.\s)', lines[i]):
            plines.append(lines[i])
            i += 1
        result.append('<p>' + process_inline(' '.join(plines)) + '</p>')

    if in_table:
        flush_table()

    return '\n'.join(result)


def process_inline(text):
    """Process inline Markdown formatting."""
    # Bold (**text**)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic (*text*)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Inline code (`text`)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links [text](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    # Strikethrough (~~text~~) — less common
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    return text


def parse_frontmatter(md_text):
    """Parse YAML-like frontmatter from Markdown."""
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


def tag_class(tag_slug):
    """Map tag slug to CSS class."""
    mapping = {
        'delivery-systems': 'delivery',
        'regulatory': 'regulatory',
        'formulation': 'formulation',
        'market-trends': 'market',
        'pet-wellness': 'pet',
        'dtc': 'market',
        'brand-strategy': 'market',
        'fda': 'regulatory',
        'efsa': 'regulatory',
        'eu': 'regulatory',
        'compliance': 'regulatory',
        'functional-beverage': 'delivery',
        'product-innovation': 'delivery',
        'sleep-health': 'formulation',
        'functional-powders': 'formulation',
        'product-development': 'formulation',
        'flavor': 'formulation',
        'companion-animal': 'pet',
        'supplements': 'pet',
        'innovation': 'delivery',
        'oral-films': 'delivery',
        'sublingual': 'delivery',
        'market-entry': 'regulatory',
        'industry-outlook': 'market',
    }
    return f"tag-{mapping.get(tag_slug, 'delivery')}"


def tag_label(tag_slug):
    """Human-readable tag label."""
    mapping = {
        'delivery-systems': 'Delivery Systems',
        'regulatory': 'Regulatory',
        'formulation': 'Formulation',
        'market-trends': 'Industry Trends',
        'pet-wellness': 'Pet Wellness',
        'dtc': 'DTC Strategy',
        'brand-strategy': 'Brand Strategy',
        'fda': 'FDA',
        'efsa': 'EFSA',
        'eu': 'EU Regulatory',
        'compliance': 'Compliance',
        'functional-beverage': 'Functional Beverage',
        'product-innovation': 'Product Innovation',
        'sleep-health': 'Sleep Health',
        'functional-powders': 'Functional Powders',
        'product-development': 'Product Dev',
        'flavor': 'Flavor Science',
        'companion-animal': 'Pet Health',
        'supplements': 'Supplements',
        'innovation': 'Innovation',
        'oral-films': 'Oral Films',
        'sublingual': 'Sublingual',
        'market-entry': 'Market Entry',
        'industry-outlook': 'Industry Outlook',
    }
    return mapping.get(tag_slug, tag_slug.replace('-', ' ').title())


# ── Page Wrappers ──

def page_head(title, description, canonical_url):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — SuppBridge Journal</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical_url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700;800&display=swap" rel="stylesheet">
{SITE_CSS}"""


def nav_html():
    return """<nav class="nav">
<div class="nav-inner">
<a href="/" class="nav-brand">
<img src="/images/logo.png" alt="SuppBridge">
<span>Innovation Partner</span>
</a>
<ul class="nav-links">
<li><a href="/#formats">Delivery Formats</a></li>
<li><a href="/#insights">Insights</a></li>
<li><a href="/#about">About</a></li>
<li><a href="/#contact">Contact</a></li>
</ul>
</div>
</nav>"""


def footer_html():
    return f"""<footer class="blog-footer">
<div class="container">
<p>&copy; {datetime.now().year} SuppBridge. Advanced Wellness Product Innovation &amp; Compliance Partner.</p>
<p><a href="/">Home</a> · <a href="/blog/">All Articles</a> · <a href="/#contact">Contact</a></p>
</div>
</footer>"""


def article_schema(title, date, description, slug, tags):
    tag_names = [tag_label(t) for t in tags]
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "datePublished": "{date}",
  "dateModified": "{date}",
  "description": "{description}",
  "url": "{SITE_URL}/blog/{slug}.html",
  "author": {{ "@type": "Person", "name": "Jun Lee" }},
  "publisher": {{ "@type": "Organization", "name": "SuppBridge" }},
  "keywords": "{', '.join(tag_names)}"
}}
</script>"""


# ── Build ──

def build():
    md_files = sorted(glob.glob(os.path.join(BLOG_DIR, "*.md")))
    articles = []

    for md_path in md_files:
        with open(md_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        fm, body = parse_frontmatter(md_text)
        slug = fm.get('slug', os.path.splitext(os.path.basename(md_path))[0])
        title = fm.get('title', slug)
        date = fm.get('date', '2026-01-01')
        tags = fm.get('tags', [])
        description = fm.get('description', '')
        primary_tag = tags[0] if tags else 'delivery-systems'
        tag_cls = tag_class(primary_tag)
        tag_lbl = tag_label(primary_tag)

        body_html = md_to_html(body)
        canonical = f"{SITE_URL}/blog/{slug}.html"
        og_image = fm.get('og_image', f"{SITE_URL}/images/blog-og.png")

        html = f"""{page_head(title, description, canonical)}
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:type" content="article">
{article_schema(title, date, description, slug, tags)}
</head>
<body>
{nav_html()}
<article>
<header class="article-hero">
<div class="container">
<span class="tag {tag_cls}">{tag_lbl}</span>
<h1>{title}</h1>
<p class="meta">{date}</p>
<p class="excerpt">{description}</p>
</div>
</header>
<div class="article-body">
<div class="container">
{body_html}
<div class="article-cta">
<p style="margin-bottom:14px;color:var(--muted);font-size:.92rem;">Ready to turn insights into action?</p>
<a href="/#contact">Start a Conversation →</a>
</div>
</div>
</div>
</article>
{footer_html()}
</body>
</html>"""

        out_path = os.path.join(BLOG_DIR, f"{slug}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓ {slug}.html")

        articles.append({
            'slug': slug, 'title': title, 'date': date, 'description': description,
            'tags': tags, 'primary_tag': primary_tag, 'tag_cls': tag_cls, 'tag_lbl': tag_lbl
        })

    # Sort by date descending
    articles.sort(key=lambda a: a['date'], reverse=True)

    # ── Blog Index ──
    cards = []
    for a in articles:
        cards.append(f"""<article class="blog-card">
<span class="tag {a['tag_cls']}">{a['tag_lbl']}</span>
<h2><a href="/blog/{a['slug']}.html">{a['title']}</a></h2>
<p class="desc">{a['description']}</p>
<p class="meta">{a['date']}</p>
</article>""")

    index_html = f"""{page_head("SuppBridge Journal — Wellness Product Innovation Insights", "Expert insights on supplement delivery systems, regulatory compliance, formulation science, and DTC wellness brand strategy.", f"{SITE_URL}/blog/")}
<meta property="og:title" content="SuppBridge Journal">
<meta property="og:description" content="Expert insights on supplement delivery systems, regulatory compliance, formulation science, and DTC wellness brand strategy.">
<meta property="og:image" content="{SITE_URL}/images/blog-og.png">
<meta property="og:url" content="{SITE_URL}/blog/">
<meta property="og:type" content="website">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "SuppBridge Journal",
  "description": "Expert insights on supplement delivery systems, regulatory compliance, formulation science, and DTC wellness brand strategy.",
  "url": "{SITE_URL}/blog/",
  "author": {{ "@type": "Person", "name": "Jun Lee" }},
  "publisher": {{ "@type": "Organization", "name": "SuppBridge" }}
}}
</script>
</head>
<body>
{nav_html()}
<header class="blog-hero">
<div class="container">
<h1>SuppBridge Journal</h1>
<p>Expert insights on supplement delivery systems, regulatory compliance, formulation science, and DTC wellness brand strategy.</p>
</div>
</header>
<div class="blog-list">
<div class="container">
{''.join(cards)}
</div>
</div>
{footer_html()}
</body>
</html>"""

    with open(os.path.join(BLOG_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"  ✓ index.html ({len(articles)} articles)")

    # ── Sitemap ──
    urls = [f"{SITE_URL}/blog/"]
    for a in articles:
        urls.append(f"{SITE_URL}/blog/{a['slug']}.html")

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        sitemap += f"  <url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n"
    sitemap += '</urlset>'

    with open(os.path.join(BLOG_DIR, "sitemap.xml"), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print(f"  ✓ sitemap.xml")

    # Save articles.json for index.html integration
    with open(os.path.join(BLOG_DIR, "articles.json"), 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"  ✓ articles.json")

    print(f"\n✅ Blog built: {len(articles)} articles in {BLOG_DIR}/\n   Deploy to suppbridge.com/blog/")


if __name__ == '__main__':
    build()
