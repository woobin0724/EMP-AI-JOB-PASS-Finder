# -*- coding: utf-8 -*-
"""
core/spec_score.py  (호환 레이어)

W3 리팩토링에서 '취업 등용문 점수' 산출 로직은 core/matching.py 로 일원화되었다.
기존 코드(app.py, services/pdf_report.py 등)가 `from core.spec_score import ...`
형태로 import 하고 있을 수 있으므로, 이 모듈은 동일 이름을 그대로 재노출한다.
새로 작성하는 코드는 core.matching 을 직접 import 할 것.
"""

from core.matching import (  # noqa: F401
    GRADE_MIN, GRADE_MAX, GRADE_WEIGHT, CERT_WEIGHT, FIT_WEIGHT, TALENT_WEIGHT,
    convert_grade_to_score, calc_cert_score, calc_fit_score, calc_talent_score,
    calc_spec_score, build_feedback,
)

__all__ = [
    "GRADE_MIN", "GRADE_MAX", "GRADE_WEIGHT", "CERT_WEIGHT", "FIT_WEIGHT",
    "TALENT_WEIGHT", "convert_grade_to_score", "calc_cert_score",
    "calc_fit_score", "calc_talent_score", "calc_spec_score", "build_feedback",
]
