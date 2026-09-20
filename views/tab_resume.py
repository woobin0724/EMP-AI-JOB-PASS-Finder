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
from core.catalog import all_talent_keywords
from data.company_showcase import COMPANY_BY_ID, COMPANY_SHOWCASE, all_companies
from services.coverletter import LENGTH_OPTIONS, TONE_OPTIONS, angle_for, normalize_options
from services import review as review_svc
from services.llm import (
    clear_cover_letter_cache, cost_guard_caption, current_variation,
    generate_cover_letter_cached, last_api_failure, next_variation, reset_variation,
)
from ui import mascot
from ui.components import back_to_hub, render_html, section_title, topbar
from ui.theme import BG, BLUE, BRAND, CARD_BORDER, GOLD, GREEN, MUTED


def render() -> None:
    topbar(active=ss.PAGE_RESUME)
    back_to_hub()
    section_title("합격 이력서 & 자소서", icon_name="file", sub=
                  "스펙으로 <b>새로 쓰거나</b>, 직접 쓴 초안을 <b>첨삭받거나</b>. "
                  "둘 다 같은 화면에서 합니다.")

    # 생성과 첨삭은 하는 일이 다르다 — 재료로 글을 만드는 것과, 이미 있는
    # 글을 읽고 고칠 곳을 짚는 것. 탭으로 갈라 서로 섞이지 않게 한다.
    gen_tab, review_tab = st.tabs(["자소서 생성", "내 초안 첨삭"])

    with review_tab:
        _render_review()

    with gen_tab:
        _render_generator()


