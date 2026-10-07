# -*- coding: utf-8 -*-
"""
services/access.py
팀 관리자 권한 — '기업 데이터 입력'과 '사용 통계' 화면을 지키는 단일 관문

▣ 왜 메뉴 숨기기만으로는 부족한가
   메뉴를 숨겨도 ?page=admin_data 처럼 URL 로 직접 들어오거나 세션 값을
   바꾸면 화면이 열린다. 그래서 메뉴(마이페이지)와 화면 자체 두 곳에서 모두
   이 모듈의 is_admin() 을 본다. 화면 쪽 검사가 실제 방어선이고, 메뉴 쪽은
   보이지 않게 하는 편의다.

▣ 관리자 지정
   st.secrets 의 ADMIN_USER_IDS 에 user_id 를 적는다. 기본값은 빈 목록이라
   아무도 관리자가 아니다.

       ADMIN_USER_IDS = ["kakao_1234567890"]

   게스트 계정(guest_XXXXXX)도 목록에 넣을 수는 있지만, 게스트는 6자리
   이어하기 코드만 알면 누구나 같은 계정으로 들어올 수 있다. 관리자는
   소셜 로그인 계정으로 지정하는 것을 권한다.
"""

import streamlit as st

from core import session as ss


def _secret(name: str, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def id_list(secret_name: str) -> set[str]:
    """
    secrets 의 ID 목록. TOML 배열과 쉼표 구분 문자열 둘 다 받는다
    (Streamlit Cloud 의 Secrets 편집기에서 배열 문법을 틀리는 경우가 잦다).
    """
    raw = _secret(secret_name, [])
    if isinstance(raw, str):
        items = raw.split(",")
    else:
        try:
            items = list(raw)
        except TypeError:
            items = []
    return {str(item).strip() for item in items if str(item).strip()}


def admin_user_ids() -> set[str]:
    return id_list("ADMIN_USER_IDS")


def is_admin(user_id: str | None = None) -> bool:
    uid = ss.user_id() if user_id is None else user_id
    return bool(uid) and uid in admin_user_ids()


def deny_if_not_admin() -> bool:
    """
    관리자가 아니면 안내를 그리고 True 를 돌려준다. 화면은 이 값이 True 면
    바로 return 한다 — 데이터 읽기·쓰기 코드까지 내려가지 않게.
    """
    if is_admin():
        return False
    st.error("팀 관리자만 열 수 있는 화면입니다.")
    st.caption("관리자는 운영 설정(Secrets)의 ADMIN_USER_IDS 에 등록된 계정입니다.")
    return True
