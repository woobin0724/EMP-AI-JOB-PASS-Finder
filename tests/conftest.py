# -*- coding: utf-8 -*-
"""pytest 공통 설정 — 저장소 루트를 import 경로에 넣는다."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
