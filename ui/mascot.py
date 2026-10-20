# -*- coding: utf-8 -*-
"""
ui/mascot.py
[Phase 4] 마스코트 캐릭터 — 감정을 전하는 단 하나의 컬러 요소

▣ 배치 규칙 (ui/icons.py 와 역할을 나눈다)
   마스코트   = 컬러풀 · **화면당 1곳** · 반기고 축하하고 위로한다
   기능 아이콘 = 미니멀 라인 · 작고 절제 · 의미를 가리킨다
   둘이 한 화면에서 경쟁하면 시선이 분산되므로, 마스코트는 포인트로만 쓴다.

▣ 이미지 해석 순서 (앞에서 찾으면 뒤는 보지 않는다)
   1) assets/mascot/manifest.json  — 대회 공식 OGQ API 로 내려받은 PNG
      scripts/fetch_mascot.py 가 만든다. slots 매핑으로 감정별 낱장을 고른다.
      (지금 저장소에는 없다 — 내려받은 적이 없다)
   2) 없으면 아무것도 그리지 않는다(빈 영역). 말풍선은 문구만 보여준다.

▣ [심사대응] assets/ogq/*.jpg 11장은 삭제했다
   OGQ마켓 스티커를 이용 허락 없이 캡처해 쓰던 이미지였다. 그 파일을 읽고
   배경을 깎아 쓰던 과도기 코드도 함께 지웠다(README '자산과 라이선스' 정정 참고).

▣ API 호출은 하지 않는다
   마스코트는 최초 1회 내려받은 정적 파일로만 동작한다. 화면을 그릴 때마다
   API 를 부르면 분당 60회 한도에 금방 걸린다.
"""

import base64
import json
import os

import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASCOT_DIR = os.path.join(BASE_DIR, "assets", "mascot")
MANIFEST_PATH = os.path.join(MASCOT_DIR, "manifest.json")

# 화면이 쓰는 감정 슬롯 이름 (매니페스트의 slots 키와 같다)
SLOT_NAMES = ("welcome", "celebrate", "cheer", "comfort", "thinking", "stamp", "encourage", "thanks")


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
    """출처 표기 문구. 공식 API 로 받은 이미지가 있을 때만, 매니페스트 값 그대로."""
    data = manifest()
    if data.get("files"):
        title = data.get("title") or ""
        creator = data.get("creator") or ""
        return f"마스코트: {title} · {creator}".strip(" ·")
    return ""


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

    v2: 회색 면 한 장 (테두리·색띠 없음). tone 은 호환용으로 남겼고, 성공·주의
    톤일 때만 면을 연한 상태색으로 바꾼다.
    """
    from ui.theme import CARD, GOLD_SOFT, GREEN_SOFT

    bg = {"success": GREEN_SOFT, "warn": GOLD_SOFT}.get(tone, CARD)
    markup = html(slot, size)

    if not markup:
        # 마스코트가 없으면 말풍선만 (문구는 전달돼야 한다)
        st.markdown(
            f'<div class="mjp-speech" style="background:{bg};">'
            f'<div class="mjp-speech-text">{message}</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"""
    <div class="mjp-mascot-row mjp-speech" style="background:{bg};">
        <div style="flex:none;">{markup}</div>
        <div class="mjp-speech-text">{message}</div>
    </div>
    """, unsafe_allow_html=True)
