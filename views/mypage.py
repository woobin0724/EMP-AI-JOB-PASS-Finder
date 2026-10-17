# -*- coding: utf-8 -*-
"""
views/mypage.py
마이페이지 — 계정 정보 / 역할 변경 / 로그아웃

현재 범위(Phase 1): 계정 패널 + 역할 변경 + 로그아웃 + 이어하기 코드
다음 범위(Phase 3): 찜한 기업 · 열람 이력 · 매칭 점수 히스토리 · 로드맵 진행 단계
                    (services/store.py 에 스키마와 저장 함수는 이미 준비되어 있다)
"""

import streamlit as st

from core import session as ss
from data.company_showcase import COMPANY_BY_ID
from data.roadmap import MILESTONES
from services import access
from services import activity
from services import premium
from services import reactions, store, usage_log
from ui import mascot
from ui.components import (
    back_to_hub, code_display, grid_columns, list_row, render_html, section_title, status_chip, topbar,
)
from ui.icons import icon
from ui.theme import BRAND, BRAND_LIGHT, CARD_BORDER, GOLD, GREEN, MUTED, RED, STATUS_VIVID, TEXT

_PROVIDER_LABEL = {"kakao": "카카오", "naver": "네이버", "google": "Google", "guest": "게스트모드"}
_ROLE_LABEL = {"student": "학생", "teacher": "선생님"}


