# -*- coding: utf-8 -*-
"""
core/class_match.py
[big-patch 5단계] 선생님 반 화면 — '이 기업에 맞는 학생 목록' · 반 현황 CSV

점수는 새로 만들지 않는다. 학생이 스펙 진단에서 저장한 학과·내신·자격증·강점으로
core.matching.calc_spec_score 를 기업마다 다시 돌린다(학생 화면과 같은 숫자). 로컬 연산, API 0회.
"""

import csv
import io

from core.matching import calc_spec_score
from core.score_simulation import SAFE_LINE
from data.departments import get_category

CAUTION_LINE = 50.0
CSV_COLUMNS = ["이름", "학과", "내신", "목표 기업", "진행 단계", "최근 점수", "최근 진단일", "최근 활동"]


def student_fit(user: dict, company: dict) -> dict | None:
    """학생 1명의 이 기업 점수. 스펙 진단 기록(학과·내신)이 없으면 None."""
    profile = user.get("profile") or {}
    dept, grade = profile.get("dept"), profile.get("grade")
    if not dept or grade is None:
        return None
    certs = list(profile.get("certs") or [])
    result = calc_spec_score(
        grade=float(grade), user_certs=certs, dept_category=get_category(dept),
        company=company, strength_keywords=list(profile.get("strengths") or []),
    )
    missing = [d["cert"] for d in result.get("cert_details") or [] if d["ratio"] == 0]
    score = float(result["final_score"])
    return {
        "user_id": user.get("user_id", ""),
        "name": user.get("display_name") or "이름 미입력",
        "dept": dept,
        "grade": float(grade),
        "score": score,
        "band": "합격 안정권" if score >= SAFE_LINE else ("분발 필요" if score >= CAUTION_LINE else "보완 시급"),
        "missing_certs": missing,
        # 예전 기록에는 자격증이 저장되지 않았다 — 점수가 낮게 나올 수 있음을 표시한다
        "certs_known": "certs" in profile,
    }


def students_for_company(users: list[dict], company: dict) -> list[dict]:
    """점수 높은 순. 진단 기록이 없는 학생은 빠진다."""
    rows = [r for r in (student_fit(u, company) for u in users) if r]
    rows.sort(key=lambda r: (-r["score"], r["name"]))
    return rows


def _cell(value) -> str:
    """엑셀 수식 주입 방지 — '=' '+' '@' 등으로 시작하는 글자는 앞에 ' 를 붙인다."""
    text = "" if value is None else str(value)
    if text and (text[0] in "=+@\t\r" or (text[0] == "-" and len(text) > 1 and not text[1:].replace(".", "").isdigit())):
        return "'" + text
    return text


def class_csv(rows: list[dict], total_stages: int) -> bytes:
    """반 현황 CSV (엑셀에서 한글이 깨지지 않게 UTF-8 BOM)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_COLUMNS)
    for r in rows:
        w.writerow([_cell(v) for v in [
            r.get("name", ""), r.get("dept", ""),
            "" if r.get("grade") is None else r["grade"],
            r.get("target", ""),
            f"{r.get('stage_done', 0)}/{total_stages} {r.get('stage', '')}".strip(),
            "" if r.get("score") is None else r["score"],
            r.get("scored_at", ""), r.get("last_seen", ""),
        ]])
    return buf.getvalue().encode("utf-8-sig")
