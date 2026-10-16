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
from ui import brand
from ui.icons import brand_symbol
from ui.components import or_divider, render_html
from ui.emblem import emblem_svg
from ui.theme import CARD, MUTED, TEXT


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
    # v2: 가운데 좁은 칼럼 하나. 제일 큰 것은 '로그인' 제목, 주요 행동은 게스트 시작.
    render_html(f"""
    <div class="mjp-narrow" style="text-align:center; padding:24px 0 8px;">
        <div class="mjp-landing-mark" style="background:{TEXT}; border-radius:20px; padding:6px;
             width:64px; height:64px; margin-bottom:24px;">{emblem_svg(64, detail="mark", uid="loginmark")}</div>
        <span class="mjp-eyebrow">{brand.SERVICE_NAME}</span>
        <div class="mjp-section-title">로그인</div>
        <div class="mjp-section-sub" style="margin:10px auto 0;">
            진단 결과와 찜한 기업을 다음에 다시 볼 수 있어요.
        </div>
    </div>
    """)

    with st.container(key="mjp_narrow_login"):
        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])
            st.session_state["login_error"] = ""

        # ---------- 게스트모드 ----------
        # 라벨을 숨기면 무엇을 적는 칸인지 placeholder 로만 알 수 있다 → 보이게 둔다
        nickname = st.text_input(
            "이름 또는 닉네임 (선택)", key="guest_nickname", placeholder="예: 김우빈",
        )
        # 폰에서는 이 버튼이 화면 하단에 꽉 차게 고정된다 (key 가 mjp_cta_ 로 시작)
        with st.container(key="mjp_cta_login"):
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

    # ---------- 개발자용 설정 현황 ----------
    with st.container(key="mjp_narrow_setup"):
        _setup_panel()


def _setup_panel() -> None:
    """
    소셜 로그인 연동 현황과 설정 방법을 표로 보여준다.
    심사위원에게는 '왜 지금 준비중인지'를, 팀원에게는 '뭘 넣으면 켜지는지'를
    같은 화면에서 설명한다.
    """
    ready = auth_svc.configured_providers()
    label = ("소셜 로그인 연동 현황 — "
             + (f"{len(ready)}개 제공자 활성화" if ready else "현재 게스트모드로 동작 중"))

    with st.expander(label, expanded=False):
        st.markdown(
            "소셜 로그인은 **코드가 아니라 각 플랫폼의 앱 등록·검수 절차**가 병목입니다. "
            "그래서 OAuth2 인가 코드 흐름(`services/auth.py`)을 전부 구현해 두고, "
            "`st.secrets` 에 키가 있는지로 **런타임에 자동 전환**되도록 했습니다. "
            "키만 등록하면 코드 수정 없이 아래 상태가 '연동됨'으로 바뀝니다."
        )
        st.table(auth_svc.status_table())
        st.caption(
            f"현재 등록된 Redirect URI: `{auth_svc.redirect_uri()}` — "
            "각 개발자 콘솔에 **문자 단위로 동일하게** 등록되어야 합니다. "
            "배포 URL이 확정되면 `secrets.toml` 의 `OAUTH_REDIRECT_URI` 만 바꾸면 됩니다."
        )
