#!/usr/bin/env python3
"""Analytics for the static site: a GA4 loader plus PII-free event tracking.

Constraints this module exists to enforce
----------------------------------------
1. **Off means off.** With no measurement ID configured, nothing is
   emitted — no gtag.js request, no event, no residual script. A site that
   silently points analytics at a non-existent property is worse than a
   site with no analytics, because it looks finished.
2. **No personal data ever leaves the page.** The tracking script reads
   click targets and section ids. It never touches a form field: no value,
   no filename, no notes. `validate-site.py` re-checks the emitted block
   against FORBIDDEN_PAYLOAD_TOKENS, so the rule is enforced by the build
   rather than by reviewer memory.
3. **One implementation.** `build-blog.py` (generated pages) and
   `scripts/sync-chrome.py` (hand-authored pages) both call
   `head_block()`, so the two halves of the site cannot drift apart.

The block is bounded by HTML comment markers so the sync step can insert,
replace or remove it idempotently — turning analytics on or off is a
one-line config change plus a rebuild.
"""

import re

from content.site_config import GA4_MEASUREMENT_ID, ENQUIRY_SUCCESS_PATH

BEGIN_MARKER = "<!-- analytics:begin -->"
END_MARKER = "<!-- analytics:end -->"

BLOCK_RE = re.compile(re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER), re.S)
# Same match, but also eats the newline the insert added. Without it,
# turning analytics off restores the page minus the block and plus a blank
# line before </head> — a config flip that edits files it should not.
BLOCK_RE_WITH_NEWLINE = re.compile(
    re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?", re.S)

# Event and parameter names live here so the browser script, the validator
# and the reporting scripts all describe the same contract.
EVENT_CTA = "cta_click"
EVENT_ENQUIRY = "project_enquiry_submit"
CTA_PARAMS = ("cta_name", "cta_location", "page_path")
ENQUIRY_PARAMS = ("page_path",)

# Tokens that must not appear inside the emitted analytics block. These are
# the shapes a PII leak takes in practice: reading a field, serialising a
# form, or naming a personal field in a payload. Checked by validate-site.py
# against the block only — pages legitimately contain mailto: links and
# input elements, so a site-wide grep would be meaningless.
FORBIDDEN_PAYLOAD_TOKENS = (
    "FormData",
    ".value",
    "serialize",
    "email",
    "phone",
    "company",
    "notes",
    "gotcha",
    "querySelector('input",
    'querySelector("input',
)


def enabled():
    """True when a real measurement ID is configured."""
    return bool(GA4_MEASUREMENT_ID.strip())


# The event script. Kept as a plain template rather than an f-string: it is
# mostly braces, and doubling every one of them to satisfy an f-string is
# how a script like this gets silently mangled.
_EVENTS_JS = """(function(){
  'use strict';
  try {
    var PAGE = location.pathname;
    var ENQUIRY_PATH = '__ENQUIRY_PATH__';

    function send(name, params){
      if (typeof window.gtag !== 'function') return;
      var payload = { page_path: PAGE };
      if (params) {
        for (var k in params) {
          if (Object.prototype.hasOwnProperty.call(params, k) && params[k]) {
            payload[k] = params[k];
          }
        }
      }
      window.gtag('event', name, payload);
    }

    /* CTA name: the explicit data-cta label where an author pinned one,
       otherwise the link's own visible text. Trailing arrows are stripped
       so the same button does not report two different names depending on
       where it sits. */
    function ctaName(el){
      var explicit = el.getAttribute('data-cta');
      if (explicit) return explicit;
      var t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
      t = t.replace(/[\\u2192\\u00bb\\u203a>]+\\s*$/, '').trim();
      return t || 'unlabelled';
    }

    /* CTA location: the explicit data-cta-location where an author pinned
       one, otherwise the id of the enclosing landmark. Derived instead of
       hard-coded so a button added somewhere new cannot report a stale
       location. */
    function ctaLocation(el){
      var explicit = el.getAttribute('data-cta-location');
      if (explicit) return explicit;
      var host = el.closest ? el.closest('section[id], header[id], form[id], footer[id], nav[id]') : null;
      if (host) return host.id;
      if (el.closest && el.closest('footer')) return 'footer';
      if (el.closest && el.closest('nav')) return 'nav';
      return 'page';
    }

    /* One delegated listener covers every CTA on every page, including
       ones added later. Capture phase, so it fires even for links whose own
       handler calls preventDefault(). */
    document.addEventListener('click', function(e){
      var el = e.target && e.target.closest
        ? e.target.closest('a[data-cta], a.btn, button[data-cta]')
        : null;
      if (!el) return;
      if (el.type === 'submit') return;   /* an attempt is not a submission */
      send('cta_click', { cta_name: ctaName(el), cta_location: ctaLocation(el) });
    }, true);

    /* Enquiry success. The form posts natively to Formspree and Formspree
       redirects to the thank-you page on success, so arriving here is the
       success signal. No field is read or sent: the POST already navigated
       away, the values are gone, and those fields are personal by nature. */
    if (PAGE === ENQUIRY_PATH) send('project_enquiry_submit', null);
  } catch (err) { /* analytics must never break the page */ }
})();"""


def head_block():
    """The analytics block for `<head>`, or '' when analytics is off."""
    if not enabled():
        return ""
    gid = GA4_MEASUREMENT_ID.strip()
    loader = (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
        "<script>\n"
        "window.dataLayer=window.dataLayer||[];\n"
        "function gtag(){dataLayer.push(arguments);}\n"
        "gtag('js',new Date());\n"
        f"gtag('config','{gid}');\n"
        "</script>"
    )
    events = (
        "<script>\n"
        + _EVENTS_JS.replace("__ENQUIRY_PATH__", ENQUIRY_SUCCESS_PATH)
        + "\n</script>"
    )
    return f"{BEGIN_MARKER}\n{loader}\n{events}\n{END_MARKER}"


def splice(html):
    """Insert, replace or remove the marked block. Returns `(html, changed)`.

    Used by scripts/sync-chrome.py for the hand-authored pages. Removing the
    block when analytics is turned off is deliberate: a config flip has to
    clean up after itself, or the site keeps shipping a dead tag.
    """
    block = head_block()
    found = BLOCK_RE.search(html)

    if found:
        if block and found.group(0) == block:
            return html, False
        if block:
            return BLOCK_RE.sub(lambda _: block, html, count=1), True
        stripped = BLOCK_RE_WITH_NEWLINE.sub("", html, count=1)
        return re.sub(r"\n{3,}", "\n\n", stripped), True

    if not block:
        return html, False

    idx = html.find("</head>")
    if idx == -1:
        return html, False
    return html[:idx] + block + "\n" + html[idx:], True
