# -*- coding: utf-8 -*-
"""
data/ogq_assets.py
점수 구간 → 반응 매핑 (레거시 스티커 경로 포함)

[Phase 4 이후]
감정 표현과 이미지 해석은 ui/mascot.py 로 일원화되었다. 이 모듈에 있던
이모지 폴백 테이블은 **삭제**했다 — 이모지를 걷어내는 것이 Phase 4 의
목표였고, 폴백이 남아 있으면 어딘가에서 다시 이모지가 새어 나온다.

여기 남은 것은 두 가지뿐이다.
  · 점수 → 반응 키 매핑 (sticker_key_for_score)
  · 구간별 판정 문구 (SCORE_STICKER_MESSAGES)
레거시 스티커 파일 경로는 ui/mascot.py 가 과도기 폴백으로 참조한다.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OGQ_DIR = os.path.join(BASE_DIR, "assets", "ogq")

# 스티커가 판매되는 OGQ마켓 (출처 표기용)
OGQ_MARKET_URL = "https://ogqmarket.naver.com/"

# 레거시 스티커 파일명 (ui/mascot.py 의 과도기 폴백이 참조)
OGQ_LOCAL_FILES = {
    "success":   "ogq_success.jpg",
    "cheer":     "ogq_cheer.jpg",
    "comfort":   "ogq_comfort.jpg",
    "stamp":     "ogq_stamp.jpg",
    "clap":      "ogq_clap.jpg",
    "hello":     "ogq_hello.jpg",
    "encourage": "ogq_encourage.jpg",
    "thinking":  "ogq_thinking.jpg",
    "thanks":    "ogq_thanks.jpg",
    "rest":      "ogq_rest.jpg",
    "sheet":     "ogq_sheet.jpg",
}

# 점수 구간별 판정 문구
SCORE_STICKER_MESSAGES = {
    "success": ("합격 안정권", "이 정도면 자신 있게 지원해도 좋아요. 남은 건 면접 실전 연습!"),
    "cheer":   ("분발 필요",   "방향은 맞습니다. 자격증 1개만 더 채우면 안정권까지 금방이에요."),
    "comfort": ("보완 시급",   "지금 점수는 출발선일 뿐입니다. 로드맵 1단계부터 같이 채워봐요."),
}


def sticker_key_for_score(score: float) -> str:
    """점수(100점 만점) → 반응 키. 80↑ 축하 / 50~79 격려 / 50↓ 위로."""
    if score >= 80:
        return "success"
    if score >= 50:
        return "cheer"
    return "comfort"


def sticker(key: str):
    """[하위 호환] 레거시 스티커의 로컬 경로. 없으면 None."""
    filename = OGQ_LOCAL_FILES.get(key)
    if not filename:
        return None
    path = os.path.join(OGQ_DIR, filename)
    return path if os.path.exists(path) else None


def available() -> bool:
    return any(sticker(k) for k in OGQ_LOCAL_FILES)
