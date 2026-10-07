# AI Job Pass Finder

> "학교에서 시장으로" — 마이스터의 등용문을 여는 AI 맞춤형 취업 파트너

**전북기계공업고등학교 팀 E.M.P (Employment Meister Partner)**
김우빈(팀장·개발·기획) · 김정수(문서·디자인) · 오상명(영상·개발) · 이건희(백엔드·데이터)

제4회 NAVER OGQ마켓 AI Competition 출품작

---

## 1. 무엇을 해결하나 — "실력은 마이스터, 정보는 미스매치"

마이스터고 학생은 실무 역량이 있어도, 자신의 **5등급 성취평가제 내신**과 **전공 자격증**이
어느 기업에 통하는지 스스로 판단하기 어렵습니다.

AI Job Pass Finder 는 내신과 자격증을 **목표 기업별 100점 만점 '합격 지수'**로 바꿔 보여 주고,
그 점수를 바탕으로 **기업 탐색 → 채용 대비 → 자소서 작성**까지 한 앱에서 이어지게 합니다.
선생님은 반 코드로 학생들을 모아 진행 상황을 한 화면에서 봅니다.

---

## 2. 화면과 기능

화면 15개 — 사용자 화면 13개 + 팀 관리자 화면 2개 (`app.py` 의 `ROUTES`).

| 화면 | 사용자가 하는 일 |
|---|---|
| 랜딩 | 서비스 소개 → '시작하기' |
| 로그인 | **게스트로 바로 시작**(닉네임만) · 카카오/네이버/구글 로그인 · **이어하기 코드**(6자리)로 지난 기록 불러오기 |
| 역할 선택 | 학생 / 선생님 |
| 반 등록 · 반 개설 | 학생은 반 코드 입력(건너뛰기 가능), 선생님은 학교·학년·반 입력 → 6자리 반 코드 발급 |
| 허브 | 4대 기능 중 하나 선택 |
| ① 스펙 진단 | 학과·내신·자격증·강점·목표 기업 입력 → **입력 즉시 100점 점수**, 항목별 막대, 점수 설명, 다음 행동 제안 |
| ② 기업 탐색 | **기업 스토리**(카드 넘겨 보기, ❤️ 관심 / 👎 패스) · 관심 기업 모아보기 · 채용공고 통합 검색 · 매칭 점수순 정렬·필터·추천 · 찜하기 |
| ③ 가이드 | 기업별 평점·장단점·필수 자격증·필기 키워드·예상 면접 질문, 4주 커리큘럼, 로드맵 3단계 스탬프, **PDF 리포트** |
| ④ 자소서 | 자소서 초안 생성(문체·분량·다시 생성) · **무료 AI 에 붙여넣을 요청문 복사** · 직접 쓴 초안 첨삭 |
| 로드맵 | 만든 기능과 '아직 만들지 않은 기능 + 이유' |
| 마이페이지 | 이어하기 코드, 점수 기록, 로드맵, 찜·열람 기록, 반 정보, 요금제 |
| 우리 반 (선생님) | 반 평균 점수, 학생별 목표 기업·진행 단계·점수, 관심이 필요한 학생 |
| 기업 데이터 입력 (관리자) | 출처 URL·조사자·조사일을 필수로 받는 기업 정보 입력, CSV/JSON 가져오기·내보내기 |
| 사용 통계 (관리자) | 사용자 수, 날짜별 접속자, 재방문 비율, 기능별 사용 횟수, 스토리 관심 비율 |

---

## 3. 합격 지수 — 계산 방식 (`core/matching.py`)

**AI 를 쓰지 않는 파이썬 계산**이라 입력하는 즉시 바뀌고 비용이 들지 않습니다.

```
합격 지수(100) = 내신 성취도(30) + 자격증 가산점(40) + 전공 적합성(20) + 인재상 일치도(10)

- 내신(30)   : 30 × (5.0 − 등급) ÷ 4.0       1.0등급 = 30점, 3.0등급 = 15점, 5.0등급 = 0점
- 자격증(40) : 기업 요구 자격증마다 정확히 보유 100% · 유사 자격증 70% · 미보유 0% → 평균 × 40
               (기업 미선택 시 보유 1개당 8점, 최대 40)
- 적합성(20) : 학과 계열 = 기업 계열 20점 · 다르면 5점 · 기업 미선택 10점
- 인재상(10) : 내 강점 키워드 중 기업 인재상과 겹치는 비율 × 10
```

