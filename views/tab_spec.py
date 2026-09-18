# -*- coding: utf-8 -*-
"""
views/tab_spec.py
기능 1. 스펙 진단 & 추천 (+ OGQ 점수 구간별 반응형 스티커)

원본 app.py 의 TAB 1 블록을 그대로 이관했다. 점수 산출 로직(core/matching.py)은
손대지 않았다 — 이번 단계의 목표는 '진입 방식 변경'이지 '계산 변경'이 아니다.
"""

import streamlit as st

from core import session as ss
from core.catalog import all_talent_keywords, certs_for_department, load_cert_names
from core.matching import calc_spec_score
from data import ogq_assets as ogq
from data.certifications import get_bonus_points
from data.company_showcase import COMPANY_SHOWCASE, COMPANY_SIZE_TAGS
from services import activity
from data.departments import (
    DEPARTMENT_LIST, get_category, get_employment_rate, get_majors_for_department,
)
from ui import mascot
from ui.components import back_to_hub, render_html, section_title, topbar
from ui.theme import BG, BLUE, CARD_BORDER, GREEN, GOLD, MUTED, RED, TEXT, render_stars, score_bar


# 점수 구간 → 마스코트 감정 슬롯
# 숫자만 보여주는 진단은 낮은 점수를 받은 학생을 밀어낸다. 같은 48점이라도
# 위로하는 캐릭터가 옆에 있으면 다음 화면으로 넘어갈 확률이 달라진다.
_MASCOT_BY_SCORE = {"success": "celebrate", "cheer": "cheer", "comfort": "comfort"}


