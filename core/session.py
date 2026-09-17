# -*- coding: utf-8 -*-
"""
core/session.py
[Phase 1] 화면 라우팅 + 세션 상태 단일 관문

▣ Streamlit 라우팅의 구조적 한계와 채택안
   Streamlit 은 매 상호작용마다 스크립트를 위에서 아래로 전부 재실행한다.
   진짜 URL 라우터가 없어 선택지는 셋이었다.

     (1) st.navigation / st.Page (네이티브 멀티페이지)
         → 사이드바 메뉴가 강제 노출된다. 랜딩·로그인 화면에 네비가 뚫고
           나오고 모바일에서는 햄버거 안에 갇힌다. 우리 디자인과 충돌 → 탈락
     (2) session_state 디스패처
         → 화면 전환을 100% 제어할 수 있다. 단 새로고침하면 처음으로 돌아간다.
     (3) query_params 미러링
         → URL 공유·QR 딥링크가 되지만, 양방향으로 동기화하면 rerun 무한루프.

   채택: (2)를 단일 진실원천으로 두고 (3)을 **단방향으로만** 병행한다.
     · 부팅 시 1회 URL → 세션 하이드레이션 (_bootstrapped 플래그로 1회 보장)
     · 이후에는 세션 → URL 쓰기만 수행
   덕분에 QR 로 접속한 폰에서 새로고침해도 보던 화면이 유지된다.
   (모바일 시연에서 화면이 랜딩으로 튕기는 사고를 막는 장치다.)
"""

import streamlit as st

from data.departments import DEPARTMENT_LIST
from data.roadmap import empty_milestones
from services import store
from services.fallback import SourceTracker

# ------------------------------------------------------------
# 화면 키
# ------------------------------------------------------------
PAGE_LANDING = "landing"
PAGE_LOGIN = "login"
PAGE_ROLE = "role"
PAGE_HUB = "hub"
PAGE_MYPAGE = "mypage"

# [Phase 2] 반 등록
PAGE_CLASS_SETUP = "class_setup"   # 선생님 — 우리 반 개설
PAGE_CLASS_JOIN = "class_join"     # 학생 — 반 코드 입력 (선택)
PAGE_CLASS_BOARD = "class_board"   # 선생님 — 우리 반 현황 대시보드

PAGE_SPEC = "spec"
PAGE_EXPLORE = "explore"
PAGE_GUIDE = "guide"
PAGE_RESUME = "resume"
PAGE_NEXT = "next"

# 로그인 없이 볼 수 있는 화면
PUBLIC_PAGES = {PAGE_LANDING, PAGE_LOGIN}

# 역할 선택을 마쳐야 들어갈 수 있는 화면
FEATURE_PAGES = {
    PAGE_HUB, PAGE_MYPAGE, PAGE_SPEC, PAGE_EXPLORE, PAGE_GUIDE, PAGE_RESUME, PAGE_NEXT,
    PAGE_CLASS_SETUP, PAGE_CLASS_JOIN, PAGE_CLASS_BOARD,
}

ALL_PAGES = PUBLIC_PAGES | {PAGE_ROLE} | FEATURE_PAGES

# 메인 허브에 카드로 노출할 4대 핵심 기능 (+ 부록 탭)
FEATURES = [
    {
        "key": PAGE_SPEC, "icon": "📊", "title": "스펙 진단 & 추천", "nav": "스펙 진단",
        "desc": "내신·자격증·인재상을 100점 만점으로 환산해 합격 가능성을 즉시 계산합니다. "
                "AI 호출 없이 로컬 연산이라 슬라이더를 움직이는 즉시 갱신됩니다.",
    },
    {
        "key": PAGE_EXPLORE, "icon": "🔍", "title": "실시간 기업 탐색기", "nav": "기업 탐색",
        "desc": "고용24·잡알리오·강소기업 포털을 한 번에 검색합니다. "
                "응답하지 않는 소스는 즉시 백업 데이터로 전환돼 화면이 멈추지 않습니다.",
    },
    {
        "key": PAGE_GUIDE, "icon": "🛠", "title": "채용 대비 가이드 & 커리큘럼", "nav": "가이드",
        "desc": "목표 기업별 면접 기출·필기 키워드·4주 커리큘럼을 제공하고, "
                "커리어 로드맵 3단계를 스탬프로 관리합니다.",
    },
    {
        "key": PAGE_RESUME, "icon": "📄", "title": "합격 이력서 & 자소서", "nav": "자소서",
        "desc": "내 스펙과 기업 인재상을 엮어 자기소개서 초안을 생성합니다. "
                "동일 입력은 캐시로 응답해 API 과금을 막습니다.",
    },
]


