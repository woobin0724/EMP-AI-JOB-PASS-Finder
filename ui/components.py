# -*- coding: utf-8 -*-
"""
ui/components.py
여러 화면이 공유하는 렌더링 조각 (스티커 · 상단 내비 · 설정 패널)
"""

import streamlit as st

from core import session as ss
from services import fallback as fb
from ui.brand import SERVICE_NAME, TEAM_FULL
from ui.emblem import emblem_svg
from ui.icons import icon
from ui.theme import BG, CARD_BORDER, GREEN


# ------------------------------------------------------------
# HTML 마크업
# ------------------------------------------------------------
def render_html(markup: str) -> None:
    """
    스타일이 들어간 HTML 조각을 마크다운 해석에 걸리지 않게 렌더링한다.

    st.markdown 은 문자열에 textwrap.dedent 를 걸고 CommonMark 로 파싱한다.
    이때 두 가지가 HTML 을 망가뜨린다.

    1. 빈 줄: CommonMark 에서 빈 줄은 HTML 블록을 닫는다. f-string 안의
       조건부 보간이 빈 문자열이 되면 (`{icon(...) if 찜 else ""}`) 그 줄이
       통째로 빈 줄이 되어 블록이 거기서 끊긴다.
    2. 4칸 이상 들여쓰기: 블록이 끊긴 뒤의 줄들은 들여쓰기 코드블록으로
       파싱돼 태그가 화면에 글자 그대로 찍힌다.

    줄 단위로 공백을 털고 빈 줄을 버려 한 줄로 만들면 두 조건이 모두 사라진다.
    태그 사이 공백은 HTML 에서 의미가 없으므로 결과는 동일하다.
    """
    st.markdown(
        " ".join(line.strip() for line in markup.splitlines() if line.strip()),
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# OGQ 스티커
# ------------------------------------------------------------
def show_sticker(key: str, width: int = 130, caption: str | None = None) -> None:
    """
    [하위 호환] 예전 스티커 호출부를 마스코트로 넘긴다.

    Phase 4 에서 감정 표현은 ui/mascot.py 로 일원화됐다. 이 함수는 남아 있는
    호출부가 깨지지 않도록 두되, 실제 렌더링은 마스코트가 담당한다.
    이모지 폴백은 없앴다 — 이모지를 걷어내는 것이 이번 작업의 목표이고,
    깨진 그림보다 여백이 낫다.
    """
    from ui import mascot

    slot_alias = {"hello": "welcome", "clap": "celebrate", "success": "celebrate",
                  "stamp": "stamp", "sheet": "cheer"}
    markup = mascot.html(slot_alias.get(key, key), size=width)
    if markup:
        st.markdown(
            f'<div style="display:flex; justify-content:center;">{markup}</div>',
            unsafe_allow_html=True)
    if caption:
        st.caption(caption)


# ------------------------------------------------------------
# 상단 내비게이션 (사이드바 대체)
# ------------------------------------------------------------
def topbar(active: str | None = None) -> None:
    """
    로고 · 서비스명 · 기능 메뉴 · 마이페이지를 한 줄로 배치한다.

    ▣ 왜 사이드바를 버렸는가
       Streamlit 사이드바는 모바일에서 기본 접힘 상태다. 학생이 QR 로 접속하면
       햄버거를 한 번 눌러야 메뉴가 나오는데, 시연 흐름에서 그 한 번의 터치가
       이탈 지점이 된다. 그래서 내비게이션을 전부 본문 상단으로 끌어올렸다.
       (ui/theme.py 의 @media 블록에서 이 내비만 모바일에서도 가로 스크롤로
        유지되도록 예외 처리한다 — 5개 버튼이 세로로 쌓이면 화면을 다 먹는다.)
    """
    name = ss.display_name()
    role_label = {"student": "학생", "teacher": "선생님"}.get(st.session_state.get("role"), "")

    # 브랜드 | 사용자 한 줄. 모바일 1단 강제 규칙에서 예외로 빼야
    # (theme.py 의 st-key-mjp_brandrow) 좁은 화면에서도 좌우로 남는다.
    with st.container(key="mjp_brandrow"):
        bcol, ucol = st.columns([2.4, 1])
    with bcol:
        # 브랜드 마크는 그라데이션 사각형이 아니라 로고를 벡터로 재구성한 엠블럼이다.
        # 36px 에서는 회로선·아크텍스트가 뭉개지므로 compact 레벨을 쓴다.
        st.markdown(f"""
        <div class="mjp-brand" style="padding-top:4px;">
            <div class="mjp-brand-mark">{emblem_svg(36, detail="compact", uid="navmark")}</div>
            <div>
                <div class="mjp-brand-name">{SERVICE_NAME}</div>
                <div class="mjp-brand-sub">{TEAM_FULL}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with ucol:
        st.markdown(f"""
        <div class="mjp-userchip">
            <div class="mjp-userchip-name">{name} 님</div>
            <div class="mjp-muted">{role_label}{' · ' if role_label else ''}{_provider_label()}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 기능 메뉴 (모바일에서도 가로 유지) ---
    # 항목 수는 역할에 따라 달라진다(선생님은 '우리 반'이 추가되어 7개).
    # 컬럼 수를 항목 수에 맞춰야 빈 칸이 생기거나 줄이 넘치지 않는다.
    with st.container(key="mjp_navbar"):
        items = ss.nav_items()
        cols = st.columns(len(items))
        for col, (key, label) in zip(cols, items):
            with col:
                is_active = (active == key)
                if st.button(label, key=f"nav_{key}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    ss.goto(key)

    st.markdown(f'<div style="height:1px;background:{CARD_BORDER};margin:2px 0 16px;"></div>',
                unsafe_allow_html=True)


def _provider_label() -> str:
    mapping = {"kakao": "카카오", "naver": "네이버", "google": "Google", "guest": "게스트"}
    return mapping.get(ss.provider(), "")


def back_to_hub(label: str = "← 메인 허브로") -> None:
    """기능 화면 좌상단 뒤로가기. 브라우저 뒤로가기가 없는 Streamlit 의 보완책."""
    if st.button(label, key=f"back_hub_{ss.current_page()}"):
        ss.goto(ss.PAGE_HUB)


# ------------------------------------------------------------
# 데이터 연동 상태 (키 입력칸 없음 — 연결 상태만 표시)
# ------------------------------------------------------------
def settings_expander() -> None:
    """
    데이터 연동 상태 — 키 입력칸 없이 '연결 상태'만 보여준다. [심사대응]

    예전에는 키 입력칸이 서버 secrets 값을 초기값으로 채워, 배포 서버에 키가 있으면
    로그인한 누구나 브라우저에서 키를 볼 수 있었다. 키는 운영자가 서버 secrets 에만
    넣고(services/fallback.server_key), 화면은 설정 여부만 표시한다.
    """
    def chip(label: str, on: bool) -> str:
        bg, text = (GREEN, "키 설정됨 · 연결 시도") if on else (CARD_BORDER, "키 없음 · 백업 데이터")
        fg = "#FFFFFF" if on else "#4E5968"
        return (f'<span class="mjp-badge" style="background:{bg}; color:{fg}; margin:0 6px 6px 0;">'
                f'{label} · {text}</span>')

    with st.expander("데이터 연동 상태", expanded=False):
        st.markdown(
            chip("Q-Net 자격증", fb.key_configured(fb.QNET_SECRET))
            + chip("고용24 채용공고", fb.key_configured(fb.WORKNET_SECRET)),
            unsafe_allow_html=True,
        )
        st.caption("API 키는 운영자가 서버 설정(secrets)에만 넣으며, 화면에서 입력하거나 볼 수 없습니다. "
                   "키가 없거나 응답이 없으면 백업 데이터로 동작합니다.")
        st.caption(f"내장 백업: {fb.backup_summary()}")


def disclaimer(text: str) -> None:
    st.markdown(f'<div class="mjp-disclaimer">{text}</div>', unsafe_allow_html=True)


def note(markup: str) -> None:
    """
    예시 데이터·백업 전환 안내 한 줄 (본문 크기 · 보조색).

    st.caption 은 13px 캡션이라, '예시'·'백업' 안내를 캡션으로 두면 눈에 덜 띈다.
    이런 안내는 이 함수로 넣어 본문 크기를 유지한다. markup 은 HTML 이다.
    """
    st.markdown(f'<div class="mjp-note">{markup}</div>', unsafe_allow_html=True)


def section_title(title: str, sub: str = "", icon_name: str = "", eyebrow: str = "") -> None:
    """
    화면 머리 — [작은 파란 라벨] + 큰 제목 + 설명 (v2 · 포트폴리오 섹션 머리와 같은 언어).

    v2 에서는 제목 옆 아이콘을 그리지 않는다. 화면의 가장 큰 요소는 제목 하나여야
    하고, 아이콘은 목록 행·카드 안에서만 쓴다. icon_name 은 기존 호출부 호환용으로 남겼다.
    """
    del icon_name   # v2: 제목 옆 아이콘 없음
    render_html(f"""
    <div class="mjp-screen-head">
        {f'<span class="mjp-eyebrow">{eyebrow}</span>' if eyebrow else ''}
        <div class="mjp-section-title">{title}</div>
        {f'<div class="mjp-section-sub">{sub}</div>' if sub else ''}
    </div>
    """)


def pill(text: str, color: str = GREEN) -> str:
    return f'<span class="mjp-badge" style="background:{color}; color:{BG};">{text}</span>'


# ------------------------------------------------------------
# v2 공통 부품 — 면 기반 (테두리·색띠 없음)
# ------------------------------------------------------------
def status_chip(text: str, color: str) -> str:
    """상태 칩 HTML — 연한 상태색 면 + 진한 상태색 글자 (예: '등록 완료', '준비 중')."""
    from ui.theme import BG, MUTED, STATUS_SOFT
    # 상태색이 아니면(회색 '준비 중' 등) 흰 칩 — 칩이 놓이는 카드가 회색 면이라서
    soft = STATUS_SOFT.get(color, BG)
    fg = color if color in STATUS_SOFT else MUTED
    return f'<span class="mjp-schip" style="background:{soft}; color:{fg};">{text}</span>'


def stat_tiles(items: list[tuple]) -> None:
    """
    큰 숫자 타일 묶음. items: [(라벨, 값, 보조문구, 색 | None), ...]

    색이 상태색이면 큰 숫자는 밝은 톤(STATUS_VIVID)으로 그린다 — 큰 글자 기준 3:1.
    """
    from ui.theme import STATUS_VIVID, TEXT
    tiles = "".join(f"""
        <div class="mjp-tile">
            <div class="mjp-tile-label">{label}</div>
            <div class="mjp-tile-value" style="color:{STATUS_VIVID.get(color, color or TEXT)};">{value}</div>
            {f'<div class="mjp-tile-note">{note}</div>' if note else ''}
        </div>""" for label, value, note, color in items)
    render_html(f'<div class="mjp-tiles">{tiles}</div>')


def list_row(icon_name: str, title: str, desc: str = "", right: str = "") -> str:
    """목록 행 HTML — 연한 블루 아이콘 타일 + 제목/설명 + 오른쪽 보조 정보."""
    from ui.theme import BRAND
    mark = (f'<div class="mjp-row-icon">{icon(icon_name, size=22, color=BRAND, stroke=1.8)}</div>'
            if icon_name else "")
    return f"""
    <div class="mjp-row">
        {mark}
        <div class="mjp-row-main">
            <div class="mjp-row-title">{title}</div>
            {f'<div class="mjp-row-desc">{desc}</div>' if desc else ''}
        </div>
        {f'<div class="mjp-row-right">{right}</div>' if right else ''}
    </div>"""


def code_display(label: str, code: str, desc: str = "") -> None:
    """반 코드·이어하기 코드 — 크게, 글자 사이를 띄워 칠판에 옮겨 적기 쉽게."""
    render_html(f"""
    <div class="mjp-codebox">
        <div class="mjp-codebox-label">{label}</div>
        <div class="mjp-codebox-code">{code}</div>
        {f'<div class="mjp-codebox-desc">{desc}</div>' if desc else ''}
    </div>
    """)


def or_divider(text: str = "또는") -> None:
    render_html(f'<div class="mjp-or"><span></span><b>{text}</b><span></span></div>')


# ------------------------------------------------------------
# 그리드 — 모바일 1단 전환 시 순서 보존
# ------------------------------------------------------------
def grid_columns(total: int, per_row: int) -> list:
    """
    카드 목록용 컬럼을 **행 단위로** 만들어 반환한다.

    ▣ 왜 필요한가 (모바일에서 실제로 깨졌던 부분)
       흔한 패턴인
           cols = st.columns(2)
           for i, item in enumerate(items):
               with cols[i % 2]: ...
       은 컬럼 2개를 만들어 놓고 항목을 번갈아 넣는다. 데스크톱에서는
       문제없지만, 모바일에서 컬럼이 1단으로 접히면 **컬럼 통째로** 쌓이므로
       0→2→4→1→3 순서가 된다. 학생 명단이나 기능 카드의 순서가 뒤섞인다.

       행마다 st.columns() 를 새로 만들면 [0,1] [2,3] [4] 로 묶이므로
       1단으로 접혀도 0→1→2→3→4 순서가 그대로 보존된다.

    반환값: 항목 순서와 1:1 대응하는 컬럼 리스트
    """
    columns = []
    for start in range(0, total, per_row):
        row = st.columns(per_row)
        for offset in range(per_row):
            if start + offset < total:
                columns.append(row[offset])
    return columns


# ------------------------------------------------------------
# [big-patch 1단계] 데이터 종류 표시 — 가상 예시 vs 출처가 있는 실제 기업
# ------------------------------------------------------------
def data_kind_chip(company: dict) -> str:
    """기업 카드 위에 붙이는 데이터 종류 칩 HTML."""
    if company.get("data_kind") == "verified":
        when = str(company.get("checked_at") or "")[:10]
        return (f'<span class="mjp-chiptag">출처 확인{" · 수집일 " + when if when else ""}</span>')
    return '<span class="mjp-chiptag gray">가상 기업 · 예시 데이터</span>'


def source_links(company: dict) -> str:
    """실제 기업의 출처 링크 줄 HTML (가상 기업이면 빈 문자열)."""
    if company.get("data_kind") != "verified":
        return ""
    import html as _html
    links = []
    for key, label in (("official_recruit_url", "공식 채용 페이지"),
                       ("talent_source_url", "인재상 출처"),
                       ("source_url", "출처")):
        url = str(company.get(key) or "").strip()
        if url.startswith(("http://", "https://")):
            links.append(f'<a href="{_html.escape(url, quote=True)}" target="_blank" '
                         f'rel="noopener" style="color:#1B64DA;">{label}</a>')
    return ('<div class="mjp-muted" style="margin-top:8px;">' + " · ".join(links) + "</div>") if links else ""

