# -*- coding: utf-8 -*-
"""pytest 공통 설정 — 저장소 루트를 import 경로에 넣는다."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest


@pytest.fixture
def usage_tmp(tmp_path, monkeypatch):
    """사용 기록(usage) 문서를 임시 파일로 바꿔 끼운다 — 실제 data/userdata 를 건드리지 않는다."""
    from services import storage_backend
    monkeypatch.setitem(storage_backend.DOCS, "usage", (str(tmp_path / "usage.json"), "usage"))
    storage_backend.reset_backend()
    yield tmp_path
    storage_backend.reset_backend()
