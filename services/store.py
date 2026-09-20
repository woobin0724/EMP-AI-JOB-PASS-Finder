# -*- coding: utf-8 -*-
"""
services/store.py
[Phase 1~3] 사용자 · 반(학급) · 활동기록 영속 저장소

문서 하나를 통째로 읽고 쓴다
---------------------------
사용자·반·활동기록을 dict 하나에 담고, _read_all() / _write_all() 두 함수로만
주고받는다. 스키마를 잘게 쪼개지 않은 덕에 '어디에 저장하는가'를 바꿔도
이 파일의 나머지 코드는 그대로다.

▣ 어디에 저장되는가
   services/storage_backend.py 가 정한다. secrets 에 SUPABASE_URL·SUPABASE_KEY
   가 있으면 Supabase(Postgres), 없으면 로컬 JSON 파일이다.

   로컬 파일은 Streamlit Community Cloud 에서 **재배포·슬립 해제 시 초기화**된다.
   즉 "한 세션~며칠" 수준의 영속성이며 영구 저장이 아니다. 실사용으로 가려면
   Supabase 를 붙여야 한다 — 설정 순서는 docs/STORAGE.md 에 있다.
   현재 어느 쪽으로 동작 중인지는 store_summary() 가 알려준다.

동시성
------
Streamlit 은 사용자마다 별도 스레드로 스크립트를 재실행하므로 동시 쓰기가
일어난다. 로컬 파일은 임시파일 + os.replace 로 원자적으로 쓰지만 마지막
쓰기가 이긴다(last-write-wins). Supabase 백엔드는 version 컬럼으로 낙관적
잠금을 걸고, 충돌하면 최신 문서에 내 변경만 얹어 재시도한다.
자세한 내용과 한계는 storage_backend.py 와 docs/STORAGE.md 참고.
"""

import os
import random
from datetime import datetime, timezone

from services import storage_backend

# 경로는 백엔드가 소유한다. 다른 모듈이 참조하던 이름이라 여기서도 노출한다.
STORE_DIR = storage_backend.STORE_DIR
STORE_PATH = storage_backend.STORE_PATH

SCHEMA_VERSION = 1

# 반 코드에서 헷갈리는 글자(0/O, 1/I)를 뺀 안전 문자집합.
# 선생님이 칠판에 적고 학생이 폰으로 옮겨 적는 상황을 가정했다.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CLASS_CODE_LENGTH = 6


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty_doc() -> dict:
    return {
        "_meta": {"version": SCHEMA_VERSION, "updated_at": _now()},
        "users": {},
        "classes": {},
    }


# ------------------------------------------------------------
# 저수준 입출력 — 실서비스 이관 시 이 두 함수만 교체하면 된다
# ------------------------------------------------------------
def _read_all() -> dict:
    """
    저장소 전체를 읽는다. 어디서 읽는지는 백엔드가 정한다
    (services/storage_backend.py — 로컬 파일 또는 Supabase).
    읽기가 실패해도 예외를 던지지 않고 빈 문서를 돌려준다.
    """
    doc = storage_backend.get_backend().read(_empty_doc)
    # 최소 스키마 보정 (수동 편집·구버전 문서 대비)
    doc.setdefault("users", {})
    doc.setdefault("classes", {})
    doc.setdefault("_meta", {"version": SCHEMA_VERSION})
    return doc


def _write_all(doc: dict) -> bool:
    """저장소 전체를 쓴다. 원자성·동시성 처리는 백엔드가 맡는다."""
    doc["_meta"] = {"version": SCHEMA_VERSION, "updated_at": _now()}
    return storage_backend.get_backend().write(doc)


# ------------------------------------------------------------
# 사용자
# ------------------------------------------------------------
def get_user(user_id: str) -> dict | None:
    if not user_id:
        return None
    return _read_all()["users"].get(user_id)


def _default_user(user_id: str) -> dict:
    """
    사용자 레코드의 표준 형태.
    upsert_user 뿐 아니라 create_class / join_class 에서도 이걸 쓴다.
    (예전에는 각자 최소 dict 를 만들어서, 반에 먼저 등록된 사용자는
     bookmarks·score_history 같은 키가 통째로 빠진 채 저장됐다.)
    """
    return {
        "user_id": user_id,
        "provider": "guest",
        "display_name": "",
        "email": "",
        "role": None,           # "student" | "teacher" | None
        "class_code": None,     # 학생: 소속 반 / 선생님: 담당 반
        "class_skipped": False, # 반 등록을 건너뛴 학생 (다시 묻지 않기 위함)
        "created_at": _now(),
        "profile": {},          # 학과·내신·목표기업 스냅샷 (선생님 대시보드용)
        "bookmarks": [],        # 찜한 기업
        "viewed": [],           # 열람 이력
        "score_history": [],    # 매칭 점수 히스토리
        "milestones": {},       # 로드맵 진행 단계
    }


