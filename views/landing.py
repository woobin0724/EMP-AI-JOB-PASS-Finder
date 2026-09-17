# -*- coding: utf-8 -*-
"""
views/landing.py
[Phase 1-1] 랜딩 화면 — 접속 시 가장 먼저 보이는 화면

디자인 기준 (참고: Better Stack 스타일)
---------------------------------------
 · 넉넉한 여백 + 큰 타이포그래피 + 은은한 방사형 그라데이션
 · 화면에 CTA 는 단 하나("시작하기")만 두어 시선을 분산시키지 않는다
 · 로고는 clamp() 로 화면 폭에 비례 축소 (ui/brand.py)
"""

import streamlit as st

from core import session as ss
from ui import brand
from ui.theme import CARD_BORDER, GREEN, MUTED, TEXT


def render() -> None:
    # ---------- 히어로 ----------
    # 로고 → 소속 → 대회 배지 → 서비스명 → 설명 순서의 세로 락업.
    # 엠블럼 하단 아크가 이미 EMPLOYMENT MEISTER PARTNER 를 말하고 있으므로,
    # 바로 아래 줄에서 같은 문구를 반복하지 않고 소속 정보를 넣는다.
    # (레터스페이싱 처리는 원본 로고의 아크 타이포에서 가져왔다)
    st.markdown(f"""
    <div class="mjp-hero">
        {brand.logo_html(max_px=196, min_px=118, detail="full")}
        <div class="mjp-hero-team">전북기계공업고등학교 · 팀 E.M.P</div>
        <div style="margin-top:18px;">
            <span class="mjp-hero-kicker">제4회 NAVER OGQ마켓 AI Competition 본선 진출</span>
        </div>
        <h1 class="mjp-hero-title">{brand.SERVICE_NAME}</h1>
        <p class="mjp-hero-sub">
            내신 등급과 자격증이 <b style="color:{TEXT};">어느 기업에 통하는지</b> 숫자로 알려드립니다.<br>
            진단부터 자소서까지, 마이스터고 취업의 전 과정을 한 화면에서.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ---------- CTA ----------
    # 가운데 정렬을 위해 3분할하되, 모바일에서는 theme.py 규칙에 따라
    # 1단으로 접히면서 버튼이 화면 폭을 꽉 채운다.
    left, center, right = st.columns([1, 1.15, 1])
    with center:
        if st.button("🚀 시작하기", type="primary", use_container_width=True, key="landing_cta"):
            ss.goto(ss.PAGE_LOGIN)
        st.markdown(
            f'<div style="text-align:center; color:{MUTED}; font-size:12.5px; margin-top:10px;">'
            f'회원가입 없이 <b style="color:{GREEN};">게스트모드</b>로도 모든 기능을 쓸 수 있어요.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:38px;'></div>", unsafe_allow_html=True)

    # ---------- 3가지 가치 제안 ----------
    points = [
        ("📊", "100점 만점 합격 지수",
         "5등급 성취평가제를 정량 환산하고 자격증 인정 비율까지 계산합니다. "
         "AI 호출 없는 로컬 연산이라 입력하는 즉시 점수가 바뀝니다."),
        ("🔄", "6대 포털 통합 검색",
         "고용24·잡알리오·강소기업 포털을 동시에 호출합니다. "
         "한 소스가 죽어도 백업 데이터로 즉시 전환돼 화면이 멈추지 않습니다."),
        ("🎨", "OGQ 캐릭터 성장 스탬프",
         "점수와 로드맵 단계에 맞춰 캐릭터가 반응합니다. "
         "낮은 점수를 받은 학생이 화면을 닫지 않게 만드는 장치입니다."),
    ]
    cols = st.columns(3)
    for col, (icon, title, desc) in zip(cols, points):
        with col:
            st.markdown(f"""
            <div class="mjp-feature">
                <div class="mjp-feature-icon">{icon}</div>
                <div class="mjp-feature-title">{title}</div>
                <div class="mjp-feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ---------- 푸터 ----------
    st.markdown(f"""
    <div style="text-align:center; margin-top:44px; padding-top:20px;
                border-top:1px solid {CARD_BORDER}; color:{MUTED}; font-size:12px; line-height:1.8;">
        {brand.TEAM_NAME} · 김우빈 · 김정수 · 오상명 · 이건희<br>
        기업 별점·복지·선배 리뷰 등 세부 콘텐츠는 팀이 구성한 <b>예시 데이터</b>입니다.
    </div>
    """, unsafe_allow_html=True)
