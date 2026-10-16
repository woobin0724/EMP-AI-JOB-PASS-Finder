# -*- coding: utf-8 -*-
"""
ui/theme.py
[v2] 디자인 토큰 + 전역 CSS + 모바일 반응형 단일 관문

설계 의도
---------
화면 파일(views/*.py)은 색을 직접 알 필요가 없고 여기서 import 하기만 한다.
v2 는 팀 포트폴리오 사이트의 디자인 언어(흰 바탕 · 연회색 면 · 블루 한 가지 ·
큰 굵은 제목)를 그대로 가져오고, 토스 앱식 원칙을 더했다.

  · 테두리 대신 여백과 면 색으로 구분한다 (카드 = 연회색 면, 선 없음)
  · 한 화면에 핵심 하나 — 제일 큰 글자는 화면마다 하나뿐이다
  · 둥근 카드(24px), 큰 버튼(56px), 폰에서는 주요 버튼이 화면 하단에 꽉 차게 붙는다

▣ 토큰 이름을 유지한 이유
   BG · CARD · TEXT · MUTED · GREEN … 같은 이름을 다른 화면 15개가 import 한다.
   이름은 그대로 두고 값만 바꿔, 구조를 아직 바꾸지 않은 화면도 새 색을 따라오게 했다.

▣ 모바일 대응이 왜 CSS 한 곳에 모여야 하는가
   심사 현장에서 학생/심사위원은 QR을 찍어 '폰'으로 접속한다. Streamlit의
   st.columns()는 좁은 화면에서 자동으로 1단이 되지 않고 가로로 짓눌리기만
   한다. 그래서 아래 @media 블록에서 Streamlit이 컬럼에 붙이는 data-testid를
   직접 잡아 1단으로 강제 전환한다.
"""

import streamlit as st

# ============================================================
# 디자인 토큰 (config.toml 의 [theme] 값과 일치시킬 것)
# ============================================================
# 바탕과 면 — 포트폴리오의 --bg / --bg-alt / --card / --line
BG = "#FFFFFF"            # 기본 바탕
BG_SOFT = "#F9FAFB"       # 섹션을 번갈아 깔 때의 연한 바탕
CARD = "#F2F4F6"          # 카드·입력칸·보조 버튼의 면
CARD_BORDER = "#E5E8EB"   # 구분선·막대 트랙 (카드 테두리로는 쓰지 않는다)

# 글자 — 포트폴리오의 --title / --body. 보조 글자(--sub #8B95A1)는 흰 바탕
# 대비가 3.04:1 이라 본문 크기 글자에 쓰면 AA(4.5:1) 미달이다. 한 단 진하게 쓴다.
TEXT = "#191F28"          # 제목·숫자
BODY = "#4E5968"          # 본문
MUTED = "#626B78"         # 보조 글자 (흰 바탕 5.39 · 회색 면 4.89)

# 블루 한 가지 — 포트폴리오의 --blue / --blue-dark / --blue-soft
BRAND = "#3182F6"         # 큰 숫자·막대·아이콘 (큰 글자·비글자 전용, 흰 바탕 3.71)
BRAND_DEEP = "#1B64DA"    # 주요 버튼 면·작은 파란 글자 (흰 글자 5.41)
BRAND_PRESS = "#1550B8"   # 주요 버튼 누름/호버
BRAND_LIGHT = "#E8F3FF"   # 연한 블루 면 (선택된 내비 · 안내 박스 · 태그)
BLUE = BRAND_DEEP         # 흰 글자를 얹는 파란 배지

# 상태색 — 흰 바탕에서 글자로 읽히도록 진하게. 연한 면(_SOFT)은 칩 배경.
#   그린 = 좋음 · LIVE / 골드 = 주의 · BACKUP / 레드 = 위험
GREEN = "#08734C"
GOLD = "#A44A06"
RED = "#C42B1C"
GREEN_SOFT = "#E7F6EF"
GOLD_SOFT = "#FEF3E2"
RED_SOFT = "#FDECEC"
PURPLE = "#6D28D9"

STATUS_SOFT = {GREEN: GREEN_SOFT, GOLD: GOLD_SOFT, RED: RED_SOFT}
# 큰 숫자·막대용 밝은 상태색 — 큰 글자·비글자 기준(3:1)을 흰 바탕과 회색 면 모두에서
# 넘긴다(3.24 이상). 작은 글자에는 쓰지 않는다 (작은 글자는 위의 진한 값).
STATUS_VIVID = {GREEN: "#0B9B63", GOLD: "#D9650B", RED: "#E5484D"}

# 데이터 출처 배지 (services/fallback.badge_html). 흰 글자를 얹는다.
# 큐레이션은 장애가 아니라 설계된 상태 — 경고색(골드)이 아니라 무채색.
BADGE_COLORS = {"live": GREEN, "backup": GOLD, "curated": MUTED,
                "ink": "#FFFFFF", "muted": MUTED}

# 브랜드 제공자별 색 (로그인 버튼)
PROVIDER_COLORS = {
    "kakao": "#FEE500",
    "naver": "#03C75A",
    "google": "#FFFFFF",
    "guest": CARD,
}

# 모바일 기준 폭 — 이 값 아래에서 모든 다단 레이아웃이 1단으로 접힌다.
MOBILE_BREAKPOINT = 768


