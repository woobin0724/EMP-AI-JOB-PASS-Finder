# -*- coding: utf-8 -*-
"""
services/curated.py
팀이 직접 조사해 넣는 기업 마스터 데이터 — 저장소와 검증

▣ 설계 원칙
   데이터는 스크래핑이 아니라 사람이 조사해 넣는다. 그러면 "이 값이 어디서
   왔는가"가 코드가 아니라 사람의 기억에만 남는다. 그래서 기존 스키마에
   출처 필드(source_url / source_type / checked_by / checked_at)를 더해
   나중에 누구든 원문을 다시 확인할 수 있게 했다.

▣ 저장 위치와 Streamlit Cloud 주의
   data/curated_companies.json 에 저장한다. 다만 Streamlit Community Cloud 는
   재배포·슬립 해제 시 파일시스템이 초기화되므로, 화면에서 JSON 을 내려받아
   저장소에 커밋하는 것까지가 한 사이클이다. 관리자 화면이 그 안내를 띄운다.
"""

import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATED_PATH = os.path.join(BASE_DIR, "data", "curated_companies.json")

SOURCE_TYPES = ["공식 홈페이지", "채용 공고", "보도자료", "공공데이터", "기타"]

# 기존 company_showcase 스키마 + 출처 필드.
# (키, 라벨, 종류, 필수여부) — 종류는 입력 위젯을 고르는 데 쓴다.
FIELDS = [
    ("id",                  "식별자 (영문·숫자·밑줄)",        "text",   True),
    ("name",                "기업명",                         "text",   True),
    ("size_tag",            "기업 규모",                      "choice", True),
    ("field_tag",           "분야 태그",                      "text",   True),
    ("category",            "계열 분류",                      "choice", True),
    ("description",         "한 줄 소개",                     "text",   True),
    ("hire_dept",           "채용 부서",                      "text",   False),
    ("overall_rating",      "종합 별점 (0~5)",                "number", False),
    ("benefit_short",       "복지 요약",                      "area",   False),
    ("required_certs",      "요구 자격증 (쉼표로 구분)",      "list",   True),
    ("required_skills",     "요구 역량 (쉼표로 구분)",        "list",   False),
    ("ideal_talent",        "인재상 키워드 (쉼표로 구분)",    "list",   True),
    ("exam_keywords",       "필기 키워드",                    "area",   False),
    ("interview_questions", "면접 기출 (줄바꿈으로 구분)",    "lines",  False),
    ("pros",                "장점",                           "area",   False),
    ("cons",                "단점·고충",                      "area",   False),
    ("avg_applicant_grade", "합격자 평균 내신 (1.0~5.0)",     "number", False),
    ("avg_applicant_certs", "합격자 평균 자격증 수",          "int",    False),
    # ---- 출처 (검증용) ----
    ("source_url",          "출처 URL",                       "text",   True),
    ("source_type",         "출처 유형",                      "choice", True),
    ("checked_by",          "조사자",                         "text",   True),
    ("checked_at",          "조사일",                         "date",   True),
]

REQUIRED = [k for k, _, _, req in FIELDS if req]

# 숫자 필드의 허용 범위와 기본값.
# 위젯에서 범위를 막지 않으면, 선택 항목인데도 기본값 0 이 범위 검증에 걸려
# 저장이 막힌다(실제로 그렇게 막혔다).
BOUNDS = {
    "overall_rating":      (0.0, 5.0, 4.0),
    "avg_applicant_grade": (1.0, 5.0, 3.0),
    "avg_applicant_certs": (0, 10, 2),
}

SIZE_TAGS = ["대기업", "중견기업", "중소기업", "강소기업", "공기업", "스타트업"]


def load() -> list[dict]:
    """큐레이션 데이터를 읽는다. 파일이 없거나 깨져 있으면 빈 목록."""
    try:
        with open(CURATED_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def save(rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(CURATED_PATH), exist_ok=True)
    with open(CURATED_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def validate(row: dict, existing: list[dict], editing_id: str = "") -> list[str]:
    """저장 전 검사. 반환값은 사람이 읽을 오류 메시지 목록(빈 목록이면 통과)."""
    errors = []
    for key in REQUIRED:
        value = row.get(key)
        if value in (None, "", [], []):
            label = next(lbl for k, lbl, _, _ in FIELDS if k == key)
            errors.append(f"'{label}' 은(는) 필수입니다.")

    ident = (row.get("id") or "").strip()
    if ident and not all(c.isalnum() or c == "_" for c in ident):
        errors.append("식별자는 영문·숫자·밑줄만 쓸 수 있습니다.")
    if ident and ident != editing_id and any(r.get("id") == ident for r in existing):
        errors.append(f"식별자 '{ident}' 는 이미 있습니다.")

    url = (row.get("source_url") or "").strip()
    if url and not url.startswith(("http://", "https://")):
        errors.append("출처 URL 은 http:// 또는 https:// 로 시작해야 합니다.")

    for key, (lo, hi, _) in BOUNDS.items():
        value = row.get(key)
        if value in (None, ""):
            continue
        try:
            if not (lo <= float(value) <= hi):
                label = next(lbl for k, lbl, _, _ in FIELDS if k == key)
                errors.append(f"'{label}' 은(는) {lo}~{hi} 범위여야 합니다.")
        except (TypeError, ValueError):
            errors.append(f"'{key}' 에 숫자가 아닌 값이 들어 있습니다.")
    return errors


def upsert(row: dict, editing_id: str = "") -> None:
    """식별자 기준으로 추가하거나 덮어쓴다."""
    rows = load()
    target = editing_id or row.get("id")
    for i, existing in enumerate(rows):
        if existing.get("id") == target:
            rows[i] = row
            break
    else:
        rows.append(row)
    save(rows)


def delete(ident: str) -> None:
    save([r for r in load() if r.get("id") != ident])


def blank_row() -> dict:
    """새 입력 폼의 기본값."""
    row = {}
    for key, _, kind, _ in FIELDS:
        if kind in ("list", "lines"):
            row[key] = []
        elif key in BOUNDS:
            row[key] = BOUNDS[key][2]
        else:
            row[key] = ""
    row["checked_at"] = date.today().isoformat()
    row["source_type"] = SOURCE_TYPES[0]
    return row


def to_csv_rows(rows: list[dict]) -> list[dict]:
    """스프레드시트로 내보내기 — 리스트 필드를 문자열로 평탄화한다."""
    out = []
    for r in rows:
        flat = {}
        for key, _, kind, _ in FIELDS:
            v = r.get(key)
            if kind == "list":
                flat[key] = ", ".join(v or [])
            elif kind == "lines":
                flat[key] = " | ".join(v or [])
            else:
                flat[key] = "" if v is None else v
        out.append(flat)
    return out


def from_csv_rows(rows: list[dict]) -> list[dict]:
    """스프레드시트에서 들여오기 — 문자열을 리스트로 되돌린다."""
    out = []
    for r in rows:
        item = {}
        for key, _, kind, _ in FIELDS:
            raw = (r.get(key) or "").strip() if isinstance(r.get(key), str) else r.get(key)
            if kind == "list":
                item[key] = [s.strip() for s in (raw or "").split(",") if s.strip()]
            elif kind == "lines":
                item[key] = [s.strip() for s in (raw or "").split("|") if s.strip()]
            elif kind in ("number", "int"):
                try:
                    item[key] = (int(raw) if kind == "int" else float(raw)) if raw not in (None, "") else None
                except (TypeError, ValueError):
                    item[key] = None
            else:
                item[key] = raw or ""
        out.append(item)
    return out
