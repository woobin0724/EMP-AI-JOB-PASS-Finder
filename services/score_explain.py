# -*- coding: utf-8 -*-
"""
services/score_explain.py
[Phase B] 규칙 기반 점수 + Claude 설명 하이브리드

▣ 왜 하이브리드인가
   점수 계산(core/matching.py)은 로컬 파이썬 연산 그대로 둔다. 슬라이더를
   움직일 때마다 API 를 부르면 과금이 순식간에 터지고, 계산은 이미 정확하다.
   LLM 이 잘하는 일은 '계산'이 아니라 '설명'이다. 그래서 점수가 나온 뒤,
   그 숫자를 재료로 왜 이 점수인지만 말하게 한다.

▣ 과금 방어 3단 (services/llm.py 와 같은 구조)
   1단 캐싱  : 항목별 점수가 그대로면 재호출하지 않는다. 학생이 슬라이더를
              흔들어도 같은 점수 조합이면 캐시가 맞는다.
   2단 키 부재: 키가 없으면 네트워크로 나가지 않고 규칙 기반 설명을 쓴다.
   3단 실패  : 호출이 실패하면 규칙 기반으로 내려가되, 사유를 남긴다.

▣ 규칙 기반 설명을 남겨둔 이유
   키가 없는 상태로 100명이 쓰면 이 기능이 통째로 안 보인다. 점수만 덩그러니
   나오는 것보다는, 같은 재료로 만든 설명이라도 있는 편이 낫다.
"""

import hashlib
import json

import streamlit as st

from services.coverletter import apply_josa

MODEL_NAME = "claude-opus-5"
# 출력은 두세 문장이지만 현행 모델은 추론 토큰이 기본으로 켜져 있고 그 양이
# max_tokens 에 함께 잡힌다. 낮게 잡으면 문장 중간에서 잘린다(자소서 쪽에서
# 900 으로 뒀다가 같은 문제를 겪었다). 상한일 뿐이라 실제 생성량만 과금된다.
MAX_TOKENS = 8000
EFFORT = "low"          # 두세 문장 설명에 깊은 추론은 필요 없다
REQUEST_TIMEOUT = 40.0

CACHE_TTL = 3600
CACHE_MAX_ENTRIES = 128

# 항목 정의 — 라벨과 배점을 한 곳에서 관리한다
ITEMS = [
    ("grade_score",  "내신 성취도",   30, "남은 학기 성적 관리"),
    ("cert_score",   "자격증 가산점", 40, "목표 기업 요구 자격증 취득"),
    ("fit_score",    "전공 적합성",   20, "같은 계열 기업으로 목표 조정"),
    ("talent_score", "인재상 일치도", 10, "기업 인재상과 겹치는 강점 선택"),
]

_FAILURE_KEY = "_score_explain_error"
_FALLBACKS_SUPPORTED = True


def _api_key() -> str:
    for name in ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        try:
            value = st.secrets.get(name, "")
        except Exception:
            value = ""
        if value:
            return str(value).strip()
    return ""


def has_api_key() -> bool:
    return bool(_api_key())


def last_failure() -> str:
    """키가 있는데도 규칙 기반으로 내려갔을 때의 사유."""
    if not has_api_key():
        return ""
    try:
        return st.session_state.get(_FAILURE_KEY, "") or ""
    except Exception:
        return ""


def weakest_item(result: dict) -> tuple:
    """
    점수를 가장 많이 남긴 항목. '올리면 이득이 큰 곳'을 고르는 기준이라
    절대 점수가 아니라 **남은 점수**로 판단한다.
    반환값: (키, 라벨, 획득점, 배점, 제안문구)
    """
    best = None
    for key, label, full, action in ITEMS:
        got = float(result.get(key, 0) or 0)
        room = full - got
        if best is None or room > best[0]:
            best = (room, key, label, got, full, action)
    _, key, label, got, full, action = best
    return key, label, got, full, action


