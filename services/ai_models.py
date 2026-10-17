# -*- coding: utf-8 -*-
"""
services/ai_models.py
[big-patch 4단계] AI 호출 등급 — 초안은 저렴한 모델, 최종 첨삭만 상위 모델

   TIER_DRAFT : 자소서 초안 생성 · 점수 설명 · 모의 면접 피드백 (자주, 짧게)
   TIER_FINAL : 자소서 최종 첨삭 (학생이 제출 직전에 한 번)

   모델 이름은 st.secrets 의 AI_MODEL_DRAFT · AI_MODEL_FINAL 로 바꿀 수 있다
   (코드 수정 없이 운영자가 비용과 품질을 조정). 단가는 docs/cost.md.
"""

import streamlit as st

TIER_DRAFT = "draft"
TIER_FINAL = "final"

DEFAULT_MODELS = {
    TIER_DRAFT: "claude-sonnet-5-5",
    TIER_FINAL: "claude-opus-5-5",
}
_SECRET_NAMES = {TIER_DRAFT: "AI_MODEL_DRAFT", TIER_FINAL: "AI_MODEL_FINAL"}


def model_for(tier: str) -> str:
    """등급별 모델 이름. secrets 에 값이 있으면 그 값을 쓴다."""
    try:
        override = str(st.secrets.get(_SECRET_NAMES.get(tier, ""), "") or "").strip()
    except Exception:
        override = ""
    return override or DEFAULT_MODELS.get(tier, DEFAULT_MODELS[TIER_DRAFT])
