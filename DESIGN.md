---
name: AI Job Pass Finder
version: 2
description: 팀 포트폴리오 사이트와 같은 디자인 언어 + 토스 앱식 원칙. 흰 바탕 · 연회색 면 · 블루 한 가지 · 큰 굵은 제목.
colors:
  bg: "#FFFFFF"
  bg-soft: "#F9FAFB"
  surface: "#F2F4F6"
  line: "#E5E8EB"
  title: "#191F28"
  body: "#4E5968"
  sub: "#626B78"
  brand: "#3182F6"
  brand-deep: "#1B64DA"
  brand-press: "#1550B8"
  brand-soft: "#E8F3FF"
  green: "#08734C"
  gold: "#A44A06"
  red: "#C42B1C"
  green-soft: "#E7F6EF"
  gold-soft: "#FEF3E2"
  red-soft: "#FDECEC"
  green-vivid: "#0B9B63"
  gold-vivid: "#D9650B"
  red-vivid: "#E5484D"
  purple: "#6D28D9"
typography:
  family: '"Pretendard Variable", Pretendard, "Noto Sans KR", -apple-system, system-ui, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
  display: { size: "clamp(34px, 5.6vw, 60px)", weight: 700, line-height: 1.25, use: "랜딩 첫 화면 헤드라인" }
  number: { size: "clamp(56px, 9vw, 88px)", weight: 800, use: "화면의 핵심 숫자 (점수)" }
  h1: { size: "clamp(26px, 3.6vw, 40px)", weight: 700, line-height: 1.3, use: "화면·섹션 헤드라인 (두 줄)" }
  h2: { size: 22px, weight: 700, use: "블록 제목 (####)" }
  h3: { size: 19px, weight: 700, use: "카드 제목 · STEP 제목" }
  eyebrow: { size: 17px, weight: 600, color: brand-deep, use: "헤드라인 위 작은 라벨" }
  lead: { size: "clamp(17px, 1.6vw, 19px)", line-height: 1.7, use: "헤드라인 아래 설명" }
  body: { size: 16px, line-height: 1.7 }
  small: { size: 14px }
  caption: { size: 13px }
rounded:
  card: 24px
  input-group: 20px
  button: 16px
  input: 14px
  tag: 8px
  pill: 999px
spacing:
  s1: 8px
  s2: 16px
  s3: 32px
  s4: "64px (폰 48px)"
  s5: "112px (폰 72px) — 섹션 띠 위아래"
components:
  - eyebrow-headline
  - stat
  - tag-chip-card
  - step-timeline
  - band
  - score-hero
  - score-breakdown
  - button
  - input
  - bottom-cta
  - disclaimer
  - data-source-badge
---

# DESIGN.md — AI Job Pass Finder (v2)

> v2 디자인 시스템. 브랜치 `design-v2` 에서 만들었다 (2026-10-16).
> 출처는 두 가지다.
> 1. **팀 포트폴리오 사이트** (woobin0724.github.io) 의 `index.html` CSS — 색 · 글꼴 · 크기 · 간격 · 모서리 · 섹션 패턴을 추출했다.
>    포트폴리오 파일은 이 저장소에 복사하지 않았다. 값만 옮겼다.
> 2. **토스 앱식 원칙** — 흰 바탕과 연회색 면, 테두리 대신 여백·면 색, 큰 굵은 제목과 큰 숫자, 한 화면에 핵심 하나,
>    둥근 카드, 폰에서 하단 꽉 찬 주요 버튼. 토스의 로고·아이콘·전용 글꼴(Toss Product Sans)은 쓰지 않는다. 글꼴은 Pretendard.
>
> 구현: `.streamlit/config.toml` (Streamlit 테마) + `ui/theme.py` (토큰 · 전역 CSS) + `ui/components.py` (공통 부품).
> 적용 범위: 15개 화면 전부. 랜딩·스펙 진단에서 시범 적용한 뒤 나머지 13개 화면에 같은 언어로 넓혔다.

## 1. Overview

