# -*- coding: utf-8 -*-
"""
trend_pipeline.py  (Korean Salaryman — ENGLISH edition)
────────────────────────────────────────────────────────────
Two-way trend fusion that drives English blog topics:

  Direction 1 — what FOREIGNERS are curious about regarding Korea
    (Google News EN searches + Reddit communities + Korea-related US trends)
  Direction 2 — what is actually TRENDING inside Korea right now
    (Google Trends KR realtime)

  topic = (foreign curiosity) × (on-the-ground Korea trend)
        = "the thing you're curious about? here's what it looks like in Korea right now."

A safety filter drops politics / celebrity gossip / accidents / military conflict.
Gemini fuses the two directions into clickable topics for an actual Seoul
salaryman to explain. All sources verified 200-OK in stage-1 testing.
"""
import os
import re
import time
import json as _json
import html as _html
import xml.etree.ElementTree as ET
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # GitHub Actions injects env directly

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

ATOM_NS = "{http://www.w3.org/2005/Atom}"


# ═══════════════════════════════════════════════════════
#  Direction 1 — what foreigners want to know about Korea
# ═══════════════════════════════════════════════════════
GOOGLE_NEWS_EN = {
    "culture": "https://news.google.com/rss/search?q=korean+culture&hl=en-US&gl=US&ceid=US:en",
    "food":    "https://news.google.com/rss/search?q=korean+food+trend&hl=en-US&gl=US&ceid=US:en",
    "travel":  "https://news.google.com/rss/search?q=korea+travel&hl=en-US&gl=US&ceid=US:en",
    "general": "https://news.google.com/rss/search?q=south+korea&hl=en-US&gl=US&ceid=US:en",
}

REDDIT_FEEDS = {
    "r/korea":           "https://www.reddit.com/r/korea/.rss",
    "r/Living_in_Korea": "https://www.reddit.com/r/Living_in_Korea/.rss",
    "r/KoreanFood":      "https://www.reddit.com/r/KoreanFood/.rss",
}

# US realtime trends, filtered to Korea-related keywords only
GOOGLE_TRENDS_US = "https://trends.google.com/trending/rss?geo=US"

# ═══════════════════════════════════════════════════════
#  Direction 2 — what is trending inside Korea right now
# ═══════════════════════════════════════════════════════
GOOGLE_TRENDS_KR = "https://trends.google.com/trending/rss?geo=KR"

# Korea-relevance filter for the US trends feed
KOREA_HINTS = [
    "korea", "korean", "k-", "seoul", "busan", "kimchi", "kpop", "k-pop",
    "kdrama", "k-drama", "hangul", "soju", "bts", "blackpink", "samsung",
    "hyundai", "kia", "squid game", "bibimbap", "bulgogi", "tteokbokki",
    "gangnam", "hanbok", "chaebol",
]


# ═══════════════════════════════════════════════════════
#  Safety filter — drop sensational / off-brand topics
# ═══════════════════════════════════════════════════════
BLOCK_PATTERNS = [
    # politics
    r"\belection\b", r"\bpresident\b", r"\bimpeach", r"\bparliament\b",
    r"\blawmaker", r"\bprosecutor", r"\bindict", r"\bruling party\b",
    r"\bopposition party\b", r"\bsenate\b", r"\bcongress\b", r"\bballot\b",
    r"political scandal",
    # celebrity gossip / personal
    r"dating scandal", r"\bdivorce", r"\baffair\b", r"\barrest", r"\blawsuit\b",
    r"\bcocaine\b", r"\bnarcotic", r"\bd\.u\.i\b", r"\bdui\b", r"sex scandal",
    # accidents / incidents
    r"\bmurder", r"\bkilled\b", r"\bkilling\b", r"\bsuicide\b", r"\bstabbing\b",
    r"\bshooting\b", r"\bcrash\b", r"\bcollision\b", r"\bblaze\b",
    r"\bcasualt", r"\bfatal", r"\bdisaster\b", r"\bdeadly\b",
    # military conflict (note: "north korea" alone is NOT blocked — culture
    # comparisons are fine; only the military/weapon context is dropped)
    r"\bwar\b", r"\bwartime\b", r"\bmissile", r"\bnuclear\b", r"\bwarhead\b",
    r"\bairstrike\b", r"\btroops\b", r"\barmed forces\b", r"\bweapon",
    r"military drill", r"military provocation", r"military tension",
]
_BLOCK_RE = re.compile("|".join(BLOCK_PATTERNS), re.IGNORECASE)


def _is_safe(text: str) -> bool:
    """Drop politics / gossip / accidents / military conflict."""
    if not text:
        return False
    return _BLOCK_RE.search(text) is None


