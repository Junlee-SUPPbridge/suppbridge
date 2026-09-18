#!/usr/bin/env python3
"""Build static blog HTML pages from Markdown files.

Usage: python3 build-blog.py
Reads blog/*.md -> generates blog/*.html + blog/index.html + blog/sitemap.xml
                 + blog/articles.json

Notes
-----
* Blog pages use the SAME stylesheet as the rest of the site (/styles/main.css).
  Blog-specific rules inside that file are scoped under `body.page-blog`, so
  they can never leak into the homepage layout again.
* Blog pages carry `class="page-blog"` on <body> for exactly that reason.
* Every article ends with a commercial CTA (supplier review), not a generic
  "contact us" link, so SEO traffic has a real conversion path.
"""

import os, re, glob, json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(BASE_DIR, "blog")
SITE_URL = "https://suppbridge.com"
CSS_URL = "/styles/main.css"

# Contact / conversion destinations
CONTACT = "/#start-project"
REVIEW = "/china-supplement-sourcing.html#review"


# ── Markdown -> HTML converter (no external deps) ──

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

        # Blank line
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
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
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


# Tag slug -> CSS class / human label.
# Buyer-problem tags (sourcing, verification, ...) are the growth area; the
# legacy topic tags are kept so existing articles keep rendering correctly.
TAG_CLASS = {
    'delivery-systems': 'delivery', 'regulatory': 'regulatory',
    'formulation': 'formulation', 'market-trends': 'market',
    'pet-wellness': 'pet', 'dtc': 'market', 'brand-strategy': 'market',
    'fda': 'regulatory', 'efsa': 'regulatory', 'eu': 'regulatory',
    'compliance': 'regulatory', 'functional-beverage': 'delivery',
    'product-innovation': 'delivery', 'sleep-health': 'formulation',
    'functional-powders': 'formulation', 'product-development': 'formulation',
    'flavor': 'formulation', 'companion-animal': 'pet', 'supplements': 'pet',
    'innovation': 'delivery', 'oral-films': 'delivery', 'sublingual': 'delivery',
    'market-entry': 'regulatory', 'industry-outlook': 'market',
    # ── buyer-problem / sourcing cluster ──
    'sourcing': 'sourcing', 'china-sourcing': 'sourcing', 'alibaba': 'sourcing',
    'factory': 'sourcing', 'trading-company': 'sourcing',
    'supplier-verification': 'verification', 'manufacturer-verification': 'verification',
    'coa': 'verification', 'due-diligence': 'verification',
    'quality': 'verification', 'procurement': 'sourcing',
    # ── V2.1 content clusters (product / ingredient / manufacturing / supply chain / consulting) ──
    'product-strategy': 'product', 'product': 'product',
    'ingredient-sourcing': 'ingredient', 'ingredients': 'ingredient',
    'botanical-extract': 'ingredient', 'specification': 'ingredient',
    'manufacturing': 'manufacturing', 'manufacturer': 'manufacturing',
    'oem': 'manufacturing', 'moq': 'manufacturing', 'packaging': 'manufacturing',
    'supply-chain': 'supplychain', 'cost': 'supplychain',
    'supplier-management': 'supplychain', 'project-management': 'supplychain',
    'industry-consulting': 'consulting', 'market-entry-strategy': 'consulting',
    'china': 'consulting',
}

