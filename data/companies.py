# -*- coding: utf-8 -*-
"""
data/companies.py
채용 공고 모의(Mock) / 백업 데이터

※ 아래 기업명은 모두 가상(fictional) 기업이며, 실제 존재하는 특정 기업의
   채용 조건을 그대로 옮긴 것이 아닙니다. 워크넷 Open API 연동이 실패하거나
   서비스키가 없을 때 자동으로 사용되는 대체 데이터입니다.
   (services/worknet_api.py 의 fallback 로직 참고)
"""

MOCK_JOBS = [
    # ---------------- 기계 ----------------
    {"id": 1, "company": "한빛정밀공업", "title": "CNC 선반·밀링 오퍼레이터",
     "department": "기계과", "required_cert_codes": ["MC01", "MC02"],
     "region": "전북 익산", "salary": "2,800~3,200만원", "company_type": "중견기업"},
    {"id": 2, "company": "대성메카트로닉스", "title": "생산자동화 설비 엔지니어",
     "department": "기계과", "required_cert_codes": ["MC03", "EL01"],
     "region": "전북 군산", "salary": "2,900~3,300만원", "company_type": "중소기업"},
    {"id": 3, "company": "태백중공업", "title": "중공업 생산기술 신입사원",
     "department": "기계과", "required_cert_codes": ["MC01", "MC04"],
     "region": "경남 창원", "salary": "3,200~3,800만원", "company_type": "대기업"},
    {"id": 4, "company": "신성정공", "title": "정밀가공 라인 기술직",
     "department": "기계과", "required_cert_codes": ["MC02", "MC03"],
     "region": "전북 완주", "salary": "3,000~3,400만원", "company_type": "중견기업"},
    {"id": 5, "company": "우진산업기계", "title": "설비보전 및 유지보수",
     "department": "기계과", "required_cert_codes": ["MC05", "MC06"],
     "region": "전북 전주", "salary": "2,700~3,000만원", "company_type": "중소기업"},

    # ---------------- 전기/전자 ----------------
    {"id": 6, "company": "코리아파워시스템", "title": "전기설비 유지보수 기술직",
     "department": "전기전자과", "required_cert_codes": ["EL01", "EL02"],
     "region": "전북 전주", "salary": "2,900~3,300만원", "company_type": "중견기업"},
    {"id": 7, "company": "한강전력엔지니어링", "title": "승강기 유지보수 기사",
     "department": "전기전자과", "required_cert_codes": ["EL01", "EL06"],
     "region": "서울 강동구", "salary": "2,800~3,100만원", "company_type": "중소기업"},
    {"id": 8, "company": "미래에너지솔루션", "title": "신재생에너지 발전설비 엔지니어",
     "department": "전기전자과", "required_cert_codes": ["EL02", "EL03"],
     "region": "전남 나주", "salary": "3,300~3,800만원", "company_type": "중견기업"},
    {"id": 9, "company": "대한이엔지", "title": "전기공사 현장 보조기사",
     "department": "전기전자과", "required_cert_codes": ["EL01"],
     "region": "전북 김제", "salary": "2,600~2,900만원", "company_type": "스타트업"},
    {"id": 10, "company": "서울전기설비", "title": "건축전기설비 시공기술직",
     "department": "전기전자과", "required_cert_codes": ["EL01", "EL02"],
     "region": "서울 금천구", "salary": "2,900~3,200만원", "company_type": "중소기업"},

    # ---------------- IT/소프트웨어 ----------------
    {"id": 11, "company": "넥스트웨이브소프트", "title": "백엔드 주니어 개발자",
     "department": "IT소프트웨어과", "required_cert_codes": ["IT01", "IT05"],
     "region": "서울 강남구", "salary": "3,200~3,800만원", "company_type": "중견기업"},
    {"id": 12, "company": "스마트팩토리시스템즈", "title": "스마트팩토리 관제 시스템 운영",
     "department": "IT소프트웨어과", "required_cert_codes": ["IT06", "IT01"],
     "region": "전북 전주", "salary": "3,000~3,400만원", "company_type": "중소기업"},
    {"id": 13, "company": "클라우드베이스코리아", "title": "클라우드 인프라 신입 엔지니어",
     "department": "IT소프트웨어과", "required_cert_codes": ["IT05", "IT04"],
     "region": "경기 판교", "salary": "3,400~4,000만원", "company_type": "스타트업"},
    {"id": 14, "company": "한빛데이터센터", "title": "데이터센터 운영 인프라 직군",
     "department": "IT소프트웨어과", "required_cert_codes": ["IT01", "IT03"],
     "region": "전북 정읍", "salary": "3,000~3,300만원", "company_type": "중소기업"},
    {"id": 15, "company": "이지테크솔루션", "title": "IT 인프라 지원 신입사원",
     "department": "IT소프트웨어과", "required_cert_codes": ["IT06"],
     "region": "전북 전주", "salary": "2,700~2,900만원", "company_type": "중소기업"},

    # ---------------- 화공 ----------------
    {"id": 16, "company": "도담화학산업", "title": "화학분석 품질관리직",
     "department": "화공과", "required_cert_codes": ["CH01"],
     "region": "전남 여수", "salary": "2,900~3,300만원", "company_type": "중견기업"},
    {"id": 17, "company": "해든케미칼", "title": "위험물 안전관리 담당",
     "department": "화공과", "required_cert_codes": ["CH02"],
     "region": "울산", "salary": "3,100~3,500만원", "company_type": "대기업"},
    {"id": 18, "company": "대성가스엔지니어링", "title": "가스설비 안전점검 기술직",
     "department": "화공과", "required_cert_codes": ["CH04"],
     "region": "전북 군산", "salary": "2,800~3,100만원", "company_type": "중소기업"},
    {"id": 19, "company": "청우화공", "title": "화공플랜트 공정기술 신입",
     "department": "화공과", "required_cert_codes": ["CH03", "CH02"],
     "region": "전남 여수", "salary": "3,300~3,900만원", "company_type": "중견기업"},

    # ---------------- 메카트로닉스 ----------------
    {"id": 20, "company": "로보텍코리아", "title": "산업용 로봇 유지보수 엔지니어",
     "department": "메카트로닉스과", "required_cert_codes": ["MT01", "MT02"],
     "region": "경기 안산", "salary": "3,100~3,600만원", "company_type": "중견기업"},
    {"id": 21, "company": "오토메카트로닉스", "title": "자동화 라인 설계보조",
     "department": "메카트로닉스과", "required_cert_codes": ["MT01"],
     "region": "전북 익산", "salary": "2,900~3,200만원", "company_type": "중소기업"},
    {"id": 22, "company": "퓨처로보틱스", "title": "로봇 기구 개발 신입 엔지니어",
     "department": "메카트로닉스과", "required_cert_codes": ["MT03", "MT02"],
     "region": "대전", "salary": "3,300~3,800만원", "company_type": "스타트업"},

    # ---------------- 건축/토목 ----------------
    {"id": 23, "company": "한국건축시공", "title": "건축 마감시공 기술직",
     "department": "건축토목과", "required_cert_codes": ["CV01", "CV02"],
     "region": "전북 전주", "salary": "2,800~3,100만원", "company_type": "중소기업"},
    {"id": 24, "company": "다온토목엔지니어링", "title": "토목 현장 시공관리 보조",
     "department": "건축토목과", "required_cert_codes": ["CV04"],
     "region": "전북 남원", "salary": "2,900~3,200만원", "company_type": "중견기업"},
    {"id": 25, "company": "바른측량기술", "title": "측량 및 지형정보 조사원",
     "department": "건축토목과", "required_cert_codes": ["CV05"],
     "region": "전북 정읍", "salary": "2,700~3,000만원", "company_type": "중소기업"},
    {"id": 26, "company": "온결건설", "title": "건축시공 현장기술직",
     "department": "건축토목과", "required_cert_codes": ["CV03", "CV02"],
     "region": "광주", "salary": "3,000~3,400만원", "company_type": "중견기업"},

    # ---------------- 자동차 ----------------
    {"id": 27, "company": "전북모터스정비", "title": "자동차 정비 기술직",
     "department": "자동차과", "required_cert_codes": ["AT01"],
     "region": "전북 전주", "salary": "2,700~3,000만원", "company_type": "중소기업"},
    {"id": 28, "company": "한일오토서비스", "title": "차체 수리 및 도장 기술직",
     "department": "자동차과", "required_cert_codes": ["AT03", "AT01"],
     "region": "전북 군산", "salary": "2,800~3,100만원", "company_type": "중소기업"},
    {"id": 29, "company": "누리모빌리티파츠", "title": "완성차 정비 품질관리직",
     "department": "자동차과", "required_cert_codes": ["AT02", "AT01"],
     "region": "충남 아산", "salary": "3,200~3,600만원", "company_type": "대기업"},

    # ---------------- 조선 ----------------
    {"id": 30, "company": "동해조선기술", "title": "선박 의장 생산기술직",
     "department": "조선과", "required_cert_codes": ["SB01"],
     "region": "경남 거제", "salary": "3,100~3,500만원", "company_type": "대기업"},
    {"id": 31, "company": "한주조선산업", "title": "조선 생산관리 신입사원",
     "department": "조선과", "required_cert_codes": ["SB02", "SB01"],
     "region": "전남 목포", "salary": "3,000~3,400만원", "company_type": "중견기업"},

    # ---------------- 식품가공 ----------------
    {"id": 32, "company": "청정식품가공", "title": "식품가공 생산관리직",
     "department": "식품가공과", "required_cert_codes": ["FD01"],
     "region": "전북 익산", "salary": "2,600~2,900만원", "company_type": "중소기업"},
    {"id": 33, "company": "고소한베이커리랩", "title": "제과·제빵 생산기술직",
     "department": "식품가공과", "required_cert_codes": ["FD02", "FD03"],
     "region": "전북 전주", "salary": "2,700~3,000만원", "company_type": "중견기업"},
    {"id": 34, "company": "익산푸드파크", "title": "식품안전 품질관리 신입",
     "department": "식품가공과", "required_cert_codes": ["FD01"],
     "region": "전북 익산", "salary": "2,700~3,000만원", "company_type": "중소기업"},
]


