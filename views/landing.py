# -*- coding: utf-8 -*-
"""
views/landing.py
[v2] 랜딩 화면 — 접속 시 가장 먼저 보이는 화면

디자인 기준 (DESIGN.md v2 · 팀 포트폴리오 사이트와 같은 언어)
-------------------------------------------------------------
 · 흰 바탕과 연회색 띠를 번갈아 깔고, 섹션마다 '작은 파란 라벨 + 큰 두 줄 헤드라인'
 · 첫 화면에는 핵심 하나 — 이 앱이 무엇을 알려주는지 한 문장과 시작 버튼
 · 버튼은 '시작하기' 하나. 폰에서는 화면 하단에 꽉 차게 붙어 스크롤해도 따라온다
   (컨테이너 key mjp_cta_ → ui/theme.py 모바일 규칙)
 · 문구는 기존 랜딩·기능 설명에 있던 사실만 쓴다 (새 수치·주장 없음)
"""

import streamlit as st

from core import session as ss
from ui import brand, mascot
from ui.components import render_html
from ui.emblem import emblem_svg

# 100점의 구성 — 스펙 진단 화면의 세부 점수 만점과 같은 값 (views/tab_spec.py)
_SCORE_PARTS = [
    ("내신 성취도", "30점", "5등급 성취평가제를 정량 환산"),
    ("자격증 가산점", "40점", "직무 유사 자격증은 70% 인정"),
    ("전공 적합성", "20점", "학과 계열과 기업 산업 분류의 일치"),
    ("인재상 일치도", "10점", "나의 강점 키워드와 기업 인재상"),
]

# 기존 랜딩의 가치 제안 3가지 (제목·설명 문구 그대로)
_POINTS = [
    (["로컬 연산", "AI 호출 없음"], "100점 만점 합격 지수",
     "5등급 성취평가제를 정량 환산하고 자격증 인정 비율까지 계산합니다. "
     "AI 호출 없는 로컬 연산이라 입력하는 즉시 점수가 바뀝니다."),
    (["고용24 · 잡알리오 · 강소기업"], "3개 출처 통합 검색",
     "고용24·잡알리오·강소기업 포털을 동시에 호출합니다. "
     "한 소스가 죽어도 백업 데이터로 즉시 전환돼 화면이 멈추지 않습니다."),
    (["OGQ 마스코트"], "OGQ 캐릭터 성장 스탬프",
     "점수와 로드맵 단계에 맞춰 캐릭터가 반응합니다. "
     "낮은 점수를 받은 학생이 화면을 닫지 않게 만드는 장치입니다."),
]


def render() -> None:
    _render_hero()
    _render_score_parts()
    _render_points()
    _render_steps()
    _render_closing()


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


# ------------------------------------------------------------
# 2. 큰 숫자 — 100점이 어떻게 나뉘는지
# ------------------------------------------------------------
def _render_score_parts() -> None:
    stats = "".join(f"""
        <div class="mjp-stat">
            <div class="mjp-stat-label">{label}</div>
            <div class="mjp-stat-value">{value}</div>
            <div class="mjp-stat-note">{note}</div>
        </div>""" for label, value, note in _SCORE_PARTS)
    render_html(f"""
    <section class="mjp-band mjp-band-alt mjp-center" style="margin-top:var(--mjp-s4);">
        <span class="mjp-eyebrow">100점 만점 합격 지수</span>
        <h2 class="mjp-headline">100점은<br>이렇게 나뉩니다</h2>
        <p class="mjp-lead">입력하는 즉시 네 가지 점수가 다시 계산됩니다.</p>
        <div class="mjp-grid mjp-g4">{stats}</div>
    </section>
    """)


# ------------------------------------------------------------
# 3. 태그 칩 카드 — 기존 가치 제안 3가지
# ------------------------------------------------------------
def _render_points() -> None:
    cards = "".join(f"""
        <div class="mjp-tcard">
            {''.join(f'<span class="mjp-chiptag">{t}</span>' for t in tags)}
            <h4>{title}</h4>
            <p>{desc}</p>
        </div>""" for tags, title, desc in _POINTS)
    render_html(f"""
    <section class="mjp-band mjp-center">
        <span class="mjp-eyebrow">핵심 기능</span>
        <h2 class="mjp-headline">점수만 보여주고<br>끝나지 않게</h2>
        <div class="mjp-grid mjp-g3">{cards}</div>
    </section>
    """)


# ------------------------------------------------------------
# 4. STEP 타임라인 — 메인 허브의 4대 기능 순서 (core.session.FEATURES 문구 그대로)
# ------------------------------------------------------------
def _render_steps() -> None:
    steps = "".join(f"""
        <li>
            <div class="mjp-step-no">STEP {i}</div>
            <h4>{f['title']}</h4>
            <p>{f['desc']}</p>
        </li>""" for i, f in enumerate(ss.FEATURES, start=1))
    render_html(f"""
    <section class="mjp-band mjp-band-alt mjp-center">
        <span class="mjp-eyebrow">이렇게 써요</span>
        <h2 class="mjp-headline">진단부터 자소서까지,<br>한 화면에서</h2>
        <ol class="mjp-steps">{steps}</ol>
    </section>
    """)


# ------------------------------------------------------------
# 5. 마스코트 인사 + 팀 · 예시 데이터 안내
# ------------------------------------------------------------
def _render_closing() -> None:
    # 마스코트는 기존과 같은 한 곳 · 같은 크기(104px)로만 둔다
    m_html = mascot.html("welcome", size=104)
    if m_html:
        render_html(f"""
        <div class="mjp-mascot-hello">
            {m_html}
            <p>안녕하세요! 저는 여러분의 취업 준비를 함께할 <b>마스코트</b>예요.<br>
               진단부터 자소서까지 옆에서 응원할게요.</p>
        </div>
        """)

    render_html(f"""
    <div class="mjp-footer">
        {brand.TEAM_NAME} · 김우빈 · 김정수 · 오상명 · 이건희<br>
        <div class="mjp-disclaimer">
            기업 별점·복지·선배 리뷰 등 세부 콘텐츠는 팀이 구성한 <b>예시 데이터</b>입니다.
        </div>
    </div>
    """)
