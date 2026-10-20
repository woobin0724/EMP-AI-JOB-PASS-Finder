# -*- coding: utf-8 -*-
"""
views/tab_spec.py
기능 1. 스펙 진단 & 추천 (+ 점수 구간별 응원 문구)

원본 app.py 의 TAB 1 블록을 그대로 이관했다. 점수 산출 로직(core/matching.py)은
손대지 않았다 — 이번 단계의 목표는 '진입 방식 변경'이지 '계산 변경'이 아니다.

[v2] 화면의 핵심은 점수 하나다. 맨 위에 큰 숫자 + 판정 칩 + 100점 눈금 막대를
두고, 세부 점수 4줄은 회색 면 한 장에 목록으로 묶었다. 입력은 STEP 1·2·3 으로
나눠 무엇부터 넣으면 되는지 순서가 보이게 했다. (위젯 key·동작은 그대로)

[big-patch 2단계] 기업 유형별 배점(core/matching.WEIGHTS_BY_TYPE)에 맞춰 막대의
만점이 바뀌고, 막대마다 '왜 이 점수인지' 한 줄이 붙는다. 그 아래 시뮬레이션
(자격증 하나 더 · 내신 상승 시 안정권 진입 기업)은 core/score_simulation 이
같은 계산식을 입력만 바꿔 다시 돌린 결과다. 전부 로컬 연산(API 0회).
"""

from html import escape

import streamlit as st

from core import session as ss
from core.catalog import all_talent_keywords, certs_for_department, load_cert_names
from core.matching import calc_spec_score
from core import score_simulation as sim
from data import ogq_assets as ogq
from data.certifications import get_bonus_points
from data.company_showcase import COMPANY_SHOWCASE, COMPANY_SIZE_TAGS, all_companies
from services import activity, usage_log
from services import score_explain
from data.departments import (
    DEPARTMENT_LIST, get_category, get_majors_for_department,
)
from ui import mascot
from ui.components import back_to_hub, disclaimer, sample_notice, note, render_html, section_title, topbar
from ui.theme import BLUE, CARD, GREEN, GOLD, MUTED, RED, STATUS_SOFT, STATUS_VIVID, render_stars, score_bar


# 점수 구간 → 마스코트 감정 슬롯
# 숫자만 보여주는 진단은 낮은 점수를 받은 학생을 밀어낸다. 같은 48점이라도
# 위로하는 캐릭터가 옆에 있으면 다음 화면으로 넘어갈 확률이 달라진다.
_MASCOT_BY_SCORE = {"success": "celebrate", "cheer": "cheer", "comfort": "comfort"}

# 학생이 이번 세션에서 입력을 한 번이라도 건드렸는가.
# 처음 들어오면 기본값(내신 3.0 · 자격증 없음)으로 계산한 25점이 빨간
# '보완 시급'으로 먼저 뜬다. 아무것도 넣지 않은 학생에게 경고부터 보여주지
# 않도록, 입력 전에는 중립 안내를 띄운다. (점수 계산·기록 로직은 그대로)
_TOUCHED = "spec_touched"


def _mark_touched() -> None:
    st.session_state[_TOUCHED] = True


def _step(no: int, title: str) -> None:
    """입력 단계 머리 — 'STEP 1  학과와 내신'."""
    render_html(f'<div class="mjp-stephead"><b>STEP {no}</b><span>{title}</span></div>')