# ------------------------------------------------------------
# 세션 기본값
# ------------------------------------------------------------
def _defaults() -> dict:
    return {
        # --- 라우팅/인증 ---
        "page": PAGE_LANDING,
        "auth": None,            # {"user_id","provider","display_name","email"}
        "role": None,            # "student" | "teacher"
        "class_code": None,      # 소속 반(학생) / 담당 반(선생님)
        "resume_code": "",       # 게스트 이어하기 코드
        "login_error": "",

        # --- 기존 기능 상태 (원본 app.py 에서 이관) ---
        "student_name": "",
        "dept": DEPARTMENT_LIST[0],
        "grade": 3.0,
        "user_certs": [],
        "strength_keywords": [],
        "selected_company_id": None,
        "milestones": empty_milestones(),
        "last_spec_result": None,
        "last_curriculum": None,
        "cover_letter": None,
        "cover_letter_source": None,
        "cover_letter_cached": False,
        "cover_letter_options": None,   # [Phase 5] 문체·분량·회차
        "live_jobs": None,
        "tracker": SourceTracker(),

        # --- 외부 API 키 (사이드바 → 설정 패널로 이동) ---
        "qnet_key": "",
        "worknet_key": "",
    }


def init_session() -> None:
    """부팅 시 1회 호출. 기본값 주입 + URL 하이드레이션."""
    for key, value in _defaults().items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.get("_bootstrapped"):
        _hydrate_from_url()
        st.session_state["_bootstrapped"] = True


def _hydrate_from_url() -> None:
    """
    URL 쿼리스트링(?page=...&uid=...)에서 상태를 복원한다.
    **부팅 시 단 한 번만** 실행된다 — 매 rerun 마다 하면 사용자의 화면 이동을
    URL 이 되돌려버려 무한루프가 된다.
    """
    try:
        params = st.query_params
    except Exception:
        return

    uid = params.get("uid")
    if uid:
        user = store.get_user(uid)
        if user:
            st.session_state["auth"] = {
                "user_id": user["user_id"],
                "provider": user.get("provider", "guest"),
                "display_name": user.get("display_name", ""),
                "email": user.get("email", ""),
            }
            st.session_state["role"] = user.get("role")
            st.session_state["class_code"] = user.get("class_code")
            if not st.session_state["student_name"]:
                st.session_state["student_name"] = user.get("display_name", "")

    page = params.get("page")
    if page in ALL_PAGES:
        st.session_state["page"] = page


def _sync_url() -> None:
    """세션 → URL 단방향 반영. 새로고침/공유 시 같은 화면으로 돌아오게 한다."""
    try:
        st.query_params["page"] = st.session_state["page"]
        auth = st.session_state.get("auth")
        if auth:
            st.query_params["uid"] = auth["user_id"]
    except Exception:
        # query_params 를 지원하지 않는 구버전에서도 앱은 정상 동작해야 한다
        pass


def goto(page: str, rerun: bool = True) -> None:
    """화면 전환. 콜백 안에서 쓸 때는 rerun=False 로 호출한다."""
    if page not in ALL_PAGES:
        page = PAGE_LANDING
    st.session_state["page"] = page
    _sync_url()
    if rerun:
        st.rerun()


def current_page() -> str:
    return st.session_state.get("page", PAGE_LANDING)


# ------------------------------------------------------------
# 인증 상태
# ------------------------------------------------------------
def is_authed() -> bool:
    return bool(st.session_state.get("auth"))


def user_id() -> str:
    auth = st.session_state.get("auth") or {}
    return auth.get("user_id", "")


