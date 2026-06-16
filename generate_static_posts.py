# -*- coding: utf-8 -*-
"""
글 정적화 A단계 — 정적 HTML 생성기.

post.html 을 템플릿으로 읽어, posts/manifest.json 의 status=published 글마다
/p/{id}.html 정적 페이지를 생성한다. (CSR fetch 렌더링 → 크롤러가 완성본을 바로 봄)

- 메타태그(title/description/og/twitter/canonical) 정적 치환
- JSON-LD BlogPosting 정적 삽입
- 본문 콘텐츠(hero/summary/body) 정적 삽입
- post.html 의 fetch 렌더링 블록 제거, 인터랙션 JS(조회수/공유/댓글/네비) 유지

의존성 추가 없음 (표준 라이브러리 + 정규식 문자열 치환만).
사이트 링크 교체/sitemap/리다이렉트/자동화 연결은 B단계.
"""
import json
import re
import math
import html
import os
import unicodedata
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(ROOT, "post.html")
MANIFEST_PATH = os.path.join(ROOT, "posts", "manifest.json")
POSTS_DIR = os.path.join(ROOT, "posts")
OUT_DIR = os.path.join(ROOT, "p")
ARCHIVE_PATH = os.path.join(ROOT, "archive.html")
SITE = "https://en.koreansalaryman.com"

# 카테고리 표시 라벨 (index/blog 푸터와 동일 순서·표시명)
CATEGORY_LABELS = [
    ("k-trends",          "K-Trends"),
    ("korean-life",       "Korean Life"),
    ("culture-explained", "Culture Explained"),
    ("essay",             "Essays"),
]


def esc_attr(s):
    """HTML 속성값용 이스케이프."""
    return html.escape(str(s or ""), quote=True)


def esc_text(s):
    """HTML 텍스트 노드용 이스케이프."""
    return html.escape(str(s or ""), quote=False)


def set_attr_by_id(doc, elem_id, attr, value):
    """id 로 태그를 찾아 attr="..." 를 value 로 치환 (정규식, 1회)."""
    tag_re = re.compile(r'<[^>]*\bid="' + re.escape(elem_id) + r'"[^>]*>')

    def repl_tag(m):
        tag = m.group(0)
        attr_re = re.compile(r'\b' + re.escape(attr) + r'="[^"]*"')
        if attr_re.search(tag):
            return attr_re.sub(lambda _: attr + '="' + value + '"', tag, count=1)
        # 속성이 없으면 닫는 > 앞에 삽입
        return tag[:-1] + ' ' + attr + '="' + value + '">'

    return tag_re.sub(repl_tag, doc, count=1)


def make_slug(title, existing):
    """제목 → 한글 슬러그. 한글/영문/숫자만 남기고 공백→하이픈, 최대 50자, 중복 시 -2."""
    s = unicodedata.normalize("NFC", title or "")
    s = s.lower()  # 영어 제목 소문자화 (한글은 영향 없음)
    s = re.sub(r"[^\w가-힣\s-]", "", s)    # 특수문자 제거 (한글/영문/숫자/공백/하이픈만)
    s = re.sub(r"[\s_]+", "-", s.strip())  # 공백→하이픈
    s = re.sub(r"-{2,}", "-", s).strip("-")
    s = s[:50].rstrip("-")
    if not s:
        s = "post"
    base, n = s, 2
    while s in existing:
        s = "%s-%d" % (base, n)
        n += 1
    return s


# ── 옛 /p/post_xxx.html → 슬러그 주소 리다이렉트 stub ──
STUB = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="%(new_url)s">
<meta http-equiv="refresh" content="0;url=%(new_url)s">
<script>location.replace("%(new_url)s");</script>
</head><body><p><a href="%(new_url)s">Go to the new address</a></p></body></html>"""


MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def format_date_kr(iso):
    """JS formatDate 와 동일: YYYY년 M월 D일."""
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(iso)
    except ValueError:
        try:
            d = datetime.fromisoformat(iso.split(".")[0])
        except Exception:
            return ""
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def read_time(content):
    """JS readTime 와 동일: max(1, ceil(len/500)) + '분'."""
    return "%d min" % max(1, math.ceil(len(content or "") / 500))


def text_to_html(text):
    """JS textToHtml 폴백: 빈 줄 기준 단락 분리."""
    parts = re.split(r"\n\n+", text or "")
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append("<p>" + p.replace("\n", "<br>") + "</p>")
    return "".join(out)


# ── 정적 인터랙션 init (fetch 렌더링 블록 대체) ──────────────────
# 조회수/댓글/이전다음/관련글만 manifest 기반으로 동작. 본문은 이미 정적 렌더됨.
# 주의: manifest fetch 는 작은따옴표 사용 (백틱 fetch 제거 검증과 무관).
STATIC_INIT = r"""// Static prerendered page: initialize interactions only (fetch rendering removed)
const postId = "%(filename)s";
updateViewCount(postId);
renderComments(postId);