def inject_css() -> None:
    """전역 스타일을 주입한다. app.py 부팅 시 단 한 번만 호출한다."""
    st.markdown(f"""
<style>
/* 주 폰트 Pretendard (jsdelivr) + 폴백 웹폰트 Noto Sans KR (Google Fonts).
   학교·기관망이 jsdelivr 을 막을 때 폴백까지 웹폰트여야 화면이 덜 달라진다. */
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css");
@import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap");

:root {{
    --mjp-font: "Pretendard Variable", Pretendard, "Noto Sans KR", -apple-system,
                BlinkMacSystemFont, system-ui, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;

    /* 타이포 — 포트폴리오 스케일을 앱 화면에 맞게 한 단 줄였다 */
    --mjp-display: clamp(34px, 5.6vw, 60px);  /* 랜딩 첫 화면 헤드라인 */
    --mjp-num: clamp(56px, 9vw, 88px);        /* 화면의 핵심 숫자 (점수) */
    --mjp-h1: clamp(26px, 3.6vw, 40px);       /* 화면·섹션 헤드라인 (두 줄) */
    --mjp-h2: 22px;                           /* 블록 제목 */
    --mjp-h3: 19px;                           /* 카드 제목 */
    --mjp-lead: clamp(17px, 1.6vw, 19px);     /* 헤드라인 아래 설명 */
    --mjp-body: 16px;
    --mjp-small: 14px;
    --mjp-caption: 13px;

    /* 여백 — 묶음은 촘촘하게, 섹션 사이는 크게 */
    --mjp-s1: 8px;
    --mjp-s2: 16px;
    --mjp-s3: 32px;
    --mjp-s4: 64px;
    --mjp-s5: 112px;

    /* 면으로 구분하므로 그림자는 거의 쓰지 않는다 */
    --mjp-shadow-1: none;
    --mjp-shadow-2: 0 8px 24px rgba(25,31,40,0.08);

    --mjp-ease: 200ms cubic-bezier(.22,.61,.36,1);
    --mjp-radius: 20px;        /* 입력 묶음 · 작은 면 */
    --mjp-radius-card: 24px;   /* 카드 */
    --mjp-radius-btn: 16px;    /* 버튼 */
}}

/* ===== 0. 바탕 · 글꼴 · 브라우저 기본값 ===== */
html, body, .stApp, .stApp *,
input, textarea, select, button, [class^="st-"], [class*=" st-"] {{
    font-family: var(--mjp-font) !important;
}}
/* 아이콘 폰트·코드·수식은 본문 폰트로 덮이면 깨진다 → 되돌린다 */
[data-testid="stIconMaterial"],
.material-icons, .material-icons-outlined,
.material-symbols-rounded, .material-symbols-outlined {{
    font-family: "Material Symbols Rounded", "Material Icons" !important;
}}
code, pre, kbd, samp, .stCode, [data-testid="stCode"] * {{
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace !important;
}}
.katex, .katex * {{ font-family: KaTeX_Main, "Times New Roman", serif !important; }}

/* 한국어는 어절 단위로 줄바꿈. Streamlit 이 <p> 에 break-word 를 직접 걸어
   상속만으로는 안 덮이므로 하위 전체에 건다. 어절이 칸보다 길 때만 강제로 끊는다. */
.stApp, .stApp * {{ word-break: keep-all !important; overflow-wrap: anywhere !important; }}

.stApp {{
    background: {BG}; color: {BODY}; font-size: var(--mjp-body);
    -webkit-font-smoothing: antialiased; caret-color: {BRAND};
}}
::selection {{ background: {BRAND_LIGHT}; color: {TEXT}; }}
* {{ scrollbar-width: thin; scrollbar-color: {CARD_BORDER} transparent; }}
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-thumb {{ background: {CARD_BORDER}; border-radius: 8px; }}
h1, h2, h3, h4, h5, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {{
    color: {TEXT} !important; letter-spacing: -0.03em;
}}

/* Streamlit 기본 크롬 숨김 — 상단 헤더 바·툴바·장식 띠·푸터 */
header[data-testid="stHeader"], div[data-testid="stToolbar"],
div[data-testid="stDecoration"], #MainMenu, footer {{ display: none !important; }}

.block-container {{ padding-top: 28px; padding-bottom: 96px; max-width: 1080px; }}
/* Streamlit 위젯 사이 기본 간격(1rem)을 조금 줄인다 — 여백은 섹션이 만든다 */
div[data-testid="stVerticalBlock"] {{ gap: 0.75rem; }}

/* ===== 1. 글자 스케일 ===== */
.stMarkdown h1, .stMarkdown h2 {{ font-size: var(--mjp-h1) !important; font-weight: 700; line-height: 1.3; }}
.stMarkdown h3, .stMarkdown h4 {{
    font-size: var(--mjp-h2) !important; font-weight: 700; line-height: 1.4;
    margin-top: var(--mjp-s3) !important; margin-bottom: var(--mjp-s1) !important;
}}
.stMarkdown h5 {{
    font-size: var(--mjp-h3) !important; font-weight: 700;
    margin-top: var(--mjp-s3) !important; margin-bottom: var(--mjp-s1) !important;
}}
.stMarkdown p, .stMarkdown li {{ font-size: var(--mjp-body); line-height: 1.7; color: {BODY}; }}
.stMarkdown strong, .stMarkdown b {{ color: {TEXT}; }}
div[data-testid="stCaptionContainer"], .stCaption, small {{
    font-size: var(--mjp-caption) !important; line-height: 1.6; color: {MUTED} !important;
}}
div[data-testid="stCaptionContainer"] p,
div[data-testid="stCaptionContainer"] li {{
    font-size: var(--mjp-caption) !important; line-height: 1.6; color: {MUTED} !important;
}}
/* 예시 데이터·백업 전환 안내 줄 — 캡션보다 작아지지 않게 본문 크기 (ui.components.note) */
.mjp-note {{ color: {BODY}; font-size: var(--mjp-body); line-height: 1.6; margin-bottom: var(--mjp-s1); }}

/* 화면 제목 블록 (ui.components.section_title) */
.mjp-section-title {{
    font-size: var(--mjp-h1); font-weight: 700; color: {TEXT};
    letter-spacing: -0.03em; line-height: 1.3;
}}
.mjp-section-sub {{
    color: {BODY}; font-size: var(--mjp-body);
    margin-top: var(--mjp-s1); line-height: 1.7; max-width: 62ch;
}}
.mjp-section {{ margin-top: var(--mjp-s4); }}
hr, div[data-testid="stDivider"] {{
    margin-top: var(--mjp-s4) !important; margin-bottom: var(--mjp-s3) !important;
    border-color: {CARD_BORDER} !important; border-width: 1px 0 0 !important;
}}

/* ===== 2. 섹션 패턴 (포트폴리오에서 가져옴) ===== */
/* 작은 파란 라벨 + 큰 두 줄 헤드라인 + 설명 */
.mjp-eyebrow {{
    display: inline-block; font-size: 17px; font-weight: 600; color: {BRAND_DEEP};
    margin-bottom: 14px; letter-spacing: -0.01em;
}}
.stMarkdown .mjp-headline {{
    font-size: var(--mjp-h1) !important; font-weight: 700; color: {TEXT};
    line-height: 1.3; letter-spacing: -0.03em; margin: 0 !important; padding: 0 !important;
}}
.mjp-lead {{
    margin-top: 18px; font-size: var(--mjp-lead); color: {BODY}; line-height: 1.7; max-width: 40em;
}}
.mjp-center {{ text-align: center; }}
.mjp-center .mjp-lead {{ margin-left: auto; margin-right: auto; }}
/* 섹션 블록 — 바탕을 화면 끝까지 칠한다. box-shadow 로 칠해 레이아웃 폭은
   늘지 않는다(100vw 마진 방식은 데스크톱에서 가로 스크롤을 만든다). */
.mjp-band {{ padding: var(--mjp-s5) 0; }}
.mjp-band-alt {{
    background: {BG_SOFT}; box-shadow: 0 0 0 100vmax {BG_SOFT}; clip-path: inset(0 -100vmax);
}}
.mjp-band-alt .mjp-tcard, .mjp-band-alt .mjp-stat {{ background: {BG}; }}

/* 그리드 */
.mjp-grid {{ display: grid; gap: 16px; margin-top: var(--mjp-s4); }}
.mjp-g3 {{ grid-template-columns: repeat(3, 1fr); }}
.mjp-g2 {{ grid-template-columns: repeat(2, 1fr); }}
.mjp-g4 {{ grid-template-columns: repeat(4, 1fr); }}

/* 큰 숫자 통계 */
.mjp-stat {{ background: {CARD}; border-radius: var(--mjp-radius-card); padding: 36px 24px; text-align: center; }}
.mjp-stat-label {{ font-size: var(--mjp-body); color: {MUTED}; font-weight: 500; }}
.mjp-stat-value {{
    margin: 10px 0 6px; font-size: clamp(36px, 4.4vw, 48px); font-weight: 700; color: {BRAND};
    letter-spacing: -0.03em; line-height: 1.15; font-variant-numeric: tabular-nums;
}}
.mjp-stat-note {{ font-size: var(--mjp-small); color: {MUTED}; line-height: 1.6; }}

/* 태그 칩 카드 */
.mjp-tcard {{ background: {CARD}; border-radius: var(--mjp-radius-card); padding: 32px; text-align: left; }}
.stMarkdown .mjp-tcard h4 {{ font-size: var(--mjp-h3) !important; font-weight: 700; color: {TEXT}; margin: 0 0 8px !important; padding: 0 !important; line-height: 1.4; }}
.mjp-tcard p {{ font-size: var(--mjp-body); color: {BODY}; line-height: 1.7; margin: 0; }}
.mjp-chiptag {{
    display: inline-block; font-size: var(--mjp-caption); font-weight: 600;
    padding: 4px 10px; border-radius: 8px; background: {BRAND_LIGHT}; color: {BRAND_DEEP};
    margin: 0 4px 14px 0;
}}
.mjp-chiptag.gray {{ background: {CARD_BORDER}; color: {BODY}; }}
/* 알약 칩 (히어로 아래 소속·자격 표시) */
.mjp-chips {{ display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 28px; }}
.mjp-chip {{
    font-size: 15px; font-weight: 600; color: {BODY};
    background: {CARD}; padding: 8px 16px; border-radius: 999px;
}}

/* STEP 타임라인 */
.mjp-steps {{ list-style: none; margin: var(--mjp-s4) auto 0; padding: 0; max-width: 640px; position: relative; }}
.mjp-steps::before {{
    content: ""; position: absolute; left: 7px; top: 10px; bottom: 10px; width: 2px; background: {CARD_BORDER};
}}
.mjp-steps li {{ position: relative; padding: 0 0 36px 44px; text-align: left; margin: 0; }}
.mjp-steps li:last-child {{ padding-bottom: 0; }}
.mjp-steps li::before {{
    content: ""; position: absolute; left: 0; top: 4px; width: 16px; height: 16px;
    border-radius: 50%; background: {BG}; border: 4px solid {BRAND}; box-sizing: border-box;
}}
.mjp-step-no {{ font-size: var(--mjp-small); color: {BRAND_DEEP}; font-weight: 700; }}
.stMarkdown .mjp-steps h4 {{ font-size: var(--mjp-h3) !important; font-weight: 700; color: {TEXT}; margin: 2px 0 4px !important; padding: 0 !important; }}
.mjp-steps p {{ font-size: var(--mjp-body); color: {BODY}; margin: 0; line-height: 1.65; }}

/* 입력 단계 머리 (스펙 진단 STEP 1·2·3) */
.mjp-stephead {{ display: flex; align-items: baseline; gap: 10px; margin: 8px 0 2px; }}
.mjp-stephead b {{ font-size: var(--mjp-small); color: {BRAND_DEEP}; font-weight: 700; }}
.mjp-stephead span {{ font-size: var(--mjp-h3); color: {TEXT}; font-weight: 700; letter-spacing: -0.02em; }}

/* ===== 3. 카드 · 배지 · 안내 ===== */
.mjp-card {{
    background: {CARD}; border: none; border-radius: var(--mjp-radius-card);
    padding: 24px 28px; margin-bottom: var(--mjp-s2);
}}
.mjp-badge {{
    display: inline-block; font-size: var(--mjp-caption); font-weight: 600; padding: 4px 10px;
    border-radius: 8px; letter-spacing: 0;
}}
.mjp-tag {{
    display: inline-block; font-size: var(--mjp-caption); font-weight: 500; padding: 4px 10px; border-radius: 8px;
    margin-right: 4px; background: {CARD_BORDER}; color: {BODY};
}}
.mjp-muted {{ color: {MUTED}; font-size: var(--mjp-small); line-height: 1.65; }}
.mjp-star {{ color: {GOLD}; }}
/* 예시 데이터 안내 — 연한 블루 면에 본문색 14px. 테두리 대신 면으로 눈에 띄게 둔다 */
.mjp-disclaimer {{
    background: {BRAND_LIGHT}; border: none; border-radius: 16px;
    padding: 14px 18px; font-size: var(--mjp-small); line-height: 1.65;
    color: {BODY}; margin-bottom: var(--mjp-s2);
}}
.mjp-interview {{ background: {CARD}; border-radius: 16px; padding: 16px 18px; margin-bottom: 10px; }}
.mjp-qbadge {{ color: {PURPLE}; font-weight: 700; font-size: var(--mjp-caption); margin-bottom: 4px; display: block; }}
.mjp-btn-align {{ height: 28px; }}
div[class*="st-key-mjp_searchbar"], div[class*="st-key-mjp_filterbar"] {{
    background: {CARD}; border-radius: var(--mjp-radius-card); padding: 20px 24px 8px;
    margin-bottom: var(--mjp-s2);
}}
div[class*="st-key-mjp_searchbar"] div[data-baseweb="input"],
div[class*="st-key-mjp_searchbar"] div[data-baseweb="select"] > div,
div[class*="st-key-mjp_filterbar"] div[data-baseweb="input"],
div[class*="st-key-mjp_filterbar"] div[data-baseweb="select"] > div {{ background: {BG} !important; }}
.mjp-bar-track {{ background: {CARD_BORDER}; border-radius: 999px; height: 8px; width: 100%; }}
.mjp-bar-fill {{ background: {BRAND}; border-radius: 999px; height: 8px; }}
.mjp-later {{ background: {CARD}; border-radius: 16px; padding: 18px 20px; margin-bottom: 14px; }}

/* 기존 화면용 (로그인·역할 선택·허브) — 구조는 3단계에서 바꾼다 */
.mjp-hero {{ position: relative; text-align: center; padding: 24px 12px 16px; }}
.mjp-hero-title {{ font-size: var(--mjp-h1); font-weight: 700; line-height: 1.3; color: {TEXT}; margin: 16px 0 0; }}
.mjp-hero-sub {{ font-size: var(--mjp-lead); color: {BODY}; margin: 14px auto 0; line-height: 1.7; max-width: 620px; }}
.mjp-hero-kicker {{ display: inline-block; font-size: 15px; font-weight: 600; color: {BRAND_DEEP}; }}
.mjp-hero-team {{ font-size: var(--mjp-small); font-weight: 600; color: {MUTED}; margin-top: 12px; }}
.mjp-feature {{
    background: {CARD}; border: none; border-radius: var(--mjp-radius-card);
    padding: 28px 28px 24px; height: 100%;
}}
.mjp-feature-icon {{ line-height: 1; }}
.mjp-feature-title {{ font-size: var(--mjp-h3); font-weight: 700; color: {TEXT}; margin-top: 14px; letter-spacing: -0.02em; }}
.mjp-feature-desc {{ font-size: var(--mjp-body); color: {BODY}; margin-top: var(--mjp-s1); line-height: 1.7; min-height: 62px; }}

/* ===== 4. 상단 바 ===== */
.mjp-topbar {{ display: flex; align-items: center; justify-content: space-between; padding: 8px 0 12px; }}
.mjp-brand {{ display: flex; align-items: center; gap: 10px; }}
.mjp-brand-mark {{ width: 32px; height: 32px; flex: none; display: flex; align-items: center; justify-content: center; }}
.mjp-brand-mark svg {{ width: 100%; height: 100%; display: block; }}
.mjp-logo {{ height: auto; max-width: 100%; display: block; margin: 0 auto; }}
.mjp-logo-svg svg {{ width: 100%; height: 100%; display: block; }}
.mjp-brand-name {{ font-size: 18px; font-weight: 700; color: {TEXT}; line-height: 1.25; letter-spacing: -0.02em; }}
.mjp-brand-sub {{ font-size: 11px; font-weight: 600; color: {MUTED}; letter-spacing: 0.12em; }}
.mjp-userchip {{ text-align: right; padding-top: 4px; overflow-wrap: anywhere; }}
.mjp-userchip-name {{ color: {TEXT}; font-size: var(--mjp-small); font-weight: 600; }}

/* ===== 5. Streamlit 위젯을 새 언어로 덮기 ===== */
/* 버튼 — 기본(보조)은 회색 면, 테두리·그림자 없음 */
.stButton > button,
div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stLinkButton"] a {{
    border-radius: var(--mjp-radius-btn) !important; border: none !important;
    background: {CARD} !important; color: {TEXT} !important;
    min-height: 48px; padding: 0 20px; font-weight: 600; font-size: var(--mjp-body);
    box-shadow: none !important;
    transition: background-color var(--mjp-ease), transform var(--mjp-ease);
}}
.stButton > button p, div[data-testid="stButton"] button p,
div[data-testid="stFormSubmitButton"] button p, div[data-testid="stDownloadButton"] button p {{
    font-size: inherit !important; font-weight: inherit !important; color: inherit !important;
}}
.stButton > button:hover, div[data-testid="stButton"] button:hover,
div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stDownloadButton"] button:hover {{
    background: {CARD_BORDER} !important; color: {TEXT} !important;
}}
.stButton > button:active, div[data-testid="stButton"] button:active,
div[data-testid="stFormSubmitButton"] button:active, div[data-testid="stDownloadButton"] button:active {{
    transform: scale(0.98);
}}
/* 주요 버튼 — 블루 면 + 흰 글자. 면은 BRAND_DEEP(흰 글자 5.41:1).
   위 보조 버튼 규칙(div[data-testid] button)보다 구체적이어야 이긴다. */
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
div[data-testid="stFormSubmitButton"] button[data-testid="stBaseButton-primaryFormSubmit"],
div[data-testid="stDownloadButton"] button[kind="primary"] {{
    background: {BRAND_DEEP} !important; color: #FFFFFF !important;
}}
div[data-testid="stButton"] button[kind="primary"]:hover,
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover,
div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover,
div[data-testid="stFormSubmitButton"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
div[data-testid="stDownloadButton"] button[kind="primary"]:hover {{
    background: {BRAND_PRESS} !important; color: #FFFFFF !important;
}}
.stButton > button:focus-visible, div[data-testid="stButton"] button:focus-visible,
div[data-testid="stDownloadButton"] button:focus-visible {{
    outline: 2px solid {BRAND} !important; outline-offset: 2px;
}}
/* 뒤로가기(← 메인 허브로)는 글자 버튼 */
div[class*="st-key-back_hub_"] button {{
    background: transparent !important; color: {BODY} !important; padding-left: 4px; font-weight: 500;
}}
div[class*="st-key-back_hub_"] button:hover {{ background: {CARD} !important; }}

/* 입력칸 — 회색 면, 테두리 없음, 포커스는 블루 링 */
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div,
div[data-testid="stNumberInputContainer"] {{
    background: {CARD} !important; border: none !important; border-radius: 14px !important;
    transition: box-shadow var(--mjp-ease);
}}
div[data-baseweb="input"] > div, div[data-baseweb="base-input"],
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
    background: transparent !important;
}}
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within, div[data-testid="stNumberInputContainer"]:focus-within {{
    box-shadow: 0 0 0 2px {BRAND} !important;
}}
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea {{
    font-size: var(--mjp-body) !important; min-height: 48px; color: {TEXT} !important;
}}
div[data-baseweb="select"] > div {{ min-height: 48px; }}
/* 선택된 항목 칩 — Streamlit 기본은 primaryColor 면에 흰 글자(3.71:1)라 연한 블루 면으로 바꾼다 */
/* 1.41 계열은 baseweb tag, 1.63 은 react-aria 의 [data-tag] 로 그린다 — 둘 다 잡는다 */
.stApp span[data-baseweb="tag"], div[data-testid="stMultiSelect"] [data-tag] {{
    background-color: {BRAND_LIGHT} !important; color: {BRAND_DEEP} !important; border-radius: 8px !important;
}}
.stApp span[data-baseweb="tag"] span, .stApp span[data-baseweb="tag"] svg,
div[data-testid="stMultiSelect"] [data-tag] *, div[data-testid="stMultiSelect"] [data-tag] svg {{
    color: {BRAND_DEEP} !important; fill: {BRAND_DEEP} !important;
}}
/* 제목 옆 링크(앵커) 아이콘 숨김 — Streamlit 기본 크롬 */
[data-testid="stHeaderActionElements"], .stMarkdown h1 a[href^="#"], .stMarkdown h2 a[href^="#"],
.stMarkdown h3 a[href^="#"], .stMarkdown h4 a[href^="#"] {{ display: none !important; }}
input::placeholder, textarea::placeholder {{ color: {MUTED} !important; opacity: 1; }}
div[data-testid="stWidgetLabel"] label, label[data-testid="stWidgetLabel"],
div[data-testid="stWidgetLabel"] p {{
    font-size: 15px !important; font-weight: 600; color: {TEXT} !important;
}}
/* 접이식 · 알림 · 탭 */
div[data-testid="stExpander"] details {{
    border: none !important; background: {CARD}; border-radius: 16px;
}}
div[data-testid="stExpander"] summary {{ padding: 14px 18px; border-radius: 16px; }}
div[data-testid="stExpander"] summary:hover {{ color: {BRAND_DEEP}; }}
div[data-testid="stAlert"] > div, div[data-testid="stAlertContainer"] {{
    border-radius: 16px !important; border: none !important;
}}
div[data-testid="stDataFrame"] {{ border-radius: 16px; overflow: hidden; }}

/* 레거시 마스코트 스티커 — 원래 배경색(RGB 37,41,42) 타일 위에 원본 그대로 (ui/mascot.py) */
.mjp-mascot-legacy {{ background: #25292A; border-radius: 22px; padding: 8px; box-sizing: border-box; }}

/* ===== 6. 랜딩 ===== */
.mjp-landing-hero {{ text-align: center; padding: 56px 8px 24px; }}
.mjp-landing-mark {{ width: 72px; height: 72px; margin: 0 auto 28px; }}
.mjp-landing-mark svg, .mjp-landing-mark img {{ width: 100%; height: 100%; display: block; }}
.stMarkdown .mjp-landing-title {{
    font-size: var(--mjp-display) !important; font-weight: 700; color: {TEXT};
    line-height: 1.25; letter-spacing: -0.035em; margin: 0 !important; padding: 0 !important;
}}
.mjp-landing-title em {{ font-style: normal; color: {BRAND}; }}
.mjp-landing-note {{ text-align: center; font-size: var(--mjp-small); color: {MUTED}; margin-top: 4px; }}
.mjp-landing-note b {{ color: {TEXT}; font-weight: 600; }}
div[class*="st-key-mjp_cta_landing"] {{ max-width: 340px; margin: 12px auto 0; }}
div[class*="st-key-mjp_cta_landing"] button {{ min-height: 56px; font-size: 17px; }}
.mjp-mascot-hello {{
    display: flex; align-items: center; justify-content: center; gap: 16px; flex-wrap: wrap;
    margin-top: var(--mjp-s4);
}}
.mjp-mascot-hello p {{ color: {BODY}; font-size: var(--mjp-body); line-height: 1.7; max-width: 300px; margin: 0; }}
.mjp-footer {{
    text-align: center; padding: 40px 8px 8px; font-size: var(--mjp-small); color: {MUTED}; line-height: 1.8;
    border-top: 1px solid {CARD_BORDER}; margin-top: var(--mjp-s4);
}}
.mjp-footer .mjp-disclaimer {{ display: inline-block; margin: 12px 0 0; color: {BODY}; }}

/* ===== 7. 스펙 진단 점수 ===== */
/* 데스크톱: 왼쪽 큰 점수 · 오른쪽 세부 4줄. 폰: 위아래 */
.mjp-score-grid {{
    display: grid; grid-template-columns: 1.15fr 1fr; gap: 40px; align-items: center;
    padding: 8px 0 var(--mjp-s3);
}}
.mjp-score-grid-single {{ grid-template-columns: 1fr; max-width: 680px; }}
.mjp-score {{ padding: 8px 0 4px; }}
.mjp-score-label {{ font-size: 17px; font-weight: 600; color: {BODY}; }}
.mjp-score-line {{ display: flex; align-items: baseline; gap: 8px; margin-top: 4px; flex-wrap: wrap; }}
.mjp-score-num {{
    font-size: var(--mjp-num); font-weight: 800; letter-spacing: -0.045em; line-height: 1.05;
    font-variant-numeric: tabular-nums;
}}
.mjp-score-unit {{ font-size: 22px; font-weight: 600; color: {MUTED}; }}
.mjp-score-chip {{
    display: inline-block; font-size: var(--mjp-body); font-weight: 700; padding: 6px 12px; border-radius: 10px;
    margin-left: 6px; transform: translateY(-10px);
}}
.mjp-score-msg {{ font-size: var(--mjp-lead); color: {BODY}; margin-top: 10px; line-height: 1.6; }}
/* 100점 눈금 막대 — 50 · 80 구간 경계에 눈금 */
.mjp-meter {{ position: relative; margin: 28px 0 8px; }}
.mjp-meter-track {{ height: 12px; border-radius: 999px; background: {CARD}; overflow: hidden; }}
.mjp-meter-fill {{ height: 100%; border-radius: 999px; }}
.mjp-meter-tick {{ position: absolute; top: -4px; width: 2px; height: 20px; background: {BG}; }}
.mjp-meter-labels {{ position: relative; height: 22px; margin-top: 6px; font-size: var(--mjp-caption); color: {MUTED}; }}
.mjp-meter-labels span {{ position: absolute; transform: translateX(-50%); white-space: nowrap; }}
.mjp-meter-labels span:first-child {{ transform: none; }}
.mjp-meter-labels span:last-child {{ transform: translateX(-100%); }}
.mjp-meter-labels em {{ font-style: normal; }}
/* 세부 점수 4줄 — 회색 면 한 장 안의 목록 */
.mjp-break {{ background: {CARD}; border-radius: var(--mjp-radius-card); padding: 8px 24px; }}
.mjp-break-row {{ padding: 16px 0; }}
.mjp-break-row + .mjp-break-row {{ border-top: 1px solid {CARD_BORDER}; }}
.mjp-break-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }}
.mjp-break-name {{ font-size: var(--mjp-body); color: {BODY}; font-weight: 500; }}
.mjp-break-val {{ font-size: 18px; color: {TEXT}; font-weight: 700; font-variant-numeric: tabular-nums; }}
.mjp-break-val small {{ font-size: var(--mjp-small) !important; color: {MUTED} !important; font-weight: 500; margin-left: 2px; }}
.mjp-break .mjp-bar-track {{ height: 6px; margin-top: 10px; background: {CARD_BORDER}; }}
.mjp-break .mjp-bar-fill {{ height: 6px; }}
/* 설명 카드 (마스코트 옆) */
.mjp-explain {{ background: {CARD}; border-radius: var(--mjp-radius-card); padding: 24px 28px; }}
.mjp-explain-body {{ margin-top: 12px; color: {BODY}; line-height: 1.75; }}
.mjp-explain-next {{
    margin-top: 16px; padding: 14px 16px; border-radius: 14px; background: {BG};
    color: {TEXT}; font-weight: 600; line-height: 1.6;
}}
.mjp-explain-next b {{ color: {BRAND_DEEP}; margin-right: 6px; }}

/* ===== 8. 모바일 (QR 스캔 접속) ===== */
@media (max-width: {MOBILE_BREAKPOINT}px) {{
    .block-container {{ padding: 16px 16px 48px; }}
    :root {{ --mjp-s4: 48px; --mjp-s5: 72px; }}

    /* 숫자 스테퍼·파일 업로더 버튼 44px */
    div[data-testid="stNumberInput"] button,
    div[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputStepUp"] {{ min-height: 44px !important; min-width: 44px !important; }}
    section[data-testid="stFileUploaderDropzone"] button,
    div[data-testid="stFileUploader"] button {{ min-height: 44px !important; }}

    /* 상단 브랜드|사용자 줄은 1단 전환에서 제외 */
    div[class*="st-key-mjp_brandrow"] div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important; flex-wrap: nowrap !important; gap: 8px !important;
    }}
    div[class*="st-key-mjp_brandrow"] div[data-testid="stColumn"]:first-child {{
        width: auto !important; flex: 1 1 auto !important; min-width: 0 !important;
    }}
    div[class*="st-key-mjp_brandrow"] div[data-testid="stColumn"]:last-child {{
        width: auto !important; flex: 0 0 auto !important; min-width: 0 !important;
    }}
    .mjp-brand-name {{ white-space: nowrap; font-size: 17px; }}
    .mjp-userchip-name {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .mjp-userchip .mjp-muted {{ display: none; }}
    .mjp-userchip {{ max-width: 42%; text-align: right; padding-top: 6px; overflow: hidden; }}

    /* 핵심: st.columns 다단을 1단으로 강제 전환 */
    div[data-testid="stHorizontalBlock"] {{ flex-direction: column !important; gap: 0.75rem !important; }}
    div[data-testid="stColumn"] {{ width: 100% !important; min-width: 100% !important; flex: 1 1 100% !important; }}

    .mjp-g3, .mjp-g2 {{ grid-template-columns: 1fr; }}
    .mjp-g4 {{ grid-template-columns: repeat(2, 1fr); gap: 12px; }}
    .mjp-tcard {{ padding: 28px 24px; }}
    .mjp-stat {{ padding: 28px 20px; }}
    .mjp-landing-hero {{ padding: 32px 0 8px; }}
    .mjp-landing-mark {{ width: 60px; height: 60px; margin-bottom: 24px; }}
    .mjp-section-sub {{ font-size: var(--mjp-small); }}
    .mjp-card {{ padding: 20px; }}
    .mjp-card, .mjp-feature {{ padding: 20px; }}
    .mjp-feature-desc {{ min-height: 0; }}
    .mjp-break {{ padding: 4px 20px; }}
    .mjp-score-grid {{ grid-template-columns: 1fr; gap: 24px; }}
    .mjp-meter-labels em {{ display: none; }}   /* 폰에서는 눈금 숫자만 — 구간 이름은 칩이 말한다 */
    .mjp-explain {{ padding: 20px; }}
    .mjp-score-chip {{ transform: translateY(-6px); }}
    hr, div[data-testid="stDivider"] {{ margin-top: var(--mjp-s3) !important; margin-bottom: var(--mjp-s2) !important; }}

    /* 버튼은 엄지 크기 */
    .stButton > button, div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button, div[data-testid="stDownloadButton"] button {{
        min-height: 48px !important;
    }}

    /* ▣ 주요 버튼을 화면 하단에 꽉 차게 고정 (토스식 하단 CTA)
       컨테이너 key 가 mjp_cta_ 로 시작하면 적용된다. 본문 맨 아래가 버튼에
       가리지 않도록 그 화면에서만 아래 여백을 늘린다. */
    div[class*="st-key-mjp_cta_"] {{
        position: fixed; left: 0; right: 0; bottom: 0; z-index: 100; max-width: none; margin: 0;
        padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
        background: linear-gradient(to top, {BG} 72%, rgba(255,255,255,0));
    }}
    div[class*="st-key-mjp_cta_"] button {{ min-height: 56px !important; font-size: 17px !important; }}
    .stApp:has(div[class*="st-key-mjp_cta_"]) .block-container {{ padding-bottom: 120px; }}

    /* 입력 컨트롤 터치 높이 44px */
    div[data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{ min-height: 48px !important; }}
    div[data-baseweb="select"] [aria-label="Open"],
    div[data-testid="stTextInputRootElement"] button {{ min-height: 44px !important; min-width: 40px !important; }}

    /* iOS 사파리 자동 확대 방지 — 입력 글자 16px 이상 */
    div[data-testid="stSelectbox"] input, div[data-testid="stMultiSelect"] input,
    div[data-testid="stMultiSelectTagsContainer"] input,
    div[data-baseweb="select"] input, div[data-baseweb="input"] input {{ font-size: var(--mjp-body) !important; }}

    /* 도움말(?) 아이콘의 탭 영역 */
    div[data-testid="stTooltipHoverTarget"] {{
        min-width: 30px; min-height: 30px; display: inline-flex; align-items: center; justify-content: center;
    }}

    .mjp-topbar {{ flex-wrap: nowrap; gap: 10px; padding: 6px 0 10px; }}
    .mjp-brand-sub {{ display: none; }}
    .mjp-brand-mark {{ width: 28px; height: 28px; }}
    .st-key-mjp_hub_sticker {{ display: none !important; }}

    /* 예외: 상단 기능 내비는 가로 스크롤 */
    .st-key-mjp_navbar div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important; flex-wrap: nowrap !important; overflow-x: auto;
        -webkit-overflow-scrolling: touch; scrollbar-width: none; gap: 4px !important; padding-bottom: 2px;
    }}
    .st-key-mjp_navbar div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {{ display: none; }}
    .st-key-mjp_navbar div[data-testid="stColumn"] {{ width: auto !important; min-width: auto !important; flex: 0 0 auto !important; }}
    .st-key-mjp_navbar .stButton > button {{ white-space: nowrap; padding: 0 14px; }}

    /* 예외 2: 카드 하단의 짧은 버튼 줄은 가로 유지 */
    div[class*="st-key-mjp_row"] div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important; flex-wrap: nowrap !important; gap: 0.4rem !important;
    }}
    div[class*="st-key-mjp_row"] div[data-testid="stColumn"] {{ width: auto !important; min-width: 0 !important; flex: 1 1 0 !important; }}
    div[class*="st-key-mjp_row"] .stButton > button {{
        font-size: var(--mjp-small); padding-left: 6px; padding-right: 6px; white-space: nowrap; overflow: hidden;
    }}
    div.st-key-mjp_row_story_nav .stButton > button,
    div.st-key-mjp_row_story_nav .stButton > button p {{ white-space: normal !important; line-height: 1.25; }}

    div[data-testid="stDataFrame"] {{ overflow-x: auto; }}
}}

/* 상단 내비 — 데스크톱·모바일 공통: 글자 탭. 선택된 탭만 연한 블루 면 */
.st-key-mjp_navbar div[data-testid="stButton"] button {{
    background: transparent !important; color: {BODY} !important; font-size: 15px; font-weight: 600;
    min-height: 44px; border-radius: 12px !important; padding: 0 12px;
}}
.st-key-mjp_navbar div[data-testid="stButton"] button:hover {{ background: {CARD} !important; color: {TEXT} !important; }}
.st-key-mjp_navbar div[data-testid="stButton"] button[kind="primary"],
.st-key-mjp_navbar div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {{
    background: {BRAND_LIGHT} !important; color: {BRAND_DEEP} !important;
}}

@media (max-width: 380px) {{
    .mjp-brand-sub {{ display: none; }}
}}
@media (prefers-reduced-motion: reduce) {{
    .stApp * {{ transition: none !important; }}
}}
</style>
""", unsafe_allow_html=True)


