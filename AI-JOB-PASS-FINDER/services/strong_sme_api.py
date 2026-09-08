# -*- coding: utf-8 -*-
"""
services/strong_sme_api.py
'참 괜찮은 강소기업' 포털(중소벤처기업부 강소기업 인증제 관련) 채용정보 수집

동작 방식
---------
1) 강소기업 포털 페이지를 requests + BeautifulSoup으로 조회 시도한다.
2) 파싱 실패(구조 변경/네트워크 오류/차단 등) 시 예외를 모두 흡수하고
   data/companies.py 의 BACKUP_STRONG_SME(강소기업 10건)로 자동 전환한다.
3) 반환값은 항상 (list[dict], "live"|"backup") 튜플이다.

※ 매우 중요 — 스크래핑 관련 안내
- 아래 URL(STRONG_SME_URL)은 요청 주신 도메인을 그대로 넣어둔 예시입니다.
  이 코드가 작성된 시점 기준 해당 사이트의 실제 페이지 구조·정확한 URL
  경로를 직접 확인하지 못했으므로, CSS 선택자(.company-list .item 등)는
  **일반적인 채용/기업목록 페이지 구조를 참고한 예시**입니다.
- 실제 배포 전 반드시:
  1) 사이트의 robots.txt와 이용약관을 확인하고
  2) 브라우저 개발자도구로 실제 HTML 구조를 확인해 URL과 선택자를 재검증해야 합니다.
- 선택자가 실제 구조와 다르면 자동으로 "구조 변경 감지"로 처리되어 백업
  데이터로 전환되므로, 서비스 자체는 항상 정상 동작합니다.
- 백업 데이터의 기업명은 모두 가상(fictional) 기업입니다. 실제로 이 인증을
  받은 특정 기업의 정보를 담고 있지 않습니다 (data/companies.py 상단 주석 참고).
"""

import requests
from bs4 import BeautifulSoup

from data.companies import BACKUP_STRONG_SME
from data.certifications import CERT_CODE_TO_NAME

# 예시 URL (실제 배포 전 정확한 채용정보 목록 페이지 경로로 검증 필요)
STRONG_SME_URL = "https://smdoctor.go.kr/recruit/list"

HEADERS = {"User-Agent": "Mozilla/5.0 (AI-Job-Pass-Finder EMP-Team Bot)"}

# 전북기계공고 학생 전공과 직결되는 학과 — 매칭 시 우선순위 가중치를 부여한다.
PRIORITY_DEPARTMENTS = {"기계과", "메카트로닉스과", "전기전자과", "자동차과", "IT소프트웨어과", "정보통신과"}


def _backup_strong_sme():
    """자격증 코드를 자격증명으로 변환한 강소기업 백업 데이터를 반환한다."""
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
    '참 괜찮은 강소기업' 포털에서 기업명/주력분야/요구스펙/합격팁을 가져온다.
    실패 시 예외를 흡수하고 BACKUP_STRONG_SME로 전환한다.
    반환값: (list[dict], "live" | "backup")
    """
    try:
        res = requests.get(STRONG_SME_URL, headers=HEADERS, timeout=timeout)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # ⚠️ 예시 선택자 - 실제 사이트 구조로 재검증 필요
        cards = soup.select(".company-list .item")
        if not cards:
            raise ValueError("강소기업 포털 파싱 결과가 비어 있음 (페이지 구조 변경 의심)")

        records = []
        for i, card in enumerate(cards):
            name_el = card.select_one(".company-name")
            field_el = card.select_one(".main-field")
            spec_el = card.select_one(".required-spec")

            if not name_el:
                continue

            records.append({
                "id": 2000 + i,
                "company": name_el.get_text(strip=True),
                "title": field_el.get_text(strip=True) if field_el else "채용공고",
                "department": "",
                "required_certs": (
                    [s.strip() for s in spec_el.get_text(strip=True).split(",")] if spec_el else []
                ),
                "region": "",
                "salary": "",
                "company_type": "강소기업",
                "ai_tip": "'참 괜찮은 강소기업' 포털에서 실시간 수집된 공고입니다. 상세 요건은 원문을 확인해줘.",
            })

        if not records:
            raise ValueError("강소기업 포털 파싱 결과 유효 데이터 없음")
        return records, "live"

    except Exception:
        return _backup_strong_sme(), "backup"


def prioritize_by_department(records: list) -> list:
    """
    전북기계공고 학생 전공(기계/전기/제조/IT, PRIORITY_DEPARTMENTS)과 관련된
    공고가 리스트 상단에 오도록 정렬한다. 원래 순서는 안정 정렬로 보존된다.
    """
    return sorted(records, key=lambda r: 0 if r.get("department") in PRIORITY_DEPARTMENTS else 1)
