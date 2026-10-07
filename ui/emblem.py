# -*- coding: utf-8 -*-
"""
ui/emblem.py
E.M.P 팀 로고를 '다크 테마용 디자인 언어'로 재구성한 인라인 SVG 엠블럼

왜 이미지를 그대로 쓰지 않는가
------------------------------
원본 로고는 **흰 배경 위에 짙은 네이비 잉크**로 그려진 래스터 이미지다.
이걸 우리 다크 테마(#0A0E17) 위에 그대로 올리면 흰 판이 그대로 떠서
'붙여넣은 티'가 난다. 배경만 투명하게 빼면 이번엔 짙은 잉크가 어두운
배경에 묻혀 형체가 사라진다.

그래서 로고를 **요소로 분해해 벡터로 다시 그렸다.**

    원본 요소                    → 재구성
    ------------------------------------------------------------
    이중 동심원 (실선 + 파선)    → ring / dashed ring
    방사형 회로 트레이스 + 노드  → circuit traces (엘보 + 노드 사각형)
    세 인물 실루엣               → 3단 필러 (가운데가 가장 높음)
                                    = '세 사람'이자 '성장 그래프'
    점묘 악수                    → 점선 클래스프(맞잡은 형태)
    EMPLOYMENT MEISTER PARTNER   → 하단 아크 레터스페이싱
    딥네이비 → 일렉트릭 블루     → 다크 배경에서 읽히도록 밝기 반전한 컬러 램프

SVG라서 어떤 크기에서도 선명하고, 배경이 없으므로 다크 테마에 그대로 녹는다.

detail 수준
-----------
 · "full"    : 랜딩 히어로용 — 회로 트레이스 + 아크 텍스트 포함
 · "compact" : 상단 내비 마크용(34px) — 링과 필러만 남겨 형태만 읽히게
"""

import itertools

# 로고에서 추출한 컬러 램프 (원본의 네이비 잉크를 다크 배경용으로 밝기 반전)
INK_LIGHT = "#A8CEF5"   # 시안 하이라이트
INK_MID = "#4C8FE0"     # 일렉트릭 블루 (로고 회로선)
INK_DEEP = "#2B6BC4"    # 딥 블루
GLOW = "#3B82F6"

# 엠블럼 인스턴스마다 gradient id가 겹치지 않도록 하는 카운터
_uid_counter = itertools.count(1)


def _traces() -> str:
    """
    방사형 회로 트레이스.
    원본 로고처럼 링 바깥으로 뻗다가 한 번 꺾이고(엘보) 끝에 노드가 붙는다.
    각도를 불규칙하게 둬야 기계적으로 찍어낸 느낌이 안 난다.
    """
    import math

    specs = [
        # (각도°, 뻗는 길이, 엘보 방향(+1/-1), 노드 크기)
        (18, 26, 1, 3.2), (52, 17, -1, 2.4), (86, 30, 1, 3.6),
        (124, 19, -1, 2.6), (158, 27, 1, 3.2), (196, 16, -1, 2.2),
        (232, 29, 1, 3.4), (266, 18, -1, 2.4), (304, 25, 1, 3.0),
        (338, 20, -1, 2.6),
    ]
    cx = cy = 120.0
    r0 = 106.0
    out = []

    for angle, length, elbow, node in specs:
        rad = math.radians(angle)
        dx, dy = math.cos(rad), math.sin(rad)
        # 링에서 뻗어나온 직선 구간
        x1, y1 = cx + dx * r0, cy + dy * r0
        x2, y2 = cx + dx * (r0 + length), cy + dy * (r0 + length)
        # 접선 방향으로 한 번 꺾는다 (PCB 트레이스 느낌)
        tx, ty = -dy * elbow, dx * elbow
        x3, y3 = x2 + tx * 9, y2 + ty * 9

        out.append(
            f'<path d="M {x1:.1f},{y1:.1f} L {x2:.1f},{y2:.1f} L {x3:.1f},{y3:.1f}" '
            f'fill="none" stroke="{INK_MID}" stroke-width="1.1" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="0.38"/>'
        )
        out.append(
            f'<rect x="{x3 - node / 2:.1f}" y="{y3 - node / 2:.1f}" '
            f'width="{node:.1f}" height="{node:.1f}" rx="0.6" '
            f'fill="{INK_LIGHT}" opacity="0.55"/>'
        )

    return "".join(out)