TAG_LABEL = {
    'delivery-systems': 'Delivery Systems', 'regulatory': 'Regulatory',
    'formulation': 'Formulation', 'market-trends': 'Industry Trends',
    'pet-wellness': 'Pet Wellness', 'dtc': 'DTC Strategy',
    'brand-strategy': 'Brand Strategy', 'fda': 'FDA', 'efsa': 'EFSA',
    'eu': 'EU Regulatory', 'compliance': 'Compliance',
    'functional-beverage': 'Functional Beverage',
    'product-innovation': 'Product Innovation', 'sleep-health': 'Sleep Health',
    'functional-powders': 'Functional Powders',
    'product-development': 'Product Dev', 'flavor': 'Flavor Science',
    'companion-animal': 'Pet Health', 'supplements': 'Supplements',
    'innovation': 'Innovation', 'oral-films': 'Oral Films',
    'sublingual': 'Sublingual', 'market-entry': 'Market Entry',
    'industry-outlook': 'Industry Outlook',
    # ── buyer-problem / sourcing cluster ──
    'sourcing': 'Sourcing', 'china-sourcing': 'China Sourcing',
    'alibaba': 'Alibaba Sourcing', 'factory': 'Factory Checks',
    'trading-company': 'Trading Companies',
    'supplier-verification': 'Supplier Verification',
    'manufacturer-verification': 'Manufacturer Verification',
    'coa': 'COA & Documents', 'due-diligence': 'Due Diligence',
    'quality': 'Quality', 'procurement': 'Procurement',
    # ── V2.1 content clusters ──
    'product-strategy': 'Product Development', 'product': 'Product Development',
    'ingredient-sourcing': 'Ingredient Sourcing', 'ingredients': 'Ingredient Sourcing',
    'botanical-extract': 'Botanical Extracts', 'specification': 'Specifications',
    'manufacturing': 'Manufacturing', 'manufacturer': 'Manufacturer Selection',
    'oem': 'OEM / ODM', 'moq': 'MOQ & Cost', 'packaging': 'Packaging',
    'supply-chain': 'Supply Chain', 'cost': 'Cost Optimization',
    'supplier-management': 'Supplier Management', 'project-management': 'China Project Management',
    'industry-consulting': 'Industry Consulting', 'market-entry-strategy': 'Market Strategy',
    'china': 'China',
}


def tag_class(tag_slug):
    return f"tag-{TAG_CLASS.get(tag_slug, 'sourcing')}"


def tag_label(tag_slug):
    return TAG_LABEL.get(tag_slug, tag_slug.replace('-', ' ').title())


# ── Shared page chrome ──

SITE_NAV_LINKS = [
    ("How We Help", "/#services"),
    ("Our Process", "/#process"),
    ("Projects", "/#projects"),
    ("About Jun", "/#founder"),
    ("Insights", "/blog/"),
]


def page_head(title, description, canonical_url):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical_url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{CSS_URL}">
<link rel="preload" href="{CSS_URL}" as="style">"""


def nav_html(current="blog"):
    items = "".join(
        f'<li><a href="{url}"{" aria-current=\"page\"" if label == current else ""}>{label}</a></li>'
        for label, url in SITE_NAV_LINKS
    )
    mobile = "".join(f'<a href="{url}">{label}</a>' for label, url in SITE_NAV_LINKS)
    return f"""<nav class="nav" id="nav">
<div class="nav-wrap">
<a href="/" class="nav-brand">
<img src="/images/logo.png" alt="SuppBridge" width="121" height="56">
<span class="nav-brand-text"><span>China Supplement Industry Advisor</span></span>
</a>
<ul class="nav-links">{items}</ul>
<a href="{CONTACT}" class="btn btn--primary btn--nav nav-cta-desktop">Discuss Your Project</a>
<button class="nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false" aria-controls="mobileMenu">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
</button>
</div>
<div class="mobile-menu" id="mobileMenu">
{mobile}
<a href="{CONTACT}" style="color:var(--teal);font-weight:700;">Discuss Your Project →</a>
</div>
</nav>"""


FOOTER_NAV = [
    ("How We Help", "/#services"),
    ("Our Process", "/#process"),
    ("Long-Term Partnership", "/#long-term"),
    ("Projects", "/#projects"),
    ("About Jun", "/#founder"),
    ("Product Formats", "/product-formats.html"),
    ("Supplier Due Diligence", "/china-supplement-sourcing.html"),
    ("Insights", "/blog/"),
    ("FAQ", "/#faq"),
    ("Contact", CONTACT),
]


def footer_html():
    links = " · ".join(f'<a href="{url}">{label}</a>' for label, url in FOOTER_NAV)
    year = datetime.now().year
    return f"""<footer class="blog-footer">
