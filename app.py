# -*- coding: utf-8 -*-
"""
AI Job Pass Finder — 전북기계공업고등학교 E.M.P 팀
제4회 NAVER OGQ마켓 AI Competition 본선 진출작

실행: streamlit run app.py

▣ 이 파일의 역할은 '라우터' 하나뿐이다
   개편 전에는 820줄짜리 app.py 안에 5개 탭 내용이 if/elif 로 모두 들어 있었고,
   접속하자마자 1번 탭이 바로 떴다. 이제 app.py 는 화면을 그리지 않는다.
   부팅 → 인증 처리 → 접근 제어 → 해당 화면 모듈 호출, 딱 이 순서만 담당한다.

   화면 흐름:
       랜딩 → 로그인 → 역할 선택 → 메인 허브 → 기능 화면
       (재방문 유저는 역할 선택을 건너뛰고 곧장 허브로)

   구조:
       core/session.py   라우팅 · 세션 상태 · 접근 제어
       services/auth.py  카카오/네이버/구글 OAuth2 + 게스트모드
       services/store.py 사용자 · 반 · 활동기록 영속 저장
       ui/               디자인 토큰 · 전역 CSS(모바일 포함) · 공통 컴포넌트
       views/            화면별 렌더링 모듈
"""

import streamlit as st

# ------------------------------------------------------------
# 0. 페이지 설정 — 반드시 다른 st.* 호출보다 먼저 와야 한다
# ------------------------------------------------------------
st.set_page_config(
    page_title="AI Job Pass Finder",
    page_icon="🧭",
    layout="wide",
    # 모바일(QR 접속)에서 사이드바 햄버거를 누르게 만들지 않기 위해,
    # 내비게이션을 전부 본문 상단으로 올리고 사이드바는 접어둔다.
    initial_sidebar_state="collapsed",
)

from core import session as ss                      # noqa: E402
from services import auth as auth_svc               # noqa: E402
from ui.theme import inject_css                     # noqa: E402
from views import (                                 # noqa: E402
    class_board, class_join, class_setup, hub, landing, login, mypage, role_select,
    tab_explore, tab_guide, tab_next, tab_resume, tab_spec,
)

# ------------------------------------------------------------
# 1. 전역 스타일 + 세션 부팅
# ------------------------------------------------------------
inject_css()
ss.init_session()

# ------------------------------------------------------------
# 2. OAuth 콜백 처리
#    제공자가 ?code=... 를 붙여 돌려보냈는지 매 rerun 마다 확인한다.
#    consume_oauth_callback() 이 사용한 파라미터를 즉시 URL 에서 제거하므로
#    같은 코드가 두 번 교환되는 일은 없다.
# ------------------------------------------------------------
if not ss.is_authed():
    oauth_user, oauth_error = auth_svc.consume_oauth_callback()
    if oauth_user:
        ss.login(oauth_user)
    elif oauth_error:
        st.session_state["login_error"] = oauth_error
        st.session_state["page"] = ss.PAGE_LOGIN

# ------------------------------------------------------------
# 3. 접근 제어
#    URL 로 ?page=spec 을 직접 치고 들어와도 로그인·역할 선택을 건너뛸 수 없다.
# ------------------------------------------------------------
ss.guard()

# ------------------------------------------------------------
# 4. 라우팅
# ------------------------------------------------------------
ROUTES = {
    ss.PAGE_LANDING: landing.render,
    ss.PAGE_LOGIN: login.render,
    ss.PAGE_ROLE: role_select.render,
    ss.PAGE_HUB: hub.render,
    ss.PAGE_MYPAGE: mypage.render,
    ss.PAGE_CLASS_SETUP: class_setup.render,
    ss.PAGE_CLASS_JOIN: class_join.render,
    ss.PAGE_CLASS_BOARD: class_board.render,
    ss.PAGE_SPEC: tab_spec.render,
    ss.PAGE_EXPLORE: tab_explore.render,
    ss.PAGE_GUIDE: tab_guide.render,
    ss.PAGE_RESUME: tab_resume.render,
    ss.PAGE_NEXT: tab_next.render,
}

ROUTES.get(ss.current_page(), landing.render)()
