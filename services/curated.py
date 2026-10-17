# -*- coding: utf-8 -*-
"""
services/curated.py
팀이 직접 조사해 넣는 기업 마스터 데이터 — 저장소와 검증

▣ 설계 원칙
   데이터는 스크래핑이 아니라 사람이 조사해 넣는다. 그러면 "이 값이 어디서
   왔는가"가 코드가 아니라 사람의 기억에만 남는다. 그래서 기존 스키마에
   출처 필드(source_url / source_type / checked_by / checked_at)를 더해
   나중에 누구든 원문을 다시 확인할 수 있게 했다.

▣ 실제 기업은 '확인 가능한 사실'만 [big-patch 1단계]
   이 파일로 들어오는 기업은 실제 기업이다. 그래서 팀이 지어낼 수밖에 없는
   항목(별점 · 장단점 · 면접 기출 · 합격자 평균 스펙 · 복지 요약)은 스키마에서
   뺐고, 예전 형식으로 저장된 값이 있어도 sanitize_real() 이 읽을 때 지운다.
   남는 것은 업종 · 소재지 · 공식 채용 페이지 같은 공개 사실과, 원문을 복사하지
   않은 짧은 인재상 요약(출처 링크 필수) 뿐이다. 모든 레코드에 출처 URL 과
   수집일(checked_at)이 필수다. 확실하지 않은 값은 비워 둔다.

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

# 실제 기업 스키마 — 공개적으로 확인 가능한 사실 + 출처.
# (키, 라벨, 종류, 필수여부) — 종류는 입력 위젯을 고르는 데 쓴다.
FIELDS = [
    ("id",                  "식별자 (영문·숫자·밑줄)",                  "text",   True),
    ("name",                "기업명 (공식 명칭)",                      "text",   True),
    ("size_tag",            "기업 유형",                               "choice", True),
    ("category",            "계열 분류",                               "choice", True),
    ("field_tag",           "분야 태그 (비우면 계열과 같게)",           "text",   False),
    ("description",         "업종 한 줄 (예: 송배전 설비 운영)",        "text",   True),
    ("region",              "소재지 (예: 전남 나주)",                   "text",   False),
    ("official_recruit_url", "공식 채용 페이지 URL",                    "text",   False),
    ("hire_dept",           "채용 직무 (공식 공고에 있는 경우만)",      "text",   False),
    ("work_conditions",     "근무 조건 (공식 공고에 있는 경우만)",      "area",   False),
    ("required_certs",      "우대·필수 자격증 (공식 공고 기준, 쉼표)",  "list",   False),
    ("required_skills",     "요구 역량 (공식 공고 기준, 쉼표)",         "list",   False),
    ("ideal_talent",        "인재상 키워드 (요약, 쉼표)",               "list",   False),
    ("talent_summary",      f"인재상 한 줄 요약 (원문 복사 금지, {80}자 이내)", "area", False),
    ("talent_source_url",   "인재상 출처 URL (인재상을 쓰면 필수)",     "text",   False),
    # ---- 출처 (검증용 · 모든 레코드 필수) ----
    ("source_url",          "출처 URL",                                 "text",   True),
    ("source_type",         "출처 유형",                                "choice", True),
    ("checked_by",          "조사자",                                   "text",   True),
    ("checked_at",          "수집일 (YYYY-MM-DD)",                      "date",   True),
]

REQUIRED = [k for k, _, _, req in FIELDS if req]
URL_FIELDS = ("source_url", "official_recruit_url", "talent_source_url")
TALENT_SUMMARY_MAX = 80

# 실제 기업에는 둘 수 없는 항목 — 팀이 사실로 확인할 수 없어 지어내게 되는 값들.
# 예전 형식으로 저장된 레코드에 남아 있어도 읽을 때 지운다.
FORBIDDEN_REAL_FIELDS = (
    "overall_rating", "ratings", "pros", "cons", "interview_questions",
    "avg_applicant_grade", "avg_applicant_certs", "benefit_short", "exam_keywords",
    "salary", "reviews",
)

# 숫자 필드 범위 (실제 기업 스키마에는 숫자 필드가 없다 — 관리자 화면 호환용)
BOUNDS: dict = {}

SIZE_TAGS = ["대기업", "중견기업", "중소기업", "강소기업", "공기업", "스타트업"]


def sanitize_real(row: dict) -> dict:
    """
    화면에 내보내기 전에 실제 기업 레코드를 정리한다.

    · 지어낼 수밖에 없는 항목(FORBIDDEN_REAL_FIELDS)을 지운다
    · data_kind = "verified" 를 붙여 화면이 '출처 확인' 표시를 하게 한다
    · 화면이 기대하는 목록 필드는 빈 목록으로 채운다 (값을 지어내지 않는다)
    """
    clean = {k: v for k, v in row.items() if k not in FORBIDDEN_REAL_FIELDS}
    clean["data_kind"] = "verified"
    for key in ("required_certs", "required_skills", "ideal_talent"):
        if not isinstance(clean.get(key), list):
            clean[key] = []
    for key in ("description", "region", "work_conditions", "hire_dept",
                "official_recruit_url", "talent_summary", "talent_source_url"):
        clean[key] = str(clean.get(key) or "")
    clean["field_tag"] = clean.get("field_tag") or clean.get("category", "")
    return clean


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

    for key in URL_FIELDS:
        url = (row.get(key) or "").strip()
        if url and not url.startswith(("http://", "https://")):
            label = next(lbl for k, lbl, _, _ in FIELDS if k == key)
            errors.append(f"'{label}' 은(는) http:// 또는 https:// 로 시작해야 합니다.")

    has_talent = bool(row.get("ideal_talent")) or bool((row.get("talent_summary") or "").strip())
    if has_talent and not (row.get("talent_source_url") or "").strip():
        errors.append("인재상을 적었다면 인재상 출처 URL 이 필요합니다.")
    if len((row.get("talent_summary") or "").strip()) > TALENT_SUMMARY_MAX:
        errors.append(f"인재상 요약은 {TALENT_SUMMARY_MAX}자 이내로 줄여 주세요 (원문 복사 방지).")

    checked = str(row.get("checked_at") or "").strip()
    if checked:
        try:
            if date.fromisoformat(checked[:10]) > date.today():
                errors.append("수집일이 오늘보다 뒤일 수 없습니다.")
        except ValueError:
            errors.append("수집일은 YYYY-MM-DD 형식이어야 합니다.")

    leftover = [k for k in FORBIDDEN_REAL_FIELDS if row.get(k) not in (None, "", [], {})]
    if leftover:
        errors.append("실제 기업에는 확인할 수 없는 항목을 둘 수 없습니다: " + ", ".join(leftover))

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
