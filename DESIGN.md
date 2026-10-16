---
name: AI Job Pass Finder
description: 마이스터고 학생·선생님용 취업 진단 Streamlit 앱의 현행 디자인 시스템 (코드에서 추출)
colors:
  bg: "#0A0E17"
  bg-soft: "#0E1320"
  card: "#131826"
  card-border: "#232B3D"
  text: "#E7EAF0"
  muted: "#8A93A6"
  brand-light: "#A8CEF5"
  brand: "#4C8FE0"
  brand-deep: "#2B6BC4"
  status-green: "#34D399"
  status-gold: "#FBBF24"
  status-red: "#F87171"
  accent-purple: "#8B5CF6"
  accent-blue: "#3B82F6"
typography:
  family: '"Pretendard Variable", Pretendard, "Noto Sans KR", -apple-system, system-ui, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
  display: { size: 34px, weight: 800, use: "랜딩 히어로(데스크톱은 clamp(34px, 5.4vw, 52px))" }
  h1: { size: 26px, weight: 800, use: "화면 제목 (.mjp-section-title)" }
  h2: { size: 20px, weight: 800, use: "섹션 제목 (#### / .mjp-verdict / 기능 카드 제목)" }
  body: { size: 16px, line-height: 1.7, use: "본문 · 입력창(iOS 자동 확대 방지)" }
  small: { size: 14px, line-height: 1.65, use: "보조 설명 · 버튼 라벨(데스크톱) · 위젯 라벨" }
  caption: { size: 13px, line-height: 1.6, use: "캡션 · 배지 · 태그" }
rounded:
  base: 14px
  button: 11px
  scorecard: 18px
  feature: 16px
  pill: 999px
spacing:
  s1: 8px
  s2: 16px
  s3: 32px
  s4: 56px
components:
  - mjp-card
  - mjp-feature
  - mjp-scorecard
  - mjp-badge
  - mjp-tag
  - mjp-disclaimer
  - mjp-hero
  - topbar
  - section_title
  - score_bar
  - story_viewer
  - mascot
---

# DESIGN.md — AI Job Pass Finder

> 이 문서는 **현재 코드에 있는 디자인을 그대로 기록한 것**이다 (impeccable `document` 스캔 모드).
> 새로 제안하는 디자인이 아니다. 출처: `.streamlit/config.toml`, `ui/theme.py`, `ui/components.py`,
> `ui/brand.py`, `ui/emblem.py`, `ui/icons.py`, `ui/mascot.py`, `ui/story_viewer.py`, `views/*.py`
> (브랜치 `design`, 2026-10-16 기준).
>
> 표시 규칙: 코드에서 확인한 값은 그대로 적었다. 의도·이름처럼 코드만으로 확정할 수 없는 것은
> **[팀 확인 필요]**, 추정은 **[추측]**으로 표시했다.

## 1. Overview

- **제품**: 마이스터고 학생이 내신·자격증으로 기업별 합격 가능성을 진단하고(스펙 진단), 기업을 훑어보고(기업 탐색·스토리),
  자소서까지 쓰는 Streamlit 앱. 선생님은 '우리 반' 대시보드로 학생 진행을 본다.
- **사용 장면**: 심사·수업 현장에서 **QR로 폰 접속**하는 것이 기본 전제다 (`ui/theme.py` 주석). 그래서 모바일 1단 레이아웃,
  44px 터치 타깃, 16px 입력 폰트가 시스템 수준 규칙으로 들어가 있다.
- **화면 모드** (impeccable 기준): 랜딩 = Persuade, 로그인·역할·허브·스펙·탐색·자소서·마이페이지·우리 반·관리자 = Operate,
  가이드·로드맵 = Read.
- **톤**: 다크 네이비 배경 + 팀 로고에서 뽑은 일렉트릭 블루. 회로(PCB) 패턴과 방사형 글로우가 랜딩에만 깔린다.
  감정 표현은 OGQ 마스코트가, 기능 표시는 단색 라인 아이콘이 맡는다.
