# Korean Salaryman EN — HANDOFF v2.0

> 다음 세션이 **이 문서만 읽고** 전체 맥락을 잡기 위한 인수인계 노트.
> **현재 버전: v2.0 (2026-06-12 ~ 06-19 세션)** — 아래 §0~§7은 v1.0 내용 보존, v2.0 변경은 별도 블록(§§ v2.0).
> 작성 시점 기준 최신 커밋: `eca8fdc`. v1.0 작성 시점 커밋은 `05ce82f`.

---

## §0 정체성

- **사이트**: en.koreansalaryman.com
- **repo**: `daehongpark/korean-salaryman-en`
- **호스팅**: Vercel **별도 프로젝트** (본진 koreansalaryman.com SEO와 격리)
- **컨셉**: "Korea, as we actually live it" — 서울 현직 직장인 1인칭이 외국인에게 한국을 설명. **실명·회사명·구체 수익 금지.**
- **카테고리 비중**: `k-trends` 0.40 / `korean-life` 0.35 / `culture-explained` 0.25 / `essay` 0.00 (에세이는 박대홍이 직접 작성)
- **운영 리듬**: 하루 1편 **draft** 생성 (cron 12:00 UTC = 21:00 KST) → 박대홍이 admin에서 검수 후 수동 발행.

## §1 핵심 시스템

- **양방향 트렌드** (`trend_pipeline.py`):
  - 방향1 — 외국인 관심사: 구글뉴스 EN 4쿼리 + 레딧 3종 Atom 피드 + Google Trends US(한국 필터)
  - 방향2 — 한국 내 트렌드: 트렌드 KR
  - `convert_trends_to_topics_en` 가 Gemini로 두 방향을 융합해 영어 주제 생성.
- **ko_review**: 완성된 영어 글의 **한글 전체 번역**을 글 JSON에 저장. **admin 검수 전용 — 발행 HTML엔 절대 미포함.**
- **영어 페르소나**: `prompt_template.json` 가 단일 소스.

## §2 디자인 (Pudding × Dazed)

- **팔레트**: `#FFFFFF` / `#0A0A0A` / `#FF3D00`(포인트) / `#6B6B6B` / `#F6F5F2`
- **타이포**: Archivo Black 대문자 헤드라인 + Inter 본문 + Noto Sans KR 900 한글 액센트
- 히어로 아웃라인 텍스트 "월급쟁이", 카테고리 라벨 한글 병기
- **절제 원칙**: 그림자·그라데이션 금지 (미니멀 유지)

## §3 admin (`admin.html`)

- 🇰🇷 **한글 검수본**: 편집 화면 하단 접이식 패널, `ko_review` 보존(편집해도 안 날아감)
- ✍️ **에세이 작성**: 한글 입력 → 페르소나 영어로 변환, 원문 한글은 `ko_review`에 저장
- 🤖 **주제 글생성**: `/prompt_template.json` fetch(단일 소스) → `finalize-post` API로 조립
- geminiKey 는 브라우저 `localStorage` 보관

## §4 공유 활성화 (커밋 `501aeb2`)

- X / Reddit / Facebook / WhatsApp / Copy **5채널**
- 모바일 `navigator.share` 네이티브 공유
- 글 끝 CTA + 인용구(selection) 공유
- OG 폴백 이미지 `/assets/og-default.png`

## §5 함정 / 구조 ⚠️ (반드시 숙지)

- **post.html = `generate_static_posts.py` 템플릿**. 치환 마커 **24종 절대 보존** (지우면 정적 생성 깨짐).
- **썸네일**:
  - **원본 저장 위치는 `hero_image.url`**. (개선: `finalize_article`이 top-level `thumbnail` 필드에도 복사 → 자체 완결형 JSON)
  - 3단 폴백: Gemini 이미지(현재 404 상태) → Unsplash(키 없으면 skip) → **그라데이션**.
  - ⚠️ **"썸네일 없음"처럼 보여도 먼저 `hero_image`를 확인할 것.** (글 JSON에 top-level `thumbnail`이 없다고 미생성으로 오진한 사례 있음 — 실제로는 hero_image에 정상 존재했음)
