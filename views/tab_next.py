# -*- coding: utf-8 -*-
"""
views/tab_next.py
기능 5. 향후 로드맵 (The Cut) — 지금 만들지 '않은' 것들

▣ 이번 개편으로 바뀐 부분
   원본에서 "잘라냈다"고 선언했던 항목 중 **소셜 로그인**과 **선생님 대시보드**는
   본선 진출 이후 실제로 구현에 착수했다. 잘라낸 기능을 잘라냈다고만 적어두면
   심사에서 "그래서 지금은?" 이라는 질문에 답할 수 없으므로, 각 항목에
   '열림 조건'과 '현재 상태'를 함께 표기하도록 바꿨다.
"""

import streamlit as st

from core import session as ss
from services import auth as auth_svc
from ui import mascot
from ui.components import back_to_hub, grid_columns, render_html, section_title, status_chip, topbar
from ui.icons import icon
from ui.theme import BRAND, GOLD, GREEN, MUTED


SHIPPED = "구현 완료"
PLANNED = "준비 중"


def _shipped(features: list[dict]) -> list[dict]:
    return [f for f in features if f["when"] == SHIPPED]


def _planned(features: list[dict]) -> list[dict]:
    """아직 쓸 수 없는 항목. 학생 화면에서는 기본으로 접어 둔다."""
    return [f for f in features if f["when"] != SHIPPED]


def _cut_features() -> list[dict]:
    """소셜 로그인 항목은 secrets 설정 상태에 따라 현재 상태 문구가 바뀐다."""
    oauth_ready = auth_svc.any_oauth_ready()
    return [
        {
            "icon": "lock", "title": "카카오·네이버·구글 소셜 로그인",
            "when": "구현 완료" if oauth_ready else "준비 중",
            "status_color": GREEN if oauth_ready else GOLD,
            "why": "로그인은 '다시 돌아올 이유'가 있을 때 필요합니다. 찜하기·진행 기록처럼 "
                   "재방문해야 값이 생기는 기능이 들어오면서 로그인이 비로소 필요해졌습니다.",
            "trigger": ("세 제공자의 OAuth2 인가 코드 흐름을 모두 구현했고, 게스트모드는 "
                        "키 없이도 100% 동작합니다."
                        if oauth_ready else
                        "OAuth2 흐름은 구현 완료. 각 개발자 콘솔에서 키를 발급받아 "
                        "secrets.toml 에 넣으면 즉시 활성화됩니다."),
        },
        {
            "icon": "school", "title": "선생님용 우리 반 현황 대시보드",
            "when": "구현 완료",
            "status_color": GREEN,
            "why": "선생님 대시보드는 학생 데이터가 쌓여야 값이 채워집니다. 역할 선택과 "
                   "반 코드 체계가 먼저 있어야 '누구의 데이터인지'가 성립합니다.",
            "trigger": "역할 선택(학생/선생님) 구현으로 전제 조건이 충족되어 착수했습니다.",
        },
        {
            "icon": "users", "title": "현직자·선배 1:1 전문가 매칭",
            "when": "준비 중",
            "status_color": MUTED,
            "why": "매칭은 학생과 현직자 양쪽이 모두 모여야 성립하는 양면 시장입니다. "
                   "한쪽만 있는 상태로 만들면 빈 채팅방만 남습니다. 대신 지금은 선배 리뷰·"
                   "예상 면접질문 카드로 \"현직자 정보에 대한 수요\"가 실재하는지부터 확인합니다.",
            "trigger": "가이드 화면 체류시간과 '더 묻고 싶다'는 요청 빈도.",
        },
        {
            "icon": "bell", "title": "공고 마감 알림 · 푸시",
            "when": "준비 중",
            "status_color": MUTED,
            "why": "알림은 사용자가 이미 특정 공고를 '내 것'으로 찜한 뒤에야 의미가 있습니다. "
                   "찜하기가 로그인에 의존하므로 자연스럽게 로그인 다음 순서가 됩니다.",
            "trigger": "관심 공고 저장(찜하기) 기능이 충분히 쓰이는 것이 확인된 이후.",
        },
    ]


def _feature_card(f: dict) -> None:
    # v2: 왼쪽 색띠 대신 상태 칩. 아이콘은 연한 블루 타일 한 가지 색으로 통일한다.
    render_html(f"""
    <div class="mjp-tcard" style="margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div class="mjp-row-icon">{icon(f["icon"], size=22, color=BRAND, stroke=1.8)}</div>
            <div style="flex:1; min-width:0;">
                <h4 style="margin:0 0 4px !important;">{f['title']}</h4>
                {status_chip(f['when'], f['status_color'])}
            </div>
        </div>
        <p style="margin-top:14px !important;">{f['why']}</p>
        <p class="mjp-muted" style="margin-top:10px !important;"><b>열림 조건</b> · {f['trigger']}</p>
    </div>
    """)


def render() -> None:
    topbar(active=ss.PAGE_NEXT)
    back_to_hub()

    tcol1, tcol2 = st.columns([2.4, 1])
    with tcol1:
        section_title("서비스 로드맵", icon_name="route", eyebrow="로드맵", sub=
                      "지금 <b>바로 쓸 수 있는 기능</b>과, 이어서 준비하고 있는 기능을 "
                      "구분해 적었습니다.")
    with tcol2:
        st.markdown(mascot.html("thanks", size=128), unsafe_allow_html=True)

    features = _cut_features()

    st.markdown("#### 지금 남긴 것 (현재 범위)")
    kept = [
        ("스펙 진단", "100점 만점 합격 점수 — 서비스의 존재 이유. 이것 하나가 안 되면 나머지는 무의미합니다."),
        ("공고 탐색", "백업 데이터 기반 검색 + 공식 API 연결 자리(검증 전) — 외부 응답이 없어도 화면이 멈추지 않습니다."),
        ("커리어 로드맵", "3단계 마일스톤 스탬프 — 진단 이후 '그래서 뭘 하지'에 답하는 최소 장치."),
        ("자소서 초안", "캐싱된 생성기 — 비용 상한을 지키면서도 결과물을 손에 쥐어주는 마무리."),
    ]
    kcols = st.columns(4)
    for i, (title, desc) in enumerate(kept):
        with kcols[i]:
            render_html(f"""<div class="mjp-tcard" style="height:100%; padding:24px; margin-bottom:12px;">
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>""")

    shipped = _shipped(features)
    if shipped:
        st.markdown("#### 최근 추가된 기능")
        for col, f in zip(grid_columns(len(shipped), 2), shipped):
            with col:
                _feature_card(f)

    # 아직 쓸 수 없는 항목은 접어 둔다. 펼치기 전에는 화면에 나오지 않으므로
    # 학생이 '미완성 화면'으로 오해하지 않고, 심사·교사용으로는 그대로 남는다.
    planned = _planned(features)
    if planned:
        with st.expander(f"준비 중인 기능 {len(planned)}건 — 왜 아직 만들지 않았는지"):
            st.caption("아래 기능은 아직 사용할 수 없습니다. 버린 것이 아니라 확인해야 할 "
                       "가설이 남아 있어 순서를 뒤로 미룬 항목입니다.")
            for f in planned:
                _feature_card(f)
