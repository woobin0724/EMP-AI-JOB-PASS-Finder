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

BADGE_COLORS = {"live": GREEN, "backup": GOLD, "ink": BG, "muted": MUTED}

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
    font-size: 30px; font-weight: 800; color: {TEXT}; letter-spacing: -0.03em;
    line-height: 1.22;
}}
.mjp-section-sub {{
    color: {MUTED}; font-size: 14px; margin-top: 8px; line-height: 1.6;
}}

/* ===== 1. 공통 카드 ===== */
.mjp-card {{
    background: {CARD}; border: 1px solid {CARD_BORDER}; border-radius: 14px;
    padding: 18px 20px; margin-bottom: 16px;
}}
.mjp-badge {{
    display: inline-block; font-size: 11px; font-weight: 700; padding: 3px 10px;
    border-radius: 999px; letter-spacing: 0.03em;
}}
.mjp-tag {{
    display: inline-block; font-size: 11px; padding: 2px 9px; border-radius: 6px;
    margin-right: 4px; background: {CARD_BORDER}; color: {MUTED};
}}
.mjp-muted {{ color: {MUTED}; font-size: 12.5px; }}
.mjp-star {{ color: {GOLD}; }}
.mjp-disclaimer {{
    background: rgba(52,211,153,0.08); border: 1px dashed {GREEN};
    border-radius: 10px; padding: 8px 12px; font-size: 12px;
    color: {MUTED}; margin-bottom: 14px;
}}
.mjp-interview {{
    background: {CARD}; border: 1px solid {PURPLE}; border-radius: 10px;
    padding: 12px 14px; margin-bottom: 10px;
}}
.mjp-qbadge {{ color: {PURPLE}; font-weight: 700; font-size: 12px; margin-bottom: 4px; display: block; }}
.mjp-bar-track {{ background: {CARD_BORDER}; border-radius: 999px; height: 8px; width: 100%; }}
.mjp-bar-fill {{ background: {GREEN}; border-radius: 999px; height: 8px; }}
.mjp-later {{
    background: {CARD}; border: 1px dashed {CARD_BORDER}; border-left: 4px solid {PURPLE};
    border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
}}

