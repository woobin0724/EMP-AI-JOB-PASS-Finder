#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/fetch_mascot.py
[Phase 4] OGQ 경연 API 에서 마스코트 캐릭터를 골라 내려받는 CLI

왜 앱이 아니라 CLI 인가
----------------------
마스코트 이미지는 **최초 1회만** 받으면 되고, 그 뒤로는 assets/mascot/ 의
정적 파일로 동작해야 한다(스펙의 분당 호출 한도도 그래야 지켜진다).
앱 실행 중에 API 를 부르면 학생 한 명이 새로고침할 때마다 호출이 나간다.

사용법
------
  # 0) 키 준비 — 셋 중 아무거나
  #    .streamlit/secrets.toml 에  OGQ_API_KEY = "..."
  #    .env 에                    OGQ_API_KEY=...
  #    환경변수                    export OGQ_API_KEY=...

  python3 scripts/fetch_mascot.py --list
      전체 카탈로그를 받아 캐시하고, 우리 서비스에 어울리는 후보를
      점수순으로 보여준다. (다운로드는 하지 않는다)

  python3 scripts/fetch_mascot.py --show <assetId>
      해당 자산의 낱장 목록(images)과 미리보기 URL 을 보여준다.

  python3 scripts/fetch_mascot.py --download <assetId>
      낱장을 전부 내려받아 assets/mascot/<assetId>/ 에 저장하고
      manifest.json 을 쓴다.

  python3 scripts/fetch_mascot.py --download <assetId> --map welcome=1.png,celebrate=7.png
      감정 슬롯에 특정 낱장을 매핑한다 (앱이 이 매핑을 읽어 쓴다).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ogq_api import (  # noqa: E402
    MANIFEST_PATH, MASCOT_DIR, OGQError, download_to, fetch_catalog, get_asset,
    has_api_key, issue_download, key_source, ping,
)

# ------------------------------------------------------------
# 후보 점수화
# ------------------------------------------------------------
# 우리 서비스: 마이스터고 학생 대상 AI 취업 컨설팅 / 다크 테마 / 미니멀
# 판단 기준을 코드로 옮겨 두면, 카탈로그가 바뀌어도 같은 기준으로 다시 고를 수 있다.
FRIENDS = ["피오", "키오", "마리모", "박하", "픽키"]

# 감정 표현이 다양한 스티커일수록 마일스톤 단계별로 다른 낱장을 쓸 수 있다
EMOTION_WORDS = ["감정", "표정", "리액션", "일상", "인사", "축하", "응원", "칭찬", "화이팅"]

# 고등학생 대상이라 과하게 유아적이거나 주제가 어긋나는 것은 감점
NEGATIVE_WORDS = ["아기", "베이비", "유아", "연말", "크리스마스", "새해", "명절", "수능",
                  "할로윈", "밸런타인", "커플", "연애"]


def score_asset(asset: dict) -> tuple[int, list]:
    """자산 하나에 점수와 근거를 매긴다."""
    title = (asset.get("title") or "")
    tags = [str(t) for t in (asset.get("tags") or [])]
    cats = [(c.get("krName") or "") for c in (asset.get("categories") or [])]
    blob = " ".join([title] + tags + cats)

    score, why = 0, []

    # OGQ프렌즈 시리즈 우선 (사용자 지정 기준)
    if any("OGQ프렌즈" in c or "오지큐" in c for c in cats) or "오지큐프렌즈" in blob:
        score += 30; why.append("OGQ프렌즈 시리즈")

    # 단일 캐릭터가 주인공인지 — 태그에 등장하는 캐릭터 이름 수로 추정
    named = [f for f in FRIENDS if f in blob]
    if len(named) == 1:
        score += 25; why.append(f"단일 캐릭터({named[0]})")
    elif len(named) > 1:
        score -= 10; why.append(f"여러 캐릭터 혼재({', '.join(named)})")

    # 감정 표현 다양성
    hits = [w for w in EMOTION_WORDS if w in blob]
    if hits:
        score += 5 * len(hits); why.append(f"감정/리액션 태그({', '.join(hits[:3])})")

    # 움직이는 스티커는 정적 이미지로 쓰기 어렵다
    if asset.get("animated"):
        score -= 15; why.append("애니메이션(정적 배치에 불리)")

    # 시즌성·유아 톤 감점
    bad = [w for w in NEGATIVE_WORDS if w in blob]
    if bad:
        score -= 12 * len(bad); why.append(f"톤 불일치({', '.join(bad[:2])})")

    if asset.get("type") != "STICKER":
        score -= 40; why.append(f"스티커 아님({asset.get('type')})")

    return score, why


def cmd_list(args) -> int:
    print(f"🔑 키 출처: {key_source() or '없음'}")
    assets = fetch_catalog(force=args.refresh)
    print(f"📦 카탈로그 {len(assets)}건 (캐시: data/ogq_catalog.json)\n")

    ranked = sorted(((score_asset(a), a) for a in assets),
                    key=lambda x: -x[0][0])

    print(f"{'점수':>4}  {'assetId':<16} {'낱장':>4}  제목 / 선정 근거")
    print("-" * 100)
    for (score, why), a in ranked[:args.top]:
        title = (a.get("title") or "")[:40]
        print(f"{score:>4}  {a.get('assetId',''):<16} {'?':>4}  {title}")
        print(f"{'':>4}  {'':<16} {'':>4}  └ {' · '.join(why) or '특이사항 없음'}")
        print(f"{'':>4}  {'':<16} {'':>4}    태그: {', '.join((a.get('tags') or [])[:8])}")
        print(f"{'':>4}  {'':<16} {'':>4}    썸네일: {a.get('thumbnailUrl','')}")
    print("\n다음 단계:  python3 scripts/fetch_mascot.py --show <assetId>")
    return 0


