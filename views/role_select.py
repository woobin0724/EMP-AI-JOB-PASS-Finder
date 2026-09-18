# -*- coding: utf-8 -*-
"""
views/role_select.py
[Phase 1-3] 역할 선택 — 로그인 직후 1회만 노출

재방문 처리
-----------
선택 결과는 세션과 영속 저장소(services/store.py) 양쪽에 저장된다.
다음 접속 때 core/session.py 의 login() 이 저장소에서 role 을 읽어와
role 이 있으면 이 화면을 건너뛰고 곧장 메인 허브로 보낸다.
(= 요구사항 "이미 역할을 선택한 재방문 유저는 이 화면을 건너뛴다")
"""

import streamlit as st

from core import session as ss
from services import store
from ui.icons import icon
from ui.theme import BLUE, CARD_BORDER, GREEN, MUTED, PURPLE, TEXT

ROLES = [
    {
        "key": "student", "icon": "cap", "title": "학생이에요",
        "color": GREEN,
        "desc": "내 스펙을 진단하고, 목표 기업을 찾고, 자소서를 만들어요.",
        "bullets": ["100점 만점 합격 지수 진단", "관심 기업 찜하기 & 기록", "커리어 로드맵 스탬프 모으기"],
    },
    {
        "key": "teacher", "icon": "users", "title": "선생님이에요",
        "color": PURPLE,
        "desc": "우리 반을 만들고 학생들의 취업 준비 현황을 한눈에 봐요.",
        "bullets": ["우리 반 개설 & 반 코드 발급", "학생별 목표 기업 · 진행 단계 확인", "반 평균 매칭 점수 모니터링"],
    },
]


def render() -> None:
    st.markdown(f"""
    <div style="text-align:center; margin:26px 0 10px;">
        <div style="font-size:34px; font-weight:800; color:{TEXT}; letter-spacing:-0.03em;">
            어떻게 사용하실 건가요?
        </div>
        <div style="color:{MUTED}; font-size:15px; margin-top:12px; line-height:1.6;">
            역할에 따라 화면 구성이 달라집니다. 처음 한 번만 선택하면 돼요.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    cols = st.columns(2)
    for col, role in zip(cols, ROLES):
        with col:
            bullets = "".join(
                f'<li style="margin-bottom:6px;">{b}</li>' for b in role["bullets"]
            )
            st.markdown(f"""
            <div class="mjp-feature" style="border-color:{role['color']}33;">
                <div style="line-height:1;">{icon(role["icon"], size=38, color=role["color"], stroke=1.7)}</div>
                <div style="font-size:21px; font-weight:800; color:{role['color']}; margin-top:14px;">
                    {role['title']}
                </div>
                <div style="color:{MUTED}; font-size:13.5px; margin-top:10px; line-height:1.6;">
                    {role['desc']}
                </div>
                <ul style="color:{MUTED}; font-size:12.5px; margin:14px 0 6px; padding-left:18px;
                           line-height:1.55;">{bullets}</ul>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"{role['title']} 선택", key=f"role_{role['key']}",
                         type="primary", use_container_width=True):
                _choose(role["key"])

    st.markdown(f"""
    <div style="text-align:center; margin-top:28px; padding-top:16px;
                border-top:1px solid {CARD_BORDER}; color:{MUTED}; font-size:12px;">
        선택한 역할은 나중에 마이페이지에서 바꿀 수 있어요.
    </div>
    """, unsafe_allow_html=True)


def _choose(role: str) -> None:
    """
    역할을 세션과 저장소에 기록하고 역할에 맞는 다음 화면으로 보낸다.

      선생님 → 우리 반 개설 (반 코드를 받아야 학생을 모을 수 있다)
      학생   → 반 코드 입력 (건너뛸 수 있음 · 반 등록은 선택)

    둘 다 '나중에 하기'로 빠져나갈 수 있어서, 어느 쪽도 허브 진입을 막지 않는다.
    """
    st.session_state["role"] = role
    uid = ss.user_id()
    if uid:
        store.set_role(uid, role)

    if role == "teacher":
        ss.goto(ss.PAGE_CLASS_SETUP)
    elif uid and store.needs_class_prompt(uid):
        ss.goto(ss.PAGE_CLASS_JOIN)
    else:
        ss.goto(ss.PAGE_HUB)
