# -*- coding: utf-8 -*-
"""
views/privacy.py
[big-patch 6단계] 개인정보 처리방침 — 로그인 없이 볼 수 있는 화면

▣ 원칙: 코드가 실제로 하는 일만 쓴다
   아래 표의 항목은 services/store.py(_default_user · save_profile), services/usage_log.py,
   services/reactions.py, services/ai_quota.py 가 저장하는 키와 1:1 로 맞춘다.
   저장 항목을 바꾸면 이 화면도 함께 고친다(tests/test_privacy.py 가 키 목록을 확인한다).
"""

import streamlit as st

from core import session as ss
from services import storage_backend
from ui.components import render_html, section_title

# (분류, 항목, 저장 위치 키)
STORED = [
    ("계정", "사용자 ID(게스트는 이어하기 코드가 들어간 ID, 소셜 로그인은 제공자 ID) · 로그인 방식 · "
             "표시 이름(닉네임 또는 소셜 계정 이름) · 이메일(소셜 로그인이 알려준 경우) · 역할 · 반 코드 · "
             "가입·최근 접속 시각", "main"),
    ("스펙 진단", "학과 · 내신 등급 · 목표 기업 · 자격증 · 강점 키워드 · 점수 기록(최근 100건)", "main"),
    ("활동", "찜한 기업 · 열람한 기업 · 커리어 로드맵 단계", "main"),
    ("선생님", "반을 만들 때 입력한 학교 · 학년 · 반", "main"),
    ("사용 통계", "해시 ID(원래 ID 로 되돌릴 수 없음) · 접속한 날짜 · 화면 이동 · 스토리 관심/패스 · "
                 "쓴 기능 이름 · 오늘 AI 사용 횟수. 이름·입력 내용은 없음", "usage"),
    ("스토리 반응", "사용자 ID · 기업 · 관심/패스 · 시각 (다시 접속해도 관심 목록이 남도록)", "reactions"),
]

NOT_STORED = [
    "자소서 생성에 넣은 재료와 만들어진 자소서",
    "첨삭받으려고 붙여넣은 초안",
    "모의 면접 답변",
    "PDF 리포트",
]

WHERE = {
    "main": "서비스 저장소의 사용자 문서",
    "usage": "서비스 저장소의 사용 기록 문서",
    "reactions": "서버의 반응 기록 파일",
}

DELETION = [
    ("학생이 마이페이지에서 '내 기록 지우기'를 누를 때", "계정·스펙·활동 기록을 즉시 비우고 반 명단에서 뺍니다. "
     "사용 통계와 스토리 반응 기록도 함께 지웁니다."),
    ("'반에서 나가기'를 누를 때", "반 명단에서 빠집니다(선생님 화면에서 사라짐)."),
    ("자동으로", "점수 기록은 최근 100건, 사용 통계 이벤트는 최근 20,000건만 남기고 오래된 것부터 지웁니다. "
     "AI 사용 횟수는 오늘 것만 남깁니다."),
    ("AI 결과 임시 보관", "같은 요청을 다시 부르지 않으려고 서버 메모리에 최대 1시간 보관합니다(저장소에는 남지 않음)."),
    ("서버를 다시 배포할 때", "외부 저장소(Supabase)를 연결하지 않은 서버에서는 저장 파일이 초기화됩니다."),
    ("선생님 계정 삭제", "반이 함께 사라지므로 화면에서 지우지 않고 팀에 요청해 주세요. [연락 방법: 팀 확인 필요]"),
]

SENT_OUT = [
    ("소셜 로그인(카카오 · 네이버 · 구글)", "로그인할 때 그 서비스에서 이름 · 이메일 · 계정 ID 를 받아옵니다."),
    ("AI 기능(프리미엄 · 시연 계정만)", "자소서 재료 · 첨삭 초안 · 면접 답변 · 점수 요약이 답을 만들기 위해 "
     "Anthropic 의 Claude API 로 전송됩니다. 무료 계정은 전송하지 않습니다(규칙 기반으로 처리)."),
    ("공공 채용 API(고용24 · Q-Net)", "검색어만 보냅니다. 개인 정보는 보내지 않습니다."),
]


def _rows(pairs) -> str:
    return "".join(f'<div class="mjp-sim-row"><span class="mjp-sim-name">{a}<small>{b}</small></span></div>'
                   for a, b in pairs)


def render() -> None:
    if st.button("← 돌아가기", key="privacy_back"):
        ss.goto(ss.PAGE_HUB if ss.is_authed() else ss.PAGE_LOGIN)
    section_title("개인정보 처리방침", icon_name="user", eyebrow="개인정보", sub=
                  "무엇을 저장하는지, 어디에 저장하는지, 언제 지우는지 — 이 서비스의 코드가 실제로 하는 일만 적었습니다.")

    st.markdown("#### 저장하는 것")
    render_html(f'<div class="mjp-sim">{_rows((f"{c} · {WHERE[w]}", items) for c, items, w in STORED)}</div>')

    st.markdown("#### 저장하지 않는 것")
    render_html('<div class="mjp-sim">' + _rows(
        (x, "화면을 쓰는 동안 브라우저 세션에만 있고, 창을 닫으면 사라집니다.") for x in NOT_STORED) + "</div>")

    st.markdown("#### 어디에 저장하나요")
    status = storage_backend.status()
    render_html('<div class="mjp-sim">' + _rows([
        ("외부 저장소를 연결한 경우", "Supabase(Postgres) 데이터베이스의 app_state 표 — 사용자 문서(main)와 사용 기록(usage)"),
        ("연결하지 않은 경우", "앱 서버의 파일(data/userdata/store.json · usage.json)"),
        ("반응 기록", "앱 서버의 파일(data/reactions.json)"),
        ("브라우저 주소", "새로고침해도 로그인이 유지되도록 주소 끝에 사용자 ID(uid)와 화면 이름이 붙습니다. "
         "게스트 ID 에는 이어하기 코드가 들어 있으니 주소를 다른 사람에게 보내지 마세요. 로그아웃하면 지워집니다."),
        ("지금 이 서버", f"{status['name']}"),
    ]) + "</div>")

    st.markdown("#### 언제 지우나요")
    render_html(f'<div class="mjp-sim">{_rows(DELETION)}</div>')

    st.markdown("#### 밖으로 보내는 것")
    render_html(f'<div class="mjp-sim">{_rows(SENT_OUT)}</div>')

    st.caption("이 방침은 서비스 코드 기준으로 작성했습니다(2026-10). 학교 단위 도입 시 학교·교육청의 "
               "개인정보 보호 지침에 맞춰 동의 절차와 보관 기간을 다시 정합니다. [팀 확인 필요]")
