# SuppBridge Content Plan — Industry Advisory Clusters

**Purpose:** the blog supports the positioning *China Supplement Industry Advisor & Supply Partner*. It publishes work that demonstrates product-development, sourcing, manufacturing and supply-chain judgement — not marketplace anxiety.

**Cluster taxonomy** — each cluster is also an SEO pillar page (§17). The pillar URL is derived from the cluster key, so this table *is* the site's information architecture:

| Cluster key | Pillar URL | HTML tag class | What it proves |
|---|---|---|---|
| `product` | `/product-development/` | `tag-product` | We can make product decisions, not just source |
| `ingredient` | `/ingredient-sourcing/` | `tag-ingredient` | We understand specifications and comparability |
| `manufacturing` | `/supplement-manufacturing/` | `tag-manufacturing` | We understand plants, MOQ and production reality |
| `supply` | `/china-supplement-supply-chain/` | `tag-supplychain` | We can run an ongoing relationship, not a transaction |
| `consulting` | `/supplement-industry-consulting/` | `tag-consulting` | We know where foreign brands get China wrong |

**Architecture — metadata-first, not a CMS.** All content metadata lives in `content/taxonomy.py`; `build-blog.py` reads it and emits every derived artefact. Publishing an article is three steps:

1. write `blog/<slug>.md` with frontmatter
2. add one object to `ARTICLE_META` in `content/taxonomy.py`
3. run `python3 build-blog.py` then `python3 scripts/sync-chrome.py`

Step 3 generates, with no hand-edited HTML: article page · cluster tag · breadcrumb markup **and** BreadcrumbList schema · canonical · the pillar link block · related articles · an intent-scaled CTA · Article schema · FAQ block + FAQPage schema (only when a visible FAQ exists) · blog-index grouping · pillar-page listing · sitemap entries · `blog/articles.json`.

`ARTICLE_META` fields: `cluster` (required, drives `pillar`), `commercial_intent` (`high`/`medium`/`low`, drives CTA weight), `search_intent`, `entities`, `secondary`, `featured`. `pillar` is **derived** from `cluster` by `article_meta()` rather than stored — duplicating it would only create a way for the two to disagree.

Two guard scripts keep this honest and are worth running before any deploy:

| Script | What it catches |
|---|---|
| `scripts/validate-site.py` | broken internal links & anchors · missing/duplicate canonical, title, description · missing schema for the page's kind · FAQPage schema without a visible FAQ · orphan `.md` with no `ARTICLE_META` · pillar URL that has no generated page · every forbidden claim |
| `scripts/sync-chrome.py --check` | nav/footer drift between the generated pages and the hand-authored ones |

Redirects are also metadata: `content/redirects.py` is the single source, and the build emits both real HTML redirect pages (which is what makes them work on GitHub Pages, where `_redirects` is ignored) and the `_redirects` file itself for hosts that support server-side 301s.

**Conversion path for every article:**

`organic search → article → "Discuss Your Project" (generated end-of-article CTA) → /#start-project → form → /thanks.html`

The CTA is emitted automatically by `article_cta()` in `build-blog.py`, at three visual weights. A ghost link to `/china-supplement-sourcing.html` (supplier due diligence) appears on high-intent articles only — never as the primary offer.

---

## Cluster 1 — Product Development

| # | Topic | Status | Slug |
|---|---|---|---|
| 1.1 | How to Develop a Supplement Product in China | **Published 2026-09-18** | `how-to-develop-a-supplement-product-in-china` |
| 1.2 | How to Choose the Right Dosage Form | Planned | `how-to-choose-supplement-dosage-form` |
| 1.3 | How to Build a Formula Around a Target Effect | Planned | `build-a-formula-around-target-effect` |
| 1.4 | Common Problems When Developing Supplements in China | Planned | `common-problems-developing-supplements-china` |

