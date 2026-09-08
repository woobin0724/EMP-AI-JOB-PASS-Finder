# -*- coding: utf-8 -*-
"""
data/ogq_assets.py
네이버 OGQ마켓 캐릭터 스티커 에셋 매핑 모듈

설계 원칙
---------
1) 앱 코드 어디에서도 파일 경로를 하드코딩하지 않는다. 항상 `sticker(key)` 로
   접근하고, 스티커 교체는 이 파일의 매핑 표만 수정하면 되도록 한다.
2) 로컬 파일(assets/ogq/*.jpg)이 1순위, OGQ마켓 웹 URL이 2순위, 둘 다 없으면
   이모지 대체(graceful degradation)로 내려간다. 즉 이미지가 하나도 없어도
   앱은 절대 죽지 않는다.
3) 팀원이 나중에 OGQ 상품 페이지의 이미지 주소를 받으면 OGQ_WEB_URLS 딕셔너리에
   그대로 붙여넣기만 하면 자동으로 웹 이미지가 우선 적용된다(USE_WEB_FIRST=True).

※ 저작권 안내
   OGQ 스티커는 창작자에게 저작권이 있는 상품입니다. 본 프로젝트는 교내
   프로젝트/시연 목적의 사용이며, 외부 배포 시에는 반드시 창작자 이용 허락 또는
   OGQ마켓 라이선스 정책을 확인해야 합니다.
"""

import os

# 프로젝트 루트 (= 이 파일의 상위 디렉터리)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OGQ_DIR = os.path.join(BASE_DIR, "assets", "ogq")

# 스티커가 판매되는 OGQ마켓 상품 페이지 (출처 표기용)
OGQ_MARKET_URL = "https://ogqmarket.naver.com/"

# ------------------------------------------------------------
# 1) 로컬 파일 매핑 (assets/ogq/ 아래 파일명)
# ------------------------------------------------------------
OGQ_LOCAL_FILES = {
    "success":   "ogq_success.jpg",    # 🍀 네잎클로버 "축하해요"   → 80점 이상
    "cheer":     "ogq_cheer.jpg",      # 📣 응원 술 "화이팅"        → 50~79점
    "comfort":   "ogq_comfort.jpg",    # 💗 하트 안기 "사랑해"      → 50점 미만
    "stamp":     "ogq_stamp.jpg",      # ⭐ 별점 스탬프             → 로드맵 완료 도장
    "clap":      "ogq_clap.jpg",       # 👏 "짝짝" 박수            → 전 단계 완주
    "hello":     "ogq_hello.jpg",      # 👋 "안녕!"                → 헤더/사이드바 인사
    "encourage": "ogq_encourage.jpg",  # 💪 "잘할수있어"           → 보조 격려
    "thinking":  "ogq_thinking.jpg",   # ❓ 물음표                 → 미입력/안내 상태
    "thanks":    "ogq_thanks.jpg",     # 🙇 "감사합니다"           → 향후 로드맵 탭
    "rest":      "ogq_rest.jpg",       # 😴 "잘자"                 → 휴식/보류 기능
    "sheet":     "ogq_sheet.jpg",      # 🗂 스티커 전체 시트        → 소개용
}

# ------------------------------------------------------------
# 2) 웹 URL 매핑 (OGQ마켓/이미지 호스팅 주소를 받으면 여기에 채워 넣기)
#    값이 빈 문자열이면 자동으로 로컬 파일을 사용한다.
# ------------------------------------------------------------
OGQ_WEB_URLS = {
    "success":   "",
    "cheer":     "",
    "comfort":   "",
    "stamp":     "",
    "clap":      "",
    "hello":     "",
    "encourage": "",
    "thinking":  "",
    "thanks":    "",
    "rest":      "",
    "sheet":     "",
}

# True 로 두면 URL이 채워진 키에 한해 웹 이미지를 우선 사용한다.
USE_WEB_FIRST = True

# 이미지를 전혀 찾지 못했을 때의 최종 대체 이모지
OGQ_EMOJI_FALLBACK = {
    "success": "🎉", "cheer": "📣", "comfort": "🤍", "stamp": "⭐",
    "clap": "👏", "hello": "👋", "encourage": "💪", "thinking": "🤔",
    "thanks": "🙇", "rest": "😴", "sheet": "🗂",
}

# 점수 구간별 문구 (스티커 옆에 함께 노출)
SCORE_STICKER_MESSAGES = {
    "success": ("합격 안정권", "이 정도면 자신 있게 지원해도 좋아요. 남은 건 면접 실전 연습!"),
    "cheer":   ("분발 필요",   "방향은 맞습니다. 자격증 1개만 더 채우면 안정권까지 금방이에요."),
    "comfort": ("보완 시급",   "지금 점수는 출발선일 뿐입니다. 로드맵 1단계부터 같이 채워봐요."),
}


def sticker_key_for_score(score: float) -> str:
    """점수(100점 만점) → 스티커 키 매핑. 80↑ 축하 / 50~79 격려 / 50↓ 위로."""
    if score >= 80:
        return "success"
    if score >= 50:
        return "cheer"
    return "comfort"


def sticker(key: str):
    """
    스티커 키를 st.image()에 바로 넘길 수 있는 값으로 변환한다.
    반환값: 웹 URL(str) | 로컬 파일 절대경로(str) | None(이미지 없음)
    """
    if USE_WEB_FIRST:
        url = (OGQ_WEB_URLS.get(key) or "").strip()
        if url:
            return url

    filename = OGQ_LOCAL_FILES.get(key)
    if filename:
        path = os.path.join(OGQ_DIR, filename)
        if os.path.exists(path):
            return path

    url = (OGQ_WEB_URLS.get(key) or "").strip()
    return url or None


def emoji(key: str) -> str:
    """이미지가 없을 때 쓸 대체 이모지."""
    return OGQ_EMOJI_FALLBACK.get(key, "🐾")


def available() -> bool:
    """로컬 스티커 폴더에 이미지가 하나라도 있는지 확인한다."""
    return any(sticker(k) for k in OGQ_LOCAL_FILES)
