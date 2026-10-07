# -*- coding: utf-8 -*-
"""
scripts/prewarm_story_cache.py
시연 전에 기업 스토리 카드(카드 1~4)를 미리 만들어 data/story_cache.json 에 저장한다.

왜 필요한가
-----------
스토리 카드의 AI 요약은 프리미엄(또는 데모) 계정이 볼 때만 만들어진다. 시연 중에
처음 보는 기업마다 Claude 를 기다리면 화면이 몇 초씩 멈춘다. 미리 만들어 두면
  · 시연 때 바로 뜨고 (API 호출 0회)
  · 무료 회원도 저장된 AI 요약을 그대로 본다 (services/story_cards.py 의 파일 캐시)

Streamlit Cloud 는 재배포하면 파일이 지워지므로, 이 스크립트를 로컬에서 돌린 뒤
data/story_cache.json 을 커밋해야 배포본에도 남는다. (이 파일에는 기업 예시 데이터의
요약만 들어 있고 사용자 정보는 없다.)

사용법
------
    # API 키: 환경변수 CLAUDE_API_KEY(또는 ANTHROPIC_API_KEY) 나 .streamlit/secrets.toml
    python scripts/prewarm_story_cache.py                 # 전체 기업 (이미 있는 건 건너뜀)
    python scripts/prewarm_story_cache.py kepco cosmax    # 지정한 기업 ID 만
    python scripts/prewarm_story_cache.py --force         # 이미 있어도 다시 만듦
    python scripts/prewarm_story_cache.py --list          # 기업 ID 목록과 캐시 여부만 보기

비용: 기업 1곳당 Claude 호출 1회. 원본 데이터가 바뀌지 않는 한 다시 돌려도
이미 만든 기업은 건너뛴다(--force 제외).
"""

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def _api_key() -> str:
    for name in ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        if os.environ.get(name, "").strip():
            return os.environ[name].strip()
    path = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
    try:
        import tomllib
        with open(path, "rb") as f:
            secrets = tomllib.load(f)
        for name in ("CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
            if str(secrets.get(name, "")).strip():
                return str(secrets[name]).strip()
    except (OSError, ValueError):
        pass
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="기업 스토리 카드 미리 생성")
    parser.add_argument("ids", nargs="*", help="만들 기업 ID (생략하면 전체)")
    parser.add_argument("--force", action="store_true", help="이미 저장된 요약도 다시 만든다")
    parser.add_argument("--list", action="store_true", help="기업 ID 와 캐시 여부만 출력")
    args = parser.parse_args()

    from data.company_showcase import all_companies
    from services import story_cards as sc

    companies = {c["id"]: c for c in all_companies()}
    unknown = [i for i in args.ids if i not in companies]
    if unknown:
        print(f"없는 기업 ID: {', '.join(unknown)}  (--list 로 목록 확인)")
        return 1
    targets = [companies[i] for i in (args.ids or companies)]

    def cached(company) -> bool:
        payload = sc.source_payload(company)
        return sc._file_cache_get(company["id"], sc._fingerprint(company["id"], payload)) is not None

    if args.list:
        for c in targets:
            print(f"{'캐시 있음' if cached(c) else '캐시 없음'}  {c['id']:<22} {c['name']}")
        return 0

    key = _api_key()
    if not key:
        print("API 키가 없습니다. 환경변수 CLAUDE_API_KEY 또는 .streamlit/secrets.toml 에 넣어주세요.")
        return 1

    made = skipped = failed = 0
    for c in targets:
        if cached(c) and not args.force:
            skipped += 1
            print(f"건너뜀  {c['id']:<22} (이미 저장됨)")
            continue
        payload = sc.source_payload(c)
        try:
            cards = sc._claude(payload, key)
        except Exception as exc:   # 한 곳이 실패해도 나머지는 계속 만든다
            failed += 1
            print(f"실패    {c['id']:<22} {type(exc).__name__}: {str(exc)[:120]}")
            continue
        sc._file_cache_put(c["id"], sc._fingerprint(c["id"], payload), cards)
        made += 1
        print(f"생성    {c['id']:<22} {' / '.join(card['title'] for card in cards)}")

    print(f"\n완료 — 생성 {made} · 건너뜀 {skipped} · 실패 {failed}  →  {sc.STORY_CACHE_PATH}")
    if made:
        print("배포본에도 반영하려면 data/story_cache.json 을 커밋하세요.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
