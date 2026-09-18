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
from data import ogq_assets as ogq
from services import auth as auth_svc
from ui import mascot
from ui.components import back_to_hub, grid_columns, render_html, section_title, topbar
from ui.icons import icon
from ui.theme import GREEN, MUTED, PURPLE, TEXT


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
            "status_color": GREEN if oauth_ready else "#FBBF24",
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
            "status_color": PURPLE,
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
    render_html(f"""
    <div class="mjp-later" style="border-left-color:{f['status_color']};">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="flex:none;">{icon(f["icon"], size=22, color=f["status_color"], stroke=1.8)}</div>
            <div>
                <div style="font-size:var(--mjp-body); font-weight:800; color:{TEXT};">{f['title']}</div>
                <span class="mjp-badge" style="background:{f['status_color']}; color:#0A0E17;">{f['when']}</span>
            </div>
        </div>
        <div class="mjp-muted" style="margin-top:12px; line-height:1.6;">{f['why']}</div>
        <div style="margin-top:10px; font-size:var(--mjp-caption); color:{GREEN};">▸ {f['trigger']}</div>
    </div>
    """)


def render() -> None:
    topbar(active=ss.PAGE_NEXT)
    back_to_hub()

    tcol1, tcol2 = st.columns([2.4, 1])
    with tcol1:
        section_title("서비스 로드맵", icon_name="route", sub=
                      "지금 <b>바로 쓸 수 있는 기능</b>과, 이어서 준비하고 있는 기능을 "
                      "구분해 적었습니다.")
    with tcol2:
        st.markdown(mascot.html("thanks", size=128), unsafe_allow_html=True)

    features = _cut_features()

    st.markdown("### 지금 남긴 것 (현재 범위)")
    kept = [
        ("스펙 진단", "100점 만점 합격 점수 — 서비스의 존재 이유. 이것 하나가 안 되면 나머지는 무의미합니다."),
        ("공고 탐색", "실시간 API + 백업 이중화 — 시연 중에도 절대 멈추지 않는 데이터 파이프라인."),
        ("커리어 로드맵", "3단계 마일스톤 스탬프 — 진단 이후 '그래서 뭘 하지'에 답하는 최소 장치."),
        ("자소서 초안", "캐싱된 생성기 — 비용 상한을 지키면서도 결과물을 손에 쥐어주는 마무리."),
    ]
    kcols = st.columns(4)
    for i, (title, desc) in enumerate(kept):
        with kcols[i]:
            st.markdown(f"""<div class="mjp-card" style="border-color:{GREEN}; height:100%;">
                <div style="font-weight:800; color:{TEXT};">{title}</div>
                <div class="mjp-muted" style="margin-top:8px; line-height:1.55;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    shipped = _shipped(features)
    if shipped:
        st.markdown("### 최근 추가된 기능")
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

    st.divider()
    scol1, scol2 = st.columns([1, 2.2])
    with scol1:
        st.markdown(mascot.html("cheer", size=180), unsafe_allow_html=True)
    with scol2:
        st.markdown("#### 마스코트 캐릭터에 대하여")
        st.markdown(
            "점수 결과와 로드맵 스탬프에 쓰인 캐릭터는 네이버 OGQ마켓의 창작자 스티커입니다. "
            "숫자만 보여주는 진단 도구는 낮은 점수를 받은 학생을 밀어냅니다. 같은 48점이라도 "
            "위로하는 캐릭터가 옆에 있으면 다음 화면으로 넘어갈 확률이 달라진다는 것이 "
            "유저 인터뷰에서 가장 반복된 반응이었습니다."
        )
        st.caption(f"출처: {ogq.OGQ_MARKET_URL} · 교내 프로젝트 시연 용도이며, 외부 배포 시 "
                   f"창작자 이용 허락 또는 OGQ마켓 라이선스 정책 확인이 필요합니다.")