# ═══════════════════════════════════════════════════════
#  Low-level fetchers
# ═══════════════════════════════════════════════════════
def _get(url: str):
    """GET with one retry on transient connection errors."""
    for attempt in range(2):
        try:
            return requests.get(url, headers=UA, timeout=12)
        except requests.exceptions.ConnectionError:
            if attempt == 1:
                raise
    return None


def _fetch_rss(url: str, limit: int = 20) -> list:
    """Parse an RSS 2.0 feed → [{title, desc}] (Google News / Google Trends)."""
    try:
        r = _get(url)
        if r is None or r.status_code != 200:
            print(f"   [trend] RSS {getattr(r, 'status_code', '??')}: {url[:55]}")
            return []
        root = ET.fromstring(r.content)
        items = []
        for it in root.findall(".//item")[:limit]:
            title_el = it.find("title")
            desc_el = it.find("description")
            title = _html.unescape(title_el.text).strip() if (title_el is not None and title_el.text) else ""
            desc = ""
            if desc_el is not None and desc_el.text:
                desc = re.sub(r"<[^>]+>", "", desc_el.text)
                desc = _html.unescape(desc).strip()[:300]
            if title:
                items.append({"title": title, "desc": desc})
        return items
    except Exception as e:
        print(f"   [trend] RSS fail {url[:40]}: {e}")
        return []


def _fetch_atom(url: str, limit: int = 20) -> list:
    """Parse a Reddit Atom feed → [{title, desc}] (entry/title)."""
    try:
        r = _get(url)
        if r is None or r.status_code != 200:
            print(f"   [trend] Reddit {getattr(r, 'status_code', '??')}: {url[:55]}")
            return []
        root = ET.fromstring(r.content)
        items = []
        for entry in root.findall(f"{ATOM_NS}entry")[:limit]:
            title_el = entry.find(f"{ATOM_NS}title")
            title = _html.unescape(title_el.text).strip() if (title_el is not None and title_el.text) else ""
            if title:
                items.append({"title": title, "desc": ""})
        return items
    except Exception as e:
        print(f"   [trend] Reddit fail {url[:40]}: {e}")
        return []


# ═══════════════════════════════════════════════════════
#  Direction 2 — Korea realtime trends
# ═══════════════════════════════════════════════════════
def fetch_korea_trends(limit: int = 15) -> list:
    """What's trending inside Korea right now (Google Trends KR)."""
    items = _fetch_rss(GOOGLE_TRENDS_KR, limit=limit)
    return [it for it in items if _is_safe(it["title"])]


# ═══════════════════════════════════════════════════════
#  Direction 1 — foreign curiosity about Korea
# ═══════════════════════════════════════════════════════
def fetch_korea_related_us_trends(limit: int = 25) -> list:
    """US realtime trends, filtered to Korea-related keywords only."""
    items = _fetch_rss(GOOGLE_TRENDS_US, limit=limit)
    out = []
    for it in items:
        t = it["title"].lower()
        if any(h in t for h in KOREA_HINTS) and _is_safe(it["title"]):
            out.append(it)
    return out


def fetch_category_news(category: str, limit: int = 12) -> list:
    """
    Collect Direction-1 (foreign-interest) items for an EN category.

    - k-trends           → all EN news topics + all Reddit + Korea-related US trends
    - korean-life        → general news + r/Living_in_Korea
    - culture-explained  → culture news + r/korea
    (essay is never auto-generated, so it is not handled here.)
    """
    results = []

    def _add_news(key):
        for it in _fetch_rss(GOOGLE_NEWS_EN[key], limit=limit):
            if _is_safe(it["title"]) and _is_safe(it["desc"]):
                results.append(it)

    def _add_reddit(key):
        for it in _fetch_atom(REDDIT_FEEDS[key], limit=limit):
            if _is_safe(it["title"]):
                results.append(it)

    if category == "k-trends":
        for k in ("culture", "food", "travel", "general"):
            _add_news(k)
        for k in REDDIT_FEEDS:
            _add_reddit(k)
        results.extend(fetch_korea_related_us_trends(limit=20))
    elif category == "korean-life":
        _add_news("general")
        _add_news("travel")
        _add_reddit("r/Living_in_Korea")
    elif category == "culture-explained":
        _add_news("culture")
        _add_reddit("r/korea")
    else:
        # unknown / essay → fall back to the broad general signal
        _add_news("general")

    return results


# ═══════════════════════════════════════════════════════
#  Two-way fusion → blog topics (Gemini)
# ═══════════════════════════════════════════════════════
CATEGORY_DESC_EN = {
    "k-trends":          "What's trending in Korea right now — viral food, beauty, dramas, fads, the buzz of the moment.",
    "korean-life":       "Real everyday life in Korea — housing, commuting, work, money, food, the practical day-to-day reality.",
    "culture-explained": "The why behind Korean customs — etiquette, social norms, traditions, and the unspoken rules.",
}


