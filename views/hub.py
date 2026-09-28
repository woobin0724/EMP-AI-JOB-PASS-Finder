# -*- coding: utf-8 -*-
"""
views/hub.py
[Phase 1-4] 메인 허브 — 로그인 + 역할 선택을 마친 뒤의 진입점

구성
----
 · 상단 내비게이션 (ui/components.topbar) — 참고 디자인의 Platform/Docs/Pricing 자리
 · 인사말 + 이어하기 코드 안내
 · 4대 핵심 기능 공정 순서표 (클릭 → 기존 탭 화면으로 이동)
 · 향후 로드맵 / 마이페이지 보조 진입구
"""

import streamlit as st

from core import session as ss
from services import fallback as fb
from services import store
from ui.components import render_html, section_title, settings_expander, topbar
from ui.icons import icon
from ui import mascot
from ui.theme import BADGE_COLORS, BRAND, BRAND_DEEP, TEXT


def render() -> None:
    topbar(active=ss.PAGE_HUB)

    name = ss.display_name()
    is_teacher = st.session_state.get("role") == "teacher"

    # ---------- 인사 ----------
    # [Phase 4] 로그인 직후 1회만 마스코트가 반겨준다.
    # 매번 띄우면 반가움이 아니라 소음이 된다.
    if st.session_state.pop("_just_logged_in", False):
        mascot.speech(
            "welcome",
            "처음이라면 <b>1번 스펙 진단</b>부터 해보세요. "
            "내 점수가 나오면 기업 탐색과 자소서가 그 점수를 바탕으로 움직여요.",
            tone="brand", size=96,
        )

    section_title(
        f"{name} 님, 오늘도 한 걸음 더.",
        "아래에서 시작할 기능을 선택하세요. 언제든 상단 메뉴로 다른 기능으로 이동할 수 있어요."
        if not is_teacher else
        "선생님 화면입니다. 우리 반 현황은 상단 '우리 반'에서 확인할 수 있어요.",
    )

    # ---------- 공정 순서표 ----------
    # 네 기능은 실제로 이 순서로 쓰는 게 맞다 (진단 → 탐색 → 대비 → 자소서).
    # 같은 크기 카드 네 장 대신 번호가 붙은 순서표로 보여줘야 그 순서가 읽힌다.
    with st.container(key="mjp_steps"):
        for no, feature in enumerate(ss.FEATURES, start=1):
            # 첫 줄만 key 를 달리해 구분선(border-top)을 빼준다. Streamlit 은 컨테이너마다
            # 래퍼를 씌워서 :first-child 로는 잡히지 않는다.
            step_key = "mjp_step_first" if no == 1 else f"mjp_step_{feature['key']}"
            with st.container(key=step_key):
                text_col, btn_col = st.columns([3.2, 1], vertical_alignment="center")
                with text_col:
                    render_html(f"""
                    <div class="mjp-step">
                        <div class="mjp-step-no">{no}</div>
                        <div>
                            <div class="mjp-step-title">{feature['title']}</div>
                            <div class="mjp-step-desc">{feature['desc']}</div>
                        </div>
                    </div>
                    """)
                with btn_col:
                    if st.button(f"{feature.get('nav', feature['title'])} 열기",
                                 key=f"hub_{feature['key']}", use_container_width=True,
                                 type="primary" if no == 1 else "secondary"):
                        ss.goto(feature["key"])

    # ---------- 보조 진입구 ----------
    # 부록 목록 — 아이콘 + 제목 + 한 줄 설명 + 버튼. 색 띠 장식 없이 괘선으로만 나눈다.
    st.markdown("#### 부록")
    extras = []
    if is_teacher:
        extras.append(("school", "우리 반 현황",
                       "학생별 목표 기업·진행 단계·매칭 점수를 한눈에 봅니다.",
                       "우리 반 열기", "hub_class_board", ss.PAGE_CLASS_BOARD))
    extras.append(("user", "마이페이지",
                   "찜한 기업, 열람 이력, 매칭 점수 히스토리를 모아봅니다.",
                   "마이페이지 열기", "hub_mypage", ss.PAGE_MYPAGE))
    extras.append(("route", "향후 로드맵",
                   "지금 만들지 '않은' 기능과 그 판단 기준을 공개합니다.",
                   "로드맵 보기", "hub_next", ss.PAGE_NEXT))

    for col, (ic, title, desc, label, key, page) in zip(st.columns(len(extras)), extras):
        with col:
            render_html(f"""
            <div class="mjp-card" style="margin-bottom:8px;">
                <div style="font-weight:800; color:{TEXT}; display:flex; align-items:center; gap:8px;">{icon(ic, size=17, color=BRAND)} {title}</div>
                <div class="mjp-muted" style="margin-top:6px;">{desc}</div>
            </div>
            """)
            if st.button(label, key=key, use_container_width=True):
                ss.goto(page)

    settings_expander()


