# -*- coding: utf-8 -*-
"""
services/interview.py
[big-patch 3단계] 텍스트 모의 면접 — 질문 만들기 · 답변 피드백

▣ 질문은 '연습용 일반 질문'이다
   기업 유형별 일반 질문 + 내 자격증·전공 관련 질문으로 구성한다.
   특정 기업의 실제 기출이라고 주장하지 않는다(화면에도 그렇게 표시한다).
   가상 예시 기업의 예시 면접 질문도 '예시'로만 섞는다.

▣ 피드백 경로 (자소서 첨삭과 같은 3단)
   1) AI 사용 가능(프리미엄 + 키 + 하루 한도 안) → 초안 등급(저가) 모델로 피드백, 캐시
   2) 아니면 규칙 기반 점검 — 분량 · 구체 근거(숫자) · 행동/결과 서술 · 인재상 연결
   3) 무료 계정은 '요청문 복사'로 무료 AI 에 붙여넣어 쓸 수 있다
"""

import hashlib
import json
import random
import re

import streamlit as st

from services import premium, talent_link
from services.ai_models import TIER_DRAFT

QUESTIONS_PER_SESSION = 5
MIN_ANSWER = 30
MAX_ANSWER = 1500

# 기업 유형별 일반 질문 — 팀이 만든 연습 질문 (특정 기업 기출 아님)
GENERAL_BY_TYPE = {
    "공기업": [
        "공공기관에서 일하는 사람에게 가장 중요한 태도는 무엇이라고 생각하나요? 경험과 함께 말해 주세요.",
        "규정과 절차를 지키는 것이 불편했지만 끝까지 지킨 경험이 있나요?",
        "우리 기관의 일이 지역 주민에게 어떤 도움이 된다고 생각하나요?",
        "안전 수칙을 지키지 않는 동료를 본다면 어떻게 하겠어요?",
    ],
    "대기업": [
        "팀 프로젝트에서 의견이 부딪혔을 때 어떻게 조율했는지 말해 주세요.",
        "입사 후 3년 안에 이루고 싶은 목표와 그 이유를 말해 주세요.",
        "새로운 기술이나 장비를 스스로 익힌 경험이 있나요?",
        "큰 조직에서 내 역할이 작게 느껴질 때 어떻게 동기를 유지하겠어요?",
    ],
    "중견기업": [
        "우리 회사에 지원한 이유를 본인의 전공과 연결해 말해 주세요.",
        "실습 중 실수를 했을 때 어떻게 대처했는지 말해 주세요.",
        "선배에게 배운 것 중 가장 기억에 남는 것은 무엇인가요?",
    ],
    "중소기업": [
        "작은 조직에서는 여러 일을 함께 맡습니다. 맡은 일 밖의 일을 해본 경험이 있나요?",
        "입사 첫 달에 가장 먼저 익히고 싶은 것은 무엇인가요?",
        "현장에서 바로 쓸 수 있는 본인의 실무 능력을 말해 주세요.",
    ],
    "강소기업": [
        "작은 조직에서는 여러 일을 함께 맡습니다. 맡은 일 밖의 일을 해본 경험이 있나요?",
        "우리 회사의 제품이나 기술 중 관심 있는 분야를 말해 주세요.",
        "현장에서 바로 쓸 수 있는 본인의 실무 능력을 말해 주세요.",
    ],
    "스타트업": [
        "정해진 방법이 없을 때 스스로 방법을 찾아본 경험을 말해 주세요.",
        "빠르게 바뀌는 업무 환경에 어떻게 적응하겠어요?",
    ],
}
COMMON = [
    "1분 동안 자기소개를 해 주세요.",
    "학교생활 중 가장 끈기 있게 해낸 일은 무엇인가요?",
    "본인의 단점과 그것을 고치려고 한 노력을 말해 주세요.",
]
CERT_TEMPLATES = [
    "{cert} 자격증을 준비하며 가장 어려웠던 과제와 해결 과정을 말해 주세요.",
    "{cert} 자격증으로 익힌 내용을 현장에서 어떻게 쓸 수 있을까요?",
]
MAJOR_TEMPLATES = [
    "{major} 실습에서 안전을 위해 꼭 지킨 것을 말해 주세요.",
    "{major} 전공을 고른 이유와, 공부하며 달라진 점을 말해 주세요.",
]

