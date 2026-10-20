# -*- coding: utf-8 -*-
"""
services/strong_sme_api.py
강소기업 채용정보 — 가상 예시 데이터 (BACKUP)

▣ 왜 스크래핑을 걷어냈나
   이전 구현은 강소기업 포털 HTML 을 requests + BeautifulSoup 으로 긁었으나,
   선택자(.company-list .item 등)가 실제 페이지를 확인하지 않은 추측이라
   항상 백업으로 떨어졌다. alio_api.py 와 같은 이유로 가상 예시 데이터로
   교체했다.

   [심사대응] 예전에는 이 가상 데이터를 "curated"(팀이 조사한 데이터)로 표시해
   화면에 CURATED 배지가 떴다. 실제 조사 자료가 아니므로 "backup" 으로 바꿨다.

   백업 데이터의 기업명은 모두 가상(fictional)이다. 실제로 강소기업 인증을
   받은 특정 기업의 정보가 아니다 (data/companies.py 상단 주석 참고).
"""

from data.certifications import CERT_CODE_TO_NAME
from data.companies import BACKUP_STRONG_SME

SOURCE_LABEL = "강소기업(가상 예시)"

# 전북기계공고 학생 전공과 직결되는 학과 — 매칭 시 상단으로 올린다.
PRIORITY_DEPARTMENTS = {"기계과", "메카트로닉스과", "전기전자과",
                        "자동차과", "IT소프트웨어과", "정보통신과"}


def _curated_strong_sme() -> list:
    """자격증 코드를 자격증명으로 바꾼 강소기업 가상 예시 데이터."""
    rows = []
    for job in BACKUP_STRONG_SME:
        row = dict(job)
        row["required_certs"] = [
            CERT_CODE_TO_NAME.get(code, code) for code in job.get("required_cert_codes", [])
        ]
        row.setdefault("ai_tip", "")
        rows.append(row)
    return rows


def fetch_strong_small_companies(timeout: int = 5):
    """
    강소기업 채용공고를 반환한다.

    timeout 은 호출부 시그니처를 맞추기 위해 남겨둔다.
    반환값: (list[dict], "backup")
    """
    return _curated_strong_sme(), "backup"


def prioritize_by_department(records: list) -> list:
    """
    전북기계공고 학생 전공(기계/전기/제조/IT)과 관련된 공고를 상단으로
    올린다. 원래 순서는 안정 정렬로 보존된다.
    """
    return sorted(records, key=lambda r: 0 if r.get("department") in PRIORITY_DEPARTMENTS else 1)