- **North Star 문장**: 코드에 명시된 문구가 없다 **[팀 확인 필요]**. 코드 주석에서 읽히는 방향은
  "QR로 들어온 학생이 첫 화면에서 이탈하지 않게 — 낮은 점수에도 화면을 닫지 않게"다 **[추측]**.

### 15개 화면

| 키 | 파일 | 대상 | 모드 |
|---|---|---|---|
| landing | `views/landing.py` | 전체 | Persuade |
| login | `views/login.py` | 전체 | Operate |
| role | `views/role_select.py` | 전체 | Operate |
| hub | `views/hub.py` | 전체 | Operate |
| spec | `views/tab_spec.py` | 학생 | Operate |
| explore (+기업 스토리) | `views/tab_explore.py`, `ui/story_viewer.py` | 학생 | Operate |
| guide | `views/tab_guide.py` | 학생 | Read |
| resume | `views/tab_resume.py` | 학생 | Operate |
| next (로드맵) | `views/tab_next.py` | 전체 | Read |
| mypage | `views/mypage.py` | 전체 | Operate |
| class_setup | `views/class_setup.py` | 선생님 | Operate |
| class_join | `views/class_join.py` | 학생 | Operate |
| class_board (우리 반) | `views/class_board.py` | 선생님 | Operate |
| admin_data | `views/admin_data.py` | 관리자 | Operate |
| admin_stats | `views/admin_stats.py` | 관리자 | Operate |

## 2. Colors

다크 단일 테마. `config.toml`의 `[theme]`와 `ui/theme.py` 상수가 같은 값을 가져야 한다 (주석으로 명시).

| 역할 | 토큰 (theme.py) | 값 | config.toml | 쓰임 |
|---|---|---|---|---|
| 배경 | `BG` | `#0A0E17` | `backgroundColor` | 앱 바탕, 배지 위 글자색 |
| 배경(약) | `BG_SOFT` | `#0E1320` | — | 검색바·필터바, 카드 그라데이션 끝 |
| 카드 | `CARD` | `#131826` | `secondaryBackgroundColor` | `.mjp-card`, 입력창 |
| 경계 | `CARD_BORDER` | `#232B3D` | — | 카드 테두리, 구분선, 막대 트랙, 태그 배경 |
| 본문 | `TEXT` | `#E7EAF0` | `textColor` | 본문·제목 |
| 보조 | `MUTED` | `#8A93A6` | — | 설명, 캡션, CURATED 배지 |
| 브랜드 하이라이트 | `BRAND_LIGHT` | `#A8CEF5` | — | 랜딩 키커 글자 |
| 브랜드 | `BRAND` | `#4C8FE0` | `primaryColor` | primary 버튼, 포커스 링, 호버 테두리, 아이콘 |
| 브랜드 딥 | `BRAND_DEEP` | `#2B6BC4` | — | 엠블럼·로고 블렌딩, 글로우 |
| 상태: 좋음 | `GREEN` | `#34D399` | — | LIVE 배지, 합격 안정권, 점수 막대 채움, 성공 |
| 상태: 주의 | `GOLD` | `#FBBF24` | — | BACKUP 배지, 중간 점수, 별점, 반 코드 |
| 상태: 위험 | `RED` | `#F87171` | — | 낮은 점수(보완 시급) |
| 보조 강조 | `PURPLE` | `#8B5CF6` | — | 면접 질문 카드, '나중에' 카드, 선생님 역할 |
| 보조 강조 | `BLUE` | `#3B82F6` | — | Q-NET 배지, AI 설명 배지 |

**색 역할 규칙 (theme.py 주석에 명시된 것)**

- 브랜드 블루 = 정체성 (로고·내비·히어로·카드 호버).
- 그린 = **상태 시맨틱 전용** (LIVE 배지·합격 안정권·성공). "그린을 장식으로도 쓰면 '초록 = 좋음' 신호가 희석된다."
- 데이터 출처 배지 `BADGE_COLORS`: LIVE = 그린, BACKUP = 골드, CURATED = 무채색(MUTED).
  "큐레이션은 장애가 아니라 설계된 상태"라서 경고색을 쓰지 않는다.
