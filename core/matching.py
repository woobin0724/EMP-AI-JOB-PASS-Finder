# -*- coding: utf-8 -*-
"""
core/matching.py
[W3 요구사항 #1] 100점 만점 정량적 합격 점수 공식 + 채용공고 검색/필터링 로직

▣ 비용 방어 원칙 (매우 중요)
   이 모듈의 모든 연산은 **AI API를 단 한 번도 호출하지 않는 순수 파이썬 함수**다.
   점수 산출은 결정론적(deterministic) 알고리즘이므로 LLM에 맡길 이유가 없고,
   슬라이더를 한 칸 움직일 때마다 API가 호출되면 과금이 폭발한다.
   따라서 점수 계산은 전부 로컬에서, 즉시, 무료로 수행된다.

▣ 총점 = 내신 성취도(30) + 자격증 가산점(40) + 전공 적합성(20) + 인재상 일치도(10)

  1) 내신 성취도 (30점)
     마이스터고 성취평가제 5등급을 선형 환산한다.
         Score = 30 * (5.0 - Grade) / 4.0
     · 1.0등급 → 30.0점   · 2.0등급 → 22.5점
     · 3.0등급 → 15.0점   · 5.0등급 →  0.0점

  2) 자격증 가산점 (40점)
     목표 기업이 요구하는 자격증 각각에 대해 인정 비율을 매기고 평균을 낸다.
         · 정확히 일치 보유 ................ 100% 인정
         · 직무 유사 자격증 보유 ............  70% 인정
           (예: 전기기능사 ↔ 전기산업기사, 컴퓨터응용선반 ↔ 밀링기능사)
         · 미보유 ..........................   0%
         Score = (인정 비율 평균) * 40
     목표 기업 미선택 시에는 비교 대상이 없으므로 보유 개수 기반 약식 점수
     (1개당 8점, 최대 40점)로 대체한다.

  3) 전공 적합성 (20점)
     학과 계열(category)과 목표 기업의 산업 분류 비교.
         · 일치 20점  · 불일치 5점  · 기업 미선택(중립) 10점

  4) 인재상 일치도 (10점)
     학생이 고른 강점 키워드가 기업 인재상 키워드와 겹치는 비율 * 10점.
"""

import pandas as pd

from services.text_normalize import normalize, build_search_blob
from data.certifications import CERT_CODE_TO_NAME, is_similar

# ============================================================
# 배점 상수 (총합 100점)
# ============================================================
GRADE_MIN, GRADE_MAX = 1.0, 5.0
GRADE_WEIGHT = 30   # 내신 성취도
CERT_WEIGHT = 40    # 자격증 가산점
FIT_WEIGHT = 20     # 전공 적합성
TALENT_WEIGHT = 10  # 인재상 일치도

SIMILAR_CREDIT = 0.7  # 유사 자격증 인정 비율 (70%)

CERT_BONUS_PER_ITEM_NO_COMPANY = 8   # 기업 미선택 시 자격증 1개당 약식 점수
CERT_BONUS_MAX_NO_COMPANY = CERT_WEIGHT

FIT_MATCH_SCORE = 20.0     # 계열 일치
FIT_MISMATCH_SCORE = 5.0   # 계열 불일치
FIT_NEUTRAL_SCORE = 10.0   # 기업 미선택(중립값)


# ============================================================
# 1. 내신 성취도 (30점)
# ============================================================
def convert_grade_to_score(grade: float, max_score: float = GRADE_WEIGHT) -> float:
    """
    5등급 성취평가제를 선형 환산한다.
        Score = max_score * (GRADE_MAX - grade) / (GRADE_MAX - GRADE_MIN)
    1.0등급이 만점, 5.0등급이 0점이며 범위를 벗어난 값은 자동으로 잘라낸다.
    """
    try:
        grade = float(grade)
    except (TypeError, ValueError):
        grade = GRADE_MAX
    grade = max(GRADE_MIN, min(GRADE_MAX, grade))
    score = max_score * (GRADE_MAX - grade) / (GRADE_MAX - GRADE_MIN)
    return round(score, 1)


