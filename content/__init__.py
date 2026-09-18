"""SuppBridge content metadata package.

Everything the site generator needs to know about *what exists* lives here,
separately from *how it renders*. `build-blog.py` reads this package and
emits the article pages, pillar pages, FAQ blocks, schema and sitemap.

Adding an article to the site is therefore three steps:

    1. write blog/<slug>.md with frontmatter
    2. add one entry to ARTICLE_META in this package
    3. run `python3 build-blog.py`

Step 3 then generates, without touching any HTML by hand:
    article page · cluster tag · pillar page listing · breadcrumbs ·
    canonical · related articles · pillar link block · intent-scaled CTA ·
    Article + BreadcrumbList schema · FAQ block + FAQPage schema ·
    blog index grouping · sitemap entries

This is deliberately plain Python in a static build, not a CMS. See
CONTENT-PLAN.md for the editorial roadmap that feeds it.
"""
