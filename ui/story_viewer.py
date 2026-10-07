# -*- coding: utf-8 -*-
"""
ui/story_viewer.py
인스타그램 스토리형 기업 카드 뷰어 (st.components.v1.html · 순수 JS, 외부 라이브러리 없음)

조작 (모바일 터치 우선)
  · 상단 진행 바 — 카드 수만큼 나뉘고, 5초마다 다음 카드로 넘어간다
  · 화면 왼쪽 1/3 탭 → 이전 카드 / 오른쪽 2/3 탭 → 다음 카드
  · 누르고 있으면 일시정지, 떼면 재개 (탭과 길게 누르기는 누른 시간으로 구분)
  · 마지막 카드가 끝나면 '다음 기업 보기' 안내를 띄운다

▣ 왜 '다음 기업'을 뷰어 안이 아니라 아래 Streamlit 버튼으로 하는가
   components.html 은 iframe 안에서 돈다. 값이 Streamlit 쪽으로 돌아오지 않으므로
   (단방향) 기업 넘기기·반응 기록은 아래 버튼이 맡고, 뷰어는 안내만 한다.

▣ 보안
   기업명·요약문은 데이터에서 온다. HTML 문자열에 끼우지 않고 JSON 으로 넘긴 뒤
   textContent 로만 넣는다 — 데이터에 태그가 섞여도 실행되지 않는다.
"""

import json

import streamlit.components.v1 as components

# 카드마다 다른 그라데이션 (카드 수가 더 많으면 순환)
GRADIENTS = [
    "linear-gradient(160deg, #1E3A8A 0%, #4C8FE0 100%)",
    "linear-gradient(160deg, #134E4A 0%, #34D399 100%)",
    "linear-gradient(160deg, #4C1D95 0%, #A78BFA 100%)",
    "linear-gradient(160deg, #7C2D12 0%, #FB923C 100%)",
    "linear-gradient(160deg, #0A0E17 0%, #2B6BC4 100%)",
]

SECONDS_PER_CARD = 5
VIEWER_HEIGHT = 600   # iframe 높이. 카드 폭은 높이 × 9/16 (폰 세로 비율)