def upsert_user(user_id: str, **fields) -> dict:
    """
    사용자를 생성하거나 갱신한다.
    이미 있는 사용자는 전달한 필드만 덮어쓰고 나머지(활동 기록 등)는 보존한다.
    """
    doc = _read_all()
    user = doc["users"].get(user_id)

    if user is None:
        user = _default_user(user_id)
    else:
        # 구버전 레코드에 새로 생긴 키를 채워 넣는다
        for key, value in _default_user(user_id).items():
            user.setdefault(key, value)

    user.update({k: v for k, v in fields.items() if v is not None})
    user["last_seen_at"] = _now()

    doc["users"][user_id] = user
    _write_all(doc)
    return user


def set_role(user_id: str, role: str) -> dict:
    """역할(학생/선생님)을 확정 저장한다. 재방문 시 역할 선택 화면을 건너뛰는 근거."""
    return upsert_user(user_id, role=role)


def has_role(user_id: str) -> bool:
    user = get_user(user_id)
    return bool(user and user.get("role"))


# ------------------------------------------------------------
# 반(학급) — Phase 2 에서 본격 사용, 스키마는 여기서 확정한다
# ------------------------------------------------------------
def generate_class_code(existing: dict | None = None) -> str:
    """중복되지 않는 6자리 반 코드를 발급한다."""
    existing = existing if existing is not None else _read_all()["classes"]
    for _ in range(200):
        code = "".join(random.choice(_CODE_ALPHABET) for _ in range(CLASS_CODE_LENGTH))
        if code not in existing:
            return code
    # 200회 모두 충돌하는 경우는 사실상 없지만, 그래도 멈추지 않게 한다
    return "".join(random.choice(_CODE_ALPHABET) for _ in range(CLASS_CODE_LENGTH + 2))


def create_class(teacher_id: str, school: str, grade: str, class_no: str) -> dict:
    """선생님이 '우리 반'을 만든다. 반환값에 발급된 class_code 가 들어 있다."""
    doc = _read_all()
    code = generate_class_code(doc["classes"])

    klass = {
        "class_code": code,
        "school": school,
        "grade": grade,
        "class_no": class_no,
        "teacher_id": teacher_id,
        "created_at": _now(),
        "students": [],
    }
    doc["classes"][code] = klass

    teacher = doc["users"].get(teacher_id) or _default_user(teacher_id)
    teacher["role"] = "teacher"
    teacher["class_code"] = code
    teacher["last_seen_at"] = _now()
    doc["users"][teacher_id] = teacher

    _write_all(doc)
    return klass


def get_class(class_code: str) -> dict | None:
    if not class_code:
        return None
    return _read_all()["classes"].get(class_code.strip().upper())


def join_class(user_id: str, class_code: str) -> tuple[bool, str]:
    """
    학생을 반에 등록한다.
    반환값: (성공여부, 안내 메시지)
    """
    code = (class_code or "").strip().upper()
    if not code:
        return False, "반 코드를 입력해주세요."

    doc = _read_all()
    klass = doc["classes"].get(code)
    if klass is None:
        return False, "존재하지 않는 반 코드입니다. 선생님께 다시 확인해주세요."

    if user_id not in klass["students"]:
        klass["students"].append(user_id)

    student = doc["users"].get(user_id) or _default_user(user_id)
    student["role"] = "student"
    student["class_code"] = code
    student["last_seen_at"] = _now()
    doc["users"][user_id] = student

    _write_all(doc)
    label = f"{klass['school']} {klass['grade']} {klass['class_no']}"
    return True, f"{label} 에 등록되었습니다."


def class_students(class_code: str) -> list[dict]:
    """반 소속 학생들의 사용자 레코드 목록 (선생님 대시보드용)."""
    doc = _read_all()
    klass = doc["classes"].get((class_code or "").strip().upper())
    if not klass:
        return []
    return [doc["users"][sid] for sid in klass["students"] if sid in doc["users"]]


# ------------------------------------------------------------
# 활동 기록 — Phase 3 마이페이지에서 사용
# ------------------------------------------------------------
def _mutate_user(user_id: str, fn) -> dict | None:
    """읽기→변형→쓰기를 한 번에 처리하는 내부 헬퍼."""
    if not user_id:
        return None
    doc = _read_all()
    user = doc["users"].get(user_id)
    if user is None:
        return None
    fn(user)
    user["last_seen_at"] = _now()
    doc["users"][user_id] = user
    _write_all(doc)
    return user