def render() -> None:
    topbar(active=ss.PAGE_SPEC)
    back_to_hub()
    section_title("스펙 진단 & 추천", icon_name="chart", sub=
                  "내신·자격증·전공 적합성·인재상을 100점 만점으로 환산합니다. "
                  "AI 를 쓰지 않는 정해진 계산식이라 입력하는 즉시 점수가 바뀝니다.")

    sample_notice()

    tracker = st.session_state.tracker
    all_cert_names, cert_source = load_cert_names()
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
        _step(1, "학과와 내신")
        dept = st.selectbox("학과/계열 (하이파이브 분류를 참고한 팀 자체 분류)", DEPARTMENT_LIST,
                            index=DEPARTMENT_LIST.index(st.session_state.dept),
                            key="dept_widget", on_change=_mark_touched)
        st.session_state.dept = dept

        majors = get_majors_for_department(dept)
        # [심사대응] 근거 없는 '계열 평균 취업률(예시)' 수치는 삭제했다 (data/departments.py)
        note(f"세부 전공 예시: {', '.join(majors)}")

        grade = st.slider("내신 성적 등급 (마이스터고 5등급 성취평가제)", 1.0, 5.0,
                          st.session_state.grade, 0.1, key="grade_widget", on_change=_mark_touched,
                          help="환산식: 내신 배점 × (5.0 − 등급) ÷ 4.0  |  일반 진단(30점) 기준 1.0등급=30점, 2.0등급=22.5점")
        st.session_state.grade = grade

    with in_right:
        _step(2, "자격증과 강점")
        dept_certs = certs_for_department(dept)
        cert_options = sorted(set(dept_certs) | set(all_cert_names))
        certs = st.multiselect(
            "취득 전공 자격증 다중 선택 (Q-Net 기반)", cert_options,
            default=[c for c in st.session_state.user_certs if c in cert_options],
            key="user_certs_widget", on_change=_mark_touched,
            # Streamlit 기본 placeholder 가 "Choose options" 영문이라
            # 한국어 화면에 영어가 섞인다
            placeholder="자격증을 선택하세요",
        )
        st.session_state.user_certs = certs

        talent_keywords = all_talent_keywords()
        strengths = st.multiselect(
            "나의 핵심 강점 키워드 (기업 인재상 매칭에 사용됨)", talent_keywords,
            default=[k for k in st.session_state.strength_keywords if k in talent_keywords],
            key="strength_keywords_widget", on_change=_mark_touched,
            help="선택한 키워드가 기업 '인재상'과 일치하면 인재상 점수에 반영됩니다(배점은 기업 유형에 따라 10~15점).",
            placeholder="강점 키워드를 선택하세요",
        )
        st.session_state.strength_keywords = strengths

        _step(3, "목표 기업 (선택)")
        companies = all_companies()
        company_names = ["선택 안 함 (일반 진단)"] + [c["name"] for c in companies]
        pick = st.selectbox("정밀 진단할 목표 기업 (선택)", company_names, key="target_company_widget", on_change=_mark_touched)
        target_company = None
        if pick != company_names[0]:
            target_company = next((c for c in companies if c["name"] == pick), None)
            if target_company:
                st.session_state.selected_company_id = target_company["id"]

        st.caption("※ 입력값을 바꾸면 위 점수가 **즉시** 갱신됩니다.")

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
    activity.record_spec(result, dept, grade, target_company, certs=certs, strengths=strengths)

    touched = bool(st.session_state.get(_TOUCHED) or certs or strengths or target_company)
    if not touched:
        with score_slot:
            _render_waiting()
    else:
        usage_log.log_feature("spec_done")   # 지표용 — 내용 없이 '진단을 마쳤다'만 (하루 1회)
        sticker_key = ogq.sticker_key_for_score(result["final_score"])
        verdict, verdict_msg = ogq.SCORE_STICKER_MESSAGES[sticker_key]
        color = {"success": GREEN, "cheer": GOLD, "comfort": RED}[sticker_key]
        title = target_company["name"] if target_company else "일반 진단"

        # 화면 맨 위에 잡아둔 자리에 점수를 채운다 (배치 의도는 위 주석 참조)
        with score_slot:
            # 막대 만점은 기업 유형별 배점, 막대 아래 한 줄은 '왜 이 점수인지'
            items = sim.explain_items(result, target_company, grade, certs, strengths)
            rows = "".join(score_bar(i["label"], i["score"], i["max"], why=escape(i["reason"]))
                           for i in items)
            w = result["weights"]
            weight_line = (f"배점 기준 · {escape(result['weight_profile'])} — 내신 {w['grade']} · "
                           f"자격증 {w['cert']} · 전공 {w['fit']} · 인재상 {w['talent']} (합 100)")
            render_html(f"""
            <div class="mjp-score-grid">
                {_score_hero(result["final_score"], color, verdict, verdict_msg, escape(title))}
                <div class="mjp-break">{rows}<div class="mjp-weight-line">{weight_line}</div></div>
            </div>
            """)

            if result["cert_details"]:
                with st.expander("자격증 인정 비율 상세 보기", expanded=False):
                    for d in result["cert_details"]:
                        mark = "●" if d["ratio"] == 1.0 else ("◐" if d["ratio"] > 0 else "○")
                        extra = f" ← 보유: {d['matched_by']}" if d["matched_by"] and d["ratio"] < 1.0 else ""
                        st.markdown(f"{mark} **{d['cert']}** · {d['status']}{extra}")
                    st.caption(f"정확히 일치 100% · 직무 유사 자격증 70% 인정 → 평균 인정비율 × {w['cert']}점")

        # ------------------------------------------------------------
        # [Phase B] 왜 이 점수인가 — 마스코트가 말로 풀어준다
        # ------------------------------------------------------------
        # 점수 계산은 위에서 이미 끝났다(로컬 연산). 여기서는 그 숫자를 재료로
        # 설명만 만든다. 키가 없으면 규칙 기반 문장으로 내려가므로, 키 없이
        # 100명이 써도 이 자리가 비지 않는다.
        explain_profile = {
            "dept": dept, "grade": grade, "certs": certs, "strengths": strengths,
        }
        explanation, explain_source = score_explain.explain(
            explain_profile, result, target_company)

        st.markdown("#### 왜 이 점수인가요")
        tip_l, tip_r = st.columns([1, 3])
        with tip_l:
            st.markdown(mascot.html(_MASCOT_BY_SCORE[sticker_key], size=128),
                        unsafe_allow_html=True)
        with tip_r:
            badge = ("AI 설명" if explain_source == "ai" else "규칙 기반 설명")
            # 설명 카드가 회색 면이라 규칙 기반 배지는 흰 칩으로 둔다
            badge_bg = BLUE if explain_source == "ai" else "#FFFFFF"
            badge_fg = "#FFFFFF" if explain_source == "ai" else MUTED
            render_html(f"""
            <div class="mjp-explain" style="margin-bottom:10px;">
                <span class="mjp-badge" style="background:{badge_bg}; color:{badge_fg};">{badge}</span>
                <div class="mjp-explain-body">{explanation['explanation']}</div>
                <div class="mjp-explain-next"><b>다음 한 걸음</b>{explanation['suggestion']}</div>
            </div>
            """)

            failure = score_explain.last_failure()
            if failure and explain_source == "rule":
                st.caption("AI 설명을 받지 못해 규칙 기반 설명으로 보여드렸어요.")

            for tip in result["tips"]:
                st.info(tip)

        _render_simulation(grade, certs, dept, dept_category, target_company, strengths, companies)

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
            disclaimer("※ 실제 공식 가산점 규정이 아닌 예시 데이터입니다.")

    with gcol2:
        st.markdown("**매칭 기업 탐색 (입력에 바로 반영)**")
        size_pick = st.radio("기업 규모", COMPANY_SIZE_TAGS[1:], horizontal=True,
                             key="match_size", label_visibility="collapsed")
        matched = [c for c in COMPANY_SHOWCASE
                   if c["category"] == dept_category and c["size_tag"] == size_pick]
        if not matched:
            st.caption("해당 기업군에는 이 학과 계열과 매칭되는 예시 기업이 없습니다. 다른 규모를 선택해보세요.")
        else:
            for c in matched:
                stars = render_stars(c["overall_rating"]) if c.get("overall_rating") else ""
                st.markdown(f"**{c['name']}** · {c['description']}  {stars}",
                            unsafe_allow_html=True)
                if st.button(f"{c['name']} 자세히 보기", key=f"match_{c['id']}"):
                    st.session_state.selected_company_id = c["id"]
                    ss.goto(ss.PAGE_GUIDE)


