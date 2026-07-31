# -*- coding: utf-8 -*-
"""
core/matching.py
채용공고 검색·필터링 및 매칭 스코어링 로직
"""

import pandas as pd

from services.text_normalize import normalize, build_search_blob
from data.certifications import CERT_CODE_TO_NAME


def filter_results(records: list, keyword: str) -> list:
    """
    company / title / required_certs 중 하나라도 keyword(정규화 기준 부분일치)를
    포함하는 레코드만 남긴다. records는 list[dict] 형태(딕셔너리 리스트)를 받는다.
    keyword가 비어있으면 전체 리스트를 그대로 반환한다.
    """
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
            row.get("company", ""),
            row.get("title", ""),
            row.get("department", ""),
            row.get("region", ""),
            certs_str,
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
        # 요구 자격증 중 하나라도 해당 등급이면 통과
        from data.certifications import CERTIFICATIONS
        level_names = {c["name"] for c in CERTIFICATIONS if c["level"] == cert_level}

        def has_level(certs):
            if not isinstance(certs, list):
                return False
            return any(c in level_names for c in certs)

        df = df[df["required_certs"].apply(has_level)]

    return df


def calc_cert_match_score(user_cert_names: list, required_cert_names: list) -> float:
    """사용자가 보유한 자격증과 공고 요구 자격증의 일치율(0~100점)을 계산한다."""
    if not required_cert_names:
        return 100.0
    matched = [c for c in required_cert_names if c in user_cert_names]
    return round(len(matched) / len(required_cert_names) * 100, 1)


def convert_grade_to_score(grade: float, grade_min: float = 1.0, grade_max: float = 5.0) -> float:
    """마이스터고 5등급 성취평가제(1.0~5.0)를 100점 만점으로 선형 환산한다."""
    grade = max(grade_min, min(grade_max, grade))
    return round(100 - (grade - grade_min) * (100 / (grade_max - grade_min)), 1)


def build_match_result(job_row, user_cert_names: list, grade: float) -> dict:
    """공고 1건에 대한 매칭 점수 + 1:1 피드백 문구를 생성한다."""
    required = job_row.get("required_certs", []) or []
    matched = [c for c in required if c in user_cert_names]
    missing = [c for c in required if c not in user_cert_names]

    cert_score = calc_cert_match_score(user_cert_names, required)
    grade_score = convert_grade_to_score(grade)
    final_score = round(cert_score * 0.5 + grade_score * 0.5, 1)

    parts = []
    if matched:
        parts.append(f"보유한 '{matched[0]}'은(는) 이 공고에서 우대하는 핵심 자격증이야.")
    if missing:
        parts.append(f"'{missing[0]}'을 취득하면 매칭 점수를 더 끌어올릴 수 있어.")
    else:
        parts.append("요구 자격증을 모두 갖췄어. 자신 있게 지원해봐!")

    feedback = " ".join(parts)

    return {
        "final_score": final_score,
        "cert_score": cert_score,
        "grade_score": grade_score,
        "matched": matched,
        "missing": missing,
        "feedback": feedback,
    }
