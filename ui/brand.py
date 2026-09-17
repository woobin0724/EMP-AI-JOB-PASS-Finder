# -*- coding: utf-8 -*-
"""
ui/brand.py
브랜드 락업(로고 + 워드마크) + 실제 로고 파일의 다크 테마 블렌딩

▣ 왜 로고를 '그대로' 쓰지 않는가
   팀 로고 원본은 **밝은 흰 배경 위에 짙은 네이비 잉크**로 그려진 래스터
   이미지다. 우리 앱 배경은 #0A0E17 이다. 여기서 선택지는 셋이었다.

     (1) 그대로 얹는다        → 흰 사각형 판이 그대로 떠서 '붙여넣은 티'가 난다
     (2) 흰 배경만 투명 처리  → 이번엔 짙은 네이비 잉크가 어두운 배경에 묻혀
                                형체가 사라진다
     (3) 밝기를 반전해 브랜드 컬러 램프로 다시 칠한다  ← 채택

   (3)은 로고의 '형태'는 100% 보존하면서 '명도 관계'만 다크 테마에 맞게
   뒤집는 방식이다. 흰 배경은 투명해지고, 어둡던 잉크는 밝은 블루로 빛난다.
   로고를 화면에 올려놓는 게 아니라 화면 안으로 녹여 넣는다.

   로고 파일이 아직 없으면 ui/emblem.py 의 벡터 엠블럼이 대신 쓰인다.
   (엠블럼 역시 원본 로고를 요소 단위로 분해해 다시 그린 것이다.)

▣ 의존성
   Pillow 와 numpy 는 Streamlit / pandas 의 필수 의존성이라 배포 환경에
   항상 존재한다. 그래도 import 실패 시 원본 이미지로 조용히 내려간다.
"""

import base64
import io
import os

import streamlit as st

from ui.emblem import INK_DEEP, INK_LIGHT, INK_MID, emblem_svg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

SERVICE_NAME = "AI Job Pass Finder"
SERVICE_TAGLINE = "학교에서 시장으로 — 마이스터의 등용문을 여는 AI 취업 파트너"
TEAM_NAME = "전북기계공업고등학교 E.M.P"
TEAM_FULL = "EMPLOYMENT MEISTER PARTNER"

# 우선순위 순서대로 탐색할 로고 파일명
_LOGO_CANDIDATES = ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp")

# False 로 두면 블렌딩 없이 원본 이미지를 그대로 쓴다 (디버깅용)
LOGO_BLEND = True

# 블렌딩 후 최대 변 길이. 로고를 원본 해상도 그대로 base64 로 인라인하면
# 매 rerun 마다 수 MB 를 브라우저로 밀어넣게 되므로 상한을 둔다.
_MAX_EDGE = 560


def logo_path() -> str | None:
    """로고 파일의 절대경로. 없으면 None."""
    for filename in _LOGO_CANDIDATES:
        path = os.path.join(ASSETS_DIR, filename)
        if os.path.exists(path):
            return path
    return None


def _hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