# ============================================================
# 공기업 백업 데이터 (잡알리오 연동 실패 시 대체)
# ※ 기관명은 전부 가상(fictional) 공공기관이다. [big-patch 1단계]
#   이전에는 실제 공공기관명(한국전력공사 등)에 팀이 만든 채용 분야·필수 자격증·
#   가산점 설명(ai_tip)을 붙였는데, 실제 기관에 사실이 아닌 채용 정보를 붙이는
#   셈이라 가상 기관명으로 바꾸고 ai_tip 을 비웠다. 실제 공공기관 채용공고는
#   공식 API(잡알리오 · 공공데이터포털) 키가 있을 때만 LIVE 로 보여준다.
# 자격증 코드 참고: EL01=전기기능사, EL02=전기산업기사, MC01=컴퓨터응용선반기능사,
#   MC05=설비보전기능사, MC06=지게차운전기능사, IT01=정보처리기능사, IT03=정보처리기사
# ============================================================
BACKUP_PUBLIC_COMPANIES = [
    {"id": 101, "company": "한누리전력공사", "title": "배전설비 운영 기술직", "department": "전기전자과", "required_cert_codes": ["EL01", "EL02"], "region": "전국 지사", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 102, "company": "푸른발전기술원", "title": "발전설비 정비 기술직", "department": "전기전자과", "required_cert_codes": ["EL01", "MC05"], "region": "전국 발전소", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 103, "company": "늘빛가스공사", "title": "가스설비 안전관리 기술직", "department": "화공과", "required_cert_codes": ["CH04", "CH02"], "region": "전국 지사", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 104, "company": "맑은물관리공단", "title": "수도설비 유지관리 기술직", "department": "전기전자과", "required_cert_codes": ["EL01"], "region": "전국 지사", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 105, "company": "가온도로공사", "title": "도로시설 유지보수 기술직", "department": "건축토목과", "required_cert_codes": ["CV04", "MC06"], "region": "전국 지사", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 106, "company": "이음철도공사", "title": "차량정비 기술직", "department": "기계과", "required_cert_codes": ["MC01", "MC05"], "region": "전국 차량기지", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 107, "company": "하늘길공항공사", "title": "공항시설 전기설비 기술직", "department": "전기전자과", "required_cert_codes": ["EL01", "EL02"], "region": "인천", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 108, "company": "나래공항공사", "title": "공항 기계설비 기술직", "department": "기계과", "required_cert_codes": ["MC05", "MC06"], "region": "전국 공항", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 109, "company": "온기지역난방공사", "title": "열수송설비 운영 기술직", "department": "전기전자과", "required_cert_codes": ["EL01", "MC05"], "region": "수도권 및 지방거점", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
    {"id": 110, "company": "새솔정보지원센터", "title": "정보시스템 운영 지원직", "department": "IT소프트웨어과", "required_cert_codes": ["IT01", "IT03"], "region": "세종", "salary": "기관 보수규정 기준(예시)", "company_type": "공기업", "ai_tip": ""},
]


# ============================================================
# 강소기업 백업 데이터 ('참 괜찮은 강소기업' 스크래핑 실패 시 대체)
# ※ 중소벤처기업부가 운영하는 "참 괜찮은 강소기업" 인증제를 참고해 팀이 구성한
#   예시 데이터입니다. 아래 기업명은 모두 가상(fictional) 기업이며, 실제로 이
#   인증을 받은 특정 기업의 정보가 아닙니다. (실제 기업명에 "정부 인증 강소기업"
#   같은 공식 지위를 잘못 부여하지 않기 위해 의도적으로 가상 기업명을 사용했습니다.)
# (services/strong_sme_api.py의 fallback 로직 참고)
# ============================================================
BACKUP_STRONG_SME = [
    {"id": 201, "company": "정밀테크코리아", "title": "CNC 정밀가공 기술직", "department": "기계과", "required_cert_codes": ["MC01", "MC02"], "region": "전북 익산", "salary": "2,900~3,300만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 202, "company": "대한오토메이션", "title": "생산자동화 설비 유지보수", "department": "메카트로닉스과", "required_cert_codes": ["MT01", "EL01"], "region": "전북 군산", "salary": "3,000~3,400만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 203, "company": "코리아전장시스템", "title": "전장설비 조립·검사 기술직", "department": "전기전자과", "required_cert_codes": ["EL01", "EL04"], "region": "전북 완주", "salary": "2,800~3,200만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 204, "company": "삼진정공제조", "title": "금속 부품 제조 생산기술직", "department": "기계과", "required_cert_codes": ["MC05", "MC06"], "region": "전북 김제", "salary": "2,800~3,100만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 205, "company": "위드전자제어", "title": "전자제어 시스템 개발 보조", "department": "전기전자과", "required_cert_codes": ["EL04", "EL05"], "region": "전북 전주", "salary": "2,900~3,300만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 206, "company": "한성정밀제조", "title": "정밀부품 품질검사 기술직", "department": "기계과", "required_cert_codes": ["MC01", "MC05"], "region": "전북 정읍", "salary": "2,700~3,000만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 207, "company": "스마트웨어랩", "title": "임베디드 소프트웨어 개발 신입", "department": "IT소프트웨어과", "required_cert_codes": ["IT01", "IT02"], "region": "전북 전주", "salary": "3,000~3,500만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 208, "company": "코드포지소프트", "title": "제조 MES 시스템 유지보수", "department": "IT소프트웨어과", "required_cert_codes": ["IT01", "IT06"], "region": "전북 군산", "salary": "2,900~3,300만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 209, "company": "유니크제조솔루션", "title": "생산라인 자동화 엔지니어", "department": "메카트로닉스과", "required_cert_codes": ["MT01", "MT02"], "region": "전북 익산", "salary": "3,100~3,500만원", "company_type": "강소기업", "ai_tip": ""},
    {"id": 210, "company": "이지파워일렉트릭", "title": "전기설비 시공·점검 기술직", "department": "전기전자과", "required_cert_codes": ["EL01", "EL02"], "region": "전북 남원", "salary": "2,800~3,200만원", "company_type": "강소기업", "ai_tip": ""},
]
