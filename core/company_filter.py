# -*- coding: utf-8 -*-
"""
core/company_filter.py
[Phase C] 기업 탐색기 — 매칭 점수 정렬 · 다중 필터 · 추천

▣ 설계 원칙
   1) 점수는 새로 만들지 않는다. 스펙 진단에서 쓰는 calc_spec_score 를 기업마다
      한 번씩 돌린다. 화면 두 곳이 서로 다른 점수를 보여주면 학생은 어느 쪽을
      믿어야 할지 모른다.
   2) 순수 로컬 연산이라 API 호출이 0회다. 필터를 아무리 바꿔도 과금이 없다.
   3) 기업 목록은 all_companies() 로 받는다 — Phase A 에서 팀이 기업을 추가하면
      정렬·필터·추천이 코드 수정 없이 그대로 확장된다.
"""

from core.matching import calc_spec_score
from data.departments import get_category

# 정렬 기준 — 라벨과 키를 한 곳에서 관리한다
SORT_MATCH = "내 매칭 점수순"
SORT_RATING = "기업 별점순"
SORT_NAME = "이름순"
SORT_OPTIONS = [SORT_MATCH, SORT_RATING, SORT_NAME]

# 추천 섹션에 올릴 기업 수
TOP_N = 4

# 이 점수 아래면 추천으로 올리지 않는다. 낮은 점수만 있는 학생에게
# "추천"이라며 안 맞는 기업을 들이밀면 추천이라는 말이 값을 잃는다.
RECOMMEND_FLOOR = 40.0


def student_profile(session) -> dict:
    """
    세션에 저장된 스펙 진단 입력을 매칭용 형태로 꺼낸다.

    dept·grade 는 세션 생성 시 기본값(학과 목록 첫 항목, 3.0등급)이 들어가
    있어 '값이 있다'는 것만으로는 학생이 입력했는지 알 수 없다. 그래서
    진단을 실제로 돌렸는지(last_spec_result)를 함께 싣는다.
    """
    return {
        "dept": session.get("dept") or "",
        "grade": session.get("grade"),
        "certs": list(session.get("user_certs") or []),
        "strengths": list(session.get("strength_keywords") or []),
        "diagnosed": session.get("last_spec_result") is not None,
    }


def has_spec(profile: dict) -> bool:
    """
    매칭 점수를 보여줘도 되는 상태인가.

    스펙 진단을 한 번도 안 돌린 학생에게 기본값으로 계산한 점수를 보여주면,
    본인이 입력한 적 없는 숫자를 '내 매칭 점수'로 읽게 된다. 진단을 돌렸거나
    자격증·강점을 직접 고른 경우에만 점수를 연다.
    """
    if not (profile.get("dept") and profile.get("grade") is not None):
        return False
    return bool(profile.get("diagnosed") or profile.get("certs") or profile.get("strengths"))


def match_score(company: dict, profile: dict) -> float:
    """기업 하나에 대한 내 매칭 점수 (스펙 진단과 같은 계산식)."""
    result = calc_spec_score(
        grade=float(profile.get("grade") or 5.0),
        user_certs=profile.get("certs") or [],
        dept_category=get_category(profile.get("dept") or ""),
        company=company,
        strength_keywords=profile.get("strengths") or [],
    )
    return float(result["final_score"])


def score_all(companies: list, profile: dict) -> list:
    """각 기업에 match_score 를 붙여 돌려준다. 원본은 건드리지 않는다."""
    if not has_spec(profile):
        return [{**c, "match_score": None} for c in companies]
    return [{**c, "match_score": match_score(c, profile)} for c in companies]


def filter_options(companies: list) -> dict:
    """현재 데이터에서 고를 수 있는 필터 값들. 데이터가 늘면 자동으로 늘어난다."""
    certs, sizes, cats = set(), set(), set()
    for c in companies:
        certs.update(c.get("required_certs") or [])
        if c.get("size_tag"):
            sizes.add(c["size_tag"])
        if c.get("category"):
            cats.add(c["category"])
    return {
        "certs": sorted(certs),
        "sizes": sorted(sizes),
        "categories": sorted(cats),
    }


def apply_filters(companies: list, certs: list | None = None,
                  categories: list | None = None, sizes: list | None = None) -> list:
    """
    다중 필터. 빈 목록은 '이 조건은 안 건다'는 뜻이다.
    자격증은 OR 로 본다 — 여러 개를 고른 학생은 '이 중 하나라도 쓰는 곳'을
    찾는 것이지 '전부 요구하는 곳'을 찾는 게 아니다.
    """
    certs, categories, sizes = set(certs or []), set(categories or []), set(sizes or [])
    out = []
    for c in companies:
        if categories and c.get("category") not in categories:
            continue
        if sizes and c.get("size_tag") not in sizes:
            continue
        if certs and not (certs & set(c.get("required_certs") or [])):
            continue
        out.append(c)
    return out


def sort_companies(companies: list, how: str) -> list:
    """정렬. 매칭 점수가 없는 경우(스펙 미입력)는 별점순으로 물러난다."""
    if how == SORT_MATCH:
        if any(c.get("match_score") is None for c in companies):
            how = SORT_RATING
        else:
            return sorted(companies, key=lambda c: (-c["match_score"], c["name"]))
    if how == SORT_RATING:
        return sorted(companies, key=lambda c: (-float(c.get("overall_rating") or 0), c["name"]))
    return sorted(companies, key=lambda c: c["name"])


def recommendations(companies: list, top_n: int = TOP_N) -> list:
    """
    매칭 점수 상위 기업. 점수가 없거나 기준선 아래면 빈 목록을 준다 —
    보여줄 게 없을 때 억지로 채우지 않는다.
    """
    scored = [c for c in companies
              if c.get("match_score") is not None and c["match_score"] >= RECOMMEND_FLOOR]
    scored.sort(key=lambda c: (-c["match_score"], c["name"]))
    return scored[:top_n]
