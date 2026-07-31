# -*- coding: utf-8 -*-
"""
services/curriculum.py
'코멘토(Comento)' 스타일 4주 단위 직무 부트캠프 커리큘럼 생성 로직

※ 안내
코멘토는 실제 존재하는 취업 부트캠프/멘토링 플랫폼입니다. 아래 커리큘럼은
코멘토가 제공하는 "직무 부트캠프" 형태(주차별 학습목표 + 실습과제)를 참고해
팀이 규칙 기반으로 생성한 예시 커리큘럼이며, 코멘토의 실제 커리큘럼을
그대로 가져온 것이 아닙니다.
"""


def generate_curriculum(company: dict) -> list:
    """
    선택한 기업의 required_skills를 바탕으로 4주 커리큘럼을 생성한다.
    반환값: [{week, title, goal, tasks: [...], project, portfolio_tip}, ...]
    """
    skills = company.get("required_skills") or ["직무 기초 이론", "현장 실습 기초"]
    certs = company.get("required_certs") or []
    talent = company.get("ideal_talent") or []

    # 스킬 목록을 4주에 나눠 배치 (모자라면 반복 활용)
    weekly_focus = [skills[i % len(skills)] for i in range(4)]

    plan = [
        {
            "week": 1,
            "title": "기초 이론 다지기",
            "goal": f"'{weekly_focus[0]}' 핵심 개념을 이해하고 관련 기초 용어를 정리한다.",
            "tasks": [
                f"{weekly_focus[0]} 관련 교과서/자격증 이론서 1회독",
                "핵심 용어 20개 정리 노트 작성",
                "관련 유튜브 강의 또는 공식 문서 2편 시청",
            ],
            "project": "핵심 개념 요약 노트 제작",
            "portfolio_tip": "정리한 이론 노트를 포트폴리오 '학습 기록' 섹션에 사진/PDF로 첨부하세요.",
        },
        {
            "week": 2,
            "title": "실습 & 도구 익히기",
            "goal": f"'{weekly_focus[1]}'을 실제로 다뤄보며 도구 사용법에 익숙해진다.",
            "tasks": [
                f"{weekly_focus[1]} 관련 실습 3회 이상 진행",
                "실습 중 겪은 오류/트러블 기록",
                (f"{certs[0]} 관련 기출문제 풀이" if certs else "관련 기능사 기출문제 풀이"),
            ],
            "project": "실습 결과물 1개 완성 (사진/영상 기록 필수)",
            "portfolio_tip": "실습 전-후 비교, 겪었던 문제와 해결 과정을 스토리로 남기면 면접에서 강력한 소재가 됩니다.",
        },
        {
            "week": 3,
            "title": "미니 프로젝트 수행",
            "goal": f"'{weekly_focus[2]}'을 응용해 작은 규모의 결과물을 완성한다.",
            "tasks": [
                "미니 프로젝트 주제 선정 및 계획 수립",
                "단계별 실행 및 중간 점검",
                "결과물에 대한 자체 품질 점검(체크리스트 작성)",
            ],
            "project": f"'{weekly_focus[2]}' 응용 미니 프로젝트 1건",
            "portfolio_tip": "프로젝트 목표-과정-결과-배운점 4단 구조로 정리하면 자소서에 바로 활용할 수 있습니다.",
        },
        {
            "week": 4,
            "title": "면접 대비 & 포트폴리오 완성",
            "goal": "지금까지의 학습/실습 결과를 정리하고 예상 면접 질문에 답변을 준비한다.",
            "tasks": [
                "포트폴리오 최종본 정리 (이론 노트 + 실습 기록 + 프로젝트 결과)",
                f"기업 인재상({', '.join(talent) if talent else '해당 기업 인재상'}) 관련 경험 매칭 정리",
                "예상 면접 질문 3개에 대한 답변 스크립트 작성 및 실전 연습",
            ],
            "project": "포트폴리오 최종본 + 면접 답변 스크립트",
            "portfolio_tip": "인재상 키워드와 실제 경험을 1:1로 매칭한 표를 만들어두면 자소서·면접 모두에서 재사용할 수 있습니다.",
        },
    ]
    return plan
