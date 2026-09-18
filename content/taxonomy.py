#!/usr/bin/env python3
"""Single source of truth for SuppBridge content metadata (V2.2).

Sections
--------
PILLARS      the five SEO pillar pages — clustering, intro copy, topics, FAQ
ARTICLE_META per-article cluster + intent + entities metadata
FAQ_DATA     visible FAQ content, keyed by page; FAQPage schema is emitted
             ONLY for pages listed here (never invented for SEO's sake)
ENTITIES     the entity vocabulary used for semantic internal linking
STATIC_PAGES hand-authored pages that belong in the sitemap

Conventions
-----------
* A pillar is referenced by its key: 'product', 'ingredient', 'manufacturing',
  'supply', 'consulting'.
* `cluster` on an article must be one of those keys.
* `commercial_intent` is one of 'high' | 'medium' | 'low' and drives how loud
  the end-of-article CTA is.
* Never publish a price for a service here (see CONTENT-PLAN.md rules).
"""

SITE_URL = "https://suppbridge.com"
CONTACT = "/#start-project"

# ══════════════════════════════════════════════════════════════════
# PILLARS — the five topic clusters.
#
# Every pillar page carries original introductory content (§28): a pillar
# page that is only a list of links duplicates the blog index.
# ══════════════════════════════════════════════════════════════════

