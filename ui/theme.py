# -*- coding: utf-8 -*-
"""
ui/theme.py
디자인 토큰 + 전역 CSS + 모바일 반응형 단일 관문

시각 세계 — 국가기술자격증 수첩
-------------------------------
마이스터고 학생이 가장 잘 아는 '문서'는 자격증 수첩이다. 이 앱은 학생의
스펙을 그 문서처럼 다룬다.

  · 표지    : 짙은 네이비 띠 + 금박 엠블럼 (상단 바 · 랜딩 표지)
  · 속지    : 차가운 민트그레이 보안용지 위에 흰 양식지, 1px 괘선
  · 양식    : 직각에 가까운 모서리(4px), 필드 라벨 칸, 등폭 숫자
  · 도장    : 점수·판정은 인주 도장처럼 '찍힌다' (화면당 한 번의 모션)

밝은 바탕을 고른 이유: 교실·실습실 형광등 아래에서 폰으로 보는 화면이다.
어두운 화면은 밝은 실내에서 반사광에 묻힌다.

▣ 모바일 대응이 왜 CSS 한 곳에 모여야 하는가
   심사 현장에서 학생/심사위원은 QR을 찍어 '폰'으로 접속한다. Streamlit의
   st.columns()는 좁은 화면에서 자동으로 1단이 되지 않고 가로로 짓눌리기만
   한다. 그래서 아래 @media 블록에서 Streamlit이 컬럼에 붙이는 data-testid를
   직접 잡아 1단으로 강제 전환한다.
"""

import base64
import math

import streamlit as st

# ============================================================
# 디자인 토큰 (.streamlit/config.toml 의 [theme] 값과 일치시킬 것)
# ============================================================
# 이름은 기존 화면 코드가 import 하는 그대로 두고 값만 새 세계로 바꿨다.
BG = "#EDF1EF"            # 보안용지 (앱 바탕)
BG_SOFT = "#E3E9E6"       # 한 톤 짙은 용지 (검색·필터 칸)
CARD = "#FFFFFF"          # 양식지
CARD_BORDER = "#C6D0CC"   # 괘선
TEXT = "#18212D"          # 먹
MUTED = "#55606B"         # 보조 글씨 (용지 위 5.8:1)
GREEN = "#1D7447"         # 합격 안정권 · 성공 (흰 글씨 5.9:1)
GOLD = "#8A5A00"          # 주의 · 도전권 (황토 잉크)
PURPLE = "#51438A"        # 일부인(날짜 도장) 보라 잉크
RED = "#B93A26"           # 인주 주홍 — 도장 · 경고
BLUE = "#2A5DB0"          # 정보 · 출처 표시

# ------------------------------------------------------------
# 브랜드 — 수첩 표지와 금박
# ------------------------------------------------------------
BRAND_DEEP = "#14284A"    # 표지 네이비 (상단 바 · 주 버튼)
BRAND = "#1F4E8C"         # 본문 위 브랜드 잉크 (아이콘 · 링크 · 포커스)
BRAND_LIGHT = "#C8A55E"   # 금박
COVER_TEXT = "#E8EDF5"    # 표지 위 글씨
COVER_MUTED = "#A9B6CB"   # 표지 위 보조 글씨 (네이비 위 7:1)

# ▣ 색의 역할
#   네이비 = 정체성과 행동 (표지 · 주 버튼 · 선택된 탭)
#   그린   = 상태 시맨틱 전용 (LIVE 배지 · 합격 안정권)
#   주홍   = 도장 (판정 · 낮은 점수 · 오류)
BADGE_COLORS = {"live": GREEN, "backup": GOLD, "curated": MUTED,
                "ink": CARD, "muted": MUTED}

# 브랜드 제공자별 색 (로그인 버튼)
PROVIDER_COLORS = {
    "kakao": "#FEE500",
    "naver": "#03C75A",
    "google": "#FFFFFF",
    "guest": CARD,
}

# 모바일 기준 폭 — 이 값 아래에서 모든 다단 레이아웃이 1단으로 접힌다.
MOBILE_BREAKPOINT = 768


def _guilloche_svg(color: str, opacity: float) -> str:
    """
    표지에 까는 보안 인쇄 무늬(길로셰).

    자격증·지폐의 위조 방지 곡선이다. 사인파 여러 가닥을 위상만 달리해
    겹치면 그 특유의 그물 무늬가 나온다. 타일 경계가 이어지도록 주기를
    타일 폭에 맞췄다.
    """
    width, height = 240, 60
    paths = []
    for k in range(6):
        phase = k * math.pi / 3
        amp = 10 + 4 * math.sin(k)
        points = []
        for x in range(0, width + 1, 6):
            y = height / 2 + amp * math.sin(2 * math.pi * x / width * 2 + phase)
            points.append(f"{x},{y:.1f}")
        paths.append(f'<polyline points="{" ".join(points)}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><g fill="none" stroke="{color}" '
        f'stroke-width="0.8" opacity="{opacity}">{"".join(paths)}</g></svg>'
    )


