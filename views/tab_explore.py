# -*- coding: utf-8 -*-
"""
views/tab_explore.py
기능 2. 기업 탐색기 (고용24 + 공기업 + 강소기업 통합 검색 — 백업 데이터 기반)

원본 app.py 의 TAB 2 블록 이관. 검색/필터 로직은 그대로 두고 화면 진입 방식과
모바일 레이아웃(기업 카드 3단 → 폰에서 1단)만 조정했다.
"""


import streamlit as st

from core import session as ss
from core.matching import filter_results
from core import company_filter as cf
from data.company_showcase import all_companies
from services import activity
from services import fallback as fb
from services import reactions
from services import story_cards
from services.strong_sme_api import PRIORITY_DEPARTMENTS, prioritize_by_department
from ui import mascot
from ui.components import (
    back_to_hub, data_kind_chip, grid_columns, render_html, sample_notice, section_title,
    source_links, topbar,
)
from ui.icons import icon
from ui.story_viewer import render_story
from ui.theme import BG, GREEN, MUTED, RED, TEXT, render_stars


def render() -> None:
    topbar(active=ss.PAGE_EXPLORE)
    back_to_hub()
    section_title("기업 탐색기", icon_name="search", eyebrow="기업 탐색", sub=
                  "채용공고를 한곳에서 검색합니다. 공공 채용 정보 연동은 아직 검증 전이라, "
                  "지금은 팀이 만든 예시 공고를 보여줍니다.")

    sample_notice()

    # 기업 스토리 — 카드 한 장씩 넘기며 훑어보는 진입점이라 맨 위에 둔다
    _render_story_section()
    st.divider()

    tracker = st.session_state.tracker

    # ------------------------------------------------------------
    # 채용공고 통합 검색 — 이 화면의 이름값을 하는 기능이라 맨 위에 둔다.
    # (이전 배치는 쇼케이스 카드 20장 뒤였고, 모바일에서 fold +5574px,
    #  즉 8화면쯤 내려가야 검색창이 나왔다.)
    # ------------------------------------------------------------
    st.markdown("#### 채용 공고 통합 검색 (예시 공고)")
    st.caption("고용24 · 공기업 · 강소기업 공고를 한 번에 검색합니다. 지금은 모두 팀이 만든 예시(가상) 공고입니다. "
               "기계·전기·제조·IT 전공 연관 강소기업 공고는 상단에 우선 노출됩니다.")

    # 키워드 · 유형 · 실행을 한 줄로 묶어 검색이 한 덩어리로 읽히게 한다
    with st.container(key="mjp_searchbar"):
        kcol, tcol, bcol = st.columns([2.2, 1.2, 1])
        with kcol:
            kw = st.text_input("검색 키워드 (기업명·공고명·자격증)",
                               placeholder="예: 전기기능사, CNC, 정보처리")
        with tcol:
            type_pick = st.selectbox("기업 유형",
                                     ["전체", "대기업", "중견기업", "중소기업",
                                      "스타트업", "공기업", "강소기업"])
        with bcol:
            st.markdown('<div class="mjp-btn-align"></div>', unsafe_allow_html=True)
            fetch = st.button("지금 불러오기", type="primary", use_container_width=True)

    if fetch:
        with st.spinner("예시 공고를 불러오는 중..."):
            worknet_df, _ = fb.fetch_jobs_safe(
                fb.server_key(fb.WORKNET_SECRET), kw, tracker=tracker)
            alio_records, _ = fb.fetch_alio_safe(tracker=tracker)
            sme_records, _ = fb.fetch_strong_sme_safe(tracker=tracker)

        worknet_records = (worknet_df.to_dict("records")
                           if hasattr(worknet_df, "to_dict") else list(worknet_df))
        alio_records = filter_results(alio_records, kw)
        sme_records = prioritize_by_department(filter_results(sme_records, kw))

        st.session_state.live_jobs = worknet_records + alio_records + sme_records
        st.rerun()

    if st.session_state.live_jobs is not None:
        # [심사대응] 출처 배지(LIVE/BACKUP)·오류 문구는 개발자용이라 관리자 화면에서만 본다
        sample_notice()

        records = st.session_state.live_jobs
        if type_pick != "전체":
            records = [r for r in records if r.get("company_type") == type_pick]

        if not records:
            st.warning("검색 결과가 없습니다. 다른 키워드나 기업 유형으로 다시 시도해보세요.")
            mascot.show("thinking", size=110)
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
    # 기업 카드 데이터베이스 — 참고용이므로 공고 검색 아래로 내렸다
    # ------------------------------------------------------------
    st.markdown("#### 전국 주요 계열 연계 Meister 모의 채용 기업 데이터베이스")

    # ------------------------------------------------------------
    # [Phase C] 매칭 점수 · 다중 필터 · 추천
    # ------------------------------------------------------------
    # 기업 목록은 all_companies() 로 받는다 — 팀이 기업을 추가하면 아래
    # 정렬·필터·추천이 코드 수정 없이 그대로 확장된다.
    profile = cf.student_profile(st.session_state)
    companies = cf.score_all(all_companies(), profile)
    options = cf.filter_options(companies)

    if not cf.has_spec(profile):
        st.info("스펙 진단을 먼저 하면 기업마다 **내 매칭 점수**가 붙고, "
                "점수순 정렬과 추천이 열립니다.")

    with st.container(key="mjp_filterbar"):
        fc1, fc2 = st.columns([1.2, 1])
        with fc1:
            sort_how = st.selectbox("정렬", cf.SORT_OPTIONS, key="explore_sort")
        with fc2:
            pick_sizes = st.multiselect("기업 규모", options["sizes"],
                                        key="explore_sizes",
                                        placeholder="전체 규모")
        fc3, fc4 = st.columns(2)
        with fc3:
            pick_cats = st.multiselect("전공 계열", options["categories"],
                                       key="explore_cats",
                                       placeholder="전체 계열")
        with fc4:
            pick_certs = st.multiselect("요구 자격증 (하나라도 해당)", options["certs"],
                                        key="explore_certs",
                                        placeholder="자격증 무관")

    # 추천은 필터 이전의 전체 기업 기준이다. 필터를 좁힌 뒤의 상위 4개를
    # 추천이라 부르면, 필터가 바뀔 때마다 추천이 흔들려 신뢰를 잃는다.
    top = cf.recommendations(companies)
    if top:
        st.markdown("##### 내 스펙에 가장 잘 맞는 기업")
        for col, c in zip(grid_columns(len(top), 4), top):
            with col:
                render_html(f"""
                <div class="mjp-card" style="border-color:{GREEN};">
                    <span class="mjp-badge" style="background:{GREEN}; color:{BG};">
                        매칭 {c['match_score']:.0f}점</span>
                    <div style="font-size:var(--mjp-body); font-weight:800; margin-top:10px;">{c['name']}</div>
                    <div class="mjp-muted">{c['size_tag']} · {c['category']}</div>
                </div>
                """)
        st.divider()

    filtered = cf.apply_filters(companies, certs=pick_certs,
                                categories=pick_cats, sizes=pick_sizes)
    shown = cf.sort_companies(filtered, sort_how)

    active = [len(pick_sizes), len(pick_cats), len(pick_certs)]
    if any(active):
        st.caption(f"필터 적용 — {len(shown)}개 기업 (전체 {len(companies)}개 중)")
    if not shown:
        st.warning("조건에 맞는 기업이 없습니다. 필터를 하나씩 풀어보세요.")
        mascot.show("thinking", size=110)

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
            match_chip = (
                f'<span class="mjp-badge" style="background:{GREEN}; color:{BG}; '
                f'margin-left:6px;">매칭 {c["match_score"]:.0f}</span>'
                if c.get("match_score") is not None else ""
            )
            # [big-patch 1단계] 실제 기업(verified)에는 별점·복지 같은 지어낸 값이 없다.
            # 가상 기업은 '가상 기업 · 예시 데이터' 칩, 실제 기업은 '출처 확인' 칩 + 출처 링크.
            verified = c.get("data_kind") == "verified"
            stars = "" if verified else render_stars(c.get("overall_rating") or 0)
            if verified:
                extra = (f'<div class="mjp-muted" style="margin-top:6px;">소재지 '
                         f'<b style="color:{TEXT};">{c.get("region") or "-"}</b></div>'
                         + (f'<div class="mjp-muted" style="margin-top:6px;">인재상 요약<br>'
                            f'<span style="color:{TEXT};">{c["talent_summary"]}</span></div>'
                            if c.get("talent_summary") else "")
                         + source_links(c))
            else:
                extra = (f'<div class="mjp-muted" style="margin-top:6px;">복지 (예시)<br>'
                         f'<span style="color:{TEXT};">{c.get("benefit_short", "")}</span></div>')
            talent = ", ".join(c.get("ideal_talent") or []) or "-"
            render_html(f"""
            <div class="mjp-card">
                {data_kind_chip(c)}
                <span class="mjp-tag">{c['size_tag']} · {c['field_tag']}</span>{match_chip}
                <span style="float:right; display:inline-flex; align-items:center; gap:6px;">
                    {stars}{heart}
                </span>
                <div style="font-size:var(--mjp-h2); font-weight:800; margin-top:8px;">{c['name']}</div>
                <div class="mjp-muted" style="margin-bottom:8px;">{c['description']}</div>
                <div class="mjp-muted">인재상<br><b style="color:{TEXT};">{talent}</b></div>
                {extra}
            </div>
            """)
            # 버튼 줄은 mjp_row_ 컨테이너로 감싸 모바일에서도 가로로 유지한다
            with st.container(key=f"mjp_row_card_{c['id']}"):
                # 0.7 로 두면 '찜하기'가 64px 에 갇혀 '찜...' 으로 잘린다.
                # (scrollWidth 로는 안 잡힌다 — ellipsis 는 폭을 늘리지 않는다)
                bc1, bc2, bc3 = st.columns([1, 1.15, 1.15])
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


