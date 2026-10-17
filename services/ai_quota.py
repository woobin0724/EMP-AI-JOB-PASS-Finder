# -*- coding: utf-8 -*-
"""
services/ai_quota.py
[big-patch 4단계] 학생 1명당 하루 AI 사용 한도

▣ 무엇을 세나
   실제로 Claude API 를 부른 횟수만 센다. 캐시에서 나온 결과(같은 입력 재요청)와
   규칙 기반 결과는 세지 않는다 — 학생이 같은 버튼을 여러 번 눌러도 한도가 줄지 않는다.

▣ 한도 (st.secrets 로 바꿀 수 있다)
   AI_DAILY_LIMIT          : 자소서 생성 · 첨삭 · 모의 면접 피드백 합계 (기본 10회/일)
   AI_DAILY_LIMIT_EXPLAIN  : 스펙 진단 점수 설명 (기본 10회/일)
       점수 설명은 슬라이더를 움직일 때마다 입력이 바뀌어 호출이 잦을 수 있어 따로 센다.
   한도를 넘으면 그날은 규칙 기반 결과로 내려간다(기능은 계속 쓸 수 있다).

▣ 저장 (개인을 알아볼 수 있는 정보 없음)
   services/usage_log 의 "usage" 문서에 {해시 ID: {날짜: {묶음: 횟수}}} 로 남긴다.
   Supabase 가 있으면 같은 app_state 테이블의 usage 행 — 스키마 변경 없음.
   오늘이 아닌 날짜는 쓸 때 지운다. 저장소를 못 읽으면 이 세션 안의 횟수로 센다.
"""

from datetime import datetime, timezone

import streamlit as st

from core import session as ss
from services import premium, usage_log

BUCKET_WRITE = "write"      # 자소서 생성 · 첨삭 · 모의 면접
BUCKET_EXPLAIN = "explain"  # 점수 설명

DEFAULT_LIMITS = {BUCKET_WRITE: 10, BUCKET_EXPLAIN: 10}
_SECRET_NAMES = {BUCKET_WRITE: "AI_DAILY_LIMIT", BUCKET_EXPLAIN: "AI_DAILY_LIMIT_EXPLAIN"}
_SESSION_KEY = "_ai_quota_session"

# 기능 → 묶음
FEATURE_BUCKET = {
    "coverletter": BUCKET_WRITE, "review": BUCKET_WRITE, "interview": BUCKET_WRITE,
    "explain": BUCKET_EXPLAIN,
}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def limit(bucket: str) -> int:
    try:
        value = st.secrets.get(_SECRET_NAMES[bucket], DEFAULT_LIMITS[bucket])
        return max(0, int(value))
    except Exception:
        return DEFAULT_LIMITS[bucket]


def _session_counts() -> dict:
    try:
        data = st.session_state.setdefault(_SESSION_KEY, {})
    except Exception:
        return {}
    if data.get("day") != _today():
        data.clear()
        data["day"] = _today()
    return data


def used(bucket: str, uid: str | None = None) -> int:
    uid = uid if uid is not None else ss.user_id()
    session_n = int(_session_counts().get(bucket, 0))
    if not uid:
        return session_n
    try:
        doc = usage_log.load()
        stored = int(((doc.get("ai_quota") or {}).get(usage_log.anon_id(uid)) or {})
                     .get(_today(), {}).get(bucket, 0))
    except Exception:
        stored = 0
    return max(stored, session_n)


def remaining(bucket: str, uid: str | None = None) -> int:
    return max(0, limit(bucket) - used(bucket, uid))


def can_use(feature: str) -> bool:
    """AI 를 불러도 되는가 = 프리미엄·키 조건 + 오늘 한도가 남음."""
    if not premium.ai_enabled():
        return False
    return remaining(FEATURE_BUCKET.get(feature, BUCKET_WRITE)) > 0


def consume(feature: str) -> None:
    """실제 API 호출 직전에 부른다. 기록 실패는 화면을 멈추지 않는다."""
    bucket = FEATURE_BUCKET.get(feature, BUCKET_WRITE)
    counts = _session_counts()
    counts[bucket] = int(counts.get(bucket, 0)) + 1
    uid = ss.user_id()
    if not uid:
        return
    try:
        usage_log.record_ai_call(uid, bucket, feature, _today())
    except Exception:
        pass


def status_line(feature: str) -> str:
    """화면 안내 — '오늘 AI 7회 남음 (하루 10회)'."""
    bucket = FEATURE_BUCKET.get(feature, BUCKET_WRITE)
    left, total = remaining(bucket), limit(bucket)
    if left <= 0:
        return f"오늘 AI 사용 한도({total}회)를 다 썼어요. 내일 다시 쓸 수 있고, 지금은 무료 점검으로 이어서 쓸 수 있어요"
    return f"오늘 AI {left}회 남음 (하루 {total}회 · 같은 입력 재요청은 횟수에 들어가지 않아요)"
