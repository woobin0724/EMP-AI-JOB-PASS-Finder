# -*- coding: utf-8 -*-
"""
core/score_simulation.py
[big-patch 2단계] 점수 설명 · 시뮬레이션 — 스펙 진단 화면이 쓴다.

▣ 설계 원칙
   1) 점수는 새로 만들지 않는다. 전부 core.matching.calc_spec_score 를 입력만
      바꿔 다시 돌린 결과다. 그래서 시뮬레이션의 '+N점'은 실제 진단 점수와
      항상 같은 계산식에서 나온다.
   2) 순수 로컬 연산(API 호출 0회). 화면을 다시 그릴 때마다 돌려도 과금이 없다.
   3) Streamlit 에 의존하지 않는 순수 함수라 tests/ 에서 그대로 검증한다.
"""

from core.matching import (
    SIMILAR_CREDIT, FIT_MATCH_RATIO, FIT_NEUTRAL_RATIO, GRADE_MAX, GRADE_MIN,
    calc_spec_score,
)

# 합격 안정권 경계 — data/ogq_assets.sticker_key_for_score 와 같은 값
SAFE_LINE = 80.0
# 내신 시뮬레이션 단계(등급을 이만큼 올렸을 때)
GRADE_STEPS = (0.5, 1.0)
# 자격증 시뮬레이션에 보여줄 최대 개수
TOP_CERTS = 5


def _score(grade, certs, dept_category, company, strengths) -> float:
    return float(calc_spec_score(
        grade=grade, user_certs=certs, dept_category=dept_category,
        company=company, strength_keywords=strengths,
    )["final_score"])


def explain_items(result: dict, company: dict | None, grade: float,
                  certs: list, strengths: list) -> list[dict]:
    """
    '왜 이 점수인지' 항목별 설명. 반환: [{key, label, score, max, reason}, ...]
    문장은 계산에 실제로 쓴 값만으로 만든다(추측 없음).
    """
    w = result["weights"]
    items = []

    items.append({
        "key": "grade", "label": "내신 성취도", "score": result["grade_score"], "max": w["grade"],
        "reason": (f"{grade:.1f}등급 → {w['grade']}점 × ({GRADE_MAX:.0f} − {grade:.1f}) ÷ "
                   f"{GRADE_MAX - GRADE_MIN:.0f}. 1등급이면 만점, 5등급이면 0점이에요."),
    })

    details = result.get("cert_details") or []
    if details:
        full = [d["cert"] for d in details if d["ratio"] == 1.0]
        part = [d["cert"] for d in details if 0 < d["ratio"] < 1.0]
        miss = [d["cert"] for d in details if d["ratio"] == 0]
        bits = [f"요구 자격증 {len(details)}개 중 보유 {len(full)}개"]
        if part:
            bits.append(f"유사 자격증 인정 {len(part)}개({int(SIMILAR_CREDIT * 100)}%)")
        if miss:
            bits.append("없는 것: " + ", ".join(miss))
        cert_reason = " · ".join(bits) + f". 평균 인정 비율 × {w['cert']}점."
    elif company:
        cert_reason = (f"이 기업은 요구 자격증 정보가 없어 보유 개수로 계산했어요 "
                       f"(1개당 {w['cert'] / 5:g}점, 최대 {w['cert']}점). 보유 {len(certs)}개.")
    else:
        cert_reason = (f"목표 기업이 없어 보유 개수로 계산했어요 "
                       f"(1개당 {w['cert'] / 5:g}점, 최대 {w['cert']}점). 보유 {len(certs)}개.")
    items.append({"key": "cert", "label": "자격증 가산점", "score": result["cert_score"],
                  "max": w["cert"], "reason": cert_reason})

    ratio = result.get("fit_ratio")
    if not company:
        fit_reason = "목표 기업을 고르지 않아 중간값(배점의 50%)을 넣었어요."
    elif ratio == FIT_MATCH_RATIO:
        fit_reason = f"내 학과 계열과 기업 계열({company.get('category', '')})이 같아 만점이에요."
    elif ratio == FIT_NEUTRAL_RATIO:
        fit_reason = "기업 계열 정보가 없어 중간값(배점의 50%)을 넣었어요."
    else:
        fit_reason = (f"내 학과 계열과 기업 계열({company.get('category', '')})이 달라 "
                      f"배점의 25%만 인정했어요.")
    items.append({"key": "fit", "label": "전공 적합성", "score": result["fit_score"],
                  "max": w["fit"], "reason": fit_reason})

    ideal = (company or {}).get("ideal_talent") or []
    matched = result.get("matched_talent") or []
    if not company:
        talent_reason = "목표 기업을 고르면 인재상 키워드와 내 강점을 비교해요."
    elif not ideal:
        talent_reason = "이 기업은 인재상 정보가 없어 0점으로 두었어요."
    elif matched:
        talent_reason = (f"인재상 {len(ideal)}개 중 {len(matched)}개 일치({', '.join(matched)}). "
                         f"일치 비율 × {w['talent']}점.")
    else:
        talent_reason = (f"인재상({', '.join(ideal)})과 겹치는 강점이 없어요. "
                         f"내 경험에 맞는 키워드를 STEP 2 에서 골라보세요.")
    items.append({"key": "talent", "label": "인재상 일치도", "score": result["talent_score"],
                  "max": w["talent"], "reason": talent_reason})
    return items