# ------------------------------------------------------------
# 기업 스토리 (ui/story_viewer.py · services/story_cards.py · services/reactions.py)
# ------------------------------------------------------------
_STORY_IDX = "story_idx"


def _story_companies() -> list:
    """
    스토리 순서. 아래 기업 목록과 같은 데이터·같은 점수(score_all)를 쓰고,
    스펙 진단을 했으면 매칭 점수순, 아니면 별점순으로 보여준다.
    """
    profile = cf.student_profile(st.session_state)
    companies = cf.score_all(all_companies(), profile)
    return cf.sort_companies(companies, cf.SORT_MATCH)


def _move_story(step: int, total: int) -> None:
    st.session_state[_STORY_IDX] = (st.session_state.get(_STORY_IDX, 0) + step) % total


def _render_story_section() -> None:
    st.markdown("#### 기업 스토리로 빠르게 훑어보기")
    st.caption("카드 한 장에 5초. 왼쪽을 탭하면 이전, 오른쪽을 탭하면 다음 카드예요. "
               "꾹 누르고 있으면 멈춰요.")

    companies = _story_companies()
    if not companies:
        st.info("보여줄 기업 데이터가 없습니다.")
        return

    total = len(companies)
    idx = st.session_state.get(_STORY_IDX, 0) % total
    company = companies[idx]

    cards = story_cards.make_story_cards(company)
    render_story(company["name"], cards)

    sources = {c["source"] for c in cards if c["source"] != "score"}
    if sources & {"ai", "cache"}:
        source_note = "AI 요약 (원본 데이터만 근거)"
    else:
        source_note = "원본 데이터로 만든 기본 요약 · AI 요약은 프리미엄 회원 전용"
    mine = reactions.reaction_of(company["id"])
    mine_note = {"like": " · 내 반응: 관심", "pass": " · 내 반응: 패스"}.get(mine, "")
    st.caption(f"{idx + 1} / {total} · {source_note}{mine_note}")

    failure = story_cards.last_failure()
    if failure and "basic" in sources:
        st.caption("AI 요약을 받지 못해 기본 요약으로 보여드렸어요.")

    # 모바일에서도 가로 한 줄 유지 (theme.py 의 mjp_row 예외 규칙)
    with st.container(key="mjp_row_story_nav"):
        b1, b2, b3 = st.columns([1, 1, 1.5])
        with b1:
            if st.button("← 이전 기업", key="story_prev", use_container_width=True):
                _move_story(-1, total)
                st.rerun()
        with b2:
            if st.button("관심 있어요", key="story_like", use_container_width=True,
                         type="primary" if mine == reactions.LIKE else "secondary"):
                reactions.record(company["id"], reactions.LIKE)
                st.toast(f"{company['name']} — 관심 기업에 담았어요")
                _move_story(1, total)
                st.rerun()
        with b3:
            if st.button("패스 · 다음 기업 →", key="story_pass", use_container_width=True):
                reactions.record(company["id"], reactions.PASS)
                _move_story(1, total)
                st.rerun()

    _render_liked(companies)