PILLARS = {
    "product": {
        "num": "01",
        "slug": "product-development",
        "url": "/product-development/",
        "title": "Supplement Product Development in China",
        "nav_title": "Product Development",
        "nav_desc": "Formulation, dosage form, cost, samples",
        "h1": "Supplement Product Development in China",
        "lede": (
            "How a supplement product actually gets decided in China — the dosage form, "
            "the actives, the dose, the cost envelope and the sample that has to survive "
            "production. Written for brand owners making the decisions."
        ),
        "topics": [
            "Dosage form", "Formula development", "Product development China",
            "Formula cost", "Sample development", "Stability & shelf life",
        ],
        "intro": [
            "Product development is where most of a supplement's cost, compliance exposure "
            "and manufacturing difficulty is locked in. A formula is not just a list of "
            "ingredients: the dosage form sets which manufacturing processes are even "
            "available, the dose determines how much of the formula has to be masked or "
            "encapsulated, and the ingredient grades you accept decide how repeatable the "
            "product will be batch to batch.",
            "In China specifically, the sequence matters. Choosing a manufacturer before the "
            "formula is settled usually means the product gets quietly reshaped to fit the "
            "lines that manufacturer already runs. Choosing the formula first — with a "
            "realistic view of what the market will pay and what the target regulator will "
            "allow — means you can compare manufacturers against the product you actually "
            "intended to make.",
            "The work in this section is written from the buyer's side of that sequence: how "
            "to specify a formula so it can be quoted comparably, how to read a sample "
            "against a production run, and how to price a formula before you commit to a "
            "minimum order quantity.",
        ],
        "faq": [
            ("Do I need a finished formula before talking to a manufacturer?",
             ["No, and arriving with one too early can cost you options. What you need first "
              "is a defined target: dosage form, actives and doses, the market you are "
              "selling into, a cost ceiling and a realistic volume. That is enough to "
              "compare manufacturers properly and to tell which of them can genuinely "
              "produce the product rather than a simplified version of it.",
              "A finished formula is useful once you are comparing quotations, because it is "
              "the only way two manufacturers are quoting the same thing."]),
            ("How long does supplement product development take?",
             ["For a standard format with an established formula, development through "
              "approved sample commonly runs a few weeks. Novel formulations, or ones that "
              "need stability work, masking trials or a regulatory review before launch, "
              "take considerably longer.",
              "The variable that most often extends a timeline is not manufacturing speed — "
              "it is unresolved product decisions. A brief that changes mid-development "
              "restarts more of the process than most brands expect."]),
            ("Can one formula work across several markets?",
             ["Sometimes, and it is worth designing for it deliberately rather than "
              "discovering a conflict later. Permitted ingredients, maximum doses, permitted "
              "claims and labelling requirements all differ between the United States, the "
              "EU, the UK, Australia and Canada.",
              "Where a single formula cannot serve every market, the practical answer is "
              "usually a core formula with market-specific variants, decided at the "
              "specification stage rather than retrofitted after production."]),
        ],
    },

    "ingredient": {
        "num": "02",
        "slug": "ingredient-sourcing",
        "url": "/ingredient-sourcing/",
        "title": "Supplement Ingredient Sourcing in China",
        "nav_title": "Ingredient Sourcing",
        "nav_desc": "Specifications, extracts, pricing",
        "h1": "Supplement Ingredient Sourcing in China",
        "lede": (
            "Specification before price. How to define an ingredient precisely enough that "
            "two quotations are actually comparable — and what to settle before you buy at "
            "volume."
        ),
        "topics": [
            "Ingredient specifications", "Botanical extracts", "Standardized extracts",
            "Ingredient quotes", "Ingredient pricing", "China ingredient suppliers",
        ],
        "intro": [
            "Most ingredient problems are not fraud problems. They are specification "
            "problems. Two quotations that both say \"ashwagandha extract\" can describe "
            "materials with different extraction ratios, different standardisation targets, "
            "different carriers, different particle sizes and different residue limits. "
            "Comparing their prices is meaningless until the specifications match.",
            "The Chinese ingredient market is deep and genuinely competitive — for many "
            "botanical and functional ingredients it is where the volume is, which is why "
            "the price is what it is. That same depth is the difficulty: a good supplier and "
            "a reseller of someone else's material can present almost identically on a "
            "website, and the difference only shows up in the documentation and in how "
            "questions about process are answered.",
            "This section is about the specification layer of sourcing: what to write down, "
            "what to ask for, how to read what comes back, and how to compare offers that "
            "were never designed to be compared.",
        ],
        "faq": [
            ("What is the difference between an extract ratio and standardisation?",
             ["An extract ratio tells you how much raw botanical went in to make a given "
              "amount of extract — 10:1 means ten parts of dried herb to one part extract. "
              "Standardisation tells you how much of a named marker compound the finished "
              "extract contains, for example a fixed percentage of withanolides.",
              "They describe different things and neither replaces the other. A ratio "
              "without standardisation says nothing about potency; a standardisation target "
              "without a ratio says nothing about what else is in the material. A useful "
              "specification asks for both, plus the test method."]),
            ("Why do ingredient quotations for the same material vary so much?",
             ["Because they are rarely quotations for the same material. Differences usually "
              "sit in the specification (extract ratio, standardisation, carrier, grade), in "
              "what documentation is included, in whether the price assumes a full container "
              "or a small trial quantity, and in whether the seller is the producer or a "
              "reseller.",
              "Fixing the specification first removes most of the spread. What remains is "
              "the part worth negotiating."]),
            ("How do I check an ingredient supplier I have not worked with before?",
             ["Start with the specification and the documentation, not the website. Ask for "
              "the specification sheet, a certificate of analysis for a specific lot, the "
              "test method behind the key figures, and confirmation of who actually produces "
              "the material versus who is selling it.",
              "Then compare that paperwork against the specification you wrote. Consistency "
              "between what was promised, what is documented and what the seller will commit "
              "to in writing tells you more than any supplier profile."]),
        ],
    },

    "manufacturing": {
        "num": "03",
        "slug": "supplement-manufacturing",
        "url": "/supplement-manufacturing/",
        "title": "Supplement Manufacturing in China",
        "nav_title": "Manufacturing",
        "nav_desc": "Manufacturers, OEM/ODM, MOQ, production",
        "h1": "Supplement Manufacturing in China",
        "lede": (
            "Choosing a manufacturing partner rather than a factory, understanding what "
            "OEM and ODM actually mean commercially, and knowing what a minimum order "
            "quantity is really costing you."
        ),
        "topics": [
            "Manufacturer selection", "OEM vs ODM", "MOQ", "Production",
            "Manufacturing cost", "Production readiness",
        ],
        "intro": [
            "Every supplement manufacturer in China will tell you it can make your product. "
            "The useful question is narrower: which processes for this specific dosage form, "
            "at this dose, at this volume, sit inside that company's own facility — and "
            "which are subcontracted, assumed or not currently in use at all.",
            "Manufacturer selection is a fit problem before it is a quality problem. A plant "
            "that runs gummies at scale is not the right plant for a small-batch oral film, "
            "and a plant built for two-shift commodity capsule runs may not be set up for the "
            "documentation a European launch needs. Capability, certification scope, product "
            "fit and communication all have to line up at once.",
            "This section covers the commercial shape of manufacturing too: what OEM and ODM "
            "arrangements mean for who owns the formula, how minimum order quantities "
            "translate into real cash exposure, and what has to be true before a production "
            "run can actually be scheduled.",
        ],
        "faq": [
            ("What is the difference between OEM and ODM?",
             ["OEM means the manufacturer produces to your specification — your formula, "
              "your requirements, their plant. ODM means the manufacturer owns a developed "
              "formula or product platform and you license or adapt it.",
              "The commercial difference is who owns the intellectual property and how much "
              "of the product is genuinely yours. ODM is faster and cheaper to start; OEM "
              "gives you a formula you control and can take to another supplier later. The "
              "right answer depends on whether the formula is part of your brand's value."]),
            ("How do minimum order quantities work in practice?",
             ["An MOQ is an expression of a factory's changeover cost, not a statement about "
              "the smallest quantity it is physically able to make. It is sometimes "
              "negotiable, particularly for a first run, and it is often expressed in a unit "
              "that hides what you are committing to — finished units, kilograms of bulk, or "
              "a full production batch.",
              "The useful calculation is total cash exposure at the first order including "
              "raw materials, tooling, packaging, testing and freight — not the headline "
              "per-unit price."]),
            ("Do you have to verify a manufacturer before a first production run?",
             ["It is the cheapest point in the whole project to do it. Before an order, you "
              "can still compare alternatives. After a deposit, you are managing a "
              "relationship rather than choosing one.",
              "Verification is not a guarantee about conduct. It establishes what the "
              "company's registration and licence scope actually cover, which processes it "
              "runs in-house, what its certificates are and in whose name, and whether the "
              "documents it has supplied are internally consistent with your product."]),
        ],
    },

    "supply": {
        "num": "04",
        "slug": "china-supplement-supply-chain",
        "url": "/china-supplement-supply-chain/",
        "title": "China Supplement Supply Chain Management",
        "nav_title": "Supply Chain",
        "nav_desc": "Supplier management, cost, project control",
        "h1": "China Supplement Supply Chain",
        "lede": (
            "What happens after the first order ships. Supplier management, documentation "
            "discipline, cost optimisation and remote project control across a chain you "
            "cannot visit every week."
        ),
        "topics": [
            "Supply chain setup", "Supplier management", "Cost optimization",
            "China project management", "Remote supplier management", "Documentation & QC",
        ],
        "intro": [
            "Most discussions about buying from China focus on the first order. The cost, "
            "risk and friction actually accumulate afterwards — when a raw material changes "
            "source, when a batch needs to be traced, when a second product needs to come "
            "from the same chain, or when the person who handled everything on the supplier "
            "side leaves.",
            "A supply chain is a set of relationships with documentation attached, and it "
            "only stays stable when someone is accountable for it from the buyer's side. "
            "That means agreed specifications, batch records that line up with deliveries, "
            "regular communication in the supplier's own language, and a clear view of where "
            "the single points of failure are.",
            "This section covers the ongoing work: how to set a chain up so it can be "
            "managed remotely, how to hold supplier performance to something measurable, "
            "where cost can genuinely be taken out without changing the product, and what "
            "to do when something goes wrong a few thousand kilometres away.",
        ],
        "faq": [
            ("How do you manage a Chinese supplier from abroad?",
             ["By making the specification and the documentation carry the relationship. "
              "Agreed specifications, lot-level certificates, a named contact on each side, "
              "and a predictable communication rhythm do more for reliability than frequent "
              "chasing.",
              "The part that cannot be done remotely is judging whether what the paperwork "
              "claims is what the operation actually does. That is where having someone on "
              "the China side is worth more than another email."]),
            ("Where can cost realistically be taken out of a supply chain?",
             ["Usually not by pressing the manufacturer on unit price. More often it sits in "
              "packaging format and material, in batching and order frequency, in freight "
              "consolidation, in the specification grades you actually need versus the ones "
              "you were sold, and in the cost of rework when something was specified "
              "loosely.",
              "It also helps to stop optimising something that is not the cost driver. In "
              "many supplement products the packaging bill is comparable to the fill bill, "
              "and nobody has looked at it."]),
            ("What should be in place before a second product reuses the same supply chain?",
             ["The documented version of what you learned on the first one: the approved "
              "specifications, the sample that was signed off, the certificate history, the "
              "actual yields and the agreed lead times. Without that, the second product "
              "restarts the negotiation instead of building on it.",
              "This is the main practical argument for treating a China supply chain as a "
              "long-term asset rather than a series of one-off purchases."]),
        ],
    },

    "consulting": {
        "num": "05",
        "slug": "supplement-industry-consulting",
        "url": "/supplement-industry-consulting/",
        "title": "China Supplement Industry Consulting",
        "nav_title": "Industry Consulting",
        "nav_desc": "Market entry, project judgement, long-term partner",
        "h1": "China Supplement Industry Consulting",
        "lede": (
            "Industry judgement rather than introductions — what the China supplement "
            "ecosystem looks like from inside it, where Western brands typically get the "
            "sequence wrong, and how to work with a partner on the ground over years rather "
            "than projects."
        ),
        "topics": [
            "China market entry", "Formula decisions", "Common China mistakes",
            "Project consulting", "Long-term China partner", "Category assessment",
        ],
        "intro": [
            "The China supplement industry is large, fragmented and full of real capability "
            "that is genuinely hard to see from outside. Western brand owners usually meet it "
            "through a marketplace listing or a trade-show introduction, which is a narrow "
            "and not especially representative slice of what exists.",
            "Consulting here is mostly about judgement applied early. Which questions to ask "
            "before a project starts. Which product ideas are straightforward in China and "
            "which are quietly difficult. When the honest answer is that a different dosage "
            "form, market or sequence would cost far less for the same outcome. Those "
            "decisions are cheap to make at the start and expensive to reverse later.",
            "This section collects the industry-level material: how the ecosystem is "
            "structured, how category dynamics play out for brands selling into the US, EU, "
            "UK, Australia and Canada, and what working with a long-term China-side partner "
            "actually looks like in practice.",
        ],
        "faq": [
            ("What does a China-side partner do that a sourcing agent does not?",
             ["A sourcing agent is usually paid to complete a transaction: find a supplier, "
              "get a price, place an order. A China-side partner is accountable for the "
              "product decisions around that transaction — whether the specification is "
              "right, whether the manufacturer fits, whether the timeline is realistic, and "
              "what happens when something deviates.",
              "In practice the distinction shows up when a problem occurs. An agent's job is "
              "finished at the order; a partner's is not."]),
            ("We already have suppliers. Is there still a reason to work with you?",
             ["Often yes, and it is usually the less glamorous work: specising what you have "
              "already been buying, comparing a second source so you are not single-threaded, "
              "looking at where the landed cost actually sits, and putting documentation in "
              "place that currently only exists in someone's inbox.",
              "Brands with an existing supplier most commonly come to us for a second opinion "
              "before a large commitment, or when a product needs to move from one supplier "
              "to another and nobody wants to restart from scratch."]),
            ("Do you help with market entry from scratch?",
             ["Yes, with the industry and supply side of it — category assessment, what the "
              "product realistically has to be to compete, sourcing and manufacturing "
              "strategy, and the regulatory considerations that shape the formulation before "
              "development starts.",
              "What we do not do is act as a distributor, hold stock, or sell your product in "
              "China. The advice stays buyer-side."]),
        ],
    },
}

