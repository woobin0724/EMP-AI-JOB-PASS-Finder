# -*- coding: utf-8 -*-
"""[big-patch 5단계] 선생님 화면 — 기업별 맞는 학생 · CSV."""

import csv
import io

from core import class_match as cm
from core.matching import calc_spec_score
from data.company_showcase import COMPANY_SHOWCASE
from data.departments import DEPARTMENT_LIST, get_category

C = COMPANY_SHOWCASE[0]
DEPT = next(d for d in DEPARTMENT_LIST if get_category(d) == C["category"])


def _user(uid, name, grade, certs=None, strengths=None, dept=DEPT):
    profile = {"dept": dept, "grade": grade}
    if certs is not None:
        profile["certs"] = certs
    if strengths is not None:
        profile["strengths"] = strengths
    return {"user_id": uid, "display_name": name, "profile": profile}


def test_score_matches_student_screen():
    u = _user("a", "가", 2.0, certs=list(C["required_certs"][:1]), strengths=list(C["ideal_talent"][:1]))
    fit = cm.student_fit(u, C)
    expected = calc_spec_score(grade=2.0, user_certs=u["profile"]["certs"], dept_category=get_category(DEPT),
                               company=C, strength_keywords=u["profile"]["strengths"])["final_score"]
    assert fit["score"] == expected


def test_sorted_and_skips_undiagnosed():
    users = [_user("a", "가", 4.5, certs=[]), _user("b", "나", 1.0, certs=list(C["required_certs"])),
             {"user_id": "c", "display_name": "다", "profile": {}}]
    rows = cm.students_for_company(users, C)
    assert [r["name"] for r in rows] == ["나", "가"]
    assert rows[0]["missing_certs"] == []
    assert set(rows[1]["missing_certs"]) == set(C["required_certs"])


def test_old_record_without_certs_is_flagged():
    fit = cm.student_fit(_user("a", "가", 2.0), C)
    assert fit["certs_known"] is False


def test_csv_utf8_bom_and_injection_safe():
    rows = [{"name": "=HYPERLINK(\"x\")", "dept": "기계과", "grade": 2.0, "target": "-",
             "stage_done": 1, "stage": "준비", "score": 72.5, "scored_at": "2026-10-17", "last_seen": "2026-10-17"}]
    data = cm.class_csv(rows, 5)
    assert data.startswith(b"\xef\xbb\xbf")
    parsed = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert parsed[0] == cm.CSV_COLUMNS
    assert parsed[1][0].startswith("'=")
    assert parsed[1][3] == "-" and parsed[1][5] == "72.5"
