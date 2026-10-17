#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/update_company_data.py
실제 기업 데이터(data/curated_companies.json) 갱신 · 검증 도구  [big-patch 1단계]

▣ 무엇을 하나
   실제 기업 데이터는 팀이 공식 홈페이지 · 공식 채용공고 · 공공데이터에서
   확인한 사실만 넣는다(스크래핑 없음). 이 스크립트는 그 데이터가 규칙을
   지키는지 검사하고, 팀이 스프레드시트로 모은 값을 들여온다.

     python scripts/update_company_data.py                 # 검사만 (기본)
     python scripts/update_company_data.py --report        # 현황 + 오래된 레코드(재확인 필요)
     python scripts/update_company_data.py --fix           # 금지 항목(별점·리뷰 등) 지우고 저장
     python scripts/update_company_data.py --import 조사.csv  # CSV 들여오기 (검사 통과분만 반영)

   종료 코드: 0 = 통과, 1 = 규칙 위반 있음

▣ 규칙 (services/curated.py 와 같은 기준)
   · 모든 레코드: 출처 URL · 출처 유형 · 조사자 · 수집일 필수
   · 인재상을 적으면 인재상 출처 URL 필수, 요약은 80자 이내(원문 복사 금지)
   · 별점 · 장단점 · 면접 기출 · 합격자 평균 스펙 · 복지 요약 · 연봉은 실제 기업에 둘 수 없음
   · 확실하지 않은 칸은 비워 둔다

▣ 공식 API 로 자동 갱신하지 않는 이유
   잡알리오 · 공공데이터포털 API 는 키 발급 후 활용가이드로 응답 규격을 확인해야
   한다. 규격을 확인하기 전에 추측으로 클라이언트를 쓰지 않는다는 것이 이 저장소의
   원칙이다(services/alio_api.py). 규격이 확인되면 services/api_registry.py 에
   등록하고 화면은 LIVE 로 전환된다 — 이 스크립트는 사람이 확인한 데이터의 관문이다.
"""

import argparse
import csv
import os
import sys
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from services import curated  # noqa: E402

STALE_DAYS = 180   # 수집한 지 이만큼 지나면 '재확인 필요'로 표시


def check(rows: list[dict]) -> list[tuple[str, list[str]]]:
    """레코드별 (id, 오류 목록). 오류가 없는 레코드는 빠진다."""
    problems = []
    for row in rows:
        others = [r for r in rows if r is not row]
        errors = curated.validate(row, others, editing_id="")
        if errors:
            problems.append((row.get("id") or "(id 없음)", errors))
    return problems


def stale(rows: list[dict], today: date | None = None) -> list[tuple[str, int]]:
    today = today or date.today()
    out = []
    for row in rows:
        try:
            age = (today - date.fromisoformat(str(row.get("checked_at"))[:10])).days
        except ValueError:
            continue
        if age > STALE_DAYS:
            out.append((row.get("id", ""), age))
    return out


def strip_forbidden(rows: list[dict]) -> tuple[list[dict], int]:
    """금지 항목을 지운 사본과 지운 칸 수."""
    removed = 0
    out = []
    for row in rows:
        clean = {}
        for key, value in row.items():
            if key in curated.FORBIDDEN_REAL_FIELDS or key == "data_kind":
                removed += 1 if value not in (None, "", [], {}) else 0
                continue
            clean[key] = value
        out.append(clean)
    return out, removed


def import_csv(path: str, rows: list[dict]) -> tuple[list[dict], list[tuple[str, list[str]]]]:
    """CSV 를 읽어 검사 통과분만 id 기준으로 합친다. 반환: (새 목록, 거절된 행)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        incoming = curated.from_csv_rows(list(csv.DictReader(f)))
    merged = {r.get("id"): r for r in rows}
    rejected = []
    for row in incoming:
        others = [r for k, r in merged.items() if k != row.get("id")]
        errors = curated.validate(row, others, editing_id=row.get("id", ""))
        if errors:
            rejected.append((row.get("id") or "(id 없음)", errors))
        else:
            merged[row["id"]] = row
    return list(merged.values()), rejected


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="실제 기업 데이터 검사 · 갱신")
    ap.add_argument("--report", action="store_true", help="현황과 오래된 레코드 표시")
    ap.add_argument("--fix", action="store_true", help="금지 항목을 지우고 저장")
    ap.add_argument("--import", dest="csv_path", help="CSV 를 검사해 통과분만 반영")
    args = ap.parse_args(argv)

    rows = curated.load()

    if args.csv_path:
        rows, rejected = import_csv(args.csv_path, rows)
        for ident, errors in rejected:
            print(f"거절  {ident}: " + " / ".join(errors))
        curated.save(rows)
        print(f"반영 완료 — 현재 {len(rows)}건 (거절 {len(rejected)}건)")

    if args.fix:
        rows, removed = strip_forbidden(rows)
        curated.save(rows)
        print(f"금지 항목 {removed}칸을 지우고 저장했습니다.")

    problems = check(rows)
    if args.report or not problems:
        print(f"실제 기업(출처 확인) {len(rows)}건 · 규칙 위반 {len(problems)}건")
        for ident, age in stale(rows):
            print(f"재확인 필요  {ident}: 수집한 지 {age}일 (기준 {STALE_DAYS}일)")
    for ident, errors in problems:
        print(f"위반  {ident}: " + " / ".join(errors))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