/* ===== 2. 랜딩 히어로 (참고 디자인: 큰 타이포 + 넉넉한 여백 + 은은한 그라데이션) ===== */
.mjp-hero {{
    position: relative; text-align: center;
    padding: 46px 20px 24px; margin-bottom: 8px;
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
    font-size: 58px; font-weight: 800; line-height: 1.08;
    letter-spacing: -0.035em; margin: 18px 0 0;
    background: linear-gradient(180deg, {TEXT} 0%, #9FB0CC 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.mjp-hero-sub {{
    font-size: 19px; color: {MUTED}; margin-top: 18px; line-height: 1.6;
    max-width: 620px; margin-left: auto; margin-right: auto;
}}
.mjp-hero-kicker {{
    display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: 0.08em;
    color: {BRAND_LIGHT}; border: 1px solid rgba(76,143,224,0.38);
    background: rgba(76,143,224,0.10);
    padding: 5px 14px; border-radius: 999px; text-transform: uppercase;
}}
/* 로고 하단 레터스페이싱을 타이포 요소로 가져온 서브라인 */
.mjp-hero-team {{
    font-size: 11.5px; font-weight: 700; color: {BRAND};
    letter-spacing: 0.14em; margin-top: 14px;
}}

/* ===== 3. 기능 카드 (메인 허브) ===== */
.mjp-feature {{
    background: linear-gradient(160deg, {CARD} 0%, {BG_SOFT} 100%);
    border: 1px solid {CARD_BORDER}; border-radius: 16px;
    padding: 22px 20px 18px; height: 100%;
    transition: border-color .18s ease, transform .18s ease;
}}
.mjp-feature:hover {{ border-color: {BRAND}; transform: translateY(-2px); }}
.mjp-feature-icon {{ font-size: 30px; line-height: 1; }}
.mjp-feature-title {{ font-size: 17px; font-weight: 800; color: {TEXT}; margin-top: 12px; }}
.mjp-feature-desc {{ font-size: 13px; color: {MUTED}; margin-top: 8px; line-height: 1.62; min-height: 62px; }}

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
.mjp-brand-name {{ font-size: 15px; font-weight: 800; color: {TEXT}; line-height: 1.2; }}
.mjp-brand-sub {{
    font-size: 10px; font-weight: 700; color: {BRAND};
    letter-spacing: 0.17em;   /* 원본 로고 하단 아크 타이포에서 가져온 자간 */
}}
.mjp-userchip {{ text-align: right; padding-top: 6px; overflow-wrap: anywhere; }}
.mjp-userchip-name {{ color: {TEXT}; font-size: 13px; font-weight: 700; }}

/* ===== 5. Streamlit 위젯 다듬기 ===== */
.stButton > button {{
    border-radius: 10px; font-weight: 700; border: 1px solid {CARD_BORDER};
    min-height: 44px;              /* 터치 타깃 최소 44px (애플 HIG 권장) */
    transition: border-color .15s ease;
}}
.stButton > button:hover {{ border-color: {BRAND}; }}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea {{
    font-size: 16px !important;    /* iOS 사파리 자동 확대(zoom) 방지 임계값 */
    min-height: 44px;
}}

/* ===== 6. 모바일 (QR 스캔 접속) ===== */
@media (max-width: {MOBILE_BREAKPOINT}px) {{
    .block-container {{ padding: 1.1rem 0.85rem 2.4rem; }}

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
    .mjp-hero-title {{ font-size: 34px; letter-spacing: -0.03em; }}
    .mjp-hero-sub {{ font-size: 15px; margin-top: 14px; }}
    .mjp-hero::before {{ width: 360px; height: 280px; }}

    /* 화면 제목이 폰에서 3줄로 넘치지 않게 축소 */
    .mjp-section-title {{ font-size: 22px; }}
    .mjp-section-sub {{ font-size: 13px; }}

    .mjp-card, .mjp-feature {{ padding: 15px 15px; }}
    .mjp-feature-desc {{ min-height: 0; }}

    /* 모바일에서는 버튼을 더 크게 (엄지 터치) */
    .stButton > button {{ min-height: 48px; font-size: 15px; }}

    /* 상단 브랜드 줄바꿈 허용 */
    .mjp-topbar {{ flex-wrap: wrap; gap: 8px; }}

    /* 컬럼이 1단으로 접히면 오른쪽 정렬 텍스트가 화면 밖으로 밀린다 → 왼쪽 정렬 */
    .mjp-userchip {{ text-align: left; padding-top: 2px; }}

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
    .st-key-mjp_navbar .stButton > button {{ font-size: 13px; white-space: nowrap; }}

    /* 표/데이터프레임 가로 스크롤 허용 (레이아웃을 밀어내지 않도록) */
    div[data-testid="stDataFrame"] {{ overflow-x: auto; }}
}}

/* 아주 좁은 폰(360px 이하) 추가 보정 */
@media (max-width: 380px) {{
    .mjp-hero-title {{ font-size: 28px; }}
    .mjp-brand-sub {{ display: none; }}
}}
</style>
""", unsafe_allow_html=True)


def score_bar(label: str, value: float, maximum: int) -> str:
    """점수 막대 HTML. 여러 화면에서 재사용되므로 테마 모듈에 둔다."""
    pct = 0 if not maximum else min(100, value / maximum * 100)
    return f"""
    <div style="margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; font-size:12px; color:{MUTED};">
        <span>{label}</span><span style="color:{TEXT}; font-weight:700;">{value} / {maximum}</span>
      </div>
      <div class="mjp-bar-track" style="margin-top:5px;">
        <div class="mjp-bar-fill" style="width:{pct:.0f}%;"></div>
      </div>
    </div>"""


def render_stars(rating: float) -> str:
    """별점 HTML."""
    full = int(rating)
    return f'<span class="mjp-star">{"★" * full}{"☆" * (5 - full)}</span> ({rating:.1f})'