def status_color(pct: float) -> str:
    """비율(0~100) → 상태색. 총점 판정과 같은 구간: 80↑ 그린 · 50↑ 골드 · 미만 레드."""
    return GREEN if pct >= 80 else (GOLD if pct >= 50 else RED)


def score_bar(label: str, value: float, maximum: int) -> str:
    """
    세부 점수 한 줄 HTML (이름 · 값 · 얇은 막대). 여러 화면에서 재사용되므로 테마 모듈에 둔다.

    채움 색은 비율로 정한다 — 총점 판정과 같은 구간. 그린 고정이면 15/30 이
    '보완 시급' 옆에서 초록으로 떠 '초록 = 좋음' 신호와 어긋난다.
    .mjp-break 안에 넣으면 회색 면 목록이 되고, 밖에 두면 단독 막대가 된다.
    """
    pct = 0 if not maximum else min(100, value / maximum * 100)
    fill = STATUS_VIVID[status_color(pct)]
    return f"""
    <div class="mjp-break-row">
      <div class="mjp-break-head">
        <span class="mjp-break-name">{label}</span>
        <span class="mjp-break-val">{value}<small>/ {maximum}</small></span>
      </div>
      <div class="mjp-bar-track">
        <div class="mjp-bar-fill" style="width:{pct:.0f}%; background:{fill};"></div>
      </div>
    </div>"""


def render_stars(rating: float) -> str:
    """
    별점 HTML.

    ★☆ 문자 대신 SVG 로 그린다. 문자 별은 폰트에 따라 굵기·크기가 달라지고
    안드로이드 일부 기기에서는 이모지 폰트로 렌더링돼 주황색 별이 튀어나온다.
    """
    from ui.icons import icon

    full = int(rating)
    stars = "".join(
        icon("star", size=13, color=GOLD, filled=(i < full), stroke=1.6)
        for i in range(5)
    )
    return (f'<span style="display:inline-flex; align-items:center; gap:1px; '
            f'vertical-align:-0.16em;">{stars}</span>'
            f'<span style="color:{MUTED}; font-size:var(--mjp-caption); margin-left:5px;">{rating:.1f}</span>')