_TEMPLATE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; background: transparent; overflow: hidden; }
  body { display: flex; justify-content: center; align-items: center;
         font-family: "Pretendard Variable", Pretendard, -apple-system, "Apple SD Gothic Neo",
                      "Malgun Gothic", "Noto Sans KR", sans-serif; }
  #story { position: relative; height: 100%; aspect-ratio: 9 / 16; max-width: 100%;
           border-radius: 18px; overflow: hidden; color: #fff;
           user-select: none; -webkit-user-select: none; -webkit-touch-callout: none;
           touch-action: manipulation; cursor: pointer;
           box-shadow: 0 10px 30px rgba(0,0,0,.35); transition: background .35s ease; }
  #bars { position: absolute; top: 12px; left: 12px; right: 12px; display: flex; gap: 4px; z-index: 3; }
  .bar { flex: 1; height: 3px; border-radius: 3px; background: rgba(255,255,255,.35); overflow: hidden; }
  .fill { height: 100%; width: 0; background: #fff; }
  #head { position: absolute; top: 24px; left: 14px; right: 14px; z-index: 3;
          display: flex; justify-content: space-between; align-items: center;
          font-size: 13px; font-weight: 700; text-shadow: 0 1px 2px rgba(0,0,0,.35); }
  #paused { opacity: 0; transition: opacity .15s; font-size: 12px;
            background: rgba(0,0,0,.35); padding: 2px 8px; border-radius: 999px; }
  #card { position: absolute; inset: 0; display: flex; flex-direction: column;
          justify-content: center; align-items: center; text-align: center; padding: 64px 26px 40px; }
  #emoji { font-size: 76px; line-height: 1; margin-bottom: 22px;
           filter: drop-shadow(0 6px 12px rgba(0,0,0,.25)); }
  #title { font-size: 26px; font-weight: 800; letter-spacing: -.02em; line-height: 1.3;
           word-break: keep-all; }
  #body { margin-top: 14px; font-size: 17px; line-height: 1.6; font-weight: 500;
          opacity: .95; word-break: keep-all; max-width: 19em; }
  #score { margin-top: 18px; font-size: 64px; font-weight: 900; letter-spacing: -.03em; display: none; }
  #score small { font-size: 20px; font-weight: 700; opacity: .8; margin-left: 4px; }
  #hint { position: absolute; bottom: 14px; left: 0; right: 0; text-align: center;
          font-size: 12px; opacity: .75; }
  #end { position: absolute; inset: 0; z-index: 4; display: none; flex-direction: column;
         justify-content: center; align-items: center; text-align: center; gap: 12px;
         background: rgba(10,14,23,.78); padding: 24px; }
  #end b { font-size: 22px; }
  #end span { font-size: 15px; opacity: .9; line-height: 1.6; word-break: keep-all; }
  #end .arrow { font-size: 34px; animation: bob 1.2s ease-in-out infinite; }
  @keyframes bob { 50% { transform: translateY(6px); } }
  @media (prefers-reduced-motion: reduce) { #end .arrow { animation: none; } #story { transition: none; } }
</style></head>
<body>
<div id="story" role="region" aria-label="기업 스토리">
  <div id="bars"></div>
  <div id="head"><span id="company"></span><span id="paused">일시정지</span></div>
  <div id="card">
    <div id="emoji"></div>
    <div id="title"></div>
    <div id="body"></div>
    <div id="score"></div>
  </div>
  <div id="hint">왼쪽 탭: 이전 · 오른쪽 탭: 다음 · 꾹 누르면 멈춤</div>
  <div id="end">
    <b>다음 기업 보기</b>
    <span>아래 버튼으로 ❤️ 관심 또는 👎 패스를 누르면<br>다음 기업 스토리가 시작돼요.</span>
    <div class="arrow">👇</div>
  </div>
</div>
<script>
(function () {
  const DATA = __DATA__;
  const cards = DATA.cards, gradients = DATA.gradients, DURATION = DATA.seconds * 1000;
  const HOLD_MS = 220;   // 이보다 오래 누르면 '길게 누르기'(일시정지)로 본다

  const story = document.getElementById("story");
  const bars = document.getElementById("bars");
  const fills = cards.map(() => {
    const bar = document.createElement("div"); bar.className = "bar";
    const fill = document.createElement("div"); fill.className = "fill";
    bar.appendChild(fill); bars.appendChild(bar); return fill;
  });
  document.getElementById("company").textContent = DATA.company;

  let index = 0, elapsed = 0, last = null, paused = false, ended = false;

  function show(i) {
    index = Math.max(0, Math.min(i, cards.length - 1));
    elapsed = 0; ended = false;
    document.getElementById("end").style.display = "none";
    const c = cards[index];
    story.style.background = gradients[index % gradients.length];
    document.getElementById("emoji").textContent = c.emoji || "";
    document.getElementById("title").textContent = c.title || "";
    document.getElementById("body").textContent = c.body || "";
    const score = document.getElementById("score");
    if (typeof c.score === "number") {
      score.textContent = Math.round(c.score);
      const unit = document.createElement("small"); unit.textContent = "점";
      score.appendChild(unit); score.style.display = "block";
    } else {
      score.style.display = "none";
    }
    fills.forEach((f, k) => { f.style.width = k < index ? "100%" : "0%"; });
  }

  function finish() {
    ended = true;
    fills[index].style.width = "100%";
    document.getElementById("end").style.display = "flex";
  }

  function next() { if (index < cards.length - 1) show(index + 1); else finish(); }
  function prev() { show(index - 1); }

  function tick(now) {
    if (last === null) last = now;
    const dt = now - last; last = now;
    if (!paused && !ended) {
      elapsed += dt;
      fills[index].style.width = Math.min(100, elapsed / DURATION * 100) + "%";
      if (elapsed >= DURATION) next();
    }
    requestAnimationFrame(tick);
  }

  function setPaused(p) {
    paused = p;
    document.getElementById("paused").style.opacity = p ? 1 : 0;
  }

  let downAt = 0, downX = 0;
  story.addEventListener("pointerdown", (e) => {
    downAt = performance.now(); downX = e.clientX; setPaused(true);
  });
  story.addEventListener("pointerup", () => {
    const held = performance.now() - downAt;
    setPaused(false);
    if (held >= HOLD_MS) return;                 // 길게 눌렀다 뗀 것 → 재개만
    const rect = story.getBoundingClientRect();
    if (downX - rect.left < rect.width / 3) prev(); else if (!ended) next();
  });
  story.addEventListener("pointercancel", () => setPaused(false));
  story.addEventListener("pointerleave", () => { if (paused) setPaused(false); });
  story.addEventListener("contextmenu", (e) => e.preventDefault());

  // 화면 밖(다른 탭)으로 나가면 멈춘다 — 돌아왔을 때 카드가 몇 장 건너뛰어 있지 않게
  document.addEventListener("visibilitychange", () => { last = null; setPaused(document.hidden); });

  show(0);
  requestAnimationFrame(tick);
})();
</script>
</body></html>"""


def render_story(company_name: str, cards: list[dict], height: int = VIEWER_HEIGHT) -> None:
    """카드 목록을 스토리 뷰어로 그린다. 기업이 바뀌면 HTML 이 달라져 처음 카드부터 다시 시작한다."""
    data = {
        "company": company_name,
        "cards": [
            {"title": c.get("title", ""), "body": c.get("body", ""),
             "emoji": c.get("emoji", ""), "score": c.get("score")}
            for c in cards
        ],
        "gradients": GRADIENTS,
        "seconds": SECONDS_PER_CARD,
    }
    # </script> 가 데이터에 섞여도 스크립트 블록이 닫히지 않도록 '<' 를 이스케이프한다
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    components.html(_TEMPLATE.replace("__DATA__", blob), height=height, scrolling=False)