def emblem_svg(size: int = 200, detail: str = "full", uid: str | None = None) -> str:
    """
    엠블럼 SVG 문자열을 만든다.

    size   : 렌더 크기(px)
    detail : 크기에 따라 3단계 — 작은 크기에서 요소를 욕심내면 전부 뭉개진다.
             "full"    (160px+) 회로 트레이스 + 아크 텍스트까지 전부
             "mark"    (64~150px) 링 + 필러 + E.M.P 모노그램
             "compact" (~48px)  링 + 필러만, 대신 크게 키워 형태만 읽히게
    uid    : gradient id 접두사. 한 화면에 여러 개 그릴 때 충돌을 막는다.
    """
    uid = uid or f"e{next(_uid_counter)}"

    defs = f"""
    <defs>
      <linearGradient id="{uid}_ink" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="{INK_LIGHT}"/>
        <stop offset="55%"  stop-color="{INK_MID}"/>
        <stop offset="100%" stop-color="{INK_DEEP}"/>
      </linearGradient>
      <radialGradient id="{uid}_glow" cx="50%" cy="46%" r="52%">
        <stop offset="0%"   stop-color="{GLOW}" stop-opacity="0.30"/>
        <stop offset="60%"  stop-color="{GLOW}" stop-opacity="0.08"/>
        <stop offset="100%" stop-color="{GLOW}" stop-opacity="0"/>
      </radialGradient>
    </defs>"""

    glow = f'<circle cx="120" cy="120" r="108" fill="url(#{uid}_glow)"/>'
    ring_outer = (f'<circle cx="120" cy="120" r="104" fill="none" stroke="{INK_MID}" '
                  f'stroke-width="1" opacity="0.22"/>')
    ring_dashed = (f'<circle cx="120" cy="120" r="96" fill="none" stroke="{INK_LIGHT}" '
                   f'stroke-width="1.2" opacity="0.40" stroke-dasharray="3 7" '
                   f'stroke-linecap="round"/>')
    ring_main = (f'<circle cx="120" cy="120" r="88" fill="none" stroke="url(#{uid}_ink)" '
                 f'stroke-width="2" opacity="0.85"/>')

    def svg(inner: str, label: str) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" '
                f'width="{size}" height="{size}" role="img" aria-label="{label}">'
                f'{defs}{inner}</svg>')

    # ------------------------------------------------------------
    # compact — 상단 내비(34~48px). 작은 크기에서는 디테일이 전부 뭉개지므로
    # 필러만 크게 키워 실루엣으로 읽히게 한다.
    # ------------------------------------------------------------
    if detail == "compact":
        # 필러 블록의 무게중심(y=82)을 원 중심(y=120)에 맞추는 보정.
        # scale 앞에 오는 translate 는 스케일의 영향을 받으므로 ty 를 s 로 나눠야 하는데,
        # 계산해보면 ty = 38*s/s = 38 로 s 와 무관한 상수가 된다.
        # (보정 전에는 마크가 원 안에서 아래로 처져 보였다.)
        pillars = f"""
        <g fill="url(#{uid}_ink)"
           transform="translate(120,120) scale(1.55) translate(-120,-120) translate(0,38)">
          <rect x="91"  y="70" width="13" height="38" rx="6.5"/>
          <rect x="112" y="56" width="16" height="52" rx="8"/>
          <rect x="136" y="70" width="13" height="38" rx="6.5"/>
        </g>"""
        # 파선 링은 38px에서 점이 뭉개져 지저분해지므로 빼고,
        # 남은 링은 불투명도를 올려 작은 크기에서도 원형이 읽히게 한다
        ring_compact = (f'<circle cx="120" cy="120" r="104" fill="none" '
                        f'stroke="url(#{uid}_ink)" stroke-width="3" opacity="0.55"/>')
        return svg(glow + ring_compact + pillars, "E.M.P 엠블럼")

    # ------------------------------------------------------------
    # 세 인물 실루엣 → 3단 필러 (가운데가 가장 높다)
    # 성장 그래프로도 읽히게 의도했다 — 단계가 쌓이는 서비스와 맞물린다.
    # ------------------------------------------------------------
    pillars = f"""
    <g fill="url(#{uid}_ink)">
      <rect x="91"  y="70" width="13" height="38" rx="6.5"/>
      <rect x="112" y="56" width="16" height="52" rx="8"/>
      <rect x="136" y="70" width="13" height="38" rx="6.5"/>
    </g>"""

    monogram = f"""
    <text x="120" y="139" text-anchor="middle" fill="url(#{uid}_ink)"
          font-family="system-ui, -apple-system, 'Segoe UI', sans-serif"
          font-size="33" font-weight="800" letter-spacing="1.2">E.M.P</text>"""

    # 점묘 악수 → '이어짐'을 뜻하는 점선 플러리시.
    # 처음엔 닫힌 렌즈(두 개의 호)로 그렸더니 눈동자처럼 읽혀서 한 줄로 바꿨다.
    flourish = f"""
    <path d="M 94,154 Q 120,146 146,154" fill="none" stroke="{INK_LIGHT}"
          stroke-width="1.5" stroke-dasharray="1.6 4.5" stroke-linecap="round"
          opacity="0.6"/>"""

    if detail == "mark":
        return svg(glow + ring_outer + ring_dashed + ring_main + pillars + monogram + flourish,
                   "E.M.P 엠블럼")

    # ------------------------------------------------------------
    # full — 하단 아크 텍스트
    # 반원(180°) 경로에 그렸더니 글자가 양끝에서 잘리고 모노그램과 겹쳤다.
    # 아래쪽 140°만 쓰고 자간을 줄여 경로 안에 확실히 들어오게 했다.
    #   경로 길이 = 140° × π/180 × 78 ≈ 190px
    # 자간 1.8 에서는 폭이 경로를 아주 살짝 넘겨 앞글자 'E' 가 잘렸다 → 1.05 로 축소
    # ------------------------------------------------------------
    arc = f"""
    <path id="{uid}_arc" d="M 46.7,146.7 A 78,78 0 0 0 193.3,146.7" fill="none"/>
    <text fill="{INK_MID}" opacity="0.8"
          font-family="system-ui, -apple-system, 'Segoe UI', sans-serif"
          font-size="8" font-weight="700" letter-spacing="1.05">
      <textPath href="#{uid}_arc" startOffset="50%" text-anchor="middle"
                >EMPLOYMENT MEISTER PARTNER</textPath>
    </text>"""

    return svg(
        glow + ring_outer + ring_dashed + ring_main + _traces()
        + pillars + monogram + flourish + arc,
        "E.M.P — Employment Meister Partner 엠블럼",
    )