def _b64(svg: str) -> str:
    # utf8 data URI 는 SVG 안의 '#' 색상값이 URL 프래그먼트로 잘린다 → base64
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")


def inject_css() -> None:
    """전역 스타일을 주입한다. app.py 부팅 시 단 한 번만 호출한다."""
    guilloche = _b64(_guilloche_svg(BRAND_LIGHT, 0.55))

    st.markdown(f"""
<style>
/* 본문 Pretendard (jsdelivr) + 폴백 Noto Sans KR, 제목 나눔명조.
   학교·기관망이 jsdelivr 을 막는 경우를 대비해 폴백도 웹폰트로 둔다.
   명조는 자격증·공문서 제목의 서체다. 로드되지 않으면 기기 명조로 내려간다. */
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css");
@import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&family=Nanum+Myeongjo:wght@700;800&family=Noto+Serif+KR:wght@700;800&display=swap");

:root {{
    --mjp-font: "Pretendard Variable", Pretendard, "Noto Sans KR", -apple-system,
                BlinkMacSystemFont, system-ui, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    --mjp-serif: "Nanum Myeongjo", "Noto Serif KR", "AppleMyungjo", "Batang", serif;
    --mjp-mono: ui-monospace, "SF Mono", "Roboto Mono", Menlo, Consolas, monospace;

    /* 타이포 6단 — 이 여섯 개 밖의 크기를 새로 만들지 않는다 */
    --mjp-display: 34px;
    --mjp-h1: 26px;
    --mjp-h2: 20px;
    --mjp-body: 16px;
    --mjp-small: 14px;
    --mjp-caption: 13px;

    /* 여백 4단 */
    --mjp-s1: 8px;
    --mjp-s2: 16px;
    --mjp-s3: 32px;
    --mjp-s4: 56px;

    /* 종이는 뜨지 않는다 — 그림자는 양식지가 바닥에 놓인 정도로만 */
    --mjp-shadow-1: 0 1px 0 rgba(20,40,74,0.06);
    --mjp-shadow-2: 0 2px 6px rgba(20,40,74,0.10), 0 1px 0 rgba(20,40,74,0.06);

    --mjp-ease: 160ms cubic-bezier(0.16, 1, 0.3, 1);
    --mjp-radius: 4px;

    --mjp-paper: {BG};
    --mjp-sheet: {CARD};
    --mjp-rule: {CARD_BORDER};
    --mjp-ink: {TEXT};
    --mjp-muted: {MUTED};
    --mjp-cover: {BRAND_DEEP};
    --mjp-foil: {BRAND_LIGHT};
}}

/* 폰트를 앱 전체와 Streamlit 위젯 내부까지 적용한다.
   Streamlit 은 body 에 직접 "Source Sans" 를 지정하므로 html/body 를 함께 잡는다. */
html, body, .stApp, .stApp *,
input, textarea, select, button, [class^="st-"], [class*=" st-"] {{
    font-family: var(--mjp-font) !important;
}}
/* 전역 폰트 규칙에서 되돌려야 하는 것들 — 아이콘 리거처 폰트, 코드, 수식 */
[data-testid="stIconMaterial"],
.material-icons, .material-icons-outlined,
.material-symbols-rounded, .material-symbols-outlined {{
    font-family: "Material Symbols Rounded", "Material Icons" !important;
}}
code, pre, kbd, samp, .stCode, [data-testid="stCode"] *, .mjp-serial {{
    font-family: var(--mjp-mono) !important;
}}
.katex, .katex * {{ font-family: KaTeX_Main, "Times New Roman", serif !important; }}
/* h1 에는 Streamlit 제목 규칙이 더 높은 우선순위로 붙으므로 .stApp 을 앞에 둔다 */
.stApp .mjp-serif, .stApp .mjp-section-title, .stApp h1.mjp-hero-title,
.stApp h1.mjp-cover-title, .stApp .mjp-cover-title, .stApp .mjp-scorecard-name {{
    font-family: var(--mjp-serif) !important;
}}

/* ===== 0. 바탕 · 브라우저 기본 표면 ===== */
.stApp {{ background: {BG}; color: {TEXT}; font-size: var(--mjp-body); }}
/* 한글은 어절 단위로 줄바꿈 — '알려드립니/다' 처럼 낱글자로 끊기지 않게 */
.stApp, .stMarkdown, .stMarkdown *, div[data-testid="stCaptionContainer"] *,
div[data-testid="stAlert"] * {{ word-break: keep-all !important; overflow-wrap: break-word; }}
h1, h2, h3, h4, h5 {{ color: {TEXT}; letter-spacing: -0.02em; }}
::selection {{ background: rgba(200,165,94,0.38); color: {TEXT}; }}
input, textarea {{ caret-color: {BRAND_DEEP}; }}
a {{ color: {BRAND}; text-underline-offset: 3px; text-decoration-thickness: 1px; }}
* {{ scrollbar-width: thin; scrollbar-color: {CARD_BORDER} transparent; }}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-thumb {{ background: {CARD_BORDER}; border-radius: 10px;
                             border: 2px solid {BG}; }}
/* 숫자는 전부 등폭 — 점수·코드·통계가 자리마다 흔들리지 않는다 */
.stApp {{ font-variant-numeric: tabular-nums; }}

.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1120px; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent !important; height: 2.2rem; }}
header[data-testid="stHeader"] * {{ color: {MUTED} !important; }}
div[data-testid="stToolbar"] {{ right: 0.4rem; }}

/* ===== 1. 화면 제목 — 공문서 제목처럼 명조 + 겹괘선 ===== */
.mjp-titleblock {{
    margin: 6px 0 var(--mjp-s3); padding-bottom: 14px;
    border-bottom: 3px double {TEXT};
}}
.mjp-section-title {{
    font-size: var(--mjp-h1); font-weight: 800; color: {TEXT};
    letter-spacing: -0.01em; line-height: 1.3; text-wrap: balance;
}}
.mjp-section-sub {{
    color: {MUTED}; font-size: var(--mjp-small);
    margin-top: var(--mjp-s1); line-height: 1.7; max-width: 66ch;
}}
.mjp-section {{ margin-top: var(--mjp-s4); }}
hr, div[data-testid="stDivider"] {{
    margin-top: var(--mjp-s4) !important;
    margin-bottom: var(--mjp-s3) !important;
    border-color: {CARD_BORDER};
}}
/* 마크다운 소제목 = 양식의 구획 제목. 아래로 괘선 한 줄. */
.stMarkdown h1 {{ font-size: var(--mjp-h1) !important; }}
.stMarkdown h2 {{ font-size: var(--mjp-h1) !important; }}
.stMarkdown h3, .stMarkdown h4 {{
    font-size: var(--mjp-h2) !important; font-weight: 800; color: {TEXT};
    margin-top: var(--mjp-s3) !important; margin-bottom: var(--mjp-s2) !important;
    padding-bottom: 8px !important; border-bottom: 1px solid {CARD_BORDER};
    letter-spacing: -0.02em;
}}
.stMarkdown p, .stMarkdown li {{ font-size: var(--mjp-body); line-height: 1.7; }}
div[data-testid="stCaptionContainer"], .stCaption, small {{
    font-size: var(--mjp-caption) !important; line-height: 1.6; color: {MUTED};
}}
/* Streamlit 캡션은 글자색에 투명도를 걸어 용지 위 대비가 3:1 로 떨어진다 */
div[data-testid="stCaptionContainer"] p, div[data-testid="stCaptionContainer"] {{
    color: {MUTED} !important; opacity: 1 !important;
}}

/* ===== 2. 양식지 (공통 카드) ===== */
.mjp-card {{
    background: {CARD}; border: 1px solid {CARD_BORDER};
    border-radius: var(--mjp-radius);
    padding: 20px 22px; margin-bottom: var(--mjp-s2);
    box-shadow: var(--mjp-shadow-1);
    transition: border-color var(--mjp-ease), box-shadow var(--mjp-ease);
}}
.mjp-card:hover {{ border-color: #9FB0BE; box-shadow: var(--mjp-shadow-2); }}
/* 배지 = 고무 스탬프. 둥근 알약이 아니라 직각 도장 테두리. */
.mjp-badge {{
    display: inline-block; font-size: var(--mjp-caption); font-weight: 800;
    padding: 3px 9px; border-radius: 3px; letter-spacing: 0.02em;
    line-height: 1.45; vertical-align: 1px;
}}
.mjp-tag {{
    display: inline-block; font-size: var(--mjp-caption); padding: 2px 8px;
    border-radius: 3px; margin-right: 4px; background: {BG};
    border: 1px solid {CARD_BORDER}; color: {MUTED};
}}
.mjp-muted {{ color: {MUTED}; font-size: var(--mjp-small); line-height: 1.65; }}
.mjp-star {{ color: {GOLD}; }}
.mjp-serial {{ letter-spacing: 0.12em; font-weight: 700; }}
/* 비고란 — 예시 데이터·면책 문구 */
.mjp-disclaimer {{
    background: {BG}; border: 1px dashed {CARD_BORDER};
    border-radius: var(--mjp-radius); padding: 8px 12px; font-size: var(--mjp-caption);
    color: {MUTED}; margin-bottom: 14px;
}}
.mjp-disclaimer::before {{ content: "비고 "; font-weight: 800; color: {TEXT}; }}
.mjp-interview {{
    background: {CARD}; border: 1px solid {CARD_BORDER}; border-radius: var(--mjp-radius);
    padding: 12px 14px; margin-bottom: 10px;
}}
.mjp-qno {{ color: {PURPLE}; margin-right: 4px; }}
@media (min-width: {MOBILE_BREAKPOINT + 1}px) {{
    /* 한 줄의 기업 카드 높이를 맞춰 아래 버튼 줄이 같은 높이에 선다 */
    .mjp-company {{ min-height: 272px; }}
}}
.mjp-qbadge {{ color: {PURPLE}; font-weight: 800; font-size: var(--mjp-caption); margin-bottom: 4px; display: block; }}

/* 검색·필터 칸 — 양식 상단의 '조건 기입란' */
.mjp-btn-align {{ height: 28px; }}
div[class*="st-key-mjp_searchbar"], div[class*="st-key-mjp_filterbar"] {{
    background: {BG_SOFT}; border: 1px solid {CARD_BORDER};
    border-radius: var(--mjp-radius); padding: 16px 18px 6px;
    margin-bottom: var(--mjp-s2);
}}

/* ===== 3. 진단서 — 점수 도장 ===== */
.mjp-scorecard {{
    background: {CARD}; border: 1px solid {CARD_BORDER};
    border-top: 6px solid {BRAND_DEEP};
    border-radius: var(--mjp-radius);
    padding: 0; margin-bottom: var(--mjp-s2); overflow: hidden;
}}
.mjp-scorecard-head {{
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 12px; flex-wrap: wrap;
    padding: 12px 20px; border-bottom: 1px solid {CARD_BORDER}; background: {BG};
}}
.mjp-scorecard-name {{ font-family: var(--mjp-serif) !important; font-size: var(--mjp-h2);
                       font-weight: 800; color: {TEXT}; letter-spacing: 0.04em; }}
.mjp-scorecard-row {{
    display: flex; align-items: center; gap: 28px;
    padding: 20px 24px; flex-wrap: wrap;
}}
/* 도장: 겹테두리 원 + 약간 기운 각도 + 잉크 곱하기 합성.
   색은 판정에 따라 인라인으로 준다 (--seal). */
.mjp-scorering {{
    --seal: {RED};
    width: 124px; height: 124px; border-radius: 50%; flex: none;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    color: var(--seal) !important; background: transparent !important;
    border: 3px solid var(--seal);
    box-shadow: inset 0 0 0 3px {CARD}, inset 0 0 0 4.5px var(--seal);
    transform: rotate(-7deg);
    mix-blend-mode: multiply;
    animation: mjp-stamp 560ms cubic-bezier(0.16, 1, 0.3, 1) both;
}}
.mjp-scorering-num {{ font-size: 42px; font-weight: 900; line-height: 1;
                      letter-spacing: -0.03em; }}
.mjp-scorering-cap {{ font-size: var(--mjp-caption); font-weight: 800; margin-top: 4px;
                      letter-spacing: 0.08em; }}
.mjp-verdict {{ font-size: var(--mjp-h2); font-weight: 800; letter-spacing: -0.02em; }}
/* 도장이 '찍히는' 한 번의 모션 — 이 앱의 유일한 연출.
   이미 보이는 상태(불투명도 0.4)에서 출발해 압착되듯 내려앉는다. */
@keyframes mjp-stamp {{
    0%   {{ transform: scale(1.22) rotate(-13deg); opacity: 0.4; filter: blur(1.5px); }}
    55%  {{ transform: scale(0.97) rotate(-6deg);  opacity: 1;   filter: blur(0); }}
    100% {{ transform: scale(1) rotate(-7deg);     opacity: 1; }}
}}
@media (prefers-reduced-motion: reduce) {{
    .mjp-scorering, .mjp-seal {{ animation: none !important; }}
}}

/* 점수 막대 = 눈금자. 10% 마다 눈금. */
.mjp-bar-track {{
    background:
        repeating-linear-gradient(90deg, transparent 0, transparent calc(10% - 1px),
                                  {CARD_BORDER} calc(10% - 1px), {CARD_BORDER} 10%),
        {BG};
    border: 1px solid {CARD_BORDER}; border-radius: 2px; height: 10px; width: 100%;
}}
.mjp-bar-fill {{ background: {BRAND_DEEP}; border-radius: 1px; height: 8px; }}
.mjp-later {{
    background: {CARD}; border: 1px dashed {CARD_BORDER};
    border-radius: var(--mjp-radius); padding: 16px 18px; margin-bottom: 14px;
}}

/* ===== 4. 표지 (랜딩) ===== */
.mjp-cover {{
    position: relative; overflow: hidden;
    background: {BRAND_DEEP}; color: {COVER_TEXT};
    border-radius: var(--mjp-radius);
    padding: 72px 28px 80px; text-align: center;
    box-shadow: inset 0 0 0 1px rgba(200,165,94,0.35), inset 0 0 0 7px {BRAND_DEEP},
                inset 0 0 0 8px rgba(200,165,94,0.55);
}}
/* 길로셰 보안 무늬 — 표지 위아래 띠에만 */
.mjp-cover::before, .mjp-cover::after {{
    content: ""; position: absolute; left: 8px; right: 8px; height: 60px;
    background-image: url("data:image/svg+xml;base64,{guilloche}");
    background-size: 240px 60px; opacity: 0.5; pointer-events: none;
}}
.mjp-cover::before {{ top: 8px; }}
.mjp-cover::after {{ bottom: 8px; transform: scaleY(-1); }}
.mjp-cover > * {{ position: relative; z-index: 1; }}
.mjp-cover-issuer {{
    font-size: var(--mjp-small); font-weight: 700; color: {COVER_MUTED};
    letter-spacing: 0.12em; margin-top: 22px;
}}
.mjp-hero-title, .mjp-cover-title {{
    font-size: clamp(34px, 5.2vw, 54px); font-weight: 800; line-height: 1.15;
    letter-spacing: 0.02em; margin: 10px 0 0 !important; padding: 0 !important;
    color: {BRAND_LIGHT} !important; text-wrap: balance;
}}
.mjp-hero-sub, .mjp-cover-sub {{
    font-size: var(--mjp-body) !important; color: {COVER_TEXT}; margin: 18px auto 0 !important;
    line-height: 1.75; max-width: 34em; text-wrap: balance;
}}
.mjp-hero-sub b, .mjp-cover-sub b {{ color: #FFFFFF; }}
/* 대회 본선 진출 — 표지 모서리의 원형 인장 */
.mjp-seal {{
    position: absolute; top: 26px; right: 26px; z-index: 2;
    width: 92px; height: 92px; border-radius: 50%;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    color: #E86A52; border: 2.5px solid #E86A52;
    box-shadow: inset 0 0 0 3px {BRAND_DEEP}, inset 0 0 0 4px #E86A52;
    font-size: 11px; font-weight: 800; line-height: 1.3; text-align: center;
    transform: rotate(12deg);
    animation: mjp-seal-in 620ms 180ms cubic-bezier(0.16, 1, 0.3, 1) both;
}}
.mjp-seal b {{ font-size: 16px; letter-spacing: 0.06em; }}
@keyframes mjp-seal-in {{
    0%   {{ transform: scale(1.25) rotate(20deg); opacity: 0.35; }}
    100% {{ transform: scale(1) rotate(12deg); opacity: 1; }}
}}

/* 양식 표 — 항목 | 내용 괘선 표 (랜딩 가치 제안, 역할 선택 등) */
.mjp-form {{
    background: {CARD}; border: 1px solid {TEXT}; border-radius: 2px;
    margin: var(--mjp-s3) 0 var(--mjp-s2);
}}
.mjp-form-row {{
    display: grid; grid-template-columns: 180px 1fr; border-top: 1px solid {CARD_BORDER};
}}
.mjp-form-row:first-child {{ border-top: none; }}
.mjp-form-key {{
    background: {BG}; border-right: 1px solid {CARD_BORDER};
    padding: 16px 18px; font-weight: 800; color: {TEXT}; font-size: var(--mjp-small);
    display: flex; align-items: flex-start; gap: 10px; line-height: 1.5;
}}
.mjp-form-val {{ padding: 16px 20px; color: {MUTED}; font-size: var(--mjp-small); line-height: 1.7; }}
.mjp-form-val b {{ color: {TEXT}; }}

/* ===== 5. 허브 — 공정 순서표 ===== */
.mjp-step {{
    display: flex; gap: 18px; align-items: flex-start;
    padding: 18px 0 6px;
}}
.mjp-step-no {{
    flex: none; width: 40px; height: 40px; border-radius: 50%;
    border: 1.5px solid {BRAND_DEEP}; color: {BRAND_DEEP};
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: var(--mjp-body);
}}
.mjp-step-title {{ font-size: var(--mjp-h2); font-weight: 800; color: {TEXT}; letter-spacing: -0.02em;
                   display: flex; align-items: center; gap: 8px; }}
.mjp-step-desc {{ font-size: var(--mjp-small); color: {MUTED}; margin-top: 6px; line-height: 1.65; max-width: 60ch; }}
div[class*="st-key-mjp_steps"] {{
    background: {CARD}; border: 1px solid {CARD_BORDER}; border-radius: var(--mjp-radius);
    padding: 4px 22px 10px;
}}
div[class*="st-key-mjp_step_"] {{ border-top: 1px solid {CARD_BORDER}; padding-bottom: 14px; }}
div[class*="st-key-mjp_step_first"] {{ border-top: none; }}

/* 기존 기능 카드 (역할 선택 등에서 사용) — 양식지 한 장 */
.mjp-feature {{
    background: {CARD}; border: 1px solid {CARD_BORDER}; border-radius: var(--mjp-radius);
    padding: 22px 22px 18px; height: 100%;
    transition: border-color var(--mjp-ease), box-shadow var(--mjp-ease);
}}
.mjp-feature:hover {{ border-color: {BRAND_DEEP}; box-shadow: var(--mjp-shadow-2); }}
.mjp-feature-icon {{ font-size: var(--mjp-h1); line-height: 1; }}
.mjp-feature-title {{ font-size: var(--mjp-h2); font-weight: 800; color: {TEXT}; margin-top: 12px; letter-spacing: -0.02em; }}
.mjp-feature-desc {{ font-size: var(--mjp-small); color: {MUTED}; margin-top: var(--mjp-s1); line-height: 1.65; }}

/* ===== 6. 상단 표지 띠 + 목차 탭 ===== */
.mjp-topbar {{
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    background: {BRAND_DEEP}; color: {COVER_TEXT};
    border-radius: var(--mjp-radius) var(--mjp-radius) 0 0;
    padding: 12px 18px; margin-bottom: 0;
    box-shadow: inset 0 -3px 0 {BRAND_LIGHT};
}}
.mjp-brand {{ display: flex; align-items: center; gap: 12px; min-width: 0; }}
.mjp-brand-mark {{ width: 38px; height: 38px; flex: none;
                   display: flex; align-items: center; justify-content: center; }}
.mjp-brand-mark svg {{ width: 100%; height: 100%; display: block; }}
.mjp-brand-name {{ font-size: var(--mjp-body); font-weight: 800; color: #FFFFFF; line-height: 1.25;
                   white-space: nowrap; }}
.mjp-brand-sub {{ font-size: 11px; font-weight: 700; color: {BRAND_LIGHT}; letter-spacing: 0.17em;
                  white-space: nowrap; }}
.mjp-userchip {{ text-align: right; min-width: 0; }}
.mjp-userchip-name {{ color: #FFFFFF; font-size: var(--mjp-small); font-weight: 800;
                      white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.mjp-userchip-meta {{ color: {COVER_MUTED}; font-size: var(--mjp-caption); white-space: nowrap; }}

/* 목차 탭: 버튼을 수첩 색인 탭처럼. 선택된 탭만 표지색으로 채운다. */
div.st-key-mjp_navbar {{
    border-bottom: 2px solid {BRAND_DEEP}; margin-bottom: var(--mjp-s3);
    background: {BG_SOFT}; padding: 8px 8px 0; border-left: 1px solid {CARD_BORDER};
    border-right: 1px solid {CARD_BORDER};
}}
div.st-key-mjp_navbar div[data-testid="stHorizontalBlock"] {{ gap: 4px !important; }}
div.st-key-mjp_navbar div[data-testid="stButton"] button {{
    border-radius: 3px 3px 0 0 !important; min-height: 44px;
    border: 1px solid {CARD_BORDER} !important; border-bottom: none !important;
    background: {CARD}; color: {TEXT}; box-shadow: none !important;
    transform: none !important; font-weight: 700;
}}
div.st-key-mjp_navbar div[data-testid="stButton"] button:hover {{ color: {BRAND}; background: #F7F9F8; }}
div.st-key-mjp_navbar div[data-testid="stButton"] button[kind="primary"] {{
    background: {BRAND_DEEP} !important; color: #FFFFFF !important;
    border-color: {BRAND_DEEP} !important;
}}

/* ===== 로고 ===== */
.mjp-logo {{ height: auto; max-width: 100%; display: block; margin: 0 auto; }}
.mjp-logo-svg svg {{ width: 100%; height: 100%; display: block; }}

/* ===== 7. Streamlit 위젯 — 양식 컨트롤 ===== */
.stButton > button,
div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stLinkButton"] a {{
    border-radius: var(--mjp-radius); font-weight: 800;
    border: 1px solid {BRAND_DEEP}; color: {BRAND_DEEP}; background: {CARD};
    min-height: 44px;              /* 터치 타깃 최소 44px */
    font-size: var(--mjp-small);
    box-shadow: 0 1px 0 rgba(20,40,74,0.10);
    transition: background-color var(--mjp-ease), color var(--mjp-ease),
                box-shadow var(--mjp-ease), transform var(--mjp-ease);
}}
.stButton > button:hover,
div[data-testid="stButton"] button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover {{
    background: #F2F5F8; color: {BRAND_DEEP}; border-color: {BRAND_DEEP};
}}
/* 주 버튼 = 표지색. 누르면 도장처럼 1px 눌린다. */
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
div[data-testid="stFormSubmitButton"] button[kind="primary"] {{
    background: {BRAND_DEEP}; color: #FFFFFF; border-color: {BRAND_DEEP};
    box-shadow: 0 2px 0 #0A1830;
}}
div[data-testid="stButton"] button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover {{
    background: #1C3663; color: #FFFFFF;
}}
.stButton > button:active,
div[data-testid="stButton"] button:active,
div[data-testid="stFormSubmitButton"] button:active {{
    transform: translateY(1px); box-shadow: none;
}}
/* 뒤로가기 — 주 동선이 아니므로 테두리 없는 링크 버튼 */
div[class*="st-key-back_hub"] button {{
    border: none !important; background: transparent !important; box-shadow: none !important;
    color: {BRAND} !important; padding-left: 0 !important; font-weight: 700;
}}
div[class*="st-key-back_hub"] button:hover {{ text-decoration: underline; text-underline-offset: 3px; }}
button:disabled, button[disabled] {{
    background: {BG} !important; color: #8C959E !important;
    border-color: {CARD_BORDER} !important; box-shadow: none !important;
}}
.stButton > button:focus-visible,
div[data-testid="stButton"] button:focus-visible,
a:focus-visible {{
    outline: 2px solid {BRAND}; outline-offset: 2px;
}}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea {{
    font-size: var(--mjp-body) !important;    /* iOS 사파리 자동 확대 방지 임계값 */
    min-height: 44px; color: {TEXT};
}}
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stNumberInput"] div[data-baseweb="input"],
div[data-testid="stTextArea"] div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {{
    border-radius: var(--mjp-radius); background: {CARD};
    border-color: {CARD_BORDER};
    transition: border-color var(--mjp-ease), box-shadow var(--mjp-ease);
}}
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
div[data-baseweb="select"] > div:focus-within {{
    border-color: {BRAND_DEEP} !important;
    box-shadow: 0 0 0 3px rgba(31,78,140,0.16);
}}
input::placeholder, textarea::placeholder {{ color: #6B7580 !important; opacity: 1; }}
/* 선택된 칩 — 양식에 기입한 값처럼 */
span[data-baseweb="tag"] {{
    background: {BRAND_DEEP} !important; border-radius: 3px !important;
}}
span[data-baseweb="tag"] span {{ color: #FFFFFF !important; }}
div[data-testid="stWidgetLabel"] label, label[data-testid="stWidgetLabel"] {{
    font-size: var(--mjp-small) !important; font-weight: 700; color: {TEXT};
}}
/* 접이식 구획 — 양식지 한 장 */
div[data-testid="stExpander"] details {{
    background: {CARD}; border: 1px solid {CARD_BORDER} !important;
    border-radius: var(--mjp-radius) !important;
}}
div[data-testid="stExpander"] summary {{ font-weight: 700; }}
div[data-testid="stExpander"] summary:hover {{ color: {BRAND}; }}
/* 탭 — 색인. 선택된 탭만 표지색으로 채운다. */
div[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 2px solid {BRAND_DEEP}; gap: 4px;
}}
div[data-testid="stTabs"] [role="tab"] {{
    font-weight: 800; padding: 10px 16px !important; min-height: 44px;
    border-radius: 3px 3px 0 0; border: 1px solid {CARD_BORDER}; border-bottom: none;
    background: {CARD};
}}
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: {BRAND_DEEP}; border-color: {BRAND_DEEP};
}}
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] p,
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{ color: #FFFFFF !important; }}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {{ display: none !important; }}
/* 안내 상자 */
div[data-testid="stAlert"] {{ border-radius: var(--mjp-radius); }}
/* 안내(info)는 양식의 기입 칸처럼 — 흰 칸 + 괘선. 경고·오류는 의미색을 유지한다. */
div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) > div {{
    background: {CARD} !important; border: 1px solid {CARD_BORDER};
    border-radius: var(--mjp-radius); color: {TEXT} !important;
}}
div[data-testid="stAlertContentInfo"], div[data-testid="stAlertContentInfo"] * {{ color: {TEXT} !important; }}
div[data-testid="stAlertContentInfo"] svg, div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) [data-testid="stIconMaterial"] {{
    color: {BRAND} !important;
}}
div[data-testid="stMetricValue"] {{ font-weight: 900; color: {TEXT}; }}

/* ===== 8. 모바일 (QR 스캔 접속) ===== */
@media (max-width: {MOBILE_BREAKPOINT}px) {{
    .block-container {{ padding: 1.1rem 0.85rem 2.4rem; }}

    div[data-testid="stNumberInput"] button,
    div[data-testid="stNumberInputStepDown"],
    div[data-testid="stNumberInputStepUp"] {{
        min-height: 44px !important; min-width: 44px !important;
    }}
    section[data-testid="stFileUploaderDropzone"] button,
    div[data-testid="stFileUploader"] button {{ min-height: 44px !important; }}

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

    /* 표지 */
    .mjp-cover {{ padding: 64px 18px 72px; }}
    .mjp-cover-title, .mjp-hero-title {{ font-size: var(--mjp-display); }}
    .mjp-cover-sub, .mjp-hero-sub {{ font-size: var(--mjp-small); }}
    .mjp-seal {{ width: 78px; height: 78px; top: 14px; right: 12px; font-size: var(--mjp-caption);
                 line-height: 1.15; }}
    .mjp-seal span {{ font-size: 11px; }}
    .mjp-seal b {{ font-size: 14px; }}
    /* 탭이 4개 이상이면 390px 에서 넘친다 — 탭 폭을 줄이고 가로 스크롤 */
    div[data-testid="stTabs"] [role="tablist"] {{ overflow-x: auto; scrollbar-width: none; }}
    div[data-testid="stTabs"] [role="tab"] {{ padding: 10px 11px !important; white-space: nowrap; }}
    .mjp-form-row {{ grid-template-columns: 1fr; }}
    .mjp-form-key {{ border-right: none; border-bottom: 1px solid {CARD_BORDER}; padding: 12px 14px; }}
    .mjp-form-val {{ padding: 12px 14px; }}

    .mjp-section-title {{ font-size: var(--mjp-h2); }}
    .mjp-section-sub {{ font-size: var(--mjp-caption); margin-top: 6px; }}
    .mjp-titleblock {{ margin-bottom: var(--mjp-s2); padding-bottom: 10px; }}
    .mjp-section {{ margin-top: var(--mjp-s3); }}
    hr, div[data-testid="stDivider"] {{
        margin-top: var(--mjp-s3) !important;
        margin-bottom: var(--mjp-s2) !important;
    }}
    .stMarkdown h3, .stMarkdown h4 {{ margin-top: var(--mjp-s2) !important; }}
    .mjp-card, .mjp-feature {{ padding: 15px 15px; }}
    .mjp-scorecard-row {{ padding: 16px; gap: 18px; }}
    .mjp-scorering {{ width: 104px; height: 104px; }}
    .mjp-scorering-num {{ font-size: var(--mjp-display); }}
    div[class*="st-key-mjp_steps"] {{ padding: 2px 14px 8px; }}
    .mjp-step {{ gap: 12px; }}
    .mjp-step-no {{ width: 34px; height: 34px; }}

    .stButton > button,
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stDownloadButton"] button {{
        min-height: 48px !important; font-size: var(--mjp-body);
    }}

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
    /* iOS 사파리 자동 확대 방지 — BaseWeb 내부 input 까지 16px */
    div[data-testid="stSelectbox"] input,
    div[data-testid="stMultiSelect"] input,
    div[data-testid="stMultiSelectTagsContainer"] input,
    div[data-baseweb="select"] input,
    div[data-baseweb="input"] input {{
        font-size: var(--mjp-body) !important;
    }}
    div[data-testid="stTooltipHoverTarget"] {{
        min-width: 30px; min-height: 30px;
        display: inline-flex; align-items: center; justify-content: center;
    }}

    /* 상단 표지 띠 — 로고 마크가 정체성을 지므로 영문 서브라인은 뺀다 */
    .mjp-topbar {{ padding: 10px 12px; }}
    .mjp-brand-sub {{ display: none; }}
    .mjp-brand-mark {{ width: 32px; height: 32px; }}
    .mjp-brand-name {{ font-size: var(--mjp-small); }}
    .mjp-userchip {{ max-width: 44%; }}
    .mjp-userchip-meta {{ display: none; }}

    .st-key-mjp_hub_sticker {{ display: none !important; }}

    /* 예외: 목차 탭은 가로 스크롤 유지 */
    .st-key-mjp_navbar {{ margin-bottom: var(--mjp-s2) !important; }}
    .st-key-mjp_navbar div[data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        gap: 4px !important;
    }}
    .st-key-mjp_navbar div[data-testid="stHorizontalBlock"]::-webkit-scrollbar {{ display: none; }}
    .st-key-mjp_navbar div[data-testid="stColumn"] {{
        width: auto !important;
        min-width: 30% !important;
        flex: 0 0 auto !important;
    }}
    .st-key-mjp_navbar .stButton > button {{
        font-size: var(--mjp-caption) !important; white-space: nowrap; min-height: 44px !important;
    }}

    /* 예외 2: 카드 하단의 짧은 버튼 줄은 가로 유지 */
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
        font-size: var(--mjp-caption); padding-left: 4px; padding-right: 4px;
        white-space: nowrap; overflow: hidden;
    }}

    div[data-testid="stDataFrame"] {{ overflow-x: auto; }}
}}

@media (max-width: 380px) {{
    .mjp-cover-title, .mjp-hero-title {{ font-size: var(--mjp-h1); }}
}}
</style>
""", unsafe_allow_html=True)


def score_bar(label: str, value: float, maximum: int) -> str:
    """점수 막대 HTML — 눈금자 형태. 여러 화면에서 재사용되므로 테마 모듈에 둔다."""
    pct = 0 if not maximum else min(100, value / maximum * 100)
    return f"""
    <div style="margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; font-size:var(--mjp-caption); color:{MUTED};">
        <span style="font-weight:700;">{label}</span><span style="color:{TEXT}; font-weight:800;">{value} / {maximum}</span>
      </div>
      <div class="mjp-bar-track" style="margin-top:5px;">
        <div class="mjp-bar-fill" style="width:{pct:.0f}%;"></div>
      </div>
    </div>"""


def render_stars(rating: float) -> str:
    """
    별점 HTML.

    ★☆ 문자 대신 SVG 로 그린다. 문자 별은 폰트에 따라 굵기·크기가 달라지고
    안드로이드 일부 기기에서는 이모지 폰트로 렌더링된다.
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
