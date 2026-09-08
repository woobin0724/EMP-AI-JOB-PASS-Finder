# -*- coding: utf-8 -*-
"""
data/certifications.py
국가기술자격 마스터 데이터 (기능사/산업기사/기사) + 유사 자격증 매핑 +
기업 규모별 가산점 예시 데이터 (큐넷 자격분석 가이드 카드에 사용)

※ 안내
한국산업인력공단(Q-Net)이 관리하는 국가기술자격 종목은 500종 이상입니다.
CERTIFICATIONS 리스트는 마이스터고 10개 학과와 직접 관련된 자격증을 팀이
선별한 "대표 마스터 데이터(약 55종)"이며 전체 종목 DB가 아닙니다.
CERT_BONUS_BY_SIZE(기업 규모별 가산점)와 SIMILAR_CERTS(유사 자격증) 역시
공식 통계가 아니라 팀이 구성한 예시 데이터입니다. 실제 서비스에서는
공공데이터포털의 "국가기술자격 종목별 상세정보" API로 CERTIFICATIONS를,
각 기업 채용공고의 실제 가산점 규정으로 CERT_BONUS_BY_SIZE를 대체해야 합니다.
"""

CERTIFICATIONS = [
    # ---------------- 기계 (MC) ----------------
    {"code": "MC01", "name": "컴퓨터응용선반기능사", "level": "기능사", "category": "기계"},
    {"code": "MC02", "name": "컴퓨터응용밀링기능사", "level": "기능사", "category": "기계"},
    {"code": "MC03", "name": "생산자동화산업기사", "level": "산업기사", "category": "기계"},
    {"code": "MC04", "name": "일반기계기사", "level": "기사", "category": "기계"},
    {"code": "MC05", "name": "설비보전기능사", "level": "기능사", "category": "기계"},
    {"code": "MC06", "name": "지게차운전기능사", "level": "기능사", "category": "기계"},

    # ---------------- 메카트로닉스 (MT) ----------------
    {"code": "MT01", "name": "생산자동화기능사", "level": "기능사", "category": "기계"},
    {"code": "MT02", "name": "메카트로닉스기사", "level": "기사", "category": "기계"},
    {"code": "MT03", "name": "로봇기구개발기사", "level": "기사", "category": "기계"},

    # ---------------- 전자/전기 (EL) ----------------
    {"code": "EL01", "name": "전기기능사", "level": "기능사", "category": "전자/전기"},
    {"code": "EL02", "name": "전기산업기사", "level": "산업기사", "category": "전자/전기"},
    {"code": "EL03", "name": "전기기사", "level": "기사", "category": "전자/전기"},
    {"code": "EL04", "name": "전자기기기능사", "level": "기능사", "category": "전자/전기"},
    {"code": "EL05", "name": "전자산업기사", "level": "산업기사", "category": "전자/전기"},
    {"code": "EL06", "name": "승강기기능사", "level": "기능사", "category": "전자/전기"},
    {"code": "EL07", "name": "반도체설계산업기사", "level": "산업기사", "category": "전자/전기"},

    # ---------------- IT/정보통신 (IT) ----------------
    {"code": "IT01", "name": "정보처리기능사", "level": "기능사", "category": "IT/정보통신"},
    {"code": "IT02", "name": "정보처리산업기사", "level": "산업기사", "category": "IT/정보통신"},
    {"code": "IT03", "name": "정보처리기사", "level": "기사", "category": "IT/정보통신"},
    {"code": "IT04", "name": "정보보안기사", "level": "기사", "category": "IT/정보통신"},
    {"code": "IT05", "name": "네트워크관리사2급", "level": "민간(등록)", "category": "IT/정보통신"},
    {"code": "IT06", "name": "정보기기운용기능사", "level": "기능사", "category": "IT/정보통신"},
    {"code": "IT07", "name": "리눅스마스터2급", "level": "민간(등록)", "category": "IT/정보통신"},

    # ---------------- 바이오/화학 (CH, BI) ----------------
    {"code": "CH01", "name": "화학분석기능사", "level": "기능사", "category": "바이오/화학"},
    {"code": "CH02", "name": "위험물산업기사", "level": "산업기사", "category": "바이오/화학"},
    {"code": "CH03", "name": "화공기사", "level": "기사", "category": "바이오/화학"},
    {"code": "CH04", "name": "가스기능사", "level": "기능사", "category": "바이오/화학"},
    {"code": "BI01", "name": "바이오화학제품제조기사", "level": "기사", "category": "바이오/화학"},
    {"code": "BI02", "name": "식품기사", "level": "기사", "category": "바이오/화학"},

    # ---------------- 농생명 (AG, FD) ----------------
    {"code": "AG01", "name": "종자기능사", "level": "기능사", "category": "농생명"},
    {"code": "AG02", "name": "시설원예기능사", "level": "기능사", "category": "농생명"},
    {"code": "FD01", "name": "식품가공기능사", "level": "기능사", "category": "농생명"},
    {"code": "FD02", "name": "제과기능사", "level": "기능사", "category": "농생명"},
    {"code": "FD03", "name": "제빵기능사", "level": "기능사", "category": "농생명"},

    # ---------------- 해양 (SB) ----------------
    {"code": "SB01", "name": "조선기능사", "level": "기능사", "category": "해양"},
    {"code": "SB02", "name": "조선산업기사", "level": "산업기사", "category": "해양"},
    {"code": "SB03", "name": "잠수기능사", "level": "기능사", "category": "해양"},

    # ---------------- 건축/토목 (CV) ----------------
    {"code": "CV01", "name": "건축도장기능사", "level": "기능사", "category": "건축/토목"},
    {"code": "CV02", "name": "건축목공기능사", "level": "기능사", "category": "건축/토목"},
    {"code": "CV03", "name": "건축산업기사", "level": "산업기사", "category": "건축/토목"},
    {"code": "CV04", "name": "토목산업기사", "level": "산업기사", "category": "건축/토목"},
    {"code": "CV05", "name": "측량및지형공간정보산업기사", "level": "산업기사", "category": "건축/토목"},

    # ---------------- 자동차 (AT) ----------------
    {"code": "AT01", "name": "자동차정비기능사", "level": "기능사", "category": "기계"},
    {"code": "AT02", "name": "자동차정비산업기사", "level": "산업기사", "category": "기계"},
    {"code": "AT03", "name": "자동차차체수리기능사", "level": "기능사", "category": "기계"},
]