def render() -> None:
    topbar(active=ss.PAGE_MYPAGE)
    back_to_hub()
    section_title("마이페이지", "계정 정보와 활동 기록을 확인합니다.", icon_name="user", eyebrow="내 정보")

    uid = ss.user_id()
    saved = store.get_user(uid) or {}

    # ---------- 계정 카드 ----------
    # v2: 그라데이션 원 대신 연한 블루 타일 (블루는 한 가지)
    st.markdown(f"""
    <div class="mjp-tcard" style="margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
            <div style="width:60px; height:60px; border-radius:20px; flex:none; background:{BRAND_LIGHT};
                        display:flex; align-items:center; justify-content:center;">
                        {icon("user", size=28, color=BRAND, stroke=1.8)}</div>
            <div style="flex:1; min-width:180px;">
                <div style="font-size:var(--mjp-h2); font-weight:800; color:{TEXT};">{ss.display_name()}</div>
                <div class="mjp-muted" style="margin-top:5px;">
                    {_ROLE_LABEL.get(st.session_state.get('role'), '역할 미선택')}
                    · {_PROVIDER_LABEL.get(ss.provider(), '알 수 없음')}로 로그인
                    · 요금제 {premium.plan_label()}
                </div>
                <div class="mjp-muted" style="margin-top:3px;">
                    가입일 {(saved.get('created_at') or '-')[:10]}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- 이어하기 코드 ----------
    if ss.provider() == "guest":
        code = st.session_state.get("resume_code") or uid.replace("guest_", "")
        code_display(
            "이어하기 코드", code,
            "다른 기기에서 로그인 화면의 '이어하기 코드가 있어요'에 이 코드를 넣으면 "
            "지금까지의 기록을 그대로 볼 수 있습니다. 화면을 캡처해두세요.",
        )

    # ---------- [Phase 2] 반 정보 ----------

    # ---------- [Phase 3] 나의 활동 기록 ----------
    st.markdown("#### 나의 활동 기록")

    # st.tabs 라벨도 텍스트 전용이다 (SVG 불가) → 이모지를 빼고 단어만 남긴다
    tabs = st.tabs(["매칭 점수", "로드맵", "찜한 기업", "조사한 기업"])
    with tabs[0]:
        _score_section(saved)
    with tabs[1]:
        _roadmap_section()
    with tabs[2]:
        _bookmark_section(saved)
    with tabs[3]:
        _viewed_section(saved)

    # 반 정보는 콘텐츠(활동 기록) 다음. 반 미등록 학생이 대부분이라
    # 활동 기록보다 위에 있으면 본론이 밀린다.
    _class_section(saved)

    # ---------- 계정 관리 ----------
    st.markdown("#### 계정 관리")

    mcol1, mcol2 = st.columns(2)
    with mcol1:
        if st.button("역할 다시 선택하기", use_container_width=True, key="mypage_role"):
            st.session_state["role"] = None
            if uid:
                store.set_role(uid, "")   # 저장소에서도 비워 재선택을 강제한다
            ss.goto(ss.PAGE_ROLE)
    with mcol2:
        if st.button("로그아웃", use_container_width=True, key="mypage_logout"):
            ss.logout()

    # 팀 관리자 진입구 — ADMIN_USER_IDS 에 등록된 계정에만 보인다.
    # (화면 쪽에서도 다시 검사하므로 URL 로 직접 들어와도 막힌다)
    if access.is_admin():
        acol1, acol2 = st.columns(2)
        with acol1:
            if st.button("기업 데이터 입력 (팀 관리자)", use_container_width=True,
                         key="mypage_admin_data"):
                ss.goto(ss.PAGE_ADMIN_DATA)
        with acol2:
            if st.button("사용 통계 (팀 관리자)", use_container_width=True,
                         key="mypage_admin_stats"):
                ss.goto(ss.PAGE_ADMIN_STATS)

    _privacy_section(uid)

    st.caption(f"저장소 현황: {store.store_summary()}")
    st.caption("Streamlit Community Cloud는 재배포·슬립 해제 시 파일시스템이 초기화됩니다. "
               "장기 보관이 필요하면 외부 DB 연동이 필요합니다 "
               "(services/store.py 의 `_read_all` / `_write_all` 두 함수만 교체하면 됩니다).")


# ------------------------------------------------------------
# [big-patch 6단계] 개인정보 — 처리방침 · 내 기록 지우기
# ------------------------------------------------------------
def _privacy_section(uid: str) -> None:
    st.markdown("#### 개인정보")
    if st.button("개인정보 처리방침 보기", use_container_width=True, key="mypage_privacy"):
        ss.goto(ss.PAGE_PRIVACY)
    if not uid or st.session_state.get("role") == "teacher":
        if uid:
            st.caption("선생님 계정은 반이 함께 사라지므로 기록 삭제를 팀에 요청해 주세요.")
        return
    with st.expander("내 기록 지우기"):
        st.caption("계정 정보 · 스펙 진단 · 점수 기록 · 찜 · 로드맵 · 사용 통계 · 스토리 반응을 지우고 반 명단에서 빠집니다. "
                   "되돌릴 수 없고, 지운 뒤에는 로그아웃됩니다.")
        sure = st.checkbox("지운 기록은 되돌릴 수 없다는 것을 이해했어요", key="mypage_delete_sure")
        if st.button("내 기록 모두 지우기", disabled=not sure, use_container_width=True,
                     key="mypage_delete"):
            ok = store.delete_user(uid)
            try:
                usage_log.forget(uid)
                reactions.forget(uid)
            except Exception:  # noqa: BLE001 — 통계 정리 실패가 삭제 자체를 막지 않게
                pass
            if ok:
                ss.logout()
            else:
                st.error("지울 기록이 없거나, 선생님 계정이라 화면에서 지울 수 없습니다.")


# ------------------------------------------------------------
# [Phase 2] 반 정보
# ------------------------------------------------------------
def _class_section(saved: dict) -> None:
    """
    학생: 소속 반 표시 + 미등록 시 등록 진입구
    선생님: 담당 반 + 코드 + 대시보드 진입구

    반 등록은 선택 기능이므로, 미등록 학생에게도 경고가 아니라
    '원하면 하세요' 톤으로만 안내한다.
    """
    st.markdown("#### 반 정보")

    uid = ss.user_id()

    # ---- 선생님 ----
    if ss.is_teacher():
        klass = store.teacher_class(uid)
        if not klass:
            st.info("아직 우리 반을 만들지 않으셨어요.")
            if st.button("우리 반 만들기", type="primary", key="mypage_make_class"):
                ss.goto(ss.PAGE_CLASS_SETUP)
            return

        count = len(store.class_students(klass["class_code"]))
        render_html(list_row("school", store.class_label(klass),
                             f"등록 학생 {count}명 · 개설일 {klass.get('created_at', '')[:10]}"))
        st.caption("반 코드 (눌러서 복사)")
        st.code(klass["class_code"], language=None)

        if st.button("우리 반 현황 보기", type="primary", use_container_width=True,
                     key="mypage_board"):
            ss.goto(ss.PAGE_CLASS_BOARD)
        return

    # ---- 학생 ----
    code = saved.get("class_code")
    if code:
        klass = store.get_class(code)
        render_html(f"""
        <div class="mjp-tcard" style="margin-bottom:12px;">
            {status_chip("등록됨", GREEN)}
            <h4 style="margin-top:12px !important;">{store.class_label(klass) or code}</h4>
            <p class="mjp-muted">반 코드 {code}</p>
            <p style="margin-top:8px !important;">
                진단 결과와 로드맵 진행 상황이 선생님의 '우리 반 현황'에 표시됩니다.
            </p>
        </div>
        """)
        with st.expander("반에서 나가기"):
            st.caption("나가면 이후 활동은 선생님 화면에 표시되지 않습니다. "
                       "이미 기록된 내 데이터는 마이페이지에 그대로 남습니다.")
            if st.button("반에서 나가기", use_container_width=True, key="mypage_leave"):
                store.leave_class(uid)
                ss.set_class_code(None)
                st.rerun()
        return

    render_html("""
    <div class="mjp-tcard" style="margin-bottom:12px;">
        <h4>소속된 반이 없습니다</h4>
        <p>
            반 등록은 <b>선택</b>이에요. 등록하지 않아도 모든 기능을 그대로 쓸 수 있습니다.
            선생님께 반 코드를 받았다면 아래에서 등록해보세요.
        </p>
    </div>
    """)
    if st.button("반 코드 입력하기", use_container_width=True, key="mypage_join_class"):
        ss.goto(ss.PAGE_CLASS_JOIN)


# ============================================================
# [Phase 3] 활동 기록 섹션
# ============================================================

def _empty(slot: str, title: str, desc: str, button: str, page: str, key: str) -> None:
    """빈 상태 공통 렌더러 — '아무것도 없음'이 아니라 '다음에 뭘 하면 되는지'를 보여준다."""
    c1, c2 = st.columns([1, 2.6])
    with c1:
        st.markdown(mascot.html(slot, size=104), unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="padding-top:8px;">
            <div style="font-weight:800; color:{TEXT}; font-size:var(--mjp-body);">{title}</div>
            <div class="mjp-muted" style="margin-top:6px; line-height:1.6;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(button, key=key, type="primary"):
            ss.goto(page)


# ------------------------------------------------------------
# 1. 매칭 점수
# ------------------------------------------------------------
def _score_section(saved: dict) -> None:
    """
    ▣ 형태 선택
       기록이 1건이면 라인 차트는 점 하나짜리 빈 그래프가 된다.
       '한 값 + 추세'는 차트가 아니라 스탯 타일이 맞는 형태라서,
       2건 이상 쌓였을 때만 시간축 차트를 덧붙인다.
       차트는 단일 시리즈이므로 한 가지 색(브랜드 블루)만 쓴다.
    """
    series = activity.score_series(saved)
    if not series:
        _empty("thinking", "아직 진단 기록이 없어요",
               "스펙 진단에서 내신·자격증을 입력하면 점수가 여기에 쌓입니다. "
               "진단할 때마다 기록되니 점수가 어떻게 오르는지 볼 수 있어요.",
               "스펙 진단 하러 가기", ss.PAGE_SPEC, "mypage_go_spec")
        return

    latest, delta = activity.score_delta(saved)

    # --- 스탯 타일 (헤드라인) ---
    if latest >= 80:
        tone, verdict = GREEN, "합격 안정권"
    elif latest >= 50:
        tone, verdict = GOLD, "분발 필요"
    else:
        tone, verdict = RED, "보완 시급"

    if delta is None:
        delta_html = '<div class="mjp-muted">첫 진단 기록</div>'
    elif delta > 0:
        delta_html = (f'<div style="color:{GREEN}; font-size:var(--mjp-caption); font-weight:700;">'
                      f'▲ {delta}점 상승</div>')
    elif delta < 0:
        delta_html = (f'<div style="color:{RED}; font-size:var(--mjp-caption); font-weight:700;">'
                      f'▼ {abs(delta)}점 하락</div>')
    else:
        delta_html = '<div class="mjp-muted">직전과 동일</div>'

    # v2: 스펙 진단 점수 히어로와 같은 언어 — 큰 숫자(VIVID) + '/ 100점' + 판정 칩
    render_html(f"""
    <div class="mjp-tcard" style="margin-bottom:12px;">
        <div class="mjp-score-label">최근 매칭 점수</div>
        <div class="mjp-score-line">
            <span class="mjp-score-num" style="color:{STATUS_VIVID[tone]}; font-size:clamp(48px, 7vw, 64px);">{latest}</span>
            <span class="mjp-score-unit">/ 100점</span>
            {status_chip(verdict, tone)}
        </div>
        <div style="margin-top:6px;">{delta_html}</div>
        <div class="mjp-muted" style="margin-top:4px;">기록 {len(series)}회</div>
    </div>
    """)

    if len(series) < 2:
        st.caption("진단을 한 번 더 하면 점수 변화 그래프가 나타납니다.")
        return

    _score_chart(series)


def score_dataframe(series: list[dict]):
    """
    점수 히스토리 → 차트용 DataFrame. (순수 함수 — 테스트에서 직접 검증한다)

    ▣ x축을 '시각'이 아니라 '진단 회차'로 잡은 이유
       처음에는 시간축으로 그렸는데, 실제로 렌더링해보니 점이 세로로 한 줄
       쌓였다. 학생이 슬라이더를 조정하며 연속으로 진단하면 기록 여러 건이
       같은 분·초에 찍히기 때문이다(저장 시각은 초 단위). 반대로 며칠 만에
       다시 들어오면 점 두 개가 화면 양끝에 떨어져 추세가 안 보인다.

       학생이 이 차트에서 알고 싶은 건 "몇 시에 쟀나"가 아니라 "내 점수가
       오르고 있나"다. 그래서 x는 회차(1,2,3…)로 두고 실제 시각은 툴팁에
       담았다. 이러면 진단이 몰려 있든 띄엄띄엄이든 추세가 항상 읽힌다.
    """
    import pandas as pd

    return pd.DataFrame([
        {"회차": i + 1,
         "시각": pd.to_datetime(row["at"]),
         "점수": row["score"],
         # 저장된 이름이 아니라 ID 로 현재 기업명을 찾는다 (기업명이 바뀌어도 일관)
         "목표 기업": (COMPANY_BY_ID.get(row.get("company_id") or "", {}).get("name")
                    or row.get("company_name") or "일반 진단")}
        for i, row in enumerate(series)
    ])


def build_score_chart(series: list[dict]):
    """
    점수 추이 라인 차트를 만든다.

    Streamlit 호출과 분리한 이유: AppTest 는 vega-lite 차트를 UnknownElement 로만
    노출해서 화면 테스트로는 '차트가 제대로 만들어졌는지'를 확인할 수 없다.
    스펙을 반환하는 순수 함수로 두면 축 범위·색·툴팁을 직접 단언할 수 있다.

    단일 시리즈이므로 색은 브랜드 블루 하나만 쓴다. 점수 구간 색(초록/금색/빨강)은
    위 스탯 타일에서 라벨과 함께 쓰이는 '상태 표시'이고, 그걸 선 색으로 가져오면
    선 하나에 두 가지 의미가 섞인다.
    """
    import altair as alt

    df = score_dataframe(series)

    axis_common = dict(labelColor=MUTED, titleColor=MUTED,
                       domainColor=CARD_BORDER, tickColor=CARD_BORDER)

    chart = (
        alt.Chart(df)
        .mark_line(
            color=BRAND, strokeWidth=2, strokeCap="round",
            point=alt.OverlayMarkDef(color=BRAND, size=70,
                                     stroke=CARD_BORDER, strokeWidth=2),
        )
        .encode(
            x=alt.X("회차:Q", title="진단 회차",
                    scale=alt.Scale(nice=False, padding=18),
                    axis=alt.Axis(tickMinStep=1, format="d", grid=False, **axis_common)),
            y=alt.Y("점수:Q", title=None,
                    scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(grid=True, gridColor=CARD_BORDER, gridOpacity=0.55,
                                  tickCount=5, **axis_common)),
            tooltip=[
                alt.Tooltip("시각:T", title="진단 시각", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("점수:Q", title="매칭 점수"),
                alt.Tooltip("목표 기업:N", title="목표 기업"),
            ],
        )
        .properties(height=230)
        .configure_view(strokeWidth=0, fill=None)
        .configure_axis(domainWidth=1)
    )
    return chart


def _score_chart(series: list[dict]) -> None:
    """차트 + 표 보기. 표를 함께 두는 이유는 정보가 색과 위치에만 의존하지 않게 하기 위함."""
    st.altair_chart(build_score_chart(series), use_container_width=True)
    st.caption("가로축은 진단 회차입니다. 점 위에 손가락을 올리면 실제 진단 시각과 "
               "목표 기업이 표시됩니다.")

    with st.expander("표로 보기"):
        table = score_dataframe(series).iloc[::-1].copy()   # 최신순
        table["시각"] = table["시각"].dt.strftime("%Y-%m-%d %H:%M")
        table = table[["회차", "시각", "점수", "목표 기업"]]
        st.dataframe(table, use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# 2. 커리어 로드맵
# ------------------------------------------------------------
def _roadmap_section() -> None:
    milestones = st.session_state.get("milestones") or {}
    done = sum(1 for v in milestones.values() if v)
    total = len(MILESTONES)

    st.progress(done / total, text=f"{done} / {total} 단계 완료")

    for col, (key, label, desc) in zip(grid_columns(total, 3), MILESTONES):
        with col:
            checked = bool(milestones.get(key))
            chip = status_chip("완료", GREEN) if checked else status_chip("진행 전", MUTED)
            render_html(f"""
            <div class="mjp-tcard" style="padding:24px; margin-bottom:12px;">
                {chip}
                <h4 style="margin-top:12px !important; color:{TEXT if checked else MUTED} !important;">{label}</h4>
                <p class="mjp-muted">{desc}</p>
            </div>
            """)

    if done == total:
        st.success("세 단계를 모두 완료했습니다. 이제 실제 지원서를 넣을 준비가 끝났어요.")
    else:
        st.caption("단계 체크는 '채용 대비 가이드 & 커리큘럼' 화면에서 할 수 있습니다.")
        if st.button("로드맵 이어서 하기", key="mypage_go_guide"):
            ss.goto(ss.PAGE_GUIDE)


# ------------------------------------------------------------
# 3. 찜한 기업
# ------------------------------------------------------------
def _bookmark_section(saved: dict) -> None:
    marks = [cid for cid in (saved.get("bookmarks") or []) if cid in COMPANY_BY_ID]

    if not marks:
        _empty("encourage", "아직 찜한 기업이 없어요",
               "기업 탐색기에서 마음에 드는 기업의 '찜하기'를 누르면 여기에 모입니다. "
               "나중에 자소서를 쓸 때 바로 꺼내 쓸 수 있어요.",
               "기업 탐색하러 가기", ss.PAGE_EXPLORE, "mypage_go_explore")
        return

    st.caption(f"찜한 기업 {len(marks)}곳")

    for col, cid in zip(grid_columns(len(marks), 2), marks):
        company = COMPANY_BY_ID[cid]
        with col:
            st.markdown(f"""
            <div class="mjp-card">
                <span class="mjp-tag">{company['size_tag']} · {company['field_tag']}</span>
                <div style="font-size:var(--mjp-body); font-weight:800; color:{TEXT}; margin-top:8px;">
                    {company['name']}</div>
                <div class="mjp-muted" style="margin-top:4px;">{company['description']}</div>
                <div class="mjp-muted" style="margin-top:8px;">인재상
                    <b style="color:{TEXT};">{', '.join(company['ideal_talent'])}</b></div>
            </div>
            """, unsafe_allow_html=True)

            with st.container(key=f"mjp_row_fav_{cid}"):
                f1, f2, f3 = st.columns([0.8, 1, 1])
                with f1:
                    if st.button("찜 해제", key=f"unfav_{cid}", use_container_width=True,
                                 type="primary"):
                        activity.toggle_bookmark(cid)
                        st.rerun()
                with f2:
                    if st.button("합격 정보", key=f"myfav_info_{cid}", use_container_width=True):
                        st.session_state.selected_company_id = cid
                        ss.goto(ss.PAGE_GUIDE)
                with f3:
                    if st.button("자소서", key=f"myfav_resume_{cid}", use_container_width=True):
                        st.session_state.selected_company_id = cid
                        ss.goto(ss.PAGE_RESUME)


# ------------------------------------------------------------
# 4. 조사한 기업
# ------------------------------------------------------------
def _viewed_section(saved: dict) -> None:
    viewed = [v for v in (saved.get("viewed") or []) if v.get("company_id") in COMPANY_BY_ID]

    if not viewed:
        _empty("thinking", "아직 열어본 기업이 없어요",
               "'채용 대비 가이드'에서 기업을 선택하면 열람 이력이 여기에 쌓입니다. "
               "어떤 기업을 조사했는지 되짚어볼 때 쓰세요.",
               "기업 가이드 보러 가기", ss.PAGE_GUIDE, "mypage_go_guide2")
        return

    st.caption(f"최근 열어본 기업 {len(viewed)}곳 · 최신순")

    for item in viewed:
        company = COMPANY_BY_ID[item["company_id"]]
        marked = icon("heart", size=14, color=RED, filled=True) if activity.is_bookmarked(company["id"]) else ""
        render_html(list_row(
            "", f"{company['name']} <span style='color:{RED};'>{marked}</span>",
            f"{company['size_tag']} · {company['description']}", right=item.get('at', '')[:10],
        ))