- 기업 탐색의 정렬·추천과 스토리 카드의 '내 매칭 점수'도 같은 계산을 씁니다 (`core/company_filter.py`).
- 추천: 매칭 상위 4곳, 40점 미만은 추천하지 않습니다.
- 점수 구간 반응: 80점 이상 '합격 안정권' / 50~79 '분발 필요' / 50 미만 '보완 시급'.

---

## 4. 데이터와 출처

**스크래핑은 하지 않습니다.** 데이터는 ① 공식 API 또는 ② 팀이 직접 조사해 출처와 함께 입력한 데이터만 씁니다.
예전에 잡알리오·강소기업 포털을 스크래핑하던 코드는 삭제했습니다(커밋 `762172d`).

| 데이터 | 공식 API (키가 있을 때) | 키가 없거나 실패하면 |
|---|---|---|
| 자격증 | 공공데이터포털 Q-Net (`services/qnet_api.py`) | `data/certifications.py` 45종 |
| 채용공고 | 고용24 Open API (`services/worknet_api.py`) | `data/companies.py` 34건 |
| 공기업 공고 | 설정 자리만 있음 (`services/api_registry.py`) | 큐레이션 10건 |
| 강소기업 공고 | 설정 자리만 있음 | 큐레이션 10건 |

- 모든 외부 호출은 `services/fallback.py` 의 `safe_call()` 로 감싸 실패해도 화면이 멈추지 않습니다.
  화면에는 **LIVE API / BACKUP DATA / CURATED** 배지로 출처를 표시합니다.
- Q-Net·고용24 의 엔드포인트는 코드 주석에 '예시'로 표기되어 있습니다. 활용가이드로 규격을 확인한 뒤
  `services/api_registry.py` 를 채워야 실제 연동이 됩니다.
- 팀이 넣는 기업 정보는 **출처 URL · 출처 유형 · 조사자 · 조사일이 없으면 저장되지 않습니다** (`services/curated.py`).

### 예시(모의) 데이터 안내
- 기업 분석 카드 20곳(`data/company_showcase.py`)의 **기업명은 모두 가상**이고, 별점·복지·인재상·
  선배 리뷰·면접 질문·합격자 평균 스펙은 팀이 만든 **예시 데이터**입니다. 화면에도 "예시 데이터" 안내를 띄웁니다.
  (예전에는 일부 실제 기업명을 썼으나 실제 정보로 오해될 수 있어 가상 이름으로 바꿨습니다 — 커밋 `22d2c83`)
- 채용공고 백업 34건·강소기업 10건의 기업명도 가상입니다.
- 공기업 백업 10건(`data/companies.py` 의 `BACKUP_PUBLIC_COMPANIES`)은 실제 공공기관명을 쓰고, 채용 분야·자격증·
  안내 문구는 팀이 구성한 예시입니다(코드 주석·화면 문구에 '예시'로 표기). [팀 확인 필요] 가상 이름으로 바꿀지.
- 근무지·근무 조건은 확인된 값이 없어 비워 두었습니다(지어내지 않음).

---

## 5. Claude API 활용과 비용 방어

| 기능 | 파일 | 모델 | AI 가 없을 때 |
|---|---|---|---|
| 자소서 생성 | `services/coverletter.py`, `services/llm.py` | `claude-opus-5` | 문장 풀 템플릿 생성기 |
| 자소서 첨삭 | `services/review.py` | `claude-opus-5` | 규칙 점검(분량·상투어·문장 길이 등) |
| 점수 설명 | `services/score_explain.py` | `claude-opus-5` | 규칙 기반 설명 |
| 기업 스토리 카드 1~4 | `services/story_cards.py` | `claude-opus-5-5` | 원본 데이터로 만든 기본 카드 |

**비용 방어**
1. **점수 계산은 AI 에 맡기지 않습니다.** AI 는 이미 계산된 점수를 '설명'만 합니다.
2. **캐싱**: 같은 입력은 다시 호출하지 않습니다(`st.cache_data`). 스토리 카드는 `data/story_cache.json` 에도 저장해
   앱을 다시 켜도 재호출하지 않습니다.
