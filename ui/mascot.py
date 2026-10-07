# -*- coding: utf-8 -*-
"""
ui/mascot.py
[Phase 4] 마스코트 캐릭터 — 감정을 전하는 단 하나의 컬러 요소

▣ 배치 규칙 (ui/icons.py 와 역할을 나눈다)
   마스코트   = 컬러풀 · **화면당 1곳** · 반기고 축하하고 위로한다
   기능 아이콘 = 미니멀 라인 · 작고 절제 · 의미를 가리킨다
   둘이 한 화면에서 경쟁하면 시선이 분산되므로, 마스코트는 포인트로만 쓴다.

▣ 이미지 해석 순서 (앞에서 찾으면 뒤는 보지 않는다)
   1) assets/mascot/manifest.json  — OGQ API 로 내려받은 원본 PNG (최종 형태)
      scripts/fetch_mascot.py 가 만든다. slots 매핑으로 감정별 낱장을 고른다.
   2) assets/ogq/*.jpg             — 레포에 이미 있던 스티커 (과도기)
      다만 이 파일들은 어두운 회색(RGB 37,41,42) 배경이 붙은 저해상도 크롭이라,
      그대로 올리면 다크 테마 위에 회색 네모가 뜬다. 런타임에 배경을 빼서 쓴다.
   3) 없으면 아무것도 그리지 않는다.
      이모지로 대체하지 않는 이유: 이모지를 걷어내는 것이 이번 작업의 목표다.
      깨진 그림 대신 여백이 낫다.

▣ API 호출은 하지 않는다
   마스코트는 최초 1회 내려받은 정적 파일로만 동작한다. 화면을 그릴 때마다
   API 를 부르면 분당 60회 한도에 금방 걸린다.
"""

import base64
import io
import json
import os

import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASCOT_DIR = os.path.join(BASE_DIR, "assets", "mascot")
MANIFEST_PATH = os.path.join(MASCOT_DIR, "manifest.json")
LEGACY_DIR = os.path.join(BASE_DIR, "assets", "ogq")

# 레거시 스티커의 배경색 (측정값). 이 색 근처를 투명으로 뺀다.
LEGACY_BG = (37, 41, 42)
LEGACY_TOLERANCE = 26

# 감정 슬롯 → 과도기 레거시 파일 매핑
_LEGACY_SLOTS = {
    "welcome": "ogq_hello.jpg",
    "celebrate": "ogq_clap.jpg",
    "cheer": "ogq_cheer.jpg",
    "comfort": "ogq_comfort.jpg",
    "thinking": "ogq_thinking.jpg",
    "stamp": "ogq_stamp.jpg",
    "encourage": "ogq_encourage.jpg",
    "thanks": "ogq_thanks.jpg",
}

SLOT_NAMES = tuple(_LEGACY_SLOTS)


# ------------------------------------------------------------
# 매니페스트
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_manifest(mtime: float) -> dict:
    """mtime 을 캐시 키에 넣어, 마스코트를 새로 받으면 자동으로 다시 읽는다."""
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def manifest() -> dict:
    if not os.path.exists(MANIFEST_PATH):
        return {}
    try:
        return _load_manifest(os.path.getmtime(MANIFEST_PATH))
    except Exception:
        return {}


def is_api_mascot() -> bool:
    """OGQ API 로 받은 마스코트를 쓰고 있는가."""
    return bool(manifest().get("files"))


def credit() -> str:
    """출처 표기 문구. 화면 하단이나 캡션에 쓴다."""
    data = manifest()
    if data.get("files"):
        title = data.get("title") or "OGQ 스티커"
        creator = data.get("creator") or "OGQ"
        return f"마스코트: {title} · {creator} · NAVER OGQ마켓"
    return "마스코트: NAVER OGQ마켓 캐릭터 스티커"


# ------------------------------------------------------------
# 파일 해석
# ------------------------------------------------------------
def _api_path(slot: str) -> str | None:
    data = manifest()
    files = data.get("files") or []
    if not files:
        return None

    asset_dir = os.path.join(MASCOT_DIR, data.get("assetId", ""))
    slots = data.get("slots") or {}

    # 1순위: 매니페스트에 지정된 슬롯 매핑
    name = slots.get(slot)
    if name and name in files:
        path = os.path.join(asset_dir, name)
        if os.path.exists(path):
            return path

    # 2순위: 매핑이 없으면 첫 번째 낱장을 공통으로 쓴다
    #        (감정별 구분은 못 하지만 캐릭터는 일관되게 나온다)
    path = os.path.join(asset_dir, files[0])
    return path if os.path.exists(path) else None


