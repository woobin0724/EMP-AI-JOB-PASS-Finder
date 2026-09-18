# -*- coding: utf-8 -*-
"""
ui/components.py
여러 화면이 공유하는 렌더링 조각 (스티커 · 상단 내비 · 설정 패널)
"""

import streamlit as st

from core import session as ss
from data import ogq_assets as ogq
from services import auth as auth_svc
from services import fallback as fb
from ui.brand import SERVICE_NAME, TEAM_FULL
from ui.emblem import emblem_svg
from ui.icons import icon
from ui.theme import BG, CARD_BORDER, GREEN, MUTED, TEXT


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
# 데이터 연동 설정 (기존 사이드바 내용을 접이식 패널로 이관)
# ------------------------------------------------------------
def settings_expander() -> None:
    """외부 API 키 입력. 사이드바를 없앴으므로 본문 expander 로 내렸다."""
    with st.expander("데이터 연동 설정 (선택)", expanded=False):
        st.session_state["qnet_key"] = st.text_input(
            "Q-Net / 공공데이터포털 서비스키", type="password",
            value=st.session_state.get("qnet_key") or auth_svc.safe_secret("QNET_API_KEY"),
            key="qnet_key_widget",
        )
        st.session_state["worknet_key"] = st.text_input(
            "고용24(워크넷) Open API 인증키", type="password",
            value=st.session_state.get("worknet_key") or auth_svc.safe_secret("WORKNET_API_KEY"),
            key="worknet_key_widget",
        )
        st.caption("키가 없어도 앱은 백업 마스터 데이터로 100% 동작합니다.")
        st.caption(f"내장 백업: {fb.backup_summary()}")


def disclaimer(text: str) -> None:
    st.markdown(f'<div class="mjp-disclaimer">{text}</div>', unsafe_allow_html=True)


def section_title(title: str, sub: str = "", icon_name: str = "") -> None:
    """
    화면 상단 제목 블록 — 큰 타이포 + 여백 (참고 디자인 톤).

    icon_name 을 주면 제목 왼쪽에 라인 아이콘이 붙는다. 이모지 대신 쓰는 자리라
    색은 브랜드 블루로 고정해 마스코트(컬러풀)와 톤이 겹치지 않게 했다.
    """
    from ui.theme import BRAND
    mark = (f'<span style="flex:none; display:inline-flex; padding-top:3px;">'
            f'{icon(icon_name, size=26, color=BRAND, stroke=1.8)}</span>') if icon_name else ""
    st.markdown(f"""
    <div style="margin:4px 0 18px;">
        <div style="display:flex; align-items:flex-start; gap:12px;">
            {mark}<div class="mjp-section-title">{title}</div>
        </div>
        {f'<div class="mjp-section-sub">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)


def pill(text: str, color: str = GREEN) -> str:
    return f'<span class="mjp-badge" style="background:{color}; color:{BG};">{text}</span>'


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
