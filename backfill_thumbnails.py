# -*- coding: utf-8 -*-
"""
backfill_thumbnails.py
──────────────────────
hero_image(썸네일)가 없는 글에 사진을 자동 생성한다. (GitHub Actions 환경 전용)

배경: admin '주제로 글 생성'/'에세이'는 Vercel 서버리스에서 finalize를 돌리는데,
Vercel 파일시스템이 읽기전용(/tmp만 쓰기)이라 thumbnail PNG 저장이 실패 →
get_hero_image가 None을 반환 → hero_image 누락.

해법(방법 B): cron과 동일한 GitHub Actions 환경(쓰기 가능 FS + 한글폰트 + 키)에서
누락 글의 썸네일을 생성·임베드하고 PNG를 posts/thumbnails에 저장한다. static_rebuild.yml
(posts/**.json push 시 발동)에서 generate_static_posts 이전에 실행되어, 새로 커밋된
admin draft가 곧바로 사진을 갖추게 한다.

안전장치:
- idempotent: 이미 thumbnail/hero_image 있는 글은 건너뜀.
- content_raw로 finalize 재실행 → hero 임베드 + thumbnail (더블랩/중복 섹션 방지).
- created_at/status/source/slug/ko_review는 원본 보존(재finalize가 덮어쓰는 값 복원).
- 키/폰트/네트워크 없으면 get_hero_image가 그라데이션으로 폴백(여전히 사진 확보).
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
MANIFEST = POSTS_DIR / "manifest.json"

# 재finalize 후에도 원본을 유지해야 하는 필드
_PRESERVE = ("created_at", "status", "source", "slug", "ko_review")
# 재finalize가 새로 생성하는 파생 필드 — 입력에서 제거해 깨끗이 재조립
_DERIVED = ("jsonld", "seo_title", "seo_description", "seo_keywords", "_references_html")


def main():
    try:
        from automation import get_hero_image, finalize_article
    except Exception as e:  # requests/pillow/dotenv 미설치 등 → 조용히 스킵
        print(f"[backfill] automation import 실패 → 스킵: {e}")
        return

    if not MANIFEST.exists():
        print("[backfill] manifest 없음 → 스킵")
        return

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fixed = 0
    manifest_dirty = False

    for entry in manifest:
        fn = entry.get("filename")
        if not fn or not fn.endswith(".json"):
            continue
        if entry.get("thumbnail"):
            continue  # manifest 기준 이미 썸네일 있음

        path = POSTS_DIR / fn
        if not path.exists():
            continue
        try:
            post = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[backfill] {fn} 읽기 실패: {e}")
            continue

        # 글 JSON에 이미 hero_image/thumbnail 있으면 manifest만 동기화
        existing_url = (post.get("hero_image") or {}).get("url") or post.get("thumbnail")
        if existing_url:
            entry["thumbnail"] = existing_url
            entry["has_image"] = True
            manifest_dirty = True
            continue

        raw = post.get("content_raw")
        if not raw:
            print(f"[backfill] {fn} content_raw 없음 → 안전하게 스킵")
            continue

        title = post.get("title", "")
        cat = post.get("category", "")
        kw = post.get("keyword") or title
        try:
            hero = get_hero_image(cat, kw, title)
        except Exception as e:
            print(f"[backfill] {fn} get_hero_image 실패: {e}")
            continue
        if not hero or not hero.get("url"):
            print(f"[backfill] {fn} 썸네일 생성 실패 → 스킵")
            continue

        # content_raw로 finalize 재실행 (hero 임베드)
        preserve = {k: post.get(k) for k in _PRESERVE}
        article = dict(post)
        article["content"] = raw
        for k in _DERIVED:
            article.pop(k, None)
        try:
            finalized = finalize_article(article, hero_image=hero)
        except Exception as e:
            print(f"[backfill] {fn} finalize 실패: {e}")
            continue
        if not finalized:
            continue

        # 원본 메타 복원
        for k, v in preserve.items():
            if v is not None:
                finalized[k] = v

        path.write_text(json.dumps(finalized, ensure_ascii=False, indent=2), encoding="utf-8")
        entry["thumbnail"] = hero["url"]
        entry["has_image"] = True
        manifest_dirty = True
        fixed += 1
        print(f"[backfill] {fn} 썸네일 생성·임베드 완료: {hero['url']} (source={hero.get('source')})")

    if manifest_dirty:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[backfill] 보강 {fixed}건 → manifest 저장")
    else:
        print("[backfill] 보강 대상 없음")


if __name__ == "__main__":
    main()
