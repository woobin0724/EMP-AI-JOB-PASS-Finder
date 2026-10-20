# -*- coding: utf-8 -*-
"""
views/class_board.py
[Phase 2-3] 선생님 — '우리 반 현황' 대시보드

데이터 출처
-----------
services/activity.py 가 학생 화면에서 기록한 값을 읽는다.
  · 목표 기업   ← 스펙 진단에서 고른 정밀 진단 기업 (profile)
  · 진행 단계   ← 커리어 로드맵 마일스톤 체크 (milestones)
  · 최근 점수   ← 스펙 진단 결과 (score_history[0])

▣ 빈 화면을 설계에 포함한다
   반을 막 만든 선생님에게는 학생이 0명이다. 이때 빈 표를 보여주면
   "고장 났나?" 싶다. 그래서 학생 수 0 / 활동 0 두 경우를 각각
   '다음에 뭘 해야 하는지' 알려주는 화면으로 만들었다.
"""

from html import escape

import pandas as pd
import streamlit as st

from core import class_match
from core import session as ss
from data.company_showcase import all_companies
from data.roadmap import MILESTONES
from services import store
from services.activity import student_summary
from ui import mascot
from ui.components import (
    back_to_hub, grid_columns, render_html, sample_notice, section_title, stat_tiles, status_chip, topbar,
)
from ui.theme import GOLD, GREEN, MUTED, RED, STATUS_VIVID, TEXT


def render() -> None:
    topbar(active=ss.PAGE_CLASS_BOARD)
    back_to_hub()

    klass = store.teacher_class(ss.user_id())
    if not klass:
        _render_no_class()
        return

    section_title("우리 반 현황", store.class_label(klass), icon_name="school", eyebrow="선생님")

    students = store.class_students(klass["class_code"])
    rows = [student_summary(u) for u in students]

    _render_code_strip(klass, len(rows))

    if not rows:
        _render_empty_class(klass)
        return

    # '누구를 먼저 도울지'가 이 화면의 목적이라 우선순위 목록을 표보다 위에 둔다.
    # (예전에는 맨 아래라 폰에서 네 화면쯤 내려가야 보였다)
    _render_attention(rows)
    _render_summary(rows)
    _render_table(rows)
    _render_export(rows, klass)
    try:
        _render_company_match(students)
    except Exception:  # noqa: BLE001 — 부가 기능 오류가 반 현황 전체를 멈추지 않게
        st.caption("기업별 학생 목록을 계산하지 못했습니다. 위 반 현황은 그대로 유효합니다.")


# ------------------------------------------------------------
# [big-patch 5단계] 반 현황 CSV · 이 기업에 맞는 학생
# ------------------------------------------------------------
def _render_export(rows: list[dict], klass: dict) -> None:
    st.download_button(
        "반 현황 엑셀(CSV) 내려받기", data=class_match.class_csv(rows, len(MILESTONES)),
        file_name=f"반현황_{klass['class_code']}.csv", mime="text/csv",
        use_container_width=True, key="board_csv",
    )
    st.caption("엑셀에서 바로 열 수 있습니다(한글 깨짐 없음). 학생 이름이 들어 있으니 학교 밖으로 공유하지 마세요.")


def _render_company_match(users: list[dict]) -> None:
    st.markdown("#### 이 기업에 맞는 학생")
    st.caption("학생이 스펙 진단에 저장한 학과·내신·자격증·강점으로 학생 화면과 같은 계산식을 기업마다 다시 돌립니다.")
    sample_notice()
    companies = all_companies()
    names = [c["name"] for c in companies]
    pick = st.selectbox("기업 고르기", names, key="board_company")
    company = next((c for c in companies if c["name"] == pick), None)
    if not company:
        return
    fits = class_match.students_for_company(users, company)
    if not fits:
        st.info("아직 스펙 진단 기록이 있는 학생이 없습니다.")
        return
    safe = sum(1 for f in fits if f["score"] >= 80)
    st.caption(f"진단 기록이 있는 {len(fits)}명 중 합격 안정권(80점 이상) {safe}명")
    color = {"합격 안정권": GREEN, "분발 필요": GOLD, "보완 시급": RED}
    out = []
    for f in fits[:30]:
        if not f["certs_known"]:
            miss = "자격증 기록 없음(예전 진단) — 학생이 다시 진단하면 정확해져요"
        elif f["missing_certs"]:
            miss = f"없는 자격증: {', '.join(f['missing_certs'])}"
        else:
            miss = "요구 자격증 모두 보유"
        out.append(
            f'<div class="mjp-sim-row"><span class="mjp-sim-name">{escape(f["name"])}'
            f'<small>{escape(f["dept"])} · 내신 {f["grade"]:.1f}등급 · {escape(miss)}</small></span>'
            f'<span class="mjp-sim-gain" style="color:{color[f["band"]]};">{f["score"]:g}점</span></div>')
    render_html(f'<div class="mjp-sim">{"".join(out)}</div>')
    if len(fits) > 30:
        st.caption(f"상위 30명만 표시 · 전체 {len(fits)}명")


