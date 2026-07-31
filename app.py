# -*- coding: utf-8 -*-
"""
AI Job Pass Finder — "Meister Job Pathfinder" (확장판)
전북기계공고 E.M.P 팀 | 마이스터고 취업 성공 올인원 패스파인더

하이파이브(전공/취업률) · 큐넷(자격증 가산점) · 캐치(기업분석 카드) ·
코멘토(4주 커리큘럼) 스타일을 참고해 확장한 통합 MVP입니다.

실행: streamlit run app.py

※ 화면 곳곳의 "예시 데이터" 라벨을 참고하세요. 실제 상용 플랫폼(하이파이브,
   큐넷 제외/캐치/코멘토/링커리어)의 데이터를 실시간으로 긁어온 것이 아니라,
   각 플랫폼의 데이터 구성 방식을 참고해 팀이 만든 예시 콘텐츠입니다.
"""

import os
import datetime

import streamlit as st

from data.departments import DEPARTMENT_LIST, DEPARTMENTS, get_category, get_employment_rate, get_majors_for_department
from data.certifications import (
    CERT_CODE_TO_NAME, get_bonus_points, CERTIFICATIONS,
)
from data.company_showcase import (
    COMPANY_SHOWCASE, COMPANY_BY_ID, COMPANY_CATEGORIES, COMPANY_SIZE_TAGS,
)
from services.qnet_api import fetch_certifications_from_api
from services.worknet_api import fetch_jobs_from_api
from services.alio_api import fetch_alio_jobs
from services.strong_sme_api import fetch_strong_small_companies, prioritize_by_department, PRIORITY_DEPARTMENTS
from core.matching import filter_results
from services.coverletter import generate_cover_letter
from services.curriculum import generate_curriculum
from services.pdf_report import build_success_report_pdf
from core.spec_score import calc_spec_score

# ============================================================
# 0. 페이지 설정 & 디자인 토큰
# ============================================================
st.set_page_config(page_title="Meister Job Pathfinder", page_icon="🧭", layout="wide")

BG = "#0A0E17"
CARD = "#131826"
CARD_BORDER = "#232B3D"
TEXT = "#E7EAF0"
MUTED = "#8A93A6"
GREEN = "#34D399"
GOLD = "#FBBF24"
PURPLE = "#8B5CF6"
RED = "#F87171"
BLUE = "#3B82F6"
KAKAO = "#FEE500"
NAVER = "#03C75A"

st.markdown(f"""
<style>
.stApp {{ background-color: {BG}; }}
h1,h2,h3,h4 {{ color: {TEXT}; }}
.mjp-card {{
    background:{CARD}; border:1px solid {CARD_BORDER}; border-radius:14px;
    padding:18px 20px; margin-bottom:16px;
}}
.mjp-badge {{
    display:inline-block; font-size:11px; font-weight:700; padding:3px 10px;
    border-radius:999px; letter-spacing:0.03em;
}}
.mjp-tag {{
    display:inline-block; font-size:11px; padding:2px 9px; border-radius:6px;
    margin-right:4px; background:{CARD_BORDER}; color:{MUTED};
}}
.mjp-muted {{ color:{MUTED}; font-size:12.5px; }}
.mjp-star {{ color:{GOLD}; }}
.mjp-disclaimer {{
    background: rgba(52,211,153,0.08); border:1px dashed {GREEN};
    border-radius:10px; padding:8px 12px; font-size:12px; color:{MUTED}; margin-bottom:14px;
}}
.mjp-interview {{
    background:{CARD}; border:1px solid {PURPLE}; border-radius:10px;
    padding:12px 14px; margin-bottom:10px;
}}
.mjp-qbadge {{ color:{PURPLE}; font-weight:700; font-size:12px; margin-bottom:4px; display:block; }}
.mjp-stamp-done {{ background:{GREEN}; color:{BG}; }}
.mjp-stamp-pending {{ background:{CARD_BORDER}; color:{MUTED}; }}
</style>
""", unsafe_allow_html=True)


def safe_secret(key: str) -> str:
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