def cert_gains(grade: float, certs: list, dept_category: str | None,
               company: dict | None, strengths: list, candidates: list,
               limit: int = TOP_CERTS) -> list[dict]:
    """
    '이 자격증을 따면 몇 점 오르나' — 아직 없는 자격증 하나를 더했을 때의 점수 변화.
    반환: [{cert, before, after, gain}, ...] (gain > 0, 큰 순)
    목표 기업이 있으면 그 기업의 요구 자격증을 먼저 후보로 둔다.
    """
    have = set(certs or [])
    pool = []
    for c in list((company or {}).get("required_certs") or []) + list(candidates or []):
        if c and c not in have and c not in pool:
            pool.append(c)
    before = _score(grade, list(certs or []), dept_category, company, strengths)
    out = []
    for cert in pool:
        after = _score(grade, list(certs or []) + [cert], dept_category, company, strengths)
        gain = round(after - before, 1)
        if gain > 0:
            out.append({"cert": cert, "before": before, "after": after, "gain": gain})
    out.sort(key=lambda r: (-r["gain"], r["cert"]))
    return out[:limit]


def grade_unlocks(grade: float, certs: list, dept_category: str | None,
                  strengths: list, companies: list,
                  steps: tuple = GRADE_STEPS) -> list[dict]:
    """
    '내신이 오르면 어느 기업이 안정권(80점)에 들어오나'.
    지금은 80점 미만인데 등급을 steps 만큼 올리면 80점 이상이 되는 기업.
    반환: [{step, target_grade, company, before, after}, ...] (가장 작은 step 기준 1회만)
    """
    out = []
    for company in companies:
        before = _score(grade, certs, dept_category, company, strengths)
        if before >= SAFE_LINE:
            continue
        for step in steps:
            target = round(max(GRADE_MIN, grade - step), 1)
            if target >= grade:
                break
            after = _score(target, certs, dept_category, company, strengths)
            if after >= SAFE_LINE:
                out.append({"step": step, "target_grade": target, "company": company,
                            "before": before, "after": after})
                break
    out.sort(key=lambda r: (r["step"], -r["after"]))
    return out


def safe_now(grade: float, certs: list, dept_category: str | None,
             strengths: list, companies: list) -> int:
    """지금 이미 안정권(80점 이상)인 기업 수."""
    return sum(1 for c in companies
               if _score(grade, certs, dept_category, c, strengths) >= SAFE_LINE)