# ------------------------------------------------------------
# 상단 — 반 코드 안내
# ------------------------------------------------------------
def _render_code_strip(klass: dict, count: int) -> None:
    # v2: 반 코드와 학생 수를 같은 무게의 타일 두 장으로
    stat_tiles([
        ("반 코드", f'<span style="letter-spacing:0.14em;">{klass["class_code"]}</span>', "", None),
        ("등록 학생", f"{count}명", "", None),
    ])
    st.caption("학생이 마이페이지에서 이 코드를 입력하면 아래 표에 나타납니다.")


# ------------------------------------------------------------
# 빈 상태
# ------------------------------------------------------------
def _render_no_class() -> None:
    section_title("우리 반 현황", "아직 반을 만들지 않으셨어요.", icon_name="school", eyebrow="선생님")
    with mascot.side("thinking", size=120):
        st.info("반을 만들면 6자리 코드가 발급되고, 학생들이 그 코드로 등록할 수 있습니다.")
        if st.button("우리 반 만들러 가기", type="primary", key="board_to_setup"):
            ss.goto(ss.PAGE_CLASS_SETUP)


def _render_empty_class(klass: dict) -> None:
    st.markdown("")
    with mascot.side("welcome", size=126):
        st.info(f"아직 등록한 학생이 없습니다. 반 코드 **{klass['class_code']}** 를 "
                f"학생들에게 알려주세요.")
        st.caption("학생 안내 문구 예시 — 아래를 복사해 학급 단톡방에 붙여넣으세요.")
        st.code(
            f"AI Job Pass Finder 접속 → 로그인 → 마이페이지 → 반 등록\n"
            f"우리 반 코드: {klass['class_code']}",
            language=None,
        )


# ------------------------------------------------------------
# 요약 지표
# ------------------------------------------------------------
def _render_summary(rows: list[dict]) -> None:
    scored = [r for r in rows if r["score"] is not None]
    avg = round(sum(r["score"] for r in scored) / len(scored), 1) if scored else None
    started = sum(1 for r in rows if r["active"])
    finished = sum(1 for r in rows if r["stage_done"] == len(MILESTONES))

    # 색은 값에 따라 정한다 (상태색은 '좋음/주의/위험' 신호이므로 고정하면 안 된다).
    #   평균 점수 — 학생 카드와 같은 구간: 80↑ 그린 · 50↑ 골드 · 그 아래 레드 · 진단 없음 회색
    #   진단 시작 — 전원 그린 · 일부 골드 · 0명 회색
    #   로드맵 완주 — 1명 이상 그린 · 0명 회색 (아직 안 했을 뿐 경고할 일은 아니다)
    if avg is None:
        avg_color = MUTED
    elif avg >= 80:
        avg_color = GREEN
    elif avg >= 50:
        avg_color = GOLD
    else:
        avg_color = RED
    started_color = GREEN if started == len(rows) else (GOLD if started else MUTED)
    finished_color = GREEN if finished else MUTED

    cards = [
        ("반 평균 매칭 점수", f"{avg}점" if avg is not None else "—", avg_color,
         f"{len(scored)}명 진단 완료"),
        ("진단 시작", f"{started} / {len(rows)}", started_color,
         f"미시작 {len(rows) - started}명"),
        ("로드맵 완주", f"{finished}명", finished_color,
         f"{len(MILESTONES)}단계 모두 완료"),
    ]

    stat_tiles([(label, value, sub, color) for label, value, color, sub in cards])


