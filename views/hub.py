# -*- coding: utf-8 -*-
"""
views/hub.py
[Phase 1-4] 메인 허브 — 로그인 + 역할 선택을 마친 뒤의 진입점

구성
----
 · 상단 내비게이션 (ui/components.topbar) — 참고 디자인의 Platform/Docs/Pricing 자리
 · 인사말 + 이어하기 코드 안내
 · 4대 핵심 기능 카드 (클릭 → 기존 탭 화면으로 이동, 탭 내용은 그대로 재사용)
 · 향후 로드맵 / 마이페이지 보조 진입구
"""

import streamlit as st

from core import session as ss
from services import fallback as fb
from ui.components import section_title, settings_expander, show_sticker, topbar
from ui.theme import BADGE_COLORS, CARD_BORDER, GOLD, GREEN, MUTED, PURPLE, TEXT


def render() -> None:
    topbar(active=ss.PAGE_HUB)

    name = ss.display_name()
    is_teacher = st.session_state.get("role") == "teacher"

    # ---------- 인사 ----------
    greet_col, sticker_col = st.columns([3, 1])
    with greet_col:
        section_title(
            f"{name} 님, 오늘도 한 걸음 더.",
            "아래에서 시작할 기능을 선택하세요. 언제든 상단 메뉴로 다른 기능으로 이동할 수 있어요."
            if not is_teacher else
            "선생님 화면입니다. 우리 반 현황은 마이페이지에서 확인할 수 있어요.",
        )
    with sticker_col:
        # 키를 부여해 ui/theme.py 의 모바일 미디어쿼리에서 통째로 숨길 수 있게 한다
        with st.container(key="mjp_hub_sticker"):
            show_sticker("hello", width=110)

    # ---------- 게스트 이어하기 코드 ----------
    if ss.provider() == "guest" and st.session_state.get("resume_code"):
        code = st.session_state["resume_code"]
        st.markdown(f"""
        <div class="mjp-card" style="border-color:{GOLD}; display:flex; align-items:center;
                    gap:14px; flex-wrap:wrap;">
            <div style="font-size:22px;">🔑</div>
            <div style="flex:1; min-width:200px;">
                <div style="font-weight:800; color:{TEXT};">이어하기 코드 · <span style="color:{GOLD};
                     letter-spacing:0.14em; font-size:19px;">{code}</span></div>
                <div class="mjp-muted" style="margin-top:4px;">
                    다음에 접속할 때 로그인 화면에서 이 코드를 넣으면 지금 기록을 그대로 이어서 볼 수 있어요.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- 데이터 출처 배지 ----------
    st.markdown(fb.badge_html(st.session_state.tracker, BADGE_COLORS), unsafe_allow_html=True)

    # ---------- 4대 핵심 기능 카드 ----------
    st.markdown(f'<div style="font-size:13px; font-weight:800; color:{MUTED}; '
                f'letter-spacing:0.08em; margin:22px 0 12px;">핵심 기능</div>',
                unsafe_allow_html=True)

    cols = st.columns(2)
    for i, feature in enumerate(ss.FEATURES):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="mjp-feature">
                <div class="mjp-feature-icon">{feature['icon']}</div>
                <div class="mjp-feature-title">{feature['title']}</div>
                <div class="mjp-feature-desc">{feature['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{feature['title']} 시작하기 →", key=f"hub_{feature['key']}",
                         use_container_width=True):
                ss.goto(feature["key"])
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ---------- 보조 진입구 ----------
    st.markdown(f'<div style="height:1px;background:{CARD_BORDER};margin:14px 0 18px;"></div>',
                unsafe_allow_html=True)

    sub1, sub2 = st.columns(2)
    with sub1:
        st.markdown(f"""
        <div class="mjp-card" style="border-left:3px solid {PURPLE};">
            <div style="font-weight:800; color:{TEXT};">👤 마이페이지</div>
            <div class="mjp-muted" style="margin-top:6px;">
                찜한 기업, 열람 이력, 매칭 점수 히스토리를 모아봅니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("마이페이지 열기", key="hub_mypage", use_container_width=True):
            ss.goto(ss.PAGE_MYPAGE)

    with sub2:
        st.markdown(f"""
        <div class="mjp-card" style="border-left:3px solid {GREEN};">
            <div style="font-weight:800; color:{TEXT};">🚀 향후 로드맵</div>
            <div class="mjp-muted" style="margin-top:6px;">
                지금 만들지 '않은' 기능과 그 판단 기준을 공개합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("로드맵 보기", key="hub_next", use_container_width=True):
            ss.goto(ss.PAGE_NEXT)

    settings_expander()