- 소셜 로그인 버튼은 각 제공자 브랜드색 (`PROVIDER_COLORS`: 카카오 `#FEE500`, 네이버 `#03C75A`, 구글 `#FFFFFF`).

**토큰 밖에서 쓰이는 색 (현행 그대로 기록)**

- 기업 스토리 뷰어(iframe) 카드 배경 그라데이션 5종: `#1E3A8A→#4C8FE0`, `#134E4A→#34D399`, `#4C1D95→#A78BFA`,
  `#7C2D12→#FB923C`, `#0A0E17→#2B6BC4` (`ui/story_viewer.py`).
- 랜딩 히어로 제목 그라데이션 끝색 `#9FB0CC`.
- 뷰 파일 안의 하드코딩 hex: `#fff`(배지 글자) 5곳, 그 밖에 `tab_next.py`·`mypage.py`·`class_join.py`에 토큰과 같은 값이 직접 쓰인 곳 6곳.

## 3. Typography

- **글꼴**: Pretendard Variable (jsdelivr CDN) → Noto Sans KR (Google Fonts) → 기기 한글 폰트.
  `html, body, .stApp *` 등에 `!important`로 강제한다. 아이콘 폰트(Material Symbols)·코드(monospace)·KaTeX는 예외로 되돌린다.
- **크기 6단** (`:root`의 `--mjp-*`). 주석: "이 여섯 개 밖의 크기를 새로 만들지 않는다."

| 토큰 | 크기 | 쓰임 |
|---|---|---|
| `--mjp-display` | 34px | 랜딩 히어로 (데스크톱 `clamp(34px, 5.4vw, 52px)`, 380px 이하 26px) |
| `--mjp-h1` | 26px | 화면 제목, `st.markdown("#")`·`##` |
| `--mjp-h2` | 20px | 섹션 제목 `###`·`####`, 판정 문구, 기능 카드 제목 (모바일 화면 제목도 20px로 축소) |
| `--mjp-body` | 16px | 본문, 모든 입력창 |
| `--mjp-small` | 14px | 보조 설명, 위젯 라벨, 데스크톱 버튼 |
| `--mjp-caption` | 13px | 캡션, 배지, 태그 |

- **굵기**: 제목·배지·버튼은 700~800. 본문 400.
- **자간**: 제목 `-0.02em ~ -0.035em`. 로고 계열 마이크로 라벨은 `+0.14em ~ +0.17em` (원본 로고 아크 타이포에서 가져옴).
- **스케일 밖 예외 (현행)**: `.mjp-brand-sub` 11px (로고 일부라 예외로 명시), 우리 반 카드 보조 줄 11px 3곳,
  스토리 뷰어 내부 12~76px (iframe 안이라 토큰을 못 씀).
- **줄 길이**: `.mjp-section-sub` `max-width: 62ch`, 히어로 부제 620px.

## 4. Layout

- **컨테이너**: `.block-container` 최대 1180px, 위 2.2rem / 아래 3rem. Streamlit 사이드바는 쓰지 않는다
  (모바일에서 기본 접힘 → 이탈 지점이라는 이유, `ui/components.py`).
- **여백 4단**: 8 / 16 / 32 / 56px. 섹션 사이와 구분선 위는 56px, 모바일은 한 단 낮춰 32px.
- **화면 골격 (Operate 화면 공통)**: `topbar()` (브랜드 | 사용자칩 + 기능 내비 버튼 줄) → `back_to_hub()` → `section_title()` → 본문.
- **반응형**: 브레이크포인트 768px 하나 (+380px 보정). 768px 아래에서는 모든 `st.columns`를 1단으로 강제한다.
  예외는 컨테이너 key로 지정한다.
  - `st-key-mjp_brandrow`: 상단 브랜드|사용자 줄은 가로 유지.
  - `st-key-mjp_navbar`: 기능 내비는 가로 스크롤.
  - `st-key-mjp_row*`: 카드 하단 짧은 버튼 줄은 가로 유지. 스토리 내비 줄만 두 줄 줄바꿈을 허용한다.
