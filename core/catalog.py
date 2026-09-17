# -*- coding: utf-8 -*-
"""
core/catalog.py
여러 화면이 공유하는 조회 헬퍼 (자격증 목록 · 인재상 키워드 · 계열별 자격증)

원본 app.py 상단에 있던 모듈 레벨 로딩 코드를 함수로 감쌌다.
화면이 파일로 쪼개진 뒤에도 Q-Net 호출이 화면마다 반복되지 않도록
@st.cache_data 로 1시간 캐싱한다.
"""

import streamlit as st

from data.certifications import CERT_CODE_TO_NAME
from data.company_showcase import COMPANY_SHOWCASE
from data.departments import DEPARTMENTS
from services import fallback as fb


@st.cache_data(ttl=3600, show_spinner=False)
def load_cert_names(api_key: str) -> tuple[list, str]:
    """Q-Net 자격증 목록. 실패 시 백업 마스터로 자동 전환된다."""
    df, source = fb.fetch_certifications_safe(api_key)
    names = df["name"].tolist() if "name" in df else []
    return names, source


def all_talent_keywords() -> list:
    """기업 인재상 키워드 전체 집합 (강점 선택지로 사용)."""
    return sorted({kw for c in COMPANY_SHOWCASE for kw in c["ideal_talent"]})


def certs_for_department(dept: str) -> list:
    """학과에 매핑된 추천 자격증 이름 목록."""
    codes = DEPARTMENTS.get(dept, {}).get("cert_codes", [])
    return [CERT_CODE_TO_NAME[c] for c in codes if c in CERT_CODE_TO_NAME]


def completed_milestones(milestones: dict) -> int:
    return sum(1 for v in (milestones or {}).values() if v)