fetch('./posts/manifest.json')
  .then(r => r.json())
  .then(manifest => {
    renderPostNav(manifest, postId);
    const currentCat = "%(category)s";
    const related = manifest
      .filter(p => p.status === 'published' && p.filename !== postId && p.category === currentCat)
      .slice(0, 4);
    const relBox = document.getElementById('relatedPosts');
    if (relBox) {
      if (related.length === 0) {
        relBox.innerHTML = '<p style="font-size:13px;color:var(--text3);">No related posts yet.</p>';
      } else {
        relBox.innerHTML = related.map(p => `
          <a class="rel-item" href="/p/${encodeURIComponent(p.slug || p.filename.replace(/\.json$/,''))}.html">
            <div class="rel-dot"></div>
            <div>
              <div class="rel-title">${p.title}</div>
              <div class="rel-cat">${formatDate(p.created_at)}</div>
            </div>
          </a>`).join('');
      }
    }
  })
  .catch(err => console.error(err));
"""


def build_page(template, post, filename, slug, manifest_entry):
    title = post.get("title") or ""
    category = post.get("category") or ""
    created = post.get("created_at") or ""
    summary = post.get("summary") or ""
    tags = post.get("tags") or []
    content = post.get("content") or ""

    # 주소는 슬러그 기반 (HTML 안에서는 한글 URL 그대로 — 가독성·공유 우선)
    page_url = "%s/p/%s.html" % (SITE, slug)

    # ── pageTitle / pageDesc (post.html JS 로직과 동일) ──
    page_title = post.get("seo_title") or ("%s | Korean Salaryman" % title)
    if post.get("seo_description"):
        page_desc = post["seo_description"]
    elif summary:
        page_desc = summary[:150].replace("\n", " ") + " | Korean Salaryman"
    else:
        page_desc = "An honest look at %s in Korea, from a salaryman in Seoul. Read it on Korean Salaryman." % (category or "Korea")

    # ── og:image (manifest thumbnail → hero_image.url → brand OG fallback) ──
    thumb = (manifest_entry or {}).get("thumbnail")
    if not thumb:
        hero = post.get("hero_image")
        if isinstance(hero, dict):
            thumb = hero.get("url")
    # No post thumbnail → fall back to the branded default OG card.
    og_image = (SITE + thumb) if thumb else (SITE + "/assets/og-default.png")

    doc = template

    # 1) <title>
    doc = doc.replace(
        "<title>Korean Salaryman</title>",
        "<title>%s</title>" % esc_text(page_title),
        1,
    )

    # 2) meta description (id 없음 → 정규식)
    doc = re.sub(
        r'<meta name="description" content="[^"]*">',
        lambda _: '<meta name="description" content="%s">' % esc_attr(page_desc),
        doc,
        count=1,
    )

    # 3) canonical href
    doc = set_attr_by_id(doc, "canonicalTag", "href", esc_attr(page_url))

    # 4) og / twitter 메타 (id 기반)
    doc = set_attr_by_id(doc, "ogTitle", "content", esc_attr(page_title))
    doc = set_attr_by_id(doc, "ogDesc", "content", esc_attr(page_desc))
    doc = set_attr_by_id(doc, "ogUrl", "content", esc_attr(page_url))
    doc = set_attr_by_id(doc, "ogPublished", "content", esc_attr(created))
    doc = set_attr_by_id(doc, "ogSection", "content", esc_attr(category))
    doc = set_attr_by_id(doc, "twTitle", "content", esc_attr(page_title))
    doc = set_attr_by_id(doc, "twDesc", "content", esc_attr(page_desc))
    if og_image:
        doc = set_attr_by_id(doc, "ogImage", "content", esc_attr(og_image))
        doc = set_attr_by_id(doc, "twImage", "content", esc_attr(og_image))

    # 5) JSON-LD BlogPosting (post.html JS 구조와 동일) → </head> 직전 삽입
    json_ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": page_desc,
        "url": page_url,
        "datePublished": created,
        "dateModified": created,
        "author": {
            "@type": "Person",
            "name": "Korean Salaryman",
            "url": "https://en.koreansalaryman.com/about.html",
        },
        "publisher": {
            "@type": "Organization",
            "name": "Korean Salaryman",
            "url": "https://en.koreansalaryman.com",
        },
        "keywords": ", ".join(tags),
        "articleSection": category,
        "inLanguage": "en-US",
        "mainEntityOfPage": {"@type": "WebPage", "@id": page_url},
    }
    ld_json = json.dumps(json_ld, ensure_ascii=False).replace("</", "<\\/")
    ld_block = '<script type="application/ld+json">%s</script>\n</head>' % ld_json
    doc = doc.replace("</head>", ld_block, 1)

    # 6) __PRERENDERED__ 플래그 (본문 데이터 직전)
    doc = doc.replace(
        '<div id="postHero" class="post-hero" style="display:none">',
        '<script>window.__PRERENDERED__ = true;</script>\n'
        '<div id="postHero" class="post-hero" style="display:block">',
        1,
    )

    # 7) 스켈레톤 숨김
    doc = doc.replace(
        '<div id="loadingSkeleton" style="max-width:1080px;margin:40px auto;padding:0 24px;">',
        '<div id="loadingSkeleton" style="max-width:1080px;margin:40px auto;padding:0 24px;display:none;">',
        1,
    )

    # 8) postLayout 표시
    doc = doc.replace(
        '<div id="postLayout" class="post-layout" style="display:none">',
        '<div id="postLayout" class="post-layout" style="display:grid">',
        1,
    )

    # 9) hero 채우기
    doc = doc.replace(
        '<span id="heroCat"></span>',
        '<span id="heroCat">%s</span>' % esc_text(category), 1)
    doc = doc.replace(
        '<div id="heroCatPill" class="post-cat-pill"></div>',
        '<div id="heroCatPill" class="post-cat-pill">%s</div>' % esc_text(category), 1)
    doc = doc.replace(
        '<h1 id="heroTitle"></h1>',
        '<h1 id="heroTitle">%s</h1>' % esc_text(title), 1)
    doc = doc.replace(
        '<span class="post-meta-info" id="heroDate"></span>',
        '<span class="post-meta-info" id="heroDate">%s</span>' % esc_text(format_date_kr(created)), 1)
    doc = doc.replace(
        '<span class="post-meta-info" id="heroReadTime"></span>',
        '<span class="post-meta-info" id="heroReadTime">Read time %s</span>' % esc_text(read_time(content)), 1)

    # 10) 요약
    if summary:
        summary_html = ('<div class="article-summary" id="articleSummary">'
                        '<div class="article-summary-label">SUMMARY</div>'
                        '<p>%s</p></div>') % summary.replace("\n", "<br>")
        doc = doc.replace(
            '<div class="article-summary" id="articleSummary"></div>', summary_html, 1)
    else:
        doc = doc.replace(
            '<div class="article-summary" id="articleSummary"></div>',
            '<div class="article-summary" id="articleSummary" style="display:none"></div>', 1)

    # 11) 본문 (HTML 이면 그대로, 아니면 textToHtml 폴백)
    if content.strip().startswith("<"):
        body_html = content
    else:
        body_html = text_to_html(content)
    doc = doc.replace(
        '<div class="article-body" id="articleBody"></div>',
        '<div class="article-body" id="articleBody">%s</div>' % body_html, 1)

    # 12) submitComment 의 postId 추출을 전역 postId 로 (정적 페이지엔 ?id= 없음)
    doc = doc.replace(
        "  const postId = new URLSearchParams(window.location.search).get('id');",
        "  // postId is injected statically (using the global)", 1)

    # 13) fetch 렌더링 실행 블록 제거 → 정적 init 으로 교체
    marker = "// Extract post ID from URL parameters"
    mi = doc.find(marker)
    if mi == -1:
        raise RuntimeError("fetch 렌더링 마커를 찾지 못함")
    si = doc.find("</script>", mi)
    if si == -1:
        raise RuntimeError("</script> 종료 태그를 찾지 못함")
    init_js = STATIC_INIT % {"filename": filename, "category": esc_attr(category)}
    doc = doc[:mi] + init_js + doc[si:]

    # 14) 상대경로 → 절대경로 (정적본은 /p/ 하위라 상대경로 깨짐)
    rel_pages = ["index.html", "blog.html", "about.html", "class.html",
                 "challenge.html", "income.html", "privacy.html", "terms.html"]
    for page in rel_pages:
        doc = doc.replace('href="%s' % page, 'href="/%s' % page)
    # fetch 경로 절대화 (작은따옴표/큰따옴표/백틱 모두)
    doc = doc.replace("fetch('./posts/", "fetch('/posts/")
    doc = doc.replace('fetch("./posts/', 'fetch("/posts/')
    doc = doc.replace("fetch(`./posts/", "fetch(`/posts/")

    return slug, doc


# ── 정적 글 목록 페이지(archive.html) — 크롤러 진입점 ──────────────
# JS fetch 없이 순수 HTML 링크. 크롤러가 즉시 전체 /p/ 글 경로를 발견하게 한다.
ARCHIVE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>All Posts — Korean Salaryman</title>
<meta name="description" content="Every post on Korean Salaryman, grouped by category — K-Trends, Korean Life, Culture Explained, and Essays.">
<link rel="canonical" href="https://en.koreansalaryman.com/archive.html">
<meta property="og:title" content="All Posts — Korean Salaryman">
<meta property="og:description" content="Every post on Korean Salaryman, grouped by category.">
<meta property="og:url" content="https://en.koreansalaryman.com/archive.html">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@300;400;500;600;700&family=Noto+Sans+KR:wght@700;900&display=swap" rel="stylesheet">
<style>
:root{--paper:#FFFFFF;--ink:#0A0A0A;--accent:#FF3D00;--muted:#666;--line:#e5e5e5;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',sans-serif;background:var(--paper);color:var(--ink);line-height:1.7;-webkit-font-smoothing:antialiased;}
a{color:inherit;text-decoration:none;}
.display{font-family:'Archivo Black',sans-serif;text-transform:uppercase;letter-spacing:-0.01em;line-height:0.98;}
header{position:sticky;top:0;z-index:100;background:rgba(255,255,255,0.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--ink);}
.hdr-in{max-width:1080px;margin:0 auto;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;}
.logo{font-family:'Archivo Black',sans-serif;text-transform:uppercase;font-size:16px;letter-spacing:-0.01em;color:var(--ink);}
.logo .dot{color:var(--accent);}
.hdr-nav a{font-size:13px;font-weight:600;color:var(--ink);margin-left:18px;text-transform:uppercase;letter-spacing:0.02em;}
.hdr-nav a:hover{color:var(--accent);}
.wrap{max-width:1080px;margin:0 auto;padding:56px 24px 72px;}
.page-title{font-size:44px;margin-bottom:10px;}
.page-sub{font-size:15px;color:var(--muted);margin-bottom:48px;}
.cat-block{margin-bottom:44px;}
.cat-head{font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:var(--accent);font-weight:700;padding-bottom:10px;border-bottom:2px solid var(--ink);margin-bottom:4px;}
.cat-count{color:var(--muted);font-weight:500;margin-left:8px;}
ul.post-list{list-style:none;}
ul.post-list li{padding:14px 2px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap;}
ul.post-list li a{font-size:17px;font-weight:600;}
ul.post-list li a:hover{color:var(--accent);}
.post-date{font-size:13px;color:var(--muted);white-space:nowrap;}
footer{border-top:1px solid var(--ink);padding:32px 24px;margin-top:32px;}
.ft-in{max-width:1080px;margin:0 auto;display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;font-size:13px;color:var(--muted);}
.ft-in a:hover{color:var(--accent);}
</style>
</head>
<body>
<header>
  <div class="hdr-in">
    <a href="/index.html" class="logo">KOREAN<span class="dot">.</span>SALARYMAN</a>
    <nav class="hdr-nav">
      <a href="/index.html">Home</a>
      <a href="/blog.html">Blog</a>
      <a href="/archive.html">All Posts</a>
    </nav>
  </div>
</header>
<main class="wrap">
  <h1 class="display page-title">All Posts</h1>
  <p class="page-sub">Every post on Korean Salaryman, grouped by category. (__TOTAL__ total)</p>
__BODY__
</main>
<footer>
  <div class="ft-in">
    <span>&copy; 2026 Korean Salaryman. All rights reserved.</span>
    <span><a href="/index.html">Home</a> · <a href="/blog.html">Blog</a> · <a href="/about.html">About</a> · en.koreansalaryman.com</span>
  </div>
</footer>
</body>
</html>
"""


