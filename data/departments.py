# -*- coding: utf-8 -*-
"""
data/departments.py
전국 마이스터고 6개 계열 및 상세 전공 마스터 데이터 (하이파이브 분류를 참고한 팀 자체 분류)

※ 안내
"하이파이브(HIFIVE)"는 마이스터고 취업지원 포털의 명칭이다(참고한 서비스 — 연동하지
않는다). [팀 확인 필요: 운영 기관명] 아래 계열/전공 분류 체계는 하이파이브가 채택하는
일반적인 마이스터고 계열 구분(기계, 전자, 바이오, 농생명, 해양, 정보통신 등)을
참고해 팀이 구성한 것이다.

[심사대응] 예전에는 학과별 '평균 취업률(예시)' 숫자를 화면에 보여줬으나 근거 자료가
없는 팀 제작 수치여서 데이터와 함께 삭제했다. 다시 넣으려면 공식 통계 공개 자료를
출처와 함께 인용해야 한다.
"""

# 학과 -> {계열(category), 세부 전공 예시, 관련 자격증 코드}
DEPARTMENTS = {
    "기계과": {
        "category": "기계",
        "majors": ["정밀기계전공", "CNC가공전공", "자동차정비전공"],
        "cert_codes": ["MC01", "MC02", "MC03", "MC04", "MC05", "MC06"],
    },
    "메카트로닉스과": {
        "category": "기계",
        "majors": ["산업자동화전공", "로봇제어전공"],
        "cert_codes": ["MT01", "MT02", "MT03"],
    },
    "전기전자과": {
        "category": "전자/전기",
        "majors": ["전기설비전공", "전자제어전공", "반도체장비전공"],
        "cert_codes": ["EL01", "EL02", "EL03", "EL04", "EL05", "EL06", "EL07"],
    },
    "정보통신과": {
        "category": "IT/정보통신",
        "majors": ["네트워크전공", "임베디드SW전공", "정보보안전공"],
        "cert_codes": ["IT01", "IT02", "IT03", "IT04", "IT05", "IT06", "IT07"],
    },
    "IT소프트웨어과": {
        "category": "IT/정보통신",
        "majors": ["소프트웨어개발전공", "데이터분석전공"],
        "cert_codes": ["IT01", "IT02", "IT03", "IT04", "IT05", "IT06"],
    },
    "바이오화학과": {
        "category": "바이오/화학",
        "majors": ["바이오공정전공", "화학분석전공", "제약공정전공"],
        "cert_codes": ["CH01", "CH02", "CH03", "CH04", "BI01", "BI02"],
    },
    "농생명과": {
        "category": "농생명",
        "majors": ["스마트팜전공", "식품가공전공", "종자생명전공"],
        "cert_codes": ["FD01", "FD02", "FD03", "AG01", "AG02"],
    },
    "해양산업과": {
        "category": "해양",
        "majors": ["조선기자재전공", "수산양식전공", "해양플랜트전공"],
        "cert_codes": ["SB01", "SB02", "SB03"],
    },
    "건축토목과": {
        "category": "건축/토목",
        "majors": ["건축시공전공", "토목측량전공"],
        "cert_codes": ["CV01", "CV02", "CV03", "CV04", "CV05"],
    },
    "자동차과": {
        "category": "기계",
        "majors": ["자동차정비전공", "차체수리전공"],
        "cert_codes": ["AT01", "AT02", "AT03"],
    },
}

DEPARTMENT_LIST = list(DEPARTMENTS.keys())
CATEGORY_LIST = sorted({v["category"] for v in DEPARTMENTS.values()})


def get_certs_for_department(dept_name: str):
    return DEPARTMENTS.get(dept_name, {}).get("cert_codes", [])


def get_majors_for_department(dept_name: str):
    return DEPARTMENTS.get(dept_name, {}).get("majors", [])


def get_category(dept_name: str):
    return DEPARTMENTS.get(dept_name, {}).get("category")
