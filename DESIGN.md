---
name: AI Job Pass Finder
description: 마이스터고 학생의 스펙을 '발급되는 자격 문서'로 다루는 취업 준비 앱 — 국가기술자격증 수첩의 표지와 양식
colors:
  cover-navy: "#14284A"
  cover-navy-hover: "#1C3663"
  brand-ink: "#1F4E8C"
  gold-foil: "#C8A55E"
  foil-highlight: "#EAD6A0"
  foil-shade: "#A8843C"
  cover-text: "#E8EDF5"
  cover-muted: "#A9B6CB"
  seal-vermilion: "#B93A26"
  seal-on-cover: "#E86A52"
  date-stamp-violet: "#51438A"
  pass-green: "#1D7447"
  ochre-ink: "#8A5A00"
  info-blue: "#2A5DB0"
  security-paper: "#EDF1EF"
  paper-deep: "#E3E9E6"
  form-sheet: "#FFFFFF"
  rule-line: "#C6D0CC"
  ink: "#18212D"
  ink-muted: "#55606B"
typography:
  display:
    fontFamily: "Nanum Myeongjo, Noto Serif KR, AppleMyungjo, Batang, serif"
    fontSize: "clamp(34px, 5.2vw, 54px)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "0.02em"
  headline:
    fontFamily: "Nanum Myeongjo, Noto Serif KR, AppleMyungjo, Batang, serif"
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  title-serif:
    fontFamily: "Nanum Myeongjo, Noto Serif KR, AppleMyungjo, Batang, serif"
    fontSize: "20px"
    fontWeight: 800
    letterSpacing: "0.04em"
  title:
    fontFamily: "Pretendard Variable, Pretendard, Noto Sans KR, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 800
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Pretendard Variable, Pretendard, Noto Sans KR, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.7
    fontFeature: "tnum"
  body-small:
    fontFamily: "Pretendard Variable, Pretendard, Noto Sans KR, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Pretendard Variable, Pretendard, Noto Sans KR, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 700
  caption:
    fontFamily: "Pretendard Variable, Pretendard, Noto Sans KR, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
  stamp-numeral:
    fontFamily: "Pretendard Variable, Pretendard, Noto Sans KR, system-ui, sans-serif"
    fontSize: "42px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "tnum"
  serial:
    fontFamily: "ui-monospace, SF Mono, Roboto Mono, Menlo, Consolas, monospace"
    fontWeight: 700
    letterSpacing: "0.12em"
rounded:
  rule: "2px"
  stamp: "3px"
  form: "4px"
  seal: "50%"
spacing:
  s1: "8px"
  s2: "16px"
  s3: "32px"
  s4: "56px"
components:
  button-primary:
    backgroundColor: "{colors.cover-navy}"
    textColor: "{colors.form-sheet}"
    rounded: "{rounded.form}"
    typography: "{typography.label}"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.cover-navy-hover}"
    textColor: "{colors.form-sheet}"
  button-secondary:
    backgroundColor: "{colors.form-sheet}"
    textColor: "{colors.cover-navy}"
    rounded: "{rounded.form}"
    typography: "{typography.label}"
    height: "44px"
  button-back:
    backgroundColor: "transparent"
    textColor: "{colors.brand-ink}"
  nav-tab:
    backgroundColor: "{colors.form-sheet}"
    textColor: "{colors.ink}"
    rounded: "3px 3px 0 0"
    height: "44px"
  nav-tab-active:
    backgroundColor: "{colors.cover-navy}"
    textColor: "{colors.form-sheet}"
  input:
    backgroundColor: "{colors.form-sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.form}"
    typography: "{typography.body}"
    height: "44px"
  form-sheet-card:
    backgroundColor: "{colors.form-sheet}"
    rounded: "{rounded.form}"
    padding: "20px 22px"
  stamp-badge:
    backgroundColor: "{colors.pass-green}"
    textColor: "{colors.form-sheet}"
    rounded: "{rounded.stamp}"
    padding: "3px 9px"
  tag:
    backgroundColor: "{colors.security-paper}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.stamp}"
    padding: "2px 8px"
  cover:
    backgroundColor: "{colors.cover-navy}"
    textColor: "{colors.cover-text}"
    rounded: "{rounded.form}"
    padding: "72px 28px 80px"
  topbar:
    backgroundColor: "{colors.cover-navy}"
    textColor: "{colors.cover-text}"
    padding: "12px 18px"
  score-stamp:
    textColor: "{colors.seal-vermilion}"
    rounded: "{rounded.seal}"
    size: "124px"