def generate_archive(manifest):
    """published 전체 글을 카테고리별 정적 링크 목록(archive.html)으로 생성."""
    published = [m for m in manifest if m.get("status") == "published"]

    groups = {}
    for m in published:
        cat = m.get("category") or "Other"
        groups.setdefault(cat, []).append(m)

    label_map = dict(CATEGORY_LABELS)
    ordered_keys = [k for k, _ in CATEGORY_LABELS if k in groups]
    for k in groups:  # 알 수 없는 카테고리는 뒤에 그대로 추가
        if k not in label_map and k not in ordered_keys:
            ordered_keys.append(k)

    blocks = []
    total_links = 0
    for k in ordered_keys:
        items = sorted(groups[k], key=lambda x: (x.get("created_at") or ""), reverse=True)
        label = label_map.get(k, k)
        rows = []
        for it in items:
            slug = it.get("slug") or it["filename"][:-5]
            title = esc_text(it.get("title") or "(untitled)")
            date = esc_text(format_date_kr(it.get("created_at") or ""))
            rows.append(
                '      <li><a href="/p/%s.html">%s</a><span class="post-date">%s</span></li>'
                % (esc_attr(slug), title, date)
            )
            total_links += 1
        block = (
            '  <section class="cat-block">\n'
            '    <h2 class="cat-head">%s<span class="cat-count">%d posts</span></h2>\n'
            '    <ul class="post-list">\n%s\n    </ul>\n'
            '  </section>'
        ) % (esc_text(label), len(items), "\n".join(rows))
        blocks.append(block)

    body = "\n".join(blocks) if blocks else "  <p>No published posts yet.</p>"
    doc = ARCHIVE_TEMPLATE.replace("__BODY__", body).replace("__TOTAL__", str(total_links))
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        f.write(doc)
    print("archive.html 생성:", total_links, "개 글 링크 /", len(ordered_keys), "개 카테고리")
    return total_links