# Ordered list, used for navigation, the blog index and sitemap generation.
PILLAR_ORDER = ["product", "ingredient", "manufacturing", "supply", "consulting"]

# ══════════════════════════════════════════════════════════════════
# ENTITIES — semantic vocabulary for internal linking.
# Article entities are matched against these to build cross-cluster links.
# ══════════════════════════════════════════════════════════════════

ENTITIES = {
    "supplement formulation": ["product"],
    "dosage form": ["product"],
    "oral film": ["product"],
    "powder": ["product"],
    "gummy": ["product"],
    "capsule": ["product"],
    "flavor masking": ["product"],
    "sample development": ["product"],
    "formula cost": ["product"],
    "ingredient sourcing": ["ingredient"],
    "ingredient specification": ["ingredient"],
    "botanical extract": ["ingredient"],
    "standardized extract": ["ingredient"],
    "extract ratio": ["ingredient"],
    "ingredient pricing": ["ingredient"],
    "ingredient supplier": ["ingredient"],
    "supplement manufacturer": ["manufacturing"],
    "OEM": ["manufacturing"],
    "ODM": ["manufacturing"],
    "MOQ": ["manufacturing"],
    "production readiness": ["manufacturing"],
    "trading company": ["manufacturing", "supply"],
    "China supply chain": ["supply"],
    "supplier management": ["supply"],
    "certificate of analysis": ["supply"],
    "cost optimization": ["supply"],
    "China project management": ["supply"],
    "due diligence": ["supply"],
    "regulatory compliance": ["consulting"],
    "FDA": ["consulting"],
    "EFSA": ["consulting"],
    "novel food": ["consulting", "ingredient"],
    "market entry": ["consulting"],
    "industry trends": ["consulting"],
}

