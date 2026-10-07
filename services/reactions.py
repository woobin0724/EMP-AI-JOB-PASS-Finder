# -*- coding: utf-8 -*-
"""
services/reactions.py
기업 스토리 반응(❤️ 관심 / 👎 패스) 기록

  · 화면 상태  : st.session_state["story_reactions"] = {기업ID: "like" | "pass"}
  · 누적 기록  : data/reactions.json — [{student, company_id, reaction, at}, ...]
                 같은 학생이 같은 기업에 반응을 바꾸면 줄이 하나 더 쌓인다
                 (마지막 줄이 현재 상태 — 반응이 바뀐 흐름 자체가 기록이다).

학생 식별값: 로그인 단계의 user_id(게스트 포함). 없으면 Streamlit 세션 ID.
reactions.json 에는 이 식별값이 들어가므로 .gitignore 에 올려 두었다.
"""

import json
import os
import tempfile
import threading
from datetime import datetime

import streamlit as st

from core import session as ss

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REACTIONS_PATH = os.path.join(BASE_DIR, "data", "reactions.json")
_FILE_LOCK = threading.Lock()

LIKE = "like"
PASS = "pass"
_STATE_KEY = "story_reactions"


def student_key() -> str:
    uid = ss.user_id()
    if uid:
        return uid
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        if ctx is not None:
            return f"session_{ctx.session_id}"
    except Exception:
        pass
    return "session_unknown"


def _state() -> dict:
    return st.session_state.setdefault(_STATE_KEY, {})


def _read() -> list:
    try:
        with open(REACTIONS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _append(row: dict) -> None:
    """임시파일 + os.replace 로 원자적으로 쓴다. 실패해도 화면 상태는 유지된다."""
    with _FILE_LOCK:
        rows = _read()
        rows.append(row)
        try:
            os.makedirs(os.path.dirname(REACTIONS_PATH), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(REACTIONS_PATH), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=1)
            os.replace(tmp, REACTIONS_PATH)
        except OSError:
            pass


def _restore() -> None:
    """세션 첫 진입 때 파일에서 이 학생의 마지막 반응을 되살린다 (다시 접속해도 관심 목록 유지)."""
    if st.session_state.get("_story_reactions_loaded"):
        return
    st.session_state["_story_reactions_loaded"] = True
    me = student_key()
    state = _state()
    for row in _read():
        if row.get("student") == me and row.get("company_id"):
            state[row["company_id"]] = row.get("reaction")


def record(company_id: str, reaction: str) -> None:
    """반응을 기록한다. 직전과 같은 반응이면 파일에 다시 쓰지 않는다."""
    _restore()
    state = _state()
    if state.get(company_id) == reaction:
        return
    state[company_id] = reaction
    _append({
        "student": student_key(),
        "company_id": company_id,
        "reaction": reaction,
        "at": datetime.now().isoformat(timespec="seconds"),
    })


def reaction_of(company_id: str) -> str | None:
    _restore()
    return _state().get(company_id)


def liked_ids() -> list[str]:
    """❤️ 누른 기업 ID (누른 순서)."""
    _restore()
    return [cid for cid, r in _state().items() if r == LIKE]
