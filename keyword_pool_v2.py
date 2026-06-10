# -*- coding: utf-8 -*-
"""
keyword_pool_v2.py  (Korean Salaryman — ENGLISH edition)
────────────────────────────────────────────────────────────
Korea explained by an actual Korean salaryman in Seoul, for a global audience.

[Category keys / label / emoji]
- k-trends           / What's trending in Korea right now   / 🔥  (main engine)
- korean-life        / Real daily life in Korea             / 🍚
- culture-explained  / The culture behind it                / 🧭
- essay              / Personal essays (human-written only) / ✍️  (auto-gen = 0%)

The trend pipeline is the main driver for k-trends; the seed pools below are a
safety net for when live trends are thin. `essay` is never auto-generated —
Park writes those by hand in the admin panel.
────────────────────────────────────────────────────────────
"""

# ═══════════════════════════════════════════════════════
#  Main keyword pool (seeds — expanded via autocomplete / related queries)
#  Written as queries a foreign reader would actually type.
# ═══════════════════════════════════════════════════════
KEYWORD_POOL_V2 = {
    "k-trends": [
        "what is trending in korea right now",
        "korean frozen kimbap trader joes",
        "korean skincare trend 2026",
        "why is korean food so popular",
        "korea viral food trend",
        "k-drama filming locations seoul",
        "korean convenience store food must try",
        "what koreans are obsessed with right now",
        "korean buldak ramen spicy challenge",
        "dalgona candy squid game where to buy",
        "korean corn dog street food",
        "tanghulu korean dessert trend",
        "korean 4-day work week news",
        "korean melon soju trend",
        "what is hot in seoul this week",
        "korean beauty glass skin routine 2026",
        "korean fried chicken vs american",
        "korea trending tiktok food",
        "korean lunchbox dosirak trend",
        "why korean dramas are everywhere",
        "korean spicy instant noodles ranking",
        "k-pop demon hunters korea reaction",
        "korean coffee culture cafe trend",
        "korean street fashion 2026",
        "korea new year viral trend",
        "korean banana milk where to buy",
        "korean mukbang explained",
        "korea trending app this year",
    ],
    "korean-life": [
        "what do koreans eat for breakfast",
        "korean delivery culture explained",
        "seoul apartment living what it's really like",
        "korean subway etiquette for tourists",
        "korean work culture reality",
        "how do koreans spend their weekends",
        "korean banking for foreigners",
        "cost of living in seoul 2026",
        "korean grocery shopping haul",
        "what is a korean officetel",
        "korean public transportation guide",
        "korean apartment deposit jeonse explained",
        "korean trash sorting rules",
        "korean hospital visit as a foreigner",
        "korean salary and taxes explained",
        "what koreans actually eat for lunch",
        "korean convenience store 24 hours",
        "korean gym culture",
        "korean late night food culture",
        "renting an apartment in seoul",
        "korean phone plan for foreigners",
        "korean cafe study culture",
        "how koreans commute to work",
        "korean grocery delivery same day",
        "living in seoul as a single person",
        "korean neighborhood dongne life",
        "korean summer humidity survival",
        "korean winter heating ondol floor",
    ],
    "culture-explained": [
        "what is nunchi korean",
        "korean age system explained",
        "why do koreans ask your age",
        "hoesik korean company dinner explained",
        "korean honorifics explained simply",
        "bowing culture in korea",
        "korean drinking etiquette rules",
        "jeong meaning korean culture",
        "why koreans take off shoes indoors",
        "korean gift giving etiquette",
        "korean dating culture explained",
        "korean wedding customs",
        "korean name order family name first",
        "korean table manners explained",
        "why koreans share food",
        "korean palli palli hurry culture",
        "korean military service explained",
        "korean respect for elders",
        "what is aegyo korean",
        "korean blood type personality belief",
        "korean lunar new year seollal",
        "korean chuseok thanksgiving explained",
        "why koreans use we instead of i",
        "korean business card etiquette",
        "korean apartment culture neighbors",
        "korean superstitions explained",
        "korean group harmony explained",
        "korean indirect communication style",
    ],
    "essay": [],   # human-written only — never auto-generated
}


# ═══════════════════════════════════════════════════════
#  Publish ratio (must sum to 1.00). essay = 0 (hand-written).
# ═══════════════════════════════════════════════════════
CATEGORY_BALANCE = {
    "k-trends":          0.40,
    "korean-life":       0.35,
    "culture-explained": 0.25,
    "essay":             0.00,
}