<div class="container">
<p>&copy; {year} SuppBridge. China supplement industry advisor &amp; supply partner.</p>
<p>{links}</p>
</div>
</footer>"""


NAV_SCRIPT = """<script>
(function(){
  var nav=document.getElementById('nav');
  var toggle=document.getElementById('navToggle');
  var menu=document.getElementById('mobileMenu');
  function onScroll(){ if(nav) nav.classList.toggle('scrolled', window.scrollY>24); }
  window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  if(toggle&&menu){
    toggle.addEventListener('click',function(){
      var open=menu.classList.toggle('active');
      toggle.setAttribute('aria-expanded', open?'true':'false');
      toggle.setAttribute('aria-label', open?'Close menu':'Open menu');
    });
  }
  document.querySelectorAll('a[href^="#"]').forEach(function(a){
    a.addEventListener('click',function(e){
      var id=this.getAttribute('href');
      if(id==='#'||id.length<2) return;
      var t=document.querySelector(id);
      if(!t) return;
      e.preventDefault();
      window.scrollTo({top:t.getBoundingClientRect().top+window.pageYOffset-78, behavior:'smooth'});
      if(menu) menu.classList.remove('active');
    });
  });
})();
</script>"""


def breadcrumb_schema(title, canonical):
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "{SITE_URL}/" }},
    {{ "@type": "ListItem", "position": 2, "name": "Insights", "item": "{SITE_URL}/blog/" }},
    {{ "@type": "ListItem", "position": 3, "name": "{json_esc(title)}", "item": "{canonical}" }}
  ]
}}
</script>"""


def article_schema(title, date, description, slug, tags, og_image):
    tag_names = [tag_label(t) for t in tags]
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "{json_esc(title)}",
  "datePublished": "{date}",
  "dateModified": "{date}",
  "description": "{json_esc(description)}",
  "url": "{SITE_URL}/blog/{slug}.html",
  "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{SITE_URL}/blog/{slug}.html" }},
  "image": "{og_image}",
  "author": {{ "@type": "Person", "name": "Jun Lee", "jobTitle": "Supplement Product & Supply Chain Strategist", "url": "{SITE_URL}/#founder" }},
  "publisher": {{ "@type": "Organization", "name": "SuppBridge", "url": "{SITE_URL}" }},
  "keywords": "{json_esc(', '.join(tag_names))}"
}}
</script>"""


def json_esc(text):
    """Escape a string for safe embedding inside a JSON string literal."""
    return (text or '').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')


def article_cta():
    """Commercial end-of-article CTA.

    Points at the project enquiry rather than a standalone supplier review, so
    the funnel is content -> lead -> project (§4 of the V2.1 brief).
    """
    return f"""<div class="article-cta">
<p class="ac-kicker">Need more than a supplier check?</p>
<h3>If you are building or sourcing a supplement in China, we can look at the whole project.</h3>
<p>Formulation, ingredients, manufacturer selection, sampling, production and supply-chain setup — reviewed by someone on your side of the table. Send us the brief, the formula or the quotation and we will tell you what is realistic and what needs checking first.</p>
<div class="ac-actions">
<a class="ac-btn" href="{CONTACT}">Discuss Your Project →</a>
<a class="ac-btn ac-btn--ghost" href="{REVIEW}">Supplier due diligence</a>
</div>
</div>"""


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
        primary_tag = tags[0] if tags else 'sourcing'
        tag_cls = tag_class(primary_tag)
        tag_lbl = tag_label(primary_tag)

        body_html = md_to_html(body)
        canonical = f"{SITE_URL}/blog/{slug}.html"
        og_image = fm.get('og_image', f"{SITE_URL}/images/blog-og.png")
        page_title = f"{title} — SuppBridge Insights"

        # Related articles: shared tags first, most recently published first.
        related = []
        for other in articles:
            common = set(tags) & set(other['tags'])
            if other['slug'] != slug and common:
                related.append((other['slug'], other['title'], len(common)))
        related.sort(key=lambda x: -x[2])
        related_links = related[:3]
        # Always give the reader a commercial next step alongside related reading.
        related_links.append(('/china-supplement-sourcing.html#alibaba-review',
                              'China Supplement Sourcing & Manufacturer Verification', 0))
        related_articles = '\n'.join(
            f'<li><a href="/blog/{s}.html">{t}</a></li>' if not s.startswith('/')
            else f'<li><a href="{s}">{t}</a></li>'
            for s, t, _ in related_links
        )

        html = f"""{page_head(page_title, description, canonical)}
