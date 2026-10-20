# -*- coding: utf-8 -*-
"""[big-patch 1단계] 기업 데이터 신뢰성 — 실제 기업에 지어낸 정보가 붙지 않는지."""
import json
import os

import pytest

from data import company_showcase as cs
from data.companies import BACKUP_PUBLIC_COMPANIES, BACKUP_STRONG_SME, MOCK_JOBS
from services import curated

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 백업·예시 데이터에 다시 들어오면 안 되는 실제 기관·대기업 그룹 이름
REAL_NAMES = ["한국전력공사", "한국수력원자력", "한국가스공사", "한국수자원공사", "한국도로공사",
              "한국철도공사", "코레일", "인천국제공항공사", "한국공항공사", "한국지역난방공사",
              "삼성", "현대", "SK", "LG", "포스코", "한화", "롯데", "대림", "한진", "신한", "우성건설"]


def _all_backup_names():
    master = json.load(open(os.path.join(ROOT, "data", "backup_master.json"), encoding="utf-8"))
    names = [j["company"] for j in master["jobs"] + master["strong_sme"]]
    names += [j["company"] for j in MOCK_JOBS + BACKUP_PUBLIC_COMPANIES + BACKUP_STRONG_SME]
    names += [c["name"] for c in cs.COMPANY_SHOWCASE]
    return names


@pytest.mark.parametrize("real", REAL_NAMES)
def test_no_real_names_in_sample_data(real):
    hits = [n for n in _all_backup_names() if real in n]
    assert not hits, f"예시 데이터에 실제 이름 '{real}' 이 남아 있음: {hits}"


def test_no_unverifiable_tips_in_backups():
    master = json.load(open(os.path.join(ROOT, "data", "backup_master.json"), encoding="utf-8"))
    rows = BACKUP_PUBLIC_COMPANIES + BACKUP_STRONG_SME + master["jobs"] + master["strong_sme"]
    assert all(not (r.get("ai_tip") or "").strip() for r in rows)


def test_alio_backup_is_labeled_backup_not_curated():
    from services.alio_api import fetch_alio_jobs
    rows, source = fetch_alio_jobs()
    assert source == "backup" and len(rows) == len(BACKUP_PUBLIC_COMPANIES)


def test_strong_sme_fictional_is_labeled_backup_not_curated():
    """[심사대응] 가상 강소기업 예시는 '팀이 조사한 데이터(CURATED)'가 아니다."""
    from services.strong_sme_api import SOURCE_LABEL, fetch_strong_small_companies
    rows, source = fetch_strong_small_companies()
    assert source == "backup" and len(rows) == len(BACKUP_STRONG_SME)
    assert "큐레이션" not in SOURCE_LABEL


def test_showcase_is_marked_sample(monkeypatch):
    monkeypatch.setattr(curated, "load", lambda: [])
    assert all(c["data_kind"] == "sample" for c in cs.all_companies())


def test_verified_record_replaces_instead_of_merging(monkeypatch):
    """실제 기업이 같은 id 의 가상 기업 별점·장단점·면접 질문을 물려받지 않는다."""
    real = {"id": "kepco", "name": "실제기관", "size_tag": "공기업", "category": "전자/전기",
            "description": "송배전", "source_url": "https://example.org", "source_type": "공식 홈페이지",
            "checked_by": "팀", "checked_at": "2026-10-01",
            "overall_rating": 4.9, "pros": "지어낸 장점"}          # 예전 형식의 금지 항목
    monkeypatch.setattr(curated, "load", lambda: [real])
    merged = {c["id"]: c for c in cs.all_companies()}["kepco"]
    assert merged["data_kind"] == "verified"
    for key in curated.FORBIDDEN_REAL_FIELDS:
        assert key not in merged, key
    assert merged["ideal_talent"] == [] and merged["required_certs"] == []


def _row(**kw):
    base = {"id": "x1", "name": "기관", "size_tag": "공기업", "category": "기계", "description": "설비",
            "source_url": "https://example.org", "source_type": "공식 홈페이지",
            "checked_by": "팀", "checked_at": "2026-10-01"}
    base.update(kw)
    return base


def test_validate_accepts_minimal_sourced_record():
    assert curated.validate(_row(), []) == []


@pytest.mark.parametrize("kw, needle", [
    ({"source_url": ""}, "출처 URL"),
    ({"checked_at": "2999-01-01"}, "수집일"),
    ({"checked_at": "어제"}, "YYYY-MM-DD"),
    ({"ideal_talent": ["성실"]}, "인재상 출처"),
    ({"talent_summary": "가" * 81, "talent_source_url": "https://e.org"}, "80자"),
    ({"official_recruit_url": "ftp://x"}, "http"),
    ({"overall_rating": 4.5}, "확인할 수 없는"),
    ({"interview_questions": ["Q"]}, "확인할 수 없는"),
])
def test_validate_rejects(kw, needle):
    errors = curated.validate(_row(**kw), [])
    assert any(needle in e for e in errors), errors