# ============================================================
# 1. 세션 상태 초기화
# ============================================================
DEFAULTS = {
    "active_tab": "spec",
    "user_nickname": None,
    "dept": DEPARTMENT_LIST[0],
    "grade": 3.0,
    "user_certs": [],
    "strength_keywords": [],
    "selected_company_id": None,
    "roadmap_step": 0,  # 0=시작전, 1=자격증 완료, 2=포트폴리오 완료, 3=면접 완료
    "last_spec_result": None,
    "last_curriculum": None,
    "cover_letter": None,
    "cover_letter_source": None,
    "live_jobs": None,
    "live_jobs_sources": None,  # (worknet_src, alio_src, sme_src) 3-tuple
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def go_to(tab_key: str):
    st.session_state.active_tab = tab_key


# ============================================================
# 2. 사이드바 — 간편 로그인 (UI 데모) + API 키(선택)
# ============================================================
with st.sidebar:
    st.markdown("### 👋 간편 로그인 (데모)")
    if st.session_state.user_nickname:
        st.success(f"{st.session_state.user_nickname}님 환영합니다!")
        if st.button("로그아웃"):
            st.session_state.user_nickname = None
            st.rerun()
    else:
        nick = st.text_input("닉네임 입력 후 아래 버튼으로 로그인", placeholder="예: 우빈")
        kc1, kc2 = st.columns(2)
        with kc1:
            if st.button("🟡 카카오로 시작", use_container_width=True):
                st.session_state.user_nickname = nick or "카카오 사용자"
                st.rerun()
        with kc2:
            if st.button("🟢 네이버로 시작", use_container_width=True):
                st.session_state.user_nickname = nick or "네이버 사용자"
                st.rerun()
        if st.button("게스트로 계속하기", use_container_width=True):
            st.session_state.user_nickname = nick or "게스트"
            st.rerun()
        st.caption(
            "※ 위 로그인은 실제 카카오/네이버 인증이 아닌 **데모용 세션 로그인**입니다. "
            "실제 소셜 로그인을 연동하려면 카카오/네이버 개발자센터에서 앱을 등록하고 "
            "REST API 키·Redirect URI를 발급받아야 합니다. (README 참고)"
        )

    st.divider()
    st.markdown("### ⚙️ 데이터 연동 설정 (선택)")
    qnet_key = st.text_input("Q-Net/공공데이터포털 서비스키", type="password",
                              value=safe_secret("QNET_API_KEY"))
    worknet_key = st.text_input("고용24(워크넷) Open API 인증키", type="password",
                                 value=safe_secret("WORKNET_API_KEY"))
    st.caption("키가 없어도 앱은 백업 데이터로 완전히 동작합니다.")

# ============================================================
# 3. 헤더
# ============================================================
hcol1, hcol2 = st.columns([3, 1])
with hcol1:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:44px; height:44px; border-radius:10px; background:{GREEN};
                    display:flex; align-items:center; justify-content:center;
                    font-weight:800; color:{BG};">MJP</div>
        <div>
            <div style="font-size:20px; font-weight:800; color:{TEXT};">Meister Job Pathfinder</div>
            <div class="mjp-muted">마이스터고 취업 성공 올인원 패스파인더</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with hcol2:
    st.markdown(f"""
    <div style="text-align:right; padding-top:6px;">
        <div class="mjp-muted">전국 마이스터고 연계망</div>
        <div style="color:{GREEN}; font-size:12px;">● 예시 데이터 기반 데모 서비스</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

NAV_ITEMS = [
    ("spec", "📊 1. 스펙 진단 & 추천"),
    ("explore", "🔍 2. 실시간 기업 탐색기"),
    ("guide", "🛠 3. 채용 대비 가이드 & 커리큘럼"),
    ("resume", "📄 4. 합격 이력서 & 자소서"),
]
nav_cols = st.columns(4)
for i, (key, label) in enumerate(NAV_ITEMS):
    with nav_cols[i]:
        btn_type = "primary" if st.session_state.active_tab == key else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            go_to(key)

st.write("")

# ============================================================
# 4. 데이터 로드 & 공통 헬퍼
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_cert_names(api_key):
    df, source = fetch_certifications_from_api(api_key)
    return df["name"].tolist(), source


ALL_CERT_NAMES, cert_source = load_cert_names(qnet_key)


@st.cache_data(ttl=600, show_spinner=False)
def load_worknet_jobs(api_key, keyword):
    """고용24 채용공고를 캐싱하여 불러온다 (동일 키워드/키에 대해 재스크래핑 방지)."""
    return fetch_jobs_from_api(api_key, keyword=keyword)


@st.cache_data(ttl=600, show_spinner=False)
def load_alio_jobs():
    """잡알리오 공기업 채용공고를 캐싱하여 불러온다 (불필요한 재스크래핑 방지)."""
    return fetch_alio_jobs()


@st.cache_data(ttl=600, show_spinner=False)
def load_strong_sme():
    """'참 괜찮은 강소기업' 포털 채용공고를 캐싱하여 불러온다 (불필요한 재스크래핑 방지)."""
    return fetch_strong_small_companies()


ALL_TALENT_KEYWORDS = sorted({kw for c in COMPANY_SHOWCASE for kw in c["ideal_talent"]})


def certs_for_department(dept: str):
    codes = DEPARTMENTS.get(dept, {}).get("cert_codes", [])
    return [CERT_CODE_TO_NAME[c] for c in codes if c in CERT_CODE_TO_NAME]


def render_stars(rating: float) -> str:
    full = int(rating)
    return f'<span class="mjp-star">{"★"*full}{"☆"*(5-full)}</span> ({rating:.1f})'


def get_selected_company():
    if st.session_state.selected_company_id:
        return COMPANY_BY_ID.get(st.session_state.selected_company_id)
    return None


ROADMAP_LABELS = ["시작 전", "자격증 준비 완료", "포트폴리오 완성", "면접 준비 완료"]

# ============================================================
# TAB 1. 스펙 진단 & 추천 (하이파이브 전공 데이터 + 큐넷 가산점, 실시간 갱신)
# ============================================================
if st.session_state.active_tab == "spec":
    left, right = st.columns([1.3, 1])

    with left:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown("#### 📝 내 현재 스펙 정보 기입")

        dept = st.selectbox("학과/계열 (하이파이브 분류 기준)", DEPARTMENT_LIST,
                             index=DEPARTMENT_LIST.index(st.session_state.dept),
                             key="dept_widget")
        st.session_state.dept = dept

        majors = get_majors_for_department(dept)
        emp_rate = get_employment_rate(dept)
        st.caption(f"세부 전공 예시: {', '.join(majors)}  ·  계열 평균 취업률(예시): **{emp_rate}%**")

        grade = st.slider("내신 성적 등급 (5등급제)", 1.0, 5.0, st.session_state.grade, 0.1,
                           key="grade_widget")
        st.session_state.grade = grade

        dept_certs = certs_for_department(dept)
        cert_options = sorted(set(dept_certs) | set(ALL_CERT_NAMES))
        # ⚠️ 버그 수정: 이전에는 key 없이 default=session_state를 읽고 동시에
        #    같은 session_state에 결과를 다시 써서, rerun마다 위젯 내부 식별자가
        #    흔들려 "홀수 번째 선택만 반영되고 이전 선택이 사라지는" 증상이 있었다.
        #    고유 key를 부여해 위젯 상태를 안정적으로 유지하도록 수정.
        certs = st.multiselect(
            "취득 전공 자격증 다중 선택 (Q-Net 기반)", cert_options,
            default=[c for c in st.session_state.user_certs if c in cert_options],
            key="user_certs_widget",
        )
        st.session_state.user_certs = certs

        strengths = st.multiselect(
            "나의 핵심 강점 키워드 (기업 인재상 매칭에 사용됨)", ALL_TALENT_KEYWORDS,
            default=[k for k in st.session_state.strength_keywords if k in ALL_TALENT_KEYWORDS],
            key="strength_keywords_widget",
            help="선택한 키워드가 기업의 '인재상'과 일치하면 인재상 점수(10점)에 반영됩니다.",
        )
        st.session_state.strength_keywords = strengths

        company_names = ["선택 안 함 (일반 진단)"] + [c["name"] for c in COMPANY_SHOWCASE]
        pick = st.selectbox("정밀 진단할 목표 기업 (선택)", company_names)
        target_company = COMPANY_BY_ID[[c["id"] for c in COMPANY_SHOWCASE if c["name"] == pick][0]] if pick != company_names[0] else None
        if target_company:
            st.session_state.selected_company_id = target_company["id"]

        st.caption("※ 입력값을 바꾸면 오른쪽 점수가 **즉시** 갱신됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- 실시간 점수 계산 (버튼 없이 위젯 값이 바뀔 때마다 즉시 갱신) ----
    dept_category = get_category(dept)
    result = calc_spec_score(
        grade=grade, user_certs=certs, dept_category=dept_category,
        company=target_company, strength_keywords=strengths,
    )
    st.session_state.last_spec_result = result

    with right:
        st.markdown(f"""
        <div class="mjp-card">
            <span class="mjp-badge" style="background:{GREEN}; color:{BG};">SPEC DIAGNOSIS · 실시간</span>
            <div style="display:flex; align-items:center; gap:16px; margin-top:10px;">
                <div style="flex:1;">
                    <div style="font-size:17px; font-weight:800;">종합 취업 등용문 점수</div>
                    <div class="mjp-muted" style="margin-top:4px;">
                        내신(30)+자격증(40)+전공적합성(20)+인재상(10) = 100점
                    </div>
                </div>
                <div style="width:96px; height:96px; border-radius:50%; background:{GREEN};
                            display:flex; flex-direction:column; align-items:center; justify-content:center; color:{BG};">
                    <div style="font-size:26px; font-weight:800;">{result['final_score']}점</div>
                    <div style="font-size:10px;">100점 만점</div>
                </div>
            </div>
            <div style="display:flex; gap:8px; margin-top:12px; flex-wrap:wrap;">
                <span class="mjp-tag">내신 {result['grade_score']}/30</span>
                <span class="mjp-tag">자격증 {result['cert_score']}/40</span>
                <span class="mjp-tag">적합성 {result['fit_score']}/20</span>
                <span class="mjp-tag">인재상 {result['talent_score']}/10</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- 큐넷 자격 분석 가이드 (가산점 즉시 연동) ----
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown(f'<span class="mjp-badge" style="background:{BLUE}; color:#fff;">Q-NET</span> **자격 분석 가이드 (예시 가산점)**',
                     unsafe_allow_html=True)
        if not certs:
            st.caption("왼쪽에서 자격증을 선택하면 기업 규모별 예시 가산점이 즉시 표시됩니다.")
        else:
            size_for_bonus = st.radio("기준 기업 규모", COMPANY_SIZE_TAGS[1:], horizontal=True,
                                       key="qnet_bonus_size", label_visibility="collapsed")
            for cert in certs:
                pts = get_bonus_points(cert, size_for_bonus)
                st.markdown(f"- **{cert}** → {size_for_bonus} 예시 가산점 **+{pts}점**")
            st.caption("※ 실제 공식 가산점 규정이 아닌 예시 데이터입니다.")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- 매칭 기업 탐색 (실시간) ----
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown("🎯 **매칭 기업 탐색 (실시간 반영)**")
        size_pick = st.radio("기업 규모", COMPANY_SIZE_TAGS[1:], horizontal=True,
                              key="match_size", label_visibility="collapsed")
        matched = [c for c in COMPANY_SHOWCASE if c["category"] == dept_category and c["size_tag"] == size_pick]
        if not matched:
            st.caption("해당 기업군에는 이 학과 계열과 매칭되는 예시 기업이 없습니다. 다른 규모를 선택해보세요.")
        else:
            for c in matched:
                st.markdown(f"**{c['name']}** · {c['description']}  {render_stars(c['overall_rating'])}",
                            unsafe_allow_html=True)
                if st.button(f"{c['name']} 자세히 보기", key=f"match_{c['id']}"):
                    st.session_state.selected_company_id = c["id"]
                    go_to("guide")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 2. 실시간 기업 탐색기 (캐치 스타일 카드 + 고용24 실시간 공고 불러오기)
# ============================================================
elif st.session_state.active_tab == "explore":
    st.markdown('<div class="mjp-disclaimer">🧪 아래 기업 카드(별점·복지 등)는 예시(모의) 데이터입니다. 하단 "실시간 채용공고"는 실제 API 연동을 시도합니다.</div>',
                unsafe_allow_html=True)
    st.markdown("#### 🏢 전국 주요 계열 연계 Meister 모의 채용 기업 데이터베이스")

    cat = st.radio("분야", COMPANY_CATEGORIES, horizontal=True, label_visibility="collapsed")
    shown = COMPANY_SHOWCASE if cat == "전체" else [c for c in COMPANY_SHOWCASE if c["category"] == cat]

    cols = st.columns(3)
    for i, c in enumerate(shown):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="mjp-card">
                <span class="mjp-tag">{c['size_tag']} · {c['field_tag']}</span>
                <span class="mjp-star" style="float:right;">{render_stars(c['overall_rating'])}</span>
                <div style="font-size:19px; font-weight:800; margin-top:8px;">{c['name']}</div>
                <div class="mjp-muted" style="margin-bottom:8px;">{c['description']}</div>
                <div class="mjp-muted">인재상<br><b style="color:{TEXT};">{', '.join(c['ideal_talent'])}</b></div>
                <div class="mjp-muted" style="margin-top:6px;">독점 복지 혜택<br>
                    <span style="color:{TEXT};">{c['benefit_short']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("합격 정보 →", key=f"info_{c['id']}", use_container_width=True):
                    st.session_state.selected_company_id = c["id"]
                    go_to("guide")
                    st.rerun()
            with bc2:
                if st.button("이력서 연동 📄", key=f"resume_{c['id']}", use_container_width=True):
                    st.session_state.selected_company_id = c["id"]
                    go_to("resume")
                    st.rerun()

    st.divider()
    st.markdown("#### 🔄 실시간 채용 공고 통합 검색 (고용24 + 잡알리오 + 강소기업)")
    st.caption("고용24(민간·중소기업), 잡알리오(공기업), '참 괜찮은 강소기업' 포털 데이터를 함께 검색합니다. "
               "기계·전기·제조·IT 전공과 연관된 강소기업 공고는 우선적으로 상단에 노출됩니다.")

    kw = st.text_input("검색 키워드 (기업명·공고명·자격증)", placeholder="예: 전기기능사, CNC, 정보처리, 한국전력공사")
    type_pick = st.selectbox("기업 유형", ["전체", "대기업", "중견기업", "중소기업", "스타트업", "공기업", "강소기업"])

    if st.button("📡 지금 불러오기", type="primary"):
        with st.spinner("고용24·잡알리오·강소기업 포털 호출 중... 실패 시 예시 데이터로 자동 전환됩니다."):
            worknet_df, worknet_src = load_worknet_jobs(worknet_key, kw)
            alio_records, alio_src = load_alio_jobs()
            sme_records, sme_src = load_strong_sme()

        worknet_records = worknet_df.to_dict("records")
        # 잡알리오·강소기업 결과에도 동일한 키워드 필터를 적용해 일관성 유지
        alio_records = filter_results(alio_records, kw)
        sme_records = filter_results(sme_records, kw)
        # 기계/전기/제조/IT 등 전북기계공고 전공과 연관된 강소기업 공고를 우선 정렬
        sme_records = prioritize_by_department(sme_records)

        combined = worknet_records + alio_records + sme_records
        st.session_state.live_jobs = combined
        st.session_state.live_jobs_sources = (worknet_src, alio_src, sme_src)

    if st.session_state.live_jobs is not None:
        w_src, a_src, s_src = st.session_state.live_jobs_sources or ("backup", "backup", "backup")
        b1 = "🟢 고용24 실시간" if w_src == "live" else "🟡 고용24 예시(백업) 데이터"
        b2 = "🟢 잡알리오 실시간" if a_src == "live" else "🟡 잡알리오 예시(백업) 데이터"
        b3 = "🟢 강소기업 포털 실시간" if s_src == "live" else "🟡 강소기업 포털 예시(백업) 데이터"
        st.caption(f"{b1}  ·  {b2}  ·  {b3}")

        records = st.session_state.live_jobs
        if type_pick != "전체":
            records = [r for r in records if r.get("company_type") == type_pick]

        if not records:
            st.warning("🔍 검색 결과가 없습니다. 다른 키워드나 기업 유형으로 다시 시도해봐.")
        else:
            st.caption(f"검색 결과 {len(records)}건")
            for r in records:
                certs = r.get("required_certs") or []
                cert_str = ", ".join(certs) if certs else "정보 없음"
                ai_tip = r.get("ai_tip") or ""
                priority_badge = (
                    ' <span class="mjp-tag" style="background:' + GREEN + '; color:' + BG + ';">⭐ 전공 우선매칭</span>'
                    if r.get("company_type") == "강소기업" and r.get("department") in PRIORITY_DEPARTMENTS
                    else ""
                )
                st.markdown(f"""
                <div class="mjp-card">
                    <span class="mjp-tag">{r.get('company_type','')}</span>{priority_badge}
                    <div style="font-size:16px; font-weight:800; margin-top:6px;">{r.get('company','')}</div>
                    <div class="mjp-muted">{r.get('title','')} · {r.get('region','')} {r.get('salary','')}</div>
                    <div class="mjp-muted" style="margin-top:4px;">필수/우대 자격증: {cert_str}</div>
                </div>
                """, unsafe_allow_html=True)
                if ai_tip:
                    st.info(f"🤖 {ai_tip}")

# ============================================================
# TAB 3. 채용 대비 가이드 & 코멘토 커리큘럼 & OGQ 로드맵
# ============================================================
elif st.session_state.active_tab == "guide":
    st.markdown('<div class="mjp-disclaimer">🧪 선배 리뷰·면접질문·커리큘럼은 팀에서 구성한 예시 콘텐츠이며 실제 후기·데이터가 아닙니다.</div>',
                unsafe_allow_html=True)

    names = {c["name"]: c["id"] for c in COMPANY_SHOWCASE}
    default_name = COMPANY_BY_ID[st.session_state.selected_company_id]["name"] if st.session_state.selected_company_id else list(names.keys())[0]
    pick_name = st.selectbox("기업별 원스톱 채용 가이드 허브", list(names.keys()),
                              index=list(names.keys()).index(default_name))
    c = COMPANY_BY_ID[names[pick_name]]
    st.session_state.selected_company_id = c["id"]

    st.markdown(f"""
    <div class="mjp-card">
        <span class="mjp-tag">{c['size_tag']} · {c['field_tag']} 타깃</span>
        <div style="font-size:24px; font-weight:800; margin-top:8px;">{c['name']}</div>
        <div class="mjp-muted">{c['description']} · 고졸 채용 종합 만족도 예시 {render_stars(c['overall_rating'])}</div>
        <div class="mjp-muted" style="margin-top:6px;">인재상: <b style="color:{TEXT};">{', '.join(c['ideal_talent'])}</b>
        &nbsp;|&nbsp; 예시 합격자 평균 스펙: 내신 {c['avg_applicant_grade']}등급 · 자격증 {c['avg_applicant_certs']}개</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📝 이 회사로 자소서 쓰기", type="primary"):
        go_to("resume")
        st.rerun()

    st.markdown("##### 🏅 고졸 출신 선배들의 직무별 세부 평점 (예시)")
    rcols = st.columns(3)
    for i, (label, val) in enumerate(c["ratings"].items()):
        with rcols[i]:
            st.markdown(f"""<div class="mjp-card" style="text-align:center;">
                <div class="mjp-muted">{label}</div><div style="margin-top:6px;">{render_stars(val)}</div>
            </div>""", unsafe_allow_html=True)

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        st.markdown(f"""<div class="mjp-card" style="border-color:{GREEN};">
            <b style="color:{GREEN};">● 장점 (예시)</b>
            <div class="mjp-muted" style="margin-top:8px; color:{TEXT};">{c['pros']}</div></div>""",
            unsafe_allow_html=True)
    with pcol2:
        st.markdown(f"""<div class="mjp-card" style="border-color:{RED};">
            <b style="color:{RED};">● 단점/고충 (예시)</b>
            <div class="mjp-muted" style="margin-top:8px; color:{TEXT};">{c['cons']}</div></div>""",
            unsafe_allow_html=True)

    kcol1, kcol2 = st.columns(2)
    with kcol1:
        tags = "".join(f'<span class="mjp-tag">{ct}</span>' for ct in c["required_certs"])
        st.markdown(f'<div class="mjp-card"><b>🏆 필수 우대 자격증</b><br><br>{tags}</div>', unsafe_allow_html=True)
    with kcol2:
        st.markdown(f"""<div class="mjp-card"><b>📘 전공 필기시험 핵심 키워드</b>
            <div class="mjp-muted" style="margin-top:8px; color:{TEXT};">{c['exam_keywords']}</div></div>""",
            unsafe_allow_html=True)

    st.markdown("##### 🔑 예상 기출 면접 질문 3선 (예시)")
    for i, q in enumerate(c["interview_questions"]):
        st.markdown(f'<div class="mjp-interview"><span class="mjp-qbadge">인터뷰 질문 {i+1:02d}</span>Q. {q}</div>',
                     unsafe_allow_html=True)

    # ---- 코멘토 스타일 4주 커리큘럼 ----
    st.markdown("##### 📚 코멘토 스타일 4주 맞춤 커리큘럼 (예시)")
    curriculum = generate_curriculum(c)
    st.session_state.last_curriculum = curriculum
    for wk in curriculum:
        with st.expander(f"{wk['week']}주차 · {wk['title']}"):
            st.write(f"**학습 목표**: {wk['goal']}")
            st.write("**이번 주 할 일**")
            for t in wk["tasks"]:
                st.write(f"- {t}")
            st.write(f"**추천 프로젝트**: {wk['project']}")
            st.info(f"📁 포트폴리오 전략: {wk['portfolio_tip']}")

    # ---- OGQ 로드맵 (스탬프 인터랙션 + AI 컨설턴트 멘트) ----
    st.markdown("##### 🗺 OGQ 커리어 로드맵")
    stamp_cols = st.columns(4)
    for i, label in enumerate(ROADMAP_LABELS):
        with stamp_cols[i]:
            cls = "mjp-stamp-done" if i <= st.session_state.roadmap_step else "mjp-stamp-pending"
            icon = "✅" if i <= st.session_state.roadmap_step else "⭕"
            st.markdown(f'<div class="mjp-card {cls}" style="text-align:center; padding:10px;">{icon}<br>{label}</div>',
                         unsafe_allow_html=True)

    if st.session_state.roadmap_step < 3:
        next_label = ROADMAP_LABELS[st.session_state.roadmap_step + 1]
        if st.button(f"🐾 다음 단계 스탬프 찍기 → {next_label}"):
            st.session_state.roadmap_step += 1
            st.rerun()
    else:
        st.success("모든 단계를 완료했습니다! 🎉")

    consultant_msgs = {
        0: "일단 왼쪽 탭에서 스펙 진단부터 해보자! 목표가 명확해질 거야.",
        1: "자격증 준비 완료! 이제 위 4주 커리큘럼으로 포트폴리오를 만들어보자 💪",
        2: "포트폴리오까지 완성했다니 대단해! 이제 예상 면접 질문으로 실전 연습해보자 🎤",
        3: "모든 준비가 끝났어! 자신감을 가지고 지원해봐. 잘할 수 있을 거야 🚀",
    }
    st.info(f"🤖 AI 컨설턴트: {consultant_msgs[st.session_state.roadmap_step]}")

    # ---- PDF 리포트 다운로드 ----
    st.divider()
    student_name_for_pdf = st.session_state.user_nickname or "학생"
    if st.button("🖨 나만의 취업 성공 리포트 PDF 만들기"):
        base_dir = os.path.dirname(__file__)
        cover_excerpt = st.session_state.cover_letter or "(4탭에서 자기소개서를 먼저 생성하면 리포트에 포함됩니다.)"
        pdf_bytes = build_success_report_pdf(
            base_dir=base_dir, student_name=student_name_for_pdf, company=c,
            spec_result=st.session_state.last_spec_result or {
                "grade_score": 0, "cert_score": 0, "fit_score": 0, "talent_score": 0, "final_score": 0,
            },
            curriculum=curriculum, cover_letter_excerpt=cover_excerpt,
            roadmap_stage_label=ROADMAP_LABELS[st.session_state.roadmap_step],
        )
        st.download_button("📥 PDF 다운로드", data=pdf_bytes,
                            file_name=f"{student_name_for_pdf}_취업성공리포트.pdf",
                            mime="application/pdf")
        if not os.path.exists(os.path.join(base_dir, "fonts", "NanumGothic.ttf")):
            st.caption("⚠ 한글이 깨져 보인다면 `fonts/NanumGothic.ttf`를 프로젝트에 추가해줘.")

# ============================================================
# TAB 4. 합격 이력서 & 자소서
# ============================================================
elif st.session_state.active_tab == "resume":
    left, right = st.columns([1, 1.3])

    with left:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 나의 프로필 & 스토리 연동 기입")

        name = st.text_input("학생 이름", value=st.session_state.user_nickname or "", placeholder="예: 김우빈")
        target_dept = st.text_input("목표 입사 지원 부서", placeholder="예: 공정설비제어팀 엔지니어")

        company_names = [c["name"] for c in COMPANY_SHOWCASE]
        default_idx = 0
        if st.session_state.selected_company_id:
            comp = COMPANY_BY_ID[st.session_state.selected_company_id]
            if comp["name"] in company_names:
                default_idx = company_names.index(comp["name"])
        target_company_name = st.selectbox("목표 지원 회사", company_names, index=default_idx)

        story = st.text_area("나의 고교 이야기 (실패 극복, 동아리 성장 에피소드 등)", height=90)

        st.file_uploader("회사 고유 서식 양식 파일 추가 (.txt 파일)", type=["txt"])
        st.caption("※ 서식 파일을 올리면 스펙·자소서 정보를 해당 서식에 맞춰 조립합니다. (베타)")

        gen_clicked = st.button("✨ 스펙 맞춤형 자기소개서 자동 완성", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        target_company = next(c for c in COMPANY_SHOWCASE if c["name"] == target_company_name)

        if gen_clicked:
            gen_profile = {
                "name": name, "target_dept": target_dept, "grade": st.session_state.grade,
                "story": story, "strength": ", ".join(st.session_state.strength_keywords) or story,
                "certs": st.session_state.user_certs,
            }
            with st.spinner("자기소개서 초안을 작성하는 중..."):
                text, source = generate_cover_letter(
                    gen_profile, company=target_company, api_key=safe_secret("ANTHROPIC_API_KEY"),
                )
            st.session_state.cover_letter = text
            st.session_state.cover_letter_source = source
            st.session_state.selected_company_id = target_company["id"]

        src_badge = ""
        if st.session_state.cover_letter_source == "ai":
            src_badge = f'<span class="mjp-badge" style="background:{GREEN}; color:{BG};">🤖 AI 생성</span>'
        elif st.session_state.cover_letter_source == "template":
            src_badge = f'<span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">📐 템플릿 생성</span>'

        st.markdown(f"""
        <div class="mjp-card">
            <span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">DRAFT SHEET</span>
            {src_badge}
            <div style="font-size:18px; font-weight:800; margin-top:8px;">합격 자기소개서 전문 통합 시트</div>
            <div class="mjp-muted" style="margin-top:4px;">{target_company['name']} 인재상: {', '.join(target_company['ideal_talent'])}</div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.cover_letter:
            st.info("왼쪽에서 정보를 입력하고 '스펙 맞춤형 자기소개서 자동 완성'을 눌러줘.")
        else:
            st.text_area("자기소개서 초안", value=st.session_state.cover_letter, height=380, label_visibility="collapsed")
            st.download_button(
                "📥 자소서 통합 다운로드 (.txt)", data=st.session_state.cover_letter,
                file_name="자기소개서_초안.txt", mime="text/plain", use_container_width=True,
            )