@st.cache_data(show_spinner=False)
def _blend_logo(path: str, mtime: float, size: int) -> bytes | None:
    """
    밝은 배경의 로고를 다크 테마용으로 재착색한다.

    캐시 키에 mtime 을 포함시켜, 팀원이 로고 파일을 교체하면 자동으로 다시
    처리되게 했다 (size 는 현재 미사용이지만 캐시 분리를 위해 남겨둔다).

    반환값: PNG 바이트 | None(처리 불가·불필요)
    """
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return None

    try:
        im = Image.open(path).convert("RGBA")
        im.thumbnail((_MAX_EDGE, _MAX_EDGE), Image.LANCZOS)
        arr = np.asarray(im).astype(np.float32)
    except Exception:
        return None

    rgb, alpha0 = arr[..., :3], arr[..., 3] / 255.0
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    # 테두리 밝기로 '밝은 배경 로고'인지 판정한다.
    # 이미 어두운 배경용으로 만들어진 이미지라면 건드리지 않는 게 맞다.
    border = np.concatenate([lum[0, :], lum[-1, :], lum[:, 0], lum[:, -1]])
    if float(np.median(border)) < 150.0:
        return None

    # 잉크 강도 = 밝기의 반전. 아래 두 줄이 이 함수의 핵심이다.
    ink = (255.0 - lum) / 255.0
    # 0.10 미만은 흰 배경의 JPEG 노이즈이므로 잘라내고, 나머지를 0~1 로 재분포
    ink = np.clip((ink - 0.10) / 0.80, 0.0, 1.0)
    ink = ink ** 0.9          # 중간톤(가는 회로선)을 조금 살려준다

    out_alpha = ink * alpha0

    # 세로 그라데이션으로 재착색 — 엠블럼(ui/emblem.py)과 같은 컬러 램프를 써서
    # 로고와 엠블럼이 한 화면에 같이 나와도 이질감이 없게 한다.
    height = arr.shape[0]
    t = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    c_light = np.array(_hex_to_rgb(INK_LIGHT), dtype=np.float32)
    c_mid = np.array(_hex_to_rgb(INK_MID), dtype=np.float32)
    c_deep = np.array(_hex_to_rgb(INK_DEEP), dtype=np.float32)

    # 0.0~0.55 구간: light→mid, 0.55~1.0 구간: mid→deep
    upper = t / 0.55
    lower = (t - 0.55) / 0.45
    ramp = np.where(
        t < 0.55,
        c_light[None, None, :] + (c_mid - c_light)[None, None, :] * np.clip(upper, 0, 1)[..., None],
        c_mid[None, None, :] + (c_deep - c_mid)[None, None, :] * np.clip(lower, 0, 1)[..., None],
    )
    ramp = np.broadcast_to(ramp, rgb.shape)

    # 진한 잉크일수록 밝은 쪽으로 살짝 끌어올려 획이 또렷하게 보이도록
    highlight = (ink[..., None] ** 2) * 26.0
    out_rgb = np.clip(ramp + highlight, 0, 255)

    out = np.dstack([out_rgb, out_alpha * 255.0]).astype(np.uint8)
    result = Image.fromarray(out, mode="RGBA")

    # 투명해진 여백을 잘라내 로고가 레이아웃에서 실제보다 작아 보이지 않게 한다
    bbox = result.getbbox()
    if bbox:
        result = result.crop(bbox)

    buffer = io.BytesIO()
    result.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def logo_data_uri() -> str | None:
    """
    화면에 바로 넣을 수 있는 로고 data URI.

    st.image() 대신 data URI + <img> 를 쓰는 이유: 히어로에서 로고를 화면 폭에
    비례해(clamp) 키우려면 CSS 제어가 필요한데 st.image(width=...) 는 픽셀
    고정값만 받아 폰에서 화면을 뚫고 나간다.
    """
    path = logo_path()
    if not path:
        return None

    if LOGO_BLEND:
        try:
            blended = _blend_logo(path, os.path.getmtime(path), _MAX_EDGE)
        except Exception:
            blended = None
        if blended:
            return "data:image/png;base64," + base64.b64encode(blended).decode("ascii")

    # 블렌딩 불가(이미 어두운 배경 로고 등) → 원본 그대로
    try:
        ext = os.path.splitext(path)[1].lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".webp": "image/webp"}.get(ext, "image/png")
        with open(path, "rb") as f:
            return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return None


def logo_html(max_px: int = 200, min_px: int = 110, detail: str = "full") -> str:
    """
    반응형 브랜드 마크.

    clamp(min, 28vw, max) — 데스크톱에서는 max_px 로 고정되고 폰에서는 화면 폭의
    28% 로 줄어든다. 미디어쿼리 없이 한 줄로 반응형이 된다.

    로고 파일이 있으면 블렌딩된 로고를, 없으면 벡터 엠블럼을 그린다.
    둘 다 같은 컬러 램프를 쓰므로 어느 쪽이 나와도 화면 톤이 유지된다.
    """
    size = f"clamp({min_px}px, 28vw, {max_px}px)"
    uri = logo_data_uri()

    if uri:
        return (
            f'<img src="{uri}" alt="{TEAM_FULL} 로고" class="mjp-logo" '
            f'style="width:{size};" />'
        )

    return (
        f'<div class="mjp-logo mjp-logo-svg" style="width:{size}; height:{size};">'
        f'{emblem_svg(max_px, detail=detail)}</div>'
    )


def wordmark_html(align: str = "center", size: str = "lg") -> str:
    """
    워드마크 락업 — 서비스명 + 팀 풀네임.

    원본 로고 하단의 'EMPLOYMENT MEISTER PARTNER' 레터스페이싱을 그대로
    타이포 요소로 가져왔다. 로고와 본문을 잇는 다리 역할을 한다.
    """
    name_size = "17px" if size == "lg" else "14px"
    sub_size = "10px" if size == "lg" else "9px"
    return f"""
    <div style="text-align:{align};">
        <div style="font-size:{name_size}; font-weight:800; color:#E7EAF0;
                    letter-spacing:-0.01em; line-height:1.25;">{SERVICE_NAME}</div>
        <div style="font-size:{sub_size}; font-weight:700; color:{INK_MID};
                    letter-spacing:0.22em; margin-top:3px;">{TEAM_FULL}</div>
    </div>"""
