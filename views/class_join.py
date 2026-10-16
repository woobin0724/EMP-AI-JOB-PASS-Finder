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
from ui.components import or_divider, render_html, section_title, status_chip, topbar
from ui.theme import GREEN


def render() -> None:
    topbar(active=ss.PAGE_CLASS_JOIN)

    current = store.get_user(ss.user_id()) or {}
    if current.get("class_code"):
        section_title("반 등록", icon_name="school")
        _render_joined(current["class_code"])
        return

    with st.container(key="mjp_narrow_join"):
        section_title("반 코드를<br>입력해주세요", icon_name="school", eyebrow="반 등록 (선택)", sub=
                      "선생님께 반 코드를 받았다면 입력해주세요. "
                      "없어도 괜찮습니다 — 모든 기능을 그대로 쓸 수 있어요.")

        # 라벨을 숨기면 무엇을 적는 칸인지 placeholder 로만 알 수 있다 → 보이게 둔다
        code = st.text_input("반 코드 (영문·숫자 6자리, 대소문자 구분 없음)", key="join_code",
                             max_chars=10, placeholder="예: K7M2QX")

        # 폰에서는 화면 하단에 꽉 차게 고정된다 (key 가 mjp_cta_ 로 시작)
        with st.container(key="mjp_cta_join"):
            if st.button("우리 반에 등록하기", type="primary",
                         use_container_width=True, key="join_submit"):
                _join(code)

        or_divider()

        if st.button("혼자 사용할게요", use_container_width=True, key="join_skip"):
            store.skip_class(ss.user_id())
            ss.goto(ss.PAGE_HUB)

        render_html(
            '<div class="mjp-muted" style="margin-top:8px; line-height:1.65;">'
            '반 등록을 하지 않아도 진단·기업 탐색·자소서 생성까지 모든 기능이 똑같이 동작합니다. '
            '나중에 코드를 받으면 <b>마이페이지</b>에서 등록할 수 있어요.</div>'
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
        st.success(message)
        st.balloons()

    render_html(f"""
    <div class="mjp-tcard">
        {status_chip("등록 완료", GREEN)}
        <h4 style="margin-top:14px !important;">{label}</h4>
        <p class="mjp-muted">반 코드 {code}</p>
        <p style="margin-top:10px !important;">
            이제 진단 결과와 로드맵 진행 상황이 선생님의 '우리 반 현황'에 표시됩니다.
        </p>
    </div>
    """)

    with st.container(key="mjp_cta_joined"):
        if st.button("기능 선택하러 가기", type="primary", use_container_width=True,
                     key="joined_hub"):
            ss.goto(ss.PAGE_HUB)

    with st.expander("반을 잘못 등록했어요"):
        st.caption("반에서 나가면 이후 활동은 선생님 화면에 표시되지 않습니다.")
        if st.button("반에서 나가기", use_container_width=True, key="join_leave"):
            store.leave_class(ss.user_id())
            ss.set_class_code(None)
            st.rerun()
