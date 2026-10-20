# -*- coding: utf-8 -*-
"""
data/ogq_assets.py
점수 구간 → 반응 매핑

감정 표현과 이미지 해석은 ui/mascot.py 로 일원화되었다. 여기 남은 것은 두 가지뿐이다.
  · 점수 → 반응 키 매핑 (sticker_key_for_score)
  · 구간별 판정 문구 (SCORE_STICKER_MESSAGES)

[심사대응] assets/ogq/*.jpg 스티커 11장과 그 경로 표(OGQ_LOCAL_FILES · sticker())는
삭제했다. 이용 허락 없이 캡처해 쓰던 이미지였다. 파일 이름은 기존 호출부 호환을
위해 그대로 둔다(ogq_assets 라는 이름은 점수 반응 키를 가리킨다).
"""

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
