# -*- coding: utf-8 -*-
"""
views/login.py
[Phase 1-2] 로그인 화면 — 카카오 / 네이버 / 구글 / 게스트모드

동작 규칙 (services/auth.py 의 설계와 짝을 이룬다)
------------------------------------------------
 · st.secrets 에 해당 제공자 키가 있으면 → 진짜 OAuth 인가 URL 로 이동
 · 키가 없으면                          → 같은 자리에 '🔒 준비중' 버튼이 뜨고
                                          게스트모드로 유도한다
즉 이 화면의 코드는 대회 전/후로 바뀌지 않는다. 바뀌는 건 secrets.toml 뿐이다.

▣ 소셜 버튼을 st.button 이 아니라 <a> 태그로 그리는 이유
   OAuth 는 사용자를 제공자 사이트로 **같은 탭에서** 보내야 한다. st.link_button
   은 새 탭으로 열려 콜백(?code=...)이 원래 앱 탭으로 돌아오지 못한다.
   그래서 target="_self" 앵커를 직접 그린다. 덤으로 카카오 노란색·네이버
   초록색 같은 브랜드 컬러를 정확히 입힐 수 있다.
"""

import streamlit as st

from core import session as ss
from services import auth as auth_svc
from services import store
from ui import brand, mascot
from ui.icons import brand_symbol
from ui.components import or_divider, render_html
from ui.theme import CARD, MUTED, TEXT
from views import login_guide

# '바로 로그인하기 ↓' 가 스크롤해 갈 앵커 id
LOGIN_ANCHOR = "mjp-login-area"


def _provider_anchor(key: str) -> str:
    """설정이 끝난 제공자의 로그인 버튼(앵커) HTML."""
    spec = auth_svc.PROVIDERS[key]
    url = auth_svc.build_authorize_url(key)
    return f"""
    <a href="{url}" target="_self" style="
        display:flex; align-items:center; justify-content:center; gap:10px;
        width:100%; min-height:52px; margin-bottom:10px;
        background:{spec['bg']}; color:{spec['fg']};
        border:1px solid {spec['border']}; border-radius:16px;
        font-size:var(--mjp-body); font-weight:600; text-decoration:none;">
        {brand_symbol(spec['icon'], size=19, color=spec['fg'])}{spec['label']}
    </a>"""


def _provider_disabled(key: str) -> str:
    """키 미등록 상태의 비활성 버튼 HTML."""
    spec = auth_svc.PROVIDERS[key]
    return f"""
    <div style="
        display:flex; align-items:center; justify-content:center; gap:10px;
        width:100%; min-height:52px; margin-bottom:10px;
        background:{CARD}; color:{MUTED}; border-radius:16px;
        font-size:var(--mjp-body); font-weight:600; cursor:not-allowed;">
        <span style="opacity:.45;">{brand_symbol(spec['icon'], size=17, color=MUTED)}</span>
        {spec['label']}<span style="font-size:var(--mjp-caption); font-weight:600;">· 준비중</span>
    </div>"""