# ═══════════════════════════════════════════════════════
#  Per-category article-type hints (the prompt reads these to pick a format)
# ═══════════════════════════════════════════════════════
CATEGORY_INTENTS = {
    "k-trends": {
        "primary_format": "insight",         # what's happening + a local's read
        "format_pool":    ["insight", "explainer", "guide", "experience"],
        "secondary":      "explainer",
        "tone":           "lively",          # timely, conversational
        "needs_official_link": False,
        "audience":       "foreigners curious about what's hot in Korea right now",
        "label":          "What's trending in Korea right now",
        "emoji":          "🔥",
    },
    "korean-life": {
        "primary_format": "explainer",       # how things actually work here
        "format_pool":    ["explainer", "guide", "experience", "comparison"],
        "secondary":      "guide",
        "tone":           "honest",          # first-person, no sugarcoating
        "needs_official_link": False,
        "audience":       "people planning to visit, move to, or just understand daily Korea",
        "label":          "Real daily life in Korea",
        "emoji":          "🍚",
    },
    "culture-explained": {
        "primary_format": "explainer",       # unpack one custom clearly
        "format_pool":    ["explainer", "insight", "guide"],
        "secondary":      "insight",
        "tone":           "thoughtful",      # patient, insider context
        "needs_official_link": False,
        "audience":       "readers who want the why behind Korean customs, not just the what",
        "label":          "The culture behind it",
        "emoji":          "🧭",
    },
    "essay": {
        "primary_format": "experience",
        "format_pool":    ["experience", "insight"],
        "secondary":      "insight",
        "tone":           "personal",
        "needs_official_link": False,
        "audience":       "readers who follow Park's personal take on living in Korea",
        "label":          "Personal essays",
        "emoji":          "✍️",
    },
}


# ═══════════════════════════════════════════════════════
#  Single Unsplash query for thumbnails
# ═══════════════════════════════════════════════════════
UNSPLASH_QUERY_V2 = {
    "k-trends":          "seoul street food korea trendy",
    "korean-life":       "seoul daily life street korea",
    "culture-explained": "korean traditional culture hanok",
    "essay":             "seoul quiet street mood",
}


# ═══════════════════════════════════════════════════════
#  Unsplash body-image query pool (for variety)
# ═══════════════════════════════════════════════════════
UNSPLASH_BODY_QUERIES_V2 = {
    "k-trends": [
        "korean street food stall", "seoul night market", "korean convenience store",
        "korean cafe trendy", "korean dessert colorful", "seoul young crowd",
    ],
    "korean-life": [
        "seoul apartment building", "korean subway station", "korean grocery store",
        "seoul commute morning", "korean home interior", "korean delivery food",
    ],
    "culture-explained": [
        "korean hanok traditional", "korean tea ceremony", "korean elders respect",
        "korean dinner table sharing", "seoul temple quiet", "korean family gathering",
    ],
    "essay": [
        "seoul rainy street", "korean alley quiet", "seoul rooftop view",
        "korean han river evening", "seoul cafe window", "seoul neon night",
    ],
}


# ═══════════════════════════════════════════════════════
#  Category → blog category page mapping (category-*.html files)
# ═══════════════════════════════════════════════════════
CATEGORY_PAGE_MAP = {
    "k-trends":          "category-k-trends.html",
    "korean-life":       "category-korean-life.html",
    "culture-explained": "category-culture-explained.html",
    "essay":             "category-essay.html",
}


# ═══════════════════════════════════════════════════════
#  Legacy / alias category map → new EN keys (manifest migration & fallback)
# ═══════════════════════════════════════════════════════
LEGACY_CATEGORY_MAP = {
    # Korean-site legacy keys (in case any old data leaks in)
    "trending":   "k-trends",
    "money":      "korean-life",
    "finance":    "korean-life",
    "realestate": "korean-life",
    "startup":    "korean-life",
    "ai":         "k-trends",
    "book":       "essay",
    # human-friendly aliases
    "trends":     "k-trends",
    "life":       "korean-life",
    "culture":    "culture-explained",
}


# ═══════════════════════════════════════════════════════
#  Standalone test
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  Korean Salaryman EN — 4-category system")
    print("=" * 60)

    total = 0
    for cat, seeds in KEYWORD_POOL_V2.items():
        ratio = CATEGORY_BALANCE.get(cat, 0)
        intent = CATEGORY_INTENTS.get(cat, {})
        emoji = intent.get("emoji", "")
        label = intent.get("label", cat)
        print(f"\n{emoji} [{cat} / {label}] seeds {len(seeds)} / ratio {ratio:.0%}")
        print(f"   format: {intent.get('primary_format')}, tone: {intent.get('tone')}")
        print(f"   audience: {intent.get('audience')}")
        if seeds:
            print(f"   sample: {', '.join(seeds[:3])}")
        total += len(seeds)

    print(f"\nTotal seed keywords: {total}")
    print(f"\nLegacy map:")
    for old, new in LEGACY_CATEGORY_MAP.items():
        print(f"   {old:12s} -> {new}")
    print(f"Ratio sum: {sum(CATEGORY_BALANCE.values()):.2f} (must be 1.00)")