def _fingerprint(profile: dict, result: dict, company_name: str) -> str:
    payload = {
        "scores": {k: result.get(k) for k, _, _, _ in ITEMS},
        "final": result.get("final_score"),
        "dept": profile.get("dept", ""),
        "grade": profile.get("grade"),
        "certs": sorted(profile.get("certs") or []),
        "strengths": sorted(profile.get("strengths") or []),
        "company": company_name,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ------------------------------------------------------------
# 프롬프트
# ------------------------------------------------------------
SYSTEM_PROMPT = """너는 마이스터고 3학년 학생의 취업 준비를 돕는 선생님이다.
학생이 방금 받은 '취업 등용문 점수'를 학생 본인에게 설명한다.

지켜야 할 것
- 존댓말로, 친근하되 호들갑스럽지 않게 쓴다.
- 설명은 2~3문장. 그 뒤에 개선 제안 1가지를 한 문장으로 덧붙인다.
- 점수를 다시 나열하지 마라. 학생은 이미 숫자를 보고 있다.
  대신 "무엇이 점수를 끌어올렸고 무엇이 남았는지"를 말로 풀어라.
- 낮은 점수를 나무라지 마라. 지금 점수는 출발선이지 평가가 아니다.
- 제안은 반드시 하나만, 가장 점수를 많이 남긴 항목에 대해 말한다.
- 숫자를 지어내지 마라. 주어진 점수 외의 수치를 쓰지 않는다.

출력 형식 (다른 말 없이 이것만)
설명: <2~3문장>
제안: <한 문장>"""


def _user_prompt(profile: dict, result: dict, company_name: str) -> str:
    lines = [f"항목별 점수 (획득/배점)"]
    for key, label, full, _ in ITEMS:
        lines.append(f"- {label}: {result.get(key, 0)} / {full}")
    lines.append(f"총점: {result.get('final_score')} / 100")
    lines.append("")
    lines.append("학생 정보")
    lines.append(f"- 학과 계열: {profile.get('dept') or '미입력'}")
    lines.append(f"- 내신 등급: {profile.get('grade')}")
    lines.append(f"- 보유 자격증: {', '.join(profile.get('certs') or []) or '없음'}")
    lines.append(f"- 강점 키워드: {', '.join(profile.get('strengths') or []) or '없음'}")
    lines.append(f"- 목표 기업: {company_name or '선택 안 함'}")

    _, label, got, full, action = weakest_item(result)
    lines.append("")
    lines.append(f"가장 점수를 많이 남긴 항목: {label} ({got}/{full}). "
                 f"이 항목에 대해 '{action}' 방향으로 제안하라.")
    return "\n".join(lines)


def _parse(text: str) -> dict:
    """모델 출력을 설명/제안으로 가른다. 형식이 어긋나도 통째로 설명에 담는다."""
    explanation, suggestion = "", ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("설명:"):
            explanation = line[3:].strip()
        elif line.startswith("제안:"):
            suggestion = line[3:].strip()
    if not explanation:
        explanation = text.strip()
    return {"explanation": explanation, "suggestion": suggestion}


# ------------------------------------------------------------
# 규칙 기반 설명 (키가 없거나 호출 실패 시)
# ------------------------------------------------------------
def _rule_based(profile: dict, result: dict, company_name: str) -> dict:
    final = float(result.get("final_score", 0) or 0)
    strong = [label for key, label, full, _ in ITEMS
              if float(result.get(key, 0) or 0) >= full * 0.7]
    _, weak_label, got, full, action = weakest_item(result)

    if strong:
        head = f"{', '.join(strong[:2])}에서 점수가 잘 나왔습니다."
    else:
        head = "아직 각 항목이 고르게 채워지기 전입니다."

    if final >= 80:
        body = "지금 수준이면 목표 기업 지원에 충분히 도전해볼 만합니다."
    elif final >= 50:
        body = "합격선에 가까워지는 중이라, 한 항목만 더 채우면 체감이 크게 달라집니다."
    else:
        body = "지금 점수는 평가가 아니라 출발선입니다. 채울 곳이 뚜렷하다는 뜻이기도 해요."

    # 조사는 services/coverletter.py 의 처리를 그대로 쓴다 — '이(가)' 같은
    # 표기는 학생이 읽는 화면에 어울리지 않는다.
    room = full - got
    if room < 3:
        # 거의 만점이면 '여기가 남았다'고 말하는 것이 오히려 어색하다.
        # 같은 항목이 '잘 나왔다'와 '남았다'에 동시에 들어가는 문제도 함께 사라진다.
        tail = "채울 곳이 거의 남지 않았습니다."
        suggestion = "이제 면접 실전 연습으로 넘어가세요."
    else:
        tail = apply_josa(f"{weak_label}#이 {room:.0f}점 남아 가장 여유가 큽니다.")
        # '부터'는 받침에 따라 변하지 않아 조사 처리가 필요 없다.
        suggestion = f"{action}부터 시작해보세요."
    return {"explanation": f"{head} {body} {tail}", "suggestion": suggestion}


# ------------------------------------------------------------
# Claude 호출
# ------------------------------------------------------------
def _claude(profile: dict, result: dict, company_name: str, api_key: str) -> dict:
    global _FALLBACKS_SUPPORTED
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=1)
    params = {
        "model": MODEL_NAME,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "output_config": {"effort": EFFORT},
        "messages": [{"role": "user",
                      "content": _user_prompt(profile, result, company_name)}],
    }

    if _FALLBACKS_SUPPORTED:
        try:
            response = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params)
        except anthropic.BadRequestError:
            # 이 계정/리전에서 beta 파라미터가 거부됨 → 이후로는 표준 경로만
            _FALLBACKS_SUPPORTED = False
            response = client.messages.create(**params)
    else:
        response = client.messages.create(**params)

    if getattr(response, "stop_reason", None) == "refusal":
        raise ValueError("모델이 설명 생성을 거절했습니다 (stop_reason=refusal)")

    text = "".join(b.text for b in response.content
                   if getattr(b, "type", "") == "text").strip()
    if not text:
        raise ValueError("응답에 본문 텍스트가 없습니다")
    return _parse(text)


@st.cache_data(ttl=CACHE_TTL, max_entries=CACHE_MAX_ENTRIES, show_spinner=False)
def _explain_cached(fingerprint: str, profile_json: str, result_json: str,
                    company_name: str, use_api: bool) -> tuple[dict, str]:
    """
    fingerprint 가 같으면 재호출하지 않는다.
    API 키는 캐시 인자로 넘기지 않는다 — 캐시 저장소에 키가 남지 않도록.
    """
    profile = json.loads(profile_json)
    result = json.loads(result_json)

    if use_api:
        key = _api_key()
        if key:
            try:
                return _claude(profile, result, company_name, key), "ai"
            except Exception as exc:
                try:
                    st.session_state[_FAILURE_KEY] = f"{type(exc).__name__}: {exc}"[:300]
                except Exception:
                    pass
    return _rule_based(profile, result, company_name), "rule"


def explain(profile: dict, result: dict, company: dict | None = None):
    """
    화면에서 부르는 공개 함수.
    반환값: (설명 dict{explanation, suggestion}, 방식 "ai"|"rule")
    """
    company_name = (company or {}).get("name", "")
    fingerprint = _fingerprint(profile, result, company_name)
    return _explain_cached(
        fingerprint,
        json.dumps(profile, ensure_ascii=False, sort_keys=True, default=str),
        json.dumps(result, ensure_ascii=False, sort_keys=True, default=str),
        company_name,
        has_api_key(),
    )
