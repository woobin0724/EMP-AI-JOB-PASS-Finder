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
from services.llm import clear_cover_letter_cache, cost_guard_caption, generate_cover_letter_cached
from ui.components import back_to_hub, section_title, show_sticker, topbar
from ui.theme import BG, BLUE, CARD_BORDER, GREEN, MUTED


def render() -> None:
    topbar(active=ss.PAGE_RESUME)
    back_to_hub()
    section_title("📄 합격 이력서 & 자소서",
                  "내 스펙과 목표 기업의 인재상을 엮어 자기소개서 초안을 생성합니다.")

    left, right = st.columns([1, 1.3])

    with left:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 나의 프로필 & 스토리 연동 기입")

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

        story = st.text_area("나의 고교 이야기 (실패 극복, 동아리 성장 에피소드 등)", height=110)

        gen_clicked = st.button("✨ 스펙 맞춤형 자기소개서 자동 완성", type="primary",
                                use_container_width=True)
        if st.button("♻️ 캐시 비우고 새로 생성", use_container_width=True):
            clear_cover_letter_cache()
            st.toast("캐시를 비웠습니다. 다음 생성은 API를 새로 호출합니다.")

        st.caption(cost_guard_caption())
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        target_company = next(c for c in COMPANY_SHOWCASE if c["name"] == target_company_name)

        if gen_clicked:
            gen_profile = {
                "name": name, "target_dept": target_dept, "grade": st.session_state.grade,
                "story": story,
                "strength": ", ".join(st.session_state.strength_keywords) or story,
                "certs": st.session_state.user_certs,
            }
            with st.spinner("자기소개서 초안을 작성하는 중..."):
                text, source, cache_hit = generate_cover_letter_cached(gen_profile, target_company)
            st.session_state.cover_letter = text
            st.session_state.cover_letter_source = source
            st.session_state.cover_letter_cached = cache_hit
            st.session_state.selected_company_id = target_company["id"]

        badges = ""
        if st.session_state.cover_letter_source == "ai":
            badges += f'<span class="mjp-badge" style="background:{GREEN}; color:{BG};">🤖 AI 생성</span> '
        elif st.session_state.cover_letter_source == "template":
            badges += f'<span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">📐 템플릿 생성</span> '
        if st.session_state.cover_letter_cached:
            badges += f'<span class="mjp-badge" style="background:{BLUE}; color:#fff;">⚡ 캐시 응답 · API 호출 0회</span>'

        st.markdown(f"""
        <div class="mjp-card">
            <span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">DRAFT SHEET</span>
            {badges}
            <div style="font-size:18px; font-weight:800; margin-top:10px;">합격 자기소개서 전문 통합 시트</div>
            <div class="mjp-muted" style="margin-top:4px;">{target_company['name']} 인재상: {', '.join(target_company['ideal_talent'])}</div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.cover_letter:
            icol1, icol2 = st.columns([1, 2])
            with icol1:
                show_sticker("encourage", width=130)
            with icol2:
                st.info("왼쪽에서 정보를 입력하고 '스펙 맞춤형 자기소개서 자동 완성'을 눌러주세요.")
        else:
            st.text_area("자기소개서 초안", value=st.session_state.cover_letter, height=380,
                         label_visibility="collapsed")
            st.download_button("📥 자소서 통합 다운로드 (.txt)", data=st.session_state.cover_letter,
                               file_name="자기소개서_초안.txt", mime="text/plain",
                               use_container_width=True)
