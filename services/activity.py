# -*- coding: utf-8 -*-
"""
services/activity.py
[Phase 2] 학생 활동 기록 — 선생님 대시보드의 데이터 공급원

왜 별도 모듈인가
----------------
선생님 대시보드(2-3)는 "학생별 목표 기업 / 로드맵 단계 / 최근 매칭 점수"를
보여줘야 한다. 그런데 기존 화면들은 점수를 **계산만 하고 버리고** 있었다.
기록을 남기지 않으면 대시보드는 영원히 빈 표다.

그렇다고 화면 코드에 store.save_*() 를 흩뿌리면 두 가지 문제가 생긴다.

  1) 쓰기 폭주
     스펙 진단 화면은 슬라이더를 한 칸 움직일 때마다 스크립트를 재실행한다.
     매 rerun 마다 JSON 을 쓰면 디스크가 갈린다. 내신 슬라이더를 드래그하면
     초당 수십 번 저장된다.
  2) 중복 로직
     "로그인 안 했으면 저장 안 함" 같은 가드를 화면마다 반복하게 된다.

그래서 이 모듈이 **디바운스(중복 제거) + 가드**를 전담한다.
각 함수는 직전에 기록한 값과 같으면 조용히 no-op 한다.
"""

import streamlit as st

from core.catalog import completed_milestones
from data.roadmap import stage_label
from services import store


def _uid() -> str:
    auth = st.session_state.get("auth") or {}
    return auth.get("user_id", "")


def _changed(slot: str, value) -> bool:
    """
    세션에 남긴 직전 값과 비교해 실제로 바뀌었을 때만 True.
    이 한 줄이 슬라이더 드래그로 인한 디스크 쓰기 폭주를 막는다.
    """
    key = f"_act_{slot}"
    if st.session_state.get(key) == value:
        return False
    st.session_state[key] = value
    return True


# ------------------------------------------------------------
# 스펙 진단
# ------------------------------------------------------------
def record_spec(result: dict, dept: str, grade: float, company: dict | None) -> None:
    """
    진단 결과를 기록한다.

    점수 히스토리는 '의미 있게 바뀐 순간'만 남긴다. 소수점 한 자리까지
    같은 점수를 반복 저장하면 히스토리가 노이즈로 가득 찬다.
    """
    uid = _uid()
    if not uid:
        return

    score = round(float(result.get("final_score", 0)), 1)
    company_id = (company or {}).get("id", "")
    company_name = (company or {}).get("name", "")

    # 프로필 스냅샷 — 선생님 대시보드의 '목표 기업' 칼럼이 여기서 나온다
    profile_sig = (dept, round(float(grade), 1), company_id)
    if _changed("profile", profile_sig):
        store.save_profile(
            uid, dept=dept, grade=float(grade),
            target_company_id=company_id, target_company_name=company_name,
        )

    if _changed("score", (score, company_id)):
        store.record_score(uid, score, company_id, company_name)


# ------------------------------------------------------------
# 커리어 로드맵
# ------------------------------------------------------------
def record_milestones(milestones: dict) -> None:
    """마일스톤 체크 상태를 저장한다 (대시보드의 '진행 단계' 칼럼)."""
    uid = _uid()
    if not uid:
        return

    signature = tuple(sorted((k, bool(v)) for k, v in (milestones or {}).items()))
    if _changed("milestones", signature):
        store.save_milestones(uid, milestones)


# ------------------------------------------------------------
# 기업 열람
# ------------------------------------------------------------
def record_company_view(company: dict | None) -> None:
    """기업 가이드 열람 이력 (마이페이지 '조사한 기업')."""
    uid = _uid()
    if not uid or not company:
        return
    if _changed("viewed", company.get("id", "")):
        store.record_view(uid, company.get("id", ""), company.get("name", ""))


# ------------------------------------------------------------
# 대시보드용 요약
# ------------------------------------------------------------
def student_summary(user: dict) -> dict:
    """
    학생 레코드 하나를 대시보드 행으로 변환한다.
    아직 아무 활동도 없는 학생은 '-' 로 채워 표가 깨지지 않게 한다.
    """
    profile = user.get("profile") or {}
    history = user.get("score_history") or []
    milestones = user.get("milestones") or {}
    done = completed_milestones(milestones)

    latest = history[0] if history else None

    return {
        "user_id": user.get("user_id", ""),
        "name": user.get("display_name") or "이름 미입력",
        "dept": profile.get("dept") or "-",
        "grade": profile.get("grade"),
        "target": profile.get("target_company_name") or "-",
        "score": latest["score"] if latest else None,
        "scored_at": (latest["at"][:10] if latest else "-"),
        "stage": stage_label(done),
        "stage_done": done,
        "last_seen": (user.get("last_seen_at") or "")[:10],
        "active": bool(history or milestones or profile),
    }