- **한 문장**: 흰 종이 위에 회색 면과 파란 숫자 하나 — 학생이 "내 점수"를 한눈에 읽고 다음 할 일을 아는 화면.
- **사용 장면**: 수업·심사 현장에서 QR 로 폰 접속이 기본. 밝은 교실·복도에서 보므로 흰 바탕을 택했다.
- **화면 모드**: 랜딩 = Persuade(설득), 스펙 진단 등 기능 화면 = Operate(작업), 가이드·로드맵 = Read(읽기).
- **세 가지 원칙**
  1. **선 대신 면** — 카드·입력칸·보조 버튼은 테두리 없이 `surface(#F2F4F6)` 면으로 구분한다. 선(`line`)은 목록 안 구분과 막대 트랙에만.
  2. **화면마다 제일 큰 것은 하나** — 랜딩은 헤드라인, 스펙 진단은 점수 숫자.
  3. **블루는 한 가지** — `brand` 계열만 강조에 쓴다. 상태(좋음·주의·위험)는 그린·골드·레드로 따로 둔다.

## 2. Colors

포트폴리오 변수 → 앱 토큰 대응. 이름(`BG`, `CARD`, `TEXT` …)은 v1 과 같게 두고 값만 바꿨다 — 다른 화면이 import 하는 이름이라서.

| 역할 | 토큰 (ui/theme.py) | 값 | 포트폴리오 | 비고 |
|---|---|---|---|---|
| 바탕 | `BG` | `#FFFFFF` | `--bg` | |
| 연한 바탕 (섹션 띠) | `BG_SOFT` | `#F9FAFB` | `--bg-alt` | 띠 위 카드는 흰색 |
| 면 (카드·입력·보조 버튼) | `CARD` | `#F2F4F6` | `--card` | |
| 선 | `CARD_BORDER` | `#E5E8EB` | `--line` | 카드 테두리로는 안 쓴다 |
| 제목·숫자 | `TEXT` | `#191F28` | `--title` | |
| 본문 | `BODY` | `#4E5968` | `--body` | |
| 보조 글자 | `MUTED` | `#626B78` | `--sub #8B95A1` | **조정**: 원래 값은 흰 바탕 3.04:1 이라 AA 미달 → 5.39:1 |
| 브랜드 | `BRAND` | `#3182F6` | `--blue` | 큰 숫자·막대·아이콘 전용 (흰 바탕 3.71:1, 큰 글자 기준만 통과) |
| 브랜드 진하게 | `BRAND_DEEP` | `#1B64DA` | `--blue-dark` | 주요 버튼 면(흰 글자 5.41:1)·작은 파란 글자 |
| 브랜드 누름 | `BRAND_PRESS` | `#1550B8` | — | 주요 버튼 호버 |
| 브랜드 연하게 | `BRAND_LIGHT` | `#E8F3FF` | `--blue-soft` | 선택된 내비·태그·예시 데이터 안내 면 |
| 상태: 좋음 | `GREEN` / `GREEN_SOFT` | `#08734C` / `#E7F6EF` | — | LIVE 배지, 합격 안정권 |
| 상태: 주의 | `GOLD` / `GOLD_SOFT` | `#A44A06` / `#FEF3E2` | — | BACKUP 배지, 분발 필요 |
| 상태: 위험 | `RED` / `RED_SOFT` | `#C42B1C` / `#FDECEC` | — | 보완 시급 |
| 큰 숫자·막대용 상태색 | `STATUS_VIVID` | `#0B9B63` · `#D9650B` · `#E5484D` | — | 큰 글자·비글자 기준 3:1 이상(회색 면에서도 3.24+). 작은 글자에 쓰지 않는다 |

**규칙**
- 상태색 글자는 진한 값, 큰 숫자와 막대는 `STATUS_VIVID`, 칩 배경은 `_SOFT`.
- 데이터 출처 배지(`BADGE_COLORS`): LIVE = 그린 면, BACKUP = 골드 면, CURATED = 보조 회색 면, 글자는 모두 흰색(4.6:1 이상). **크기·위치는 v1 그대로 — 덜 보이게 하지 않는다.**
- `config.toml` 의 `primaryColor` 는 `#3182F6`(슬라이더·라디오·탭 밑줄·포커스). 주요 버튼 면만 CSS 로 `BRAND_DEEP` 으로 덮는다.

## 3. Typography