def _render_simulation(grade, certs, dept, dept_category, company, strengths, companies) -> None:
    """
    점수 올리기 시뮬레이션 — 자격증 하나 더 · 내신 상승 시 안정권(80점) 진입 기업.
    계산은 core/score_simulation (스펙 진단과 같은 식). 실패해도 진단 화면은 유지한다.
    """
    try:
        gains = sim.cert_gains(grade, certs, dept_category, company, strengths,
                               candidates=certs_for_department(dept))
        unlocks = sim.grade_unlocks(grade, certs, dept_category, strengths, companies)
        safe = sim.safe_now(grade, certs, dept_category, strengths, companies)
    except Exception:  # noqa: BLE001 — 부가 기능이라 진단 본체를 멈추지 않는다
        st.caption("시뮬레이션을 계산하지 못했습니다. 위 점수는 그대로 유효합니다.")
        return

    st.markdown("#### 점수 올리기 시뮬레이션")
    note("지금 입력값에서 하나만 바꿨을 때의 점수예요. 같은 계산식으로 다시 계산한 값이며 합격을 보장하지 않습니다.")
    left, right = st.columns(2)

    with left:
        target = f"{escape(company['name'])} 기준" if company else "일반 진단 기준"
        st.markdown(f"**이 자격증을 따면** · {target}")
        if gains:
            rows = "".join(
                f'<div class="mjp-sim-row"><span class="mjp-sim-name">{escape(g["cert"])}'
                f'<small>{g["before"]:g}점 → {g["after"]:g}점</small></span>'
                f'<span class="mjp-sim-gain">+{g["gain"]:g}점</span></div>'
                for g in gains)
        else:
            rows = '<div class="mjp-sim-empty">자격증 점수가 이미 만점이거나, 더해서 오르는 자격증이 없어요.</div>'
        render_html(f'<div class="mjp-sim">{rows}</div>')

    with right:
        st.markdown(f"**내신이 오르면** · 지금 안정권 {safe}곳")
        if unlocks:
            rows = "".join(
                f'<div class="mjp-sim-row"><span class="mjp-sim-name">{escape(u["company"]["name"])}'
                f'<small>{u["target_grade"]:.1f}등급이면 {u["before"]:g}점 → {u["after"]:g}점</small></span>'
                f'<span class="mjp-sim-gain">{u["step"]:g}등급 ↑</span></div>'
                for u in unlocks[:6])
            more = len(unlocks) - 6
            if more > 0:
                rows += f'<div class="mjp-sim-empty">외 {more}곳</div>'
        elif grade <= 1.0:
            rows = '<div class="mjp-sim-empty">이미 1.0등급이에요. 자격증·인재상으로 점수를 올려보세요.</div>'
        else:
            rows = ('<div class="mjp-sim-empty">내신을 1등급 올려도 새로 80점을 넘는 기업이 없어요. '
                    '자격증 시뮬레이션부터 채워보세요.</div>')
        render_html(f'<div class="mjp-sim">{rows}</div>')


