# -*- coding: utf-8 -*-
"""
views/tab_guide.py
기능 3. 채용 대비 가이드 & 커리큘럼 (+ 커리어 로드맵 마일스톤 스탬프)

원본 app.py 의 TAB 3 블록 이관.
Phase 4(OGQ API 게이미피케이션)에서 이 파일의 마일스톤 영역이 확장된다.
"""

import os

import streamlit as st

from core import session as ss
from ui import mascot
from core.catalog import completed_milestones
from data.company_showcase import COMPANY_BY_ID, COMPANY_SHOWCASE
from data.roadmap import MILESTONES, stage_label
from services import activity
from services.curriculum import generate_curriculum
from services.pdf_report import build_success_report_pdf
from ui.components import back_to_hub, disclaimer, section_title, topbar
from ui.theme import CARD_BORDER, GREEN, MUTED, RED, TEXT, render_stars

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# [Phase 4] 마일스톤 → 마스코트 감정 슬롯
# 스티커 팩에 단계별로 다른 낱장이 있으면 assets/mascot/manifest.json 의
# slots 에 매핑해 두면 된다. 매핑이 없으면 같은 이미지가 나오고,
# 아래 응원 문구로 단계를 구분한다.
MILESTONE_MASCOT = {
    "cert": "celebrate",
    "portfolio": "cheer",
    "interview": "encourage",
}
MILESTONE_CHEER = {
    "cert": "자격증 준비 완료! 첫 단추를 잘 끼웠어요",
    "portfolio": "포트폴리오 완성! 이제 보여줄 게 생겼네요",
    "interview": "면접 준비 완료! 자신 있게 들어가세요",
}


def render() -> None:
    topbar(active=ss.PAGE_GUIDE)
    back_to_hub()
    section_title("채용 대비 가이드 & 커리큘럼", icon_name="wrench", sub=
                  "목표 기업의 면접 기출·필기 키워드·4주 커리큘럼을 확인하고, "
                  "커리어 로드맵 3단계를 스탬프로 관리하세요.")

    disclaimer("선배 리뷰·면접질문·커리큘럼은 팀이 구성한 예시 콘텐츠이며 실제 후기가 아닙니다.")

    names = {c["name"]: c["id"] for c in COMPANY_SHOWCASE}
    default_name = (COMPANY_BY_ID[st.session_state.selected_company_id]["name"]
                    if st.session_state.selected_company_id else list(names.keys())[0])
    pick_name = st.selectbox("기업별 원스톱 채용 가이드 허브", list(names.keys()),
                             index=list(names.keys()).index(default_name))
    c = COMPANY_BY_ID[names[pick_name]]
    st.session_state.selected_company_id = c["id"]

    # [Phase 3] 열람 이력 — 같은 기업은 최근 1건으로 합쳐진다
    activity.record_company_view(c)

    _roadmap(c)
    st.divider()
    _company_detail(c)
    _pdf_report(c)


# ------------------------------------------------------------
# 커리어 로드맵 — 3단계 마일스톤 + OGQ 스탬프
# ------------------------------------------------------------
def _roadmap(company: dict) -> None:
    st.markdown("### 나의 커리어 로드맵")
    done = completed_milestones(st.session_state.milestones)
    st.progress(done / len(MILESTONES), text=f"{done} / {len(MILESTONES)} 단계 완료")

    mcols = st.columns(3)
    for i, (key, label, desc) in enumerate(MILESTONES):
        with mcols[i]:
            checked = st.checkbox(f"**{label}**", value=st.session_state.milestones[key],
                                  key=f"ms_{key}")
            st.session_state.milestones[key] = checked
            st.caption(desc)
            if checked:
                # [Phase 4] 달성 시 마스코트가 축하한다.
                # 단계마다 다른 낱장이 있으면 그것을, 없으면 같은 이미지에
                # 문구로 차별화한다 (매니페스트 slots 에 단계별 매핑을 넣으면
                # 아래 MILESTONE_MASCOT 이 자동으로 다른 감정을 집는다).
                st.markdown(
                    f'<div style="display:flex; justify-content:center;">'
                    f'{mascot.html(MILESTONE_MASCOT.get(key, "celebrate"), size=112)}</div>',
                    unsafe_allow_html=True)
                st.markdown(
                    f'<div style="text-align:center; color:{GREEN}; font-size:12.5px; '
                    f'font-weight:700; margin-top:6px;">{MILESTONE_CHEER[key]}</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="height:126px; border:1px dashed {CARD_BORDER}; border-radius:12px;'
                    f'display:flex; align-items:center; justify-content:center; color:{MUTED};'
                    f'font-size:12px;">달성하면 마스코트가 축하해요</div>', unsafe_allow_html=True)

    # [Phase 2] 로드맵 진행 단계 저장 — 체크박스 3개를 모두 반영한 뒤 한 번만 호출한다.
    # 루프 안에서 부르면 한 번의 rerun 에 세 번 저장하게 된다.
    activity.record_milestones(st.session_state.milestones)

    if done == len(MILESTONES):
        mascot.speech("celebrate",
                      "<b>세 단계를 모두 완주했어요!</b><br>"
                      "자격증·포트폴리오·면접 준비가 끝났습니다. 이제 실제 지원서를 넣을 차례예요.",
                      tone="success", size=100)
    else:
        consultant = {
            0: "먼저 목표 기업이 요구하는 자격증부터 확인해봅시다. 아래 '필수 우대 자격증'을 보세요.",
            1: "좋아요! 이제 아래 4주 커리큘럼으로 포트폴리오를 만들어봅시다.",
            2: "포트폴리오까지 완성했네요. 마지막으로 예상 면접 질문에 답을 만들어보세요.",
        }[done]
        st.info(f"AI 컨설턴트: {consultant}")


