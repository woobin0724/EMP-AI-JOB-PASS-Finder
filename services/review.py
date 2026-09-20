# -*- coding: utf-8 -*-
"""
services/review.py
[Phase D-2] 자소서 첨삭 — 학생이 직접 쓴 초안에 피드백

▣ 생성과 첨삭은 다른 일이다
   생성은 재료로 글을 만든다. 첨삭은 이미 있는 글을 읽고 무엇이 되고 무엇이
   안 됐는지 말한다. 그래서 프롬프트도 출력 형식도 따로 둔다.

▣ 과금 방어는 services/llm.py 와 같은 3단
   1단 캐싱  : 같은 초안 + 같은 조건이면 재호출하지 않는다. 학생이 '첨삭'을
              여러 번 눌러도 과금은 최초 1회다.
   2단 키 부재: 키가 없으면 네트워크로 나가지 않고 규칙 기반 점검을 돌린다.
   3단 실패  : 실패 시 규칙 기반으로 내려가되 사유를 남긴다.

▣ 규칙 기반 점검은 'AI 첨삭인 척'하지 않는다
   임의의 글을 규칙으로 읽어 깊은 피드백을 줄 수는 없다. 대신 기계가 확실히
   셀 수 있는 것만 본다 — 분량, 상투어, 문장 길이, 구체적 근거(숫자·고유명사),
   기업 인재상 반영 여부. 화면에서도 'AI 첨삭'이 아니라 '규칙 기반 점검'으로
   표시해 학생이 무엇을 받았는지 알게 한다.
"""

import hashlib
import json
import re

import streamlit as st

MODEL_NAME = "claude-opus-5"
# 첨삭은 초안 전문을 읽고 답하므로 생성보다 출력이 길 수 있다.
# 현행 모델은 추론 토큰이 기본 on 이고 그 양도 max_tokens 에 함께 잡힌다.
MAX_TOKENS = 16000
EFFORT = "medium"
REQUEST_TIMEOUT = 90.0

CACHE_TTL = 3600
CACHE_MAX_ENTRIES = 64

MIN_CHARS = 100          # 이보다 짧으면 첨삭할 내용이 없다
MAX_CHARS = 4000         # 이보다 길면 자소서가 아니라 다른 글이다

_FAILURE_KEY = "_review_last_error"
_FALLBACKS_SUPPORTED = True

# 규칙 점검에서 찾아낼 상투어 — 자소서를 똑같아 보이게 만드는 표현들.
# services/coverletter.py 의 BANNED_EXPRESSIONS 와 같은 목록을 기계가
# 찾을 수 있는 형태로 옮긴 것이다.
CLICHES = [
    "저는 ~한 사람입니다", "귀사", "귀 사", "영광입니다", "영광으로 생각",
    "어릴 적부터", "어렸을 때부터", "열정", "최선을 다하겠습니다",
    "뼈를 묻겠습니다", "없어서는 안 될", "귀중한 기회", "성실함을 바탕으로",
    "막중한 책임감", "글로벌 인재",
]


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
    if not has_api_key():
        return ""
    try:
        return st.session_state.get(_FAILURE_KEY, "") or ""
    except Exception:
        return ""


def validate_draft(draft: str) -> str:
    """첨삭을 돌리기 전 검사. 문제가 없으면 빈 문자열."""
    text = (draft or "").strip()
    if not text:
        return "초안을 입력해주세요."
    if len(text) < MIN_CHARS:
        return f"초안이 너무 짧습니다. {MIN_CHARS}자 이상 써주세요 (현재 {len(text)}자)."
    if len(text) > MAX_CHARS:
        return f"초안이 너무 깁니다. {MAX_CHARS}자 이내로 줄여주세요 (현재 {len(text)}자)."
    return ""


