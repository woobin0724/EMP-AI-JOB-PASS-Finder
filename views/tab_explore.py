# -*- coding: utf-8 -*-
"""
views/tab_explore.py
기능 2. 실시간 기업 탐색기 (고용24 + 잡알리오 + 강소기업 통합 검색)

원본 app.py 의 TAB 2 블록 이관. 검색/필터 로직은 그대로 두고 화면 진입 방식과
모바일 레이아웃(기업 카드 3단 → 폰에서 1단)만 조정했다.
"""

import streamlit as st

from core import session as ss
from core.matching import filter_results
from data.company_showcase import COMPANY_CATEGORIES, COMPANY_SHOWCASE
from services import activity
from services import fallback as fb
from services.strong_sme_api import PRIORITY_DEPARTMENTS, prioritize_by_department
from ui import mascot
from ui.components import back_to_hub, disclaimer, grid_columns, render_html, section_title, topbar
from ui.icons import icon
from ui.theme import BADGE_COLORS, BG, GREEN, RED, TEXT, render_stars


def render() -> None:
    topbar(active=ss.PAGE_EXPLORE)
    back_to_hub()
    section_title("실시간 기업 탐색기", icon_name="search", sub=
                  "공공·민간 채용 포털을 동시에 호출합니다. 응답하지 않는 소스는 "
                  "즉시 백업 마스터 데이터로 전환되어 화면이 비지 않습니다.")

    disclaimer("기업 카드(별점·복지 등)는 예시(모의) 데이터입니다. "
               "하단 '실시간 채용공고'는 실제 API 연동을 시도하고, 실패 시 백업 데이터로 전환됩니다.")

    tracker = st.session_state.tracker

    # ------------------------------------------------------------
    # 실시간 통합 검색 — 이 화면의 이름값을 하는 기능이라 맨 위에 둔다.
    # (이전 배치는 쇼케이스 카드 20장 뒤였고, 모바일에서 fold +5574px,
    #  즉 8화면쯤 내려가야 검색창이 나왔다.)
    # ------------------------------------------------------------
    st.markdown("#### 실시간 채용 공고 통합 검색 (고용24 + 잡알리오 + 강소기업)")
    st.caption("세 소스를 동시에 호출하고, 응답하지 않는 소스는 즉시 백업 마스터 데이터로 대체합니다. "
               "기계·전기·제조·IT 전공 연관 강소기업 공고는 상단에 우선 노출됩니다.")

    # 키워드 · 유형 · 실행을 한 줄로 묶어 검색이 한 덩어리로 읽히게 한다
    with st.container(key="mjp_searchbar"):
        kcol, tcol, bcol = st.columns([2.2, 1.2, 1])
        with kcol:
            kw = st.text_input("검색 키워드 (기업명·공고명·자격증)",
                               placeholder="예: 전기기능사, CNC, 정보처리, 한국전력공사")
        with tcol:
            type_pick = st.selectbox("기업 유형",
                                     ["전체", "대기업", "중견기업", "중소기업",
                                      "스타트업", "공기업", "강소기업"])
        with bcol:
            st.markdown('<div class="mjp-btn-align"></div>', unsafe_allow_html=True)
            fetch = st.button("지금 불러오기", type="primary", use_container_width=True)

    if fetch:
        with st.spinner("고용24·잡알리오·강소기업 포털 호출 중... 실패 시 백업 데이터로 자동 전환됩니다."):
            worknet_df, _ = fb.fetch_jobs_safe(
                st.session_state.get("worknet_key", ""), kw, tracker=tracker)
            alio_records, _ = fb.fetch_alio_safe(tracker=tracker)
            sme_records, _ = fb.fetch_strong_sme_safe(tracker=tracker)

        worknet_records = (worknet_df.to_dict("records")
                           if hasattr(worknet_df, "to_dict") else list(worknet_df))
        alio_records = filter_results(alio_records, kw)
        sme_records = prioritize_by_department(filter_results(sme_records, kw))

        st.session_state.live_jobs = worknet_records + alio_records + sme_records
        st.rerun()

    if st.session_state.live_jobs is not None:
        st.markdown(fb.badge_html(tracker, BADGE_COLORS), unsafe_allow_html=True)
        for name, err in tracker.errors():
            st.caption(f"{name}: {err} → 백업 데이터로 전환됨")

        records = st.session_state.live_jobs
        if type_pick != "전체":
            records = [r for r in records if r.get("company_type") == type_pick]

        if not records:
            st.warning("검색 결과가 없습니다. 다른 키워드나 기업 유형으로 다시 시도해보세요.")
            st.markdown(mascot.html("thinking", size=110), unsafe_allow_html=True)
        else:
            st.caption(f"검색 결과 {len(records)}건")
            for r in records:
                certs_list = r.get("required_certs") or []
                cert_str = ", ".join(certs_list) if certs_list else "정보 없음"
                priority_badge = (
                    f' <span class="mjp-tag" style="background:{GREEN}; color:{BG};">전공 우선매칭</span>'
                    if r.get("company_type") == "강소기업" and r.get("department") in PRIORITY_DEPARTMENTS
                    else ""
                )
                render_html(f"""
                <div class="mjp-card">
                    <span class="mjp-tag">{r.get('company_type', '')}</span>{priority_badge}
                    <div style="font-size:var(--mjp-body); font-weight:800; margin-top:6px;">{r.get('company', '')}</div>
                    <div class="mjp-muted">{r.get('title', '')} · {r.get('region', '')} {r.get('salary', '')}</div>
                    <div class="mjp-muted" style="margin-top:4px;">필수/우대 자격증: {cert_str}</div>
                </div>
                """)
                if r.get("ai_tip"):
                    st.info(r["ai_tip"])

    st.divider()

    # ------------------------------------------------------------
    # 기업 카드 데이터베이스 — 참고용이므로 실시간 검색 아래로 내렸다
    # ------------------------------------------------------------
    st.markdown("#### 전국 주요 계열 연계 Meister 모의 채용 기업 데이터베이스")

    cat = st.radio("분야", COMPANY_CATEGORIES, horizontal=True, label_visibility="collapsed")
    shown = COMPANY_SHOWCASE if cat == "전체" else [c for c in COMPANY_SHOWCASE if c["category"] == cat]

    # 카드 20장을 한 번에 펼치면 모바일에서 화면 8개 분량이 된다.
    # 처음에는 9장만 보여주고 나머지는 눌러서 펼치게 한다.
    INITIAL = 9
    if len(shown) > INITIAL and not st.session_state.get("explore_show_all"):
        hidden = len(shown) - INITIAL
        shown = shown[:INITIAL]
    else:
        hidden = 0

    # 행 단위 컬럼 — 모바일 1단 전환 시 기업 순서 보존
    for col, c in zip(grid_columns(len(shown), 3), shown):
        with col:
            heart = (icon("heart", size=15, color=RED, filled=True)
                     if activity.is_bookmarked(c["id"]) else "")
            render_html(f"""
            <div class="mjp-card">
                <span class="mjp-tag">{c['size_tag']} · {c['field_tag']}</span>
                <span style="float:right; display:inline-flex; align-items:center; gap:6px;">
                    {render_stars(c['overall_rating'])}{heart}
                </span>
                <div style="font-size:var(--mjp-h2); font-weight:800; margin-top:8px;">{c['name']}</div>
                <div class="mjp-muted" style="margin-bottom:8px;">{c['description']}</div>
                <div class="mjp-muted">인재상<br><b style="color:{TEXT};">{', '.join(c['ideal_talent'])}</b></div>
                <div class="mjp-muted" style="margin-top:6px;">독점 복지 혜택<br>
                    <span style="color:{TEXT};">{c['benefit_short']}</span>
                </div>
            </div>
            """)
            # 버튼 줄은 mjp_row_ 컨테이너로 감싸 모바일에서도 가로로 유지한다
            with st.container(key=f"mjp_row_card_{c['id']}"):
                bc1, bc2, bc3 = st.columns([0.7, 1.2, 1.2])
                with bc1:
                    marked = activity.is_bookmarked(c["id"])
                    # Streamlit 버튼은 SVG 를 못 넣는다 → 상태는 위 카드의 하트 아이콘이,
                    # 동작은 이 텍스트 버튼이 담당한다.
                    if st.button("찜 해제" if marked else "찜하기",
                                 key=f"fav_{c['id']}", use_container_width=True,
                                 type="primary" if marked else "secondary"):
                        activity.toggle_bookmark(c["id"])
                        st.rerun()
                with bc2:
                    if st.button("합격 정보", key=f"info_{c['id']}", use_container_width=True):
                        st.session_state.selected_company_id = c["id"]
                        ss.goto(ss.PAGE_GUIDE)
                with bc3:
                    if st.button("자소서", key=f"resume_{c['id']}", use_container_width=True):
                        st.session_state.selected_company_id = c["id"]
                        ss.goto(ss.PAGE_RESUME)

    if hidden:
        if st.button(f"기업 {hidden}곳 더 보기", use_container_width=True, key="explore_more"):
            st.session_state.explore_show_all = True
            st.rerun()

