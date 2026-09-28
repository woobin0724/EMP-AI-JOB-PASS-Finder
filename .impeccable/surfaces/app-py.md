---
version: 1
slug: "app-py"
primary_target: "app.py"
related_targets: ["ui/theme.py"]
---

# Surface: 앱 전체 (Streamlit)

Scope: 랜딩·로그인·역할선택·반 개설/등록·허브·스펙 진단·기업 탐색·가이드·자소서·로드맵·마이페이지·우리 반·기업 데이터 입력. Visitor mode: Operate (랜딩만 Persuade).

Audience/job: 마이스터고 학생이 폰으로 내 점수 → 기업 → 자소서까지 진행. 선생님은 반 현황 확인. Proof: 로컬 100점 환산 점수(실제 동작), 예시 데이터 표기 유지. Constraints: 기능 전부 유지, 폰 390px, 44px 타깃, 외부 CDN 차단 가능.

Unresolved: roll ran degraded (roll service unreachable) — no challengers, no quality-bar boards; direction chosen unattended from grounded list.

## Direction contract

THESIS: 마이스터고 학생의 스펙을 '발급되는 자격 문서'로 다룬다. 점수는 진단서에 찍히는 도장이고, 화면은 국가기술자격증 수첩의 표지와 양식이다. 채용 포털의 흰 카드+파란 버튼, 그리고 이전의 다크 네이비+네온 글로우 AI 룩을 거부한다.

OWN-WORLD: 수첩 표지 네이비 띠(상단 바·랜딩 표지)에 금박 엠블럼. 본문은 차가운 민트그레이 보안용지 위 흰 양식지, 1px 괘선 표 격자, 직각에 가까운 모서리(4px), 그림자 없음. 필드 라벨 칸(성명/종목/번호 형식), 발급번호형 등폭 숫자, 인주 주홍 도장, 일부인 보라 잉크. 제목은 자간 넓힌 명조, 본문 Pretendard.

STORY: 학생은 표지를 넘기듯 들어와 내 스펙이 몇 점짜리 문서인지 확인하고, 도장이 찍힌 판정을 보고, 다음 단계(기업 탐색→자소서)로 넘어간다.

FIRST VIEWPORT: 랜딩 = 화면 폭 네이비 표지 블록: 금박 엠블럼 중앙, 명조 서비스명, 한 줄 설명, 표지 아래 흰 양식 위에 '시작하기' 주 버튼. 대회 본선 진출은 표지 모서리의 원형 인장. 진단 화면 = 점수 도장(원형 주홍/녹색 인장, 큰 등폭 숫자)이 진단서 양식 첫 칸에 있다.

FORM: 국가기술자격증 수첩·공문서 양식 — grounded list 5번째 (1 작업지시서 트래블러, 2 KS 기계제도 도면, 3 산업안전 표지·바닥 라인, 4 계측기 눈금, 5 자격증 수첩·공문서, 6 설비 명판, 7 취업 게시판). Seed key 32bfb927. Signature interaction: 점수·판정 도장이 '찍히는' 모션(1.18배→1배, 살짝 회전, 잉크 번짐) 한 번. Build path: code-led (no image generation).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