# ══════════════════════════════════════════════════════════════════
# ARTICLE_META — one entry per published article.
#
# Required keys: cluster, commercial_intent
# Optional keys: secondary (extra clusters), entities, featured,
#                search_intent (overrides the default for its intent)
#
# `commercial_intent` drives CTA weight:
#   high   → full dark CTA panel, project-led, strong ask
#   medium → full dark CTA panel, softer framing
#   low    → quiet inline prompt
#
# `pillar` and `pillar_title` are NOT stored here — they are derived from
# `cluster` by article_meta() below, so the two can never disagree. Adding a
# fourth key that duplicates the first would only create a way to be wrong.
# ══════════════════════════════════════════════════════════════════

# §21 — search intent defaults, keyed by commercial_intent. An article that
# targets a buying decision is almost always both informational and
# commercial; a trend piece is informational only. Override per entry when
# the reality differs.
DEFAULT_SEARCH_INTENT = {
    "high": ["informational", "commercial"],
    "medium": ["informational", "commercial"],
    "low": ["informational"],
}

VALID_SEARCH_INTENT = {"informational", "commercial", "transactional", "navigational"}

ARTICLE_META = {
    "how-to-develop-a-supplement-product-in-china": {
        "cluster": "product",
        "commercial_intent": "high",
        "featured": True,
        "entities": ["supplement formulation", "dosage form", "sample development",
                     "formula cost", "supplement manufacturer"],
    },
    "flavor-masking-functional-powders": {
        "cluster": "product",
        "commercial_intent": "medium",
        "entities": ["flavor masking", "powder", "supplement formulation"],
    },
    "oral-films-wellness-frontier": {
        "cluster": "product",
        "commercial_intent": "medium",
        "entities": ["oral film", "dosage form"],
    },
    "melatonin-regulations-eu": {
        "cluster": "product",
        "commercial_intent": "medium",
        "secondary": ["consulting"],
        "entities": ["supplement formulation", "regulatory compliance", "EFSA"],
    },

    "bitter-orange-extract-eu-compliance": {
        "cluster": "ingredient",
        "commercial_intent": "medium",
        "secondary": ["consulting"],
        "entities": ["botanical extract", "ingredient sourcing", "novel food", "EFSA"],
    },
    "how-to-compare-ingredient-specifications": {
        "cluster": "ingredient",
        "commercial_intent": "high",
        "entities": ["ingredient specification", "ingredient sourcing", "botanical extract",
                     "standardized extract", "certificate of analysis"],
    },

    "chinese-supplier-factory-or-trading-company": {
        "cluster": "manufacturing",
        "commercial_intent": "high",
        "secondary": ["supply"],
        # Buyers arrive here mid-evaluation and often want to act on it —
        # the only article on the site with genuine transactional intent.
        "search_intent": ["informational", "commercial", "transactional"],
        "entities": ["trading company", "supplement manufacturer", "due diligence"],
    },
    "verify-china-supplement-manufacturer": {
        "cluster": "manufacturing",
        "commercial_intent": "high",
        "secondary": ["supply"],
        "entities": ["supplement manufacturer", "production readiness", "due diligence"],
    },

    "verify-coa-chinese-supplement-supplier": {
        "cluster": "supply",
        "commercial_intent": "high",
        "secondary": ["manufacturing"],
        "entities": ["certificate of analysis", "supplier management", "ingredient specification"],
    },
    "alibaba-supplement-sourcing-what-to-verify": {
        "cluster": "supply",
        "commercial_intent": "high",
        "secondary": ["manufacturing"],
        "entities": ["due diligence", "trading company", "ingredient supplier"],
    },

    "fda-vs-efsa-supplement-regulations": {
        "cluster": "consulting",
        "commercial_intent": "medium",
        "entities": ["regulatory compliance", "FDA", "EFSA", "market entry"],
    },
    "card-liquid-wellness-trends": {
        "cluster": "consulting",
        "commercial_intent": "low",
        "entities": ["industry trends", "dosage form", "market entry"],
    },
    "dtc-wellness-evolution-2026": {
        "cluster": "consulting",
        "commercial_intent": "low",
        "entities": ["industry trends", "market entry"],
    },
    "functional-beverage-startups": {
        "cluster": "consulting",
        "commercial_intent": "low",
        "entities": ["industry trends", "dosage form", "market entry"],
    },
    "pet-wellness-supplements-growth": {
        "cluster": "consulting",
        "commercial_intent": "low",
        "entities": ["industry trends", "supplement formulation"],
    },
}