def circuit_pattern_svg(color: str = INK_MID, opacity: float = 0.5) -> str:
    """
    히어로 배경에 깔 회로 트레이스 패턴 (CSS background-image 용).

    로고의 PCB 모티프를 아주 옅게 반복시켜, 랜딩 배경이 '비어 보이지 않으면서도'
    본문 가독성을 해치지 않게 한다. 타일 크기를 크게 잡아 반복 티가 덜 나도록 했다.
    """
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220" '
        f'viewBox="0 0 220 220">'
        f'<g fill="none" stroke="{color}" stroke-width="1" opacity="{opacity}" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M0 40 H60 L80 60 H150 L170 40 H220"/>'
        f'<path d="M0 150 H40 L62 128 H128 L150 150 H220"/>'
        f'<path d="M40 0 V28 L60 48 V96"/>'
        f'<path d="M180 220 V186 L160 166 V120"/>'
        f'<path d="M110 0 V22 M110 198 V220"/>'
        f'</g>'
        f'<g fill="{color}" opacity="{opacity * 1.3:.2f}">'
        f'<rect x="58" y="58" width="4" height="4" rx="1"/>'
        f'<rect x="148" y="38" width="4" height="4" rx="1"/>'
        f'<rect x="60" y="94" width="4" height="4" rx="1"/>'
        f'<rect x="158" y="118" width="4" height="4" rx="1"/>'
        f'<rect x="108" y="20" width="4" height="4" rx="1"/>'
        f'</g></svg>'
    )