def cmd_show(args) -> int:
    detail = get_asset(args.show)
    asset = detail.get("asset") or {}
    images = detail.get("images") or []
    print(f"🎨 {asset.get('title')}  ({asset.get('assetId')})")
    print(f"   태그: {', '.join(asset.get('tags') or [])}")
    print(f"   카테고리: {', '.join((c.get('krName') or '') for c in asset.get('categories') or [])}")
    print(f"   크리에이터: {(asset.get('creator') or {}).get('nickname')}")
    print(f"   낱장 {len(images)}장\n")
    for img in images:
        print(f"   - {img.get('name','?'):<10} {img.get('imageUrl','')}")
    print("\n다음 단계:  python3 scripts/fetch_mascot.py --download "
          f"{asset.get('assetId')} --map welcome=1.png,celebrate=2.png")
    return 0


def cmd_download(args) -> int:
    asset_id = args.download
    detail = get_asset(asset_id)
    asset = detail.get("asset") or {}

    print(f"⬇️  {asset.get('title')} ({asset_id}) 내려받는 중...")
    issued = issue_download(asset_id)
    files = issued.get("files") or []
    if not files:
        print("❌ 발급된 파일이 없습니다.")
        return 1
    print(f"   토큰 발급 완료 · 파일 {len(files)}개 · 만료 {issued.get('expiresAt')}")
    print("   (토큰은 약 5분 뒤 만료되므로 바로 저장합니다)")

    out_dir = os.path.join(MASCOT_DIR, asset_id)
    saved = []
    for f in files:
        name = f.get("name") or f.get("fileId")
        dest = os.path.join(out_dir, name)
        try:
            download_to(f["downloadUrl"], dest)
            saved.append(name)
            print(f"   ✅ {name}")
        except OGQError as exc:
            print(f"   ❌ {name}: {exc}")

    # 감정 슬롯 매핑
    slot_map = {}
    if args.map:
        for pair in args.map.split(","):
            if "=" in pair:
                slot, filename = pair.split("=", 1)
                slot_map[slot.strip()] = filename.strip()

    manifest = {
        "assetId": asset_id,
        "title": asset.get("title"),
        "creator": (asset.get("creator") or {}).get("nickname"),
        "tags": asset.get("tags") or [],
        "thumbnailUrl": asset.get("thumbnailUrl"),
        "dir": os.path.relpath(out_dir, os.path.dirname(MASCOT_DIR)),
        "files": saved,
        "slots": slot_map,
        "source": "NAVER OGQ마켓 공모전 API",
    }
    os.makedirs(MASCOT_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=2)

    print(f"\n📁 저장: {out_dir}  ({len(saved)}개)")
    print(f"📝 매니페스트: {MANIFEST_PATH}")
    if not slot_map:
        print("\n⚠️  감정 슬롯 매핑이 비어 있습니다. 앱은 첫 번째 파일을 기본으로 씁니다.")
        print("   슬롯을 지정하려면 manifest.json 의 \"slots\" 를 직접 편집하거나")
        print("   --map welcome=1.png,celebrate=7.png,cheer=3.png 형태로 다시 실행하세요.")
        print("   앱이 쓰는 슬롯 이름: welcome, celebrate, cheer, comfort, thinking")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OGQ 마스코트 선정·다운로드")
    parser.add_argument("--list", action="store_true", help="카탈로그 조회 + 후보 점수화")
    parser.add_argument("--show", metavar="ASSET_ID", help="자산 상세(낱장 목록)")
    parser.add_argument("--download", metavar="ASSET_ID", help="낱장 전체 다운로드")
    parser.add_argument("--map", help="감정 슬롯 매핑 (welcome=1.png,celebrate=7.png)")
    parser.add_argument("--top", type=int, default=12, help="--list 출력 개수")
    parser.add_argument("--refresh", action="store_true", help="카탈로그 캐시 무시하고 새로 조회")
    args = parser.parse_args()

    if not has_api_key():
        print("❌ OGQ_API_KEY 를 찾지 못했습니다.")
        print("   다음 중 한 곳에 넣으세요:")
        print("     .streamlit/secrets.toml →  OGQ_API_KEY = \"키\"")
        print("     .env                    →  OGQ_API_KEY=키")
        print("     환경변수                →  export OGQ_API_KEY=키")
        return 1

    if not ping():
        print("⚠️  서버에 닿지 못했습니다 (/ping 실패).")
        print("   방화벽·프록시로 4th-ai-ogq.competition.ogq.me 가 막혀 있는지 확인하세요.")
        return 1

    try:
        if args.list:
            return cmd_list(args)
        if args.show:
            return cmd_show(args)
        if args.download:
            return cmd_download(args)
    except OGQError as exc:
        print(f"❌ {exc}")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
