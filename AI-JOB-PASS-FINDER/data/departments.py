# -*- coding: utf-8 -*-
"""
data/departments.py
전국 마이스터고 6개 계열(하이파이브 분류 참고) 및 상세 전공 마스터 데이터

※ 안내
"하이파이브(HIFIVE)"는 한국직업능력연구원 등이 운영하는 마이스터고 취업지원
포털의 실제 명칭입니다. 아래 계열/전공 분류 체계는 하이파이브가 채택하는
일반적인 마이스터고 계열 구분(기계, 전자, 바이오, 농생명, 해양, 정보통신 등)을
참고해 팀이 구성한 것이며, 전공별 "평균 취업률" 수치는 실제 하이파이브 통계를
실시간 긁어온 값이 아니라 **팀이 만든 예시(모의) 수치**입니다. 실제 서비스로
발전시킬 경우 하이파이브 공식 통계 공개 자료(연간 발간물)를 인용해야 합니다.
"""

# 계열(category) -> {전공 리스트, 각 전공의 예시 평균 취업률(%), 관련 자격증 코드}
DEPARTMENTS = {
    "기계과": {
        "category": "기계",
        "majors": ["정밀기계전공", "CNC가공전공", "자동차정비전공"],
        "avg_employment_rate": 78.4,
        "cert_codes": ["MC01", "MC02", "MC03", "MC04", "MC05", "MC06"],
    },
    "메카트로닉스과": {
        "category": "기계",
        "majors": ["산업자동화전공", "로봇제어전공"],
        "avg_employment_rate": 81.2,
        "cert_codes": ["MT01", "MT02", "MT03"],
    },
    "전기전자과": {
        "category": "전자/전기",
        "majors": ["전기설비전공", "전자제어전공", "반도체장비전공"],
        "avg_employment_rate": 83.6,
        "cert_codes": ["EL01", "EL02", "EL03", "EL04", "EL05", "EL06", "EL07"],
    },
    "정보통신과": {
        "category": "IT/정보통신",
        "majors": ["네트워크전공", "임베디드SW전공", "정보보안전공"],
        "avg_employment_rate": 76.9,
        "cert_codes": ["IT01", "IT02", "IT03", "IT04", "IT05", "IT06", "IT07"],
    },
    "IT소프트웨어과": {
        "category": "IT/정보통신",
        "majors": ["소프트웨어개발전공", "데이터분석전공"],
        "avg_employment_rate": 74.3,
        "cert_codes": ["IT01", "IT02", "IT03", "IT04", "IT05", "IT06"],
    },
    "바이오화학과": {
        "category": "바이오/화학",
        "majors": ["바이오공정전공", "화학분석전공", "제약공정전공"],
        "avg_employment_rate": 70.5,
        "cert_codes": ["CH01", "CH02", "CH03", "CH04", "BI01", "BI02"],
    },
    "농생명과": {
        "category": "농생명",
        "majors": ["스마트팜전공", "식품가공전공", "종자생명전공"],
        "avg_employment_rate": 68.2,
        "cert_codes": ["FD01", "FD02", "FD03", "AG01", "AG02"],
    },
    "해양산업과": {
        "category": "해양",
        "majors": ["조선기자재전공", "수산양식전공", "해양플랜트전공"],
        "avg_employment_rate": 72.8,
        "cert_codes": ["SB01", "SB02", "SB03"],
    },
    "건축토목과": {
        "category": "건축/토목",
        "majors": ["건축시공전공", "토목측량전공"],
        "avg_employment_rate": 69.7,
        "cert_codes": ["CV01", "CV02", "CV03", "CV04", "CV05"],
    },
    "자동차과": {
        "category": "기계",
        "majors": ["자동차정비전공", "차체수리전공"],
        "avg_employment_rate": 77.1,
        "cert_codes": ["AT01", "AT02", "AT03"],
    },
}

DEPARTMENT_LIST = list(DEPARTMENTS.keys())
CATEGORY_LIST = sorted({v["category"] for v in DEPARTMENTS.values()})


def get_certs_for_department(dept_name: str):
    return DEPARTMENTS.get(dept_name, {}).get("cert_codes", [])


def get_majors_for_department(dept_name: str):
    return DEPARTMENTS.get(dept_name, {}).get("majors", [])


def get_employment_rate(dept_name: str):
    return DEPARTMENTS.get(dept_name, {}).get("avg_employment_rate", None)


def get_category(dept_name: str):
    return DEPARTMENTS.get(dept_name, {}).get("category")