3. **프리미엄 게이트** (`services/premium.py`): API 키가 있어도 `PREMIUM_USER_IDS`(소셜 로그인 계정) 또는
   `DEMO_USER_IDS`(시연용) 계정만 Claude 를 호출합니다. 두 목록이 비어 있으면 **호출 0회**입니다.
   결제 연동은 없습니다(화면에 '결제 연동 준비 중'으로 표시).
4. **무료 대안**: 같은 지시문으로 만든 요청문을 복사해 학생이 무료 AI 채팅에 붙여넣을 수 있습니다.
5. **키 격리**: API 키는 `st.secrets` 에서만 읽고 코드에 쓰지 않습니다. 실패·거절 시 규칙 기반으로 전환하고 이유를 화면에 표시합니다.
6. 프롬프트에 "학생·원본 데이터에 없는 사실을 지어내지 말 것"을 명시했습니다.

---

## 6. 사용 기록과 관리자 기능

| 기능 | 내용 |
|---|---|
| 관리자 권한 (`services/access.py`) | `ADMIN_USER_IDS` 계정만 마이페이지에 관리자 메뉴가 보이고, 화면 자체에서도 다시 검사해 URL 로 직접 들어와도 막힙니다. |
| 사용 기록 (`services/usage_log.py`) | 최초/마지막 접속, 접속한 날짜, 화면 이동, 스토리 관심/패스. **이름·학교·입력 내용은 남기지 않고**, 사용자는 ID 의 해시로만 구분합니다. |
| 테스트 구분 | `APP_ENV` 가 `production` 이 아닌 환경과 관리자·데모·`TEST_USER_IDS` 계정의 기록은 `is_test` 로 표시되어 통계에서 빠집니다. |
| 저장 위치 | Supabase 키가 있으면 Supabase, 없으면 `data/userdata/` 의 로컬 파일 (`services/storage_backend.py`, `docs/STORAGE.md`) |
| 시연 준비 | `scripts/prewarm_story_cache.py` 로 스토리 카드를 미리 만들어 둘 수 있습니다. |

> Streamlit Community Cloud 는 재배포할 때 서버 파일을 지웁니다. 사용자·사용 기록을 보존하려면 Supabase 를 연결하세요.

---

## 7. 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

API 키를 하나도 넣지 않아도 모든 화면이 동작합니다(백업 데이터 · 규칙 기반 결과).

### 설정 (`.streamlit/secrets.toml`, 배포 시 Streamlit Cloud 의 Secrets) — 전부 선택

예시는 `secrets_example.toml` 에 있습니다. **secrets 파일은 절대 커밋하지 마세요.**

| 항목 | 용도 |
|---|---|
| `CLAUDE_API_KEY` | Claude API 키 (프리미엄·데모 계정만 사용) |
| `PREMIUM_USER_IDS` | AI 기능을 쓸 소셜 로그인 계정 목록 |
| `DEMO_USER_IDS` | 시연용 계정(게스트 가능) — 시연 후 지울 것 |
| `ADMIN_USER_IDS` | 기업 데이터 입력·사용 통계를 볼 팀 관리자 계정 (소셜 계정 권장) |
| `APP_ENV` | 배포 서버에만 `"production"` — 이 값이 있어야 사용 기록이 '실제'로 집계됨 |
| `LOG_SALT` · `TEST_USER_IDS` | 사용 기록 해시용 문자열 · 통계에서 뺄 팀원 계정 |
| `SUPABASE_URL` · `SUPABASE_KEY` | 외부 DB 저장 (`docs/STORAGE.md`) |
| `QNET_API_KEY` · `WORKNET_API_KEY` | 공공데이터 API |
| `KAKAO_/NAVER_/GOOGLE_CLIENT_ID`·`_SECRET`, `OAUTH_REDIRECT_URI` | 소셜 로그인 (없으면 '준비중' + 게스트 모드) |
| `OGQ_API_KEY` | OGQ 마스코트 내려받기 스크립트(`scripts/fetch_mascot.py`)용 |

---

## 8. 기술 스택과 구조

