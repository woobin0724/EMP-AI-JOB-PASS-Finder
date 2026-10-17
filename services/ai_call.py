# -*- coding: utf-8 -*-
"""
services/ai_call.py
[big-patch 3·4단계] Claude 호출 공통 경로 (모의 면접 등 새 기능이 쓴다)

   · 모델은 등급(services/ai_models)으로 고른다 — 초안 저가 모델 · 최종 첨삭 상위 모델
   · 안전 분류기 거절 시 서버 측 대체 모델(fallbacks="default")을 쓰고,
     그 파라미터가 거부되는 환경이면 표준 호출로 내려간다
   · 실패하면 예외를 던진다 — 호출부가 규칙 기반 결과로 내려간다
   API 키는 호출부가 st.secrets 에서 읽어 넘긴다(코드·저장소에 키 없음).
"""

from services.ai_models import model_for

_FALLBACKS_SUPPORTED = True


def complete(tier: str, system: str, user: str, api_key: str, *,
             max_tokens: int = 8000, effort: str = "low", timeout: float = 60.0) -> str:
    global _FALLBACKS_SUPPORTED
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=1)
    params = {
        "model": model_for(tier),
        "max_tokens": max_tokens,
        "system": system,
        "output_config": {"effort": effort},
        "messages": [{"role": "user", "content": user}],
    }
    if _FALLBACKS_SUPPORTED:
        try:
            response = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params)
        except anthropic.BadRequestError:
            _FALLBACKS_SUPPORTED = False
            response = client.messages.create(**params)
    else:
        response = client.messages.create(**params)

    if getattr(response, "stop_reason", None) == "refusal":
        raise ValueError("모델이 요청을 거절했습니다 (stop_reason=refusal)")
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
    if not text:
        raise ValueError("응답에 본문 텍스트가 없습니다")
    return text