# ------------------------------------------------------------
# 프롬프트
# ------------------------------------------------------------
SYSTEM_PROMPT = """당신은 마이스터고 학생의 자기소개서를 첨삭하는 진로 상담 교사입니다.
학생이 직접 쓴 초안을 읽고 피드백을 줍니다.

[태도]
- 학생이 쓴 글입니다. 다시 쓰지 말고, 이 글이 더 나아지도록 짚어주십시오.
- 존댓말로, 구체적으로 씁니다. '좋습니다' 같은 빈 칭찬은 도움이 되지 않습니다.
- 잘된 점을 먼저 말합니다. 고칠 것만 나열하면 학생은 글을 지웁니다.

[반드시 지킬 것]
1. 초안에 없는 사실을 지어내지 마십시오. 학생이 쓰지 않은 경험·수상·수치를
   전제로 조언하면 학생이 면접에서 무너집니다.
2. 개선점은 '무엇이 문제인지'가 아니라 '어떻게 바꾸면 되는지'까지 씁니다.
3. 예시 문장은 학생의 초안에 있는 재료만 써서 한 문장으로 만듭니다.
   새 경험을 만들어내지 마십시오.
4. 추상어를 지적할 때는 초안의 해당 표현을 그대로 인용하십시오.

[출력 형식 — 다른 말 없이 이것만]
잘된 점:
- <항목> (1~2개)
개선할 점:
- <항목> (2~3개)
예시 문장:
<초안의 재료로 고쳐 쓴 한 문장>"""


def _user_prompt(draft: str, company: dict | None, strengths: list | None) -> str:
    parts = []
    if company:
        parts.append(f"지원 기업: {company.get('name','')}")
        talent = ", ".join(company.get("ideal_talent") or [])
        if talent:
            parts.append(f"이 기업의 인재상: {talent}")
    if strengths:
        parts.append(f"학생이 고른 강점 키워드: {', '.join(strengths)}")
    header = "\n".join(parts)
    if header:
        header += "\n\n"
    return f"{header}[학생이 쓴 자기소개서 초안]\n{draft.strip()}"


def _parse(text: str) -> dict:
    """모델 출력을 세 구역으로 가른다. 형식이 어긋나면 통째로 본문에 담는다."""
    good, improve, example = [], [], ""
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("잘된 점"):
            section = "good"; continue
        if line.startswith("개선할 점") or line.startswith("개선점"):
            section = "improve"; continue
        if line.startswith("예시 문장"):
            section = "example"; continue
        item = line.lstrip("-•* ").strip()
        if section == "good":
            good.append(item)
        elif section == "improve":
            improve.append(item)
        elif section == "example":
            example = f"{example} {item}".strip()

    if not good and not improve:
        return {"good": [], "improve": [], "example": "", "raw": text.strip()}
    return {"good": good[:2], "improve": improve[:3], "example": example, "raw": ""}


