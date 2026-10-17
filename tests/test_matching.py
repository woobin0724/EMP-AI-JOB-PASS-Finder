# -*- coding: utf-8 -*-
"""[big-patch 2단계] 매칭 점수 — 기업 유형별 배점 · 설명 · 시뮬레이션."""

import pytest

from core import matching as m
from core import score_simulation as sim
from data.company_showcase import COMPANY_SHOWCASE


def _company(size_tag="중견기업", category="기계", certs=("기계가공기능사",),
             talent=("성실", "도전")):
    return {"id": "t", "name": "테스트기업", "size_tag": size_tag, "category": category,
            "required_certs": list(certs), "ideal_talent": list(talent)}


# ---------- 배점표 ----------

def test_every_weight_profile_sums_to_100():
    assert sum(m.DEFAULT_WEIGHTS.values()) == 100
    for tag, w in m.WEIGHTS_BY_TYPE.items():
        assert sum(w.values()) == 100, tag
        assert set(w) == {"grade", "cert", "fit", "talent"}


def test_all_showcase_size_tags_have_profile():
    for c in COMPANY_SHOWCASE:
        assert c["size_tag"] in m.WEIGHTS_BY_TYPE


def test_weights_for_unknown_or_none_is_default():
    assert m.weights_for(None) == m.DEFAULT_WEIGHTS
    assert m.weights_for({"size_tag": "모르는유형"}) == m.DEFAULT_WEIGHTS


def test_types_differ_where_documented():
    assert m.WEIGHTS_BY_TYPE["공기업"]["cert"] > m.DEFAULT_WEIGHTS["cert"]
    assert m.WEIGHTS_BY_TYPE["대기업"]["talent"] > m.DEFAULT_WEIGHTS["talent"]
    assert m.WEIGHTS_BY_TYPE["중소기업"]["fit"] > m.DEFAULT_WEIGHTS["fit"]


# ---------- 기존 동작 유지 (일반 진단 · 중견기업 = 예전 30/40/20/10) ----------

def test_no_company_matches_legacy_formula():
    r = m.calc_spec_score(grade=2.0, user_certs=["a", "b"], dept_category="기계", company=None)
    assert r["grade_score"] == 22.5
    assert r["cert_score"] == 16.0          # 8점 × 2개
    assert r["fit_score"] == 10.0           # 중립
    assert r["talent_score"] == 0.0
    assert r["final_score"] == 48.5
    assert r["weights"] == m.DEFAULT_WEIGHTS
    assert r["weight_profile"] == "일반 진단"


def test_midsize_company_matches_legacy_formula():
    c = _company("중견기업")
    r = m.calc_spec_score(grade=1.0, user_certs=["기계가공기능사"], dept_category="기계",
                          company=c, strength_keywords=["성실"])
    assert (r["grade_score"], r["cert_score"], r["fit_score"], r["talent_score"]) == (30.0, 40.0, 20.0, 5.0)
    assert r["final_score"] == 95.0


def test_legacy_component_functions_default_args_unchanged():
    assert m.convert_grade_to_score(1.0) == 30.0
    assert m.calc_fit_score("기계", "기계") == 20.0
    assert m.calc_fit_score("기계", "IT/정보통신") == 5.0
    assert m.calc_fit_score("기계", None) == 10.0
    assert m.calc_cert_score(["x"] * 9, None)[0] == 40.0


@pytest.mark.parametrize("tag", list(m.WEIGHTS_BY_TYPE))
def test_perfect_spec_is_100_for_every_type(tag):
    c = _company(tag)
    r = m.calc_spec_score(grade=1.0, user_certs=["기계가공기능사"], dept_category="기계",
                          company=c, strength_keywords=["성실", "도전"])
    assert r["final_score"] == 100.0


@pytest.mark.parametrize("tag", list(m.WEIGHTS_BY_TYPE))
def test_components_never_exceed_weights(tag):
    c = _company(tag)
    w = m.WEIGHTS_BY_TYPE[tag]
    for grade in (1.0, 2.7, 5.0):
        r = m.calc_spec_score(grade=grade, user_certs=["기계가공기능사", "x"],
                              dept_category="전자/전기", company=c,
                              strength_keywords=["성실", "도전", "협업"])
        assert r["grade_score"] <= w["grade"]
        assert r["cert_score"] <= w["cert"]
        assert r["fit_score"] <= w["fit"]
        assert r["talent_score"] <= w["talent"]
        assert 0 <= r["final_score"] <= 100


