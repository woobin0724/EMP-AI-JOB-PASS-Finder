# -*- coding: utf-8 -*-
"""
services/auth.py
[Phase 1-2] 로그인 — 카카오 / 네이버 / 구글 OAuth2 + 게스트모드

▣ 설계 결론: "UI만 만들고 준비중" 이 아니라 "배선을 다 깔고 스위치만 남긴다"
   -------------------------------------------------------------------------
   OAuth 의 진짜 병목은 코드가 아니라 **행정 절차**다.
     · 카카오  : 개발자 콘솔 앱 등록 → 카카오 로그인 활성화 → 동의항목 설정
     · 네이버  : 애플리케이션 등록 → 검수 (OIDC 디스커버리 미지원)
     · 구글    : OAuth 동의화면 구성 (미검증 앱은 테스트 사용자 100명 제한)
   그리고 셋 다 **Redirect URI 가 배포 URL 과 문자 단위로 일치**해야 한다.

   그래서 이 모듈은 Authorization Code 흐름을 완전히 구현해 두고,
   st.secrets 에 해당 제공자의 CLIENT_ID 가 있는지로 **런타임에 자동 분기**한다.

       secrets 에 KAKAO_CLIENT_ID 있음  → 진짜 카카오 로그인 동작 (코드 수정 0줄)
       없음                              → 버튼이 '🔒 준비중' 으로 자동 전환

   대회 직전에 콘솔에서 키만 발급받아 secrets.toml 에 붙여넣으면
   재배포만으로 소셜 로그인이 켜진다.

▣ 보안
   client_secret 은 절대 코드/URL/로그에 남기지 않고 st.secrets 에서만 읽는다.
   CSRF 방어용 state 는 매 요청 새로 만들어 세션에 보관하고, 콜백에서 대조한다.
"""

import secrets as pysecrets
import string
import urllib.parse

import requests
import streamlit as st

# ------------------------------------------------------------
# 제공자 스펙
# ------------------------------------------------------------
PROVIDERS = {
    "kakao": {
        "label": "카카오로 시작하기",
        "icon": "💬",
        "bg": "#FEE500", "fg": "#191600", "border": "#FEE500",
        "authorize_url": "https://kauth.kakao.com/oauth/authorize",
        "token_url": "https://kauth.kakao.com/oauth/token",
        "profile_url": "https://kapi.kakao.com/v2/user/me",
        "scope": "profile_nickname",
        "secret_prefix": "KAKAO",
        "secret_required": False,   # 카카오는 client_secret 이 선택 설정
        "console": "https://developers.kakao.com",
    },
    "naver": {
        "label": "네이버로 시작하기",
        "icon": "🟩",
        "bg": "#03C75A", "fg": "#FFFFFF", "border": "#03C75A",
        "authorize_url": "https://nid.naver.com/oauth2.0/authorize",
        "token_url": "https://nid.naver.com/oauth2.0/token",
        "profile_url": "https://openapi.naver.com/v1/nid/me",
        "scope": "",
        "secret_prefix": "NAVER",
        "secret_required": True,
        "console": "https://developers.naver.com",
    },
    "google": {
        "label": "Google로 시작하기",
        "icon": "🔵",
        "bg": "#FFFFFF", "fg": "#1F2328", "border": "#FFFFFF",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "profile_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
        "secret_prefix": "GOOGLE",
        "secret_required": True,
        "console": "https://console.cloud.google.com/apis/credentials",
    },
}

HTTP_TIMEOUT = 12
GUEST_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


# ------------------------------------------------------------
# secrets 접근 (secrets.toml 이 없어도 죽지 않는다)
# ------------------------------------------------------------
def safe_secret(key: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(key, default) or default).strip()
    except Exception:
        return default


def client_id(provider: str) -> str:
    return safe_secret(f"{PROVIDERS[provider]['secret_prefix']}_CLIENT_ID")


def client_secret(provider: str) -> str:
    return safe_secret(f"{PROVIDERS[provider]['secret_prefix']}_CLIENT_SECRET")