def _render_generator() -> None:
    left, right = st.columns([1, 1.3])

    with left:
        # ▣ 입력을 세 구획으로 나눈다
        #   9개 항목이 한 줄로 이어지면 어디까지가 필수인지 알 수 없어
        #   학생이 첫 칸에서 멈춘다. 필수 / 글을 바꾸는 재료 / 형식 옵션으로
        #   끊어, 필수만 채워도 생성이 된다는 것이 보이게 한다.
        st.markdown("#### 나의 프로필")
        st.caption("이 세 가지만 채워도 초안이 나옵니다.")

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
        # 아래 칸들이 '그 학생만의 글'을 만드는 재료다.
        st.markdown("#### 글을 바꾸는 재료")
        st.caption("선택이지만, 하나만 채워도 남들과 다른 자소서가 됩니다.")

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

        # 라벨을 숨기면 컨트롤 높이가 눌려 모바일 터치 타깃이 44px 아래로 떨어진다
        # (실측 38px). 모바일에서는 컬럼이 1단으로 접히므로 라벨을 보여주는 편이
        # 공간 손해도 없고 무엇을 고르는지도 분명해진다.
        st.markdown("#### 형식")
        ocol1, ocol2 = st.columns(2)
        with ocol1:
            tone = st.radio("문체", list(TONE_OPTIONS.keys()), horizontal=True,
                            key="cl_tone")
        with ocol2:
            length = st.selectbox(
                "분량", list(LENGTH_OPTIONS.keys()), index=1,
                format_func=lambda n: LENGTH_OPTIONS[n]["label"],
                key="cl_length",
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

        # 키를 넣었는데도 템플릿이 나왔다면 이유를 드러낸다 (조용한 폴백 방지)
        api_error = last_api_failure()
        if api_error and st.session_state.cover_letter_source == "template":
            st.warning(f"API 키는 있으나 호출에 실패해 템플릿으로 생성했습니다 — {api_error}")

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

        # ▣ 들여쓰기 금지
        #   markdown 은 4칸 이상 들여쓴 줄을 코드 블록으로 해석한다. 이 블록을
        #   12칸 들여썼더니 안쪽 <div> 한 줄이 화면에 **원시 HTML 텍스트로**
        #   그대로 노출됐다. 그래서 들여쓰기 없이 조립한다.
        st.markdown(
            '<div class="mjp-card">'
            f'<span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">DRAFT SHEET</span> '
            f'{badges}'
            '<div style="font-size:var(--mjp-h2); font-weight:800; margin-top:10px;">'
            '합격 자기소개서 전문 통합 시트</div>'
            f'<div class="mjp-muted" style="margin-top:4px;">{target_company["name"]} 인재상: '
            f'{", ".join(target_company["ideal_talent"])}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

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


# ------------------------------------------------------------
# [Phase D-2] 내 초안 첨삭
# ------------------------------------------------------------
def _render_review() -> None:
    """학생이 직접 쓴 자소서를 읽고 피드백을 준다."""
    st.markdown("#### 직접 쓴 자소서를 붙여넣으세요")
    st.caption("잘된 점과 고칠 점을 짚어드립니다. 글을 대신 써주지는 않습니다 — "
               "학생이 쓴 글이 더 나아지도록 돕는 것이 목적입니다.")

    draft = st.text_area(
        "자소서 초안", height=260, key="review_draft",
        placeholder="지금까지 쓴 자소서를 그대로 붙여넣어주세요. "
                    f"{review_svc.MIN_CHARS}자 이상이면 첨삭할 수 있어요.",
    )

    rc1, rc2 = st.columns(2)
    with rc1:
        # all_companies() 는 큐레이션 JSON 을 읽으므로 한 번만 부른다
        companies = all_companies()
        names = ["선택 안 함"] + [c["name"] for c in companies]
        pick = st.selectbox("지원 기업 (선택)", names, key="review_company")
        target = None
        if pick != names[0]:
            target = next(c for c in companies if c["name"] == pick)
    with rc2:
        strengths = st.multiselect(
            "강점 키워드 (선택)", all_talent_keywords(),
            default=list(st.session_state.get("strength_keywords") or []),
            key="review_strengths", placeholder="강점을 골라주세요",
        )

    st.caption(f"현재 {len(draft.strip())}자")

    if st.button("첨삭 받기", type="primary", use_container_width=True,
                 key="review_run"):
        problem = review_svc.validate_draft(draft)
        if problem:
            st.error(problem)
        else:
            with st.spinner("초안을 읽는 중..."):
                feedback, source = review_svc.review(draft, target, strengths)
            st.session_state["review_result"] = feedback
            st.session_state["review_source"] = source

    feedback = st.session_state.get("review_result")
    if not feedback:
        mascot.speech("thinking",
                      "초안을 붙여넣고 <b>'첨삭 받기'</b>를 눌러주세요. "
                      "지원 기업까지 고르면 그 기업 인재상에 맞춰 봐드려요.",
                      tone="brand", size=88)
        return

    source = st.session_state.get("review_source", "rule")
    badge = "AI 첨삭" if source == "ai" else "규칙 기반 점검"
    badge_bg = BLUE if source == "ai" else CARD_BORDER
    badge_fg = "#fff" if source == "ai" else MUTED

    render_html(f"""
    <div style="margin-bottom:12px;">
        <span class="mjp-badge" style="background:{badge_bg}; color:{badge_fg};">{badge}</span>
    </div>
    """)

    if source == "rule":
        st.caption("API 키가 없어 기계가 셀 수 있는 항목만 점검했습니다 — "
                   "분량·상투어·문장 길이·구체적 근거·인재상 반영 여부.")
    failure = review_svc.last_failure()
    if failure and source == "rule":
        st.warning(f"API 키는 있으나 첨삭에 실패해 규칙 점검으로 표시했습니다 — {failure}")

    if feedback.get("raw"):
        # 출력 형식이 어긋난 경우 — 통째로 보여주되 버리지는 않는다
        st.markdown(feedback["raw"])
        return

    if feedback.get("good"):
        items = "".join(f"<li style='margin-bottom:8px;'>{g}</li>"
                        for g in feedback["good"])
        render_html(f"""
        <div class="mjp-card" style="border-color:{GREEN};">
            <div style="font-weight:800; color:{GREEN};">잘된 점</div>
            <ul style="margin:10px 0 0; padding-left:20px; line-height:1.7;">{items}</ul>
        </div>
        """)

    if feedback.get("improve"):
        items = "".join(f"<li style='margin-bottom:10px;'>{g}</li>"
                        for g in feedback["improve"])
        render_html(f"""
        <div class="mjp-card" style="border-color:{GOLD};">
            <div style="font-weight:800; color:{GOLD};">이렇게 고쳐보세요</div>
            <ul style="margin:10px 0 0; padding-left:20px; line-height:1.7;">{items}</ul>
        </div>
        """)

    if feedback.get("example"):
        render_html(f"""
        <div class="mjp-card" style="border-color:{BRAND};">
            <div style="font-weight:800; color:{BRAND};">예시 문장</div>
            <div style="margin-top:10px; line-height:1.7;">{feedback['example']}</div>
        </div>
        """)