def _items_to_text(items: list, max_items: int = 14) -> str:
    text = ""
    for i, it in enumerate(items[:max_items], 1):
        text += f"{i}. {it.get('title', '')}\n"
        if it.get("desc"):
            text += f"   {it['desc']}\n"
    return text.strip() or "(none)"


def convert_trends_to_topics_en(category: str, foreign_interest: list,
                                korea_trends: list, max_topics: int = 3) -> list:
    """
    Fuse Direction-1 (foreign curiosity) × Direction-2 (Korea realtime trends)
    into blog topics for an actual Seoul salaryman to explain.

    Returns: [{"topic": "...", "source_news": "...", "angle": "..."}, ...]
    Empty list on no key / no input / credit depletion (graceful).
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY or not foreign_interest:
        return []

    cat_desc = CATEGORY_DESC_EN.get(category, category)
    foreign_text = _items_to_text(foreign_interest, max_items=16)
    korea_text = _items_to_text(korea_trends, max_items=12)

    prompt = (
        "You are planning blog topics for 'Korean Salaryman' — a blog where an "
        "actual Korean office worker in Seoul explains Korea to foreigners.\n\n"
        f"[What foreigners are currently interested in]\n{foreign_text}\n\n"
        f"[What's trending in Korea right now]\n{korea_text}\n\n"
        "Rules:\n"
        "1. Create topics that CONNECT foreign curiosity with what's actually "
        "happening in Korea now — 'the thing you're curious about? here's what it "
        "looks like on the ground in Korea right now.'\n"
        f"2. Topics must fit category '{category}' ({cat_desc}). If nothing fits "
        "naturally, return fewer or none — never force it.\n"
        "3. Skip politics, celebrity gossip, accidents, anything sensational.\n"
        "4. Each topic must be something a foreigner would actually search or click.\n\n"
        'Output JSON only: [{"topic": "...", "source_news": "...", '
        '"angle": "what value this gives the reader"}]'
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 4000,
            "responseMimeType": "application/json",
        },
    }

    for attempt in range(3):
        try:
            r = requests.post(url, headers={"Content-Type": "application/json"},
                              json=payload, timeout=45)
            if r.status_code in (500, 503):
                # transient overload → backoff retry (503 spikes clear in ~tens of sec)
                print(f"   [trend->topics API {r.status_code}] retry {attempt+1}/3")
                time.sleep(8 * (attempt + 1))
                continue
            if r.status_code == 429:
                # credit/quota depletion → graceful empty (don't crash the run)
                print("   [trend->topics] 429 rate/credit limit → empty")
                return []
            if r.status_code != 200:
                print(f"   [trend->topics API {r.status_code}]")
                return []
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()
            topics = _json.loads(text)
            if isinstance(topics, list):
                valid = [t for t in topics if isinstance(t, dict) and t.get("topic")]
                return valid[:max_topics]
            return []
        except Exception as e:
            print(f"   [trend->topics fail] {e}")
            time.sleep(3)
    return []


# Back-compat shim (older callers passed only foreign news, no korea_trends)
def convert_trends_to_topics(category: str, news_items: list, max_topics: int = 3) -> list:
    return convert_trends_to_topics_en(category, news_items, [], max_topics=max_topics)


# ═══════════════════════════════════════════════════════
#  Standalone test
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 56)
    print("  EN trend pipeline — two-way fusion test")
    print("=" * 56)

    korea = fetch_korea_trends(limit=12)
    print(f"\n[Direction 2] Korea realtime trends: {len(korea)}")
    for it in korea[:6]:
        print(f"   - {it['title'][:55]}")

    for cat in ["k-trends", "korean-life", "culture-explained"]:
        print(f"\n{'='*56}\n  [{cat}] Direction-1 collection\n{'='*56}")
        foreign = fetch_category_news(cat, limit=10)
        print(f"  foreign-interest items: {len(foreign)}")
        for it in foreign[:6]:
            print(f"    - {it['title'][:55]}")

        if foreign and os.getenv("GEMINI_API_KEY"):
            print(f"\n  [{cat}] → fusing into topics...")
            topics = convert_trends_to_topics_en(cat, foreign, korea, max_topics=3)
            print(f"  topics: {len(topics)}")
            for t in topics:
                print(f"    * {t['topic']}")
                print(f"       source: {t.get('source_news','')[:55]}")
                print(f"       angle : {t.get('angle','')[:55]}")
        else:
            print("  (no GEMINI_API_KEY or no items → skip fusion)")
