# -*- coding: utf-8 -*-
"""
services/llm.py
[W3 요구사항 #3] st.cache_data 기반 자소서 생성 비용 차단막 + API 키 보안

비용 방어 3단 구조
------------------
 1단 (캐싱)  : 동일한 입력값(이름·직무·기업·스토리·강점·자격증)으로 다시 요청하면
               API를 재호출하지 않고 캐시된 결과를 즉시 반환한다.
               시연 중 "생성" 버튼을 여러 번 눌러도 과금은 최초 1회뿐이다.
 2단 (키 부재): st.secrets 에 CLAUDE_API_KEY 가 없으면 아예 네트워크로 나가지 않고
               규칙 기반 템플릿 생성기로 동작한다. (호출 0회)
 3단 (실패)  : 호출이 실패하면 예외를 삼키고 템플릿 결과로 자동 전환한다.

보안 원칙
---------
API 키는 코드에 절대 하드코딩하지 않는다. 항상 st.secrets["CLAUDE_API_KEY"]
(배포 시 Streamlit Cloud > App settings > Secrets)에서만 읽는다.
캐시 키에도 API 키를 넣지 않아 키가 캐시 저장소에 남지 않도록 했다.
"""

import hashlib
import json

import streamlit as st

from services.coverletter import _template_cover_letter, _claude_cover_letter

# secrets에서 찾을 키 이름 (첫 번째가 표준, 나머지는 하위 호환)
SECRET_KEY_NAMES = ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY")

# 캐시 유지 시간 (초). 1시간 동안 동일 입력은 무조건 캐시 응답.
CACHE_TTL = 3600
CACHE_MAX_ENTRIES = 64


def get_api_key() -> str:
    """
    st.secrets 에서 Claude API 키를 읽는다.
    secrets.toml 이 아예 없는 로컬 환경에서도 예외 없이 빈 문자열을 반환한다.
    """
    for name in SECRET_KEY_NAMES:
        try:
            value = st.secrets.get(name, "")
        except Exception:
            value = ""
        if value:
            return str(value).strip()
    return ""


def has_api_key() -> bool:
    return bool(get_api_key())


def _profile_fingerprint(profile: dict, company_id: str) -> str:
    """캐시 키로 쓸 입력값 지문. 값이 하나라도 바뀌면 새로 생성된다."""
    payload = {
        "name": profile.get("name", ""),
        "target_dept": profile.get("target_dept", ""),
        "grade": profile.get("grade"),
        "story": (profile.get("story") or "").strip(),
        "strength": profile.get("strength", ""),
        "certs": sorted(profile.get("certs") or []),
        "company": company_id,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@st.cache_data(ttl=CACHE_TTL, max_entries=CACHE_MAX_ENTRIES, show_spinner=False)
def _generate_cached(fingerprint: str, profile_json: str, company_json: str,
                     use_api: bool) -> tuple[str, str]:
    """
    실제 생성 함수. @st.cache_data 가 걸려 있어 동일 인자로는 재실행되지 않는다.

    · fingerprint  : 입력값 해시 (캐시 무효화 트리거)
    · profile_json : 직렬화된 학생 프로필 (dict는 해시 불가라 문자열로 전달)
    · company_json : 직렬화된 목표 기업
    · use_api      : 키 보유 여부. 키를 캐시 인자로 넘기지 않기 위한 불리언 플래그.

    반환값: (자소서 본문, "ai" | "template")
    """
    profile = json.loads(profile_json)
    company = json.loads(company_json) if company_json else None

    if use_api:
        api_key = get_api_key()
        if api_key:
            try:
                return _claude_cover_letter(profile, company, api_key), "ai"
            except Exception:
                # 네트워크 오류·인증 실패·응답 구조 변경 → 조용히 템플릿으로 전환
                pass

    return _template_cover_letter(profile, company), "template"


def generate_cover_letter_cached(profile: dict, company: dict | None = None):
    """
    앱에서 호출하는 공개 함수.
    반환값: (본문, 생성 방식 "ai" | "template", 캐시 적중 여부 bool)
    """
    company_id = (company or {}).get("id", "")
    fingerprint = _profile_fingerprint(profile, company_id)

    # 캐시 적중 여부 판단용 로컬 기록 (세션 단위)
    seen = st.session_state.setdefault("_llm_fingerprints", set())
    cache_hit = fingerprint in seen

    text, source = _generate_cached(
        fingerprint,
        json.dumps(profile, ensure_ascii=False, sort_keys=True, default=str),
        json.dumps(company, ensure_ascii=False, sort_keys=True, default=str) if company else "",
        has_api_key(),
    )
    seen.add(fingerprint)
    return text, source, cache_hit


def clear_cover_letter_cache():
    """사용자가 '새로 생성'을 원할 때만 캐시를 비운다 (= 의도적 과금 승인)."""
    _generate_cached.clear()
    st.session_state["_llm_fingerprints"] = set()


def cost_guard_caption() -> str:
    """화면에 노출할 비용 방어 상태 안내 문구."""
    if has_api_key():
        return (
            "🔐 API 키는 st.secrets에서만 읽습니다(코드 내 하드코딩 없음). "
            "동일한 입력값으로 다시 누르면 캐시된 결과가 나오며 API는 재호출되지 않습니다."
        )
    return (
        "🧩 CLAUDE_API_KEY가 설정되지 않아 규칙 기반 템플릿 생성기로 동작합니다. "
        "외부 API 호출이 0회이므로 과금이 발생하지 않습니다."
    )