<meta property="og:title" content="{json_esc(title)}">
<meta property="og:description" content="{json_esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SuppBridge">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{json_esc(title)}">
<meta name="twitter:description" content="{json_esc(description)}">
<meta name="twitter:image" content="{og_image}">
{article_schema(title, date, description, slug, tags, og_image)}
{breadcrumb_schema(title, canonical)}
</head>
<body class="page-blog">
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
{article_cta()}
<div class="related-reading">
<h3>Related Reading</h3>
<ul>
{related_articles}
</ul>
</div>
</div>
</div>
</article>
{footer_html()}
{NAV_SCRIPT}
</body>
</html>"""

        with open(os.path.join(BLOG_DIR, f"{slug}.html"), 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  + {slug}.html")

        articles.append({
            'slug': slug, 'title': title, 'date': date, 'description': description,
            'tags': tags, 'primary_tag': primary_tag, 'tag_cls': tag_cls, 'tag_lbl': tag_lbl
        })

    articles.sort(key=lambda a: a['date'], reverse=True)

    # ── Blog index ──
    cards = '\n'.join(f"""<article class="blog-card">
<span class="tag {a['tag_cls']}">{a['tag_lbl']}</span>
<h2><a href="/blog/{a['slug']}.html">{a['title']}</a></h2>
<p class="desc">{a['description']}</p>
<p class="meta">{a['date']}</p>
</article>""" for a in articles)

    index_description = ("Practical guides for brands buying supplements in China — supplier verification, "
                         "manufacturer due diligence, ingredient sourcing and regulatory questions, written from the buyer's side.")
    index_html = f"""{page_head("SuppBridge Insights — Buying Supplements in China", index_description, f"{SITE_URL}/blog/")}
<meta property="og:title" content="SuppBridge Insights — Buying Supplements in China">
<meta property="og:description" content="{json_esc(index_description)}">
<meta property="og:image" content="{SITE_URL}/images/blog-og.png">
<meta property="og:url" content="{SITE_URL}/blog/">
<meta property="og:type" content="website">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "SuppBridge Insights",
  "description": "{json_esc(index_description)}",
  "url": "{SITE_URL}/blog/",
  "author": {{ "@type": "Person", "name": "Jun Lee", "url": "{SITE_URL}/#founder" }},
  "publisher": {{ "@type": "Organization", "name": "SuppBridge", "url": "{SITE_URL}" }}
}}
</script>
</head>
<body class="page-blog">
{nav_html()}
<header class="blog-hero">
<div class="container">
<h1>Building Supplements in China — Industry Notes from the Inside</h1>
<p>Practical guides on product development, ingredient sourcing, manufacturing and supply-chain management in China — written for brand owners, not for procurement departments.</p>
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
{cards}
</div>
</div>
{footer_html()}
{NAV_SCRIPT}
</body>
</html>"""

    with open(os.path.join(BLOG_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"  + index.html ({len(articles)} articles)")

    # ── Sitemap ──
    urls = [f"{SITE_URL}/blog/"] + [f"{SITE_URL}/blog/{a['slug']}.html" for a in articles]
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for url in urls:
        sitemap += f"  <url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n"
    sitemap += '</urlset>'
    with open(os.path.join(BLOG_DIR, "sitemap.xml"), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print("  + sitemap.xml")

    with open(os.path.join(BLOG_DIR, "articles.json"), 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("  + articles.json")

    print(f"\nDone: {len(articles)} articles in blog/  ->  deploy to suppbridge.com/blog/")


if __name__ == '__main__':
    build()
