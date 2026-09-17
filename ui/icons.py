# -*- coding: utf-8 -*-
"""
ui/icons.py
[Phase 4] 기능성 라인 아이콘 — 이모지 대체

▣ 왜 이모지를 걷어내는가
   이모지는 OS·브라우저마다 다른 그림으로 렌더링된다. 윈도우 크롬에서 보던
   🛠 가 아이폰 사파리에서는 전혀 다른 색과 모양으로 나온다. 다크 테마에
   맞춘 톤도 지킬 수 없고, 크기도 폰트 크기에 끌려다닌다.
   인라인 SVG 로 바꾸면 어디서나 같은 모양, 같은 굵기, 같은 색이 된다.

▣ 규격 (Lucide / Heroicons 와 같은 라인 아이콘 규격)
   viewBox 24×24 · stroke-width 2 · round cap/join · fill 없음
   Lucide 원본 path 를 기억에 의존해 옮기면 도형이 깨질 위험이 있어
   같은 규격으로 직접 작도했다. 외부 의존성도, 라이선스 문제도 없다.

▣ 색
   기본값은 currentColor — 부모의 color 를 따라간다. 그래서 링크·버튼 안에
   넣으면 그 요소의 색을 그대로 물려받고, 테마를 바꿔도 따로 손댈 곳이 없다.
   강조가 필요하면 ui/theme.py 의 CSS 변수(--mjp-brand 등)를 넘긴다.

▣ 배치 규칙 (마스코트와 역할 분리)
   마스코트(ui/mascot.py)  = 컬러풀 · 화면당 1곳 · 감정을 전한다
   기능 아이콘(이 파일)     = 미니멀 라인 · 작고 절제된 보조 · 의미를 가리킨다
   이 둘이 한 화면에서 경쟁하면 시선이 분산된다.
"""

