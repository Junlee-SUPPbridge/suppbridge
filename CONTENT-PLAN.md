# SuppBridge Content Plan — Buyer-Problem SEO

**Purpose:** shift the blog from generic supplement-industry commentary to content that captures buyers who are actively sourcing in China and are worried about getting it wrong.

**Why this works commercially:** the reader arriving from these searches has a live project and a specific fear. The matching commercial offer is the **Supplier Review** — a low-commitment entry point that does not require them to book a call or abandon a supplier they have already found.

**Conversion path for every article:**
`organic search → article → "Request a Supplier Review" (pre-footer CTA) → /china-supplement-sourcing.html#review → form → /thanks.html`

---

## Status

| # | Topic | Status | Slug |
|---|---|---|---|
| 1 | How to Verify a China Supplement Manufacturer Before Paying | **Published** | `verify-china-supplement-manufacturer` |
| 2 | How to Tell If a Chinese Supplier Is Actually a Factory | **Published** | `chinese-supplier-factory-or-trading-company` |
| 3 | How to Verify a COA From a Chinese Supplier | **Published** | `verify-coa-chinese-supplement-supplier` |
| 4 | Alibaba Supplement Sourcing: What Buyers Should Verify | **Published** | `alibaba-supplement-sourcing-what-to-verify` |
| 5 | What to Check Before Buying Supplement Ingredients From China | Planned | `buying-supplement-ingredients-from-china` |
| 6 | Why a GMP Certificate Does Not Prove Your Ingredient Is Authentic | Planned | `gmp-certificate-does-not-prove-authenticity` |
| 7 | China Supplement Manufacturer vs Trading Company (comparison-led) | Planned — *partial coverage exists in #2; consider a comparison-table version targeting a distinct query* | `manufacturer-vs-trading-company-china` |
| 8 | What Questions Should You Ask a Chinese Supplement Factory? | Planned | `questions-to-ask-chinese-supplement-factory` |
| 9 | How to Source Supplement Ingredients in China Without Getting Burned | Planned | `source-supplement-ingredients-china` |
| 10 | What to Do When Your China Supplement Sample Doesn't Match Production | Planned | `sample-doesnt-match-production` |

**Published dates:** #1 2026-09-16 · #2 2026-09-11 · #3 2026-09-05 · #4 2026-08-28

---

## Briefs for the remaining six

### #5 — What to Check Before Buying Supplement Ingredients From China
- **Target intent:** "supplement ingredient sourcing China", "buy supplement ingredients from China", "China ingredient supplier"
- **Why it matters:** closest to the top of the funnel but still problem-aware; high volume relative to the finished-product queries.
- **Outline:** why ingredient quotes aren't comparable → build your own specification first → extract ratio vs standardisation → assay method as cost driver → carrier and grade → documentation set (spec, COA, MSDS/SDS, allergen, origin, non-GMO) → sampling and retention → regulatory screening per market → like-for-like comparison table → when to commission independent testing
- **Internal links:** #3 (COA), #1 (manufacturer verification), service page anchor `/#services`
- **CTA variant:** "Send us your ingredient list and current quotes"

### #6 — Why a GMP Certificate Does Not Prove Your Ingredient Is Authentic
- **Target intent:** "GMP certificate supplement meaning", "does GMP guarantee quality", "is GMP the same as FDA approval"
- **Why it matters:** high-confusion topic with strong search demand and low-quality competition; positions SuppBridge as the honest voice.
- **Outline:** what GMP covers (systems, processes, site) → what it does not cover (identity of a given lot) → why upstream substitution defeats downstream certification → FDA does not issue GMP certificates; registration ≠ approval → certificate holder vs site vs product → what actually establishes identity (validated analytical method on a controlled sample) → how to structure testing scope → what to write into your specification
- **Internal links:** #3 (COA), #1 (verification sequence)
- **Compliance note:** must stay factual. No claims about suppliers generally being dishonest.

### #7 — China Supplement Manufacturer vs Trading Company
- **Target intent:** "supplement manufacturer vs trading company", "Chinese trading company supplement"
- **Why it matters:** already partly served by #2 — build this as a **comparison-table-first** piece targeting the distinct query, and add a cost/benefit decision framework.
- **Outline:** definitions → table (capability, price transparency, MOQ flexibility, English support, accountability, IP ownership, change control) → when each is the better choice → how price layers accumulate → questions to identify which you're dealing with → contractual protections for either case
- **Internal links:** #2 (factory signals), #1 (verification), `/#services`
- **Canonical note:** ensure this and #2 do not cannibalise. If they overlap heavily after drafting, merge and 301 the weaker slug.

