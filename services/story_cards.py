# -*- coding: utf-8 -*-
"""
services/story_cards.py
기업 탐색 '스토리' — 기업 1곳을 카드 5장으로 요약

    카드1  회사 한 줄 소개                 ┐
    카드2  하는 일 · 주요 제품/서비스        │ Claude 요약 (원본 데이터만 근거)
    카드3  채용 직무 · 자격증 · 우대 전공    │ 실패·무료 요금제면 원본으로 만든 기본 카드
    카드4  근무지 · 근무 조건 · 복리후생     ┘
    카드5  이 학생의 매칭 점수              ← Claude 가 아니라 코드. 기존 100점 로직 결과 그대로

▣ 왜 카드5는 코드로 만드는가
   점수는 스펙 진단 · 기업 목록과 같은 숫자여야 한다(core/company_filter.py).
   LLM 이 숫자를 다시 쓰면 반올림이나 표현이 달라져 화면마다 점수가 어긋난다.

▣ 과금 방어 (services/score_explain.py 와 같은 구조 + 파일 캐시)
   1단 st.cache_data : 같은 기업·같은 원본이면 프로세스 안에서 재호출하지 않는다.
   2단 story_cache.json : 앱이 재시작돼도 이미 요약한 기업은 다시 부르지 않는다.
       키는 기업 ID + 원본 데이터 지문 — 팀이 기업 정보를 고치면 자동으로 다시 요약된다.
   3단 프리미엄 게이트 : 키가 있어도 프리미엄 회원이 아니면 호출하지 않는다
       (services/premium.py). 대신 파일 캐시에 이미 있는 요약은 무료로 보여준다.
   4단 실패 : 파싱·호출이 실패하면 원본 데이터로 기본 카드를 만들고 사유를 남긴다.

▣ 지어내지 않기
   기업 데이터에 근무지·근무 시간 같은 항목이 없다. 기본 카드는 없는 값을
   '정보 없음'으로 쓰고, Claude 에게도 같은 지시를 준다.
"""

import hashlib
import json
import os
import re
import tempfile
import threading
from datetime import datetime

import streamlit as st

from services import premium

# 현행 Opus. 카드 4장(제목 15자 · 본문 60자) 요약은 깊은 추론이 필요 없어 effort 를 낮춘다.
# 이 모델은 thinking 을 끌 수 없고 추론 토큰이 max_tokens 에 함께 잡히므로 상한을 넉넉히 둔다
# (상한일 뿐이라 실제 생성량만 과금된다).
MODEL_NAME = "claude-opus-5-5"
MAX_TOKENS = 8000
EFFORT = "low"
REQUEST_TIMEOUT = 40.0

CACHE_TTL = 24 * 3600
CACHE_MAX_ENTRIES = 256

TITLE_MAX = 15
BODY_MAX = 60
AI_CARD_COUNT = 4

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_CACHE_PATH = os.path.join(BASE_DIR, "data", "story_cache.json")
_FILE_LOCK = threading.Lock()

_FAILURE_KEY = "_story_cards_error"
_FALLBACKS_SUPPORTED = True

NO_INFO = "정보 없음"

SYSTEM_PROMPT = """너는 고등학생이 기업 정보를 10초 안에 이해하도록 돕는 에디터다.
주어진 기업 원본 데이터만 근거로 요약하고, 데이터에 없는 내용은 절대 추가하지 마라.
각 카드는 title(15자 이내)과 body(2줄, 60자 이내)로 구성하고, 고등학생이 이해할 쉬운 말로 쓴다.
반드시 아래 JSON 형식만 출력하고 다른 텍스트나 마크다운은 쓰지 마라.
{"cards": [{"title": "", "body": "", "emoji": ""}, ... 4개]}"""

# 카드별로 다루는 내용 — 사용자 프롬프트와 기본 카드가 같은 순서를 쓴다
CARD_TOPICS = [
    "카드1: 회사 한 줄 소개",
    "카드2: 하는 일 / 주요 제품·서비스",
    "카드3: 채용 직무, 필요 자격증, 우대 전공",
    "카드4: 근무지, 근무 조건, 복리후생 (데이터에 없는 항목은 '정보 없음'이라고 쓴다)",
]
DEFAULT_EMOJIS = ["🏢", "🛠️", "📋", "📍", "🎯"]

# 원본 데이터 중 요약에 넘길 항목. 별점·장단점·면접질문은 예시(모의) 데이터라
# 사실처럼 요약되면 안 되므로 넘기지 않는다.
_SOURCE_FIELDS = [
    ("name", "기업명"),
    ("size_tag", "기업 규모"),
    ("field_tag", "분야"),
    ("category", "전공 계열"),
    ("description", "한 줄 소개"),
    ("hire_dept", "채용 부서"),
    ("required_certs", "필요 자격증"),
    ("required_skills", "요구 역량"),
    ("benefit_short", "복리후생"),
    ("region", "근무지"),
    ("work_conditions", "근무 조건"),
]


