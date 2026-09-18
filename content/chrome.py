#!/usr/bin/env python3
"""Shared page chrome: navigation, footer and the icon symbols they need.

Single source of truth. Both `build-blog.py` (generated pages) and
`scripts/sync-chrome.py` (hand-authored pages) import from here, so a
pillar rename or a CTA change propagates everywhere from one edit.

Nothing in this module knows about articles or pillars beyond the
taxonomy's own labels.
"""

import html as html_lib
from datetime import datetime

from content.taxonomy import SITE_URL, CONTACT, PILLARS, PILLAR_ORDER


def esc(text):
    return html_lib.escape(text or "", quote=True)


# Primary destination for every "Discuss Your Project" action on the site.
NAV_SIMPLE = [
    ("How We Help", "/#value"),
    ("Our Process", "/#process"),
    ("About Jun", "/#founder"),
    ("Insights", "/blog/"),
]

FOOTER_COMPANY = [
    ("How We Help", "/#value"),
    ("Our Process", "/#process"),
    ("Long-Term Partnership", "/#long-term"),
    ("Project Experience", "/#experience"),
    ("About Jun", "/#founder"),
    ("Insights", "/blog/"),
    ("FAQ", "/#faq"),
]

FOOTER_MORE = [
    ("Product Formats", "/product-formats.html"),
    ("Supplier Due Diligence", "/china-supplement-sourcing.html"),
    ("Regulatory", "/regulatory/"),
    ("Email", "mailto:Jun@suppbridge.com"),
]


def expertise_dropdown():
    items = "".join(
        f'<a href="{PILLARS[k]["url"]}">'
        f'<span class="nd-label">{esc(PILLARS[k]["nav_title"])}</span>'
        f'<span class="nd-desc">{esc(PILLARS[k]["nav_desc"])}</span></a>'
        for k in PILLAR_ORDER
    )
    return (
        '<li class="nav-drop">'
        '<button class="nav-drop-btn" type="button" aria-expanded="false" '
        'aria-controls="expertiseMenu">Expertise'
        '<svg><use href="#i-chev"/></svg></button>'
        f'<div class="nav-drop-panel" id="expertiseMenu">{items}</div>'
        '</li>'
    )


def nav_block(current_root=False):
    """Navigation. `current_root=True` rewrites the homepage anchors from
    `/#value` to `#value` so that on the homepage they still scroll smoothly
    instead of triggering a full re-navigation to `/`."""
    desktop = (
        f'<li><a href="{NAV_SIMPLE[0][1]}">{NAV_SIMPLE[0][0]}</a></li>'
        + expertise_dropdown()
        + "".join(f'<li><a href="{u}">{l}</a></li>' for l, u in NAV_SIMPLE[1:])
    )
    mobile = (
        f'<a href="{NAV_SIMPLE[0][1]}">{NAV_SIMPLE[0][0]}</a>'
        '<span class="mm-group">Expertise</span>'
        + "".join(
            f'<a href="{PILLARS[k]["url"]}" class="mm-sub">{esc(PILLARS[k]["nav_title"])}</a>'
            for k in PILLAR_ORDER
        )
        + "".join(f'<a href="{u}">{l}</a>' for l, u in NAV_SIMPLE[1:])
    )
    html = f"""<nav class="nav" id="nav">
<div class="nav-wrap">
<a href="/" class="nav-brand">
<img src="/images/logo.png" alt="SuppBridge" width="121" height="56">
<span class="nav-brand-text"><span>Product &amp; Supply Chain Advisor</span></span>
</a>
<ul class="nav-links">{desktop}</ul>
<a href="{CONTACT}" class="btn btn--primary btn--nav nav-cta-desktop">Discuss Your Project</a>
<button class="nav-toggle" id="navToggle" aria-label="Open menu" aria-expanded="false" aria-controls="mobileMenu">
<svg><use href="#i-menu"/></svg>
</button>
</div>
<div class="mobile-menu" id="mobileMenu">
{mobile}
<a href="{CONTACT}" style="color:var(--gold-ink);font-weight:700;">Discuss Your Project →</a>
</div>
</nav>"""
    return _rootify(html) if current_root else html