### 1.2 — How to Choose the Right Dosage Form
- **Intent:** "capsule vs powder vs gummy supplement", "best dosage form for supplement", "supplement dosage form comparison"
- **Outline:** start from the consumer experience, not the format → the three tests (does the dose fit / does the active survive / can the market carry it) → per-format reality check table (dose ceiling, typical MOQ band, cost per dose, sensory risk, regulatory notes) → formats that are usually a bad idea for a given brief → how format locks in downstream cost → when to revisit
- **Internal links:** 1.1, 3.3 (MOQ & cost), `/#services`

### 1.3 — How to Build a Formula Around a Target Effect
- **Intent:** "how to formulate a supplement", "supplement formula development", "build supplement formula"
- **Outline:** effect → dose → form of active → actives that support the effect → avoiding overlap and antagonism → sensory and stability constraints → where to stop (and why more actives is usually worse) → the specification that comes out the other end
- **Internal links:** 1.1, 2.2 (specifications), 5.2 (formula decisions and cost)
- **Compliance note:** no efficacy claims. Frame as formulation reasoning, not health outcomes.

### 1.4 — Common Problems When Developing Supplements in China
- **Intent:** "supplement development problems", "supplement formulation mistakes", "why supplement projects fail"
- **Outline:** ten failure patterns with the decision each traces back to → which are cheap to fix and which are not → the three that appear in almost every troubled project → how each is prevented at the specification stage
- **Internal links:** 1.1, 2.5, 4.1

---

## Cluster 2 — Ingredient Sourcing

| # | Topic | Status | Slug |
|---|---|---|---|
| 2.1 | How to Source Functional Ingredients in China | Planned | `source-functional-ingredients-china` |
| 2.2 | How to Compare Ingredient Specifications | **Published** | `how-to-compare-ingredient-specifications` |
| 2.3 | Extract Ratio vs Standardized Extract | Planned | `extract-ratio-vs-standardized-extract` |
| 2.4 | How to Evaluate Botanical Extract Suppliers | Planned | `evaluate-botanical-extract-suppliers` |
| 2.5 | How to Compare Ingredient Quotes | Planned | `compare-ingredient-quotes` |

### 2.1 — How to Source Functional Ingredients in China
- **Intent:** "functional ingredient supplier China", "source ingredients China", "supplement ingredient sourcing"
- **Outline:** the supplier landscape (trader / distributor / extractor / manufacturer) and who adds what → why the entity that quotes is often not the entity that produces → what to establish before the first enquiry → documentation set by ingredient type → sampling and retention → when an audit is worth paying for
- **Internal links:** 2.2, 2.5, `/#services`

### 2.2 — How to Compare Ingredient Specifications
- **Status:** **Published** as `blog/how-to-compare-ingredient-specifications.md` (2026-09-18, high commercial intent)
- **Intent:** "ingredient specification comparison", "how to read a supplement ingredient spec", "spec sheet supplement"
- **Outline:** the fields that must be fixed before quotes are comparable → identity and form → assay, method and basis → standardisation and markers → carrier, excipient and grade → particle size, flow, density → tolerances → worked example: three quotes, one specification
- **Internal links:** 2.3, 2.5, 3.4
- **Deliverable bonus:** a copy-ready specification template. Highest link-earning asset in this cluster.
- **Note:** the copy-ready specification template is still outstanding — the published article is the argument for it, not the template itself. Worth building as a downloadable asset once there is a way to gate it.

### 2.3 — Extract Ratio vs Standardized Extract
- **Intent:** "extract ratio vs standardized", "what does 10:1 extract mean", "standardized extract supplement"
- **Outline:** what a ratio describes and what it does not → what standardisation describes → why identical ratios can hide different material → markers and their limitations → how to write a specification that survives substitution → where each is the right choice
- **Internal links:** 2.2, 2.4

### 2.4 — How to Evaluate Botanical Extract Suppliers
- **Intent:** "botanical extract supplier evaluation", "how to evaluate herbal extract supplier", "botanical supplier China"
- **Outline:** source plant and origin → extraction method and solvent residue → standardisation discipline → contamination and adulteration risk areas → documentation → lot-to-lot consistency as the real test → what to ask that produces a useful answer
- **Internal links:** 2.2, 2.3, 5.3
- **Compliance note:** keep to comparability and evidence, never to accusations about suppliers as a category.

