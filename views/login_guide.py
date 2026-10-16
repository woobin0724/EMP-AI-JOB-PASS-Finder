# -*- coding: utf-8 -*-
"""
views/login_guide.py
로그인 화면 위쪽의 '사용법 · 자주 묻는 질문' 영역

▣ 왜 랜딩에서 옮겼나
   랜딩 아래에 사용법을 두었더니, 학생들이 그 내용이 있는 줄도 모르고
   '시작하기'만 누르고 지나갔다. 시작하기를 누른 직후(로그인 화면)는 어차피
   한 번은 지나가는 자리라, 여기에 사용법을 두고 로그인은 바로 아래로 내렸다.
   급한 사람은 맨 위 '바로 로그인하기 ↓' 로 건너뛴다.

▣ 길이
   STEP·핵심 기능·FAQ 를 전부 펼쳐 두면 폰에서 열 화면이 넘는다. 제목만 보이고
   누르면 펼쳐지는 st.expander 로 묶었다. 단, 예시 데이터 안내는 접지 않는다
   (예시 데이터 표시는 덜 보이게 만들지 않는다는 원칙).

문구 출처
   · STEP 1~4      — core.session.FEATURES (메인 허브와 같은 문구)
   · 핵심 기능 3개  — 기존 랜딩의 가치 제안 카드 문구 그대로
   · 100점 구성     — 스펙 진단 세부 점수 만점과 같은 값 (views/tab_spec.py)
   · FAQ           — 팀이 작성한 문구 + 앱 화면에 있던 안내 문구
"""

import streamlit as st

from core import session as ss
from ui.components import disclaimer, render_html
from ui.theme import BRAND

# 100점의 구성 — 스펙 진단 화면의 세부 점수 만점과 같은 값 (views/tab_spec.py)
_SCORE_PARTS = [
    ("내신 성취도", "30점", "5등급 성취평가제를 정량 환산"),
    ("자격증 가산점", "40점", "직무 유사 자격증은 70% 인정"),
    ("전공 적합성", "20점", "학과 계열과 기업 산업 분류의 일치"),
    ("인재상 일치도", "10점", "나의 강점 키워드와 기업 인재상"),
]

# 기존 랜딩의 가치 제안 3가지 (제목·설명 문구 그대로)
_POINTS = [
    ("100점 만점 합격 지수",
     "5등급 성취평가제를 정량 환산하고 자격증 인정 비율까지 계산합니다. "
     "AI 호출 없는 로컬 연산이라 입력하는 즉시 점수가 바뀝니다."),
    ("3개 출처 통합 검색",
     "고용24·잡알리오·강소기업 포털을 동시에 호출합니다. "
     "한 소스가 죽어도 백업 데이터로 즉시 전환돼 화면이 멈추지 않습니다."),
    ("OGQ 캐릭터 성장 스탬프",
     "점수와 로드맵 단계에 맞춰 캐릭터가 반응합니다. "
     "낮은 점수를 받은 학생이 화면을 닫지 않게 만드는 장치입니다."),
]