# ============================================================
# 2. 자격증 가산점 (40점)
# ============================================================
def calc_cert_score(user_certs: list, required_certs: list | None) -> tuple[float, list]:
    """
    자격증 가산점(40점 만점)과 항목별 상세 내역을 함께 반환한다.
    반환값: (점수, [{cert, status, ratio, matched_by}, ...])
    """
    user_certs = list(user_certs or [])

    # 목표 기업 미선택 → 보유 개수 기반 약식 점수
    if not required_certs:
        score = min(len(user_certs) * CERT_BONUS_PER_ITEM_NO_COMPANY,
                    CERT_BONUS_MAX_NO_COMPANY)
        return round(float(score), 1), []

    details = []
    total_ratio = 0.0
    for req in required_certs:
        if req in user_certs:
            ratio, status, by = 1.0, "정확히 보유 (100% 인정)", req
        else:
            similar = next((c for c in user_certs if is_similar(c, req)), None)
            if similar:
                ratio, status, by = SIMILAR_CREDIT, "유사 자격증 보유 (70% 인정)", similar
            else:
                ratio, status, by = 0.0, "미보유", None
        total_ratio += ratio
        details.append({"cert": req, "status": status, "ratio": ratio, "matched_by": by})

    avg_ratio = total_ratio / len(required_certs)
    return round(avg_ratio * CERT_WEIGHT, 1), details


def calc_cert_match_score(user_cert_names: list, required_cert_names: list) -> float:
    """공고 카드용 자격증 일치율(0~100). 유사 자격증도 70%로 인정한다."""
    if not required_cert_names:
        return 100.0
    total = 0.0
    for req in required_cert_names:
        if req in (user_cert_names or []):
            total += 1.0
        elif any(is_similar(c, req) for c in (user_cert_names or [])):
            total += SIMILAR_CREDIT
    return round(total / len(required_cert_names) * 100, 1)


# ============================================================
# 3. 전공 적합성 (20점)
# ============================================================
def calc_fit_score(dept_category: str | None, company_category: str | None) -> float:
    """학과 계열과 기업 산업분류의 일치 여부로 20/10/5점을 부여한다."""
    if not company_category:
        return FIT_NEUTRAL_SCORE
    if dept_category and dept_category == company_category:
        return FIT_MATCH_SCORE
    return FIT_MISMATCH_SCORE


# ============================================================
# 4. 인재상 일치도 (10점)
# ============================================================
def calc_talent_score(strength_keywords: list, ideal_talent: list | None) -> tuple[float, list]:
    """
    강점 키워드 ∩ 기업 인재상 키워드의 비율 * 10점.
    반환값: (점수, 일치한 키워드 리스트)
    """
    if not ideal_talent or not strength_keywords:
        return 0.0, []
    matched = [k for k in strength_keywords if k in ideal_talent]
    ratio = min(len(matched) / len(ideal_talent), 1.0)
    return round(ratio * TALENT_WEIGHT, 1), matched


# ============================================================
# 5. 종합 점수 + 자동 코칭 피드백
# ============================================================
def build_feedback(result: dict, company: dict | None) -> list:
    """점수 구성표를 읽고 학생에게 줄 다음 행동 제안을 만든다 (LLM 미사용)."""
    tips = []
    if result["grade_score"] < GRADE_WEIGHT * 0.6:
        tips.append("내신 점수 비중이 30점으로 가장 크지는 않지만, 남은 학기 성적 관리로 아직 끌어올릴 수 있어요.")
    missing = [d["cert"] for d in result.get("cert_details", []) if d["ratio"] == 0.0]
    partial = [d for d in result.get("cert_details", []) if d["ratio"] == SIMILAR_CREDIT]
    if missing:
        tips.append(f"'{missing[0]}' 취득이 지금 점수를 가장 크게 올리는 지름길입니다.")
    if partial:
        d = partial[0]
        tips.append(f"'{d['matched_by']}'은 '{d['cert']}'의 유사 자격증으로 70%만 인정돼요. 정식 취득 시 남은 30%를 채웁니다.")
    if not company:
        tips.append("목표 기업을 선택하면 요구 자격증·인재상까지 반영된 정밀 점수로 바뀝니다.")
    else:
        if result["fit_score"] == FIT_MISMATCH_SCORE:
            tips.append(f"학과 계열과 {company['name']}의 산업 분류가 달라 적합성 점수가 낮습니다. 같은 계열 기업도 함께 살펴보세요.")
        if result["talent_score"] == 0:
            tips.append(f"인재상 키워드({', '.join(company.get('ideal_talent', []))})와 겹치는 강점을 골라두면 10점을 챙길 수 있어요.")
    if not tips:
        tips.append("모든 항목이 고르게 채워졌습니다. 이제 면접 실전 연습에 집중하세요.")
    return tips


