# -*- coding: utf-8 -*-
"""
services/storage_backend.py
저장소 백엔드 — 로컬 JSON / Supabase(Postgres) 교체 지점

▣ 왜 필요한가
   Streamlit Community Cloud 의 파일시스템은 재배포·슬립 해제 시 초기화된다.
   진단 점수·찜한 기업·로드맵 스탬프가 어느 날 그냥 사라진다는 뜻이다.
   재방문해야 값이 생기는 서비스인데 재방문할 이유가 증발하는 구조라,
   외부 저장소가 붙어야 실사용이 성립한다.

▣ 설계
   services/store.py 는 문서 하나(dict)를 통째로 읽고 쓴다. 그 계약을 그대로
   두고 '어디에 쓰는가'만 바꿀 수 있게 백엔드로 분리했다. 스키마를 갈아엎지
   않으므로 기존 코드는 한 줄도 바뀌지 않는다.

   secrets 에 SUPABASE_URL·SUPABASE_KEY 가 있으면 Supabase 를, 없으면 로컬
   JSON 을 쓴다. Supabase 가 응답하지 않으면 로컬로 내려가되 사유를 남긴다 —
   이 저장소의 다른 외부 연동(fallback.py)과 같은 태도다.

▣ 동시성
   로컬 JSON 은 마지막 쓰기가 이긴다(last-write-wins). 100명이 동시에 쓰면
   한 명의 저장이 다른 사람 것을 덮어쓴다. Supabase 백엔드는 version 컬럼으로
   낙관적 잠금을 건다 — 읽은 version 과 같을 때만 쓰고, 어긋나면 최신 문서를
   다시 읽어 그 위에 내 변경만 얹어 재시도한다. 두 학생이 동시에 저장해도
   한쪽 기록이 사라지지 않는다.

▣ 의존성
   supabase-py 를 쓰지 않고 REST 를 requests 로 직접 호출한다. requests 는
   이미 배포 의존성이라 새로 추가되는 패키지가 없다.
"""

import json
import os
import tempfile
import threading
import time
from datetime import datetime, timezone

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_DIR = os.path.join(BASE_DIR, "data", "userdata")
STORE_PATH = os.path.join(STORE_DIR, "store.json")

# Supabase 에 만들 테이블 (docs/STORAGE.md 에 생성 SQL 이 있다)
TABLE = "app_state"
ROW_KEY = "main"

REQUEST_TIMEOUT = 8.0
MAX_RETRIES = 3          # 낙관적 잠금 충돌 시 재시도 횟수

_LOCK = threading.Lock()

# 마지막 실패 사유. 화면에서 '왜 로컬로 내려갔는지' 보여주는 데 쓴다.
_last_error = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def last_error() -> str:
    return _last_error


# 문서 최상위의 '레코드 모음' 키들. 이 안은 id → 레코드 구조라 키 단위로 합칠 수 있다.
_COLLECTIONS = ("users", "classes")


def _merge(fresh: dict, mine: dict) -> dict:
    """
    충돌했을 때 최신 문서(fresh) 위에 내 변경(mine)을 얹는다.

    users·classes 는 id → 레코드 구조라 키 단위로 합칠 수 있다. 내가 건드린
    레코드는 내 것이 이기고, 내가 모르는 사이 남이 추가한 레코드는 그대로 남는다.

    한계: 내가 '삭제'한 레코드는 되살아난다. 삭제인지 애초에 몰랐던 것인지
    문서만 봐서는 구분할 수 없기 때문이다. 이 앱의 쓰기는 거의 전부 추가·수정이라
    이 쪽이 안전한 선택이다.
    """
    merged = dict(fresh)
    for key in _COLLECTIONS:
        base = dict(fresh.get(key) or {})
        base.update(mine.get(key) or {})
        merged[key] = base
    for key, value in mine.items():
        if key not in _COLLECTIONS and key != "_meta":
            merged[key] = value
    merged["_meta"] = mine.get("_meta", fresh.get("_meta", {}))
    return merged


def _secret(name: str) -> str:
    """secrets.toml 이 없는 환경에서도 예외를 내지 않는다."""
    try:
        import streamlit as st
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


