# -*- coding: utf-8 -*-
"""
views/landing.py
[v2] 랜딩 화면 — 접속 시 가장 먼저 보이는 화면

▣ 히어로만 둔다
   예전에는 아래로 스크롤하면 사용법·핵심 기능이 있었지만, 학생들이 그 내용이
   있는 줄도 모르고 '시작하기'만 누르고 지나갔다. 그래서 랜딩은 첫 화면(로고 ·
   제목 · 부제 · 배지 2개 · 시작하기 · 게스트모드 안내)만 남기고, 사용법·FAQ 는
   시작하기 다음 화면(로그인 화면 위쪽, views/login_guide.py)으로 옮겼다.

 · 버튼은 '시작하기' 하나. 폰에서는 화면 하단에 꽉 차게 붙는다
   (컨테이너 key mjp_cta_ → ui/theme.py 모바일 규칙)
 · 데스크톱에서는 히어로가 화면 세로 가운데에 오도록 .mjp-landing-solo 로 감싼다
"""

import streamlit as st

from core import session as ss
from ui import brand
from ui.components import render_html
from ui.emblem import emblem_svg


def render() -> None:
    with st.container(key="mjp_landing_solo"):
        _render_hero()


# ------------------------------------------------------------
# 1. 첫 화면 — 한 문장 + 시작 버튼
# ------------------------------------------------------------
def _render_hero() -> None:
    render_html(f"""
    <div class="mjp-landing-hero">
        <div class="mjp-landing-mark" style="background:#191F28; border-radius:22px; padding:6px;">
            {emblem_svg(72, detail="mark", uid="landmark")}
        </div>
        <span class="mjp-eyebrow">{brand.SERVICE_NAME}</span>
        <h1 class="mjp-landing-title">내신 등급과 자격증이<br><em>어느 기업에 통하는지</em></h1>
        <p class="mjp-lead" style="margin-left:auto; margin-right:auto;">
            숫자로 알려드립니다.<br>
            진단부터 자소서까지, 마이스터고 취업의 전 과정을 한 화면에서.
        </p>
        <div class="mjp-chips">
            <span class="mjp-chip">전북기계공업고등학교 · 팀 E.M.P</span>
            <span class="mjp-chip">제4회 NAVER OGQ마켓 AI Competition 본선 진출</span>
        </div>
    </div>
    """)

    # 폰에서는 이 컨테이너가 화면 하단에 고정된다 (key 가 mjp_cta_ 로 시작)
    with st.container(key="mjp_cta_landing"):
        if st.button("시작하기", type="primary", use_container_width=True, key="landing_cta"):
            ss.goto(ss.PAGE_LOGIN)
    render_html(
        '<div class="mjp-landing-note">회원가입 없이 <b>게스트모드</b>로도 모든 기능을 쓸 수 있어요.</div>'
    )