### #8 — What Questions Should You Ask a Chinese Supplement Factory?
- **Target intent:** "questions to ask supplement manufacturer", "supplier questionnaire supplement", "manufacturer audit questions"
- **Why it matters:** highly linkable and highly saveable — a natural resource that earns backlinks.
- **Outline:** why questions beat documents → company & identity questions → licence & certification questions → capability questions (dosage form, batch size, yield, changeover) → documentation & QC questions → commercial questions (MOQ, lead time, payment, change control) → the five questions most likely to get a revealing answer → a copy-ready questionnaire
- **Internal links:** #1, #2, #5
- **Deliverable bonus:** consider publishing a downloadable questionnaire PDF and capturing email for it — the highest-intent list-building asset in this set.

### #9 — How to Source Supplement Ingredients in China Without Getting Burned
- **Target intent:** "supplement sourcing agent China", "how to source supplements from China", "China supplement sourcing agent"
- **Why it matters:** the closest match to the commercial service page; should be the strongest internal-link bridge to `/china-supplement-sourcing.html`.
- **Outline:** the three mistakes that cause most failures (no written specification; verification after payment; no QC doc requirement) → a staged process (define → identify → verify → sample → contract → production → ship) → what to do at each stage → how to choose between a platform, an agent and an independent partner → cost structure of each model
- **Internal links:** all four published articles plus `/china-supplement-sourcing.html`
- **Note:** avoid duplicating #5; #9 is process, #5 is specification-level detail.

### #10 — What to Do When Your China Supplement Sample Doesn't Match Production
- **Target intent:** "sample doesn't match production", "supplement sample vs production batch", "supplier used different ingredients"
- **Why it matters:** pure problem-stage intent — the reader already has a live dispute. Highest conversion rate expected in the set, lowest search volume.
- **Outline:** why this happens (pilot vs production line, hand-made samples, substituted raw material, changed carrier, different capsule or film) → immediate steps (stop, document, photograph, retain samples, compare against the approved spec) → what to ask the supplier in writing → technical comparison options (send both to one lab on the same method) → when it's a fixable process issue vs a material breach → commercially, what to negotiate → how to prevent it next time (sample approval protocol, retained reference sample, change control)
- **Internal links:** #3, #1, `/#services`
- **Compliance note:** keep it factual and remedy-oriented, not accusatory.

---

## Publishing rules for all content

1. **Never publish a claim you cannot stand behind.** No invented figures, savings, volumes, timelines or client names.
2. **No accusations against platforms or suppliers as a category.** Frame everything as buyer risk and verifiable evidence.
3. **Never promise guarantees.** Use: supplier verification, due diligence, documentation review, manufacturer identification, capability assessment, project-specific screening, risk reduction. Never: "guaranteed authentic", "100% verified", "we eliminate risk".
4. **Precise language over dramatic language.** The audience is a founder about to spend real money; precision signals competence.
5. **Every article ends with the Supplier Review CTA** — generated automatically by `build-blog.py`.
6. **Every article links to at least two other articles and one commercial page.** Internal linking is generated for related reading; the commercial link is added automatically.

---

## Measurement

There is currently **no analytics on the site**. Until that is added, none of this can be evaluated.

When analytics is in place, track for each article:

| Metric | Why |
|---|---|
| Organic sessions | Is the topic actually being searched? |
| Scroll depth past 50% | Is the content being read or bounced? |
| Click-through to `#review` CTA | Does the CTA convert intent? |
| Form submissions attributed to `/china-supplement-sourcing.html` | Commercial value |
| Search Console: impressions vs CTR per query | Whether title/meta match intent |
| Search Console: queries the page ranks for | Discover unplanned topics worth writing |

`scripts/gsc-fetcher.py` already pulls Search Console data via service account and can supply the last two without any client-side analytics.

---

## Suggested cadence

- **Publish 2 remaining articles per month**, prioritising #9 and #8 (strongest internal-link and link-earning value), then #6, #5, #10, #7.
- **Revisit published articles quarterly** — add a "what we learned from reader questions" section, which refreshes the page and improves rankings without rewriting.
- **Add FAQ schema to the top three articles** once they have Search Console impressions showing question-style queries.
