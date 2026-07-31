# -*- coding: utf-8 -*-
"""
services/alio_api.py
잡알리오(공공기관 채용정보시스템, job.alio.go.kr) 채용공고 수집

동작 방식
---------
1) 잡알리오 채용공고 목록 페이지를 requests + BeautifulSoup으로 조회 시도한다.
2) 파싱 실패(구조 변경/네트워크 오류/차단 등) 시 예외를 모두 흡수하고
   data/companies.py 의 BACKUP_PUBLIC_COMPANIES(공기업 10건)로 자동 전환한다.
3) 반환값은 항상 (list[dict], "live"|"backup") 튜플이다.

※ 매우 중요 — 스크래핑 관련 안내
잡알리오는 공공기관 경영정보 공개시스템으로 채용공고 자체는 공개 정보이지만,
- 이 코드가 작성된 시점 기준 잡알리오의 실제 HTML 구조를 직접 확인하지 못했기
  때문에, 아래 URL과 CSS 선택자(.recruit-list, .org-name 등)는 **일반적인
  채용 목록 페이지 구조를 참고한 예시**입니다. 실제 배포 전 반드시:
  1) https://job.alio.go.kr 의 robots.txt 및 이용약관을 확인하고
  2) 브라우저 개발자도구로 실제 HTML 구조를 확인해 선택자를 재검증해야 합니다.
- 선택자가 실제 구조와 다르면 자동으로 "구조 변경 감지"로 처리되어 백업
  데이터로 전환되므로, 서비스 자체는 항상 정상 동작합니다.
"""

import requests
from bs4 import BeautifulSoup

from data.companies import BACKUP_PUBLIC_COMPANIES
from data.certifications import CERT_CODE_TO_NAME

# 예시 URL (실제 배포 전 잡알리오 채용정보 목록 페이지의 정확한 경로로 검증 필요)
ALIO_JOB_LIST_URL = "https://job.alio.go.kr/recruit.do"

HEADERS = {"User-Agent": "Mozilla/5.0 (AI-Job-Pass-Finder EMP-Team Bot)"}


def _backup_public_jobs():
    """자격증 코드를 자격증명으로 변환한 공기업 백업 데이터를 반환한다."""
    rows = []
    for job in BACKUP_PUBLIC_COMPANIES:
        row = dict(job)
        row["required_certs"] = [
            CERT_CODE_TO_NAME.get(code, code) for code in job.get("required_cert_codes", [])
        ]
        row.setdefault("ai_tip", "")
        rows.append(row)
    return rows


def fetch_alio_jobs(timeout: int = 5):
    """
    잡알리오에서 공기업 채용공고(기관명/분야/고졸채용여부/필수자격증)를 가져온다.
    실패 시 예외를 흡수하고 BACKUP_PUBLIC_COMPANIES로 전환한다.
    반환값: (list[dict], "live" | "backup")
    """
    try:
        res = requests.get(ALIO_JOB_LIST_URL, headers=HEADERS, timeout=timeout)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # ⚠️ 예시 선택자 - 실제 잡알리오 페이지 구조로 재검증 필요
        cards = soup.select(".recruit-list .item")
        if not cards:
            raise ValueError("잡알리오 채용공고 파싱 결과가 비어 있음 (페이지 구조 변경 의심)")

        records = []
        for i, card in enumerate(cards):
            org_el = card.select_one(".org-name")
            field_el = card.select_one(".field")
            hs_el = card.select_one(".highschool-badge")  # 고졸 채용 여부 표시(예시)
            cert_el = card.select_one(".required-cert")

            if not org_el:
                continue

            records.append({
                "id": 1000 + i,
                "company": org_el.get_text(strip=True),
                "title": field_el.get_text(strip=True) if field_el else "채용공고",
                "department": "",
                "required_certs": (
                    [c.strip() for c in cert_el.get_text(strip=True).split(",")] if cert_el else []
                ),
                "region": "",
                "salary": "",
                "company_type": "공기업",
                "is_high_school_hire": bool(hs_el),
                "ai_tip": "잡알리오에서 실시간 수집된 공고입니다. 상세 자격 요건은 원문 공고를 확인해줘.",
            })

        if not records:
            raise ValueError("잡알리오 파싱 결과 유효 데이터 없음")
        return records, "live"

    except Exception:
        return _backup_public_jobs(), "backup"
