# -*- coding: utf-8 -*-
"""
ui/theme.py
[Phase 6] 디자인 토큰 + 전역 CSS + 모바일 반응형 단일 관문

설계 의도
---------
기존 app.py 상단에 박혀 있던 색상 상수와 <style> 블록을 이 모듈로 모았다.
화면 파일(views/*.py)은 색을 직접 알 필요가 없고 여기서 import 하기만 한다.

▣ 모바일 대응이 왜 CSS 한 곳에 모여야 하는가
   심사 현장에서 학생/심사위원은 QR을 찍어 '폰'으로 접속한다. Streamlit의
   st.columns()는 좁은 화면에서 자동으로 1단이 되지 않고 가로로 짓눌리기만
   한다(글자가 세로로 쪼개짐). 그래서 아래 @media 블록에서 Streamlit이
   컬럼에 붙이는 data-testid를 직접 잡아 1단으로 강제 전환한다.
   이 규칙이 여러 파일에 흩어지면 한 화면만 깨져도 원인을 못 찾는다.
"""

import base64

import streamlit as st

from ui.emblem import circuit_pattern_svg

# ============================================================
# 디자인 토큰 (config.toml 의 [theme] 값과 일치시킬 것)
# ============================================================
BG = "#0A0E17"
BG_SOFT = "#0E1320"
CARD = "#131826"
CARD_BORDER = "#232B3D"
TEXT = "#E7EAF0"
MUTED = "#8A93A6"
GREEN = "#34D399"
GOLD = "#FBBF24"
PURPLE = "#8B5CF6"
RED = "#F87171"
BLUE = "#3B82F6"

# ------------------------------------------------------------
# 브랜드 컬러 램프 — 팀 로고에서 추출
# ------------------------------------------------------------
# 원본 로고의 짙은 네이비 잉크를 다크 배경에서 읽히도록 밝기를 뒤집은 값이다.
# ui/emblem.py 의 엠블럼, ui/brand.py 의 로고 블렌딩, 아래 CSS 가 모두 이
# 세 값을 공유하므로 로고·엠블럼·UI가 한 벌로 붙는다.
BRAND_LIGHT = "#A8CEF5"   # 시안 하이라이트
BRAND = "#4C8FE0"         # 일렉트릭 블루 (로고 회로선)
BRAND_DEEP = "#2B6BC4"    # 딥 블루

# ▣ 색의 역할을 분리한다
#   브랜드 블루 = 정체성 (로고 · 내비 · 히어로 · 카드 호버)
#   그린        = 상태 시맨틱 전용 (LIVE 배지 · 합격 안정권 · 성공 메시지)
#   그린을 장식으로도 쓰면 "초록 = 좋음"이라는 신호가 희석된다.