- **글꼴**: Pretendard Variable (jsdelivr) → Noto Sans KR (Google Fonts) → 기기 한글 폰트. 포트폴리오와 같은 Pretendard.
- **줄바꿈**: `word-break: keep-all` (어절 단위) + 칸보다 긴 어절만 `overflow-wrap: anywhere`.
- **자간**: 제목 `-0.03em`, 랜딩 헤드라인 `-0.035em`, 점수 숫자 `-0.045em`.
- **숫자**: 점수·통계는 `font-variant-numeric: tabular-nums`.

| 역할 | 크기 | 굵기 | 쓰는 곳 |
|---|---|---|---|
| display | clamp(34–60px) | 700 | 랜딩 첫 화면 헤드라인 (두 줄, 둘째 줄 블루) |
| number | clamp(56–88px) | 800 | 스펙 진단 점수 |
| h1 | clamp(26–40px) | 700 | 화면 제목, 섹션 두 줄 헤드라인 |
| h2 | 22px | 700 | 블록 제목 (`####`) |
| h3 | 19px | 700 | 카드 제목, STEP 제목 |
| eyebrow | 17px | 600 | 헤드라인 위 작은 파란 라벨 (`BRAND_DEEP`) |
| lead | clamp(17–19px) | 400 | 헤드라인 아래 설명 |
| body | 16px | 400 | 본문, 모든 입력칸(iOS 확대 방지) |
| small | 14px | — | 보조 설명, 예시 데이터 안내 |
| caption | 13px | — | `st.caption`, 배지 |

## 4. Layout

- **컨테이너**: 최대 1080px, 위 28px · 아래 96px (폰: 좌우 16px).
- **여백 5단**: 8 / 16 / 32 / 64 / 112px (폰에서 64→48, 112→72). 묶음 안은 촘촘하게, 섹션 사이는 크게.
- **섹션 띠 (`.mjp-band`, `.mjp-band-alt`)**: 랜딩처럼 흐르는 화면은 흰 띠와 `BG_SOFT` 띠를 번갈아 깐다.
  띠 배경은 `box-shadow: 0 0 0 100vmax` + `clip-path` 로 화면 끝까지 칠한다 (레이아웃 폭은 늘지 않아 가로 스크롤이 없다).
- **그리드**: `.mjp-grid` + `.mjp-g2/.mjp-g3/.mjp-g4`, 간격 16px. 폰에서 g2·g3 는 1열, g4 는 2열.
- **Streamlit 다단(`st.columns`)**: 768px 아래에서 1단으로 접힌다. 예외는 컨테이너 key — `mjp_brandrow`(상단 줄), `mjp_navbar`(가로 스크롤 내비), `mjp_row_*`(짧은 버튼 줄).
- **하단 고정 주요 버튼**: 컨테이너 key 가 `mjp_cta_` 로 시작하면 폰에서 화면 하단에 꽉 차게 고정된다(높이 56px, safe-area 여백 포함). 그 화면만 본문 아래 여백이 120px 로 늘어난다.
- **기능 화면 골격**: 상단 바(브랜드 | 사용자) → 글자 탭 내비 → ← 메인 허브로(글자 버튼) → 화면 제목 → 핵심(점수 등) → 입력·세부.

## 5. Elevation & Depth

- 그림자는 기본적으로 쓰지 않는다 (`--mjp-shadow-1: none`). 깊이는 **면의 명도 차**로 만든다: `BG` > `BG_SOFT` > `CARD` > `CARD_BORDER`.
- 띠(`BG_SOFT`) 위의 카드는 흰색으로 뒤집어 한 단 띄운다.
- 예외: 스토리 뷰어(iframe) 카드의 그림자는 v1 그대로.
- 움직임: 버튼 누름 `scale(0.98)`, 전환 200ms `cubic-bezier(.22,.61,.36,1)` (포트폴리오와 같은 곡선). `prefers-reduced-motion` 이면 전환을 끈다.

## 6. Shapes

- 카드 24px · 입력 묶음 20px · 버튼 16px · 입력칸 14px · 칩/배지 8px · 알약 999px.
- 테두리 없음이 기본. 포커스는 2px 블루 링(`box-shadow`/`outline`).
- 아이콘: 24×24 라인 아이콘(`ui/icons.py`) 그대로.
- 엠블럼·레거시 마스코트는 어두운 바탕용 원본이라 둥근 어두운 타일 위에 얹는다 (엠블럼 `#191F28`, 마스코트는 원래 배경색 `#25292A`). 이미지 자체는 바꾸지 않는다.

