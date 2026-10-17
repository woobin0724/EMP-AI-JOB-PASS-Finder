# -*- coding: utf-8 -*-
"""
services/talent_link.py
[big-patch 3단계] 문장 ↔ 기업 인재상 연결 (규칙 기반)

자소서 첨삭과 모의 면접 피드백이 함께 쓴다. "이 문장이 인재상의 어느 부분과
이어지는가"를 문장마다 보여준다.

▣ 무엇을 보고 판단하나
   인재상 키워드마다 그 가치를 드러내는 '단서 단어'를 정해 두고, 문장에 그
   단어가 있는지만 본다. 글의 뜻을 이해하는 것이 아니라 단어를 세는 것이므로
   화면에도 "단어 기준 추정"이라고 표시한다. AI 를 쓰지 않아 비용이 0원이다.

▣ 단서 단어는 팀이 정한 것이다
   기업이 발표한 기준이 아니다. 키워드에 단서가 없으면 키워드 글자 자체만 찾는다.
"""

import re

# 인재상 키워드 → 그 가치를 드러내는 단서 단어 (팀 작성, 공식 기준 아님)
CUES = {
    "성실": ["매일", "꾸준", "빠짐없이", "지각", "결석", "개근", "기록", "성실"],
    "책임감": ["책임", "맡은", "끝까지", "마무리", "담당", "약속"],
    "꼼꼼함": ["꼼꼼", "점검", "확인", "검토", "오차", "측정", "체크", "실수"],
    "끈기": ["포기", "다시", "반복", "끝까지", "재도전", "몇 번", "꾸준"],
    "도전": ["도전", "처음", "새로", "시도", "대회", "출전"],
    "패기": ["도전", "자신감", "먼저", "앞장", "패기"],
    "창의": ["아이디어", "개선", "새로운 방법", "고안", "창의", "바꿔"],
    "문제해결": ["문제", "해결", "원인", "개선", "고장", "오류", "방법을 찾"],
    "협력": ["함께", "팀", "동료", "친구들", "역할을 나누", "도와", "협력"],
    "협업": ["함께", "팀", "동료", "조원", "역할", "소통", "협업"],
    "안전의식": ["안전", "보호구", "사고", "위험", "수칙", "점검"],
    "안전제일": ["안전", "보호구", "사고", "위험", "수칙"],
    "위생의식": ["위생", "청결", "소독", "세척", "오염"],
    "준법정신": ["규칙", "규정", "절차", "법", "수칙", "기준을 지"],
    "정직": ["정직", "솔직", "숨기지", "인정", "사실대로"],
    "공공의식": ["공공", "지역", "주민", "봉사", "사회", "국민"],
    "학습의지": ["공부", "배우", "익히", "자격증", "독학", "강의", "학습"],
    "성장지향": ["성장", "발전", "목표", "배우", "더 나은", "다음에는"],
    "자기주도성": ["스스로", "혼자", "계획", "주도", "자발"],
    "실행력": ["바로", "실행", "직접", "만들", "옮겼"],
    "집중력": ["집중", "몰입", "시간 동안", "정밀"],
    "몰입": ["몰입", "집중", "빠져"],
    "관찰력": ["관찰", "발견", "알아차", "살펴"],
    "침착함": ["침착", "당황", "차분", "급할수록"],
    "유연성": ["유연", "바꿔", "변경", "상황에 맞", "다른 방법"],
    "적응력": ["적응", "새로운 환경", "익숙해", "변화"],
    "체력": ["체력", "운동", "현장", "야간", "교대"],
}

_SENT_SPLIT = re.compile(r"(?<=[.!?다요])\s+|\n+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s and s.strip()]


def _cues(keyword: str) -> list[str]:
    return CUES.get(keyword) or [keyword]


def link_sentences(text: str, ideal_talent: list | None, limit: int = 8) -> list[dict]:
    """
    문장마다 이어지는 인재상 키워드와 근거 단어.
    반환: [{sentence, links: [{talent, cue}]}] — 연결이 하나라도 있는 문장만.
    """
    talents = [t for t in (ideal_talent or []) if t]
    if not talents:
        return []
    out = []
    for sentence in split_sentences(text):
        links = []
        for talent in talents:
            cue = next((c for c in _cues(talent) if c in sentence), None)
            if cue:
                links.append({"talent": talent, "cue": cue})
        if links:
            out.append({"sentence": sentence, "links": links})
        if len(out) >= limit:
            break
    return out


def coverage(text: str, ideal_talent: list | None) -> tuple[list[str], list[str]]:
    """(글에 드러난 인재상, 아직 안 드러난 인재상)."""
    talents = [t for t in (ideal_talent or []) if t]
    shown = [t for t in talents if any(c in (text or "") for c in _cues(t))]
    return shown, [t for t in talents if t not in shown]
