"""
generate_sitemap.py
───────────────────
posts/manifest.json을 읽어 sitemap.xml을 자동 생성합니다.
automation.py 실행 후 자동 호출하거나 단독 실행 가능.

실행: python generate_sitemap.py
"""

import json
from pathlib import Path
from datetime import datetime

# ── 설정 ──────────────────────────────────────────────
BASE_URL   = "https://en.koreansalaryman.com"
SCRIPT_DIR = Path(__file__).parent
BLOG_DIR   = SCRIPT_DIR.parent / "korean-salaryman-en"
MANIFEST   = BLOG_DIR / "posts" / "manifest.json"
OUTPUT     = BLOG_DIR / "sitemap.xml"

# 고정 페이지 (priority, changefreq)
# ★ income.html/challenge.html/class.html은 본진(koreansalaryman.com) 전용 페이지라
#   이 EN 사이트에는 파일 자체가 없다 — 예전엔 이 목록에 그대로 남아 있어서
#   sitemap이 존재하지 않는 URL 3개를 제출하고 있었다(404).
STATIC_PAGES = [
    ("",           "1.0",  "daily"),
    ("blog",       "0.95", "daily"),
    ("archive",    "0.9",  "daily"),
    ("about",      "0.8",  "monthly"),
]

# 카테고리 페이지 — EN 사이트 실제 카테고리 4개.
# ★ 예전엔 본진(koreansalaryman.com)의 7개 카테고리(money/ai/startup/finance/
#   realestate/trending/book)가 그대로 남아 있었다 — 이 사이트엔 해당 페이지가
#   없어 전부 404였고, 정작 실제로 존재하는 EN 카테고리는 누락돼 있었다.
CATEGORY_PAGES = [
    "category-essay",
    "category-korean-life",
    "category-k-trends",
    "category-culture-explained",
]


def generate_sitemap():
    today = datetime.now().strftime("%Y-%m-%d")

    urls = []

    # 고정 페이지
    for path, priority, changefreq in STATIC_PAGES:
        url = f"{BASE_URL}/{path}"
        urls.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

    # 카테고리 페이지 (7개)
    for path in CATEGORY_PAGES:
        url = f"{BASE_URL}/{path}"
        urls.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>
  </url>""")

    # 발행된 글 페이지
    if MANIFEST.exists():
        try:
            posts = json.loads(MANIFEST.read_text(encoding="utf-8"))
            published = [p for p in posts if p.get("status") == "published"]
            print(f"  발행된 글: {len(published)}개")

            for post in published:
                filename = post.get("filename", "")
                if not filename:
                    continue
                date = (post.get("created_at") or today)[:10]
                slug = post.get("slug")
                # cleanUrls:true가 .html → 무확장으로 308 리다이렉트하므로, 리다이렉트
                # 없이 바로 200이 되는 최종 주소를 sitemap에 실어야 canonical과 일치한다.
                loc  = f"{BASE_URL}/p/{slug}" if slug else f"{BASE_URL}/p/{filename.replace('.json', '')}"
                urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>""")
        except Exception as e:
            print(f"  [경고] manifest 읽기 실패: {e}")
    else:
        print("  [경고] manifest.json 없음 — 정적 페이지만 포함")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">

{chr(10).join(urls)}

</urlset>"""

    OUTPUT.write_text(sitemap, encoding="utf-8")
    print(f"  sitemap.xml 생성 완료: {len(urls)}개 URL")
    print(f"  저장 위치: {OUTPUT}")
    return len(urls)


if __name__ == "__main__":
    print(f"\n{'='*48}")
    print(f"  sitemap.xml 생성 시작")
    print(f"{'='*48}")
    count = generate_sitemap()
    print(f"\n  완료! 총 {count}개 URL 포함")
    print(f"  → Google Search Console에 제출: {BASE_URL}/sitemap.xml")
    print(f"{'='*48}\n")