SYSTEM_PROMPT = """당신은 마이스터고 학생의 모의 면접을 돕는 면접 코치입니다.
면접 질문 하나와 학생의 답변을 읽고, 지원 기업의 인재상 기준으로 피드백을 줍니다.

[반드시 지킬 것]
1. 답변에 없는 경험·수치를 지어내지 마십시오.
2. 실제 기업의 면접 기준을 아는 것처럼 말하지 마십시오. 주어진 인재상 키워드만 기준으로 씁니다.
3. 존댓말, 구체적으로. 잘된 점을 먼저.

[출력 형식 — 다른 말 없이 이것만]
잘된 점:
- <항목> (1~2개)
보완할 점:
- <항목> (2개)
인재상 연결:
- <인재상 키워드>: <답변의 어느 표현이 이어지는지, 없으면 '드러나지 않음'>
다시 말해 보기:
<답변의 재료만 써서 고친 두세 문장>"""


def build_questions(company: dict | None, certs: list, major: str = "",
                    seed: int = 0, n: int = QUESTIONS_PER_SESSION) -> list[dict]:
    """
    연습 질문 목록. 반환: [{q, kind}] — kind: 공통 · 유형 · 자격증 · 전공 · 예시 기업.
    같은 입력 + 같은 seed 면 같은 질문(새로고침해도 바뀌지 않게).
    """
    rng = random.Random(f"{(company or {}).get('id', '')}|{seed}")
    size = (company or {}).get("size_tag", "")
    typed = list(GENERAL_BY_TYPE.get(size, GENERAL_BY_TYPE["중견기업"]))
    rng.shuffle(typed)
    picks = [{"q": COMMON[0], "kind": "공통"}]
    picks += [{"q": q, "kind": f"{size or '일반'} 유형"} for q in typed[:2]]
    certs = [c for c in (certs or []) if c]
    if certs:
        cert = rng.choice(certs)
        picks.append({"q": rng.choice(CERT_TEMPLATES).format(cert=cert), "kind": "자격증"})
    if major:
        picks.append({"q": rng.choice(MAJOR_TEMPLATES).format(major=major), "kind": "전공"})
    # 가상 예시 기업에만 있는 예시 질문 — 실제 기출이 아님을 kind 로 표시
    if company and company.get("data_kind") == "sample":
        sample_q = list(company.get("interview_questions") or [])
        if sample_q:
            picks.append({"q": rng.choice(sample_q), "kind": "예시 기업 질문"})
    rest = [q for q in COMMON[1:]]
    rng.shuffle(rest)
    picks += [{"q": q, "kind": "공통"} for q in rest]
    seen, out = set(), []
    for p in picks:
        if p["q"] not in seen:
            seen.add(p["q"])
            out.append(p)
    return out[:n]


def validate_answer(answer: str) -> str:
    text = (answer or "").strip()
    if not text:
        return "답변을 입력해 주세요."
    if len(text) < MIN_ANSWER:
        return f"답변이 너무 짧아요. {MIN_ANSWER}자 이상 써 주세요 (지금 {len(text)}자)."
    if len(text) > MAX_ANSWER:
        return f"답변이 너무 길어요. {MAX_ANSWER}자 이내로 줄여 주세요 (지금 {len(text)}자)."
    return ""


_ACTION = re.compile(r"(했습니다|했어요|했다|하였|만들었|고쳤|바꿨|정리했|확인했|시도했|해결했)")
_RESULT = re.compile(r"(결과|덕분에|그래서|그 뒤|이후|줄었|늘었|올랐|통과|합격|완성)")
_NUMBER = re.compile(r"\d+(?:\.\d+)?\s*(?:mm|개|번|명|시간|일|주|개월|년|%|점|회|등급)")


def rule_feedback(question: str, answer: str, company: dict | None) -> dict:
    """규칙 기반 피드백 — 기계가 셀 수 있는 것만 본다."""
    text = (answer or "").strip()
    talents = (company or {}).get("ideal_talent") or []
    numbers = _NUMBER.findall(text)
    has_action = bool(_ACTION.search(text))
    has_result = bool(_RESULT.search(text))
    shown, missing = talent_link.coverage(text, talents)

    # 인재상 연결이 이 기능의 기준이라 먼저 둔다
    good, improve = [], []
    if shown:
        good.append(f"인재상({', '.join(shown)})과 이어지는 표현이 있어요.")
    if numbers:
        good.append(f"숫자({', '.join(numbers[:3])})가 있어 경험이 구체적으로 들려요.")
    if has_action and has_result:
        good.append("내가 한 행동과 그 결과가 함께 나와요.")
    if not good:
        good.append(f"{len(text)}자로 질문에 대한 답의 뼈대가 있어요.")

    if not numbers:
        improve.append("횟수·기간·결과 같은 숫자를 하나 넣어 보세요. 예: '2주 동안 매일 30분'.")
    if not has_action:
        improve.append("'열심히 했다' 대신 내가 실제로 한 행동을 동사로 말해 보세요.")
    elif not has_result:
        improve.append("그래서 무엇이 달라졌는지(결과)를 한 문장 붙여 보세요.")
    if missing:
        improve.append(f"아직 드러나지 않은 인재상: {', '.join(missing)}. 이 중 하나와 맞닿는 장면을 덧붙여 보세요.")
    if len(text) > 600:
        improve.append("면접 답변으로는 길어요. 1분(약 300~400자) 안에 말할 수 있게 줄여 보세요.")
    if not improve:
        improve.append("셀 수 있는 항목에서는 문제가 없어요. 소리 내어 1분 안에 말해 보세요.")

    links = [{"talent": t, "note": "답변에 이어지는 표현이 있어요" if t in shown else "드러나지 않음"}
             for t in talents]
    return {"good": good[:3], "improve": improve[:3], "links": links, "rewrite": "", "raw": ""}