# 큐레이션은 장애가 아니라 설계된 상태다 — 경고색(골드)이 아니라
# 무채색으로 두어 백업(폴백)과 눈으로 구분되게 한다.
BADGE_COLORS = {"live": GREEN, "backup": GOLD, "curated": MUTED,
                "ink": BG, "muted": MUTED}

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
    # 회로 패턴을 base64 data URI 로 인라인한다.
    # utf8 data URI 로 넣으면 SVG 안의 '#' 색상값이 URL 프래그먼트로 잘려
    # 패턴이 통째로 사라진다 — base64 가 이스케이프 사고가 없다.
    circuit_b64 = base64.b64encode(
        circuit_pattern_svg(BRAND, 0.9).encode("utf-8")
    ).decode("ascii")

    st.markdown(f"""
<style>
/* ===== 디자인 토큰 =====
   타이포·여백·그림자·전환을 여기 한 곳에서만 정의한다. 화면 CSS 는 값을
   직접 쓰지 않고 var() 로 참조하므로, 위계를 바꾸려면 이 블록만 고치면 된다. */
/* 주 폰트 Pretendard (jsdelivr) + 폴백 웹폰트 Noto Sans KR (Google Fonts).
   둘 다 싣는 이유: 학교·기관망이 jsdelivr 을 막는 경우가 있는데, 그때 폴백이
   웹폰트가 아니면 기기 기본 한글 폰트로 떨어져 화면이 완전히 달라 보인다.
   Pretendard 가 뜨면 Noto 는 실제로 내려받지 않는다(사용된 폰트만 다운로드). */
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css");
@import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap");

:root {{
    /* 본문 폰트. Pretendard 는 한글 자소서·기업명이 본문 주력인 이 앱에
       맞춰 고른 값이고, 뒤는 로드 실패 시의 한글 폴백 사슬이다. */
    --mjp-font: "Pretendard Variable", Pretendard, "Noto Sans KR", -apple-system,
                BlinkMacSystemFont, system-ui, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;

    /* 타이포 6단 — 이 여섯 개 밖의 크기를 새로 만들지 않는다.
       기존에 10~58px 17종이 흩어져 위계가 읽히지 않았다. */
    --mjp-display: 34px;   /* 랜딩 히어로 */
    --mjp-h1: 26px;        /* 화면 제목 */
    --mjp-h2: 20px;        /* 섹션 제목 */
    --mjp-body: 16px;      /* 본문 */
    --mjp-small: 14px;     /* 보조 설명 */
    --mjp-caption: 13px;   /* 캡션·배지 */

    /* 여백 4단. 섹션 사이는 항상 --mjp-s4 이상을 쓴다. */
    --mjp-s1: 8px;
    --mjp-s2: 16px;
    --mjp-s3: 32px;
    --mjp-s4: 56px;

    /* 그림자는 옅게 두 단. 진하면 다크 배경에서 카드가 뜬 것처럼 보인다. */
    --mjp-shadow-1: 0 1px 2px rgba(0,0,0,0.26);
    --mjp-shadow-2: 0 1px 2px rgba(0,0,0,0.28), 0 10px 28px rgba(0,0,0,0.20);

    --mjp-ease: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --mjp-radius: 14px;
}}

/* 폰트를 앱 전체와 Streamlit 위젯 내부까지 적용한다.
   Streamlit 은 body 에 직접 "Source Sans" 를 지정하므로 html/body 를 함께
   잡지 않으면 본문이 기본 폰트로 남는다 (.stApp 만으로는 부족하다). */
html, body, .stApp, .stApp *,
input, textarea, select, button, [class^="st-"], [class*=" st-"] {{
    font-family: var(--mjp-font) !important;
}}

/* ▣ 전역 폰트 규칙에서 되돌려야 하는 것들
   위 규칙은 !important 라 폰트 자체가 글리프인 요소까지 덮어쓴다.
   Streamlit 의 아이콘은 'keyboard_arrow_right' 같은 리거처 이름을 글자로
   넣고 아이콘 폰트로 그리는 방식이라, 본문 폰트가 씌워지면 그 이름이
   화면에 그대로 찍힌다 (expander 화살표 자리에 글자가 겹쳐 보였다).
   Material Symbols 는 Streamlit 이 로컬로 함께 배포하므로 외부망과 무관하다. */
[data-testid="stIconMaterial"],
.material-icons, .material-icons-outlined,
.material-symbols-rounded, .material-symbols-outlined {{
    font-family: "Material Symbols Rounded", "Material Icons" !important;
}}
/* 코드·수식도 본문 폰트로 덮이면 정렬이 무너진다 */
code, pre, kbd, samp, .stCode, [data-testid="stCode"] * {{
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace !important;
}}
.katex, .katex * {{ font-family: KaTeX_Main, "Times New Roman", serif !important; }}

.stApp {{ font-size: var(--mjp-body); }}

/* ===== 0. 기본 바탕 ===== */
.stApp {{ background: {BG}; }}
h1, h2, h3, h4, h5 {{ color: {TEXT}; letter-spacing: -0.02em; }}

/* Streamlit 기본 상단 여백을 줄여 랜딩 히어로가 화면을 꽉 채우게 한다 */
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }}

/* 우상단 햄버거/배포 뱃지 숨김 — 시연 화면을 깔끔하게 */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* Streamlit 기본 헤더 바를 투명하게.
   그냥 두면 흰 띠가 다크 테마 위에 남고, 모바일에서는 브랜드 영역을 덮어버린다.
   display:none 대신 투명 처리하는 이유 — 숨기면 상단 여백까지 사라져
   콘텐츠가 노치/상태바에 붙는다. */
header[data-testid="stHeader"] {{
    background: transparent !important;
    height: 2.2rem;
}}
header[data-testid="stHeader"] * {{ color: {MUTED} !important; }}
div[data-testid="stToolbar"] {{ right: 0.4rem; }}

/* ===== 화면 제목 블록 ===== */
.mjp-section-title {{
    font-size: var(--mjp-h1); font-weight: 800; color: {TEXT};
    letter-spacing: -0.03em; line-height: 1.25;
}}
.mjp-section-sub {{
    color: {MUTED}; font-size: var(--mjp-small);
    margin-top: var(--mjp-s1); line-height: 1.65; max-width: 62ch;
}}
/* 섹션 사이 호흡. Streamlit 기본 간격(1rem 남짓)으로는 화면이 빽빽해진다. */
.mjp-section {{ margin-top: var(--mjp-s4); }}
hr, div[data-testid="stDivider"] {{
    margin-top: var(--mjp-s4) !important;
    margin-bottom: var(--mjp-s3) !important;
    border-color: {CARD_BORDER};
}}
/* 마크다운 제목을 6단 스케일에 맞춘다 — Streamlit 기본값(h3=28px 등)이
   그대로 나오면 스케일 밖 크기가 화면에 섞인다. */
.stMarkdown h1 {{ font-size: var(--mjp-h1) !important; }}
.stMarkdown h2 {{ font-size: var(--mjp-h1) !important; }}
.stMarkdown h3 {{
    font-size: var(--mjp-h2) !important; font-weight: 800;
    margin-top: var(--mjp-s3) !important; margin-bottom: var(--mjp-s2) !important;
    letter-spacing: -0.02em;
}}
.stMarkdown h4 {{
    font-size: var(--mjp-h2) !important; font-weight: 800;
    margin-top: var(--mjp-s3) !important; margin-bottom: var(--mjp-s2) !important;
    letter-spacing: -0.02em;
}}
.stMarkdown p, .stMarkdown li {{ font-size: var(--mjp-body); line-height: 1.7; }}
div[data-testid="stCaptionContainer"], .stCaption, small {{
    font-size: var(--mjp-caption) !important; line-height: 1.6;
}}

/* ===== 1. 공통 카드 ===== */
.mjp-card {{
    background: {CARD}; border: 1px solid {CARD_BORDER};
    border-radius: var(--mjp-radius);
    padding: 22px 24px; margin-bottom: var(--mjp-s2);
    box-shadow: var(--mjp-shadow-1);
    transition: border-color var(--mjp-ease), box-shadow var(--mjp-ease),
                transform var(--mjp-ease);
}}
.mjp-card:hover {{
    border-color: rgba(76,143,224,0.45);
    box-shadow: var(--mjp-shadow-2);
    transform: translateY(-2px);
}}
.mjp-badge {{
    display: inline-block; font-size:var(--mjp-caption); font-weight: 700; padding: 4px 11px;
    border-radius: 999px; letter-spacing: 0.03em;
}}
.mjp-tag {{
    display: inline-block; font-size:var(--mjp-caption); padding: 3px 10px; border-radius: 7px;
    margin-right: 4px; background: {CARD_BORDER}; color: {MUTED};
}}
.mjp-muted {{ color: {MUTED}; font-size: var(--mjp-small); line-height: 1.65; }}
.mjp-star {{ color: {GOLD}; }}
.mjp-disclaimer {{
    background: rgba(52,211,153,0.08); border: 1px dashed {GREEN};
    border-radius: 10px; padding: 8px 12px; font-size:var(--mjp-caption);
    color: {MUTED}; margin-bottom: 14px;
}}
.mjp-interview {{
    background: {CARD}; border: 1px solid {PURPLE}; border-radius: 10px;
    padding: 12px 14px; margin-bottom: 10px;
}}
.mjp-qbadge {{ color: {PURPLE}; font-weight: 700; font-size:var(--mjp-caption); margin-bottom: 4px; display: block; }}
/* 검색바 — 라벨 없는 버튼을 옆 입력창의 baseline 에 맞춘다.
   (Streamlit 은 라벨 높이만큼 입력만 밀어내므로 버튼이 위로 뜬다) */
.mjp-btn-align {{ height: 28px; }}
div[class*="st-key-mjp_searchbar"] {{
    background: {BG_SOFT}; border: 1px solid {CARD_BORDER};
    border-radius: var(--mjp-radius); padding: 18px 20px 6px;
    margin-bottom: var(--mjp-s2);
}}

/* 탐색기 필터바 — 검색바와 같은 형태로 묶어 '조건을 거는 곳'으로 읽히게 한다 */
div[class*="st-key-mjp_filterbar"] {{
    background: {BG_SOFT}; border: 1px solid {CARD_BORDER};
    border-radius: var(--mjp-radius); padding: 18px 20px 6px;
    margin-bottom: var(--mjp-s2);
}}

/* ===== 스펙 진단 점수 배너 =====
   화면 폭 전체를 쓰는 요약 배너. 모바일에서도 첫 화면 안에 들어오도록
   높이를 낮게 잡고, 좁아지면 원과 판정문이 세로로 접힌다. */
.mjp-scorecard {{
    background: linear-gradient(150deg, {CARD} 0%, {BG_SOFT} 100%);
    border: 1px solid {CARD_BORDER}; border-radius: 18px;
    padding: 22px 26px; margin-bottom: var(--mjp-s2);
    box-shadow: var(--mjp-shadow-2);
}}
.mjp-scorecard-row {{
    display: flex; align-items: center; gap: 24px;
    margin-top: 14px; flex-wrap: wrap;
}}
.mjp-scorering {{
    width: 112px; height: 112px; border-radius: 50%; flex: none;
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; color: {BG};
}}
.mjp-scorering-num {{ font-size: var(--mjp-display); font-weight: 800; line-height: 1; }}
.mjp-scorering-cap {{ font-size: var(--mjp-caption); font-weight: 700; margin-top: 4px; opacity: 0.82; }}
.mjp-verdict {{ font-size: var(--mjp-h2); font-weight: 800; letter-spacing: -0.02em; }}

.mjp-bar-track {{ background: {CARD_BORDER}; border-radius: 999px; height: 8px; width: 100%; }}
.mjp-bar-fill {{ background: {GREEN}; border-radius: 999px; height: 8px; }}
.mjp-later {{
    background: {CARD}; border: 1px dashed {CARD_BORDER}; border-left: 4px solid {PURPLE};
    border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
}}

/* ===== 2. 랜딩 히어로 (참고 디자인: 큰 타이포 + 넉넉한 여백 + 은은한 그라데이션) ===== */
.mjp-hero {{
    position: relative; text-align: center;
    /* 히어로가 화면 절반을 먹으면 CTA 가 fold 아래로 밀린다 */
    padding: 30px 20px 16px; margin-bottom: 4px;
}}
/* 로고 뒤에 깔리는 은은한 방사형 글로우 — 다크 배경에 깊이를 준다 */
.mjp-hero::before {{
    content: ""; position: absolute; top: -40px; left: 50%;
    transform: translateX(-50%);
    width: 620px; height: 420px; pointer-events: none; z-index: 0;
    background: radial-gradient(circle at 50% 35%,
        rgba(76,143,224,0.22) 0%,
        rgba(43,107,196,0.12) 38%,
        rgba(10,14,23,0) 70%);
    filter: blur(6px);
}}
/* 로고의 PCB 회로 모티프를 배경에 아주 옅게 깐다.
   불투명도 0.05 — '있는 줄 모르지만 없으면 허전한' 수준으로만 둔다. */
.mjp-hero::after {{
    content: ""; position: absolute; inset: -30px 0 0; z-index: 0;
    pointer-events: none; opacity: 0.05;
    background-image: url("data:image/svg+xml;base64,{circuit_b64}");
    background-size: 220px 220px;
    -webkit-mask-image: radial-gradient(ellipse at 50% 30%, #000 0%, transparent 72%);
    mask-image: radial-gradient(ellipse at 50% 30%, #000 0%, transparent 72%);
}}
.mjp-hero > * {{ position: relative; z-index: 1; }}

.mjp-hero-title {{
    font-size: clamp(34px, 5.4vw, 52px); font-weight: 800; line-height: 1.1;
    letter-spacing: -0.035em; margin: 18px 0 0;
    background: linear-gradient(180deg, {TEXT} 0%, #9FB0CC 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.mjp-hero-sub {{
    font-size: var(--mjp-h2); color: {MUTED}; margin-top: var(--mjp-s2); line-height: 1.65;
    max-width: 620px; margin-left: auto; margin-right: auto;
}}
.mjp-hero-kicker {{
    display: inline-block; font-size: var(--mjp-caption); font-weight: 700; letter-spacing: 0.08em;
    color: {BRAND_LIGHT}; border: 1px solid rgba(76,143,224,0.38);
    background: rgba(76,143,224,0.10);
    padding: 5px 14px; border-radius: 999px; text-transform: uppercase;
}}
/* 로고 하단 레터스페이싱을 타이포 요소로 가져온 서브라인 */
.mjp-hero-team {{
    font-size: var(--mjp-caption); font-weight: 700; color: {BRAND};
    letter-spacing: 0.14em; margin-top: 14px;
}}

/* ===== 3. 기능 카드 (메인 허브) ===== */
.mjp-feature {{
    background: linear-gradient(160deg, {CARD} 0%, {BG_SOFT} 100%);
    border: 1px solid {CARD_BORDER}; border-radius: 16px;
    padding: 26px 24px 22px; height: 100%;
    box-shadow: var(--mjp-shadow-1);
    transition: border-color var(--mjp-ease), transform var(--mjp-ease),
                box-shadow var(--mjp-ease);
}}
.mjp-feature:hover {{
    border-color: {BRAND}; transform: translateY(-3px);
    box-shadow: var(--mjp-shadow-2);
}}
.mjp-feature-icon {{ font-size:var(--mjp-h1); line-height: 1; }}
.mjp-feature-title {{ font-size: var(--mjp-h2); font-weight: 800; color: {TEXT}; margin-top: 14px; letter-spacing: -0.02em; }}
.mjp-feature-desc {{ font-size: var(--mjp-small); color: {MUTED}; margin-top: var(--mjp-s1); line-height: 1.65; min-height: 62px; }}

/* ===== 4. 상단 내비게이션 바 ===== */
.mjp-topbar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0 14px; border-bottom: 1px solid {CARD_BORDER}; margin-bottom: 18px;
}}
.mjp-brand {{ display: flex; align-items: center; gap: 10px; }}
.mjp-brand-mark {{
    width: 36px; height: 36px; flex: none;
    display: flex; align-items: center; justify-content: center;
}}
.mjp-brand-mark svg {{ width: 100%; height: 100%; display: block; }}

/* ===== 로고 ===== */
.mjp-logo {{
    height: auto; max-width: 100%; display: block; margin: 0 auto;
    /* 엠블럼 링 바깥으로 번지는 발광. 로고가 배경 위에 '떠 있지' 않고
       배경에서 빛나는 것처럼 보이게 하는 장치다. */
    filter: drop-shadow(0 0 22px rgba(76,143,224,0.28));
}}
.mjp-logo-svg svg {{ width: 100%; height: 100%; display: block; }}
.mjp-brand-name {{ font-size: var(--mjp-small); font-weight: 800; color: {TEXT}; line-height: 1.25; }}
.mjp-brand-sub {{
    /* 자간을 넓힌 마이크로 라벨. 본문이 아니라 로고의 일부라 스케일 밖이지만,
       가독성 하한(11px)은 지킨다. */
    font-size: 11px; font-weight: 700; color: {BRAND};
    letter-spacing: 0.17em;   /* 원본 로고 하단 아크 타이포에서 가져온 자간 */
}}
.mjp-userchip {{ text-align: right; padding-top: 6px; overflow-wrap: anywhere; }}
.mjp-userchip-name {{ color: {TEXT}; font-size:var(--mjp-caption); font-weight: 700; }}

/* ===== 5. Streamlit 위젯 다듬기 ===== */
/* 버튼 선택자를 data-testid 기반으로 잡는다.
   .stButton 클래스만 쓰면 Streamlit 버전에 따라 일부 버튼이 규칙 밖으로
   빠진다 (실측에서 '다시 생성하기'가 40px 로 남아 있었다). */
.stButton > button,
div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button {{
    border-radius: 11px; font-weight: 700; border: 1px solid {CARD_BORDER};
    min-height: 44px;              /* 터치 타깃 최소 44px (애플 HIG 권장) */
    font-size: var(--mjp-small);
    box-shadow: var(--mjp-shadow-1);
    transition: border-color var(--mjp-ease), transform var(--mjp-ease),
                box-shadow var(--mjp-ease), background-color var(--mjp-ease);
}}
.stButton > button:hover,
div[data-testid="stButton"] button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover {{
    border-color: {BRAND};
    transform: translateY(-1px);
    box-shadow: var(--mjp-shadow-2);
}}
/* 누르는 순간 되돌아오는 반응 — 클릭이 먹었는지 눈으로 확인된다 */
.stButton > button:active,
div[data-testid="stButton"] button:active,
div[data-testid="stFormSubmitButton"] button:active {{
    transform: translateY(0); box-shadow: var(--mjp-shadow-1);
}}
/* 키보드 포커스 링 — 마우스 클릭에는 뜨지 않는다 */
.stButton > button:focus-visible,
div[data-testid="stButton"] button:focus-visible {{
    outline: 2px solid {BRAND}; outline-offset: 2px;
}}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea {{
    font-size:var(--mjp-body) !important;    /* iOS 사파리 자동 확대(zoom) 방지 임계값 */
    min-height: 44px;
}}
/* 입력 컨트롤 공통 — 포커스가 어디 있는지 보이게 한다 */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextArea"] div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {{
    border-radius: 11px;
    transition: border-color var(--mjp-ease), box-shadow var(--mjp-ease);
}}
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within {{
    border-color: {BRAND} !important;
    box-shadow: 0 0 0 3px rgba(76,143,224,0.16);
}}
/* 위젯 라벨 위계 */
div[data-testid="stWidgetLabel"] label, label[data-testid="stWidgetLabel"] {{
    font-size: var(--mjp-small) !important; font-weight: 700; color: {TEXT};
}}

/* ===== 6. 모바일 (QR 스캔 접속) ===== */
@media (max-width: {MOBILE_BREAKPOINT}px) {{
    .block-container {{ padding: 1.1rem 0.85rem 2.4rem; }}

    /* 숫자 입력의 +/- 스테퍼와 파일 업로더 버튼은 Streamlit 이 기본 38~40px 로
       그린다. 관리자 입력 화면처럼 이 컨트롤이 많은 화면에서 터치 타깃
       기준(44px)에 걸리므로 여기서 올린다. */
    div[data-testid="stNumberInput"] button,
    div[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputStepUp"] {{
        min-height: 44px !important; min-width: 44px !important;
    }}
    section[data-testid="stFileUploaderDropzone"] button,
    div[data-testid="stFileUploader"] button {{
        min-height: 44px !important;
    }}

    /* 상단 브랜드|사용자 줄은 1단 전환에서 제외 — 좁아도 좌우가 맞아야
       헤더로 읽힌다. 세로로 쌓이면 사용자명이 서비스명 바로 밑에 붙는다. */
    div[class*="st-key-mjp_brandrow"] div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important; flex-wrap: nowrap !important; gap: 8px !important;
    }}
    /* 브랜드 쪽을 넓게, 사용자칩은 한 줄로 줄여 잡는다.
       균등 분할하면 390px 에서 양쪽 다 두세 줄로 접힌다. */
    div[class*="st-key-mjp_brandrow"] div[data-testid="stColumn"]:first-child {{
        width: auto !important; flex: 1 1 auto !important; min-width: 0 !important;
    }}
    div[class*="st-key-mjp_brandrow"] div[data-testid="stColumn"]:last-child {{
        width: auto !important; flex: 0 0 auto !important; min-width: 0 !important;
    }}
    .mjp-brand-name {{ white-space: nowrap; }}
    .mjp-userchip-name {{
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    /* 역할·제공자 보조 줄은 좁은 화면에서 이름의 폭만 빼앗는다.
       같은 정보는 마이페이지에 그대로 있다. */
    .mjp-userchip .mjp-muted {{ display: none; }}
    .mjp-userchip {{ max-width: 42%; }}


    /* 핵심: st.columns 다단을 1단으로 강제 전환 */
    div[data-testid="stHorizontalBlock"] {{
        flex-direction: column !important;
        gap: 0.65rem !important;
    }}
    div[data-testid="stColumn"] {{
        width: 100% !important;
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }}

    /* 히어로 타이포를 폰 폭에 맞게 축소 */
    .mjp-hero {{ padding: 26px 6px 16px; }}
    .mjp-hero-title {{ font-size:var(--mjp-display); letter-spacing: -0.03em; }}
    .mjp-hero-sub {{ font-size:var(--mjp-body); margin-top: 14px; }}
    .mjp-hero::before {{ width: 360px; height: 280px; }}

    /* 화면 제목이 폰에서 3줄로 넘치지 않게 축소 */
    .mjp-section-title {{ font-size: var(--mjp-h2); }}
    .mjp-section-sub {{ font-size: var(--mjp-caption); margin-top: 6px; }}
    /* 모바일은 세로가 귀하다 — 섹션 간격을 한 단 낮춘다 */
    .mjp-section {{ margin-top: var(--mjp-s3); }}
    hr, div[data-testid="stDivider"] {{
        margin-top: var(--mjp-s3) !important;
        margin-bottom: var(--mjp-s2) !important;
    }}
    .stMarkdown h4 {{ margin-top: var(--mjp-s2) !important; }}
    .mjp-card {{ padding: 18px 16px; }}
    .mjp-scorecard {{ padding: 18px 18px; }}
    .mjp-section-sub {{ font-size:var(--mjp-caption); }}

    .mjp-card, .mjp-feature {{ padding: 15px 15px; }}
    .mjp-feature-desc {{ min-height: 0; }}

    /* 모바일에서는 버튼을 더 크게 (엄지 터치) */
    .stButton > button,
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stDownloadButton"] button {{
        min-height: 48px !important; font-size:var(--mjp-body);
    }}

    /* 입력 컨트롤 자체의 터치 높이 확보.
       실측 결과 selectbox 는 38px, 비밀번호 입력 래퍼는 40px 이라
       44px 기준에 미달했다. 컨트롤을 키우면 안쪽 토글도 같이 커진다. */
    div[data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
        min-height: 44px !important;
    }}
    div[data-baseweb="select"] [aria-label="Open"],
    div[data-testid="stTextInputRootElement"] button {{
        min-height: 44px !important; min-width: 40px !important;
    }}

    /* --- iOS 사파리 자동 확대 방지 (측정으로 발견) ---
       입력창 폰트가 16px 미만이면 사파리가 포커스할 때 화면을 확대하고,
       그 확대가 풀리지 않아 이후 레이아웃이 어긋난 채로 남는다.
       stTextInput/stTextArea 만 막아뒀는데 실제로는 selectbox·multiselect 의
       내부 input 이 14px 이라 그대로 뚫렸다. BaseWeb 이 만드는 input 까지 덮는다. */
    div[data-testid="stSelectbox"] input,
    div[data-testid="stMultiSelect"] input,
    div[data-testid="stMultiSelectTagsContainer"] input,
    div[data-baseweb="select"] input,
    div[data-baseweb="input"] input {{
        font-size:var(--mjp-body) !important;
    }}

    /* 도움말(?) 아이콘의 탭 영역 확보 — 16px 은 손가락으로 누르기 어렵다 */
    div[data-testid="stTooltipHoverTarget"] {{
        min-width: 30px; min-height: 30px;
        display: inline-flex; align-items: center; justify-content: center;
    }}

    /* 상단 브랜드 줄바꿈 허용 */
    .mjp-topbar {{
        flex-wrap: nowrap; gap: 10px; align-items: center;
        padding: 6px 0 10px; margin-bottom: 12px;
    }}
    /* 자간 0.17em 짜리 마이크로 라벨은 390px 에서 화면 밖으로 넘친다.
       모바일에서는 브랜드명만 남긴다 — 로고 마크가 이미 정체성을 진다. */
    .mjp-brand-sub {{ display: none; }}
    .mjp-brand-mark {{ width: 30px; height: 30px; }}

    /* 컬럼이 1단으로 접히면 오른쪽 정렬 텍스트가 화면 밖으로 밀린다 → 왼쪽 정렬 */
    .mjp-userchip {{
        text-align: right; padding-top: 0; flex: none;
        max-width: 46%; overflow: hidden;
    }}
    .mjp-userchip-name {{ font-size: var(--mjp-caption); }}

    /* 인사말 옆 장식용 스티커는 폰에서 숨긴다.
       세로 공간을 200px 가까이 먹으면서 정보는 주지 않기 때문이다. */
    .st-key-mjp_hub_sticker {{ display: none !important; }}

    /* --- 예외: 상단 기능 내비게이션만 가로 유지 ---
       위의 1단 강제 규칙을 그대로 두면 메뉴 6개가 세로로 쌓여 폰 화면을
       전부 차지한다. st.container(key="mjp_navbar") 가 붙여주는
       .st-key-mjp_navbar 클래스로 이 블록만 되돌리고 가로 스크롤을 준다. */
    .st-key-mjp_navbar div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        gap: 0.4rem !important;
        padding-bottom: 4px;
    }}
    .st-key-mjp_navbar div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {{ display: none; }}
    .st-key-mjp_navbar div[data-testid="stColumn"] {{
        width: auto !important;
        min-width: 42% !important;
        flex: 0 0 auto !important;
    }}
    .st-key-mjp_navbar .stButton > button {{ font-size:var(--mjp-caption); white-space: nowrap; }}

    /* --- 예외 2: 카드 하단의 짧은 버튼 줄은 가로 유지 ---
       기업 카드마다 [♡][합격 정보][이력서] 3개가 세로로 쌓이면 카드 하나가
       화면 절반을 먹는다. 컨테이너 key 를 mjp_row_ 로 시작하게 만들고
       부분 일치 선택자로 한 번에 잡는다 (key 는 카드마다 달라야 하므로
       클래스를 공유할 수 없다). */
    div[class*="st-key-mjp_row"] div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.35rem !important;
    }}
    div[class*="st-key-mjp_row"] div[data-testid="stColumn"] {{
        width: auto !important;
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }}
    div[class*="st-key-mjp_row"] .stButton > button {{
        font-size:var(--mjp-caption); padding-left: 4px; padding-right: 4px;
        white-space: nowrap; overflow: hidden;
    }}

    /* 표/데이터프레임 가로 스크롤 허용 (레이아웃을 밀어내지 않도록) */
    div[data-testid="stDataFrame"] {{ overflow-x: auto; }}
}}

/* 아주 좁은 폰(360px 이하) 추가 보정 */
@media (max-width: 380px) {{
    .mjp-hero-title {{ font-size:var(--mjp-h1); }}
    .mjp-brand-sub {{ display: none; }}
}}
</style>
""", unsafe_allow_html=True)


def score_bar(label: str, value: float, maximum: int) -> str:
    """점수 막대 HTML. 여러 화면에서 재사용되므로 테마 모듈에 둔다."""
    pct = 0 if not maximum else min(100, value / maximum * 100)
    return f"""
    <div style="margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; font-size:var(--mjp-caption); color:{MUTED};">
        <span>{label}</span><span style="color:{TEXT}; font-weight:700;">{value} / {maximum}</span>
      </div>
      <div class="mjp-bar-track" style="margin-top:5px;">
        <div class="mjp-bar-fill" style="width:{pct:.0f}%;"></div>
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
