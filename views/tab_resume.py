# -*- coding: utf-8 -*-
"""
views/tab_resume.py
기능 4. 합격 이력서 & 자소서

원본 app.py 의 TAB 4 블록 이관.
Phase 5(템플릿 탈피 · 프롬프트 재설계)에서 이 화면의 입력 항목과
services/llm.py 호출부가 확장된다.
"""

import streamlit as st

from core import session as ss
from data.company_showcase import COMPANY_BY_ID, COMPANY_SHOWCASE
from services.coverletter import LENGTH_OPTIONS, TONE_OPTIONS, angle_for, normalize_options
from services.llm import (
    clear_cover_letter_cache, cost_guard_caption, current_variation,
    generate_cover_letter_cached, next_variation, reset_variation,
)
from ui import mascot
from ui.components import back_to_hub, section_title, topbar
from ui.theme import BG, BLUE, CARD_BORDER, GREEN, MUTED


def render() -> None:
    topbar(active=ss.PAGE_RESUME)
    back_to_hub()
    section_title("합격 이력서 & 자소서", icon_name="file", sub=
                  "내 스펙과 목표 기업의 인재상을 엮어 자기소개서 초안을 생성합니다.")

    left, right = st.columns([1, 1.3])

    with left:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown("#### 나의 프로필 & 스토리 연동 기입")

        name = st.text_input("학생 이름",
                             value=st.session_state.student_name or ss.display_name(),
                             placeholder="예: 김우빈")
        target_dept = st.text_input("목표 입사 지원 부서", placeholder="예: 공정설비제어팀 엔지니어")

        company_names = [c["name"] for c in COMPANY_SHOWCASE]
        default_idx = 0
        if st.session_state.selected_company_id:
            comp = COMPANY_BY_ID[st.session_state.selected_company_id]
            if comp["name"] in company_names:
                default_idx = company_names.index(comp["name"])
        target_company_name = st.selectbox("목표 지원 회사", company_names, index=default_idx)

        # ---- [Phase 5] 확장 입력 ----
        # 이름·기업·강점만으로는 모든 학생의 자소서가 같아진다.
        # 아래 두 칸이 '그 학생만의 글'을 만드는 재료다.
        episode = st.text_area(
            "관련 경험이나 에피소드 (선택, 있으면 글이 완전히 달라집니다)",
            height=100,
            placeholder="예: 3학년 실습에서 치수가 계속 0.05mm씩 어긋났는데, "
                        "공구 마모를 의심하고 측정 기록을 3일간 남겨 원인을 찾았습니다.",
            help="구체적인 장면일수록 좋습니다. 비워두면 자격증과 직무를 연결해 씁니다.",
        )
        motive = st.text_input(
            "지원 동기 키워드 (선택)",
            placeholder="예: 정밀가공, 설비 자동화, 안전관리 체계",
        )
        story = st.text_area("고교 생활 이야기 (선택)", height=80,
                             placeholder="동아리·자격증 준비 과정 등")

        st.markdown("###### 문체와 분량")
        ocol1, ocol2 = st.columns(2)
        with ocol1:
            tone = st.radio("문체", list(TONE_OPTIONS.keys()), horizontal=True,
                            label_visibility="collapsed", key="cl_tone")
        with ocol2:
            length = st.selectbox(
                "분량", list(LENGTH_OPTIONS.keys()), index=1,
                format_func=lambda n: LENGTH_OPTIONS[n]["label"],
                label_visibility="collapsed", key="cl_length",
            )
        st.caption(f"구성: {LENGTH_OPTIONS[length]['structure']}")

        # 입력이 바뀌면 회차를 0으로 되돌린다.
        # 그래야 '다시 생성하기'를 눌렀던 상태가 새 입력에 묻어나지 않는다.
        input_signature = (name, target_dept, target_company_name, episode, motive,
                           story, tone, length)
        if st.session_state.get("_cl_input_sig") != input_signature:
            st.session_state["_cl_input_sig"] = input_signature
            reset_variation()

        gen_clicked = st.button("스펙 맞춤형 자기소개서 자동 완성", type="primary",
                                use_container_width=True)
        regen_clicked = st.button("다시 생성하기 (다른 구성으로)",
                                  use_container_width=True,
                                  help="같은 재료로 서사 구성을 바꿔 새 초안을 만듭니다. "
                                       "캐시를 우회해 새로 생성합니다.")

        with st.expander("고급"):
            if st.button("캐시 전체 비우기", use_container_width=True):
                clear_cover_letter_cache()
                reset_variation()
                st.toast("캐시를 비웠습니다. 다음 생성은 API를 새로 호출합니다.")
            st.caption("보통은 '다시 생성하기'면 충분합니다. 캐시를 통째로 비우면 "
                       "이전 회차 초안까지 사라져 되돌아올 때 API를 다시 호출합니다.")

        st.caption(cost_guard_caption())
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        target_company = next(c for c in COMPANY_SHOWCASE if c["name"] == target_company_name)

        if regen_clicked:
            next_variation()      # 회차 +1 → 캐시 키가 바뀌어 새 구성으로 생성된다

        if gen_clicked or regen_clicked:
            gen_profile = {
                "name": name, "target_dept": target_dept, "grade": st.session_state.grade,
                "story": story, "episode": episode, "motive": motive,
                "strength": ", ".join(st.session_state.strength_keywords) or story,
                "certs": st.session_state.user_certs,
            }
            gen_options = {"tone": tone, "length": length,
                           "variation": current_variation()}
            with st.spinner("자기소개서 초안을 작성하는 중..."):
                text, source, cache_hit = generate_cover_letter_cached(
                    gen_profile, target_company, gen_options)
            st.session_state.cover_letter = text
            st.session_state.cover_letter_source = source
            st.session_state.cover_letter_cached = cache_hit
            st.session_state.cover_letter_options = normalize_options(gen_options)
            st.session_state.selected_company_id = target_company["id"]

        badges = ""
        if st.session_state.cover_letter_source == "ai":
            badges += f'<span class="mjp-badge" style="background:{GREEN}; color:{BG};">AI 생성</span> '
        elif st.session_state.cover_letter_source == "template":
            badges += f'<span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">템플릿 생성</span> '
        if st.session_state.cover_letter_cached:
            badges += f'<span class="mjp-badge" style="background:{BLUE}; color:#fff;">캐시 응답 · API 호출 0회</span> '
        opts = st.session_state.get("cover_letter_options")
        if opts:
            badges += (f'<span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">'
                       f'{opts["tone"]} · {opts["length"]}자 · {opts["variation"] + 1}회차</span>')

        st.markdown(f"""
        <div class="mjp-card">
            <span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">DRAFT SHEET</span>
            {badges}
            <div style="font-size:18px; font-weight:800; margin-top:10px;">합격 자기소개서 전문 통합 시트</div>
            <div class="mjp-muted" style="margin-top:4px;">{target_company['name']} 인재상: {', '.join(target_company['ideal_talent'])}</div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.cover_letter:
            mascot.speech("encourage",
                          "왼쪽에서 정보를 입력하고 <b>'스펙 맞춤형 자기소개서 자동 완성'</b>을 "
                          "눌러주세요. 에피소드를 적으면 글이 확 달라져요!",
                          tone="brand", size=88)
        else:
            st.text_area("자기소개서 초안", value=st.session_state.cover_letter, height=380,
                         label_visibility="collapsed")
            st.download_button("자소서 통합 다운로드 (.txt)", data=st.session_state.cover_letter,
                               file_name="자기소개서_초안.txt", mime="text/plain",
                               use_container_width=True)
            opts = st.session_state.get("cover_letter_options")
            if opts:
                st.caption(f"이번 초안의 구성: {angle_for(opts['variation'])}")
                st.caption("마음에 들지 않으면 '다시 생성하기'를 누르세요. "
                           "같은 재료로 다른 구성의 초안이 나옵니다.")