- **ko_review 번역**: `maxOutputTokens 16384` + `thinkingConfig.thinkingBudget 0`.
  - 함정: `gemini-2.5-flash`는 thinking 토큰이 출력 한도를 잠식 → 긴 글에서 번역이 잘림. thinking을 꺼서 출력 한도 전부를 본문에 사용 (잘림 버그 `05ce82f`에서 수정됨).
  - `finishReason == MAX_TOKENS`면 경고 로그 출력 + multi-part 안전 추출.
- **slug**: admin에서 비워두면 `static_rebuild`가 self-healing 으로 채움.
- **Vercel**: Framework Preset **반드시 "Other"** (api 함수 인식됨). `functions` 선언과 `api/` 실제 파일 **일치 필수**.
- **도메인**: 가비아 CNAME `en` → `50961977ce2baa06.vercel-dns-017.com`
- **Secrets**:
  - GitHub: `GEMINI_API_KEY`, `GH_PAT`, `UNSPLASH_ACCESS_KEY`(예정)
  - Vercel: `GH_PAT`, `GEMINI_API_KEY`, `SCHEDULED_PUBLISH_SECRET`(**EN 전용 새 값** — 본진과 다름), `UNSPLASH`(예정)
- **`.env` 로컬 전용 — push 절대 금지** (`.gitignore`에 등록됨).

## §6 PENDING

- [ ] 박대홍 첫 검수 → 발행 (현재 draft 2편: **울릉도**, **Cost of Living in Seoul**)
- [ ] **Unsplash 키 수정 ⚠️**: `UNSPLASH_ACCESS_KEY` secret이 등록은 됐으나 **401 Unauthorized** 반환(키 값 무효 — Unsplash 대시보드의 "Access Key"가 맞는지, Secret Key와 혼동 아닌지 확인). 현재는 401→그라데이션 폴백으로 정상 동작 중. (2026-06-12 force 검증 run `27391652047`에서 확인)
- [ ] 수동 강제 생성: `gh workflow run daily_post.yml -f force=true` (FORCE_POST로 일일 가드 우회 — 검증용)
- [ ] cron 안정성 관찰
- [ ] cron-job.org 백업 트리거 (선택)
- [ ] 예약발행 쓰려면 `SCHEDULED_PUBLISH_SECRET` 호출측 설정 필요
- 본진(koreansalaryman.com)은 별도 HANDOFF v3.8 참조

# ═══════════════════════════════════════════
# v2.0 (2026-06-12 ~ 06-19 세션)
# ═══════════════════════════════════════════

> v1.0 §6 PENDING 처리 결과: Unsplash 401 → §v2.0-5에서 Access Key 교체로 해결, 예약발행 SECRET/워크플로 → §v2.0-6에서 신설, cron 안정성 → §v2.0-6에서 KST→UTC 수정. 미해결은 아래 v2.0 PENDING으로 이월.

## §v2.0-1. 전면 리디자인 (The Pudding × Dazed)  커밋 `8c48a58`
- **토큰**: `--paper #FFF` / `--ink #0A0A0A` / `--accent #FF3D00` / `--gray #6B6B6B` / `--surface #F6F5F2`
- **타입**: Archivo Black(대문자 헤드라인) / Inter(본문) / Noto Sans KR 900(한글 액센트)
- **시그니처**: 히어로 아웃라인 "월급쟁이" + 카테고리 한글 병기(트렌드 = K-TRENDS 등)
- ⚠️ `post.html`은 `generate_static_posts.py` 템플릿 — **치환 마커 24종 보존 필수**(§5와 동일).

## §v2.0-2. 공유 장치  커밋 `501aeb2`
- **5채널**(X / Reddit / Facebook / WhatsApp / Copy) + `navigator.share` 모바일 네이티브 + 글 끝 CTA + 인용구 selection 공유 + OG 폴백 카드(`/assets/og-default.png`).