def redirect_uri() -> str:
    """
    OAuth 콜백 주소.

    각 개발자 콘솔에 등록한 값과 **완전히 동일한 문자열**이어야 한다.
    배포 URL 이 확정되면 secrets.toml 에 아래 한 줄만 넣으면 된다.
        OAUTH_REDIRECT_URI = "https://<앱주소>.streamlit.app"
    로컬 개발 시에는 http://localhost:8501 이 기본값으로 쓰인다.
    """
    return safe_secret("OAUTH_REDIRECT_URI", "http://localhost:8501")


def is_configured(provider: str) -> bool:
    """이 제공자로 실제 로그인이 가능한 상태인가."""
    spec = PROVIDERS.get(provider)
    if not spec:
        return False
    if not client_id(provider):
        return False
    if spec["secret_required"] and not client_secret(provider):
        return False
    return True


def configured_providers() -> list[str]:
    return [p for p in PROVIDERS if is_configured(p)]


def any_oauth_ready() -> bool:
    return bool(configured_providers())


# ------------------------------------------------------------
# 1단계: 인가 URL 생성
# ------------------------------------------------------------
def _new_state() -> str:
    """CSRF 방어용 난수 state."""
    return pysecrets.token_urlsafe(24)


def build_authorize_url(provider: str) -> str:
    """
    사용자를 보낼 인가 URL 을 만든다.
    state 는 세션에 저장해 두고 콜백에서 대조한다.
    """
    spec = PROVIDERS[provider]
    state = _new_state()
    st.session_state["_oauth_state"] = state
    st.session_state["_oauth_provider"] = provider

    params = {
        "response_type": "code",
        "client_id": client_id(provider),
        "redirect_uri": redirect_uri(),
        "state": state,
    }
    if spec["scope"]:
        params["scope"] = spec["scope"]

    return f"{spec['authorize_url']}?{urllib.parse.urlencode(params)}"


# ------------------------------------------------------------
# 2단계: 콜백 처리 (code → token → profile)
# ------------------------------------------------------------
def _exchange_token(provider: str, code: str) -> str:
    """인가 코드를 액세스 토큰으로 교환한다. 실패 시 예외."""
    spec = PROVIDERS[provider]
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id(provider),
        "redirect_uri": redirect_uri(),
        "code": code,
    }
    csecret = client_secret(provider)
    if csecret:
        data["client_secret"] = csecret

    res = requests.post(
        spec["token_url"], data=data, timeout=HTTP_TIMEOUT,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
    )
    res.raise_for_status()
    payload = res.json()

    token = payload.get("access_token")
    if not token:
        raise ValueError(f"토큰 응답에 access_token 이 없습니다: {payload.get('error_description') or payload}")
    return token


def _fetch_profile(provider: str, token: str) -> dict:
    """
    액세스 토큰으로 프로필을 조회하고 제공자별 응답 구조를 공통 형태로 정규화한다.
    반환값: {"id": str, "name": str, "email": str}
    """
    spec = PROVIDERS[provider]
    res = requests.get(
        spec["profile_url"],
        headers={"Authorization": f"Bearer {token}"},
        timeout=HTTP_TIMEOUT,
    )
    res.raise_for_status()
    data = res.json()

    if provider == "kakao":
        account = data.get("kakao_account") or {}
        profile = account.get("profile") or {}
        return {
            "id": str(data.get("id", "")),
            "name": profile.get("nickname", "") or "카카오 사용자",
            "email": account.get("email", "") or "",
        }

    if provider == "naver":
        # 네이버는 실제 데이터가 response 키 안에 한 겹 더 들어 있다
        response = data.get("response") or {}
        return {
            "id": str(response.get("id", "")),
            "name": response.get("nickname") or response.get("name") or "네이버 사용자",
            "email": response.get("email", "") or "",
        }

    # google
    return {
        "id": str(data.get("id", "")),
        "name": data.get("name", "") or "Google 사용자",
        "email": data.get("email", "") or "",
    }