# 각 아이콘의 SVG 내부 요소 (24×24 기준)
_PATHS = {
    # --- 내비게이션 / 기능 ---
    "chart":      '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-6"/><path d="M22 20H2"/>',
    "search":     '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "wrench":     '<path d="M15 3a5 5 0 0 0-4.6 7L3 17.4 6.6 21l7.4-7.4A5 5 0 0 0 21 9l-3 3-3-3 3-3a5 5 0 0 0-3-3Z"/>',
    "file":       '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z"/><path d="M14 3v5h5"/><path d="M9 13h6"/><path d="M9 17h4"/>',
    "school":     ('<path d="M12 2v3"/><path d="M12 2.5h4.5L15 4.2l1.5 1.7H12"/>'
                   '<path d="M4 21V10l8-4.2 8 4.2v11"/><path d="M2.5 21h19"/>'
                   '<path d="M10.5 21v-5h3v5"/><path d="M8 12h1.5M14.5 12H16"/>'),
    # 깃발이 꽂힌 목표 지점 — '로드맵/여정'을 가장 단순하게 읽히게
    "route":      ('<path d="M6 21V4"/><path d="M6 4.5h10l-2 3 2 3H6"/>'
                   '<circle cx="6" cy="21" r="0.1"/>'),
    "user":       '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "users":      '<circle cx="9" cy="8" r="3.5"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M17 5.5a3.5 3.5 0 0 1 0 7"/><path d="M18.5 21a6.5 6.5 0 0 0-3-5.5"/>',

    # --- 상태 / 동작 ---
    "heart":      '<path d="M12 20.5 4.2 13a4.8 4.8 0 0 1 6.8-6.8l1 1 1-1A4.8 4.8 0 0 1 19.8 13Z"/>',
    "check":      '<path d="m4 12.5 5 5L20 6.5"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.5 2.5L16 9.5"/>',
    "refresh":    '<path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20 4v5h-5"/>',
    "settings":   '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/>',
    "key":        '<circle cx="8" cy="15" r="4"/><path d="m11 12 9-9"/><path d="m17 6 2 2"/><path d="m14.5 8.5 2 2"/>',
    "download":   '<path d="M12 3v12"/><path d="m7 11 5 5 5-5"/><path d="M4 20h16"/>',
    "pencil":     '<path d="M4 20h4L20 8l-4-4L4 16Z"/><path d="m14.5 5.5 4 4"/>',
    "sparkle":    '<path d="M12 3.5 13.8 9 19 10.8 13.8 12.6 12 18 10.2 12.6 5 10.8 10.2 9Z"/><path d="M18.5 3.5v3M20 5h-3"/>',
    "alert":      '<path d="M12 4 2.5 20h19Z"/><path d="M12 10v4"/><path d="M12 17.2v.1"/>',
    "lock":       '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    "info":       '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8v.1"/>',
    "eye":        '<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6Z"/><circle cx="12" cy="12" r="2.8"/>',
    "trend":      '<path d="m3 16 5-5 4 4 8-8"/><path d="M15 7h5v5"/>',
    "clipboard":  '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M9 10h6M9 14h4"/>',
    "award":      '<circle cx="12" cy="9" r="5.5"/><path d="m8.5 13.5-1.5 7 5-2.5 5 2.5-1.5-7"/>',
    "book":       '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v16H6.5A2.5 2.5 0 0 0 4 20.5Z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v4H6.5A2.5 2.5 0 0 1 4 20.5Z"/>',
    "cap":        '<path d="m2 8 10-4 10 4-10 4Z"/><path d="M6 10v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5"/>',
    "package":    '<path d="M21 8 12 3 3 8v8l9 5 9-5Z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>',
    "bell":       '<path d="M18 9a6 6 0 1 0-12 0c0 5-2 6-2 6h16s-2-1-2-6"/><path d="M10.5 20a2 2 0 0 0 3 0"/>',
    "logout":     '<path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/><path d="M10 16 6 12l4-4"/><path d="M6 12h10"/>',
    "cpu":        '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="10" y="10" width="4" height="4"/><path d="M10 2v4M14 2v4M10 18v4M14 18v4M2 10h4M2 14h4M18 10h4M18 14h4"/>',
    "flask":      '<path d="M10 3v6L4.5 18A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-3L14 9V3"/><path d="M9 3h6"/><path d="M7.5 15h9"/>',
    "star":       '<path d="m12 3.5 2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-2.9-5.3 2.9 1.1-6L3.4 9.9l6-.8Z"/>',
    "map":        '<path d="m9 4 6 3 5-2v14l-5 2-6-3-5 2V6Z"/><path d="M9 4v14M15 7v14"/>',
    "arrow-left": '<path d="M19 12H5"/><path d="m11 6-6 6 6 6"/>',
    "arrow-right":'<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "compass":    '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5Z"/>',
    "building":   '<rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2"/>',
    "target":     '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
    "calendar":   '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "stamp":      '<path d="M9 10a3 3 0 0 1 0-4 3 3 0 1 1 6 0 3 3 0 0 1 0 4Z"/><path d="M6 14h12v3H6Z"/><path d="M4 21h16"/>',
}

# 채워진 형태가 필요한 아이콘 (예: 찜한 상태의 하트)
_FILLED = {"heart", "star"}


def icon(name: str, size: int = 18, color: str = "currentColor",
         stroke: float = 2, filled: bool = False, css_class: str = "") -> str:
    """
    인라인 SVG 아이콘 문자열.

    size   : px
    color  : 기본 currentColor (부모 색을 따라감)
    filled : True 면 선 대신 채운다 (하트 찜 상태 등)
    """
    body = _PATHS.get(name)
    if body is None:
        # 없는 이름을 조용히 삼키면 화면에 빈칸이 남는다. 점 하나로 눈에 띄게.
        body = '<circle cx="12" cy="12" r="2"/>'

    fill = color if (filled and name in _FILLED) else "none"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}" fill="{fill}" stroke="{color}" '
        f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" '
        f'class="mjp-icon {css_class}" aria-hidden="true" '
        f'style="vertical-align:-0.16em; flex:none;">{body}</svg>'
    )


