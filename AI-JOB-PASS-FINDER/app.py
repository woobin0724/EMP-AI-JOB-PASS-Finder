# -*- coding: utf-8 -*-
"""
AI Job Pass Finder — "Meister Job Pathfinder" (W3 본선 리팩토링판)
전북기계공고 E.M.P 팀 | 마이스터고 취업 성공 올인원 패스파인더

실행: streamlit run app.py

W3 반영 사항
------------
 #1 [core/matching.py]    100점 만점 정량 합격 점수 공식 (AI 호출 없는 로컬 연산)
 #2 [services/fallback.py] 전 API try-except + 백업 JSON 이중화 + LIVE/BACKUP 배지
 #3 [services/llm.py]     st.cache_data 자소서 캐싱 + st.secrets 기반 키 관리
 #4 [OGQ UI]              점수 구간별 반응형 스티커 · 로드맵 마일스톤 스탬프
 #5 [The Cut]             로그인/전문가 매칭은 MVP 제외 → '향후 로드맵' 탭으로 이관
"""

import os

import streamlit as st

from data.departments import (
    DEPARTMENT_LIST, DEPARTMENTS, get_category, get_employment_rate, get_majors_for_department,
)
from data.certifications import CERT_CODE_TO_NAME, get_bonus_points
from data.company_showcase import COMPANY_SHOWCASE, COMPANY_BY_ID, COMPANY_CATEGORIES, COMPANY_SIZE_TAGS
from data import ogq_assets as ogq

from core.matching import calc_spec_score, filter_results
from services import fallback as fb
from services.fallback import SourceTracker
from services.strong_sme_api import prioritize_by_department, PRIORITY_DEPARTMENTS
from services.llm import generate_cover_letter_cached, clear_cover_letter_cache, cost_guard_caption
from services.curriculum import generate_curriculum
from services.pdf_report import build_success_report_pdf

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

