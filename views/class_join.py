# -*- coding: utf-8 -*-
"""
views/class_join.py
[Phase 2-2] 학생 — 반 코드 입력 (선택)

▣ 반 등록은 '선택'이다
   반 코드가 없는 학생(혼자 준비하는 학생, QR로 접속한 심사위원)이 코드 입력
   화면에 갇히면, 게스트모드로 모든 기능을 쓸 수 있다는 약속이 깨진다.
   그래서 이 화면은 건너뛸 수 있고, 건너뛴 사실은 영속 저장되어 다시 묻지 않는다.
   나중에 코드를 받으면 마이페이지에서 언제든 등록할 수 있다.
"""

import streamlit as st

from core import session as ss
from services import store
from ui.components import section_title, topbar
from ui.theme import BRAND, CARD_BORDER, GREEN, MUTED, TEXT


def render() -> None:
    topbar(active=ss.PAGE_CLASS_JOIN)
    section_title("🏫 반 등록",
                  "선생님께 반 코드를 받았다면 입력해주세요. "
                  "없어도 괜찮습니다 — 모든 기능을 그대로 쓸 수 있어요.")

    current = store.get_user(ss.user_id()) or {}
    if current.get("class_code"):
        _render_joined(current["class_code"])
        return

    left, center, right = st.columns([1, 1.5, 1])

    with center:
        st.markdown(f"""
        <div class="mjp-card" style="border-left:3px solid {BRAND};">
            <div style="font-weight:800; color:{TEXT};">반 코드는 6자리예요</div>
            <div class="mjp-muted" style="margin-top:6px; line-height:1.6;">
                선생님이 알려준 영문·숫자 6자리를 입력하세요.
                대소문자는 구분하지 않습니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

        code = st.text_input("반 코드", key="join_code", max_chars=10,
                             placeholder="예: K7M2QX", label_visibility="collapsed")

        if st.button("✅ 우리 반에 등록하기", type="primary",
                     use_container_width=True, key="join_submit"):
            _join(code)

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; margin:16px 0 12px;">
            <div style="flex:1; height:1px; background:{CARD_BORDER};"></div>
            <div style="color:{MUTED}; font-size:12px;">또는</div>
            <div style="flex:1; height:1px; background:{CARD_BORDER};"></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("👤 혼자 사용할게요", use_container_width=True, key="join_skip"):
            store.skip_class(ss.user_id())
            ss.goto(ss.PAGE_HUB)

        st.markdown(
            f'<div style="color:{MUTED}; font-size:12px; margin-top:8px; line-height:1.65;">'
            f'반 등록을 하지 않아도 진단·기업 탐색·자소서 생성까지 모든 기능이 똑같이 동작합니다. '
            f'나중에 코드를 받으면 <b style="color:{TEXT};">마이페이지</b>에서 등록할 수 있어요.</div>',
            unsafe_allow_html=True,
        )


def _join(code: str) -> None:
    ok, message = store.join_class(ss.user_id(), code)
    if ok:
        ss.set_class_code((code or "").strip().upper())
        st.session_state["_class_joined_msg"] = message
        st.rerun()
    else:
        st.error(message)


def _render_joined(code: str) -> None:
    """이미 반에 속한 학생 화면."""
    klass = store.get_class(code)
    label = store.class_label(klass) or code

    message = st.session_state.pop("_class_joined_msg", "")
    if message:
        st.success(f"🎉 {message}")
        st.balloons()

    st.markdown(f"""
    <div class="mjp-card" style="border-color:{GREEN};">
        <span class="mjp-badge" style="background:{GREEN}; color:#0A0E17;">등록 완료</span>
        <div style="font-size:21px; font-weight:800; color:{TEXT}; margin-top:12px;">{label}</div>
        <div class="mjp-muted" style="margin-top:6px;">반 코드 {code}</div>
        <div class="mjp-muted" style="margin-top:10px; line-height:1.6;">
            이제 진단 결과와 로드맵 진행 상황이 선생님의 '우리 반 현황'에 표시됩니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 기능 선택하러 가기", type="primary", use_container_width=True,
                 key="joined_hub"):
        ss.goto(ss.PAGE_HUB)

    with st.expander("반을 잘못 등록했어요"):
        st.caption("반에서 나가면 이후 활동은 선생님 화면에 표시되지 않습니다.")
        if st.button("반에서 나가기", use_container_width=True, key="join_leave"):
            store.leave_class(ss.user_id())
            ss.set_class_code(None)
            st.rerun()
