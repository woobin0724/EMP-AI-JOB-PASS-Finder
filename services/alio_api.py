# -*- coding: utf-8 -*-
"""
services/alio_api.py
공기업 채용정보 — 팀 큐레이션 데이터

▣ 왜 스크래핑을 걷어냈나
   이전 구현은 job.alio.go.kr 의 HTML 을 requests + BeautifulSoup 으로
   긁었다. 그런데 CSS 선택자(.recruit-list .item 등)를 실제 페이지를 확인하지
   않고 추측으로 넣어둔 것이라, 네트워크가 뚫려도 파싱이 비어 항상 백업으로
   떨어졌다. 즉 '동작하지 않는 스크래핑 코드'만 남아 있었다.

   데이터는 공식 API 아니면 사람이 직접 조사해 넣는다는 것이 이 프로젝트의
   원칙이므로, 여기서는 팀이 큐레이션한 데이터를 돌려준다.

▣ 공식 API 로 올리려면
   ALIO 는 opendata.alio.go.kr 에서 공공기관 채용정보 오픈API 를 제공하고,
   data.go.kr 에도 '기획재정부_공공기관 채용정보 조회서비스'가 등록돼 있다.
   키를 발급받고 활용가이드로 요청/응답 규격을 확인한 뒤
   services/api_registry.py 의 설정만 채우면 LIVE 로 전환된다.
   규격을 확인하기 전에는 추측으로 클라이언트를 쓰지 않는다 — 그렇게 만든
   코드가 바로 위의 스크래핑이었다.
"""

from data.certifications import CERT_CODE_TO_NAME
from data.companies import BACKUP_PUBLIC_COMPANIES

SOURCE_LABEL = "공기업 채용(큐레이션)"


def _curated_public_jobs() -> list:
    """자격증 코드를 자격증명으로 바꾼 공기업 큐레이션 데이터."""
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
    공기업 채용공고를 반환한다.

    timeout 은 쓰지 않지만 호출부(services/fallback.py)의 시그니처를 맞추기
    위해 남겨둔다 — 공식 API 가 붙으면 그대로 쓰인다.

    반환값: (list[dict], "curated")
    """
    return _curated_public_jobs(), "curated"