# ------------------------------------------------------------
# [Phase 2] 반 상태 안내 스트립
# ------------------------------------------------------------
    # ---------- 계정·반 안내 (보조) ----------
    # 학생 대부분이 매번 쓰지는 않는 정보다. 핵심 기능 카드가 첫 화면을
    # 차지하도록 주 동선 아래로 내렸다.
    if ss.provider() == "guest" and st.session_state.get("resume_code"):
        code = st.session_state["resume_code"]
        st.markdown(f"""
        <div class="mjp-card" style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
            <div style="flex:none;">{icon("key", size=20, color=BRAND)}</div>
            <div style="flex:1; min-width:200px;">
                <div style="font-weight:800; color:{TEXT};">이어하기 코드 · <span class="mjp-serial" style="color:{BRAND_DEEP};
                     font-size:var(--mjp-h2);">{code}</span></div>
                <div class="mjp-muted" style="margin-top:4px;">
                    다음에 접속할 때 로그인 화면에서 이 코드를 넣으면 지금 기록을 그대로 이어서 볼 수 있어요.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 반 등록/현황
    _class_strip(is_teacher)

    # 데이터 출처 배지
    st.markdown(fb.badge_html(st.session_state.tracker, BADGE_COLORS), unsafe_allow_html=True)


def _class_strip(is_teacher: bool) -> None:
    """
    허브 상단의 반 관련 한 줄 안내.

    선생님: 반이 없으면 개설 유도 / 있으면 코드와 학생 수
    학생  : 소속 반 표시. 미등록이면 '코드 받았으면 등록하세요' 정도로만 권하고
            강요하지 않는다 (반 등록은 선택 기능이다).
    """
    uid = ss.user_id()
    if not uid:
        return

    if is_teacher:
        klass = store.teacher_class(uid)
        if klass:
            count = len(store.class_students(klass["class_code"]))
            st.markdown(f"""
            <div class="mjp-card" style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
                <div style="flex:none;">{icon("school", size=20, color=BRAND)}</div>
                <div style="flex:1; min-width:200px;">
                    <div style="font-weight:800; color:{TEXT};">{store.class_label(klass)}
                        · 반 코드 <span class="mjp-serial" style="color:{BRAND_DEEP};">{klass['class_code']}</span></div>
                    <div class="mjp-muted" style="margin-top:4px;">등록 학생 {count}명</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("아직 우리 반을 만들지 않으셨어요. 반을 만들면 학생들의 진행 상황을 볼 수 있습니다.")
            if st.button("우리 반 만들기", key="hub_make_class"):
                ss.goto(ss.PAGE_CLASS_SETUP)
        return

    # --- 학생 ---
    user = store.get_user(uid) or {}
    code = user.get("class_code")
    if code:
        klass = store.get_class(code)
        st.markdown(
            f'<div class="mjp-muted" style="margin:2px 0 12px;">소속 반 · '
            f'<b style="color:{TEXT};">{store.class_label(klass) or code}</b></div>',
            unsafe_allow_html=True,
        )
    elif not user.get("class_skipped"):
        ccol1, ccol2 = st.columns([3, 1])
        with ccol1:
            st.caption("선생님께 반 코드를 받았다면 등록해보세요. (선택 사항)")
        with ccol2:
            if st.button("반 등록", key="hub_join_class", use_container_width=True):
                ss.goto(ss.PAGE_CLASS_JOIN)