## 7. Components

| 컴포넌트 | 클래스 / 함수 | 설명 |
|---|---|---|
| 라벨 + 두 줄 헤드라인 | `.mjp-eyebrow` + `.mjp-headline` + `.mjp-lead` | 포트폴리오 섹션 머리. 라벨 17px 파란 글자, 헤드라인 h1, 설명 lead |
| 큰 숫자 통계 | `.mjp-stat` (`-label` / `-value` / `-note`) | 회색 면, 가운데 정렬, 값은 블루 36–48px |
| 태그 칩 카드 | `.mjp-tcard` + `.mjp-chiptag` | 회색 면 24px, 위에 연한 블루 칩, 제목 19px, 본문 16px |
| STEP 타임라인 | `ol.mjp-steps` + `.mjp-step-no` | 왼쪽 세로선 + 블루 테두리 점, "STEP n" 파란 라벨 |
| 입력 단계 머리 | `.mjp-stephead` (`views/tab_spec._step`) | "STEP 1 학과와 내신" |
| 알약 칩 | `.mjp-chips` / `.mjp-chip` | 소속·수상 같은 짧은 사실 |
| 점수 히어로 | `.mjp-score` (`views/tab_spec._score_hero`) | 라벨 · 큰 숫자(상태 VIVID) · "/ 100점" · 판정 칩(SOFT 면 + 진한 글자) · 한 줄 설명 · 100점 눈금 막대(50·80 눈금 = 판정 구간 경계) |
| 세부 점수 목록 | `.mjp-break` + `score_bar()` | 회색 면 한 장 안에 4줄, 줄 사이 선, 얇은 막대(비율 색) |
| 설명 카드 | `.mjp-explain` | 회색 면, 배지 · 본문 · 흰 상자 "다음 한 걸음" |
| 버튼 | Streamlit 버튼 전역 CSS | 보조 = 회색 면/제목색 글자, 주요 = `BRAND_DEEP` 면/흰 글자, 48px(폰 48px+, 하단 CTA 56px), 반경 16 |
| 내비 | `st-key-mjp_navbar` | 글자 탭. 선택된 탭만 `BRAND_LIGHT` 면 + `BRAND_DEEP` 글자 |
| 입력칸 | Streamlit 입력 전역 CSS | 회색 면, 테두리 없음, 반경 14, 포커스 블루 링, 글자 16px, 선택 칩은 연한 블루 |
| 예시 데이터 안내 | `disclaimer()` / `.mjp-disclaimer` | 연한 블루 면 + 본문색 14px. **v1(13px 회색 글자 + 점선) 보다 덜 눈에 띄면 안 된다** |
| 안내 줄 | `note()` / `.mjp-note` | 본문 16px. 예시·백업 안내가 캡션으로 작아지지 않게 |
| 데이터 출처 배지 | `services/fallback.badge_html` + `BADGE_COLORS` | LIVE / BACKUP / CURATED — 위 2장 규칙 |
| 화면 머리 | `section_title(title, sub, eyebrow=)` | 작은 파란 라벨(선택) + h1 제목 + 설명. v2 에서 제목 옆 아이콘은 그리지 않는다 |
| 상태 칩 | `status_chip(text, color)` / `.mjp-schip` | 상태색 SOFT 면 + 진한 글자. 상태색이 아니면 흰 칩 + 보조 글자. 왼쪽 색띠 대신 쓴다 |
| 숫자 타일 | `stat_tiles([(라벨, 값, 보조, 색)])` / `.mjp-tiles` | 회색 면 타일 묶음, 값은 28–36px 굵게(상태색이면 VIVID). 폰 2열 |
| 목록 행 | `list_row(icon, title, desc, right)` / `.mjp-row` | 연한 블루 아이콘 타일 + 제목·설명 + 오른쪽 보조. 허브 보조 진입구·열람 이력·반 정보 |
| 코드 표시 | `code_display(label, code, desc)` / `.mjp-codebox` | 반 코드·이어하기 코드. 크게, 자간 0.18em |
| 또는 구분선 | `or_divider()` / `.mjp-or` | 두 선택지 사이 |
| 체크 목록 | `ul.mjp-checklist` | 블루 체크 + 본문. 역할 카드·반 만들기 안내 |
| 마스코트 말풍선 | `mascot.speech()` / `.mjp-speech` | 회색 면(성공·주의 톤은 연한 상태색 면), 테두리 없음 |
| 좁은 칼럼 | 컨테이너 key `mjp_narrow_*` | 로그인·반 등록처럼 입력 하나가 주인공인 화면은 최대 440px 가운데 |
| st.metric · 탭 · 체크박스 | 전역 CSS | metric 은 숫자 타일처럼, 탭·체크박스 글자는 본문 크기 |
| 기존 카드 | `.mjp-card`, `.mjp-feature` | v1 클래스 유지, 회색 면·테두리 없음으로 바뀜 |

