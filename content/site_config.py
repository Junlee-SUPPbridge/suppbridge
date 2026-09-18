#!/usr/bin/env python3
"""Build-time site configuration.

One source for the few values that differ between local, staging and
production, and that must never be invented at build time.

Nothing here is a secret. When a value is absent, the feature it controls
is simply not emitted: a missing analytics ID produces a site with no
analytics at all, never a tag pointing at a property that does not exist.
"""

# ── Google Analytics 4 ──────────────────────────────────────────────────
# Measurement ID of the GA4 web data stream: "G-" followed by the stream's
# alphanumeric ID.
#
# EMPTY MEANS OFF. While this is empty:
#   * no page loads gtag.js and no event is sent,
#   * validate-site.py asserts that (a stray tag fails the build),
#   * the CTA/enquiry tracking script is not emitted either.
#
# Do not put a placeholder in here. A tag with a fake ID sends nothing
# useful and hides the fact that analytics is missing; an empty string
# leaves the gap visible, which is the point.
GA4_MEASUREMENT_ID = ""

# Host the analytics property is expected to report for. The validator uses
# it as a sanity check that the configured ID belongs to this site.
GA4_EXPECTED_HOST = "suppbridge.com"

# ── Enquiry tracking ────────────────────────────────────────────────────
# The project enquiry form posts natively to Formspree and Formspree
# redirects here on success (`_next`). Landing on this path is therefore
# the only reliable success signal a static site has — the POST itself
# navigates away and never returns the submitted values, which is also why
# no form field is ever sent to analytics.
ENQUIRY_SUCCESS_PATH = "/thanks.html"
