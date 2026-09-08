# -*- coding: utf-8 -*-
"""
services/worknet_api.py
고용24(워크넷) Open API 연동 - 채용공고(구인정보) 수집

동작 방식
---------
1) api_key 가 주어지면 워크넷 Open API 채용정보 조회를 시도한다.
2) 실패 시 예외를 모두 흡수하고 data/companies.py 의 MOCK_JOBS 로 자동 전환한다.
3) 반환값은 항상 pandas.DataFrame + 데이터 출처("live"/"backup") 튜플이다.

※ 워크넷 Open API는 https://www.work24.go.kr (구 work.go.kr) 개발자센터에서
   신청 후 인증키(authKey)를 발급받아야 합니다. 아래 엔드포인트/파라미터명은
   워크넷 Open API의 일반적 규격(XML 응답 기반)을 참고한 예시이며, 실제
   서비스 적용 전 최신 활용가이드로 검증이 필요합니다.
"""

import requests
import pandas as pd
from xml.etree import ElementTree as ET

from data.companies import MOCK_JOBS
from data.certifications import CERT_CODE_TO_NAME
from core.matching import filter_results

# 예시 엔드포인트 (실서비스 적용 시 발급받은 활용가이드의 실제 URL로 교체)
WORKNET_API_ENDPOINT = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"


def _mock_dataframe(keyword: str = ""):
    """
    MOCK_JOBS의 자격증 코드(cert_codes)를 자격증명으로 변환한 뒤,
    keyword가 있으면 company/title/required_certs 기준으로 필터링해 DataFrame으로 반환.
    (이전에는 keyword를 무시하고 항상 20건 전체를 반환하던 버그가 있었음 — 수정됨)
    """
    rows = []
    for job in MOCK_JOBS:
        row = dict(job)
        row["required_certs"] = [
            CERT_CODE_TO_NAME.get(code, code) for code in job["required_cert_codes"]
        ]
        row.setdefault("ai_tip", "")
        rows.append(row)

    rows = filter_results(rows, keyword)
    return pd.DataFrame(rows)


def fetch_jobs_from_api(api_key: str | None, keyword: str = "", timeout: int = 5):
    """
    워크넷 Open API로 채용공고를 조회한다.
    api_key 가 없거나 호출/파싱이 실패하면 MOCK_JOBS 백업 데이터로 전환한다.
    두 경로 모두 keyword로 필터링된 결과만 반환한다.
    """
    if not api_key:
        return _mock_dataframe(keyword), "backup"

    try:
        params = {
            "authKey": api_key,
            "callTp": "L",
            "returnType": "XML",
            "keyword": keyword,
            "startPage": 1,
            "display": 100,
        }
        res = requests.get(WORKNET_API_ENDPOINT, params=params, timeout=timeout)
        res.raise_for_status()

        root = ET.fromstring(res.text)
        items = root.findall(".//wanted")
        if not items:
            raise ValueError("워크넷 API 응답에 채용공고가 없음")

        records = []
        for i, item in enumerate(items):
            def _text(tag):
                el = item.find(tag)
                return el.text.strip() if el is not None and el.text else ""

            records.append({
                "id": i + 1,
                "company": _text("company"),
                "title": _text("title"),
                "department": "",  # 워크넷 응답에는 학과 개념이 없어 매핑 로직 별도 필요
                "required_certs": [],
                "region": _text("region"),
                "salary": _text("sal"),
                "company_type": _text("coClcdNm"),
                "ai_tip": "",
            })

        # API 자체 keyword 파라미터를 신뢰하되, 응답 구조가 다를 수 있으므로 한 번 더 안전하게 필터링
        # (여기서 결과가 0건이 되는 것은 "검색결과 없음"이라는 정상적인 상황이므로 백업으로 전환하지 않는다)
        records = filter_results(records, keyword)
        return pd.DataFrame(records), "live"

    except Exception:
        return _mock_dataframe(keyword), "backup"
