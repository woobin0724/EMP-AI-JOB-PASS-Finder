# -*- coding: utf-8 -*-
"""
core/spec_score.py
'취업 등용문' 점수(100점 만점) 산출 로직

최종 점수 = 내신 성취도(30) + 자격증 가산점(40) + 전공 적합성(20) + 기업 인재상 일치도(10)

- 내신(30): 5등급제(1.0~5.0)를 선형 환산. 1.0등급=30점, 5.0등급=0점.
  (예: 2.0등급 = 22.5점 — 요구사항 예시와 일치)
- 자격증(40): 기업이 요구하는 자격증 각각에 대해
    · 정확히 보유 -> 100% 인정
    · 유사 자격증 보유(SIMILAR_CERTS) -> 70% 인정
    · 미보유 -> 0%
  인정 비율의 평균 × 40점. 기업을 아직 선택하지 않았다면 "보유 자격증 개수"
  기반 약식 점수(자격증 1개당 8점, 최대 40점)로 대체한다.
- 적합성(20): 학과의 산업분류(category)와 기업의 산업분류가
    · 동일 -> 20점
    · 없음(기업 미선택) -> 10점(중립값)
    · 다름 -> 5점
- 인재상(10): 학생이 입력한 강점 키워드와 기업의 ideal_talent 키워드 중
  일치하는 키워드 비율 × 10점. 기업 미선택 시 0점.
"""

from data.certifications import is_similar

GRADE_MIN, GRADE_MAX = 1.0, 5.0
GRADE_WEIGHT = 30
CERT_WEIGHT = 40
FIT_WEIGHT = 20
TALENT_WEIGHT = 10

CERT_BONUS_PER_ITEM_NO_COMPANY = 8  # 기업 미선택 시 자격증 1개당 약식 가산점
CERT_BONUS_MAX_NO_COMPANY = 40


def convert_grade_to_score(grade: float, max_score: float = GRADE_WEIGHT) -> float:
    """5등급제(1.0~5.0)를 max_score 만점으로 선형 환산한다. 1.0=만점, 5.0=0점."""
    grade = max(GRADE_MIN, min(GRADE_MAX, grade))
    return round(max_score - (grade - GRADE_MIN) * (max_score / (GRADE_MAX - GRADE_MIN)), 1)


def calc_cert_score(user_certs: list, required_certs: list | None) -> tuple[float, list]:
    """
    자격증 가산점(40점 만점)을 계산한다.
    required_certs가 없으면(기업 미선택) 보유 개수 기반 약식 점수를 반환한다.
    반환값: (점수, 상세내역 리스트[{cert, status, ratio}])
    """
    if not required_certs:
        score = min(len(user_certs) * CERT_BONUS_PER_ITEM_NO_COMPANY, CERT_BONUS_MAX_NO_COMPANY)
        return round(score, 1), []

    details = []
    total_ratio = 0.0
    for req in required_certs:
        if req in user_certs:
            ratio, status = 1.0, "정확히 보유"
        elif any(is_similar(owned, req) for owned in user_certs):
            ratio, status = 0.7, "유사 자격증 보유(70% 인정)"
        else:
            ratio, status = 0.0, "미보유"
        total_ratio += ratio
        details.append({"cert": req, "status": status, "ratio": ratio})

    avg_ratio = total_ratio / len(required_certs)
    return round(avg_ratio * CERT_WEIGHT, 1), details


def calc_fit_score(dept_category: str | None, company_category: str | None) -> float:
    """전공 적합성(20점 만점): 학과 산업분류와 기업 산업분류 일치도."""
    if not company_category:
        return FIT_WEIGHT / 2  # 기업 미선택 시 중립값
    if dept_category == company_category:
        return FIT_WEIGHT
    return FIT_WEIGHT * 0.25


def calc_talent_score(strength_keywords: list, ideal_talent: list | None) -> float:
    """기업 인재상 일치도(10점 만점): 강점 키워드와 인재상 키워드 매칭 비율."""
    if not ideal_talent:
        return 0.0
    if not strength_keywords:
        return 0.0
    matched = [k for k in strength_keywords if k in ideal_talent]
    ratio = len(matched) / len(ideal_talent)
    return round(min(ratio, 1.0) * TALENT_WEIGHT, 1)


def calc_spec_score(
    grade: float,
    user_certs: list,
    dept_category: str | None,
    company: dict | None,
    strength_keywords: list | None = None,
) -> dict:
    """4개 항목을 합산해 100점 만점 '취업 등용문 점수'를 계산한다."""
    strength_keywords = strength_keywords or []

    grade_score = convert_grade_to_score(grade)
    required_certs = company["required_certs"] if company else None
    cert_score, cert_details = calc_cert_score(user_certs, required_certs)
    company_category = company["category"] if company else None
    fit_score = calc_fit_score(dept_category, company_category)
    ideal_talent = company["ideal_talent"] if company else None
    talent_score = calc_talent_score(strength_keywords, ideal_talent)

    final_score = round(grade_score + cert_score + fit_score + talent_score, 1)
    final_score = max(0, min(100, final_score))

    return {
        "final_score": final_score,
        "grade_score": grade_score,
        "cert_score": cert_score,
        "cert_details": cert_details,
        "fit_score": fit_score,
        "talent_score": talent_score,
    }
