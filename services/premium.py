# -*- coding: utf-8 -*-
"""
services/premium.py
AI 직접 생성(자소서 · 첨삭 · 점수 설명)은 로그인한 프리미엄 회원 전용

▣ 왜 키 보유만으로 AI 를 켜지 않는가
   Claude API 는 호출할 때마다 과금된다. 키를 st.secrets 에 넣어 두기만 해도
   모든 방문자가 AI 를 쓰게 되면, 대회 시연 중 QR 로 들어온 수십 명이 그대로
   비용이 된다. 그래서 '키가 있음'과 'AI 를 써도 됨'을 분리했다.

       AI 호출 = 키 있음  AND  소셜 로그인  AND  프리미엄 회원

   셋 중 하나라도 아니면 API 는 한 번도 호출되지 않고, 무료 경로
   (템플릿 생성 · 규칙 기반 점검 · 프롬프트 복사)로 동작한다.

▣ 프리미엄 회원은 어떻게 정해지는가
   결제 연동은 아직 없다. 프리미엄은 운영자가 st.secrets 의
   PREMIUM_USER_IDS 에 user_id 를 적어 지정한다. 기본값은 빈 목록이므로
   아무도 프리미엄이 아니다 → 키를 넣어도 비용이 0원이다.

       PREMIUM_USER_IDS = ["kakao_1234567890"]

   게스트는 기기를 바꾸면 이어하기 코드만으로 들어오므로 유료 혜택의
   주체가 될 수 없다 — 프리미엄은 소셜 로그인 계정에만 붙는다.

   화면의 '프리미엄 시작하기'는 결제를 받지 않는다. 결제 연동이 준비 중이라는
   사실을 그대로 안내한다 (결제 정보를 입력받는 화면을 만들지 않는다).
"""

import streamlit as st

from core import session as ss

# services/llm.py · review.py · score_explain.py 와 같은 키 이름
_KEY_NAMES = ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY")

PLAN_FREE = "free"
PLAN_PREMIUM = "premium"

# 요금제 안내 화면에 그대로 쓰는 비교표 (무료 기능은 실제로 전부 동작한다)
PLAN_FEATURES = [
    ("스펙 진단 · 기업 탐색 · 가이드 · 로드맵", "포함", "포함"),
    ("자소서 템플릿 생성", "포함", "포함"),
    ("AI용 프롬프트 복사 (무료 AI 에 붙여넣기)", "포함", "포함"),
    ("Claude 가 자소서 직접 작성", "-", "포함"),
    ("Claude 자소서 첨삭", "-", "포함"),
    ("Claude 점수 해설", "-", "포함"),
]


def _secret(name: str, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def has_api_key() -> bool:
    return any(str(_secret(name, "") or "").strip() for name in _KEY_NAMES)


def premium_user_ids() -> set[str]:
    """
    st.secrets 의 PREMIUM_USER_IDS. TOML 배열과 쉼표 구분 문자열 둘 다 받는다
    (Streamlit Cloud 의 Secrets 편집기에서 배열 문법을 틀리는 경우가 잦다).
    """
    raw = _secret("PREMIUM_USER_IDS", [])
    if isinstance(raw, str):
        items = raw.split(",")
    else:
        try:
            items = list(raw)
        except TypeError:
            items = []
    return {str(item).strip() for item in items if str(item).strip()}


def plan() -> str:
    uid = ss.user_id()
    if uid and ss.provider() not in ("", "guest") and uid in premium_user_ids():
        return PLAN_PREMIUM
    return PLAN_FREE


def is_premium() -> bool:
    return plan() == PLAN_PREMIUM


def ai_enabled() -> bool:
    """실제로 Claude API 를 호출해도 되는가. 모든 AI 호출부가 이 값만 본다."""
    return has_api_key() and is_premium()


def plan_label() -> str:
    return "프리미엄" if is_premium() else "무료"


def lock_reason() -> str:
    """AI 기능이 꺼져 있는 이유 — 화면 안내 문구."""
    if is_premium() and not has_api_key():
        return "프리미엄 회원이지만 AI 서비스 키가 아직 설정되지 않았습니다."
    if ss.provider() in ("", "guest"):
        return "Claude 직접 작성은 소셜 로그인한 프리미엄 회원 전용입니다. 게스트는 무료 기능을 쓸 수 있어요."
    return "Claude 직접 작성은 프리미엄 회원 전용입니다. 지금은 무료 기능을 쓸 수 있어요."


def render_plan_info() -> None:
    """요금제 비교 + 업그레이드 안내. 결제는 받지 않는다."""
    # 마크다운 표는 좁은 열에서 '무/료'처럼 글자 단위로 줄바꿈된다 → 값 열은 nowrap
    cell = "padding:6px 8px; border-bottom:1px solid rgba(128,128,128,0.25);"
    val = cell + " text-align:center; white-space:nowrap;"
    rows = "".join(
        f'<tr><td style="{cell}">{name}</td><td style="{val}">{free}</td>'
        f'<td style="{val}">{premium}</td></tr>'
        for name, free, premium in PLAN_FEATURES
    )
    st.markdown(
        f'<table style="width:100%; border-collapse:collapse; font-size:14px;">'
        f'<tr><th style="{cell} text-align:left;">기능</th><th style="{val}">무료</th>'
        f'<th style="{val}">프리미엄</th></tr>{rows}</table>',
        unsafe_allow_html=True,
    )
    st.caption(
        "프리미엄 결제 연동은 준비 중입니다. 지금은 결제를 받지 않으며, "
        "운영팀이 지정한 계정에서만 AI 직접 작성이 켜집니다."
    )
