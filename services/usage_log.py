# -*- coding: utf-8 -*-
"""
services/usage_log.py
사용 기록 — 2차 심사·운영에서 '실제로 몇 명이 어떻게 썼는가'를 답하기 위한 기록

▣ 남기는 것 (이것뿐이다)
   visitors : 사용자별 최초 접속 시각 · 마지막 접속 시각 · 접속한 날짜 목록
   events   : 화면 이동 {사용자, 화면, 시각} · 스토리 반응 {사용자, 기업 ID, 관심/패스, 시각}

▣ 남기지 않는 것
   이름 · 학교 · 반 · 이메일 · 입력한 스펙 · 자소서 내용.
   사용자도 user_id 를 그대로 쓰지 않고 한 방향 해시(sha256 앞 16자)로 바꿔 쓴다.
   게스트의 user_id 에는 이어하기 코드가 그대로 들어 있어서(guest_XXXXXX),
   원본을 로그에 남기면 로그를 볼 수 있는 사람이 남의 계정으로 들어갈 수 있다.
   해시로도 '같은 사람인지'는 구분되므로 사용자 수·재방문 계산에는 지장이 없다.

▣ 테스트 기록 표시 (is_test)
   아래 중 하나면 is_test = True 로 남기고, 통계 화면은 기본적으로 뺀다.
     · 운영 설정 APP_ENV 가 "production" 이 아님 (개발 PC · 테스트 서버)
       → 배포 서버의 Secrets 에 APP_ENV = "production" 을 넣어야 실제 기록이 된다
     · 관리자(ADMIN_USER_IDS) · 데모(DEMO_USER_IDS) · 테스트(TEST_USER_IDS) 계정

▣ 저장 위치
   services/storage_backend.py 의 "usage" 문서 — secrets 에 Supabase 가 있으면
   Supabase(app_state 테이블의 usage 행), 없으면 data/userdata/usage.json.
   기록 실패가 화면을 멈추게 하지 않는다(모든 함수가 예외를 삼킨다).

▣ 쓰기 횟수
   접속일은 세션당 하루 한 번, 화면 이동은 화면이 바뀔 때만 쓴다.
   같은 화면에서 슬라이더를 움직여도(rerun) 기록이 늘지 않는다.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone

import streamlit as st

from core import session as ss
from services import access, storage_backend

DOC = "usage"
MAX_EVENTS = 20000          # 문서가 무한히 커지지 않게 오래된 이벤트부터 버린다

# 화면 키 → 통계에 보여줄 이름
PAGE_LABELS = {
    ss.PAGE_LANDING: "랜딩", ss.PAGE_LOGIN: "로그인", ss.PAGE_ROLE: "역할 선택",
    ss.PAGE_HUB: "허브", ss.PAGE_MYPAGE: "마이페이지",
    ss.PAGE_CLASS_SETUP: "반 개설", ss.PAGE_CLASS_JOIN: "반 등록", ss.PAGE_CLASS_BOARD: "우리 반",
    ss.PAGE_SPEC: "스펙 진단", ss.PAGE_EXPLORE: "기업 탐색", ss.PAGE_GUIDE: "가이드",
    ss.PAGE_RESUME: "자소서", ss.PAGE_NEXT: "로드맵",
    ss.PAGE_ADMIN_DATA: "기업 데이터 입력", ss.PAGE_ADMIN_STATS: "사용 통계",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _empty() -> dict:
    return {"_meta": {"schema": 1}, "visitors": {}, "events": []}


def _secret(name: str, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def anon_id(user_id: str) -> str:
    """user_id → 한 방향 해시. 같은 사람은 같은 값, 원래 ID 로는 되돌릴 수 없다."""
    salt = str(_secret("LOG_SALT", "") or "")
    return hashlib.sha256(f"{salt}:{user_id}".encode("utf-8")).hexdigest()[:16]


def is_production() -> bool:
    env = str(_secret("APP_ENV", "") or os.environ.get("APP_ENV", "")).strip().lower()
    return env == "production"


def is_test_user(user_id: str) -> bool:
    if not is_production():
        return True
    team = (access.admin_user_ids() | access.id_list("DEMO_USER_IDS")
            | access.id_list("TEST_USER_IDS"))
    return user_id in team


def _read() -> dict:
    doc = storage_backend.get_backend(DOC).read(_empty)
    if not isinstance(doc, dict):
        return _empty()
    doc.setdefault("visitors", {})
    doc.setdefault("events", [])
    return doc


def _write(doc: dict) -> None:
    events = doc.get("events") or []
    if len(events) > MAX_EVENTS:
        doc["events"] = events[-MAX_EVENTS:]
    storage_backend.get_backend(DOC).write(doc)


def _event(uid: str, kind: str, **fields) -> dict:
    return {"id": uuid.uuid4().hex[:12], "uid": anon_id(uid), "type": kind,
            "at": _now(), "is_test": is_test_user(uid), **fields}


# ------------------------------------------------------------
# 기록 (app.py · services/reactions.py 가 부른다)
# ------------------------------------------------------------
def track(page: str) -> None:
    """
    매 rerun 마다 불러도 된다. 실제 쓰기는
      · 이 세션에서 오늘 처음일 때 (접속일 갱신)
      · 화면이 바뀌었을 때 (화면 이동 기록)
    에만 한다.
    """
    uid = ss.user_id()
    if not uid:
        return
    try:
        today = _today()
        need_visit = st.session_state.get("_usage_visit") != (uid, today)
        need_page = st.session_state.get("_usage_page") != (uid, page)
        if not (need_visit or need_page):
            return

        doc = _read()
        if need_visit:
            key = anon_id(uid)
            v = doc["visitors"].get(key) or {"first_seen": _now(), "days": []}
            v["last_seen"] = _now()
            if today not in v["days"]:
                v["days"].append(today)
            v["is_test"] = bool(v.get("is_test")) or is_test_user(uid)
            doc["visitors"][key] = v
        if need_page:
            doc["events"].append(_event(uid, "page", page=page))
        _write(doc)

        st.session_state["_usage_visit"] = (uid, today)
        st.session_state["_usage_page"] = (uid, page)
    except Exception:
        pass


def log_reaction(company_id: str, reaction: str) -> None:
    uid = ss.user_id()
    if not uid:
        return
    try:
        doc = _read()
        doc["events"].append(_event(uid, "reaction", company_id=company_id, reaction=reaction))
        _write(doc)
    except Exception:
        pass


# ------------------------------------------------------------
# 통계 (views/admin_stats.py)
# ------------------------------------------------------------
def load() -> dict:
    try:
        return _read()
    except Exception:
        return _empty()


def summarize(doc: dict, include_test: bool = False) -> dict:
    """화면에 보여줄 숫자를 계산한다. include_test=False 면 테스트 기록을 뺀다."""
    def keep(record: dict) -> bool:
        return include_test or not record.get("is_test")

    visitors = {k: v for k, v in (doc.get("visitors") or {}).items() if keep(v)}
    events = [e for e in (doc.get("events") or []) if keep(e)]

    users = len(visitors)
    returning = sum(1 for v in visitors.values() if len(v.get("days") or []) >= 2)

    by_day: dict[str, int] = {}
    for v in visitors.values():
        for day in v.get("days") or []:
            by_day[day] = by_day.get(day, 0) + 1

    by_page: dict[str, int] = {}
    for e in events:
        if e.get("type") == "page":
            label = PAGE_LABELS.get(e.get("page"), e.get("page") or "?")
            by_page[label] = by_page.get(label, 0) + 1

    # 같은 학생이 같은 기업에 반응을 바꾸면 마지막 반응만 센다
    latest: dict[tuple, str] = {}
    for e in sorted((e for e in events if e.get("type") == "reaction"),
                    key=lambda e: e.get("at", "")):
        latest[(e.get("uid"), e.get("company_id"))] = e.get("reaction")
    likes = sum(1 for r in latest.values() if r == "like")
    passes = sum(1 for r in latest.values() if r == "pass")

    return {
        "users": users,
        "returning": returning,
        "returning_rate": (returning / users) if users else None,
        "by_day": dict(sorted(by_day.items())),
        "by_page": dict(sorted(by_page.items(), key=lambda kv: -kv[1])),
        "likes": likes,
        "passes": passes,
        "like_rate": (likes / (likes + passes)) if (likes + passes) else None,
        "test_visitors": sum(1 for v in (doc.get("visitors") or {}).values() if v.get("is_test")),
        "events_total": len(doc.get("events") or []),
    }