# ------------------------------------------------------------
# 학생 목록
# ------------------------------------------------------------
def _render_table(rows: list[dict]) -> None:
    st.markdown("#### 학생별 진행 현황")

    view = st.radio("보기", ["표로 보기", "카드로 보기"], horizontal=True,
                    label_visibility="collapsed", key="board_view")

    if view == "표로 보기":
        df = pd.DataFrame([{
            "이름": r["name"],
            "학과": r["dept"],
            "내신": f"{r['grade']}등급" if r["grade"] is not None else "-",
            "목표 기업": r["target"],
            "진행 단계": f"{r['stage_done']}/{len(MILESTONES)} · {r['stage']}",
            "최근 점수": r["score"] if r["score"] is not None else None,
            "최근 활동": r["last_seen"] or "-",
        } for r in rows])

        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={
                "최근 점수": st.column_config.ProgressColumn(
                    "최근 점수", min_value=0, max_value=100, format="%d점",
                ),
            },
        )
        st.caption("※ 점수 막대는 100점 만점 기준입니다. 진단을 한 번도 하지 않은 학생은 비어 있습니다.")
    else:
        _render_cards(rows)


def _render_cards(rows: list[dict]) -> None:
    # 행 단위 컬럼 — 모바일에서 1단으로 접혀도 학생 순서가 뒤섞이지 않는다
    for col, r in zip(grid_columns(len(rows), 2), rows):
        with col:
            score = r["score"]
            if score is None:
                color, score_text = MUTED, "미진단"
            elif score >= 80:
                color, score_text = GREEN, f"{score}점"
            elif score >= 50:
                color, score_text = GOLD, f"{score}점"
            else:
                color, score_text = RED, f"{score}점"

            pct = int((r["stage_done"] / len(MILESTONES)) * 100)

            render_html(f"""
            <div class="mjp-tcard" style="padding:24px; margin-bottom:12px;">
                <div style="display:flex; align-items:flex-start; gap:12px;">
                    <div style="flex:1; min-width:0;">
                        <h4>{r['name']}</h4>
                        <div class="mjp-muted">{r['dept']}{f" · 내신 {r['grade']}등급" if r['grade'] is not None else ""}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:24px; font-weight:800; color:{STATUS_VIVID.get(color, color)};
                                    letter-spacing:-0.02em;">{score_text}</div>
                        <div class="mjp-muted" style="font-size:var(--mjp-caption);">{r['scored_at']}</div>
                    </div>
                </div>
                <div class="mjp-muted" style="margin-top:12px;">목표 기업
                    <b style="color:{TEXT};">{r['target']}</b></div>
                <div style="margin-top:12px;">
                    <div style="display:flex; justify-content:space-between; font-size:var(--mjp-caption);
                                color:{MUTED}; margin-bottom:6px;">
                        <span>{r['stage']}</span><span>{r['stage_done']}/{len(MILESTONES)}</span>
                    </div>
                    <div class="mjp-bar-track">
                        <div class="mjp-bar-fill" style="width:{pct}%;"></div>
                    </div>
                </div>
            </div>
            """)


# ------------------------------------------------------------
# 지도가 필요한 학생
# ------------------------------------------------------------
def _render_attention(rows: list[dict]) -> None:
    """
    대시보드의 존재 이유는 '누구를 먼저 도울지' 고르는 것이다.
    표만 주면 선생님이 눈으로 훑어야 하므로, 우선순위를 직접 계산해 보여준다.
    """
    not_started = [r for r in rows if not r["active"]]
    low_score = [r for r in rows if r["score"] is not None and r["score"] < 50]
    stalled = [r for r in rows if r["active"] and r["stage_done"] == 0]

    if not (not_started or low_score or stalled):
        st.success("모든 학생이 진단을 시작했고, 점수 보완이 시급한 학생도 없습니다.")
        return

    st.markdown("#### 먼저 챙겨보면 좋을 학생")
    acols = st.columns(3)
    groups = [
        ("아직 시작 안 함", not_started, MUTED, "접속은 했지만 진단을 한 번도 하지 않았습니다."),
        ("점수 보완 시급", low_score, RED, "매칭 점수가 50점 미만입니다."),
        ("로드맵 미착수", stalled, GOLD, "진단은 했지만 로드맵 단계를 시작하지 않았습니다."),
    ]
    for col, (title, group, color, desc) in zip(acols, groups):
        with col:
            names = ", ".join(r["name"] for r in group[:6]) or "해당 없음"
            more = f" 외 {len(group) - 6}명" if len(group) > 6 else ""
            # v2: 왼쪽 색띠 대신 상태 칩으로 심각도를 표시한다
            render_html(f"""
            <div class="mjp-tcard" style="padding:24px; margin-bottom:12px;">
                {status_chip(f"{len(group)}명", color)}
                <h4 style="margin-top:12px !important;">{title}</h4>
                <p class="mjp-muted">{desc}</p>
                <p style="margin-top:10px !important; font-weight:600; color:{TEXT};">{names}{more}</p>
            </div>
            """)