def consume_oauth_callback() -> tuple[dict | None, str]:
    """
    URL 에 ?code=... 가 붙어 돌아왔는지 확인하고, 있으면 로그인을 완성한다.

    앱 부팅 시 매 rerun 마다 호출해도 안전하도록, 처리 후에는 query_params 에서
    code/state 를 즉시 제거한다(같은 코드를 두 번 교환하면 제공자가 거부한다).

    반환값: (사용자 dict | None, 오류 메시지)
    """
    try:
        params = st.query_params
        code = params.get("code")
        state = params.get("state")
    except Exception:
        return None, ""

    if not code:
        return None, ""

    provider = st.session_state.get("_oauth_provider", "")
    expected_state = st.session_state.get("_oauth_state", "")

    # 사용한 파라미터는 무조건 URL 에서 제거 (재사용·재교환 방지)
    for key in ("code", "state"):
        try:
            if key in st.query_params:
                del st.query_params[key]
        except Exception:
            pass

    if not provider:
        return None, "로그인 세션이 만료되었습니다. 다시 시도해주세요."
    if expected_state and state != expected_state:
        return None, "보안 검증(state)에 실패했습니다. 다시 로그인해주세요."

    try:
        token = _exchange_token(provider, code)
        profile = _fetch_profile(provider, token)
    except requests.HTTPError as exc:
        return None, f"{PROVIDERS[provider]['label']} 인증에 실패했습니다. (HTTP {exc.response.status_code if exc.response else '?'})"
    except Exception as exc:  # noqa: BLE001 — 로그인 실패가 앱을 죽이면 안 된다
        return None, f"로그인 처리 중 문제가 발생했습니다: {type(exc).__name__}"
    finally:
        st.session_state.pop("_oauth_state", None)

    if not profile.get("id"):
        return None, "프로필 정보를 받아오지 못했습니다."

    return {
        "user_id": f"{provider}_{profile['id']}",
        "provider": provider,
        "display_name": profile["name"],
        "email": profile["email"],
    }, ""


# ------------------------------------------------------------
# 게스트모드 — 키가 하나도 없어도 서비스 전체가 동작해야 한다
# ------------------------------------------------------------
def new_guest_code(length: int = 6) -> str:
    return "".join(pysecrets.choice(GUEST_CODE_ALPHABET) for _ in range(length))


def guest_login(nickname: str = "") -> dict:
    """
    게스트 계정을 만든다.

    게스트에게도 고유 코드를 부여하는 이유: 게스트 ID 가 접속할 때마다 새로
    생기면 '재방문 유저는 역할 선택을 건너뛴다'(Phase 1-3 요구사항)가
    성립하지 않는다. 화면에 '이어하기 코드'로 노출하고, 로그인 화면에서
    그 코드를 입력하면 같은 계정으로 돌아올 수 있게 한다.
    """
    code = new_guest_code()
    return {
        "user_id": f"guest_{code}",
        "provider": "guest",
        "display_name": nickname.strip() or f"게스트 {code}",
        "email": "",
        "resume_code": code,
    }


def resume_code_to_user_id(code: str) -> str:
    """이어하기 코드 → 게스트 user_id."""
    cleaned = "".join(ch for ch in (code or "").upper() if ch in string.ascii_uppercase + string.digits)
    return f"guest_{cleaned}" if cleaned else ""


# ------------------------------------------------------------
# 안내 문구
# ------------------------------------------------------------
def setup_hint(provider: str) -> str:
    """키가 없을 때 개발자에게 보여줄 설정 안내."""
    spec = PROVIDERS[provider]
    prefix = spec["secret_prefix"]
    need_secret = " / " + f"{prefix}_CLIENT_SECRET" if spec["secret_required"] else ""
    return (
        f"`.streamlit/secrets.toml` 에 `{prefix}_CLIENT_ID`{need_secret} 를 등록하면 "
        f"이 버튼이 즉시 실제 로그인으로 전환됩니다. (콘솔: {spec['console']})"
    )


def status_table() -> list[dict]:
    """설정 현황 표 — 로그인 화면 하단 개발자 안내용."""
    rows = []
    for key, spec in PROVIDERS.items():
        rows.append({
            "제공자": spec["label"].replace("로 시작하기", "").replace(" 시작하기", ""),
            "상태": "✅ 연동됨" if is_configured(key) else "🔒 키 미등록",
            "필요한 secrets 키": (
                f"{spec['secret_prefix']}_CLIENT_ID"
                + (f", {spec['secret_prefix']}_CLIENT_SECRET" if spec["secret_required"] else "")
            ),
        })
    return rows