---

# Design System: AI Job Pass Finder

## Overview

**Creative North Star: "국가기술자격증 수첩"**

마이스터고 학생이 가장 잘 아는 문서는 자격증 수첩이다. 이 앱은 학생의 스펙을 그 문서처럼 다룬다. 앱의 정체성은 짙은 네이비 수첩 표지와 금박 엠블럼이 지고, 본문은 차가운 민트그레이 보안용지 위에 놓인 흰 양식지다. 점수와 판정은 인주 도장처럼 '찍힌다'. 채용 포털의 흰 카드 + 파란 버튼, 그리고 이전 빌드의 다크 네이비 + 네온 글로우 AI 룩은 이 세계에서 쓰지 않는다.

밝은 바탕은 교실·실습실 형광등 아래 폰으로 보는 화면이라서 고른 것이다. 어두운 화면은 반사광에 묻힌다. 밀도는 공문서 양식 수준으로 중간: 1px 괘선으로 칸을 나누고, 필드 라벨 칸(항목 | 내용)으로 정보를 정리하며, 숫자는 전부 등폭으로 자리를 지킨다. 장식은 문서가 원래 가진 재료(길로셰 보안 무늬, 겹괘선, 금박, 도장)에서만 가져온다.

모션은 도장이 찍히는 순간 한 번뿐이다. 나머지 상태 변화는 160ms 안에 조용히 끝난다.

**Key Characteristics:**
- 표지(네이비 + 금박)와 속지(보안용지 + 흰 양식지)의 두 층 구조
- 1px 괘선 격자, 직각에 가까운 4px 모서리
- 명조 제목 + Pretendard 본문, 모든 숫자는 tabular-nums
- 판정은 원형 겹테두리 도장으로 찍히고, 색은 판정 구간을 따른다
- 그림자는 종이가 바닥에 놓인 정도(1px)까지만

## Colors

수첩 표지의 네이비와 금박, 인주·일부인 같은 문서 잉크, 그리고 서늘한 보안용지 중성색으로 이루어진 팔레트.

### Primary
- **표지 네이비 (cover-navy)**: 정체성과 행동의 색. 상단 표지 띠, 랜딩 표지, 주 버튼, 선택된 목차 탭, 진단서 상단 6px 띠, 점수 막대 채움, 선택된 칩. 주 버튼 호버는 한 톤 밝은 cover-navy-hover.
- **브랜드 잉크 (brand-ink)**: 본문 위에서 네이비를 대신하는 한 단계 밝은 잉크. 링크, 제목 옆 라인 아이콘, 포커스 링, 뒤로가기 링크 버튼.

### Secondary
- **금박 (gold-foil)**: 표지 위에서만 쓴다. 랜딩 표지 제목, 표지 띠 아래 3px 금선, 브랜드 서브라인, 길로셰 무늬, 표지 겹테두리. 엠블럼은 foil-highlight → gold-foil → foil-shade 세 잉크의 그라디언트로 금박을 흉내 낸다. 텍스트 선택 색도 금박(38% 투명도)이다.

### Tertiary (문서 잉크 · 상태)
- **인주 주홍 (seal-vermilion)**: 도장의 기본 잉크. 낮은 점수 판정, 경고·오류.
- **표지 위 인주 (seal-on-cover)**: 네이비 표지 위에서는 seal-vermilion이 묻히므로 한 단계 밝힌 주홍. 랜딩 표지 모서리의 '본선 진출' 인장 전용.
- **합격 녹색 (pass-green)**: 상태 시맨틱 전용. LIVE 배지, 합격 안정권 도장. 흰 글씨 5.9:1.
- **황토 잉크 (ochre-ink)**: 도전권 도장, BACKUP 배지, 별점.
- **일부인 보라 (date-stamp-violet)**: 날짜 도장 잉크. 면접 질문 번호(Q1.) 같은 일련 표기.
- **정보 파랑 (info-blue)**: 출처 표시 배지(Q-NET).

