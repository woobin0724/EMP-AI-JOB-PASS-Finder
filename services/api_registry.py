# -*- coding: utf-8 -*-
"""
services/api_registry.py
공식 오픈API 연동 설정 — 코드가 아니라 '설정'으로 붙인다

▣ 왜 설정으로 분리했나
   이 저장소에는 엔드포인트와 파라미터명을 추측해 쓴 클라이언트가 세 개
   있었다(워크넷·잡알리오·강소기업). 추측이라 한 번도 성공한 적이 없고,
   화면에는 영구히 BACKUP 배지만 떴다. 규격을 확인하지 못한 상태에서
   클라이언트를 더 쓰면 같은 일이 반복된다.

   그래서 '언제 붙일 수 있는지'를 코드 밖으로 뺐다. 팀이 포털에서 키를
   발급받고 활용가이드로 요청/응답 규격을 확인한 뒤, 아래 표의 빈 칸을
   채우고 secrets 에 키를 넣으면 그때부터 LIVE 로 동작한다.

▣ 채우는 방법
   1) 포털에서 활용신청 → 키 발급
   2) 활용가이드(요청 URL·파라미터명·응답 필드)를 보고 endpoint/params/
      response_path 를 채운다
   3) .streamlit/secrets.toml 에 secret_name 으로 키를 넣는다
   4) ready() 가 True 가 되면 화면 배지가 CURATED → LIVE 로 바뀐다

   규격을 확인하기 전에는 빈 칸으로 두는 것이 맞다. 빈 칸이면 이 모듈은
   "아직 준비 안 됨"을 정직하게 보고하고 큐레이션 데이터가 쓰인다.
"""

from dataclasses import dataclass, field

import streamlit as st


@dataclass
class ApiSpec:
    """오픈API 한 건의 연동 설정."""

    key: str                      # 내부 식별자
    label: str                    # 화면에 보일 이름
    portal: str                   # 어디서 신청하는지
    portal_url: str
    secret_name: str              # secrets.toml 에 넣을 키 이름
    endpoint: str = ""            # 활용가이드의 요청 URL
    params: dict = field(default_factory=dict)      # 고정 파라미터
    key_param: str = "serviceKey"                   # 인증키를 실어 보낼 파라미터명
    response_path: list = field(default_factory=list)  # 응답에서 목록까지의 경로
    note: str = ""

    def api_key(self) -> str:
        """secrets 에서 키를 읽는다. secrets.toml 이 없어도 예외를 내지 않는다."""
        try:
            return str(st.secrets.get(self.secret_name, "") or "").strip()
        except Exception:
            return ""

    def ready(self) -> bool:
        """엔드포인트 규격과 키가 모두 준비됐는가."""
        return bool(self.endpoint) and bool(self.api_key())

    def status(self) -> str:
        """화면에 보여줄 준비 상태."""
        if not self.endpoint:
            return "규격 미확인"
        if not self.api_key():
            return "키 미등록"
        return "연동 준비 완료"


# ------------------------------------------------------------
# 연동 후보 — endpoint/params 는 활용가이드 확인 후 채운다
# ------------------------------------------------------------
REGISTRY: list[ApiSpec] = [
    ApiSpec(
        key="qnet",
        label="Q-Net 국가자격 정보",
        portal="공공데이터포털",
        portal_url="https://www.data.go.kr",
        secret_name="QNET_API_KEY",
        # 이 건만 실제 엔드포인트가 확인돼 있다 (services/qnet_api.py 참고)
        endpoint="https://apis.data.go.kr/B490007/qualInfoService/getQualInfo",
        note="유일하게 실제 엔드포인트가 확인된 소스. 키만 넣으면 동작한다.",
    ),
    ApiSpec(
        key="public_recruit",
        label="공공기관 채용정보",
        portal="공공데이터포털 (기획재정부)",
        portal_url="https://www.data.go.kr/data/15125273/openapi.do",
        secret_name="PUBLIC_RECRUIT_API_KEY",
        note="공공기관 채용공고 통합 제공. 스크래핑하던 잡알리오의 공식 대체 경로.",
    ),
    ApiSpec(
        key="worknet",
        label="워크넷 채용정보",
        portal="공공데이터포털 (한국고용정보원)",
        portal_url="https://www.data.go.kr/data/3038225/openapi.do",
        secret_name="WORKNET_API_KEY",
        key_param="authKey",
        note="채용목록 + 상세정보. 현재 services/worknet_api.py 의 파라미터는 미검증 추측값이다.",
    ),
    ApiSpec(
        key="saramin",
        label="사람인 채용정보",
        portal="사람인 개발자센터",
        portal_url="https://oapi.saramin.co.kr",
        secret_name="SARAMIN_API_KEY",
        key_param="access-key",
        note="이용신청 후 승인 필요, 1일 500회 상한. 100명 동시 테스트에는 상한이 빠듯하다.",
    ),
]

BY_KEY = {spec.key: spec for spec in REGISTRY}


def ready_specs() -> list[ApiSpec]:
    """규격과 키가 모두 준비돼 실제 호출이 가능한 API 목록."""
    return [s for s in REGISTRY if s.ready()]


def summary_rows() -> list[dict]:
    """관리자 화면에 표로 뿌릴 준비 현황."""
    return [
        {"API": s.label, "포털": s.portal, "상태": s.status(),
         "secrets 키": s.secret_name, "비고": s.note}
        for s in REGISTRY
    ]
