# -*- coding: utf-8 -*-
"""
ui/brand.py
로고 에셋 해석 + 브랜드 상수

왜 별도 모듈인가
----------------
로고 파일(assets/logo.png)은 팀이 나중에 교체할 수 있고, 파일이 아직
없을 수도 있다. 화면 코드가 경로를 직접 알면 파일이 없을 때 st.image 가
예외를 던져 **랜딩 화면 전체가 하얗게 죽는다**. 그래서 data/ogq_assets.py 가
스티커에 대해 하는 것과 똑같이, 로고도 "있으면 쓰고 없으면 우아하게 대체"
하는 단일 관문을 둔다.

탐색 우선순위
  1) assets/logo.png  (팀이 넣기로 한 표준 경로)
  2) assets/logo.jpg / .jpeg / .webp / .svg
  3) 없으면 None → 화면은 CSS로 그린 'EMP' 마크로 자동 대체
"""

import base64
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

SERVICE_NAME = "AI Job Pass Finder"
SERVICE_TAGLINE = "학교에서 시장으로 — 마이스터의 등용문을 여는 AI 취업 파트너"
TEAM_NAME = "전북기계공업고등학교 E.M.P"

# 우선순위 순서대로 탐색할 로고 파일명
_LOGO_CANDIDATES = ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp", "logo.svg")

_MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".svg": "image/svg+xml",
}


def logo_path() -> str | None:
    """로고 파일의 절대경로. 없으면 None."""
    for filename in _LOGO_CANDIDATES:
        path = os.path.join(ASSETS_DIR, filename)
        if os.path.exists(path):
            return path
    return None


def logo_data_uri() -> str | None:
    """
    로고를 data URI(base64)로 변환한다.

    st.image() 대신 data URI 를 쓰는 이유: 랜딩 히어로에서 로고를 화면 폭에
    비례해(반응형) 키우려면 CSS 로 제어해야 하는데, st.image(width=...) 는
    픽셀 고정값만 받기 때문에 폰에서 로고가 화면을 뚫고 나간다.
    HTML <img> 로 직접 그리면 max-width:100% 와 clamp() 를 쓸 수 있다.
    """
    path = logo_path()
    if not path:
        return None
    try:
        ext = os.path.splitext(path)[1].lower()
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return f"data:{_MIME.get(ext, 'image/png')};base64,{encoded}"
    except Exception:
        # 파일이 손상돼도 랜딩은 떠야 한다
        return None


def logo_html(max_px: int = 200, min_px: int = 110) -> str:
    """
    반응형 로고 HTML.

    clamp(min, 28vw, max) — 데스크톱에서는 max_px 로 고정되고, 폰에서는
    화면 폭의 28% 로 줄어든다. 미디어쿼리 없이 한 줄로 반응형이 된다.
    로고 파일이 없으면 그라데이션 'EMP' 마크로 대체한다.
    """
    uri = logo_data_uri()
    size = f"clamp({min_px}px, 28vw, {max_px}px)"

    if uri:
        return (
            f'<img src="{uri}" alt="{SERVICE_NAME} 로고" '
            f'style="width:{size}; height:auto; max-width:100%; '
            f'border-radius:22px; display:block; margin:0 auto;" />'
        )

    # 폴백: 로고 파일이 아직 없을 때의 CSS 마크
    return (
        f'<div style="width:{size}; height:{size}; margin:0 auto; border-radius:26px;'
        f'background:linear-gradient(135deg,#3B82F6,#8B5CF6);'
        f'display:flex; align-items:center; justify-content:center;'
        f'font-size:calc({size} * 0.26); font-weight:800; color:#fff;'
        f'letter-spacing:0.04em;">E.M.P</div>'
    )