### 2.5 — How to Compare Ingredient Quotes
- **Intent:** "compare supplement quotes", "ingredient price comparison China", "why are quotes different"
- **Outline:** why quotes differ without anyone being dishonest → the seven variables hidden inside a unit price → normalising to cost per active unit → when the cheapest is genuinely cheapest and when it is not → total landed cost → the questions that make quotes comparable
- **Internal links:** 2.2, 5.3, `/#services`
- **Canonical note:** overlaps 5.3 (cheapest quote ≠ lowest cost). Keep 2.5 mechanical and arithmetic; keep 5.3 argumentative and strategic. If they converge, merge into 5.3 and 301.

---

## Cluster 3 — Manufacturing

| # | Topic | Status | Slug |
|---|---|---|---|
| 3.1 | How to Choose a Supplement Manufacturer in China | Planned | `choose-supplement-manufacturer-china` |
| 3.2 | OEM vs ODM for Supplement Brands | Planned | `oem-vs-odm-supplement-brands` |
| 3.3 | MOQ, Lead Time and Development Costs | Planned | `moq-lead-time-development-costs` |
| 3.4 | What to Prepare Before Starting Production | Planned | `prepare-before-starting-production` |

### 3.1 — How to Choose a Supplement Manufacturer in China
- **Intent:** "choose supplement manufacturer China", "supplement manufacturer selection", "how to find a good supplement factory"
- **Outline:** fitness is relative to a specific brief → process capability vs category claims → MOQ and where it actually comes from → certification scope and whose name it is in → tolerance and the specification → finishing and packaging → how they behave when something goes wrong → the shortlist and trial-run strategy
- **Internal links:** 3.3, 3.4, 5.2

### 3.2 — OEM vs ODM for Supplement Brands
- **Intent:** "OEM vs ODM supplement", "private label vs custom formula", "ODM supplement China"
- **Outline:** what each model actually transfers → IP and formulation ownership → time to market → cost structure and where each is cheaper → change control and exclusivity → which model fits which stage of a brand → the hybrid arrangement most brands end up in
- **Internal links:** 3.1, 4.1, `/#services`

### 3.3 — MOQ, Lead Time and Development Costs
- **Intent:** "supplement MOQ", "supplement manufacturing lead time", "supplement development cost"
- **Outline:** what sets MOQ (line minimum, raw material pack size, tooling, packaging) → how to reduce it legitimately → the real timeline broken into stages, with the stages most often underestimated → where development cost goes and what drives it → the decisions that trade cost against flexibility
- **Internal links:** 1.2, 3.1, 3.4

### 3.4 — What to Prepare Before Starting Production
- **Intent:** "before starting supplement production", "production readiness supplement", "supplement batch checklist"
- **Outline:** locked specification → approved retained sample → raw material lots confirmed → packaging and artwork released → release criteria and who signs → retention samples and QC documents contracted → logistics and labelling checked per market → the pre-production confirmation email worth sending
- **Internal links:** 1.1, 3.1, 4.1

---

## Cluster 4 — Supply Chain

| # | Topic | Status | Slug |
|---|---|---|---|
| 4.1 | How to Build a China Supplement Supply Chain | Planned | `build-china-supplement-supply-chain` |
| 4.2 | How to Reduce Ingredient and Manufacturing Costs | Planned | `reduce-ingredient-manufacturing-costs` |
| 4.3 | How to Manage Chinese Suppliers Remotely | Planned | `manage-chinese-suppliers-remotely` |
| 4.4 | When a Supplement Brand Needs a China-Side Project Manager | Planned | `when-brands-need-china-project-manager` |

### 4.1 — How to Build a China Supplement Supply Chain
- **Intent:** "supplement supply chain China", "build supplement supply chain", "China supply chain setup"
- **Outline:** single vs dual sourcing by component → where a second source is worth the qualification cost → ingredient continuity vs finished-goods continuity → documentation as infrastructure → the point at which a supply chain becomes an asset rather than a dependency → what changes when SKU count grows
- **Internal links:** 3.1, 4.2, 4.4, `/#long-term`