### Neutral
- **보안용지 (security-paper)**: 앱 바탕. 양식 표의 라벨 칸, 진단서 머리칸, 태그 바탕, 비고란 바탕.
- **짙은 용지 (paper-deep)**: 검색·필터 '조건 기입란'과 목차 탭 줄의 바탕.
- **양식지 (form-sheet)**: 카드·입력·탭·펼침 구획 등 모든 기입 표면.
- **괘선 (rule-line)**: 1px 테두리, 구획선, 눈금, 스크롤바.
- **먹 (ink)**: 본문과 제목. 양식 표 외곽선과 제목 아래 겹괘선도 먹으로 긋는다.
- **보조 글씨 (ink-muted)**: 설명, 캡션, 양식 표의 내용 칸. 용지 위 5.8:1.
- **표지 글씨 (cover-text / cover-muted)**: 네이비 위 본문과 보조 글씨(7:1).

### Named Rules
**The Two Layers Rule.** 네이비와 금박은 '표지'다. 표지 띠·랜딩 표지·주 행동에만 쓰고, 속지(본문)를 네이비로 칠하지 않는다. 금박은 네이비 위에서만 읽힌다.

**The Semantic Green Rule.** 녹색은 브랜드 색이 아니다. LIVE 상태와 합격 안정권에만 쓴다.

**The Ink Follows Verdict Rule.** 도장의 잉크는 판정 구간을 따른다: 안정권 pass-green, 도전권 ochre-ink, 보완 필요 seal-vermilion. 판정 문구도 같은 잉크로 쓴다.

## Typography

**Display Font:** Nanum Myeongjo (with Noto Serif KR, AppleMyungjo, Batang)
**Body Font:** Pretendard Variable (with Noto Sans KR, 시스템 산세리프)
**Label/Mono Font:** ui-monospace 계열 (발급번호·이어하기 코드·반 코드 전용)

**Character:** 명조는 자격증·공문서 제목의 서체이고, Pretendard는 기입 내용의 서체다. 문서 이름에는 명조, 그 문서에 적힌 값에는 고딕.

### Hierarchy
- **Display** (800, clamp(34px–54px), 1.15, +0.02em, 금박색): 랜딩 표지의 서비스명 한 곳. 모바일 34px, 380px 이하 26px.
- **Headline** (800, 26px, 1.3, 명조): 화면 제목. 아래 3px 겹괘선(먹)과 함께 쓴다. 모바일에서는 20px.
- **Title-serif** (800, 20px, +0.04em, 명조): 문서명 칸. 진단서 머리칸의 '합격 지수 진단서'.
- **Title** (800, 20px, −0.02em, Pretendard): 양식 구획 제목(마크다운 h3/h4, 아래 1px 괘선), 허브 단계 제목, 판정 문구.
- **Body** (400, 16px, 1.7): 본문. 입력 글자도 16px(iOS 확대 방지). 설명 문단은 60–66ch.
- **Body-small / Label** (14px; 본문 400, 라벨 700): 설명 칸, 위젯 라벨, 버튼 글씨, 양식 표.
- **Caption** (13px, 1.6): 캡션, 배지, 태그, 비고란.
- **Stamp numeral** (900, 42px, 1, −0.03em): 도장 안 점수 하나에만. 모바일 34px.
- **Serial** (mono 700, +0.12em): 코드·번호 같은 발급번호형 값.

### Named Rules
**The Six Sizes Rule.** 크기는 34 / 26 / 20 / 16 / 14 / 13px 여섯 단(`--mjp-display`…`--mjp-caption`)만 쓴다. 예외는 표지 제목의 clamp와 도장 숫자 42px뿐이다.

**The Tabular Rule.** 앱 전체가 tabular-nums다. 점수·통계·코드가 자리마다 흔들리지 않는다.

**The Keep-All Rule.** 한글은 어절 단위로 줄을 바꾼다(`word-break: keep-all`). 제목과 표지 문구는 `text-wrap: balance`.

## Layout

본문 폭은 최대 1120px 단일 열이고, 그 위에 상단 표지 띠 + 목차 탭 줄이 문서 머리처럼 붙는다(사이드바 없음). 여백은 8 / 16 / 32 / 56px 네 단: 구획 사이 56px, 제목 블록 아래와 구분선 아래 32px, 카드 사이 16px. 양식 표는 `180px | 1fr` 두 칸(항목 | 내용) 격자다.