# ------------------------------------------------------------
# 원본 데이터
# ------------------------------------------------------------
def source_payload(company: dict) -> dict:
    """요약 근거로 넘길 원본. 값이 비어 있는 항목은 아예 싣지 않는다."""
    out = {}
    for key, label in _SOURCE_FIELDS:
        value = company.get(key)
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value if str(v).strip())
        value = str(value or "").strip()
        if value:
            out[label] = value
    return out


def _fingerprint(company_id: str, payload: dict) -> str:
    blob = json.dumps({"id": company_id, "src": payload, "model": MODEL_NAME},
                      ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------
# 파싱
# ------------------------------------------------------------
_FENCE_RE = re.compile(r"^\s*```[a-zA-Z]*\s*|\s*```\s*$")


def strip_code_fence(text: str) -> str:
    """```json ... ``` 같은 코드펜스를 벗긴다. 앞뒤 설명문이 붙어도 첫 { ~ 마지막 } 만 쓴다."""
    text = _FENCE_RE.sub("", (text or "").strip())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return text


def _clip(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def parse_cards(text: str) -> list[dict]:
    """
    Claude 응답 → 카드 4장. 형식이 어긋나면 ValueError.
    글자 수 상한은 화면이 깨지지 않도록 여기서 한 번 더 지킨다.
    """
    data = json.loads(strip_code_fence(text))
    cards = data.get("cards") if isinstance(data, dict) else None
    if not isinstance(cards, list) or len(cards) < AI_CARD_COUNT:
        raise ValueError(f"카드가 {AI_CARD_COUNT}장이 아닙니다")
    out = []
    for i, card in enumerate(cards[:AI_CARD_COUNT]):
        if not isinstance(card, dict):
            raise ValueError("카드 형식이 아닙니다")
        title, body = _clip(card.get("title"), TITLE_MAX), _clip(card.get("body"), BODY_MAX)
        if not title or not body:
            raise ValueError("빈 카드가 있습니다")
        emoji = _clip(card.get("emoji"), 4) or DEFAULT_EMOJIS[i]
        out.append({"title": title, "body": body, "emoji": emoji})
    return out


# ------------------------------------------------------------
# 기본 카드 (키 없음 · 무료 요금제 · 실패)
# ------------------------------------------------------------
def basic_cards(company: dict) -> list[dict]:
    """원본 데이터만으로 만든 카드 4장. 없는 값은 '정보 없음'."""
    name = company.get("name") or "이 기업"
    size = company.get("size_tag") or ""
    field = company.get("field_tag") or company.get("category") or ""
    certs = ", ".join(company.get("required_certs") or []) or NO_INFO
    region = str(company.get("region") or "").strip() or NO_INFO
    conditions = str(company.get("work_conditions") or "").strip() or NO_INFO
    benefit = str(company.get("benefit_short") or "").strip() or NO_INFO

    return [
        {"title": _clip(name, TITLE_MAX), "emoji": DEFAULT_EMOJIS[0],
         "body": _clip(" · ".join(x for x in (size, field) if x) or NO_INFO, BODY_MAX)},
        {"title": "하는 일", "emoji": DEFAULT_EMOJIS[1],
         "body": _clip(company.get("description") or NO_INFO, BODY_MAX)},
        {"title": "이런 사람 뽑아요", "emoji": DEFAULT_EMOJIS[2],
         "body": _clip(f"{company.get('hire_dept') or '채용 부서 정보 없음'} · 자격증 {certs}"
                       f" · 우대 계열 {company.get('category') or NO_INFO}", BODY_MAX)},
        {"title": "근무 · 복지", "emoji": DEFAULT_EMOJIS[3],
         "body": _clip(f"근무지 {region} · 근무조건 {conditions} · 복지 {benefit}", BODY_MAX)},
    ]


def score_card(company: dict) -> dict:
    """카드5 — 기존 매칭 점수(company['match_score'], core/company_filter.score_all)."""
    score = company.get("match_score")
    if score is None:
        return {"title": "내 매칭 점수", "emoji": DEFAULT_EMOJIS[4], "score": None,
                "body": "스펙 진단을 먼저 하면 이 기업과의 매칭 점수가 나와요."}
    score = float(score)
    if score >= 70:
        verdict = "합격 안정권이에요"
    elif score >= 50:
        verdict = "조금만 더 채우면 돼요"
    else:
        verdict = "보완이 필요해요"
    return {"title": "내 매칭 점수", "emoji": DEFAULT_EMOJIS[4], "score": round(score, 1),
            "body": f"100점 만점에 {score:.0f}점 · {verdict}"}


# ------------------------------------------------------------
# 파일 캐시 (data/story_cache.json)
# ------------------------------------------------------------
def _read_file_cache() -> dict:
    try:
        with open(STORY_CACHE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _file_cache_get(company_id: str, fingerprint: str) -> list[dict] | None:
    entry = _read_file_cache().get(company_id)
    if isinstance(entry, dict) and entry.get("fingerprint") == fingerprint:
        cards = entry.get("cards")
        if isinstance(cards, list) and len(cards) == AI_CARD_COUNT:
            return cards
    return None


def _file_cache_put(company_id: str, fingerprint: str, cards: list[dict]) -> None:
    """임시파일 + os.replace 로 원자적으로 쓴다. 실패해도 화면은 멈추지 않는다."""
    with _FILE_LOCK:
        doc = _read_file_cache()
        doc[company_id] = {
            "fingerprint": fingerprint, "model": MODEL_NAME, "cards": cards,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            os.makedirs(os.path.dirname(STORY_CACHE_PATH), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(STORY_CACHE_PATH), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=1)
            os.replace(tmp, STORY_CACHE_PATH)
        except OSError:
            pass


# ------------------------------------------------------------
# Claude 호출
# ------------------------------------------------------------
def _api_key() -> str:
    for name in ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        try:
            value = st.secrets.get(name, "")
        except Exception:
            value = ""
        if value:
            return str(value).strip()
    return ""


def _user_prompt(payload: dict) -> str:
    lines = ["[기업 원본 데이터]"]
    lines += [f"- {label}: {value}" for label, value in payload.items()]
    lines += ["", "[카드 구성 — 순서대로 4장]"] + CARD_TOPICS
    return "\n".join(lines)


def _claude(payload: dict, api_key: str) -> list[dict]:
    global _FALLBACKS_SUPPORTED
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=1)
    params = {
        "model": MODEL_NAME,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "output_config": {"effort": EFFORT},
        "messages": [{"role": "user", "content": _user_prompt(payload)}],
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
        raise ValueError("모델이 요약을 거절했습니다 (stop_reason=refusal)")

    text = "".join(b.text for b in response.content
                   if getattr(b, "type", "") == "text").strip()
    if not text:
        raise ValueError("응답에 본문 텍스트가 없습니다")
    return parse_cards(text)


@st.cache_data(ttl=CACHE_TTL, max_entries=CACHE_MAX_ENTRIES, show_spinner=False)
def _summary_cached(company_id: str, fingerprint: str, payload_json: str,
                    company_json: str, use_api: bool) -> tuple[list[dict], str]:
    """
    기업 ID(+원본 지문) 기준 캐시. 반환값: (카드 4장, "ai" | "basic")
    API 키는 캐시 인자로 넘기지 않는다 — 캐시 저장소에 키가 남지 않도록.
    파일 캐시는 이 함수 밖(make_story_cards)에서 먼저 본다 — 다른 사용자가 방금
    요약한 기업이 이 프로세스의 'basic' 캐시에 가려지지 않게 하기 위해서다.
    """
    company = json.loads(company_json)
    if use_api:
        key = _api_key()
        if key:
            try:
                cards = _claude(json.loads(payload_json), key)
                _file_cache_put(company_id, fingerprint, cards)
                return cards, "ai"
            except Exception as exc:
                try:
                    st.session_state[_FAILURE_KEY] = f"{type(exc).__name__}: {exc}"[:300]
                except Exception:
                    pass
    return basic_cards(company), "basic"


def last_failure() -> str:
    try:
        return st.session_state.get(_FAILURE_KEY, "") or ""
    except Exception:
        return ""


# ------------------------------------------------------------
# 공개 함수
# ------------------------------------------------------------
def make_story_cards(company: dict) -> list[dict]:
    """
    기업 1곳 → 카드 5장. 각 카드: {title, body, emoji, source[, score]}
    source: "ai"(방금 요약) · "cache"(저장된 요약) · "basic"(원본 기본 카드) · "score"(카드5)

    company 는 core/company_filter.score_all() 을 거친 dict 를 기대한다
    (match_score 가 붙어 있어야 카드5에 점수가 나온다).
    """
    company_id = str(company.get("id") or company.get("name") or "")
    payload = source_payload(company)
    base = {k: v for k, v in company.items() if k != "match_score"}

    fingerprint = _fingerprint(company_id, payload)

    cards = _file_cache_get(company_id, fingerprint)
    source = "cache"
    if cards is None:
        cards, source = _summary_cached(
            company_id,
            fingerprint,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            json.dumps(base, ensure_ascii=False, sort_keys=True, default=str),
            # 키가 있어도 프리미엄 회원이 아니면 API 를 부르지 않는다 (services/premium.py)
            premium.ai_enabled(),
        )
    out = [{**card, "source": source} for card in cards]
    out.append({**score_card(company), "source": "score"})
    return out