def _parse(text: str) -> dict:
    sections = {"good": [], "improve": [], "links": [], "rewrite": ""}
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("잘된 점"):
            cur = "good"; continue
        if line.startswith("보완할 점") or line.startswith("개선할 점"):
            cur = "improve"; continue
        if line.startswith("인재상 연결"):
            cur = "links"; continue
        if line.startswith("다시 말해 보기"):
            cur = "rewrite"; continue
        item = line.lstrip("-•* ").strip()
        if cur in ("good", "improve"):
            sections[cur].append(item)
        elif cur == "links":
            talent, _, note = item.partition(":")
            sections["links"].append({"talent": talent.strip(), "note": note.strip()})
        elif cur == "rewrite":
            sections["rewrite"] = f"{sections['rewrite']} {item}".strip()
    if not sections["good"] and not sections["improve"]:
        return {"good": [], "improve": [], "links": [], "rewrite": "", "raw": text.strip()}
    return {**sections, "raw": ""}


def _user_prompt(question: str, answer: str, company: dict | None) -> str:
    parts = []
    if company:
        parts.append(f"지원 기업: {company.get('name', '')} ({company.get('size_tag', '')})")
        talents = ", ".join(company.get("ideal_talent") or [])
        if talents:
            parts.append(f"인재상 키워드: {talents}")
    parts.append(f"면접 질문: {question}")
    parts.append(f"[학생 답변]\n{answer.strip()}")
    return "\n".join(parts)


def copy_prompt(question: str, answer: str, company: dict | None) -> str:
    """무료 계정용 — 무료 AI 에 붙여넣을 요청문."""
    return SYSTEM_PROMPT + "\n\n" + _user_prompt(question, answer, company)


def _api_key() -> str:
    for name in ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        try:
            value = st.secrets.get(name, "")
        except Exception:
            value = ""
        if value:
            return str(value).strip()
    return ""


_FAILURE_KEY = "_interview_last_error"


def last_failure() -> str:
    try:
        return st.session_state.get(_FAILURE_KEY, "") or ""
    except Exception:
        return ""


@st.cache_data(ttl=3600, max_entries=128, show_spinner=False)
def _feedback_cached(fingerprint: str, question: str, answer: str,
                     company_json: str, use_api: bool) -> tuple[dict, str]:
    company = json.loads(company_json) if company_json else None
    if use_api:
        key = _api_key()
        if key:
            try:
                from services import ai_call
                text = ai_call.complete(TIER_DRAFT, SYSTEM_PROMPT,
                                        _user_prompt(question, answer, company), key,
                                        max_tokens=8000, effort="low", timeout=60.0)
                return _parse(text), "ai"
            except Exception as exc:  # noqa: BLE001 — 규칙 기반으로 내려간다
                try:
                    st.session_state[_FAILURE_KEY] = f"{type(exc).__name__}: {exc}"[:300]
                except Exception:
                    pass
    return rule_feedback(question, answer, company), "rule"


def fingerprint(question: str, answer: str, company: dict | None) -> str:
    blob = json.dumps({"q": question, "a": (answer or "").strip(),
                       "c": (company or {}).get("id", "")}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def feedback(question: str, answer: str, company: dict | None,
             use_api: bool | None = None) -> tuple[dict, str]:
    """반환: (피드백 {good, improve, links, rewrite, raw}, "ai" | "rule")."""
    if use_api is None:
        use_api = premium.ai_enabled()
    return _feedback_cached(
        fingerprint(question, answer, company), question, (answer or "").strip(),
        json.dumps(company, ensure_ascii=False, sort_keys=True, default=str) if company else "",
        bool(use_api),
    )