def _render_liked(companies: list) -> None:
    """'관심 있어요'를 누른 기업과 매칭 점수."""
    liked = reactions.liked_ids()
    by_id = {c["id"]: c for c in companies}
    liked = [by_id[cid] for cid in liked if cid in by_id]

    with st.expander(f"관심 기업 모아보기 ({len(liked)})", expanded=bool(liked)):
        if not liked:
            st.caption("스토리를 보다가 '관심 있어요'를 누르면 여기에 모여요.")
            return
        for c in liked:
            score = c.get("match_score")
            score_html = (f'<b style="color:{GREEN};">매칭 {score:.0f}점</b>' if score is not None
                          else f'<span style="color:{MUTED};">스펙 진단 후 점수 표시</span>')
            with st.container(key=f"mjp_row_liked_{c['id']}"):
                lc, rc = st.columns([3, 1.2])
                with lc:
                    render_html(f"""
                    <div style="padding:6px 0;">
                        <div style="font-weight:800; color:{TEXT};">{c['name']}</div>
                        <div class="mjp-muted">{c['size_tag']} · {c['category']} · {score_html}</div>
                    </div>
                    """)
                with rc:
                    if st.button("스토리 보기", key=f"liked_view_{c['id']}",
                                 use_container_width=True):
                        st.session_state[_STORY_IDX] = companies.index(c)
                        st.rerun()
