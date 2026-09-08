# -*- coding: utf-8 -*-
"""
services/fallback.py
[W3 요구사항 #2] 외부 API 예외처리 + 데이터 이중화(Fallback) 단일 관문

설계 의도
---------
심사 시연 도중 Q-Net·고용24 API가 죽거나 학교 네트워크가 느려지는 순간
화면이 하얗게 비는 것이 이 프로젝트의 가장 큰 리스크였다. 그래서 외부에
나가는 모든 호출을 이 모듈 하나로 통과시키고, 다음 규칙을 강제한다.

  1) 모든 외부 호출은 `safe_call()` 안에서 실행된다. 어떤 예외(타임아웃,
     DNS 실패, 인증 실패, 응답 구조 변경, JSON 파싱 오류)가 나도 위로 전파되지
     않는다. 즉 앱은 절대 죽지 않는다.
  2) 실패하면 즉시 `data/backup_master.json`(기계·전기·제조 계열 가상 마스터
     백업 데이터)으로 부드럽게 전환한다. JSON 파일이 없거나 깨져 있으면
     파이썬 모듈(data/companies.py)의 원본 데이터로 한 번 더 내려간다.
  3) 매 호출의 출처("live" / "backup")와 실패 사유를 SourceTracker에 기록해,
     화면 상단 [LIVE API] / [BACKUP DATA] 배지로 실시간 표출한다.
"""

import json
import os
import time

import pandas as pd

# ------------------------------------------------------------
# 백업 데이터 로딩
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_JSON_PATH = os.path.join(BASE_DIR, "data", "backup_master.json")

# 상태 상수
LIVE = "live"
BACKUP = "backup"


def load_backup_master() -> dict:
    """
    가상 마스터 백업 JSON을 읽어온다.
    파일이 없거나 손상된 경우에도 예외를 던지지 않고 파이썬 모듈 데이터로 복구한다.
    """
    try:
        with open(BACKUP_JSON_PATH, "r", encoding="utf-8") as f:
            doc = json.load(f)
        if not doc.get("jobs"):
            raise ValueError("백업 JSON에 채용공고 데이터가 없음")
        return doc
    except Exception:
        # 2차 방어선: 파이썬 모듈 원본에서 직접 조립
        from data.companies import MOCK_JOBS, BACKUP_STRONG_SME
        from data.certifications import CERTIFICATIONS, CERT_CODE_TO_NAME

        jobs = []
        for job in MOCK_JOBS:
            row = dict(job)
            row["required_certs"] = [
                CERT_CODE_TO_NAME.get(c, c) for c in job.get("required_cert_codes", [])
            ]
            row.setdefault("ai_tip", "")
            jobs.append(row)

        return {
            "_meta": {"notice": "JSON 백업 파일을 읽지 못해 내장 모듈 데이터로 복구했습니다."},
            "jobs": jobs,
            "certifications": CERTIFICATIONS,
            "strong_sme": BACKUP_STRONG_SME,
        }


BACKUP_MASTER = load_backup_master()


def backup_jobs() -> list:
    return [dict(j) for j in BACKUP_MASTER.get("jobs", [])]


def backup_certifications() -> list:
    return [dict(c) for c in BACKUP_MASTER.get("certifications", [])]


def backup_strong_sme() -> list:
    return [dict(c) for c in BACKUP_MASTER.get("strong_sme", [])]


def backup_summary() -> str:
    meta = BACKUP_MASTER.get("_meta", {})
    return (
        f"채용공고 {len(BACKUP_MASTER.get('jobs', []))}건 · "
        f"자격증 {len(BACKUP_MASTER.get('certifications', []))}종 · "
        f"강소기업 {len(BACKUP_MASTER.get('strong_sme', []))}건"
        + (f" | {meta['notice']}" if meta.get("notice") else "")
    )


# ------------------------------------------------------------
# 안전 호출 래퍼
# ------------------------------------------------------------
class SourceTracker:
    """
    각 데이터 소스의 출처(live/backup)·응답시간·실패 사유를 모아두는 기록기.
    Streamlit 세션에 하나만 두고 화면 상단 배지에 그대로 사용한다.
    """

    def __init__(self):
        self.entries = {}

    def record(self, name: str, source: str, elapsed_ms: int = 0, error: str = ""):
        self.entries[name] = {
            "source": source, "elapsed_ms": elapsed_ms, "error": error,
        }

    def get(self, name: str) -> dict:
        return self.entries.get(name, {"source": BACKUP, "elapsed_ms": 0, "error": ""})

    def is_live(self, name: str) -> bool:
        return self.get(name)["source"] == LIVE

    def any_live(self) -> bool:
        return any(e["source"] == LIVE for e in self.entries.values())

    def all_live(self) -> bool:
        return bool(self.entries) and all(e["source"] == LIVE for e in self.entries.values())

    def errors(self) -> list:
        return [(n, e["error"]) for n, e in self.entries.items() if e["error"]]