def article_meta(slug):
    """Normalised metadata for one article, or None if unmapped.

    Everything downstream (build-blog.py, validate-site.py, future link
    engine and Search Console joins) reads through this function rather than
    touching ARTICLE_META directly, so derived fields stay consistent.
    """
    raw = ARTICLE_META.get(slug)
    if raw is None:
        return None
    cluster = raw["cluster"]
    intent = raw.get("commercial_intent", "low")
    pillar = PILLARS[cluster]
    search_intent = raw.get("search_intent") or DEFAULT_SEARCH_INTENT.get(intent, ["informational"])
    return {
        **raw,
        "slug": slug,
        "cluster": cluster,
        # derived — never stored
        "pillar_key": cluster,
        "pillar": pillar["url"],
        "pillar_title": pillar["nav_title"],
        "pillar_h1": pillar["h1"],
        # defaults
        "secondary": raw.get("secondary", []),
        "entities": raw.get("entities", []),
        "commercial_intent": intent,
        "search_intent": list(search_intent),
        "featured": raw.get("featured", False),
    }


def articles_in_pillar(key, articles=None):
    """Slugs belonging to a pillar, primary cluster first, then secondary.

    Used for pillar-page listings and for the internal link engine's
    "same pillar" tier (§19).
    """
    primary, secondary = [], []
    for slug, meta in ARTICLE_META.items():
        if meta.get("cluster") == key:
            primary.append(slug)
        elif key in (meta.get("secondary") or []):
            secondary.append(slug)
    ordered = primary + secondary
    if articles is None:
        return ordered
    live = {a["slug"] for a in articles}
    return [s for s in ordered if s in live]