BADGE_COLORS = {"live": GREEN, "backup": GOLD, "ink": BG, "muted": MUTED}

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
.mjp-bar-track {{ background:{CARD_BORDER}; border-radius:999px; height:8px; width:100%; }}
.mjp-bar-fill {{ background:{GREEN}; border-radius:999px; height:8px; }}
.mjp-later {{
    background:{CARD}; border:1px dashed {CARD_BORDER}; border-left:4px solid {PURPLE};
    border-radius:12px; padding:16px 18px; margin-bottom:14px;
}}
</style>
""", unsafe_allow_html=True)


def safe_secret(key: str) -> str:
    """secrets.toml 이 없어도 예외 없이 빈 문자열을 반환한다."""
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


# ============================================================
# 1. 세션 상태 초기화
# ============================================================
MILESTONES = [
    ("cert", "자격증 준비", "목표 기업이 요구하는 자격증을 취득했거나 시험 접수를 마쳤습니다."),
    ("portfolio", "포트폴리오 완성", "4주 커리큘럼의 프로젝트 결과물을 문서로 정리했습니다."),
    ("interview", "면접 준비", "예상 기출 질문 3선에 대한 나만의 답변을 만들었습니다."),
]

DEFAULTS = {
    "active_tab": "spec",
    "student_name": "",
    "dept": DEPARTMENT_LIST[0],
    "grade": 3.0,
    "user_certs": [],
    "strength_keywords": [],
    "selected_company_id": None,
    "milestones": {key: False for key, _, _ in MILESTONES},
    "last_spec_result": None,
    "last_curriculum": None,
    "cover_letter": None,
    "cover_letter_source": None,
    "cover_letter_cached": False,
    "live_jobs": None,
    "tracker": SourceTracker(),
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

tracker: SourceTracker = st.session_state.tracker


def go_to(tab_key: str):
    st.session_state.active_tab = tab_key


def show_sticker(key: str, width: int = 130, caption: str | None = None):
    """OGQ 스티커를 렌더링한다. 이미지가 없으면 이모지로 자동 대체된다."""
    src = ogq.sticker(key)
    if src:
        try:
            st.image(src, width=width, caption=caption)
            return
        except Exception:
            pass
    st.markdown(
        f'<div style="font-size:{int(width * 0.42)}px; text-align:center;">{ogq.emoji(key)}</div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)


# ============================================================
# 2. 사이드바 — 표시 이름 + 데이터 연동 설정
#    (소셜 로그인은 MVP 범위에서 제외 → '향후 로드맵' 탭 참고)
# ============================================================
with st.sidebar:
    st.markdown("### 🧭 시작하기")
    st.session_state.student_name = st.text_input(
        "표시할 이름", value=st.session_state.student_name, placeholder="예: 김우빈",
    )
    st.caption("6주차 MVP에서는 계정 로그인 없이 바로 진단을 시작합니다. "
               "이유는 상단 '향후 로드맵' 탭에 정리해두었습니다.")

    st.divider()
    st.markdown("### ⚙️ 데이터 연동 설정 (선택)")
    qnet_key = st.text_input("Q-Net/공공데이터포털 서비스키", type="password",
                             value=safe_secret("QNET_API_KEY"))
    worknet_key = st.text_input("고용24(워크넷) Open API 인증키", type="password",
                                value=safe_secret("WORKNET_API_KEY"))
    st.caption("키가 없어도 앱은 백업 마스터 데이터로 100% 동작합니다.")
    st.caption(f"📦 내장 백업: {fb.backup_summary()}")

    st.divider()
    st.markdown("### 🎨 캐릭터 스티커")
    show_sticker("hello", width=110)
    st.caption(f"OGQ마켓 캐릭터 스티커 · 출처: {ogq.OGQ_MARKET_URL}")

# ============================================================
# 3. 헤더 + 데이터 출처 배지
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

# --- [W3 #2] 실시간 데이터 출처 배지 ---
st.markdown(fb.badge_html(tracker, BADGE_COLORS), unsafe_allow_html=True)

NAV_ITEMS = [
    ("spec", "📊 1. 스펙 진단 & 추천"),
    ("explore", "🔍 2. 실시간 기업 탐색기"),
    ("guide", "🛠 3. 커리어 로드맵 & 가이드"),
    ("resume", "📄 4. 합격 이력서 & 자소서"),
    ("next", "🚀 5. 향후 로드맵"),
]
nav_cols = st.columns(5)
for i, (key, label) in enumerate(NAV_ITEMS):
    with nav_cols[i]:
        btn_type = "primary" if st.session_state.active_tab == key else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            go_to(key)

st.write("")

# ============================================================
# 4. 데이터 로드 (캐싱 + 예외처리 이중화)
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_cert_names(api_key):
    """Q-Net 자격증 목록. 실패 시 백업 마스터로 전환된다."""
    df, source = fb.fetch_certifications_safe(api_key)
    names = df["name"].tolist() if "name" in df else []
    return names, source


ALL_CERT_NAMES, cert_source = load_cert_names(qnet_key)
tracker.record("Q-Net 자격증", cert_source)

ALL_TALENT_KEYWORDS = sorted({kw for c in COMPANY_SHOWCASE for kw in c["ideal_talent"]})


def certs_for_department(dept: str):
    codes = DEPARTMENTS.get(dept, {}).get("cert_codes", [])
    return [CERT_CODE_TO_NAME[c] for c in codes if c in CERT_CODE_TO_NAME]


def render_stars(rating: float) -> str:
    full = int(rating)
    return f'<span class="mjp-star">{"★" * full}{"☆" * (5 - full)}</span> ({rating:.1f})'


def score_bar(label: str, value: float, maximum: int) -> str:
    pct = 0 if not maximum else min(100, value / maximum * 100)
    return f"""
    <div style="margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; font-size:12px; color:{MUTED};">
        <span>{label}</span><span style="color:{TEXT}; font-weight:700;">{value} / {maximum}</span>
      </div>
      <div class="mjp-bar-track" style="margin-top:5px;">
        <div class="mjp-bar-fill" style="width:{pct:.0f}%;"></div>
      </div>
    </div>"""


def completed_milestones() -> int:
    return sum(1 for v in st.session_state.milestones.values() if v)


ROADMAP_STAGE_LABELS = ["시작 전", "자격증 준비 완료", "포트폴리오 완성", "면접 준비 완료"]

# ============================================================
# TAB 1. 스펙 진단 & 추천  (+ OGQ 반응형 스티커)
# ============================================================
if st.session_state.active_tab == "spec":
    left, right = st.columns([1.25, 1])

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

        grade = st.slider("내신 성적 등급 (마이스터고 5등급 성취평가제)", 1.0, 5.0,
                          st.session_state.grade, 0.1, key="grade_widget",
                          help="환산식: 30 × (5.0 − 등급) ÷ 4.0  |  1.0등급=30점, 2.0등급=22.5점")
        st.session_state.grade = grade

        dept_certs = certs_for_department(dept)
        cert_options = sorted(set(dept_certs) | set(ALL_CERT_NAMES))
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
            help="선택한 키워드가 기업 '인재상'과 일치하면 인재상 점수(10점)에 반영됩니다.",
        )
        st.session_state.strength_keywords = strengths

        company_names = ["선택 안 함 (일반 진단)"] + [c["name"] for c in COMPANY_SHOWCASE]
        pick = st.selectbox("정밀 진단할 목표 기업 (선택)", company_names, key="target_company_widget")
        target_company = None
        if pick != company_names[0]:
            target_company = next(c for c in COMPANY_SHOWCASE if c["name"] == pick)
            st.session_state.selected_company_id = target_company["id"]

        st.caption("※ 입력값을 바꾸면 오른쪽 점수가 **즉시** 갱신됩니다. "
                   "이 연산은 AI API 호출 없이 로컬 파이썬 알고리즘으로만 수행됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---- 실시간 점수 계산 (순수 로컬 연산, 과금 0원) ----
    dept_category = get_category(dept)
    result = calc_spec_score(
        grade=grade, user_certs=certs, dept_category=dept_category,
        company=target_company, strength_keywords=strengths,
    )
    st.session_state.last_spec_result = result

    sticker_key = ogq.sticker_key_for_score(result["final_score"])
    verdict, verdict_msg = ogq.SCORE_STICKER_MESSAGES[sticker_key]
    ring_color = {"success": GREEN, "cheer": GOLD, "comfort": RED}[sticker_key]

    with right:
        st.markdown(f"""
        <div class="mjp-card">
            <span class="mjp-badge" style="background:{ring_color}; color:{BG};">SPEC DIAGNOSIS · 실시간</span>
            <div style="display:flex; align-items:center; gap:16px; margin-top:12px;">
                <div style="width:104px; height:104px; border-radius:50%; background:{ring_color};
                            display:flex; flex-direction:column; align-items:center;
                            justify-content:center; color:{BG}; flex:none;">
                    <div style="font-size:27px; font-weight:800;">{result['final_score']}점</div>
                    <div style="font-size:10px;">100점 만점</div>
                </div>
                <div style="flex:1;">
                    <div style="font-size:17px; font-weight:800; color:{ring_color};">{verdict}</div>
                    <div class="mjp-muted" style="margin-top:6px; line-height:1.5;">{verdict_msg}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- [W3 #4] 점수 구간별 OGQ 반응형 스티커 ----
        sc1, sc2 = st.columns([1, 1.4])
        with sc1:
            show_sticker(sticker_key, width=150)
        with sc2:
            st.markdown(score_bar("내신 성취도", result["grade_score"], 30), unsafe_allow_html=True)
            st.markdown(score_bar("자격증 가산점", result["cert_score"], 40), unsafe_allow_html=True)
            st.markdown(score_bar("전공 적합성", result["fit_score"], 20), unsafe_allow_html=True)
            st.markdown(score_bar("인재상 일치도", result["talent_score"], 10), unsafe_allow_html=True)

        # ---- 자격증 인정 비율 상세 ----
        if result["cert_details"]:
            with st.expander("🔎 자격증 인정 비율 상세 보기", expanded=False):
                for d in result["cert_details"]:
                    icon = "✅" if d["ratio"] == 1.0 else ("🟡" if d["ratio"] > 0 else "⬜")
                    extra = f" ← 보유: {d['matched_by']}" if d["matched_by"] and d["ratio"] < 1.0 else ""
                    st.markdown(f"{icon} **{d['cert']}** · {d['status']}{extra}")
                st.caption("정확히 일치 100% · 직무 유사 자격증 70% 인정 → 평균 인정비율 × 40점")

        for tip in result["tips"]:
            st.info(f"🤖 {tip}")

    st.divider()

    # ---- Q-Net 자격 분석 가이드 & 매칭 기업 ----
    gcol1, gcol2 = st.columns(2)
    with gcol1:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown(f'<span class="mjp-badge" style="background:{BLUE}; color:#fff;">Q-NET</span> '
                    f'**자격 분석 가이드 (예시 가산점)**', unsafe_allow_html=True)
        if not certs:
            st.caption("자격증을 선택하면 기업 규모별 예시 가산점이 즉시 표시됩니다.")
        else:
            size_for_bonus = st.radio("기준 기업 규모", COMPANY_SIZE_TAGS[1:], horizontal=True,
                                      key="qnet_bonus_size", label_visibility="collapsed")
            for cert in certs:
                st.markdown(f"- **{cert}** → {size_for_bonus} 예시 가산점 "
                            f"**+{get_bonus_points(cert, size_for_bonus)}점**")
            st.caption("※ 실제 공식 가산점 규정이 아닌 예시 데이터입니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    with gcol2:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown("🎯 **매칭 기업 탐색 (실시간 반영)**")
        size_pick = st.radio("기업 규모", COMPANY_SIZE_TAGS[1:], horizontal=True,
                             key="match_size", label_visibility="collapsed")
        matched = [c for c in COMPANY_SHOWCASE
                   if c["category"] == dept_category and c["size_tag"] == size_pick]
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
# TAB 2. 실시간 기업 탐색기
# ============================================================
elif st.session_state.active_tab == "explore":
    st.markdown('<div class="mjp-disclaimer">🧪 기업 카드(별점·복지 등)는 예시(모의) 데이터입니다. '
                '하단 "실시간 채용공고"는 실제 API 연동을 시도하고, 실패 시 백업 데이터로 전환됩니다.</div>',
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
    st.caption("세 소스를 동시에 호출하고, 응답하지 않는 소스는 즉시 백업 마스터 데이터로 대체합니다. "
               "기계·전기·제조·IT 전공 연관 강소기업 공고는 상단에 우선 노출됩니다.")

    kw = st.text_input("검색 키워드 (기업명·공고명·자격증)", placeholder="예: 전기기능사, CNC, 정보처리, 한국전력공사")
    type_pick = st.selectbox("기업 유형", ["전체", "대기업", "중견기업", "중소기업", "스타트업", "공기업", "강소기업"])

    if st.button("📡 지금 불러오기", type="primary"):
        with st.spinner("고용24·잡알리오·강소기업 포털 호출 중... 실패 시 백업 데이터로 자동 전환됩니다."):
            worknet_df, _ = fb.fetch_jobs_safe(worknet_key, kw, tracker=tracker)
            alio_records, _ = fb.fetch_alio_safe(tracker=tracker)
            sme_records, _ = fb.fetch_strong_sme_safe(tracker=tracker)

        worknet_records = worknet_df.to_dict("records") if hasattr(worknet_df, "to_dict") else list(worknet_df)
        alio_records = filter_results(alio_records, kw)
        sme_records = prioritize_by_department(filter_results(sme_records, kw))

        st.session_state.live_jobs = worknet_records + alio_records + sme_records
        st.rerun()

    if st.session_state.live_jobs is not None:
        st.markdown(fb.badge_html(tracker, BADGE_COLORS), unsafe_allow_html=True)
        for name, err in tracker.errors():
            st.caption(f"⚠️ {name}: {err} → 백업 데이터로 전환됨")

        records = st.session_state.live_jobs
        if type_pick != "전체":
            records = [r for r in records if r.get("company_type") == type_pick]

        if not records:
            st.warning("🔍 검색 결과가 없습니다. 다른 키워드나 기업 유형으로 다시 시도해보세요.")
            show_sticker("thinking", width=120)
        else:
            st.caption(f"검색 결과 {len(records)}건")
            for r in records:
                certs_list = r.get("required_certs") or []
                cert_str = ", ".join(certs_list) if certs_list else "정보 없음"
                priority_badge = (
                    f' <span class="mjp-tag" style="background:{GREEN}; color:{BG};">⭐ 전공 우선매칭</span>'
                    if r.get("company_type") == "강소기업" and r.get("department") in PRIORITY_DEPARTMENTS
                    else ""
                )
                st.markdown(f"""
                <div class="mjp-card">
                    <span class="mjp-tag">{r.get('company_type', '')}</span>{priority_badge}
                    <div style="font-size:16px; font-weight:800; margin-top:6px;">{r.get('company', '')}</div>
                    <div class="mjp-muted">{r.get('title', '')} · {r.get('region', '')} {r.get('salary', '')}</div>
                    <div class="mjp-muted" style="margin-top:4px;">필수/우대 자격증: {cert_str}</div>
                </div>
                """, unsafe_allow_html=True)
                if r.get("ai_tip"):
                    st.info(f"🤖 {r['ai_tip']}")

# ============================================================
# TAB 3. 커리어 로드맵 & 채용 대비 가이드 (+ OGQ 마일스톤 스탬프)
# ============================================================
elif st.session_state.active_tab == "guide":
    st.markdown('<div class="mjp-disclaimer">🧪 선배 리뷰·면접질문·커리큘럼은 팀이 구성한 예시 콘텐츠이며 실제 후기가 아닙니다.</div>',
                unsafe_allow_html=True)

    names = {c["name"]: c["id"] for c in COMPANY_SHOWCASE}
    default_name = (COMPANY_BY_ID[st.session_state.selected_company_id]["name"]
                    if st.session_state.selected_company_id else list(names.keys())[0])
    pick_name = st.selectbox("기업별 원스톱 채용 가이드 허브", list(names.keys()),
                             index=list(names.keys()).index(default_name))
    c = COMPANY_BY_ID[names[pick_name]]
    st.session_state.selected_company_id = c["id"]

    # ------------------------------------------------------------
    # 🗺 커리어 로드맵 — 3단계 마일스톤 + OGQ 스탬프
    # ------------------------------------------------------------
    st.markdown("### 🗺 나의 커리어 로드맵")
    done = completed_milestones()
    st.progress(done / len(MILESTONES), text=f"{done} / {len(MILESTONES)} 단계 완료")

    mcols = st.columns(3)
    for i, (key, label, desc) in enumerate(MILESTONES):
        with mcols[i]:
            checked = st.checkbox(f"**{label}**", value=st.session_state.milestones[key],
                                  key=f"ms_{key}")
            st.session_state.milestones[key] = checked
            st.caption(desc)
            if checked:
                # 완료 시 단순 텍스트 대신 OGQ 스탬프 이미지를 찍는다
                show_sticker("stamp", width=120)
                st.markdown(
                    f'<div style="text-align:center; color:{GREEN}; font-size:12px; font-weight:700;">'
                    f'STAMPED · {label} 완료</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="height:126px; border:1px dashed {CARD_BORDER}; border-radius:12px;'
                    f'display:flex; align-items:center; justify-content:center; color:{MUTED};'
                    f'font-size:12px;">스탬프 자리</div>', unsafe_allow_html=True)

    if done == len(MILESTONES):
        fin1, fin2 = st.columns([1, 3])
        with fin1:
            show_sticker("clap", width=140)
        with fin2:
            st.success("세 개의 스탬프를 모두 모았습니다! 이제 실제 지원서를 넣을 준비가 끝났어요. 🎉")
    else:
        consultant = {
            0: "먼저 목표 기업이 요구하는 자격증부터 확인해봅시다. 아래 '필수 우대 자격증'을 보세요.",
            1: "좋아요! 이제 아래 4주 커리큘럼으로 포트폴리오를 만들어봅시다 💪",
            2: "포트폴리오까지 완성했네요. 마지막으로 예상 면접 질문에 답을 만들어보세요 🎤",
        }[done]
        st.info(f"🤖 AI 컨설턴트: {consultant}")

    st.divider()

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
        st.markdown(f'<div class="mjp-card"><b>🏆 필수 우대 자격증</b><br><br>{tags}</div>',
                    unsafe_allow_html=True)
    with kcol2:
        st.markdown(f"""<div class="mjp-card"><b>📘 전공 필기시험 핵심 키워드</b>
            <div class="mjp-muted" style="margin-top:8px; color:{TEXT};">{c['exam_keywords']}</div></div>""",
                    unsafe_allow_html=True)

    st.markdown("##### 🔑 예상 기출 면접 질문 3선 (예시)")
    for i, q in enumerate(c["interview_questions"]):
        st.markdown(f'<div class="mjp-interview"><span class="mjp-qbadge">인터뷰 질문 {i + 1:02d}</span>Q. {q}</div>',
                    unsafe_allow_html=True)

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

    # ---- PDF 리포트 ----
    st.divider()
    student_name_for_pdf = st.session_state.student_name or "학생"
    if st.button("🖨 나만의 취업 성공 리포트 PDF 만들기"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cover_excerpt = st.session_state.cover_letter or "(4번 탭에서 자기소개서를 먼저 생성하면 리포트에 포함됩니다.)"
        try:
            pdf_bytes = build_success_report_pdf(
                base_dir=base_dir, student_name=student_name_for_pdf, company=c,
                spec_result=st.session_state.last_spec_result or {
                    "grade_score": 0, "cert_score": 0, "fit_score": 0,
                    "talent_score": 0, "final_score": 0,
                },
                curriculum=curriculum, cover_letter_excerpt=cover_excerpt,
                roadmap_stage_label=ROADMAP_STAGE_LABELS[completed_milestones()],
            )
            st.download_button("📥 PDF 다운로드", data=pdf_bytes,
                               file_name=f"{student_name_for_pdf}_취업성공리포트.pdf",
                               mime="application/pdf")
            if not os.path.exists(os.path.join(base_dir, "fonts", "NanumGothic.ttf")):
                st.caption("⚠ 한글이 깨져 보인다면 `fonts/NanumGothic.ttf`를 프로젝트에 추가하세요.")
        except Exception as exc:
            st.error(f"PDF 생성 중 문제가 발생했습니다: {exc}")

# ============================================================
# TAB 4. 합격 이력서 & 자소서 (캐싱된 LLM 호출)
# ============================================================
elif st.session_state.active_tab == "resume":
    left, right = st.columns([1, 1.3])

    with left:
        st.markdown('<div class="mjp-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 나의 프로필 & 스토리 연동 기입")

        name = st.text_input("학생 이름", value=st.session_state.student_name, placeholder="예: 김우빈")
        target_dept = st.text_input("목표 입사 지원 부서", placeholder="예: 공정설비제어팀 엔지니어")

        company_names = [c["name"] for c in COMPANY_SHOWCASE]
        default_idx = 0
        if st.session_state.selected_company_id:
            comp = COMPANY_BY_ID[st.session_state.selected_company_id]
            if comp["name"] in company_names:
                default_idx = company_names.index(comp["name"])
        target_company_name = st.selectbox("목표 지원 회사", company_names, index=default_idx)

        story = st.text_area("나의 고교 이야기 (실패 극복, 동아리 성장 에피소드 등)", height=110)

        gen_clicked = st.button("✨ 스펙 맞춤형 자기소개서 자동 완성", type="primary",
                                use_container_width=True)
        if st.button("♻️ 캐시 비우고 새로 생성", use_container_width=True):
            clear_cover_letter_cache()
            st.toast("캐시를 비웠습니다. 다음 생성은 API를 새로 호출합니다.")

        st.caption(cost_guard_caption())
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        target_company = next(c for c in COMPANY_SHOWCASE if c["name"] == target_company_name)

        if gen_clicked:
            gen_profile = {
                "name": name, "target_dept": target_dept, "grade": st.session_state.grade,
                "story": story,
                "strength": ", ".join(st.session_state.strength_keywords) or story,
                "certs": st.session_state.user_certs,
            }
            with st.spinner("자기소개서 초안을 작성하는 중..."):
                text, source, cache_hit = generate_cover_letter_cached(gen_profile, target_company)
            st.session_state.cover_letter = text
            st.session_state.cover_letter_source = source
            st.session_state.cover_letter_cached = cache_hit
            st.session_state.selected_company_id = target_company["id"]

        badges = ""
        if st.session_state.cover_letter_source == "ai":
            badges += f'<span class="mjp-badge" style="background:{GREEN}; color:{BG};">🤖 AI 생성</span> '
        elif st.session_state.cover_letter_source == "template":
            badges += f'<span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">📐 템플릿 생성</span> '
        if st.session_state.cover_letter_cached:
            badges += f'<span class="mjp-badge" style="background:{BLUE}; color:#fff;">⚡ 캐시 응답 · API 호출 0회</span>'

        st.markdown(f"""
        <div class="mjp-card">
            <span class="mjp-badge" style="background:{CARD_BORDER}; color:{MUTED};">DRAFT SHEET</span>
            {badges}
            <div style="font-size:18px; font-weight:800; margin-top:10px;">합격 자기소개서 전문 통합 시트</div>
            <div class="mjp-muted" style="margin-top:4px;">{target_company['name']} 인재상: {', '.join(target_company['ideal_talent'])}</div>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.cover_letter:
            icol1, icol2 = st.columns([1, 2])
            with icol1:
                show_sticker("encourage", width=130)
            with icol2:
                st.info("왼쪽에서 정보를 입력하고 '스펙 맞춤형 자기소개서 자동 완성'을 눌러주세요.")
        else:
            st.text_area("자기소개서 초안", value=st.session_state.cover_letter, height=380,
                         label_visibility="collapsed")
            st.download_button("📥 자소서 통합 다운로드 (.txt)", data=st.session_state.cover_letter,
                               file_name="자기소개서_초안.txt", mime="text/plain",
                               use_container_width=True)

# ============================================================
# TAB 5. 향후 로드맵 (The Cut) — MVP에서 덜어낸 기능들
# ============================================================
elif st.session_state.active_tab == "next":
    tcol1, tcol2 = st.columns([2.4, 1])
    with tcol1:
        st.markdown("### 🚀 지금 만들지 '않은' 것들")
        st.markdown(
            "메신저 앱을 만든다면 **채팅은 필수지만 이모티콘은 아닙니다.** 이모티콘이 나쁜 기능이라서가 "
            "아니라, 채팅이 동작하는지 먼저 확인해야 이모티콘을 만들 이유가 생기기 때문입니다.\n\n"
            "저희 6주차 MVP도 같은 기준으로 잘라냈습니다. 아래 기능들은 **버린 것이 아니라 "
            "검증 순서를 뒤로 미룬 것**이며, 각각이 어떤 가설을 확인한 뒤에 열릴지 적어두었습니다."
        )
    with tcol2:
        show_sticker("thanks", width=150)

    CUT_FEATURES = [
        {
            "icon": "🔐", "title": "카카오·네이버 소셜 로그인",
            "when": "Next Release · v1.1",
            "why": "로그인은 '다시 돌아올 이유'가 있을 때 필요한 기능입니다. 지금 검증할 가설은 "
                   "\"점수 진단 한 번이 학생에게 유용한가\"이므로, 계정 없이 즉시 진단이 되는 편이 "
                   "가입 이탈 없이 더 많은 피드백을 모읍니다.",
            "trigger": "재방문 요청(= 진단 결과를 저장하고 싶다는 요구)이 관측되는 순간.",
        },
        {
            "icon": "🧑‍🏫", "title": "현직자·선배 1:1 전문가 매칭",
            "when": "Next Release · v1.2",
            "why": "매칭은 학생과 현직자 양쪽이 모두 모여야 성립하는 양면 시장입니다. 한쪽만 있는 "
                   "상태로 만들면 빈 채팅방만 남습니다. 대신 지금은 선배 리뷰·예상 면접질문 카드로 "
                   "\"현직자 정보에 대한 수요\"가 실재하는지부터 확인합니다.",
            "trigger": "가이드 탭 체류시간과 '더 묻고 싶다'는 요청 빈도.",
        },
        {
            "icon": "🔔", "title": "공고 마감 알림 · 푸시",
            "when": "Backlog",
            "why": "알림은 사용자가 이미 특정 공고를 '내 것'으로 찜한 뒤에야 의미가 있습니다. "
                   "찜하기가 로그인에 의존하므로 자연스럽게 로그인 다음 순서가 됩니다.",
            "trigger": "관심 공고 저장 기능 출시 이후.",
        },
        {
            "icon": "🏫", "title": "학교 관리자용 취업 현황 대시보드",
            "when": "Backlog",
            "why": "선생님용 대시보드는 학생 데이터가 충분히 쌓여야 값이 채워집니다. 학생 사용이 "
                   "먼저 검증되지 않으면 빈 그래프를 만드는 일이 됩니다.",
            "trigger": "누적 진단 데이터가 유의미한 규모에 도달했을 때.",
        },
    ]

    ccols = st.columns(2)
    for i, f in enumerate(CUT_FEATURES):
        with ccols[i % 2]:
            st.markdown(f"""
            <div class="mjp-later">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="font-size:24px;">{f['icon']}</div>
                    <div>
                        <div style="font-size:16px; font-weight:800; color:{TEXT};">{f['title']}</div>
                        <span class="mjp-badge" style="background:{PURPLE}; color:#fff;">{f['when']}</span>
                    </div>
                </div>
                <div class="mjp-muted" style="margin-top:12px; line-height:1.6;">{f['why']}</div>
                <div style="margin-top:10px; font-size:12px; color:{GREEN};">▸ 열림 조건: {f['trigger']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### ✅ 지금 6주차에 남긴 것 (MVP 범위)")
    kept = [
        ("📊 스펙 진단", "100점 만점 합격 점수 — 서비스의 존재 이유. 이것 하나가 안 되면 나머지는 무의미합니다."),
        ("🔍 공고 탐색", "실시간 API + 백업 이중화 — 시연 중에도 절대 멈추지 않는 데이터 파이프라인."),
        ("🗺 커리어 로드맵", "3단계 마일스톤 스탬프 — 진단 이후 '그래서 뭘 하지'에 답하는 최소 장치."),
        ("📄 자소서 초안", "캐싱된 생성기 — 비용 상한을 지키면서도 결과물을 손에 쥐어주는 마무리."),
    ]
    kcols = st.columns(4)
    for i, (title, desc) in enumerate(kept):
        with kcols[i]:
            st.markdown(f"""<div class="mjp-card" style="border-color:{GREEN}; height:100%;">
                <div style="font-weight:800; color:{TEXT};">{title}</div>
                <div class="mjp-muted" style="margin-top:8px; line-height:1.55;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    scol1, scol2 = st.columns([1, 2.2])
    with scol1:
        show_sticker("sheet", width=260)
    with scol2:
        st.markdown("#### 🎨 캐릭터 스티커에 대하여")
        st.markdown(
            "점수 결과와 로드맵 스탬프에 쓰인 캐릭터는 네이버 OGQ마켓의 창작자 스티커입니다. "
            "숫자만 보여주는 진단 도구는 낮은 점수를 받은 학생을 밀어냅니다. 같은 48점이라도 "
            "위로하는 캐릭터가 옆에 있으면 다음 화면으로 넘어갈 확률이 달라진다는 것이 "
            "W2 유저 인터뷰에서 가장 반복된 반응이었습니다."
        )
        st.caption(f"출처: {ogq.OGQ_MARKET_URL} · 교내 프로젝트 시연 용도이며, 외부 배포 시 "
                   f"창작자 이용 허락 또는 OGQ마켓 라이선스 정책 확인이 필요합니다.")