### 4.2 — How to Reduce Ingredient and Manufacturing Costs
- **Intent:** "reduce supplement manufacturing cost", "lower supplement cost", "supplement cost optimization"
- **Outline:** cost levers ranked by effect and by risk → specification-driven savings vs substitution savings → volume, format and pack-size effects → where cost reduction breaks the product → negotiating without damaging the relationship → the recurring annual review that keeps unit cost honest
- **Internal links:** 2.5, 5.2, 5.3, `/#services`

### 4.3 — How to Manage Chinese Suppliers Remotely
- **Intent:** "manage Chinese supplier remotely", "working with Chinese suppliers", "China supplier communication"
- **Outline:** why distance fails (language, time zone, indirect answers, unwritten expectations) → what to put in writing and what to leave to a call → the reporting rhythm that prevents drift → site visits and third-party inspection: when each is worth it → escalation and dispute posture → what to localise and what to keep yourself
- **Internal links:** 4.1, 4.4, `/#start-project`

### 4.4 — When a Supplement Brand Needs a China-Side Project Manager
- **Intent:** "China project manager supplement", "do I need a sourcing agent", "China-side partner supplement brand"
- **Outline:** the trigger points (SKU count, custom formulations, multiple suppliers, regulatory complexity) → what the role actually does week to week → when a freelancer is enough and when it is not → agency vs independent partner vs in-house hire, honestly compared → how to scope and measure the engagement
- **Internal links:** 4.1, 4.3, `/#services`, `/#long-term`
- **Note:** the closest article in the plan to the service page — write it as the strategic bridge to 05 China Project Consulting.

---

## Cluster 5 — Industry Consulting

| # | Topic | Status | Slug |
|---|---|---|---|
| 5.1 | What Foreign Supplement Brands Often Get Wrong in China | Planned | `foreign-brands-get-wrong-china` |
| 5.2 | How Formula Decisions Affect Manufacturing Cost | Planned | `formula-decisions-manufacturing-cost` |
| 5.3 | Why the Cheapest Ingredient Quote Is Not Always the Lowest Cost | Planned | `cheapest-ingredient-quote-not-lowest-cost` |
| 5.4 | What to Check Before Moving a Supplement Project to China | Planned | `before-moving-supplement-project-to-china` |

### 5.1 — What Foreign Supplement Brands Often Get Wrong in China
- **Intent:** "supplement brand China mistakes", "doing business in China supplements", "China supplement market entry mistakes"
- **Outline:** eight recurring assumptions and what each costs → treating price as the primary signal → assuming a quotation is a specification → treating a certificate as evidence of a lot → optimising for first order instead of third → expecting written answers to unwritten questions → how each assumption is corrected
- **Internal links:** 5.4, 4.3, `/#founder`

### 5.2 — How Formula Decisions Affect Manufacturing Cost
- **Intent:** "formulation cost supplement", "supplement formula cost", "cost per serving supplement"
- **Outline:** cost per serving vs cost per kg → how dose, format and pack size compound → excipient and processing choices that add cost invisibly → yield, scrap and rework as cost lines → where a more expensive ingredient is the cheaper decision → the formula review that should precede price negotiation
- **Internal links:** 1.3, 3.3, 4.2

### 5.3 — Why the Cheapest Ingredient Quote Is Not Always the Lowest Cost
- **Intent:** "cheapest supplement ingredient", "why are quotes different", "supplement ingredient cost"
- **Outline:** what a low quote can mean (different grade, down-specified assay, different carrier, smaller pack, excluded testing, hidden freight) → normalising to cost per active unit → the cost of qualifying a second source later → downstream cost of a weak specification → a worked comparison
- **Internal links:** 2.5, 5.2, 4.2

### 5.4 — What to Check Before Moving a Supplement Project to China
- **Intent:** "move supplement production to China", "should I manufacture in China", "China supplement manufacturing checklist"
- **Outline:** the commercial case, honestly stated → what must be true before you start (specification, target market, volume, budget, timeline) → regulatory screening by market → IP and formulation protection → what to qualify first → the pilot sequence → when China is genuinely the wrong answer
- **Internal links:** 5.1, 4.1, 3.1, `/#start-project`

