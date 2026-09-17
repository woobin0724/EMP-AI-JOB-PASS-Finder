# -*- coding: utf-8 -*-
"""
services/ogq_api.py
[Phase 4] NAVER OGQ마켓 경연 API 클라이언트

▣ API 키를 읽는 곳 (이 순서대로 찾는다)
   1) st.secrets["OGQ_API_KEY"]      ← Streamlit 앱에서 실행할 때 (배포 포함)
      파일: .streamlit/secrets.toml
      형식: OGQ_API_KEY = "여기에_키"

   2) 환경변수 OGQ_API_KEY            ← CLI 스크립트로 내려받을 때
      예: OGQ_API_KEY=xxx python3 scripts/fetch_mascot.py

   3) 프로젝트 루트의 .env 파일       ← 로컬에서 편한 방법
      형식: OGQ_API_KEY=여기에_키      (따옴표 있어도 됨)

   두 경로를 모두 지원하는 이유: 마스코트 다운로드는 Streamlit 밖에서 도는
   CLI 스크립트라 st.secrets 를 쓸 수 없고, 앱 실행 중에는 반대로 .env 가
   배포 환경에 없다. 세 곳을 순서대로 보면 어느 쪽이든 동작한다.
   키는 절대 코드에 하드코딩하지 않는다.

▣ 호출 제한 (스펙 명시)
   조회   분당 60회
   다운로드 발급 분당 10회
   그래서 카탈로그는 디스크에 캐시하고, 앱 실행 중에는 API 를 아예 부르지 않는다.
   마스코트 이미지는 최초 1회 내려받아 assets/mascot/ 에 두고 정적으로 쓴다.
"""

import json
import os
import threading
import time
from collections import deque

import requests

BASE_URL = "https://4th-ai-ogq.competition.ogq.me"
API_KEY_NAME = "OGQ_API_KEY"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
CATALOG_PATH = os.path.join(BASE_DIR, "data", "ogq_catalog.json")
MASCOT_DIR = os.path.join(BASE_DIR, "assets", "mascot")
MANIFEST_PATH = os.path.join(MASCOT_DIR, "manifest.json")

TIMEOUT = 20

# 스펙에 명시된 분당 제한
QUERY_LIMIT_PER_MIN = 60
DOWNLOAD_LIMIT_PER_MIN = 10


# ------------------------------------------------------------
# API 키 로딩
# ------------------------------------------------------------
def _from_streamlit_secrets() -> str:
    """Streamlit 실행 중일 때만 성공한다. CLI 에서는 조용히 빈 문자열."""
    try:
        import streamlit as st
        return str(st.secrets.get(API_KEY_NAME, "") or "").strip()
    except Exception:
        return ""


def _from_dotenv() -> str:
    """의존성 없이 .env 를 직접 파싱한다 (python-dotenv 를 추가하지 않기 위해)."""
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == API_KEY_NAME:
                    return value.strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def load_api_key() -> str:
    """st.secrets → 환경변수 → .env 순서로 찾는다. 없으면 빈 문자열."""
    return (_from_streamlit_secrets()
            or os.environ.get(API_KEY_NAME, "").strip()
            or _from_dotenv())


def has_api_key() -> bool:
    return bool(load_api_key())


def key_source() -> str:
    """키를 어디서 읽었는지 알려준다 (설정 안내 화면용)."""
    if _from_streamlit_secrets():
        return ".streamlit/secrets.toml"
    if os.environ.get(API_KEY_NAME, "").strip():
        return "환경변수"
    if _from_dotenv():
        return ".env"
    return ""


# ------------------------------------------------------------
# 호출 제한기
# ------------------------------------------------------------
class _RateLimiter:
    """분당 N회 제한을 지킨다. 초과하면 가장 오래된 호출이 만료될 때까지 잠깐 기다린다."""

    def __init__(self, limit_per_min: int):
        self.limit = limit_per_min
        self.calls = deque()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        with self.lock:
            now = time.monotonic()
            while self.calls and now - self.calls[0] > 60:
                self.calls.popleft()
            if len(self.calls) >= self.limit:
                wait = 60 - (now - self.calls[0]) + 0.1
                time.sleep(max(0.0, wait))
                now = time.monotonic()
                while self.calls and now - self.calls[0] > 60:
                    self.calls.popleft()
            self.calls.append(time.monotonic())


_query_limiter = _RateLimiter(QUERY_LIMIT_PER_MIN)
_download_limiter = _RateLimiter(DOWNLOAD_LIMIT_PER_MIN)


class OGQError(RuntimeError):
    pass


def _headers(api_key: str | None = None) -> dict:
    key = api_key or load_api_key()
    if not key:
        raise OGQError(
            f"{API_KEY_NAME} 를 찾지 못했습니다. "
            f".streamlit/secrets.toml 또는 .env 에 넣거나 환경변수로 지정하세요."
        )
    return {"X-OGQ-API-KEY": key, "Accept": "application/json"}