CERT_CODE_TO_NAME = {c["code"]: c["name"] for c in CERTIFICATIONS}
CERT_NAME_TO_CODE = {c["name"]: c["code"] for c in CERTIFICATIONS}
CERT_LEVELS = sorted({c["level"] for c in CERTIFICATIONS})


def get_certs_by_category(category: str):
    return [c for c in CERTIFICATIONS if c["category"] == category]


def get_cert_names(codes):
    return [CERT_CODE_TO_NAME[c] for c in codes if c in CERT_CODE_TO_NAME]


# ============================================================
# 유사 자격증 매핑 (요구 자격증을 정확히 보유하지 않아도 70% 인정)
# ============================================================
SIMILAR_CERTS = {
    "전기기능사": ["전기산업기사", "전기기사", "전자기기기능사"],
    "전자기기기능사": ["전기기능사", "전자산업기사"],
    "컴퓨터응용선반기능사": ["컴퓨터응용밀링기능사", "일반기계기사"],
    "컴퓨터응용밀링기능사": ["컴퓨터응용선반기능사", "생산자동화산업기사"],
    "생산자동화기능사": ["생산자동화산업기사", "메카트로닉스기사"],
    "정보처리기능사": ["정보처리산업기사", "정보처리기사"],
    "화학분석기능사": ["화공기사", "위험물산업기사"],
    "위험물산업기사": ["화학분석기능사", "가스기능사"],
    "식품가공기능사": ["식품기사", "제과기능사", "제빵기능사"],
    "조선기능사": ["조선산업기사"],
    "자동차정비기능사": ["자동차정비산업기사", "자동차차체수리기능사"],
}


def is_similar(owned_cert: str, required_cert: str) -> bool:
    """보유 자격증이 요구 자격증과 유사 자격증 관계인지 확인한다 (양방향)."""
    if owned_cert == required_cert:
        return True
    return (
        owned_cert in SIMILAR_CERTS.get(required_cert, [])
        or required_cert in SIMILAR_CERTS.get(owned_cert, [])
    )


# ============================================================
# 기업 규모별 가산점 예시 데이터 (큐넷 자격분석 가이드 카드용)
# 실제 공식 가산점 규정이 아닌, 팀이 구성한 예시 수치입니다.
# ============================================================
CERT_BONUS_BY_SIZE = {
    "전기기능사": {"대기업": 8, "중견기업": 6, "공기업": 10, "강소기업": 5},
    "전기산업기사": {"대기업": 10, "중견기업": 8, "공기업": 12, "강소기업": 6},
    "컴퓨터응용선반기능사": {"대기업": 7, "중견기업": 6, "공기업": 5, "강소기업": 6},
    "컴퓨터응용밀링기능사": {"대기업": 7, "중견기업": 6, "공기업": 5, "강소기업": 6},
    "생산자동화기능사": {"대기업": 9, "중견기업": 7, "공기업": 6, "강소기업": 5},
    "정보처리기능사": {"대기업": 6, "중견기업": 6, "공기업": 8, "강소기업": 7},
    "정보처리산업기사": {"대기업": 9, "중견기업": 8, "공기업": 10, "강소기업": 7},
    "화학분석기능사": {"대기업": 8, "중견기업": 7, "공기업": 6, "강소기업": 5},
    "위험물산업기사": {"대기업": 9, "중견기업": 8, "공기업": 7, "강소기업": 6},
    "식품가공기능사": {"대기업": 6, "중견기업": 6, "공기업": 5, "강소기업": 6},
    "조선기능사": {"대기업": 8, "중견기업": 7, "공기업": 6, "강소기업": 5},
    "자동차정비기능사": {"대기업": 7, "중견기업": 6, "공기업": 6, "강소기업": 6},
}

DEFAULT_BONUS = {"대기업": 5, "중견기업": 5, "공기업": 5, "강소기업": 5}


def get_bonus_points(cert_name: str, company_size: str) -> int:
    """자격증명 + 기업 규모로 예시 가산점을 조회한다. 데이터가 없으면 기본값(5점)."""
    return CERT_BONUS_BY_SIZE.get(cert_name, DEFAULT_BONUS).get(company_size, 5)