def _score_hero(score, color: str, verdict: str, message: str, title: str) -> str:
    """
    점수 히어로 HTML — 큰 숫자 · 판정 칩 · 한 줄 설명 · 100점 눈금 막대.

    눈금 50 · 80 은 판정 구간 경계(data/ogq_assets.sticker_key_for_score)와 같다.
    score 가 None 이면 '입력 전' 상태로 그린다.
    """
    waiting = score is None
    # 큰 글씨의 대시(—)는 긴 막대처럼 보여 '점수 없음'으로 읽히지 않는다 → 물음표
    num = "?" if waiting else f"{score}"
    pct = 0 if waiting else max(0.0, min(100.0, float(score)))
    soft = STATUS_SOFT.get(color, CARD)
    vivid = STATUS_VIVID.get(color, color)   # 큰 숫자·막대는 밝은 톤, 칩 글자는 진한 톤
    return f"""
    <div class="mjp-score">
        <div class="mjp-score-label">내 합격 지수 · {title}</div>
        <div class="mjp-score-line">
            <span class="mjp-score-num" style="color:{vivid};">{num}</span>
            <span class="mjp-score-unit">/ 100점</span>
            <span class="mjp-score-chip" style="background:{soft}; color:{color};">{verdict}</span>
        </div>
        <div class="mjp-score-msg">{message}</div>
        <div class="mjp-meter">
            <div class="mjp-meter-track">
                <div class="mjp-meter-fill" style="width:{pct:.0f}%; background:{vivid};"></div>
            </div>
            <div class="mjp-meter-tick" style="left:50%;"></div>
            <div class="mjp-meter-tick" style="left:80%;"></div>
        </div>
        <div class="mjp-meter-labels">
            <span style="left:0;">0</span>
            <span style="left:50%;">50<em> · 분발 필요</em></span>
            <span style="left:80%;">80<em> · 합격 안정권</em></span>
            <span style="left:100%;">100</span>
        </div>
    </div>"""


def _render_waiting() -> None:
    """입력 전 중립 상태 — 점수·판정 대신 무엇을 넣으면 되는지만 알려준다."""
    render_html(f"""
    <div class="mjp-score-grid mjp-score-grid-single">
        {_score_hero(None, MUTED, "입력 전", "아래 STEP 1·2·3 에서 학과·내신 등급·자격증을 고르면 100점 만점 점수가 바로 계산돼요.", "일반 진단")}
    </div>
    """)
