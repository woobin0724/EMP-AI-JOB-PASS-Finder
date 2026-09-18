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
from services import store
from ui.components import grid_columns, section_title, settings_expander, topbar
from ui.icons import icon
from ui import mascot
from ui.theme import BADGE_COLORS, BRAND, CARD_BORDER, GOLD, GREEN, MUTED, PURPLE, TEXT


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
            f"<b>{name} 님, 환영합니다!</b><br>"
            "여기서 진단하고, 기업을 찾고, 자소서까지 한 번에 만들 수 있어요. "
            "무엇부터 해볼까요?",
            tone="brand", size=96,
        )

    section_title(
        f"{name} 님, 오늘도 한 걸음 더.",
        "아래에서 시작할 기능을 선택하세요. 언제든 상단 메뉴로 다른 기능으로 이동할 수 있어요."
        if not is_teacher else
        "선생님 화면입니다. 우리 반 현황은 상단 '우리 반'에서 확인할 수 있어요.",
    )

    # ---------- 게스트 이어하기 코드 ----------
    if ss.provider() == "guest" and st.session_state.get("resume_code"):
        code = st.session_state["resume_code"]
        st.markdown(f"""
        <div class="mjp-card" style="border-color:{GOLD}; display:flex; align-items:center;
                    gap:14px; flex-wrap:wrap;">
            <div style="flex:none;">{icon("key", size=20, color=GOLD)}</div>
            <div style="flex:1; min-width:200px;">
                <div style="font-weight:800; color:{TEXT};">이어하기 코드 · <span style="color:{GOLD};
                     letter-spacing:0.14em; font-size:19px;">{code}</span></div>
                <div class="mjp-muted" style="margin-top:4px;">
                    다음에 접속할 때 로그인 화면에서 이 코드를 넣으면 지금 기록을 그대로 이어서 볼 수 있어요.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- [Phase 2] 반 관련 안내 ----------
    _class_strip(is_teacher)

    # ---------- 데이터 출처 배지 ----------
    st.markdown(fb.badge_html(st.session_state.tracker, BADGE_COLORS), unsafe_allow_html=True)

    # ---------- 4대 핵심 기능 카드 ----------
    st.markdown(f'<div style="font-size:13px; font-weight:800; color:{MUTED}; '
                f'letter-spacing:0.08em; margin:22px 0 12px;">핵심 기능</div>',
                unsafe_allow_html=True)

    for col, feature in zip(grid_columns(len(ss.FEATURES), 2), ss.FEATURES):
        with col:
            st.markdown(f"""
            <div class="mjp-feature">
                <div class="mjp-feature-icon">{icon(feature['icon'], size=30, color=BRAND, stroke=1.7)}</div>
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

    sub_cols = st.columns(3 if is_teacher else 2)
    if is_teacher:
        with sub_cols[0]:
            st.markdown(f"""
            <div class="mjp-card" style="border-left:3px solid {GOLD};">
                <div style="font-weight:800; color:{TEXT}; display:flex; align-items:center; gap:8px;">{icon("school", size=17, color=GOLD)} 우리 반 현황</div>
                <div class="mjp-muted" style="margin-top:6px;">
                    학생별 목표 기업·진행 단계·매칭 점수를 한눈에 봅니다.
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("우리 반 열기", key="hub_class_board", use_container_width=True):
                ss.goto(ss.PAGE_CLASS_BOARD)

    sub1, sub2 = (sub_cols[1], sub_cols[2]) if is_teacher else (sub_cols[0], sub_cols[1])
    with sub1:
        st.markdown(f"""
        <div class="mjp-card" style="border-left:3px solid {PURPLE};">
            <div style="font-weight:800; color:{TEXT}; display:flex; align-items:center; gap:8px;">{icon("user", size=17, color=PURPLE)} 마이페이지</div>
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
            <div style="font-weight:800; color:{TEXT}; display:flex; align-items:center; gap:8px;">{icon("route", size=17, color=GREEN)} 향후 로드맵</div>
            <div class="mjp-muted" style="margin-top:6px;">
                지금 만들지 '않은' 기능과 그 판단 기준을 공개합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("로드맵 보기", key="hub_next", use_container_width=True):
            ss.goto(ss.PAGE_NEXT)

    settings_expander()


# ------------------------------------------------------------
# [Phase 2] 반 상태 안내 스트립
# ------------------------------------------------------------
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
            <div class="mjp-card" style="border-left:3px solid {GOLD}; display:flex;
                        align-items:center; gap:14px; flex-wrap:wrap;">
                <div style="flex:none;">{icon("school", size=20, color=GOLD)}</div>
                <div style="flex:1; min-width:200px;">
                    <div style="font-weight:800; color:{TEXT};">{store.class_label(klass)}
                        · 반 코드 <span style="color:{GOLD}; letter-spacing:0.12em;">{klass['class_code']}</span></div>
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