# 자주 묻는 질문 — (질문, 답). '__SCORE_PARTS__' 자리에는 100점 구성 타일이 들어간다.
_FAQ = [
    ("이 서비스는 뭘 해주나요?",
     "내 내신 등급과 자격증으로 목표 기업에 얼마나 가까운지 100점 만점 '합격 지수'로 보여줘요. "
     "그 점수를 바탕으로 기업 탐색, 채용 준비, 자소서 작성까지 한곳에서 이어서 할 수 있어요."),
    ("회원가입을 꼭 해야 하나요?",
     "아니요. 닉네임만 입력하면 게스트로 바로 시작할 수 있어요. 모든 기본 기능을 게스트로 쓸 수 있어요."),
    ("게스트로 했는데, 다음에 들어오면 기록이 사라지나요?",
     "마이페이지에 있는 6자리 '이어하기 코드'를 적어두세요. 다음에 로그인 화면에서 이 코드를 "
     "입력하면 지난 기록을 그대로 불러올 수 있어요."),
    ("합격 지수는 어떻게 계산되나요?",
     "내신 30점 + 자격증 40점 + 전공 적합성 20점 + 인재상 일치도 10점, 총 100점이에요. "
     "AI가 아니라 정해진 계산식으로 바로 계산하기 때문에 입력을 바꾸면 점수도 즉시 바뀌어요. "
     "80점 이상은 '합격 안정권', 50~79점은 '분발 필요', 50점 미만은 '보완 시급'으로 보여줘요."
     "__SCORE_PARTS__"),
    ("점수가 낮게 나왔어요. 떨어진다는 뜻인가요?",
     "아니요. 합격 지수는 합격 여부를 예측하는 게 아니라, 지금 내 스펙에서 무엇을 보완하면 좋을지 "
     "알려주는 지표예요. 점수 아래에 있는 항목별 막대와 '다음 행동 제안'을 참고해보세요."),
    ("채용 공고는 어디서 가져오나요?",
     "고용24·잡알리오·강소기업 포털을 동시에 호출합니다. "
     "한 소스가 죽어도 백업 데이터로 즉시 전환돼 화면이 멈추지 않습니다."),
    ("기업 정보는 실제 정보인가요?",
     "기업 분석 카드에 나오는 기업명과 평점·리뷰·면접 질문 등은 서비스 이해를 돕기 위해 팀이 만든 "
     "예시 데이터예요. 화면에 '예시 데이터' 표시가 있는 정보는 실제 기업 정보가 아니니 참고용으로만 "
     "봐주세요. 채용공고는 공식 API와 연결된 경우 실제 데이터를 보여주고, 화면의 "
     "LIVE API / BACKUP DATA / CURATED 표시로 출처를 구분할 수 있어요."),
    ("기업 스토리는 어떻게 보나요?",
     "카드를 넘기면서 기업을 둘러보고, 마음에 들면 '관심', 아니면 '패스'를 누르면 돼요. "
     "관심을 누른 기업은 따로 모아볼 수 있어요."),
    ("자소서도 AI가 써주나요?",
     "네, 문체와 분량을 골라 초안을 만들 수 있고, 직접 쓴 자소서를 첨삭받을 수도 있어요. "
     "AI 기능을 쓸 수 없는 계정이라면 '요청문 복사' 버튼으로 같은 지시문을 복사해서 무료 AI 채팅에 "
     "붙여넣어 쓸 수 있어요. AI가 만든 초안은 꼭 내 경험에 맞게 직접 고쳐서 사용하세요."),
    ("선생님도 쓸 수 있나요?",
     "네. 역할 선택에서 '선생님'을 고르고 학교·학년·반을 입력하면 6자리 반 코드가 만들어져요. "
     "학생들이 이 코드로 반에 들어오면 반 평균 점수와 학생별 진행 상황을 한 화면에서 볼 수 있어요."),
    ("반 코드는 꼭 입력해야 하나요?",
     "아니요, 건너뛰어도 돼요. 나중에 마이페이지에서 입력할 수 있어요."),
    ("학생/선생님 역할을 잘못 골랐어요.",
     "선택한 역할은 나중에 마이페이지에서 바꿀 수 있어요."),
    ("내 정보는 안전한가요?",
     "이름, 학교, 입력한 내용은 사용 기록에 남기지 않아요. 서비스 개선을 위한 접속 기록은 개인을 "
     "알아볼 수 없는 형태로만 저장해요."),
    ("결과를 따로 저장할 수 있나요?",
     "가이드 화면에서 PDF 리포트로 내려받을 수 있어요."),
]


def _score_parts_html() -> str:
    tiles = "".join(f"""
        <div class="mjp-tile">
            <div class="mjp-tile-label">{label}</div>
            <div class="mjp-tile-value" style="color:{BRAND};">{value}</div>
            <div class="mjp-tile-note">{note}</div>
        </div>""" for label, value, note in _SCORE_PARTS)
    return f'<div class="mjp-tiles mjp-tiles-4" style="margin-top:14px;">{tiles}</div>'


def _answer(text: str) -> None:
    body, marker, _ = text.partition("__SCORE_PARTS__")
    render_html(f'<div class="mjp-faq-a">{body}</div>')
    if marker:
        render_html(_score_parts_html())


def render() -> None:
    """사용법 · 핵심 기능 · FAQ — 연회색 띠 한 장 안에 담는다 (ui/theme.py st-key-mjp_guide)."""
    with st.container(key="mjp_guide"):
        render_html("""
        <div class="mjp-guide-head">
            <span class="mjp-eyebrow">이렇게 써요</span>
            <h2 class="mjp-headline">진단부터 자소서까지,<br>한 화면에서</h2>
        </div>
        """)
        for no, f in enumerate(ss.FEATURES, start=1):
            with st.expander(f"STEP {no} · {f['title']}"):
                render_html(f'<div class="mjp-faq-a">{f["desc"]}</div>')

        render_html('<div class="mjp-guide-sub">핵심 기능</div>')
        for title, desc in _POINTS:
            with st.expander(title):
                render_html(f'<div class="mjp-faq-a">{desc}</div>')

        render_html('<div class="mjp-guide-sub">자주 묻는 질문</div>')
        for question, answer in _FAQ:
            with st.expander(f"Q. {question}"):
                _answer(answer)

        # 예시 데이터 안내는 접지 않는다
        disclaimer("기업 별점·복지·선배 리뷰 등 세부 콘텐츠는 팀이 구성한 <b>예시 데이터</b>입니다.")

        render_html('<div class="mjp-guide-next">이제 시작해볼까요? ↓</div>')