def _rootify(html):
    """Turn `href="/#x"` into `href="#x"` for the page that owns those anchors."""
    return html.replace('href="/#', 'href="#')


# Icon symbols the shared chrome depends on. Any page carrying the nav must
# define these in its inline sprite or the icons render empty.
SPRITE_SYMBOLS = [
    '<symbol id="i-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></symbol>',
    '<symbol id="i-menu" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></symbol>',
]

NAV_SPRITE = (
    '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">\n'
    '<symbol id="i-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></symbol>\n'
    '<symbol id="i-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>\n'
    '<symbol id="i-menu" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></symbol>\n'
    '</svg>'
)


def nav_html():
    """Sprite + navigation, for pages that need both."""
    return NAV_SPRITE + "\n" + nav_block()


def footer_block(current_root=False):
    year = datetime.now().year
    expertise = "".join(
        f'<a href="{PILLARS[k]["url"]}">{esc(PILLARS[k]["nav_title"])}</a>' for k in PILLAR_ORDER
    )
    company = "".join(f'<a href="{u}">{l}</a>' for l, u in FOOTER_COMPANY)
    more = "".join(f'<a href="{u}">{l}</a>' for l, u in FOOTER_MORE)
    html = f"""<footer class="site-footer">
<div class="container">
<div class="footer-inner">
<div class="footer-brand">
<img src="/images/logo.png" alt="SuppBridge" width="121" height="56">
<span>Supplement product &amp; supply-chain advisor. Product development, ingredient sourcing, manufacturer selection and long-term China supply-chain management &mdash; with China as our core sourcing and manufacturing network, and other markets evaluated when a project requires it.</span>
</div>
<div class="footer-cols">
<div class="footer-col"><h4>Expertise</h4><nav aria-label="Expertise">{expertise}</nav></div>
<div class="footer-col"><h4>Company</h4><nav aria-label="Company">{company}</nav></div>
<div class="footer-col"><h4>More</h4><nav aria-label="More">{more}</nav></div>
</div>
</div>
<div class="footer-bottom">
<div>&copy; {year} SuppBridge. All rights reserved.</div>
<div><a href="mailto:Jun@suppbridge.com">Jun@suppbridge.com</a></div>
</div>
<p class="footer-legal">SuppBridge is an independent product, sourcing and supply-chain advisory partner. We are not affiliated with any marketplace or manufacturing group, and we do not provide guarantees of supplier conduct, ingredient authenticity or product quality. Verification and due-diligence findings are project-specific and provided in writing.</p>
</div>
</footer>"""
    return _rootify(html) if current_root else html


# Script shared by every page that carries the chrome: nav scroll state,
# mobile menu, expertise dropdown, reveal-on-scroll, smooth anchors.
NAV_SCRIPT = """<script>
(function(){
  'use strict';
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
  var drop=document.querySelector('.nav-drop-btn');
  if(drop){
    drop.addEventListener('click',function(e){
      e.preventDefault();
      var open = drop.getAttribute('aria-expanded')==='true';
      drop.setAttribute('aria-expanded', open?'false':'true');
    });
    document.addEventListener('keydown',function(e){
      if(e.key==='Escape') drop.setAttribute('aria-expanded','false');
    });
  }
  var reveals=document.querySelectorAll('.reveal');
  if('IntersectionObserver' in window){
    var obs=new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('visible'); obs.unobserve(e.target); } });
    },{threshold:0.05,rootMargin:'0px 0px -28px 0px'});
    reveals.forEach(function(el){ obs.observe(el); });
  } else {
    reveals.forEach(function(el){ el.classList.add('visible'); });
  }
  var NAV_OFFSET=78;
  document.querySelectorAll('a[href^="#"]').forEach(function(a){
    a.addEventListener('click',function(e){
      var id=this.getAttribute('href');
      if(id==='#'||id.length<2) return;
      var t=document.querySelector(id);
      if(!t) return;
      e.preventDefault();
      window.scrollTo({top:t.getBoundingClientRect().top+window.pageYOffset-NAV_OFFSET, behavior:'smooth'});
      if(menu) menu.classList.remove('active');
      if(history.pushState) history.pushState(null,'',id);
    });
  });
})();
</script>"""