# ══════════════════════════════════════════════════════════════════
# FAQ_DATA — visible FAQ content per page.
#
# FAQPage schema is generated ONLY for keys in this dict, and only
# alongside the visible markup on the same page. Do not add an entry
# here purely to emit schema.
#
# Shape: list of (question, [answer paragraph, ...])
# ══════════════════════════════════════════════════════════════════

FAQ_DATA = {
    "index": [
        ("How do you verify a supplement manufacturer in China?",
         ["Verification is project-specific and starts with the company behind the quotation. "
          "We look at the legal entity and how it is registered, whether the operation is a "
          "manufacturer or a trading company, which production processes actually sit in-house "
          "versus subcontracted, what certifications are held and in whose name, and whether the "
          "documents provided are internally consistent.",
          "We then compare those findings against your specific formula, dosage form, dose per "
          "unit, MOQ and target market. You get a report of what we found and what remains open — "
          "we do not issue guarantees about a supplier's conduct."]),
        ("Can you tell whether a Chinese supplier is a factory or a trading company?",
         ["In most cases we can establish useful evidence either way. Business registration "
          "records, food production licence scopes, certification documents, audit reports and "
          "the ability to discuss process detail all carry signals.",
          "A trading company is not automatically a problem — many are legitimate and useful. "
          "The risk is paying factory pricing for a trading company's margin, or discovering that "
          "the specific process your product needs is subcontracted to a third party you know "
          "nothing about."]),
        ("Do you guarantee that a supplier is honest?",
         ["No — and you should be cautious of anyone who does. What we provide is supplier "
          "verification, documentation review, manufacturer identification and capability "
          "assessment against your project: a structured due-diligence process that reduces risk "
          "and gives you specific questions to ask before you commit.",
          "We tell you what we could verify, what we could not, and where the remaining exposure "
          "sits."]),
        ("Are you a manufacturer?",
         ["No. SuppBridge is an independent advisor and project partner, not a factory owner. We "
          "coordinate the manufacturers, ingredient suppliers, laboratories and packaging partners "
          "that fit your project.",
          "That independence is the point: we can compare options and recommend what fits, rather "
          "than steering you toward whatever our own lines happen to run."]),
        ("Do you work on a single project, or can you support us longer term?",
         ["Both, and most relationships become the second. A project often starts with one "
          "product — formulation, ingredient sourcing, manufacturer selection and production. "
          "From there we commonly continue into the next SKU, recurring ingredient supply, cost "
          "optimization and ongoing supplier management.",
          "Many brands work with us precisely because they do not want to rebuild their China "
          "supply chain from scratch for every new product."]),
        ("I already have a Chinese supplier. Can you review it before I commit?",
         ["Yes. Send the supplier link or company name, the quotation, the specification, any COA "
          "or certificate and the supplier contact.",
          "We review company identity, manufacturer-versus-trading-company signals, product "
          "capability for your format, consistency between certifications and documents, "
          "specification gaps and obvious red flags — then give you a list of questions to put to "
          "the supplier before you order."]),
        ("What does a typical project cost and how long does it take?",
         ["Scope and timing depend entirely on the project. For standard formats with an existing "
          "formulation, we typically work toward a 45–60 day path from confirmed brief to "
          "delivery. Advanced delivery systems, or novel formulations that need stability work "
          "and regulatory review, more commonly run 90–120 days.",
          "Fees are quoted per project after we've reviewed your brief, so you're paying for a "
          "defined scope rather than an open-ended retainer."]),
        ("Which markets do you work with?",
         ["Most of our work is for brands selling into the United States, the European Union, the "
          "United Kingdom, Australia and Canada.",
          "We consider regulatory requirements at the sourcing and formulation stage — EU Novel "
          "Food classification, permitted ingredients, claim substantiation and labelling — so "
          "compliance isn't retrofitted after development."]),
    ],
}

# ══════════════════════════════════════════════════════════════════
# STATIC_PAGES — hand-authored pages that belong in the root sitemap.
# (rel_path, changefreq, priority)
# ══════════════════════════════════════════════════════════════════

STATIC_PAGES = [
    ("index.html", "weekly", "1.0"),
    ("china-supplement-sourcing.html", "monthly", "0.8"),
    ("product-formats.html", "monthly", "0.7"),
    ("regulatory/index.html", "monthly", "0.6"),
]