- **카드 그리드**: `grid_columns(total, per_row)`로 행마다 `st.columns`를 새로 만든다. 1단으로 접혀도 순서가 보존된다.
- **점수 우선 배치**: 스펙 진단은 `st.container()`로 위쪽 자리를 먼저 잡고, 계산이 끝난 뒤 점수를 채운다 (점수가 항상 첫 화면에 온다).

## 5. Elevation & Depth

- 그림자 2단만 쓴다. `--mjp-shadow-1: 0 1px 2px rgba(0,0,0,.26)`, `--mjp-shadow-2: 0 1px 2px rgba(0,0,0,.28), 0 10px 28px rgba(0,0,0,.20)`.
  주석: "진하면 다크 배경에서 카드가 뜬 것처럼 보인다."
- 깊이는 그림자보다 **면의 명도 차**로 만든다: BG(`#0A0E17`) < BG_SOFT < CARD(`#131826`) < CARD_BORDER(`#232B3D`).
- 호버: 카드·버튼이 `translateY(-1~-3px)`로 뜨고 `shadow-2`와 브랜드색 테두리가 붙는다. 누르면 원위치.
  전환은 `150ms cubic-bezier(0.4,0,0.2,1)`.
- 랜딩 히어로만 장식적 깊이를 쓴다: 방사형 블루 글로우(`::before`, blur 6px)와 회로 패턴(`::after`, 불투명도 0.05, 방사형 마스크).
- 로고에는 `drop-shadow(0 0 22px rgba(76,143,224,.28))` 발광이 있다.

## 6. Shapes

- 기본 반경 14px (`--mjp-radius`). 버튼·입력 11px, 기능 카드 16px, 점수 배너 18px, 스토리 카드 18px, 배지 999px(알약), 태그 7px.
- 점수 링: 112px 원, 상태색으로 채우고 숫자는 BG색.
- 강조 띠: `border-left` 3~4px 상태색 (우리 반 '먼저 챙겨볼 학생', '나중에' 카드).
- 안내 박스(`.mjp-disclaimer`): 그린 점선 테두리 + 그린 8% 배경, 반경 10px.
- 아이콘: 24×24 라인 아이콘, stroke 1.6~2, round cap/join, fill 없음 (`ui/icons.py`, 직접 작도).

## 7. Components

