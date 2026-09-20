# -*- coding: utf-8 -*-
"""Phase 6 모바일 QA — 브라우저에서 실제로 측정한다."""
import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8501/"
OUT = "/tmp/claude-0/-home-user-EMP-AI-JOB-PASS-Finder/669256b0-90c9-52a9-8a52-b2d435ad48c8/scratchpad"

# 실측 스크립트 — 화면마다 동일하게 돌린다
PROBE = """() => {
  const vw = window.innerWidth;
  const r = { vw,
    scrollWidth: document.documentElement.scrollWidth,
    hOverflow: document.documentElement.scrollWidth - vw,
    overflowing: [], smallTargets: [], smallInputs: [], tinyText: [] };

  // 뷰포트 오른쪽을 넘어가는 요소 (가로 스크롤 유발)
  for (const el of document.querySelectorAll('body *')) {
    const b = el.getBoundingClientRect();
    if (b.width === 0 || b.height === 0) continue;
    const st = getComputedStyle(el);
    if (st.overflowX === 'auto' || st.overflowX === 'scroll') continue;   // 의도적 가로 스크롤 영역
    if (b.right > vw + 1.5 && !el.closest('[class*="st-key-mjp_navbar"],[class*="st-key-mjp_row"]')) {
      r.overflowing.push({ tag: el.tagName, cls: (el.className+'').slice(0,42),
                           right: Math.round(b.right), text: (el.innerText||'').slice(0,28) });
    }
  }
  // 터치 타깃 (버튼)
  for (const el of document.querySelectorAll('button')) {
    const b = el.getBoundingClientRect();
    // Streamlit 개발 툴바(Deploy/메인메뉴)와 툴팁 아이콘은 배포본 사용자 동작이 아님
    const tid = el.getAttribute('data-testid')||'';
    // Streamlit 개발 툴바 — 배포본 사용자에게 보이지 않음
    if (tid.startsWith('stBaseButton-header') || tid === 'stMainMenuButton') continue;
    if (el.closest('[data-testid="stTooltipHoverTarget"]')) continue;
    // 컨트롤 내부 서브요소(드롭다운 화살표, 비밀번호 표시 토글)는 독립 탭 타깃이
    // 아니다 — 컨트롤 아무 곳이나 누르면 동작한다. 감싸는 컨트롤이 44px 이상이면
    // 실제 터치에는 문제가 없으므로 그 경우만 통과시킨다.
    const ctrl = el.closest('[data-testid="stSelectbox"],[data-testid="stMultiSelect"],'
                          + '[data-testid="stTextInputRootElement"],[data-baseweb="select"]');
    if (ctrl && ctrl.getBoundingClientRect().height >= 44) continue;
    if (b.height > 0 && b.height < 44) r.smallTargets.push({ h: Math.round(b.height),
        tid, t: (el.innerText||'').slice(0,24) });
  }
  // 입력창 폰트 (16px 미만이면 iOS 사파리가 자동 확대)
  for (const el of document.querySelectorAll('input, textarea, select')) {
    const fs = parseFloat(getComputedStyle(el).fontSize);
    const b = el.getBoundingClientRect();
    if (b.height > 0 && fs < 16) r.smallInputs.push({ fs, type: el.tagName });
  }
  // 본문 가독성 (11px 미만 텍스트)
  for (const el of document.querySelectorAll('p,div,span,label,li')) {
    if (el.children.length) continue;
    const t = (el.innerText||'').trim(); if (t.length < 4) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 11) r.tinyText.push({ fs, t: t.slice(0,26) });
  }
  r.overflowing = r.overflowing.slice(0,6);
  r.smallTargets = r.smallTargets.slice(0,6);
  r.tinyText = r.tinyText.slice(0,5);
  return r;
}"""

async def probe(pg, name, results, shot=True):
    await pg.wait_for_timeout(1600)
    data = await pg.evaluate(PROBE)
    data["screen"] = name
    results.append(data)
    if shot:
        await pg.screenshot(path=f"{OUT}/qa_{name}.png", full_page=True)
    return data

async def run(device, vw, vh, mobile):
    results = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        ctx = await b.new_context(viewport={"width":vw,"height":vh}, device_scale_factor=2,
                                  is_mobile=mobile, has_touch=mobile)
        pg = await ctx.new_page()

        await pg.goto(URL, wait_until="networkidle"); await pg.wait_for_timeout(2600)
        await probe(pg, f"{device}_1_landing", results)

        await pg.get_by_role("button", name="시작하기").first.click(); await pg.wait_for_timeout(2200)
        await probe(pg, f"{device}_2_login", results)

        await pg.get_by_role("button", name="게스트모드로 바로 시작하기").first.click()
        await pg.wait_for_timeout(3000)
        await pg.get_by_role("button", name="학생이에요 선택").first.click()
        await pg.wait_for_timeout(3200)
        await probe(pg, f"{device}_3_hub", results)

        for label, key in [("스펙 진단","4_spec"), ("기업 탐색","5_explore"),
                           ("가이드","6_guide"), ("자소서","7_resume"),
                           ("로드맵","8_next"), ("마이페이지","9_mypage")]:
            await pg.get_by_role("button", name=label, exact=True).first.click()
            await pg.wait_for_timeout(2800)
            await probe(pg, f"{device}_{key}", results)

        await ctx.close(); await b.close()
    return results

async def main():
    allr = []
    allr += await run("mobile", 390, 844, True)
    allr += await run("desktop", 1440, 950, False)
    json.dump(allr, open(f"{OUT}/qa_results.json","w"), ensure_ascii=False, indent=2)

    print(f"{'화면':<22} {'가로넘침':>8} {'넘친요소':>8} {'작은버튼':>8} {'작은입력':>8} {'작은글씨':>8}")
    print("-"*72)
    fails = 0
    for r in allr:
        mob = r["screen"].startswith("mobile")
        # 44px 터치 타깃과 16px 입력(iOS 자동확대)은 **모바일 기준**이다.
        # 마우스로 쓰는 데스크톱에 같은 잣대를 대면 잘못된 실패가 나온다.
        bad = (r["hOverflow"] > 2) or r["overflowing"] or (mob and (r["smallTargets"] or r["smallInputs"]))
        fails += 1 if bad else 0
        mark = "" if not bad else "  <-- 확인"
        print(f"{r['screen']:<22} {r['hOverflow']:>8} {len(r['overflowing']):>8} "
              f"{len(r['smallTargets']):>8} {len(r['smallInputs']):>8} {len(r['tinyText']):>8}{mark}")
    print(f"\n문제 있는 화면: {fails} / {len(allr)}")
    for r in allr:
        if r["overflowing"] or r["smallTargets"] or r["smallInputs"]:
            print(f"\n[{r['screen']}]")
            for o in r["overflowing"]:   print(f"   넘침: {o['tag']}.{o['cls']} right={o['right']} (vw={r['vw']}) '{o['text']}'")
            for t in r["smallTargets"]:  print(f"   작은버튼 {t['h']}px: {t['t']}")
            for i in r["smallInputs"]:   print(f"   입력 폰트 {i['fs']}px: {i['type']}")
asyncio.run(main())