def calc_spec_score(
    grade: float,
    user_certs: list,
    dept_category: str | None,
    company: dict | None,
    strength_keywords: list | None = None,
) -> dict:
    """
    100점 만점 '취업 등용문 점수'를 계산한다.
    ※ 순수 파이썬 연산으로만 이루어져 있으며 외부 API를 호출하지 않는다.
    """
    strength_keywords = list(strength_keywords or [])

    grade_score = convert_grade_to_score(grade)

    required_certs = company.get("required_certs") if company else None
    cert_score, cert_details = calc_cert_score(user_certs, required_certs)

    company_category = company.get("category") if company else None
    fit_score = calc_fit_score(dept_category, company_category)

    ideal_talent = company.get("ideal_talent") if company else None
    talent_score, matched_talent = calc_talent_score(strength_keywords, ideal_talent)

    final_score = round(grade_score + cert_score + fit_score + talent_score, 1)
    final_score = max(0.0, min(100.0, final_score))

    result = {
        "final_score": final_score,
        "grade_score": grade_score,
        "cert_score": cert_score,
        "cert_details": cert_details,
        "fit_score": fit_score,
        "talent_score": talent_score,
        "matched_talent": matched_talent,
        "weights": {
            "grade": GRADE_WEIGHT, "cert": CERT_WEIGHT,
            "fit": FIT_WEIGHT, "talent": TALENT_WEIGHT,
        },
    }
    result["tips"] = build_feedback(result, company)
    return result


# ============================================================
# 6. 채용공고 검색 · 필터링
# ============================================================
def filter_results(records: list, keyword: str) -> list:
    """company / title / required_certs 중 하나라도 키워드를 포함하는 공고만 남긴다."""
    if not keyword:
        return records

    key = normalize(keyword)
    filtered = []
    for r in records:
        certs = r.get("required_certs", []) or []
        certs_str = " ".join(certs) if isinstance(certs, list) else str(certs)
        haystack = build_search_blob(r.get("company", ""), r.get("title", ""), certs_str)
        if key in haystack:
            filtered.append(r)
    return filtered


def attach_search_blob(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """검색용 정규화 문자열 컬럼(_blob)을 추가한다."""
    df = jobs_df.copy()

    def make_blob(row):
        certs = row.get("required_certs", [])
        certs_str = " ".join(certs) if isinstance(certs, list) else str(certs)
        return build_search_blob(
            row.get("company", ""), row.get("title", ""),
            row.get("department", ""), row.get("region", ""), certs_str,
        )

    df["_blob"] = df.apply(make_blob, axis=1)
    return df


def search_jobs(jobs_df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """기업명/자격증명/직무명/지역 통합 키워드 검색 (정규화 기반 부분일치)."""
    if not keyword:
        return jobs_df
    key = normalize(keyword)
    return jobs_df[jobs_df["_blob"].str.contains(key, na=False)]


def filter_jobs(
    jobs_df: pd.DataFrame,
    department: str | None = None,
    cert_level: str | None = None,
    company_type: str | None = None,
    region_keyword: str | None = None,
) -> pd.DataFrame:
    """학과 / 자격증 등급 / 기업 유형 / 지역 조건으로 필터링한다."""
    df = jobs_df

    if department and department != "전체":
        df = df[df["department"] == department]

    if company_type and company_type != "전체":
        df = df[df["company_type"] == company_type]

    if region_keyword:
        df = df[df["region"].apply(lambda r: normalize(region_keyword) in normalize(r))]

    if cert_level and cert_level != "전체":
        from data.certifications import CERTIFICATIONS
        level_names = {c["name"] for c in CERTIFICATIONS if c["level"] == cert_level}

        def has_level(certs):
            if not isinstance(certs, list):
                return False
            return any(c in level_names for c in certs)

        df = df[df["required_certs"].apply(has_level)]

    return df


def build_match_result(job_row, user_cert_names: list, grade: float) -> dict:
    """공고 1건에 대한 매칭 점수 + 1:1 피드백 문구를 생성한다."""
    required = job_row.get("required_certs", []) or []
    matched = [c for c in required if c in user_cert_names]
    missing = [c for c in required if c not in user_cert_names]

    cert_score = calc_cert_match_score(user_cert_names, required)
    grade_score = convert_grade_to_score(grade, max_score=100)
    final_score = round(cert_score * 0.5 + grade_score * 0.5, 1)

    parts = []
    if matched:
        parts.append(f"보유한 '{matched[0]}'은(는) 이 공고에서 우대하는 핵심 자격증입니다.")
    if missing:
        parts.append(f"'{missing[0]}'을 취득하면 매칭 점수를 더 끌어올릴 수 있어요.")
    else:
        parts.append("요구 자격증을 모두 갖췄습니다. 자신 있게 지원해보세요!")

    return {
        "final_score": final_score,
        "cert_score": cert_score,
        "grade_score": grade_score,
        "matched": matched,
        "missing": missing,
        "feedback": " ".join(parts),
    }
