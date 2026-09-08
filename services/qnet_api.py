# -*- coding: utf-8 -*-
"""
services/qnet_api.py
한국산업인력공단(Q-Net) / 공공데이터포털(data.go.kr) 국가기술자격 정보 API 연동

동작 방식
---------
1) api_key 가 주어지면 공공데이터포털 REST API 호출을 시도한다.
2) 요청 실패(키 없음/네트워크 오류/응답 구조 변경 등) 시 예외를 모두 흡수하고
   data/certifications.py 의 정적 마스터 데이터로 자동 전환(fallback)한다.
3) 반환값은 항상 pandas.DataFrame + 데이터 출처("live"/"backup") 튜플이다.

※ 실제 엔드포인트/파라미터명은 공공데이터포털에서 "국가기술자격" 관련 API를
   신청하면 발급되는 활용가이드 문서의 값으로 반드시 교체해야 합니다.
   아래 URL/파라미터는 공공데이터포털 REST API의 일반적인 규격(서비스키,
   페이지 번호, 응답 타입)을 따른 예시이며 실제 서비스 URL이 아닙니다.
"""

import requests
import pandas as pd

from data.certifications import CERTIFICATIONS

# 예시 엔드포인트 (실서비스 적용 시 발급받은 활용가이드의 실제 URL로 교체)
QNET_API_ENDPOINT = "https://apis.data.go.kr/B490007/qualInfoService/getQualInfo"


def fetch_certifications_from_api(api_key: str | None, timeout: int = 5):
    """
    공공데이터포털 국가기술자격 API를 호출해 자격증 마스터 데이터를 가져온다.
    api_key 가 없거나 호출/파싱이 실패하면 정적 백업 데이터를 반환한다.
    """
    if not api_key:
        return pd.DataFrame(CERTIFICATIONS), "backup"

    try:
        params = {
            "serviceKey": api_key,
            "pageNo": 1,
            "numOfRows": 200,
            "type": "json",
        }
        res = requests.get(QNET_API_ENDPOINT, params=params, timeout=timeout)
        res.raise_for_status()
        payload = res.json()

        items = (
            payload.get("response", {})
            .get("body", {})
            .get("items", [])
        )
        if not items:
            raise ValueError("API 응답에 자격증 데이터가 없음")

        records = []
        for item in items:
            records.append({
                "code": item.get("jmCd", ""),
                "name": item.get("jmFldNm", ""),
                "level": item.get("seriesNm", ""),
                "category": item.get("mdobligFldNm", ""),
            })

        df = pd.DataFrame(records)
        if df.empty:
            raise ValueError("파싱된 자격증 데이터프레임이 비어있음")

        return df, "live"

    except Exception:
        # 키가 유효하지 않거나, 네트워크 문제, 응답 구조 변경 등 모든 경우 백업으로 전환
        return pd.DataFrame(CERTIFICATIONS), "backup"