def _get(path: str, params: dict | None = None, api_key: str | None = None,
         limiter: _RateLimiter | None = None) -> dict:
    (limiter or _query_limiter).acquire()
    url = f"{BASE_URL}{path}"
    try:
        res = requests.get(url, headers=_headers(api_key), params=params, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise OGQError(f"{url} 호출 실패: {type(exc).__name__}: {exc}") from exc

    if not res.ok:
        # 스펙상 모든 오류는 {"code": ..., "message": ...} 형태다
        try:
            payload = res.json()
            code = payload.get("code", "UNKNOWN")
            message = payload.get("message", "")
        except ValueError:
            code, message = "UNKNOWN", res.text[:200]

        hint = {
            "UNAUTHORIZED": "API 키를 확인하세요.",
            "RATE_LIMIT_EXCEEDED": "호출 한도 초과입니다. 1분 뒤 다시 시도하세요.",
            "CATALOG_NOT_READY": "서버가 자산 목록을 준비 중입니다. 잠시 후 재시도하세요.",
            "DOWNLOAD_TOKEN_EXPIRED": "다운로드 토큰이 만료되었습니다(약 5분). 발급부터 다시 하세요.",
            "ASSET_NOT_FOUND": "노출 대상이 아니거나 없는 자산입니다.",
            "INVALID_REQUEST": "파라미터를 확인하세요 (pageSize 최대 100 등).",
        }.get(code, "")
        raise OGQError(f"[{res.status_code}] {code}: {message} {hint}".strip())

    try:
        return res.json()
    except ValueError as exc:
        raise OGQError(f"{url} 응답이 JSON 이 아닙니다") from exc


# ------------------------------------------------------------
# 엔드포인트
# ------------------------------------------------------------
def fetch_openapi() -> dict:
    """정본 스펙. 인증 불필요 — 필드명 재확인용."""
    res = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT)
    res.raise_for_status()
    return res.json()


def list_assets(query: str | None = None, asset_type: str | None = None,
                category_id=None, is_animated: bool | None = None,
                page: int = 0, page_size: int = 40,
                ordering: str | None = None, api_key: str | None = None) -> dict:
    """
    GET /v1/assets — 검색/목록.

    반환: {page, pageSize, total, hasNext, elements: [Asset, ...]}
    · page 는 **0부터** 시작한다 (스펙 기본값 0)
    · pageSize 기본 40, 최대 100 (101 이면 400 INVALID_REQUEST)
    · type 은 쉼표 구분 다중 지정 가능 (STICKER, STOCK_IMAGE, AUDIO, ...)
    """
    params = {"page": int(page), "pageSize": min(int(page_size), 100)}
    if query:
        params["query"] = query
    if asset_type:
        params["type"] = asset_type
    if category_id is not None:
        params["categoryId"] = category_id
    if is_animated is not None:
        params["isAnimated"] = str(bool(is_animated)).lower()
    if ordering:
        params["ordering"] = ordering
    return _get("/v1/assets", params, api_key)


def get_asset(asset_id, api_key: str | None = None) -> dict:
    """GET /v1/assets/{assetId} — 상세. 스티커면 images 배열에 낱장 목록."""
    return _get(f"/v1/assets/{asset_id}", None, api_key)


def issue_download(asset_id, api_key: str | None = None) -> dict:
    """
    GET /v1/assets/{assetId}/download — 다운로드 URL 발급.

    반환: {assetId, type, expiresAt, files: [{fileId, name, format, downloadUrl}, ...]}
    스티커는 **낱장 수만큼 files 가 나온다** (24장이면 24개).
    downloadUrl 은 약 5분 뒤 만료되므로 받는 즉시 저장해야 한다.
    토큰 URL 호출에는 API 키가 필요 없다 (토큰 자체가 자격증명).
    """
    return _get(f"/v1/assets/{asset_id}/download", None, api_key, _download_limiter)


def ping() -> bool:
    """GET /ping → 'pong'. 인증 불필요. 연결 점검용."""
    try:
        res = requests.get(f"{BASE_URL}/ping", timeout=TIMEOUT)
        return res.ok and "pong" in res.text.lower()
    except requests.RequestException:
        return False


def download_to(download_url: str, dest_path: str) -> str:
    """
    발급받은 downloadUrl 을 호출해 실제 파일을 저장한다.
    이 URL 은 302 로 S3 로 리다이렉트되며 API 키가 필요 없다.
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        res = requests.get(download_url, timeout=TIMEOUT, allow_redirects=True)
        res.raise_for_status()
    except requests.RequestException as exc:
        raise OGQError(f"파일 다운로드 실패: {type(exc).__name__}: {exc}") from exc

    with open(dest_path, "wb") as f:
        f.write(res.content)
    return dest_path


# ------------------------------------------------------------
# 카탈로그 캐시
# ------------------------------------------------------------
def fetch_catalog(api_key: str | None = None, force: bool = False) -> list:
    """
    전체 자산 목록을 받아 디스크에 캐시한다.
    스펙상 전체가 38건 규모라 pageSize=100 한 번이면 끝나지만,
    응답에 다음 페이지가 있으면 이어서 받는다.
    """
    if not force and os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("assets", [])
        except Exception:
            pass

    assets, page = [], 0
    while True:
        payload = list_assets(page=page, page_size=100, api_key=api_key)
        items = _extract_items(payload)
        assets.extend(items)
        # 스펙이 hasNext 를 주므로 그것으로 판단한다 (길이 추론보다 정확)
        if not payload.get("hasNext") or not items:
            break
        page += 1
        if page > 10:      # 안전장치 (38건 규모라 실제로는 1페이지면 끝)
            break

    os.makedirs(os.path.dirname(CATALOG_PATH), exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "count": len(assets), "assets": assets},
                  f, ensure_ascii=False, indent=2)
    return assets


def _extract_items(payload) -> list:
    """목록 응답에서 자산 배열을 꺼낸다. 스펙상 키는 `elements` 다."""
    if isinstance(payload, dict):
        return payload.get("elements") or []
    return payload if isinstance(payload, list) else []