def test_public_company_rewards_certs_more_than_grade():
    """같은 학생이라도 공기업은 자격증 비중이 커서, 자격증만 있는 학생이 더 높게 나온다."""
    args = dict(grade=4.0, user_certs=["기계가공기능사"], dept_category="기계",
                strength_keywords=[])
    public = m.calc_spec_score(company=_company("공기업"), **args)["final_score"]
    big = m.calc_spec_score(company=_company("대기업"), **args)["final_score"]
    assert public > big


def test_fit_ratio_values():
    assert m.fit_ratio("기계", "기계") == 1.0
    assert m.fit_ratio("기계", "IT/정보통신") == 0.25
    assert m.fit_ratio("기계", None) == 0.5


def test_tips_use_profile_weight():
    r = m.calc_spec_score(grade=4.5, user_certs=[], dept_category="기계",
                          company=_company("공기업"))
    assert any("25점" in t for t in r["tips"])


# ---------- 왜 이 점수인지 ----------

def test_explain_items_cover_four_parts_and_match_result():
    c = _company("대기업")
    r = m.calc_spec_score(grade=2.0, user_certs=[], dept_category="IT/정보통신",
                          company=c, strength_keywords=["성실"])
    items = sim.explain_items(r, c, 2.0, [], ["성실"])
    assert [i["key"] for i in items] == ["grade", "cert", "fit", "talent"]
    assert sum(i["max"] for i in items) == 100
    by = {i["key"]: i for i in items}
    assert by["cert"]["score"] == r["cert_score"]
    assert "기계가공기능사" in by["cert"]["reason"]          # 없는 자격증을 알려준다
    assert "25%" in by["fit"]["reason"]                     # 계열 불일치
    assert "성실" in by["talent"]["reason"]
    assert all(i["reason"] for i in items)


def test_explain_items_without_company():
    r = m.calc_spec_score(grade=3.0, user_certs=["a"], dept_category="기계", company=None)
    items = sim.explain_items(r, None, 3.0, ["a"], [])
    assert "목표 기업" in items[1]["reason"]
    assert "50%" in items[2]["reason"]


# ---------- 시뮬레이션 ----------

def test_cert_gain_equals_real_score_difference():
    c = _company("공기업", certs=("기계가공기능사", "용접기능사"))
    gains = sim.cert_gains(3.0, [], "기계", c, [], candidates=["무관자격증"])
    names = [g["cert"] for g in gains]
    assert names[:2] == ["기계가공기능사", "용접기능사"]
    for g in gains:
        after = m.calc_spec_score(grade=3.0, user_certs=[g["cert"]], dept_category="기계",
                                  company=c)["final_score"]
        assert g["after"] == after
        assert g["gain"] == round(after - g["before"], 1)
        assert g["gain"] > 0
    assert "무관자격증" not in names                 # 요구 자격증이 아니면 0점 → 빠진다


def test_cert_gain_skips_owned_and_caps():
    c = _company(certs=("기계가공기능사",))
    assert sim.cert_gains(3.0, ["기계가공기능사"], "기계", c, [], candidates=[]) == []
    no_company = sim.cert_gains(3.0, ["a", "b", "c", "d", "e"], "기계", None, [], candidates=["f"])
    assert no_company == []                         # 이미 40점 만점


def test_grade_unlocks_cross_safe_line():
    c = _company("공기업")
    # 공기업 배점: 자격증·전공·인재상 만점 75 + 내신 25 × (5 − 등급) ÷ 4
    unlocks = sim.grade_unlocks(4.5, ["기계가공기능사"], "기계", ["성실", "도전"], [c])
    before = m.calc_spec_score(grade=4.5, user_certs=["기계가공기능사"], dept_category="기계",
                               company=c, strength_keywords=["성실", "도전"])["final_score"]
    assert before < sim.SAFE_LINE
    assert len(unlocks) == 1
    u = unlocks[0]
    assert before == 78.1
    assert (u["step"], u["target_grade"], u["after"]) == (0.5, 4.0, 81.2)


def test_grade_unlocks_excludes_already_safe_and_hopeless():
    safe = _company("공기업")
    hopeless = _company("공기업", category="농생명", certs=("없는자격증",), talent=("x",))
    out = sim.grade_unlocks(1.2, ["기계가공기능사"], "기계", ["성실", "도전"], [safe, hopeless])
    assert out == []
    assert sim.safe_now(1.2, ["기계가공기능사"], "기계", ["성실", "도전"], [safe, hopeless]) == 1


def test_grade_unlocks_at_top_grade_is_empty():
    assert sim.grade_unlocks(1.0, [], "기계", [], [_company()]) == []


def test_simulation_runs_on_all_showcase_companies():
    out = sim.grade_unlocks(3.0, ["전기기능사"], "전자/전기", ["성실"], COMPANY_SHOWCASE)
    for u in out:
        assert u["after"] >= sim.SAFE_LINE > u["before"]