# ------------------------------------------------------------
# 기업 상세 + 커리큘럼
# ------------------------------------------------------------
def _company_detail(c: dict) -> None:
    st.markdown(f"""
    <div class="mjp-card">
        <span class="mjp-tag">{c['size_tag']} · {c['field_tag']} 타깃</span>
        <div style="font-size:24px; font-weight:800; margin-top:8px;">{c['name']}</div>
        <div class="mjp-muted">{c['description']} · 고졸 채용 종합 만족도 예시 {render_stars(c['overall_rating'])}</div>
        <div class="mjp-muted" style="margin-top:6px;">인재상: <b style="color:{TEXT};">{', '.join(c['ideal_talent'])}</b>
        &nbsp;|&nbsp; 예시 합격자 평균 스펙: 내신 {c['avg_applicant_grade']}등급 · 자격증 {c['avg_applicant_certs']}개</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(key="mjp_row_guide_actions"):
        gb1, gb2 = st.columns([1, 1.6])
        with gb1:
            marked = activity.is_bookmarked(c["id"])
            if st.button("찜 해제" if marked else "찜하기",
                         key="guide_fav", use_container_width=True,
                         type="primary" if marked else "secondary"):
                activity.toggle_bookmark(c["id"])
                st.rerun()
        with gb2:
            if st.button("이 회사로 자소서 쓰기", type="primary",
                         use_container_width=True, key="guide_to_resume"):
                ss.goto(ss.PAGE_RESUME)

    st.markdown("##### 고졸 출신 선배들의 직무별 세부 평점 (예시)")
    rcols = st.columns(3)
    for i, (label, val) in enumerate(c["ratings"].items()):
        with rcols[i]:
            st.markdown(f"""<div class="mjp-card" style="text-align:center;">
                <div class="mjp-muted">{label}</div><div style="margin-top:6px;">{render_stars(val)}</div>
            </div>""", unsafe_allow_html=True)

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        st.markdown(f"""<div class="mjp-card" style="border-color:{GREEN};">
            <b style="color:{GREEN};">● 장점 (예시)</b>
            <div class="mjp-muted" style="margin-top:8px; color:{TEXT};">{c['pros']}</div></div>""",
                    unsafe_allow_html=True)
    with pcol2:
        st.markdown(f"""<div class="mjp-card" style="border-color:{RED};">
            <b style="color:{RED};">● 단점/고충 (예시)</b>
            <div class="mjp-muted" style="margin-top:8px; color:{TEXT};">{c['cons']}</div></div>""",
                    unsafe_allow_html=True)

    kcol1, kcol2 = st.columns(2)
    with kcol1:
        tags = "".join(f'<span class="mjp-tag">{ct}</span>' for ct in c["required_certs"])
        st.markdown(f'<div class="mjp-card"><b>필수 우대 자격증</b><br><br>{tags}</div>',
                    unsafe_allow_html=True)
    with kcol2:
        st.markdown(f"""<div class="mjp-card"><b>전공 필기시험 핵심 키워드</b>
            <div class="mjp-muted" style="margin-top:8px; color:{TEXT};">{c['exam_keywords']}</div></div>""",
                    unsafe_allow_html=True)

    st.markdown("##### 예상 기출 면접 질문 3선 (예시)")
    for i, q in enumerate(c["interview_questions"]):
        st.markdown(
            f'<div class="mjp-interview"><span class="mjp-qbadge">인터뷰 질문 {i + 1:02d}</span>Q. {q}</div>',
            unsafe_allow_html=True)

    st.markdown("##### 코멘토 스타일 4주 맞춤 커리큘럼 (예시)")
    curriculum = generate_curriculum(c)
    st.session_state.last_curriculum = curriculum
    for wk in curriculum:
        with st.expander(f"{wk['week']}주차 · {wk['title']}"):
            st.write(f"**학습 목표**: {wk['goal']}")
            st.write("**이번 주 할 일**")
            for t in wk["tasks"]:
                st.write(f"- {t}")
            st.write(f"**추천 프로젝트**: {wk['project']}")
            st.info(f"포트폴리오 전략: {wk['portfolio_tip']}")


# ------------------------------------------------------------
# PDF 리포트
# ------------------------------------------------------------
def _pdf_report(c: dict) -> None:
    st.divider()
    student_name = st.session_state.student_name or ss.display_name() or "학생"

    if st.button("나만의 취업 성공 리포트 PDF 만들기"):
        cover_excerpt = (st.session_state.cover_letter
                         or "(자기소개서 기능에서 먼저 생성하면 리포트에 포함됩니다.)")
        try:
            pdf_bytes = build_success_report_pdf(
                base_dir=BASE_DIR, student_name=student_name, company=c,
                spec_result=st.session_state.last_spec_result or {
                    "grade_score": 0, "cert_score": 0, "fit_score": 0,
                    "talent_score": 0, "final_score": 0,
                },
                curriculum=st.session_state.last_curriculum or generate_curriculum(c),
                cover_letter_excerpt=cover_excerpt,
                roadmap_stage_label=stage_label(completed_milestones(st.session_state.milestones)),
            )
            st.download_button("PDF 다운로드", data=pdf_bytes,
                               file_name=f"{student_name}_취업성공리포트.pdf",
                               mime="application/pdf")
            if not os.path.exists(os.path.join(BASE_DIR, "fonts", "NanumGothic.ttf")):
                st.caption("한글이 깨져 보인다면 `fonts/NanumGothic.ttf`를 프로젝트에 추가하세요.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"PDF 생성 중 문제가 발생했습니다: {exc}")
