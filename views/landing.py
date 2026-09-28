# -*- coding: utf-8 -*-
"""
views/landing.py
[Phase 1-1] 랜딩 화면 — 접속 시 가장 먼저 보이는 화면

디자인 기준 — 자격증 수첩의 표지와 속지
----------------------------------------
 · 표지: 네이비 + 금박 엠블럼 + 명조 제목 + 대회 인장
 · 화면에 CTA 는 단 하나("시작하기")만 두어 시선을 분산시키지 않는다
 · 속지: 이 앱이 하는 일을 '항목 | 내용' 괘선 표로
"""

import streamlit as st

from core import session as ss
from ui import brand, icons, mascot
from ui.components import render_html
from ui.theme import BRAND, CARD_BORDER, MUTED, TEXT


def render() -> None:
    # ---------- 표지 ----------
    # 국가기술자격증 수첩의 표지: 네이비 바탕, 금박 엠블럼, 명조 제목.
    # 대회 본선 진출은 제목 위 라벨이 아니라 표지 모서리의 원형 인장으로 찍는다.
    render_html(f"""
    <div class="mjp-cover">
        <div class="mjp-seal" aria-label="제4회 NAVER OGQ마켓 AI Competition 본선 진출">
            <span>제4회 OGQ</span><b>본선</b><span>진출</span>
        </div>
        {brand.logo_html(max_px=176, min_px=112, detail="full")}
        <h1 class="mjp-cover-title">{brand.SERVICE_NAME}</h1>
        <p class="mjp-cover-sub">
            내신 등급과 자격증이 <b>어느 기업에 통하는지</b> 100점 만점 점수로 알려드립니다.
            진단부터 자소서까지, 마이스터고 취업 준비를 한 곳에서.
        </p>
        <div class="mjp-cover-issuer">발급 · 전북기계공업고등학교 E.M.P</div>
    </div>
    """)

    # ---------- CTA ----------
    # 표지 바로 아래, 화면에 행동은 하나만 둔다.
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.15, 1])
    with center:
        if st.button("시작하기", type="primary", use_container_width=True, key="landing_cta"):
            ss.goto(ss.PAGE_LOGIN)
        render_html(
            f'<div style="text-align:center; color:{MUTED}; font-size:var(--mjp-caption); margin-top:10px;">'
            f'회원가입 없이 <b style="color:{TEXT};">게스트모드</b>로도 모든 기능을 쓸 수 있어요.</div>'
        )

    # ---------- 수첩 속지: 이 앱이 하는 일 ----------
    # 같은 크기 카드 세 장 대신, 자격증 속지의 '항목 | 내용' 괘선 표로 적는다.
    points = [
        ("chart", "합격 지수",
         "5등급 성취평가제 내신과 전공 자격증을 <b>100점 만점</b>으로 환산합니다. "
         "AI 호출 없는 로컬 연산이라 입력하는 즉시 점수가 바뀝니다."),
        ("search", "기업 탐색",
         "고용24·잡알리오·강소기업 포털을 한 번에 조회합니다. "
         "응답하지 않는 소스는 <b>백업 데이터로 즉시 전환</b>돼 화면이 멈추지 않습니다."),
        ("pencil", "자소서",
         "진단 결과와 목표 기업을 바탕으로 자소서 초안을 만들고, "
         "직접 쓴 초안은 <b>문항별로 첨삭</b>합니다."),
        ("stamp", "성장 스탬프",
         "점수와 로드맵 단계에 맞춰 OGQ 캐릭터가 반응합니다. "
         "낮은 점수에도 <b>다음에 할 일</b>을 함께 알려줍니다."),
    ]
    rows = "".join(
        f'<div class="mjp-form-row">'
        f'<div class="mjp-form-key">{icons.icon(ic, size=18, color=BRAND, stroke=1.8)}{title}</div>'
        f'<div class="mjp-form-val">{desc}</div></div>'
        for ic, title, desc in points
    )
    render_html(f'<div class="mjp-form">{rows}</div>')

    # [Phase 4] 마스코트 인사 — 인상이지 행동 유도가 아니므로 표 아래.
    m_html = mascot.html("welcome", size=96)
    if m_html:
        render_html(f"""
        <div style="display:flex; align-items:center; justify-content:center;
                    gap:14px; margin-top:24px; flex-wrap:wrap;">
            {m_html}
            <div style="color:{MUTED}; font-size:var(--mjp-small); line-height:1.6; max-width:300px;">
                안녕하세요! 저는 여러분의 취업 준비를 함께할 <b style="color:{TEXT};">마스코트</b>예요.
                진단부터 자소서까지 옆에서 응원할게요.
            </div>
        </div>
        """)

    # ---------- 판권면 ----------
    render_html(f"""
    <div style="text-align:center; margin-top:40px; padding-top:18px;
                border-top:3px double {CARD_BORDER}; color:{MUTED}; font-size:var(--mjp-caption); line-height:1.8;">
        {brand.TEAM_NAME} · 김우빈 · 김정수 · 오상명 · 이건희<br>
        기업 별점·복지·선배 리뷰 등 세부 콘텐츠는 팀이 구성한 <b>예시 데이터</b>입니다.
    </div>
    """)