def main():
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    by_name = {m["filename"]: m for m in manifest}
    published = [m for m in manifest if m.get("status") == "published"]

    # ── slug 부여 (self-healing): slug 없는 published 글에 제목 기반 슬러그 영구 기록 ──
    existing_slugs = set(m["slug"] for m in manifest if m.get("slug"))
    new_slugs = 0
    for entry in manifest:
        if entry.get("status") == "published" and not entry.get("slug"):
            slug = make_slug(entry.get("title", ""), existing_slugs)
            entry["slug"] = slug
            existing_slugs.add(slug)
            new_slugs += 1
    if new_slugs:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print("slug 신규 부여:", new_slugs, "건 → manifest.json 저장")

    os.makedirs(OUT_DIR, exist_ok=True)

    generated = skipped = failed = stubs = 0
    fail_list = []
    for entry in published:
        filename = entry["filename"]
        slug = entry.get("slug") or filename[:-5]
        path = os.path.join(POSTS_DIR, filename)
        if not os.path.exists(path):
            skipped += 1
            print("SKIP (파일 없음):", filename)
            continue
        try:
            with open(path, encoding="utf-8") as f:
                post = json.load(f)
            out_slug, doc = build_page(template, post, filename, slug, by_name.get(filename))
            out_path = os.path.join(OUT_DIR, out_slug + ".html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(doc)
            generated += 1
            # 옛 /p/post_xxx.html 자리에 새 슬러그로 보내는 리다이렉트 stub
            old_pid = filename[:-5] if filename.endswith(".json") else filename
            if old_pid != out_slug:
                stub_html = STUB % {"new_url": "/p/%s.html" % out_slug}
                with open(os.path.join(OUT_DIR, old_pid + ".html"), "w", encoding="utf-8") as f:
                    f.write(stub_html)
                stubs += 1
        except Exception as e:  # 한 글 실패해도 전체 중단 X
            failed += 1
            fail_list.append((filename, str(e)))
            print("FAIL:", filename, "->", e)

    # ── 정적 글 목록(archive.html) 생성 — 크롤러 진입점 ──
    archive_links = generate_archive(manifest)

    print("\n=== 정적 생성 결과 ===")
    print("published 대상:", len(published))
    print("생성(슬러그):", generated)
    print("리다이렉트 stub:", stubs)
    print("archive.html 글 링크:", archive_links)
    print("스킵:", skipped)
    print("실패:", failed)
    if fail_list:
        print("실패 목록:")
        for fn, err in fail_list:
            print("  -", fn, ":", err)


if __name__ == "__main__":
    main()