# ------------------------------------------------------------
# 규칙 기반 점검 (키가 없거나 호출 실패 시)
# ------------------------------------------------------------
def _rule_based(draft: str, company: dict | None, strengths: list | None) -> dict:
    text = draft.strip()
    sentences = [s for s in re.split(r"(?<=[.!?다])\s+", text) if s.strip()]
    long_ones = [s for s in sentences if len(s) > 90]
    found_cliches = [c for c in CLICHES if c.replace("~", "") in text]
    numbers = re.findall(r"\d+(?:\.\d+)?\s*(?:mm|개|번|명|시간|일|주|개월|년|%|점)", text)

    good, improve = [], []

    if numbers:
        good.append(f"구체적인 수치({', '.join(numbers[:3])})가 들어가 장면이 그려집니다.")
    if len(sentences) >= 5 and not long_ones:
        good.append("문장 길이가 고르게 유지돼 읽기 편합니다.")
    talent = set(company.get("ideal_talent") or []) if company else set()
    hit_talent = [t for t in talent if t in text]
    if hit_talent:
        good.append(f"기업 인재상({', '.join(hit_talent)})이 글에 실제로 드러납니다.")
    if not good:
        good.append(f"{len(text)}자 분량으로 초안의 뼈대가 잡혀 있습니다.")

    if found_cliches:
        improve.append(
            f"상투어가 보입니다 — {', '.join(found_cliches[:3])}. "
            "이 표현들은 거의 모든 자소서에 있어 눈에 남지 않습니다. "
            "같은 뜻을 본인 경험으로 바꿔 써보세요."
        )
    if long_ones:
        improve.append(
            f"{len(long_ones)}개 문장이 90자를 넘습니다. "
            "한 문장에 한 가지만 담도록 끊으면 훨씬 또렷해집니다."
        )
    if not numbers:
        improve.append(
            "구체적인 수치나 고유명사가 없습니다. "
            "'열심히 했다' 대신 '3일간 측정 기록을 남겼다'처럼 세어볼 수 있는 "
            "사실을 넣으면 글이 달라집니다."
        )
    if talent and not hit_talent:
        improve.append(
            f"지원 기업 인재상({', '.join(sorted(talent))})과 이어지는 대목이 "
            "보이지 않습니다. 키워드를 나열하지 말고, 본인 경험 중 그 가치와 "
            "맞닿는 장면을 하나 고르세요."
        )
    if not improve:
        improve.append("기계가 셀 수 있는 항목에서는 문제가 보이지 않습니다. "
                       "이제 선생님이나 친구에게 소리 내어 읽어봐 주세요.")

    return {
        "good": good[:2],
        "improve": improve[:3],
        "example": "",   # 예시 문장은 글을 이해해야 만들 수 있어 규칙으로 쓰지 않는다
        "raw": "",
    }


# ------------------------------------------------------------
# Claude 호출
# ------------------------------------------------------------
def _claude(draft: str, company: dict | None, strengths: list | None,
            api_key: str) -> dict:
    global _FALLBACKS_SUPPORTED
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=1)
    params = {
        "model": MODEL_NAME,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "output_config": {"effort": EFFORT},
        "messages": [{"role": "user",
                      "content": _user_prompt(draft, company, strengths)}],
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
        raise ValueError("모델이 첨삭을 거절했습니다 (stop_reason=refusal)")

    text = "".join(b.text for b in response.content
                   if getattr(b, "type", "") == "text").strip()
    if not text:
        raise ValueError("응답에 본문 텍스트가 없습니다")
    return _parse(text)


@st.cache_data(ttl=CACHE_TTL, max_entries=CACHE_MAX_ENTRIES, show_spinner=False)
def _review_cached(fingerprint: str, draft: str, company_json: str,
                   strengths_json: str, use_api: bool) -> tuple[dict, str]:
    company = json.loads(company_json) if company_json else None
    strengths = json.loads(strengths_json) if strengths_json else []

    if use_api:
        key = _api_key()
        if key:
            try:
                return _claude(draft, company, strengths, key), "ai"
            except Exception as exc:
                try:
                    st.session_state[_FAILURE_KEY] = f"{type(exc).__name__}: {exc}"[:300]
                except Exception:
                    pass
    return _rule_based(draft, company, strengths), "rule"


def review(draft: str, company: dict | None = None, strengths: list | None = None):
    """
    화면에서 부르는 공개 함수.
    반환값: (피드백 dict{good, improve, example, raw}, 방식 "ai"|"rule")
    """
    payload = {
        "draft": (draft or "").strip(),
        "company": (company or {}).get("id", ""),
        "strengths": sorted(strengths or []),
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    fingerprint = hashlib.sha256(blob.encode("utf-8")).hexdigest()

    return _review_cached(
        fingerprint,
        (draft or "").strip(),
        json.dumps(company, ensure_ascii=False, sort_keys=True, default=str) if company else "",
        json.dumps(sorted(strengths or []), ensure_ascii=False),
        has_api_key(),
    )