**Streamlit 기본 크롬 처리**: 상단 헤더 바·툴바·장식 띠·푸터 숨김, 제목 앵커 아이콘 숨김, 선택 영역·캐럿·스크롤바 색을 팔레트로.
멀티셀렉트 칩은 1.41 계열(baseweb `tag`)과 1.63(react-aria `[data-tag]`) 둘 다 잡는다.

## 8. Do's and Don'ts

**Do**
- 색·크기·여백은 `ui/theme.py` 토큰으로. `config.toml` `[theme]` 값과 맞춘다.
- 구분은 면 색과 여백으로. 카드 안에 카드를 넣지 않는다.
- 화면마다 제일 큰 요소를 하나만 둔다.
- 폰에서 그 화면의 주요 행동이 하나라면 `st.container(key="mjp_cta_...")` 로 하단 고정한다.
  현재: 랜딩(시작하기) · 로그인(게스트모드로 바로 시작하기) · 반 등록(우리 반에 등록하기 / 기능 선택하러 가기) ·
  반 만들기(우리 반 만들고 코드 받기 / 우리 반 현황 보기). 한 화면에 고정 버튼은 하나만.
- 상태색은 글자 = 진한 값, 큰 숫자·막대 = VIVID, 칩 면 = SOFT.
- 예시 데이터 안내와 LIVE / BACKUP / CURATED 배지는 지금 이상으로 보이게 둔다.
- 변경 후 `docs/qa_mobile.py` 로 390px·1440px 실측 (가로 넘침 0, 버튼 44px+, 입력 16px+, 11px 미만 글자 0).

**Don't**
- 카드에 테두리·두꺼운 왼쪽 색띠(1px 초과)를 두르지 않는다. 그림자로 띄우지 않는다. 심각도는 `status_chip` 으로.
- 역할·기능마다 다른 색을 칠하지 않는다 (예: 학생 = 초록, 선생님 = 보라). 블루 한 가지 + 상태색만.
- 그라데이션 글자, 유리(blur) 장식, 이모지 아이콘을 쓰지 않는다.
- `BRAND(#3182F6)` 를 작은 글자색이나 흰 글자 버튼 면으로 쓰지 않는다 (대비 부족) — `BRAND_DEEP` 을 쓴다.
- `MUTED` 대신 포트폴리오의 `#8B95A1` 을 글자에 쓰지 않는다.
- 토스 로고·아이콘·Toss Product Sans 를 쓰지 않는다.
- 마스코트(`assets/ogq`)를 새 위치에 노출하거나 이미지를 변형하지 않는다.
- React·Tailwind 등 별도 프론트엔드로 바꾸지 않는다. `core/`·`services/`·`data/` 는 디자인 작업 범위가 아니다.
- `requirements.txt` 의 `streamlit>=1.41,<1.64` 범위를 바꾸지 않는다.

**알려진 긴장 (의도적으로 남긴 것)**
- impeccable 의 craft-floor 는 "헤드라인 위 작은 라벨(eyebrow)"과 "큰 숫자 + 작은 라벨 통계"를 기본값 함정으로 본다.
  이 프로젝트에서는 포트폴리오와 같은 언어로 맞추라는 요청에 따라 두 패턴을 의도적으로 채택했다.