def _legacy_path(slot: str) -> str | None:
    name = _LEGACY_SLOTS.get(slot)
    if not name:
        return None
    path = os.path.join(LEGACY_DIR, name)
    return path if os.path.exists(path) else None


# ------------------------------------------------------------
# 레거시 스티커 배경 제거
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _keyed_png(path: str, mtime: float) -> bytes | None:
    """
    회색 배경(RGB 37,41,42)을 투명하게 만든다.

    단순 임계값으로 자르면 캐릭터 외곽선이 계단처럼 남는다. 배경색과의 거리로
    알파를 부드럽게 깎아 경계를 자연스럽게 했다.
    """
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return None

    try:
        im = Image.open(path).convert("RGBA")
        arr = np.asarray(im).astype(np.float32)
    except Exception:
        return None

    rgb = arr[..., :3]
    bg = np.array(LEGACY_BG, dtype=np.float32)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=-1))

    # 거리 0 → 완전 투명, tolerance 이상 → 완전 불투명 (그 사이는 선형)
    alpha = np.clip(dist / LEGACY_TOLERANCE, 0.0, 1.0)
    out = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)

    result = Image.fromarray(out, mode="RGBA")
    bbox = result.getbbox()
    if bbox:
        result = result.crop(bbox)

    buffer = io.BytesIO()
    result.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def data_uri(slot: str) -> str | None:
    """슬롯에 해당하는 이미지를 data URI 로 반환한다. 없으면 None."""
    path = _api_path(slot)
    if path:
        # API 로 받은 PNG 는 이미 투명 배경이므로 그대로 쓴다
        try:
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
        except Exception:
            pass

    path = _legacy_path(slot)
    if path:
        try:
            keyed = _keyed_png(path, os.path.getmtime(path))
        except Exception:
            keyed = None
        if keyed:
            return "data:image/png;base64," + base64.b64encode(keyed).decode("ascii")
    return None


def available(slot: str = "welcome") -> bool:
    return data_uri(slot) is not None


# ------------------------------------------------------------
# 렌더링
# ------------------------------------------------------------
def html(slot: str, size: int = 110, min_size: int | None = None) -> str:
    """
    마스코트 <img> HTML. 이미지가 없으면 빈 문자열(아무것도 그리지 않음).

    clamp() 로 폰에서 자동 축소된다 — st.image 는 픽셀 고정이라 좁은 화면에서
    레이아웃을 밀어낸다.
    """
    uri = data_uri(slot)
    if not uri:
        return ""
    min_size = min_size or max(56, int(size * 0.62))
    width = f"clamp({min_size}px, 18vw, {size}px)"
    return (
        f'<img src="{uri}" alt="" class="mjp-mascot" '
        f'style="width:{width}; height:auto; display:block;" />'
    )


def render(slot: str, size: int = 110, caption: str = "") -> None:
    """마스코트를 단독으로 그린다."""
    markup = html(slot, size)
    if not markup:
        return
    st.markdown(
        f'<div style="display:flex; flex-direction:column; align-items:center; gap:6px;">'
        f'{markup}'
        + (f'<div class="mjp-muted" style="text-align:center;">{caption}</div>' if caption else "")
        + '</div>',
        unsafe_allow_html=True,
    )


def speech(slot: str, message: str, tone: str = "brand", size: int = 92) -> None:
    """
    마스코트 + 말풍선. 축하·환영·위로처럼 '감정을 전하는' 자리에 쓴다.

    tone: brand | success | warn — 말풍선 테두리 색만 달라진다.
    """
    from ui.theme import BRAND, CARD, CARD_BORDER, GOLD, GREEN, TEXT

    color = {"brand": BRAND, "success": GREEN, "warn": GOLD}.get(tone, BRAND)
    markup = html(slot, size)

    if not markup:
        # 마스코트가 없으면 말풍선만 (문구는 전달돼야 한다)
        st.markdown(
            f'<div class="mjp-card" style="border-left:3px solid {color};">'
            f'<div style="color:{TEXT}; line-height:1.6;">{message}</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"""
    <div class="mjp-mascot-row" style="display:flex; align-items:center; gap:14px;
                background:{CARD}; border:1px solid {CARD_BORDER};
                border-left:3px solid {color}; border-radius:14px;
                padding:14px 18px; margin-bottom:16px; flex-wrap:wrap;">
        <div style="flex:none;">{markup}</div>
        <div style="flex:1; min-width:180px; color:{TEXT}; font-size:var(--mjp-small);
                    line-height:1.65;">{message}</div>
    </div>
    """, unsafe_allow_html=True)
