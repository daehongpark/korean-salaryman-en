# Korean Salaryman EN — HANDOFF v1.0

> 다음 세션이 **이 문서만 읽고** 전체 맥락을 잡기 위한 인수인계 노트.
> 작성 시점 기준 최신 커밋: `05ce82f` (fix: 썸네일 3단 폴백 복구 + ko_review 잘림 해결 + 기존 글 소급).

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
- [ ] Unsplash 키 등록 (실사진 썸네일 활성화)
- [ ] cron 안정성 관찰
- [ ] cron-job.org 백업 트리거 (선택)
- [ ] 예약발행 쓰려면 `SCHEDULED_PUBLISH_SECRET` 호출측 설정 필요
- 본진(koreansalaryman.com)은 별도 HANDOFF v3.8 참조

## §7 운영 규칙

- 강제승인 모드 — 먼저 묻지 않기
- 시간·컨디션 추정 금지
- 추측하지 말고 **데이터로 확인**
- 실명·회사명 금지
- 비용: 월 1만원 통합 한도