---

## Retained secondary cluster — Supplier & Supply-Chain Due Diligence

These four articles stay published, stay indexed and keep their internal links. They are **not** the brand narrative and should not be surfaced as the homepage hook — they serve readers who arrive with a live supplier question and route them into the wider project conversation.

| Topic | Published | Slug |
|---|---|---|
| How to Verify a China Supplement Manufacturer Before Paying | 2026-09-16 | `verify-china-supplement-manufacturer` |
| How to Tell If a Chinese Supplier Is Actually a Factory | 2026-09-11 | `chinese-supplier-factory-or-trading-company` |
| How to Verify a COA From a Chinese Supplier | 2026-09-05 | `verify-coa-chinese-supplement-supplier` |
| Alibaba Supplement Sourcing: What Buyers Should Verify | 2026-08-28 | `alibaba-supplement-sourcing-what-to-verify` |

Writer's note: when one of these is updated, reframe the opening toward the *project* rather than the platform. The content stays; the framing follows the positioning.

---

## Publishing rules for all content

1. **Never publish a claim you cannot stand behind.** No invented figures, savings, volumes, timelines or client names.
2. **No accusations against platforms or suppliers as a category.** Frame everything as buyer risk and verifiable evidence.
3. **Never promise guarantees.** Use: supplier verification, due diligence, documentation review, manufacturer identification, capability assessment, project-specific screening, risk reduction. Never: "guaranteed authentic", "100% verified", "we eliminate risk".
4. **Never publish a price for a service on the site.** Due diligence and consulting are quoted per project. No published day rates, no packaged low-cost reviews.
5. **No fabricated client names.** Where a client has not agreed to be named, use an anonymised label (*US Supplement Brand — Focus Powder*, *European Supplement Brand — Oral Film*, *US Brand — Functional Gummy*).
6. **Precise language over dramatic language.** The audience is a founder about to spend real money; precision signals competence.
7. **Every article ends with the project-enquiry CTA** — generated automatically by `build-blog.py`.
8. **Every article links to at least two other articles and one commercial page.** Related reading is generated; the commercial link is added automatically.
9. **Tag from the five clusters.** New tags must be added to `TAG_CLASS` and `TAG_LABEL` in `build-blog.py`, or the article falls back to the `sourcing` class.

---

## Measurement

There is currently **no analytics on the site**. Until that is added, none of this can be evaluated.

When analytics is in place, track per article:

| Metric | Why |
|---|---|
| Organic sessions | Is the topic actually being searched? |
| Scroll depth past 50% | Is the content being read or bounced? |
| Click-through to the generated CTA | Does the article move a reader toward the project conversation? |
| Form submissions attributed to assessment sources | Are we attracting product owners or one-off reviewers? |
| **Share of enquiries selecting "ongoing support" or "long-term partner"** | The single best proxy for whether the repositioning is working |
| Search Console: impressions vs CTR per query | Whether title/meta match intent |
| Search Console: queries the page ranks for | Discover unplanned topics worth writing |

`scripts/gsc-fetcher.py` already pulls Search Console data via service account and can supply the last two without client-side analytics.

**Watch for a positioning regression:** if the due-diligence articles keep out-performing the product-development cluster on conversions, the site is still being read as a supplier-check service. That is the signal to write more from clusters 1, 3 and 5.

---

## Suggested cadence

- **Publish two articles per month**, in this order: **4.4** (strategic bridge to the consulting service), **3.1** (highest-intent manufacturing query), **2.2** (specification template — the best link-earning asset), **1.2**, then work the clusters.
- **Revisit published articles quarterly** — add a "what we learned from reader questions" section, which refreshes the page and improves rankings without rewriting.
- **Add FAQ schema to the top three articles** once they have Search Console impressions showing question-style queries.
- **Batch by cluster where possible.** Two articles from the same cluster interlink for free and build topical authority faster than two scattered topics.
