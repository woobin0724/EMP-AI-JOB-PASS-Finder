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
from services import store
from ui.components import back_to_hub, section_title, topbar
from ui.theme import CARD_BORDER, GOLD, GREEN, MUTED, PURPLE, TEXT

_PROVIDER_LABEL = {"kakao": "카카오", "naver": "네이버", "google": "Google", "guest": "게스트모드"}
_ROLE_LABEL = {"student": "🎓 학생", "teacher": "🧑‍🏫 선생님"}


def render() -> None:
    topbar(active=ss.PAGE_MYPAGE)
    back_to_hub()
    section_title("👤 마이페이지", "계정 정보와 활동 기록을 확인합니다.")

    uid = ss.user_id()
    saved = store.get_user(uid) or {}

    # ---------- 계정 카드 ----------
    st.markdown(f"""
    <div class="mjp-card">
        <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
            <div style="width:62px; height:62px; border-radius:50%; flex:none;
                        background:linear-gradient(135deg,#3B82F6,#8B5CF6);
                        display:flex; align-items:center; justify-content:center;
                        font-size:26px;">👤</div>
            <div style="flex:1; min-width:180px;">
                <div style="font-size:20px; font-weight:800; color:{TEXT};">{ss.display_name()}</div>
                <div class="mjp-muted" style="margin-top:5px;">
                    {_ROLE_LABEL.get(st.session_state.get('role'), '역할 미선택')}
                    · {_PROVIDER_LABEL.get(ss.provider(), '알 수 없음')}로 로그인
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
        st.markdown(f"""
        <div class="mjp-card" style="border-color:{GOLD};">
            <div style="font-weight:800; color:{TEXT};">🔑 이어하기 코드</div>
            <div style="color:{GOLD}; font-size:26px; font-weight:800;
                        letter-spacing:0.2em; margin:8px 0 6px;">{code}</div>
            <div class="mjp-muted">
                다른 기기에서 로그인 화면의 '이어하기 코드가 있어요'에 이 코드를 넣으면
                지금까지의 기록을 그대로 볼 수 있습니다. 화면을 캡처해두세요.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- [Phase 2] 반 정보 ----------
    _class_section(saved)

    # ---------- 활동 기록 (Phase 3 예정) ----------
    st.markdown(f'<div style="height:1px;background:{CARD_BORDER};margin:18px 0;"></div>',
                unsafe_allow_html=True)
    st.markdown("#### 📌 나의 활동 기록")

    acols = st.columns(3)
    upcoming = [
        ("♡", "찜한 기업", "기업 탐색기에서 하트를 누른 기업이 여기 모입니다."),
        ("👀", "조사한 기업", "가이드에서 열어본 기업의 이력이 쌓입니다."),
        ("📈", "매칭 점수 히스토리", "진단할 때마다 점수 변화가 기록됩니다."),
    ]
    for col, (icon, title, desc) in zip(acols, upcoming):
        with col:
            st.markdown(f"""
            <div class="mjp-card" style="border-style:dashed; text-align:center;">
                <div style="font-size:26px;">{icon}</div>
                <div style="font-weight:800; color:{TEXT}; margin-top:8px;">{title}</div>
                <div class="mjp-muted" style="margin-top:6px; line-height:1.5;">{desc}</div>
                <div style="margin-top:10px;">
                    <span class="mjp-badge" style="background:{PURPLE}; color:#fff;">다음 업데이트</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ---------- 계정 관리 ----------
    st.markdown(f'<div style="height:1px;background:{CARD_BORDER};margin:18px 0;"></div>',
                unsafe_allow_html=True)
    st.markdown("#### ⚙️ 계정 관리")

    mcol1, mcol2 = st.columns(2)
    with mcol1:
        if st.button("🔄 역할 다시 선택하기", use_container_width=True, key="mypage_role"):
            st.session_state["role"] = None
            if uid:
                store.set_role(uid, "")   # 저장소에서도 비워 재선택을 강제한다
            ss.goto(ss.PAGE_ROLE)
    with mcol2:
        if st.button("🚪 로그아웃", use_container_width=True, key="mypage_logout"):
            ss.logout()

    st.caption(f"📦 저장소 현황: {store.store_summary()}")
    st.caption("ℹ️ Streamlit Community Cloud는 재배포·슬립 해제 시 파일시스템이 초기화됩니다. "
               "장기 보관이 필요하면 외부 DB 연동이 필요합니다 "
               "(services/store.py 의 `_read_all` / `_write_all` 두 함수만 교체하면 됩니다).")


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
    st.markdown(f'<div style="height:1px;background:{CARD_BORDER};margin:18px 0;"></div>',
                unsafe_allow_html=True)
    st.markdown("#### 🏫 반 정보")

    uid = ss.user_id()

    # ---- 선생님 ----
    if ss.is_teacher():
        klass = store.teacher_class(uid)
        if not klass:
            st.info("아직 우리 반을 만들지 않으셨어요.")
            if st.button("🏫 우리 반 만들기", type="primary", key="mypage_make_class"):
                ss.goto(ss.PAGE_CLASS_SETUP)
            return

        count = len(store.class_students(klass["class_code"]))
        st.markdown(f"""
        <div class="mjp-card" style="border-color:{GOLD};">
            <div style="font-size:18px; font-weight:800; color:{TEXT};">
                {store.class_label(klass)}</div>
            <div class="mjp-muted" style="margin-top:6px;">등록 학생 {count}명 ·
                개설일 {klass.get('created_at', '')[:10]}</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("반 코드 (눌러서 복사)")
        st.code(klass["class_code"], language=None)

        if st.button("📊 우리 반 현황 보기", type="primary", use_container_width=True,
                     key="mypage_board"):
            ss.goto(ss.PAGE_CLASS_BOARD)
        return

    # ---- 학생 ----
    code = saved.get("class_code")
    if code:
        klass = store.get_class(code)
        st.markdown(f"""
        <div class="mjp-card" style="border-color:{GREEN};">
            <span class="mjp-badge" style="background:{GREEN}; color:#0A0E17;">등록됨</span>
            <div style="font-size:17px; font-weight:800; color:{TEXT}; margin-top:10px;">
                {store.class_label(klass) or code}</div>
            <div class="mjp-muted" style="margin-top:4px;">반 코드 {code}</div>
            <div class="mjp-muted" style="margin-top:8px; line-height:1.55;">
                진단 결과와 로드맵 진행 상황이 선생님의 '우리 반 현황'에 표시됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("반에서 나가기"):
            st.caption("나가면 이후 활동은 선생님 화면에 표시되지 않습니다. "
                       "이미 기록된 내 데이터는 마이페이지에 그대로 남습니다.")
            if st.button("반에서 나가기", use_container_width=True, key="mypage_leave"):
                store.leave_class(uid)
                ss.set_class_code(None)
                st.rerun()
        return

    st.markdown(f"""
    <div class="mjp-card" style="border-style:dashed;">
        <div style="font-weight:800; color:{TEXT};">소속된 반이 없습니다</div>
        <div class="mjp-muted" style="margin-top:6px; line-height:1.6;">
            반 등록은 <b>선택</b>이에요. 등록하지 않아도 모든 기능을 그대로 쓸 수 있습니다.
            선생님께 반 코드를 받았다면 아래에서 등록해보세요.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏫 반 코드 입력하기", use_container_width=True, key="mypage_join_class"):
        ss.goto(ss.PAGE_CLASS_JOIN)
