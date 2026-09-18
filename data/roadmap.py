# -*- coding: utf-8 -*-
"""
data/roadmap.py
커리어 로드맵 마일스톤 정의

app.py 에 흩어져 있던 MILESTONES / ROADMAP_STAGE_LABELS 를 콘텐츠 데이터로
분리했다. Phase 4(OGQ 스티커 게이미피케이션)에서 단계별 보상 스티커를
연결할 때 이 파일 한 곳만 수정하면 되도록 설계했다.
"""

# (키, 표시명, 설명)
MILESTONES = [
    ("cert", "자격증 준비", "목표 기업이 요구하는 자격증을 취득했거나 시험 접수를 마쳤습니다."),
    ("portfolio", "포트폴리오 완성", "4주 커리큘럼의 프로젝트 결과물을 문서로 정리했습니다."),
    ("interview", "면접 준비", "예상 기출 질문 3선에 대한 나만의 답변을 만들었습니다."),
]

MILESTONE_KEYS = [key for key, _, _ in MILESTONES]

# 완료 개수 → 진행 단계 라벨 (PDF 리포트 · 선생님 대시보드에서 사용)
ROADMAP_STAGE_LABELS = ["시작 전", "자격증 준비 완료", "포트폴리오 완성", "면접 준비 완료"]


def empty_milestones() -> dict:
    return {key: False for key in MILESTONE_KEYS}


def stage_label(done_count: int) -> str:
    idx = max(0, min(len(ROADMAP_STAGE_LABELS) - 1, int(done_count)))
    return ROADMAP_STAGE_LABELS[idx]
