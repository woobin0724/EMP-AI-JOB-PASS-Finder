# -*- coding: utf-8 -*-
"""
views/class_setup.py
[Phase 2-1] 선생님 — '우리 반' 개설 & 반 코드 발급

반 코드 설계
------------
services/store.py 의 _CODE_ALPHABET 에서 0/O, 1/I 를 뺐다.
선생님이 칠판에 적고 학생이 폰으로 옮겨 적는 상황을 가정하면,
헷갈리는 글자 하나가 "코드가 안 돼요" 문의를 만든다.
"""

import streamlit as st

from core import session as ss
from services import store
from ui.components import back_to_hub, section_title, topbar
from ui.theme import BRAND, CARD_BORDER, GOLD, GREEN, MUTED, TEXT

GRADE_OPTIONS = ["1학년", "2학년", "3학년"]


def render() -> None:
    topbar(active=ss.PAGE_CLASS_SETUP)

    existing = store.teacher_class(ss.user_id())
    if existing:
        _render_existing(existing)
        return

    back_to_hub()
    section_title("우리 반 만들기", icon_name="school", sub=
                  "반을 만들면 6자리 반 코드가 발급됩니다. "
                  "학생들이 그 코드를 입력하면 우리 반 현황에서 진행 상황을 볼 수 있어요.")

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        school = st.text_input("학교명", placeholder="예: 전북기계공업고등학교",
                               key="cls_school")
        gcol, ccol = st.columns(2)
        with gcol:
            grade = st.selectbox("학년", GRADE_OPTIONS, index=2, key="cls_grade")
        with ccol:
            class_no = st.text_input("반", placeholder="예: 2반", key="cls_no")

        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("우리 반 만들고 코드 받기", type="primary",
                     use_container_width=True, key="cls_create"):
            _create(school, grade, class_no)

        if st.button("나중에 만들기", use_container_width=True, key="cls_later"):
            ss.goto(ss.PAGE_HUB)

    with right:
        st.markdown(f"""
        <div class="mjp-card" style="border-left:3px solid {BRAND};">
            <div style="font-weight:800; color:{TEXT};">반을 만들면 이런 걸 볼 수 있어요</div>
            <ul style="color:{MUTED}; font-size:13px; margin:12px 0 0; padding-left:18px;
                       line-height:1.75;">
                <li>학생별 <b style="color:{TEXT};">목표 기업</b></li>
                <li>커리어 로드맵 <b style="color:{TEXT};">진행 단계</b></li>
                <li>최근 <b style="color:{TEXT};">매칭 점수</b>와 반 평균</li>
                <li>아직 시작하지 않은 학생 확인</li>
            </ul>
            <div style="color:{MUTED}; font-size:12px; margin-top:14px; line-height:1.6;">
                학생이 반 코드를 넣지 않아도 앱은 그대로 쓸 수 있습니다.
                반 등록은 선생님이 현황을 보기 위한 <b>선택 기능</b>이에요.
            </div>
        </div>
        """, unsafe_allow_html=True)


def _create(school: str, grade: str, class_no: str) -> None:
    """입력값을 검증하고 반을 만든다."""
    school = (school or "").strip()
    class_no = (class_no or "").strip()

    if not school:
        st.error("학교명을 입력해주세요.")
        return
    if not class_no:
        st.error("반을 입력해주세요. (예: 2반)")
        return

    klass = store.create_class(ss.user_id(), school, grade, class_no)
    ss.set_class_code(klass["class_code"])
    st.rerun()


def _render_existing(klass: dict) -> None:
    """이미 반을 만든 선생님에게는 코드와 현황 진입구를 보여준다."""
    section_title("우리 반", store.class_label(klass), icon_name="school")

    students = store.class_students(klass["class_code"])

    st.markdown(f"""
    <div class="mjp-card" style="border-color:{GOLD};">
        <div class="mjp-muted">반 코드</div>
        <div style="color:{GOLD}; font-size:34px; font-weight:800;
                    letter-spacing:0.22em; margin:6px 0 10px;">{klass['class_code']}</div>
        <div class="mjp-muted" style="line-height:1.6;">
            학생들에게 이 코드를 알려주세요. 학생은 <b style="color:{TEXT};">마이페이지 →
            반 등록</b>에서 코드를 입력하면 우리 반에 들어옵니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # st.code 는 우상단에 복사 버튼을 기본 제공한다.
    # 직접 만든 복사 버튼은 클립보드 API 권한 문제로 모바일 사파리에서 자주 실패한다.
    st.caption("아래 코드를 눌러 복사하세요")
    st.code(klass["class_code"], language=None)

    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.markdown(f"""
        <div class="mjp-card" style="text-align:center;">
            <div class="mjp-muted">등록된 학생</div>
            <div style="font-size:30px; font-weight:800; color:{GREEN};">{len(students)}명</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"""
        <div class="mjp-card" style="text-align:center;">
            <div class="mjp-muted">개설일</div>
            <div style="font-size:18px; font-weight:800; color:{TEXT}; margin-top:8px;">
                {klass.get('created_at', '')[:10]}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("우리 반 현황 보기", type="primary", use_container_width=True,
                 key="cls_to_board"):
        ss.goto(ss.PAGE_CLASS_BOARD)
    if st.button("← 메인 허브로", use_container_width=True, key="cls_to_hub"):
        ss.goto(ss.PAGE_HUB)

    st.markdown(f'<div style="height:1px;background:{CARD_BORDER};margin:16px 0;"></div>',
                unsafe_allow_html=True)
    st.caption("한 선생님 계정당 하나의 반을 운영합니다. 반을 새로 만들려면 "
               "마이페이지에서 역할을 다시 선택해주세요.")