768px 이하에서 모든 다단(st.columns)은 1단으로 접히고 여백은 한 단씩 줄어든다(56→32, 32→16). 예외는 두 가지: 목차 탭 줄은 가로 스크롤을 유지하고, 카드 하단의 짧은 버튼 줄은 가로를 유지한다. 양식 표는 모바일에서 라벨 칸이 내용 위로 쌓인다. 카드 목록은 행 단위로 컬럼을 만들어 1단으로 접혀도 순서가 보존된다. 모든 터치 타깃은 44px 이상, 모바일 버튼은 48px.

## Elevation & Depth

거의 평평하다. 종이는 뜨지 않는다. 깊이는 표지/속지의 색 대비와 괘선으로 나타내고, 그림자는 양식지가 바닥에 놓인 정도의 1px 선(shadow-1)이 기본이다. 호버 시에만 한 단계(shadow-2) 올라간다. 표지의 입체감은 바깥 그림자가 아니라 inset 겹테두리(금박 1px + 네이비 간격 + 금박 1px)로 만든다. 도장은 `mix-blend-mode: multiply`로 종이에 스며든다.

### Shadow Vocabulary
- **놓인 종이** (`box-shadow: 0 1px 0 rgba(20,40,74,0.06)`): 카드의 기본 상태.
- **들린 종이** (`box-shadow: 0 2px 6px rgba(20,40,74,0.10), 0 1px 0 rgba(20,40,74,0.06)`): 카드·기능 카드 호버.
- **포커스 번짐** (`box-shadow: 0 0 0 3px rgba(31,78,140,0.16)`): 입력칸 포커스.

### Named Rules
**The Paper Doesn't Float Rule.** 쉬는 상태의 표면은 1px 그림자를 넘지 않는다. 더 깊은 그림자는 호버에만, 그리고 shadow-2까지만.

## Shapes

직각에 가까운 양식의 모서리. 표면(카드·입력·버튼·표지·펼침 구획·안내 상자)은 4px, 배지·태그·선택 칩·탭 윗모서리는 3px 도장 테두리, 양식 표와 눈금 막대는 2px. 둥근 알약(pill)은 쓰지 않는다. 원은 도장·인장·허브 단계 번호에만 쓴다. 선은 1px 괘선이 기본이고, 화면 제목 아래와 랜딩 바닥글 위에는 3px 겹괘선(double), 비고란과 '나중에' 칸은 1px 점선이다. 도장은 −7°, 표지 인장은 +12° 기울어 찍힌다.

## Components