## §v2.0-3. admin 강화  커밋 `1213a32`,`2180794`,`e1e8800`,`5f865d8`
- **UI 전체 한국어화** (박대홍 전용).
- 🇰🇷 **한글 검수본 칸**(`ko_review` read-only, 편집 저장 시 보존).
- ✍️ **에세이 작성**(한글→영어 변환) + ✨ **다듬기**(한글 윤문, `polishEssay`).
- 🤖 **주제로 글 생성**(`/prompt_template.json` fetch 단일 소스).
- 글 편집 시 🇰🇷 **한글로 수정→영어 번역**(`translateEdit`, 부분수정 지원).
- 모든 Gemini 호출 `maxOutputTokens 16384` + `thinkingBudget 0`.

## §v2.0-4. 글 생성 품질 (admin 경로)  커밋 `b08d665`,`e642f52`,`c71e679`
- **★ 사진**: Vercel 서버리스 FS가 읽기전용이라 `finalize-post`가 썸네일 저장 실패 → **`backfill_thumbnails.py`로 GitHub Actions(static_rebuild)에서 사진 생성+커밋**하는 방식으로 우회 (Vercel에서는 사진 안 만듦).
- `finalize_article`: `hero_image`/`body_images`가 None이면 자체 생성(`get_hero_image`/`get_body_images`).
- **시의성/사실성**: `api/news.js`로 구글뉴스 실시간 헤드라인 주입 + today 날짜 + 날조 금지 가드 + 익명화(Coach X) 금지.
- **본문 이미지 3장 삽입** (cron 경로는 됐는데 admin 경로에서 누락이던 것 수정).

## §v2.0-5. 배포 / 인프라
- **Vercel 배포 완료**, Framework Preset **Other 필수**, api 폴더 복사(scheduled-publish `REPO=en`).
- **도메인 `en.koreansalaryman.com`** (가비아 CNAME `en` → `50961977ce2baa06.vercel-dns-017.com`).
- **GSC 등록**(소유권 자동 확인) + **sitemap 제출 성공**.
- **Unsplash**: Secret Key를 잘못 넣어 401이던 것 → **Access Key로 교체 해결**(실사진 정상). v1.0 §6 PENDING 해소.

## §v2.0-6. cron / 예약발행 안정화
- **★ cron KST/UTC 버그 수정** 커밋 `81a62d0`: GitHub Actions 지연으로 글이 KST 다음날로 찍혀 다음날 cron이 SKIP → **`_already_ran_today` UTC 기준**으로 변경. **★ EN은 UTC, 본진은 KST — cron 타이밍이 반대라 서로 패치 교차 적용 금지.**
- **예약발행 워크플로 신설**(`scheduled_publish.yml`, 본진 복사 `REPO=en`) + `SCHEDULED_PUBLISH_SECRET` 필요.
- **push 레이스 수정**(concurrency + pull-rebase 5회) static_rebuild / daily_post. 커밋 `cac2ea2`.

## §v2.0-7. 뉴스레터  커밋 `4601120`→`af9d5a6`
- **Supascribe 임베드** (id: **626540047570**, 로더 `js.supascribe.com`). Substack 직접 연결 403 → 임베드로 교체.
- **★ 영어 구독 실테스트 통과** (이메일 수신 확인됨).

---

## §v2.0-PENDING (v2.0 이후 — 다음 세션 할 일)

1. **Supascribe 폼 디자인 커스텀** — 기본 디자인이면 대시보드에서 `#FF3D00` 등 토큰 맞추기.
2. **Vercel Redeploy** — 예약발행 SECRET 반영.
3. **예약발행 실작동 확인** — Actions 초록불.
4. **발행 글 색인 요청** — GSC, 발행마다 1개.
5. **트렌드 503 안정화가 EN에도 적용됐는지 확인** — 본진 `5d3c8bc` 패턴(재시도 5회+백오프 45s+thinkingBudget 0). 참고: EN은 `195ad22`에서 503 안정화 일부 이식됨 — 본진 최신 패턴과 일치하는지 대조 필요.

---

## §7 운영 규칙

- 강제승인 모드 — 먼저 묻지 않기
- 시간·컨디션 추정 금지
- 추측하지 말고 **데이터로 확인**
- 실명·회사명 금지
- 비용: 월 1만원 통합 한도

---

*v2.0 작성 완료. 다음 세션은 §v2.0-PENDING부터.*