def display_name() -> str:
    auth = st.session_state.get("auth") or {}
    return auth.get("display_name") or st.session_state.get("student_name") or "학생"


def provider() -> str:
    auth = st.session_state.get("auth") or {}
    return auth.get("provider", "")


def login(user: dict) -> None:
    """
    로그인 완료 처리.
    저장소에 사용자를 기록하고, **이미 역할을 고른 재방문 유저는 역할 선택을
    건너뛰고 곧장 허브로** 보낸다 (Phase 1-3 요구사항).
    """
    st.session_state["auth"] = {
        "user_id": user["user_id"],
        "provider": user.get("provider", "guest"),
        "display_name": user.get("display_name", ""),
        "email": user.get("email", ""),
    }
    st.session_state["resume_code"] = user.get("resume_code", "")
    st.session_state["login_error"] = ""

    # 이전 사용자의 찜 캐시·디바운스 기록이 남아 있으면 남의 데이터를 보게 된다.
    # (같은 브라우저 세션에서 이어하기 코드로 계정을 바꾸는 경우가 실제로 있다.)
    from services.activity import clear_caches
    clear_caches()

    saved = store.upsert_user(
        user["user_id"],
        provider=user.get("provider", "guest"),
        display_name=user.get("display_name", ""),
        email=user.get("email", ""),
    )

    st.session_state["role"] = saved.get("role")
    st.session_state["class_code"] = saved.get("class_code")
    if not st.session_state["student_name"]:
        st.session_state["student_name"] = saved.get("display_name", "")

    # 저장된 마일스톤 복원 (재방문 시 로드맵 진행도 유지)
    if saved.get("milestones"):
        merged = empty_milestones()
        merged.update({k: bool(v) for k, v in saved["milestones"].items() if k in merged})
        st.session_state["milestones"] = merged

    goto(PAGE_HUB if saved.get("role") else PAGE_ROLE)


def logout() -> None:
    """로그아웃. 기능 상태까지 초기화해 다음 사용자에게 남지 않게 한다."""
    for key in list(st.session_state.keys()):
        if key not in ("_bootstrapped",):
            del st.session_state[key]
    try:
        st.query_params.clear()
    except Exception:
        pass
    init_session()
    st.session_state["page"] = PAGE_LANDING
    st.rerun()


def guard() -> None:
    """
    접근 제어. 라우팅 직전에 호출한다.
      · 로그인 안 했는데 기능 화면 요청 → 로그인 화면으로
      · 로그인은 했는데 역할 미선택 → 역할 선택 화면으로
    URL 로 ?page=spec 을 직접 치고 들어오는 경우까지 막아준다.
    """
    page = current_page()

    if page in PUBLIC_PAGES:
        return

    if not is_authed():
        st.session_state["page"] = PAGE_LOGIN
        return

    if not st.session_state.get("role") and page != PAGE_ROLE:
        st.session_state["page"] = PAGE_ROLE


# ------------------------------------------------------------
# [Phase 2] 반(학급) 상태
# ------------------------------------------------------------
def is_teacher() -> bool:
    return st.session_state.get("role") == "teacher"


def is_student() -> bool:
    return st.session_state.get("role") == "student"


def class_code() -> str | None:
    return st.session_state.get("class_code")


def set_class_code(code: str | None) -> None:
    st.session_state["class_code"] = code


def nav_items() -> list[tuple[str, str]]:
    """
    상단 내비에 올릴 (화면키, 라벨) 목록.

    역할에 따라 달라진다 — 선생님에게는 '우리 반'이 추가된다.
    라벨은 FEATURES 의 짧은 nav 값을 쓴다. 긴 제목을 그대로 쓰면
    좁은 컬럼에서 말줄임표로 잘려 무슨 메뉴인지 알 수 없게 된다.
    """
    items = [(f["key"], f"{f['icon']} {f.get('nav', f['title'])}") for f in FEATURES]
    if is_teacher():
        items.append((PAGE_CLASS_BOARD, "🏫 우리 반"))
    items.append((PAGE_NEXT, "🚀 로드맵"))
    items.append((PAGE_MYPAGE, "👤 마이페이지"))
    return items