def safe_call(fn, *args, fallback=None, tracker: SourceTracker | None = None,
              name: str = "", **kwargs):
    """
    외부 호출 공통 래퍼.
    - fn 이 (data, source) 튜플을 반환하면 그대로 사용한다.
    - 그 외 값을 반환하면 "live" 로 간주한다.
    - 어떤 예외가 나도 삼키고 fallback 값 + "backup" 을 반환한다.
    반환값: (데이터, "live"|"backup")
    """
    started = time.perf_counter()
    label = name or getattr(fn, "__name__", "external_api")
    try:
        result = fn(*args, **kwargs)
        if isinstance(result, tuple) and len(result) == 2 and result[1] in (LIVE, BACKUP):
            data, source = result
        else:
            data, source = result, LIVE

        # 빈 응답도 장애로 간주하지 않고 그대로 전달하되, None 이면 백업 처리
        if data is None:
            raise ValueError(f"{label} 응답이 비어 있음")

        elapsed = int((time.perf_counter() - started) * 1000)
        if tracker:
            tracker.record(label, source, elapsed)
        return data, source

    except Exception as exc:  # noqa: BLE001 — 모든 장애를 여기서 흡수한다
        elapsed = int((time.perf_counter() - started) * 1000)
        if tracker:
            tracker.record(label, BACKUP, elapsed, f"{type(exc).__name__}: {exc}")
        return fallback, BACKUP


# ------------------------------------------------------------
# 각 데이터 소스별 안전 조회 함수
# ------------------------------------------------------------
def fetch_certifications_safe(api_key: str | None, tracker: SourceTracker | None = None):
    """Q-Net(공공데이터포털) 자격증 마스터 조회. 실패 시 백업 자격증 데이터."""
    from services.qnet_api import fetch_certifications_from_api

    df, source = safe_call(
        fetch_certifications_from_api, api_key,
        fallback=pd.DataFrame(backup_certifications()),
        tracker=tracker, name="Q-Net 자격증",
    )
    if df is None or (hasattr(df, "empty") and df.empty):
        df, source = pd.DataFrame(backup_certifications()), BACKUP
        if tracker:
            tracker.record("Q-Net 자격증", BACKUP, 0, "응답 데이터가 비어 있어 백업으로 전환")
    return df, source


def fetch_jobs_safe(api_key: str | None, keyword: str = "",
                    tracker: SourceTracker | None = None):
    """고용24(워크넷) 채용공고 조회. 실패 시 가상 마스터 백업 공고."""
    from services.worknet_api import fetch_jobs_from_api
    from core.matching import filter_results

    df, source = safe_call(
        fetch_jobs_from_api, api_key, keyword,
        fallback=pd.DataFrame(filter_results(backup_jobs(), keyword)),
        tracker=tracker, name="고용24 채용공고",
    )
    if df is None:
        df, source = pd.DataFrame(filter_results(backup_jobs(), keyword)), BACKUP
    return df, source


def fetch_alio_safe(tracker: SourceTracker | None = None):
    """잡알리오 공기업 공고 조회. 실패 시 빈 리스트(다른 소스로 화면은 유지)."""
    from services.alio_api import fetch_alio_jobs

    records, source = safe_call(
        fetch_alio_jobs, fallback=[], tracker=tracker, name="잡알리오 공기업",
    )
    return (records or []), source


def fetch_strong_sme_safe(tracker: SourceTracker | None = None):
    """'참 괜찮은 강소기업' 포털 조회. 실패 시 백업 강소기업 데이터."""
    from services.strong_sme_api import fetch_strong_small_companies

    records, source = safe_call(
        fetch_strong_small_companies, fallback=backup_strong_sme(),
        tracker=tracker, name="강소기업 포털",
    )
    return (records or backup_strong_sme()), source


# ------------------------------------------------------------
# 화면 배지 렌더링
# ------------------------------------------------------------
BADGE_CSS_ID = "mjp-source-badge"


def badge_html(tracker: SourceTracker, colors: dict | None = None) -> str:
    """
    화면 상단에 붙일 [LIVE API] / [BACKUP DATA] 컬러 배지 HTML을 만든다.
    소스별로 개별 배지를 나열해 어떤 계열이 실시간이고 어떤 계열이 백업인지
    한눈에 보이도록 한다.
    """
    colors = colors or {}
    live_bg = colors.get("live", "#34D399")
    backup_bg = colors.get("backup", "#FBBF24")
    ink = colors.get("ink", "#0A0E17")
    muted = colors.get("muted", "#8A93A6")

    if not tracker.entries:
        return (
            f'<div id="{BADGE_CSS_ID}" style="margin:2px 0 14px;">'
            f'<span style="background:{muted};color:{ink};font-size:11px;font-weight:800;'
            f'padding:4px 10px;border-radius:999px;">STANDBY</span>'
            f'<span style="color:{muted};font-size:11.5px;margin-left:8px;">'
            f'아직 외부 데이터를 호출하지 않았습니다.</span></div>'
        )

    chips = []
    for name, info in tracker.entries.items():
        is_live = info["source"] == LIVE
        bg = live_bg if is_live else backup_bg
        text = "LIVE API" if is_live else "BACKUP DATA"
        ms = f"{info['elapsed_ms']}ms" if info["elapsed_ms"] else ""
        chips.append(
            f'<span style="display:inline-flex;align-items:center;gap:6px;'
            f'background:{bg};color:{ink};font-size:11px;font-weight:800;'
            f'padding:4px 10px;border-radius:999px;margin-right:6px;">'
            f'{"●" if is_live else "◐"} {text}'
            f'<span style="font-weight:600;opacity:.75;">{name}{" · " + ms if ms else ""}</span>'
            f'</span>'
        )

    note = ""
    if not tracker.all_live():
        note = (
            f'<div style="color:{muted};font-size:11.5px;margin-top:6px;">'
            f'일부 소스가 응답하지 않아 준비된 백업 마스터 데이터로 전환했습니다 '
            f'({backup_summary()}). 화면 기능은 100% 그대로 동작합니다.</div>'
        )

    return f'<div id="{BADGE_CSS_ID}" style="margin:2px 0 14px;">{"".join(chips)}{note}</div>'
