# 저장소 설정 — 기록을 잃지 않으려면

## 왜 필요한가

Streamlit Community Cloud 의 파일시스템은 **재배포·슬립 해제 시 초기화**됩니다.
지금 상태로 100명이 쓰면, 진단 점수·찜한 기업·로드맵 스탬프가 어느 날 그냥
사라집니다. 재방문해야 값이 생기는 서비스인데 재방문할 이유가 없어지는 구조라,
실사용으로 가려면 외부 저장소가 필요합니다.

앱은 `SUPABASE_URL`·`SUPABASE_KEY` 가 secrets 에 있으면 Supabase 를 쓰고,
없으면 로컬 파일로 동작합니다. **설정하지 않아도 앱은 그대로 돌아갑니다** —
다만 기록이 휘발될 뿐입니다. 현재 어느 쪽으로 동작 중인지는 마이페이지 하단과
관리자 화면(기업 데이터 입력) 상단에 표시됩니다.

---

## 설정 순서 (약 10분)

### 1. Supabase 프로젝트 만들기

1. https://supabase.com 에서 가입 후 새 프로젝트 생성 (무료 플랜으로 충분)
2. 프로젝트가 준비되면 **Project Settings → API** 에서 두 값을 확인
   - `Project URL` → `SUPABASE_URL`
   - `anon public` 키 → `SUPABASE_KEY`

### 2. 테이블 만들기

Supabase 대시보드의 **SQL Editor** 에 아래를 붙여넣고 실행합니다.

```sql
create table if not exists app_state (
  key        text primary key,
  doc        jsonb not null default '{}'::jsonb,
  version    bigint not null default 0,
  updated_at timestamptz not null default now()
);

-- 앱은 anon 키로 접속하므로 RLS 를 켜고 이 테이블만 열어준다.
alter table app_state enable row level security;

create policy "app_state 읽기" on app_state
  for select using (true);
create policy "app_state 쓰기" on app_state
  for insert with check (true);
create policy "app_state 갱신" on app_state
  for update using (true);
```

> **주의** — 위 정책은 anon 키를 가진 누구나 읽고 쓸 수 있게 합니다. 교내
> 시연·수업용으로는 충분하지만, 외부에 공개할 서비스라면 Supabase Auth 를
> 붙여 사용자별로 정책을 좁혀야 합니다. 지금 앱은 게스트 모드가 기본이라
> 사용자별 인증 주체가 없어 이렇게 두었습니다.

### 3. 키 등록

**로컬**: `.streamlit/secrets.toml`

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOi..."
```

**Streamlit Cloud**: 앱 → Settings → Secrets 에 같은 내용을 붙여넣습니다.

`.streamlit/secrets.toml` 은 `.gitignore` 에 들어 있어 커밋되지 않습니다.
키를 저장소에 올리지 마세요.

### 4. 확인

앱을 다시 켜고 마이페이지 하단을 봅니다.

- `저장 위치: Supabase` → 연결 성공
- `저장 위치: 로컬 파일 · 재배포 시 초기화됨` → 키가 안 읽히고 있음
- 관리자 화면 상단에 연결 오류 메시지가 뜨면 그 사유를 확인

---

## 동시 저장은 어떻게 처리하나

문서 하나를 통째로 읽고 쓰는 구조라, 두 학생이 같은 순간에 저장하면 한쪽이
다른 쪽을 덮어쓸 수 있습니다. 이를 막기 위해 `version` 컬럼으로 낙관적 잠금을
겁니다.

1. 읽을 때 `version` 을 같이 받아둔다
2. 쓸 때 `version` 이 그대로일 때만 갱신한다
3. 어긋나면(= 그 사이 누가 썼다) **최신 문서를 다시 읽어 그 위에 내 변경만
   얹어** 재시도한다

3번이 핵심입니다. 그냥 재시도하면 내가 들고 있던 옛 문서가 상대의 저장을
지웁니다. 실제로 그렇게 구현했다가 테스트에서 다른 사용자 레코드가 사라지는
것을 확인하고 고쳤습니다.

**한계**: 삭제한 레코드는 되살아날 수 있습니다. 삭제인지 애초에 몰랐던 것인지
문서만 봐서는 구분할 수 없기 때문입니다. 이 앱의 쓰기는 거의 전부 추가·수정이라
이 쪽이 안전한 선택입니다.

검증: `python3 scripts/test_storage_backend.py` (네트워크 없이 가짜 REST 로
6가지 시나리오를 돌립니다 — 빈 상태, 첫 저장, 재조회, 갱신, 동시 충돌,
네트워크 실패)

---

## 다른 DB 를 쓰고 싶다면

`services/storage_backend.py` 에 클래스를 하나 더 만들고 `get_backend()` 에서
고르게 하면 됩니다. 필요한 것은 두 메서드뿐입니다.

```python
class MyBackend:
    name = "내 DB"
    durable = True
    def read(self, empty_doc) -> dict: ...
    def write(self, doc) -> bool: ...
```

`services/store.py` 는 이 두 함수만 부르므로 나머지 코드는 건드리지 않아도
됩니다.
