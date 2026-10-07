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

import pandas as pd
import streamlit as st

from core import session as ss
from data.roadmap import MILESTONES
from services import store
from services.activity import student_summary
from ui import mascot
from ui.components import back_to_hub, grid_columns, section_title, topbar
from ui.theme import BRAND, CARD_BORDER, GOLD, GREEN, MUTED, RED, TEXT


def render() -> None:
    topbar(active=ss.PAGE_CLASS_BOARD)
    back_to_hub()

    klass = store.teacher_class(ss.user_id())
    if not klass:
        _render_no_class()
        return

    section_title("우리 반 현황", store.class_label(klass), icon_name="school")

    students = store.class_students(klass["class_code"])
    rows = [student_summary(u) for u in students]

    _render_code_strip(klass, len(rows))

    if not rows:
        _render_empty_class(klass)
        return

    _render_summary(rows)
    _render_table(rows)
    _render_attention(rows)


# ------------------------------------------------------------
# 상단 — 반 코드 안내
# ------------------------------------------------------------
def _render_code_strip(klass: dict, count: int) -> None:
    st.markdown(f"""
    <div class="mjp-card" style="display:flex; align-items:center; gap:18px; flex-wrap:wrap;">
        <div>
            <div class="mjp-muted">반 코드</div>
            <div style="color:{GOLD}; font-size:var(--mjp-h1); font-weight:800;
                        letter-spacing:0.2em;">{klass['class_code']}</div>
        </div>
        <div style="width:1px; height:40px; background:{CARD_BORDER};"></div>
        <div>
            <div class="mjp-muted">등록 학생</div>
            <div style="color:{TEXT}; font-size:var(--mjp-h1); font-weight:800;">{count}명</div>
        </div>
        <div style="flex:1; min-width:180px;">
            <div class="mjp-muted" style="line-height:1.6;">
                학생이 마이페이지에서 이 코드를 입력하면 아래 표에 나타납니다.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------
# 빈 상태
# ------------------------------------------------------------
def _render_no_class() -> None:
    section_title("우리 반 현황", "아직 반을 만들지 않으셨어요.", icon_name="school")
    c1, c2 = st.columns([1, 2.4])
    with c1:
        st.markdown(mascot.html("thinking", size=120), unsafe_allow_html=True)
    with c2:
        st.info("반을 만들면 6자리 코드가 발급되고, 학생들이 그 코드로 등록할 수 있습니다.")
        if st.button("우리 반 만들러 가기", type="primary", key="board_to_setup"):
            ss.goto(ss.PAGE_CLASS_SETUP)


def _render_empty_class(klass: dict) -> None:
    st.markdown("")
    c1, c2 = st.columns([1, 2.4])
    with c1:
        st.markdown(mascot.html("welcome", size=126), unsafe_allow_html=True)
    with c2:
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

    cards = [
        ("반 평균 매칭 점수", f"{avg}점" if avg is not None else "—", GREEN,
         f"{len(scored)}명 진단 완료"),
        ("진단 시작", f"{started} / {len(rows)}", BRAND,
         f"미시작 {len(rows) - started}명"),
        ("로드맵 완주", f"{finished}명", GOLD,
         f"{len(MILESTONES)}단계 모두 완료"),
    ]

    cols = st.columns(3)
    for col, (label, value, color, sub) in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div class="mjp-card" style="text-align:center;">
                <div class="mjp-muted">{label}</div>
                <div style="font-size:var(--mjp-h1); font-weight:800; color:{color}; margin:6px 0 4px;">{value}</div>
                <div class="mjp-muted" style="font-size:11px;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)


# ------------------------------------------------------------
# 학생 목록
# ------------------------------------------------------------
def _render_table(rows: list[dict]) -> None:
    st.markdown("##### 학생별 진행 현황")

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

            st.markdown(f"""
            <div class="mjp-card">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="flex:1;">
                        <div style="font-size:var(--mjp-body); font-weight:800; color:{TEXT};">{r['name']}</div>
                        <div class="mjp-muted">{r['dept']}
                            {f" · 내신 {r['grade']}등급" if r['grade'] is not None else ""}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:var(--mjp-h2); font-weight:800; color:{color};">{score_text}</div>
                        <div class="mjp-muted" style="font-size:11px;">{r['scored_at']}</div>
                    </div>
                </div>
                <div class="mjp-muted" style="margin-top:10px;">목표 기업
                    <b style="color:{TEXT};">{r['target']}</b></div>
                <div style="margin-top:10px;">
                    <div style="display:flex; justify-content:space-between; font-size:11px;
                                color:{MUTED}; margin-bottom:4px;">
                        <span>{r['stage']}</span><span>{r['stage_done']}/{len(MILESTONES)}</span>
                    </div>
                    <div class="mjp-bar-track">
                        <div class="mjp-bar-fill" style="width:{pct}%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


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

    st.markdown("##### 먼저 챙겨보면 좋을 학생")
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
            st.markdown(f"""
            <div class="mjp-card" style="border-left:3px solid {color};">
                <div style="font-weight:800; color:{TEXT};">{title}
                    <span style="color:{color};">{len(group)}명</span></div>
                <div class="mjp-muted" style="margin-top:6px; line-height:1.55;">{desc}</div>
                <div style="color:{TEXT}; font-size:var(--mjp-caption); margin-top:8px;">{names}{more}</div>
            </div>
            """, unsafe_allow_html=True)