### Buttons
문서에 찍는 행동. 단단하고 짧다.
- **Shape:** 4px 모서리, 최소 높이 44px(모바일 48px), 14px 800 굵기.
- **Primary:** 표지 네이비 바탕 + 흰 글씨. 호버 시 cover-navy-hover.
- **Secondary:** 흰 양식지 바탕 + 네이비 1px 테두리 + 네이비 글씨, 호버 시 아주 옅은 청회색(#F2F5F8).
- **Active:** 누르면 1px 아래로 눌린다(`translateY(1px)`), 그림자는 사라진다.
- **Focus:** brand-ink 2px 외곽선, 2px 간격.
- **Back link:** 테두리 없는 brand-ink 글씨, 호버 시 밑줄. 주 동선이 아닌 '메인 허브로'.
- **Disabled:** 보안용지 바탕, #8C959E 글씨, 괘선 테두리.

### Chips (배지 · 태그)
- **도장 배지:** 13px 800, 3px 모서리, 의미색 바탕 + 흰 글씨. 출처 배지(LIVE API / BACKUP DATA / CURATED)는 pass-green / ochre-ink / ink-muted.
- **태그:** 보안용지 바탕 + 1px 괘선 + 보조 글씨, 3px.
- **선택된 칩(멀티셀렉트):** 네이비 바탕 + 흰 글씨, 3px — 양식에 기입한 값.

### Cards / Containers
- **Corner Style:** 4px.
- **Background:** 흰 양식지, 1px 괘선.
- **Shadow Strategy:** 놓인 종이 → 호버 시 들린 종이, 테두리는 #9FB0BE로 짙어진다(기능 카드는 네이비).
- **Internal Padding:** 20px 22px (모바일 15px).
- **변형:** 조건 기입란(paper-deep 바탕, 검색·필터), 비고란(점선 테두리 + '비고' 머리말, 예시 데이터·면책 문구), 안내 상자(info는 흰 칸 + 괘선으로 바꾸고 경고·오류는 의미색 유지).

### Inputs / Fields
- **Style:** 흰 바탕, 1px 괘선, 4px, 최소 44px, 글자 16px. 플레이스홀더 #6B7580.
- **Focus:** 테두리가 네이비로 바뀌고 3px 옅은 브랜드 잉크 번짐.
- **Label:** 14px 700 먹.

### Navigation
- **표지 띠:** 네이비 바탕, 윗모서리만 4px, 아래 3px 금박선. 왼쪽 금박 엠블럼(38px) + 서비스명(16px 800 흰색) + 팀명 서브라인, 오른쪽 사용자 이름. 모바일에서 서브라인과 사용자 메타는 숨긴다.
- **목차 탭:** 띠 바로 아래 paper-deep 줄에 흰 색인 탭(윗모서리 3px, 아래 테두리 없음)이 붙고, 줄 아래 2px 네이비선. 선택된 탭만 네이비로 채운다. st.tabs도 같은 규칙.

### 진단서 (Signature)
문서 양식 한 장. 위 6px 네이비 띠, 보안용지 머리칸(명조 문서명 + 기입 사항), 본문 칸에 점수 도장 + 판정. 도장은 124px 원(모바일 104px), 3px 테두리 + inset 겹테두리, −7° 기울기, multiply 합성, 판정 구간 잉크. 점수가 바뀔 때마다 한 번 찍힌다: 560ms `cubic-bezier(0.16, 1, 0.3, 1)`, 1.22배·−13°·흐림에서 1배·−7°로 내려앉는다. `prefers-reduced-motion`이면 정지.

### 눈금 막대
점수 막대는 자(ruler)다. 10px 높이, 1px 괘선 테두리, 2px 모서리, 10%마다 괘선 눈금, 네이비 채움.

### 표지 (랜딩)
네이비 표지 블록, 위아래 60px 길로셰 보안 무늬 띠(금박 0.5 투명도, 아래는 뒤집음), inset 금박 겹테두리, 중앙 금박 엠블럼 + 명조 금박 제목 + 표지 글씨 설명 + '발급 · …' 발급처 줄. 오른쪽 위에 표지 위 인주로 '본선 진출' 원형 인장(92px, +12°, 한 번 찍힘). 표지 아래 흰 양식 위에 주 버튼, 그 아래 항목 | 내용 양식 표.

### 공정 순서표 (허브)
흰 양식지 한 장 안에 번호 원(40px, 네이비 1.5px 테두리, 900 굵기) + 단계 제목 + 설명이 괘선으로 나뉘어 쌓인다. 실제 진행 순서가 있는 목록에만 번호를 쓴다.

## Do's and Don'ts

### Do:
- **Do** 새 화면 제목은 명조 26px + 3px 겹괘선 제목 블록(section_title)으로 연다.
- **Do** 정보를 나열할 때는 항목 | 내용 양식 표나 1px 괘선 구획으로 나눈다.
- **Do** 크기는 여섯 단, 여백은 8 / 16 / 32 / 56px 네 단 안에서 고른다.
- **Do** 판정·점수는 원형 도장으로, 판정 구간 잉크(pass-green / ochre-ink / seal-vermilion)로 찍는다.
- **Do** 코드·번호는 mono serial, 숫자는 tabular-nums로 둔다.
- **Do** 예시·백업·큐레이션 데이터는 도장 배지와 비고란으로 그렇다고 표기한다.
- **Do** 모든 터치 타깃 44px, 입력 글자 16px을 지킨다.

### Don't:
- **Don't** 금박을 흰 속지 위에 쓰지 않는다. 금박은 네이비 표지 위에서만 읽힌다.
- **Don't** 둥근 알약 배지나 8px 이상의 둥근 카드를 만들지 않는다. 표면 4px, 도장 테두리 3px.
- **Don't** 녹색을 브랜드·장식 색으로 쓰지 않는다.
- **Don't** 쉬는 상태의 표면에 1px을 넘는 그림자나 글로우를 주지 않는다.
- **Don't** 도장 말고 다른 곳에 연출 모션을 추가하지 않는다. 상태 전환은 160ms `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Don't** 이모지나 문자 기호(★☆)를 아이콘으로 쓰지 않는다. 아이콘은 SVG 라인 아이콘(ui/icons.py)이다.