- Python 3.11 · **Streamlit 1.41 이상 1.64 미만** (1.64 부터 구형 브라우저에서 오류 — 커밋 `a9f3f26`)
- pandas · requests · anthropic(공식 SDK) · reportlab(PDF)
- 배포: Streamlit Community Cloud

```
app.py                 화면 라우팅 + 접근 제어 + 사용 기록
core/                  session(화면 상태) · matching(합격 지수) · company_filter(정렬·필터·추천)
data/                  기업 20곳 · 자격증 45종 · 학과 10개/계열 7개 · 백업 공고 · 로드맵 3단계
services/              외부 API · fallback · Claude 호출(llm, coverletter, review, score_explain, story_cards)
                       store/storage_backend(저장) · premium · access · usage_log · reactions · pdf_report
views/                 화면 15개
ui/                    테마 · 공통 컴포넌트 · 마스코트 · 스토리 뷰어
scripts/               check_static(정적 검사) · prewarm_story_cache · fetch_mascot · test_storage_backend
docs/                  STORAGE(외부 DB) · MOBILE_QA(모바일 자동 검사) · W3_SUBMISSION(W3 제출 원문 보관)
fonts/                 NanumGothic.ttf + OFL.txt (PDF 한글용)
```

### 검증
- `python scripts/check_static.py` — 실행 전에 코드 실수(정의 안 된 이름 등)를 찾습니다. GitHub Actions 가 push 마다 자동 실행합니다.
- `python docs/qa_mobile.py` — 9개 화면 × 휴대폰·PC 2개 크기를 자동으로 열어 가로 넘침·터치 영역(44px)·글자 크기를 잽니다.
- `python scripts/test_storage_backend.py` — 저장소(동시 저장 충돌 포함) 테스트.

---

## 9. 자산과 라이선스

| 항목 | 출처 · 라이선스 |
|---|---|
| Streamlit · pandas · requests · anthropic · reportlab | 각 프로젝트의 오픈소스 라이선스 (Apache-2.0, BSD, MIT 등) |
| PDF 한글 폰트 `fonts/NanumGothic.ttf` | Google Fonts 배포본, SIL Open Font License 1.1 (`fonts/OFL.txt`). [팀 확인 필요] 공식 OFL.txt 원문으로 교체 |
| 마스코트 이미지 `assets/ogq/*.jpg` (11장) | **[팀 확인 필요]** 제작자와 사용 허락 범위. 코드 주석은 'NAVER OGQ마켓 캐릭터 스티커'로, 이전 README 의 W3 절은 '팀 자체 제작'으로 적고 있어 서로 다릅니다. 대회 공식 OGQ API 로 받는 도구(`scripts/fetch_mascot.py`)는 있으나 아직 실행 기록이 없습니다. |
| 팀 로고 · 엠블럼 | 팀 로고를 코드로 다시 그린 벡터(`ui/emblem.py`) |

---

## 10. AI 도구 사용 내역 (공개)

| 도구 | 쓰인 곳 |
|---|---|
| **Anthropic Claude API** (서비스 안) | 자소서 생성·첨삭, 점수 설명, 기업 스토리 카드 요약 (5장) |
| **Claude Code** (개발 도구) | 코드 작성·리팩터링·버그 수정·테스트·문서화. 커밋 작성자가 `Claude` 로 기록된 커밋은 이 도구로 만든 것입니다(`git log --author=Claude`로 확인 가능). 팀원이 요구사항을 정하고 결과를 검토해 반영했습니다. |
| Gemini · 짓다 등 | [팀 확인 필요] 이전 README 는 기획·설계 보조, UX 문구 작성에 썼다고 적었습니다. 서비스 코드 안에서 호출하지는 않습니다. |

---

## 11. 알려진 한계

- Q-Net·고용24 실제 연동은 키와 규격 확인 전이라 현재는 백업 데이터로 동작합니다.
- 공기업·강소기업 공고는 공식 API 미연동(큐레이션 데이터).
- 팀 큐레이션 기업 데이터는 아직 0건입니다.
- 프리미엄 결제는 구현되어 있지 않습니다.
- 소셜 로그인은 각 플랫폼 키를 등록해야 켜집니다.
- Supabase 를 연결하지 않으면 재배포 때 사용자·기록이 사라집니다.

---

E.M.P Team — 학교에서 배운 기술이 시장의 기회가 되는 그날까지.