# ------------------------------------------------------------
# 로컬 JSON
# ------------------------------------------------------------
class LocalJsonBackend:
    """
    파일 하나에 통째로 쓴다. 임시파일 + os.replace 로 원자적이라, 쓰는 도중
    프로세스가 죽어도 기존 파일이 깨지지 않는다.

    한계는 분명하다 — Streamlit Cloud 에서는 재배포 시 사라지고, 동시 쓰기는
    마지막 것이 이긴다.
    """

    name = "로컬 파일"
    durable = False

    def read(self, empty_doc):
        try:
            with open(STORE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return empty_doc()

    def write(self, doc) -> bool:
        try:
            os.makedirs(STORE_DIR, exist_ok=True)
            with _LOCK:
                fd, tmp = tempfile.mkstemp(dir=STORE_DIR, suffix=".tmp")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(doc, f, ensure_ascii=False, indent=2)
                    os.replace(tmp, STORE_PATH)
                except Exception:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                    raise
            return True
        except Exception:
            # 저장 실패가 앱을 죽이면 안 된다. 세션 메모리로는 계속 동작한다.
            return False


# ------------------------------------------------------------
# Supabase (Postgres REST)
# ------------------------------------------------------------
class SupabaseBackend:
    """
    app_state 테이블에 문서 한 행을 두고 통째로 읽고 쓴다.

    낙관적 잠금: 읽을 때 version 을 같이 받아두고, 쓸 때 'version 이 그대로일
    때만' 갱신한다. 조건이 어긋나면 갱신된 행이 0개로 돌아온다.

    이때 그냥 재시도하면 안 된다 — 내가 들고 있는 문서는 상대가 쓰기 전에
    읽은 것이라, 그대로 다시 쓰면 상대의 저장이 통째로 지워진다. (실제로
    그렇게 구현했다가 테스트에서 다른 사용자 레코드가 사라지는 것을 확인했다.)
    그래서 충돌하면 최신 문서를 다시 읽어, 그 위에 내 변경만 얹어 재시도한다.
    """

    name = "Supabase"
    durable = True

    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + f"/rest/v1/{TABLE}"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self._version = None   # 마지막으로 읽은 버전

    def _get(self):
        res = requests.get(
            self.base,
            params={"key": f"eq.{ROW_KEY}", "select": "doc,version"},
            headers=self.headers, timeout=REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        rows = res.json()
        return rows[0] if rows else None

    def read(self, empty_doc):
        global _last_error
        try:
            row = self._get()
            if row is None:
                self._version = 0
                return empty_doc()
            self._version = int(row.get("version") or 0)
            doc = row.get("doc")
            return doc if isinstance(doc, dict) else empty_doc()
        except Exception as exc:
            _last_error = f"{type(exc).__name__}: {exc}"[:200]
            # 읽기 실패 시 로컬에 남아 있는 것이라도 보여준다
            return LocalJsonBackend().read(empty_doc)

    def write(self, doc) -> bool:
        global _last_error
        for attempt in range(MAX_RETRIES):
            try:
                if self._version is None:
                    row = self._get()
                    self._version = int(row.get("version") or 0) if row else 0

                payload = {"key": ROW_KEY, "doc": doc,
                           "version": self._version + 1, "updated_at": _now()}

                if self._version == 0:
                    # 행이 아직 없다. 있으면 무시되므로 곧바로 재시도로 넘어간다.
                    res = requests.post(
                        self.base, headers={**self.headers,
                                            "Prefer": "return=representation,resolution=ignore-duplicates"},
                        json=payload, timeout=REQUEST_TIMEOUT,
                    )
                else:
                    res = requests.patch(
                        self.base,
                        params={"key": f"eq.{ROW_KEY}",
                                "version": f"eq.{self._version}"},
                        headers={**self.headers, "Prefer": "return=representation"},
                        json=payload, timeout=REQUEST_TIMEOUT,
                    )
                res.raise_for_status()
                changed = res.json()

                if changed:
                    self._version = int(changed[0].get("version") or self._version + 1)
                    # 로컬에도 같은 내용을 남겨둔다 — 다음에 Supabase 가
                    # 응답하지 않아도 마지막 상태를 보여줄 수 있다.
                    LocalJsonBackend().write(doc)
                    return True

                # 갱신된 행이 0개 = 그 사이 다른 사람이 썼다.
                # 최신 문서를 읽어 그 위에 내 변경을 얹고 재시도한다.
                fresh_row = self._get()
                if fresh_row:
                    self._version = int(fresh_row.get("version") or 0)
                    fresh = fresh_row.get("doc")
                    if isinstance(fresh, dict):
                        doc = _merge(fresh, doc)
                else:
                    self._version = 0
                time.sleep(0.15 * (attempt + 1))
            except Exception as exc:
                _last_error = f"{type(exc).__name__}: {exc}"[:200]
                break

        # 외부 저장에 실패했어도 로컬에는 남긴다. 세션은 계속 살아 있어야 한다.
        return LocalJsonBackend().write(doc)


# ------------------------------------------------------------
# 선택
# ------------------------------------------------------------
_backend = None


def get_backend():
    """secrets 설정에 따라 백엔드를 고른다. 한 번 고르면 재사용한다."""
    global _backend
    if _backend is None:
        url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
        _backend = SupabaseBackend(url, key) if (url and key) else LocalJsonBackend()
    return _backend


def reset_backend() -> None:
    """테스트용 — 백엔드 선택을 다시 하게 한다."""
    global _backend, _last_error
    _backend, _last_error = None, ""


def status() -> dict:
    """화면에 보여줄 저장소 상태."""
    b = get_backend()
    return {
        "name": b.name,
        "durable": b.durable,
        "error": _last_error,
    }
