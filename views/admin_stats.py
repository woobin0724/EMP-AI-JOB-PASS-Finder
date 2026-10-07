# -*- coding: utf-8 -*-
"""
views/admin_stats.py
사용 통계 — 팀 관리자 전용 (services/access.py 로 화면 자체에서 검사)

services/usage_log.py 가 쌓은 기록을 숫자로 보여준다. 기본은 테스트 기록
(개발 환경 · 관리자 · 데모 계정)을 뺀 '실제 사용자' 기준이다.
"""

import pandas as pd
import streamlit as st

from services import access, storage_backend, usage_log
from ui.components import back_to_hub, section_title, topbar


def _pct(value) -> str:
    return f"{value * 100:.0f}%" if value is not None else "—"


def render() -> None:
    topbar()
    back_to_hub()
    if access.deny_if_not_admin():
        return
    section_title("사용 통계", icon_name="chart", sub=
                  "로그인한 사용자의 접속일·화면 이동·스토리 반응 기록입니다. "
                  "이름·학교 같은 개인 정보는 남기지 않고, 사용자는 해시 ID 로만 구분합니다.")

    if not usage_log.is_production():
        st.warning("지금 서버는 운영 환경으로 설정되어 있지 않아(APP_ENV ≠ production) "
                   "새로 쌓이는 기록이 전부 '테스트'로 표시됩니다. 배포 서버의 Secrets 에 "
                   "APP_ENV = \"production\" 을 넣어야 실제 사용자 기록이 됩니다.")
    store = storage_backend.status()
    if not store["durable"]:
        st.info(f"기록 저장 위치: {store['name']} — Streamlit Cloud 에서는 재배포 때 지워집니다. "
                "오래 보관하려면 Supabase 를 연결하세요 (docs/STORAGE.md).")

    include_test = st.toggle("테스트 기록 포함해서 보기", value=False, key="stats_include_test")
    s = usage_log.summarize(usage_log.load(), include_test=include_test)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("사용자 수", s["users"])
    c2.metric("재방문 사용자", s["returning"], help="서로 다른 날 2번 이상 접속한 사용자")
    c3.metric("재방문 비율", _pct(s["returning_rate"]))
    c4.metric("스토리 관심 비율", _pct(s["like_rate"]),
              help=f"관심 {s['likes']} · 패스 {s['passes']} (같은 기업에 반응을 바꾸면 마지막 것만 셈)")
    st.caption(f"테스트로 표시된 사용자 {s['test_visitors']}명 · 저장된 이벤트 {s['events_total']}건")

    left, right = st.columns(2)
    with left:
        st.markdown("#### 날짜별 접속자 수")
        if s["by_day"]:
            st.dataframe(pd.DataFrame(
                [{"날짜": d, "접속자 수": n} for d, n in s["by_day"].items()]),
                hide_index=True, use_container_width=True)
        else:
            st.caption("아직 기록이 없습니다.")
    with right:
        st.markdown("#### 기능별 사용 횟수 (화면 이동)")
        if s["by_page"]:
            st.dataframe(pd.DataFrame(
                [{"화면": p, "이동 횟수": n} for p, n in s["by_page"].items()]),
                hide_index=True, use_container_width=True)
        else:
            st.caption("아직 기록이 없습니다.")
