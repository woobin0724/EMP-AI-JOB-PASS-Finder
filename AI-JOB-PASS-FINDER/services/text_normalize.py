# -*- coding: utf-8 -*-
"""
services/text_normalize.py
검색/필터링 시 띄어쓰기·대소문자·특수문자 차이로 검색이 실패하지 않도록
텍스트를 정규화하는 유틸리티 모듈.
"""

import re

# 정규화 시 제거할 특수문자 패턴 (한글/영문/숫자만 남김)
_SPECIAL_CHARS_RE = re.compile(r"[^0-9a-zA-Z가-힣]")


def normalize(text: str) -> str:
    """
    검색/비교용 텍스트 정규화.
    - 공백 제거
    - 영문 소문자 통일
    - 특수문자 제거 (하이픈, 슬래시, 괄호 등)
    예) "정보처리 기능사" -> "정보처리기능사"
        "IT/소프트웨어과" -> "it소프트웨어과"
    """
    if text is None:
        return ""
    text = str(text).strip().lower()
    text = _SPECIAL_CHARS_RE.sub("", text)
    return text


def contains(haystack: str, needle: str) -> bool:
    """정규화된 문자열 기준 부분 일치 여부를 반환한다."""
    if not needle:
        return True
    return normalize(needle) in normalize(haystack)


def build_search_blob(*fields) -> str:
    """검색 대상 필드 여러 개를 하나의 정규화된 문자열로 결합한다."""
    return " ".join(normalize(f) for f in fields if f)