def label(name: str, text: str, size: int = 16, color: str = "currentColor",
          gap: int = 7, **kwargs) -> str:
    """아이콘 + 텍스트 한 줄. 줄바꿈 시 아이콘이 따라 붙도록 inline-flex 로 감싼다."""
    return (
        f'<span style="display:inline-flex; align-items:center; gap:{gap}px;">'
        f'{icon(name, size=size, color=color, **kwargs)}<span>{text}</span></span>'
    )


def available() -> list:
    return sorted(_PATHS)


# ------------------------------------------------------------
# 브랜드 심볼 (로그인 버튼 전용)
# ------------------------------------------------------------
# 요구사항: 카카오/네이버/구글은 각 브랜드 공식 심볼을 유지하고
# 마스코트나 일반 라인 아이콘으로 대체하지 않는다.
# 각 사의 로고 원본을 재배포하지 않기 위해, 브랜드 가이드가 규정한
# 형태(말풍선 / N / G)를 단순 도형으로 그려 브랜드 컬러 위에 얹는다.
_BRAND_SYMBOLS = {
    # 카카오 — 말풍선 (노란 버튼 위 검정 심볼)
    "kakao": ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
              'width="{size}" height="{size}" fill="{color}" aria-hidden="true" '
              'style="vertical-align:-0.18em; flex:none;">'
              '<path d="M12 4C7 4 3 7.1 3 10.9c0 2.4 1.7 4.6 4.2 5.8l-.9 3.3c-.1.3.3.6.6.4'
              'l3.9-2.6c.4 0 .8.1 1.2.1 5 0 9-3.1 9-6.9S17 4 12 4Z"/></svg>'),
    # 네이버 — N (초록 버튼 위 흰 심볼)
    "naver": ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
              'width="{size}" height="{size}" fill="{color}" aria-hidden="true" '
              'style="vertical-align:-0.18em; flex:none;">'
              '<path d="M5 5h4.6l4.8 7.1V5H19v14h-4.6L9.6 11.9V19H5Z"/></svg>'),
    # 구글 — G (흰 버튼 위 컬러 심볼). 단색 fill 을 받지 않고 브랜드 4색을 유지한다.
    "google": ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
               'width="{size}" height="{size}" aria-hidden="true" '
               'style="vertical-align:-0.18em; flex:none;">'
               '<path fill="#4285F4" d="M21.6 12.2c0-.7-.1-1.4-.2-2H12v3.9h5.4a4.6 4.6 0 0 1-2 3v2.5h3.2c1.9-1.7 3-4.3 3-7.4Z"/>'
               '<path fill="#34A853" d="M12 22c2.7 0 5-.9 6.6-2.4l-3.2-2.5c-.9.6-2 1-3.4 1-2.6 0-4.8-1.7-5.6-4.1H3.1v2.6A10 10 0 0 0 12 22Z"/>'
               '<path fill="#FBBC05" d="M6.4 14c-.2-.6-.3-1.3-.3-2s.1-1.4.3-2V7.4H3.1a10 10 0 0 0 0 9.2Z"/>'
               '<path fill="#EA4335" d="M12 5.9c1.5 0 2.8.5 3.8 1.5l2.8-2.8A10 10 0 0 0 3.1 7.4L6.4 10c.8-2.4 3-4.1 5.6-4.1Z"/></svg>'),
}


def brand_symbol(name: str, size: int = 18, color: str = "currentColor") -> str:
    """로그인 버튼용 브랜드 심볼. 구글은 브랜드 4색을 유지하므로 color 를 무시한다."""
    template = _BRAND_SYMBOLS.get(name)
    if not template:
        return icon("user", size=size, color=color)
    return template.format(size=size, color=color)