def render() -> None:
    """
    [화면 구성] 시작하기 다음 화면
      1. 맨 위 안내 — '처음이라면 사용법부터' + '바로 로그인하기 ↓' (로그인 영역으로 앵커 이동)
      2. 사용법 · 핵심 기능 · FAQ — 연회색 띠 (views/login_guide.py)
      3. 로그인 영역 — 게스트 시작 · 소셜 로그인 · 이어하기 코드 (동작은 예전과 같다)
      4. 마스코트 인사 · 팀 안내 (예전 랜딩 맨 아래에 있던 것)
    """
    # 소셜 로그인이 실패해 돌아온 경우의 오류는 화면 맨 위에 보여준다.
    # 로그인 영역은 사용법 아래에 있어서, 거기에만 띄우면 처음 화면에서 보이지 않는다.
    if st.session_state.get("login_error"):
        st.error(st.session_state["login_error"])
        st.session_state["login_error"] = ""

    _render_intro()
    login_guide.render()

    # 앵커 — '바로 로그인하기 ↓' 와 FAQ 끝 '이제 시작해볼까요? ↓' 가 여기로 온다
    render_html(f'<div id="{LOGIN_ANCHOR}" class="mjp-anchor"></div>')
    render_html("""
    <div class="mjp-narrow" style="text-align:center; padding:8px 0 8px;">
        <div class="mjp-section-title">로그인</div>
        <div class="mjp-section-sub" style="margin:10px auto 0;">
            진단 결과와 찜한 기업을 다음에 다시 볼 수 있어요.
        </div>
    </div>
    """)

    with st.container(key="mjp_narrow_login"):

        # ---------- 게스트모드 ----------
        # 라벨을 숨기면 무엇을 적는 칸인지 placeholder 로만 알 수 있다 → 보이게 둔다
        nickname = st.text_input(
            "이름 또는 닉네임 (선택)", key="guest_nickname", placeholder="예: 김우빈",
        )
        # 이 화면은 위쪽이 사용법이라 하단 고정 버튼을 두지 않는다 — 고정하면 사용법을 읽는
        # 내내 '게스트 시작'이 떠 있어 맨 위 '바로 로그인하기 ↓' 와 행동 유도가 둘이 된다.
        if st.button("게스트모드로 바로 시작하기", type="primary",
                     use_container_width=True, key="guest_login_btn"):
            user = auth_svc.guest_login(nickname)
            ss.login(user)

        render_html(
            '<div class="mjp-muted" style="margin:4px 0 8px; line-height:1.65;">'
            f'게스트로 시작하면 <b style="color:{TEXT};">이어하기 코드</b>가 발급됩니다. '
            '다음에 그 코드를 입력하면 저장된 기록을 그대로 이어서 볼 수 있어요.</div>'
        )

        or_divider()

        # ---------- 소셜 로그인 ----------
        # ▣ 왜 아래로 내렸나
        #   세 제공자 모두 키 미등록이면 '준비중' 버튼이다. 동작하지 않는
        #   버튼 3개가 실제로 동작하는 게스트 시작 위에 있으면, 첫 화면
        #   인상이 '안 되는 앱'이 된다. 키가 등록된 제공자가 하나라도 있으면
        #   펼친 상태로, 전부 준비중이면 접어서 보여준다.
        any_ready = any(auth_svc.is_configured(k) for k in ("kakao", "naver", "google"))
        with st.expander("소셜 계정으로 로그인", expanded=any_ready):
            for key in ("kakao", "naver", "google"):
                if auth_svc.is_configured(key):
                    st.markdown(_provider_anchor(key), unsafe_allow_html=True)
                else:
                    st.markdown(_provider_disabled(key), unsafe_allow_html=True)

        # ---------- 이어하기 ----------
        with st.expander("이어하기 코드가 있어요"):
            code = st.text_input("이어하기 코드 (6자리)", key="resume_code_input",
                                 placeholder="예: K7M2QX", max_chars=10)
            if st.button("코드로 이어하기", use_container_width=True, key="resume_btn"):
                uid = auth_svc.resume_code_to_user_id(code)
                saved = store.get_user(uid) if uid else None
                if saved:
                    ss.login({
                        "user_id": saved["user_id"],
                        "provider": saved.get("provider", "guest"),
                        "display_name": saved.get("display_name", ""),
                        "email": saved.get("email", ""),
                        "resume_code": uid.replace("guest_", ""),
                    })
                else:
                    st.error("해당 코드로 저장된 기록을 찾지 못했습니다. 코드를 다시 확인해주세요.")

        if st.button("← 처음 화면으로", use_container_width=True, key="login_back"):
            ss.goto(ss.PAGE_LANDING)

    _render_closing()


def _render_intro() -> None:
    """맨 위 짧은 안내 + 로그인 영역으로 건너뛰는 버튼 (폰 첫 화면 안에 들어오게 짧게)."""
    render_html(f"""
    <div class="mjp-login-intro">
        <span class="mjp-eyebrow">{brand.SERVICE_NAME}</span>
        <div class="mjp-section-title">처음이라면<br>사용법부터 살펴보세요</div>
        <div class="mjp-section-sub">로그인은 아래에 있어요.</div>
        <a class="mjp-jump" href="#{LOGIN_ANCHOR}" target="_self">바로 로그인하기 ↓</a>
    </div>
    """)


def _render_closing() -> None:
    """마스코트 인사 + 팀 안내 — 예전 랜딩 맨 아래에 있던 것 (마스코트는 같은 크기·한 곳)."""
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
        {brand.TEAM_NAME} · 김우빈 · 김정수 · 오상명 · 이건희
    </div>
    """)
