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

※ 연동 상태: 공식 활용가이드 기준 검증 전, 키 미설정 시 백업 데이터로 동작.
   아래 엔드포인트·파라미터·응답 필드는 공공데이터포털 REST API 의 일반 규격을
   따른 값으로, 활용가이드로 확인해 실제 호출에 성공한 기록은 아직 없다.
   (services/api_registry.py 의 같은 항목과 설명을 맞췄다)
"""

import requests
import pandas as pd

from data.certifications import CERTIFICATIONS

# 검증 전 엔드포인트 — 활용가이드로 확인한 뒤 확정한다
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