def toggle_bookmark(user_id: str, company_id: str) -> bool:
    """찜하기 토글. 반환값은 '토글 후 찜 상태'."""
    state = {"on": False}

    def _fn(user):
        marks = user.setdefault("bookmarks", [])
        if company_id in marks:
            marks.remove(company_id)
            state["on"] = False
        else:
            marks.append(company_id)
            state["on"] = True

    _mutate_user(user_id, _fn)
    return state["on"]


def is_bookmarked(user_id: str, company_id: str) -> bool:
    user = get_user(user_id)
    return bool(user and company_id in (user.get("bookmarks") or []))


def record_view(user_id: str, company_id: str, company_name: str = "") -> None:
    """기업 상세 열람 이력을 남긴다. 같은 기업은 최근 1건으로 합친다."""
    def _fn(user):
        viewed = [v for v in user.setdefault("viewed", []) if v.get("company_id") != company_id]
        viewed.insert(0, {"company_id": company_id, "company_name": company_name, "at": _now()})
        user["viewed"] = viewed[:50]

    _mutate_user(user_id, _fn)


def record_score(user_id: str, score: float, company_id: str = "", company_name: str = "") -> None:
    """매칭 점수 히스토리를 남긴다 (최근 100건 유지)."""
    def _fn(user):
        history = user.setdefault("score_history", [])
        history.insert(0, {
            "score": round(float(score), 1), "company_id": company_id,
            "company_name": company_name, "at": _now(),
        })
        user["score_history"] = history[:100]

    _mutate_user(user_id, _fn)


def save_milestones(user_id: str, milestones: dict) -> None:
    """로드맵 마일스톤 진행 상태를 저장한다 (선생님 대시보드에서 조회)."""
    _mutate_user(user_id, lambda u: u.update({"milestones": dict(milestones)}))


def save_profile(user_id: str, **profile) -> None:
    """학과·내신·목표기업 등 프로필 스냅샷 저장."""
    def _fn(user):
        snapshot = user.setdefault("profile", {})
        snapshot.update({k: v for k, v in profile.items() if v is not None})

    _mutate_user(user_id, _fn)


# ------------------------------------------------------------
# 운영 편의
# ------------------------------------------------------------
def store_summary() -> str:
    doc = _read_all()
    st_info = storage_backend.status()
    where = st_info["name"] + ("" if st_info["durable"] else " · 재배포 시 초기화됨")
    return f"가입 {len(doc['users'])}명 · 개설된 반 {len(doc['classes'])}개 · 저장 위치: {where}"


def store_exists() -> bool:
    return os.path.exists(STORE_PATH)


# ------------------------------------------------------------
# [Phase 2] 반 등록 보조
# ------------------------------------------------------------
def skip_class(user_id: str) -> None:
    """
    학생이 '혼자 사용할게요'를 선택한 경우.

    반 등록은 **선택**이다. 반 코드가 없는 학생(혼자 준비하는 학생, 시연 중인
    심사위원)이 코드 입력 화면에 갇히면 게스트모드로 모든 기능을 쓸 수 있다는
    약속이 깨진다. 그래서 건너뛴 사실을 영속 저장해 다시 묻지 않는다.
    """
    _mutate_user(user_id, lambda u: u.update({"class_skipped": True}))


def needs_class_prompt(user_id: str) -> bool:
    """반 코드 입력 화면을 보여줘야 하는 학생인가 (아직 소속도 없고 건너뛰지도 않음)."""
    user = get_user(user_id)
    if not user or user.get("role") != "student":
        return False
    return not user.get("class_code") and not user.get("class_skipped")


def leave_class(user_id: str) -> bool:
    """학생을 현재 반에서 탈퇴시킨다 (반을 잘못 입력한 경우)."""
    doc = _read_all()
    user = doc["users"].get(user_id)
    if not user or not user.get("class_code"):
        return False

    klass = doc["classes"].get(user["class_code"])
    if klass and user_id in klass.get("students", []):
        klass["students"].remove(user_id)

    user["class_code"] = None
    user["class_skipped"] = True   # 탈퇴 후 다시 묻지 않는다
    user["last_seen_at"] = _now()
    doc["users"][user_id] = user
    _write_all(doc)
    return True


def teacher_class(teacher_id: str) -> dict | None:
    """선생님이 담당하는 반. 없으면 None."""
    doc = _read_all()
    for klass in doc["classes"].values():
        if klass.get("teacher_id") == teacher_id:
            return klass
    return None


def class_label(klass: dict | None) -> str:
    """'전북기계공고 3학년 2반' 형태의 표시 문자열."""
    if not klass:
        return ""
    parts = [klass.get("school", ""), klass.get("grade", ""), klass.get("class_no", "")]
    return " ".join(p for p in parts if p)