| 컴포넌트 | 위치 | 설명 |
|---|---|---|
| `render_html(markup)` | `ui/components.py` | HTML 조각을 한 줄로 펴서 CommonMark 빈 줄·들여쓰기 사고를 막는 렌더 헬퍼. 스타일 HTML은 이걸로 넣는다. |
| `topbar(active)` | `ui/components.py` | 엠블럼 + 서비스명 + 팀명 마이크로 라벨 / 사용자칩 / 기능 내비 버튼(역할에 따라 6~7개, 활성 = primary). |
| `back_to_hub()` | `ui/components.py` | "← 메인 허브로" 보조 버튼. |
| `section_title(title, sub, icon_name)` | `ui/components.py` | 화면 제목 26px + 브랜드색 라인 아이콘 + 보조 설명. |
| `disclaimer(text)` | `ui/components.py` | 그린 점선 안내 박스. **"예시 데이터" 안내 전용** — 줄이거나 흐리게 만들지 않는다. |
| `pill(text, color)` | `ui/components.py` | 상태색 알약 배지. |
| `.mjp-card` | `ui/theme.py` | 기본 카드: CARD 면 + 1px 경계 + 14px 반경 + 22/24px 안여백. 모바일 15~18px. |
| `.mjp-feature` | `ui/theme.py` | 허브·랜딩 기능 카드: 그라데이션 면, 아이콘 + 20px 제목 + 14px 설명. |
| `.mjp-scorecard` / `.mjp-scorering` / `.mjp-verdict` | `ui/theme.py` | 스펙 점수 배너: 상태색 배지 + 112px 점수 링 + 판정 문구. |
| `score_bar(label, value, max)` | `ui/theme.py` | 세부 점수 막대 (트랙 CARD_BORDER, 채움 GREEN 고정). |
| `render_stars(rating)` | `ui/theme.py` | SVG 별점 (이모지 별 금지). |
| 데이터 출처 배지 | `services/fallback.badge_html` + `BADGE_COLORS` | **LIVE API / BACKUP DATA / CURATED** — 줄이거나 흐리게 만들지 않는다. |
| `.mjp-badge` / `.mjp-tag` | `ui/theme.py` | 13px 굵은 알약 배지 / 무채색 태그. |
| 검색바·필터바 | `st.container(key="mjp_searchbar"/"mjp_filterbar")` | BG_SOFT 면으로 '조건을 거는 곳'을 묶는다. |
| 기업 스토리 뷰어 | `ui/story_viewer.py` | `components.html` iframe, 9:16 카드, 진행 바, 탭/길게 누르기, 5초 자동 넘김. 하단 Streamlit 버튼 줄(이전·관심·패스)이 상태를 바꾼다. |
| 로고·엠블럼 | `ui/brand.py`, `ui/emblem.py` | 로고 이미지 블렌딩 또는 벡터 엠블럼 (full / compact). |
| 마스코트 | `ui/mascot.py` | OGQ 마스코트, 감정 슬롯(welcome·cheer·comfort·celebrate·thinking 등), `clamp()` 크기. **출처 확인 전이라 노출 위치를 늘리거나 변형하지 않는다.** |
| 라인 아이콘 | `ui/icons.py` | 이모지 대체용 SVG. 마스코트 = 컬러·화면당 1곳, 아이콘 = 단색·보조. |

**Streamlit 위젯 다듬기 (theme.py §5·§6)**: 버튼 최소 44px(모바일 48px), 입력 16px·44px, 포커스 링 = 브랜드 2px 외곽선 /
3px 글로우, 위젯 라벨 14px 700, 숫자 스테퍼·업로더·셀렉트 화살표 44px 보정, 툴팁 아이콘 탭 영역 30px.

## 8. Do's and Don'ts

**Do**

- 색·크기·여백은 `ui/theme.py` 토큰(`BG`…`BRAND`, `--mjp-*`)을 쓴다. `config.toml` `[theme]`와 값을 맞춘다.
- 그린은 상태(좋음·LIVE·성공)에만 쓴다.
- 스타일 HTML은 `render_html()`로 넣는다.
- 다단 레이아웃의 모바일 예외는 컨테이너 key(`mjp_navbar`, `mjp_row_*`, `mjp_brandrow`)로 만든다.
- 카드 목록은 `grid_columns()`로 행 단위 컬럼을 만든다.
- 변경 후 `docs/qa_mobile.py`로 390px·1440px을 실측한다 (가로 넘침 0, 버튼 44px+, 입력 16px+, 11px 미만 글자 0).
- 예시 데이터 안내(`disclaimer`)와 LIVE / BACKUP / CURATED 배지는 지금 이상으로 잘 보이게 둔다.

**Don't**

- 6단 밖의 글자 크기, 토큰 밖의 hex를 새로 만들지 않는다.
- 이모지를 아이콘 대용으로 쓰지 않는다 (`ui/icons.py` 원칙). Streamlit 버튼·탭 라벨은 텍스트만 쓴다.
- 사이드바로 내비게이션을 옮기지 않는다.
- 마스코트(`assets/ogq`)를 새 위치에 노출하거나 변형하지 않는다 (출처 확인 전).
- React·Tailwind 등 별도 프론트엔드로 바꾸지 않는다. `core/`·`services/`·`data/`는 디자인 작업 범위가 아니다.
- `requirements.txt`의 `streamlit>=1.41,<1.64` 범위를 바꾸지 않는다.