def render() -> None:
    topbar(active=ss.PAGE_SPEC)
    back_to_hub()
    section_title("스펙 진단 & 추천", icon_name="chart", sub=
                  "내신·자격증·전공 적합성·인재상을 100점 만점으로 환산합니다. "
                  "이 연산은 AI API 호출 없이 로컬에서만 수행되므로 입력 즉시 갱신됩니다.")

    tracker = st.session_state.tracker
    all_cert_names, cert_source = load_cert_names(st.session_state.get("qnet_key", ""))
    tracker.record("Q-Net 자격증", cert_source)

    # ▣ 배치 의도 — 점수가 항상 첫 화면에 온다
    #   이 화면의 존재 이유는 '내 점수가 몇 점인가'다. 그런데 점수는 입력값이
    #   있어야 계산되므로 코드 순서상 뒤에 온다. st.container() 로 화면 위쪽
    #   자리를 먼저 잡아두고 계산이 끝난 뒤 그 자리에 채우면, 실행 순서는
    #   그대로 두고 렌더 위치만 위로 올릴 수 있다.
    #   (이전 배치는 입력 폼이 왼쪽 1.25 · 점수가 오른쪽 1 이라, 모바일에서
    #    1단으로 접히면 점수가 fold 아래 125px 지점에 있었다.)
    score_slot = st.container()

    # ------------------------------------------------------------
    # 입력 — 전체 폭 2열. 한 열에 몰면 세로로 길어져 점수가 밀려난다.
    # ------------------------------------------------------------
    st.markdown("#### 내 현재 스펙 정보 기입")
    in_left, in_right = st.columns(2)

    with in_left:
        dept = st.selectbox("학과/계열 (하이파이브 분류 기준)", DEPARTMENT_LIST,
                            index=DEPARTMENT_LIST.index(st.session_state.dept),
                            key="dept_widget")
        st.session_state.dept = dept

        majors = get_majors_for_department(dept)
        emp_rate = get_employment_rate(dept)
        st.caption(f"세부 전공 예시: {', '.join(majors)}  ·  계열 평균 취업률(예시): **{emp_rate}%**")

        grade = st.slider("내신 성적 등급 (마이스터고 5등급 성취평가제)", 1.0, 5.0,
                          st.session_state.grade, 0.1, key="grade_widget",
                          help="환산식: 30 × (5.0 − 등급) ÷ 4.0  |  1.0등급=30점, 2.0등급=22.5점")
        st.session_state.grade = grade

    with in_right:
        dept_certs = certs_for_department(dept)
        cert_options = sorted(set(dept_certs) | set(all_cert_names))
        certs = st.multiselect(
            "취득 전공 자격증 다중 선택 (Q-Net 기반)", cert_options,
            default=[c for c in st.session_state.user_certs if c in cert_options],
            key="user_certs_widget",
            # Streamlit 기본 placeholder 가 "Choose options" 영문이라
            # 한국어 화면에 영어가 섞인다
            placeholder="자격증을 선택하세요",
        )
        st.session_state.user_certs = certs

        talent_keywords = all_talent_keywords()
        strengths = st.multiselect(
            "나의 핵심 강점 키워드 (기업 인재상 매칭에 사용됨)", talent_keywords,
            default=[k for k in st.session_state.strength_keywords if k in talent_keywords],
            key="strength_keywords_widget",
            help="선택한 키워드가 기업 '인재상'과 일치하면 인재상 점수(10점)에 반영됩니다.",
            placeholder="강점 키워드를 선택하세요",
        )
        st.session_state.strength_keywords = strengths

        company_names = ["선택 안 함 (일반 진단)"] + [c["name"] for c in COMPANY_SHOWCASE]
        pick = st.selectbox("정밀 진단할 목표 기업 (선택)", company_names, key="target_company_widget")
        target_company = None
        if pick != company_names[0]:
            target_company = next(c for c in COMPANY_SHOWCASE if c["name"] == pick)
            st.session_state.selected_company_id = target_company["id"]

        st.caption("※ 입력값을 바꾸면 오른쪽 점수가 **즉시** 갱신됩니다.")

    # ------------------------------------------------------------
    # 점수 (순수 로컬 연산, 과금 0원)
    # ------------------------------------------------------------
    dept_category = get_category(dept)
    result = calc_spec_score(
        grade=grade, user_certs=certs, dept_category=dept_category,
        company=target_company, strength_keywords=strengths,
    )
    st.session_state.last_spec_result = result

    # [Phase 2] 선생님 대시보드에 쓰일 진단 기록.
    # services/activity.py 가 직전 값과 비교해 실제로 바뀐 경우에만 저장하므로,
    # 슬라이더를 드래그해도 디스크 쓰기가 폭주하지 않는다.
    activity.record_spec(result, dept, grade, target_company)

    sticker_key = ogq.sticker_key_for_score(result["final_score"])
    verdict, verdict_msg = ogq.SCORE_STICKER_MESSAGES[sticker_key]
    ring_color = {"success": GREEN, "cheer": GOLD, "comfort": RED}[sticker_key]

    # 화면 맨 위에 잡아둔 자리에 점수를 채운다 (배치 의도는 위 주석 참조)
    with score_slot:
        render_html(f"""
        <div class="mjp-scorecard">
            <span class="mjp-badge" style="background:{ring_color}; color:{BG};">SPEC DIAGNOSIS · 실시간</span>
            <div class="mjp-scorecard-row">
                <div class="mjp-scorering" style="background:{ring_color};">
                    <div class="mjp-scorering-num">{result['final_score']}</div>
                    <div class="mjp-scorering-cap">100점 만점</div>
                </div>
                <div style="flex:1; min-width:210px;">
                    <div class="mjp-verdict" style="color:{ring_color};">{verdict}</div>
                    <div class="mjp-muted" style="margin-top:6px;">{verdict_msg}</div>
                </div>
            </div>
        </div>
        """)

        # 세부 점수 4개는 점수 바로 아래. 가로 2열로 놓아 세로 길이를 줄인다.
        bar_l, bar_r = st.columns(2)
        with bar_l:
            st.markdown(score_bar("내신 성취도", result["grade_score"], 30), unsafe_allow_html=True)
            st.markdown(score_bar("자격증 가산점", result["cert_score"], 40), unsafe_allow_html=True)
        with bar_r:
            st.markdown(score_bar("전공 적합성", result["fit_score"], 20), unsafe_allow_html=True)
            st.markdown(score_bar("인재상 일치도", result["talent_score"], 10), unsafe_allow_html=True)

        if result["cert_details"]:
            with st.expander("자격증 인정 비율 상세 보기", expanded=False):
                for d in result["cert_details"]:
                    mark = "●" if d["ratio"] == 1.0 else ("◐" if d["ratio"] > 0 else "○")
                    extra = f" ← 보유: {d['matched_by']}" if d["matched_by"] and d["ratio"] < 1.0 else ""
                    st.markdown(f"{mark} **{d['cert']}** · {d['status']}{extra}")
                st.caption("정확히 일치 100% · 직무 유사 자격증 70% 인정 → 평균 인정비율 × 40점")

    # 팁과 마스코트는 입력 폼 아래. 점수 블록을 짧게 유지해야 입력까지
    # 첫 화면에 들어온다.
    tip_l, tip_r = st.columns([1, 3])
    with tip_l:
        st.markdown(mascot.html(_MASCOT_BY_SCORE[sticker_key], size=128),
                    unsafe_allow_html=True)
    with tip_r:
        for tip in result["tips"]:
            st.info(tip)

    st.divider()

    # ------------------------------------------------------------
    # Q-Net 가산점 가이드 & 매칭 기업
    # ------------------------------------------------------------
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        st.markdown(f'<span class="mjp-badge" style="background:{BLUE}; color:#fff;">Q-NET</span> '
                    f'**자격 분석 가이드 (예시 가산점)**', unsafe_allow_html=True)
        if not certs:
            st.caption("자격증을 선택하면 기업 규모별 예시 가산점이 즉시 표시됩니다.")
        else:
            size_for_bonus = st.radio("기준 기업 규모", COMPANY_SIZE_TAGS[1:], horizontal=True,
                                      key="qnet_bonus_size", label_visibility="collapsed")
            for cert in certs:
                st.markdown(f"- **{cert}** → {size_for_bonus} 예시 가산점 "
                            f"**+{get_bonus_points(cert, size_for_bonus)}점**")
            st.caption("※ 실제 공식 가산점 규정이 아닌 예시 데이터입니다.")

    with gcol2:
        st.markdown("**매칭 기업 탐색 (실시간 반영)**")
        size_pick = st.radio("기업 규모", COMPANY_SIZE_TAGS[1:], horizontal=True,
                             key="match_size", label_visibility="collapsed")
        matched = [c for c in COMPANY_SHOWCASE
                   if c["category"] == dept_category and c["size_tag"] == size_pick]
        if not matched:
            st.caption("해당 기업군에는 이 학과 계열과 매칭되는 예시 기업이 없습니다. 다른 규모를 선택해보세요.")
        else:
            for c in matched:
                st.markdown(f"**{c['name']}** · {c['description']}  {render_stars(c['overall_rating'])}",
                            unsafe_allow_html=True)
                if st.button(f"{c['name']} 자세히 보기", key=f"match_{c['id']}"):
                    st.session_state.selected_company_id = c["id"]
                    ss.goto(ss.PAGE_GUIDE)
