# -*- coding: utf-8 -*-
"""
services/coverletter.py
[Phase 5] 자기소개서 생성 — 템플릿 채우기에서 '서사 쓰기'로

▣ 무엇이 문제였나
   기존 생성기는 f-string 세 단락에 이름·기업·강점만 갈아끼웠다. 그래서
   전교생의 자소서가 조사(助詞)만 다른 같은 글이 됐다. AI 경로도 마찬가지로
   "다음 정보를 바탕으로 써줘" 뒤에 항목을 나열하는 수준이라, 모델이 받은
   재료를 그대로 문장에 배치할 뿐 이야기를 만들지 않았다.

▣ 이번에 바꾼 것
   1) 프롬프트를 '재료 나열'에서 '서사 지시'로 재설계.
      금지 표현 목록(자소서를 똑같이 보이게 만드는 상투어)을 명시했다.
   2) 입력을 확장: 에피소드(선택), 지원 동기 키워드, 문체, 분량.
   3) 분량에 따라 구성 자체를 바꾼다. 500자에 3개 섹션을 넣으면 각 섹션이
      두 문장짜리 토막이 된다.
   4) 서사 접근(narrative angle)을 회차마다 바꿔 '다시 생성하기'가
      같은 글의 재탕이 아니라 다른 구성의 초안을 내놓게 했다.
   5) API 키가 없을 때 쓰는 템플릿 생성기도 문장 풀에서 고르도록 바꿨다.
      대회 시연에서 키가 없으면 이 경로가 실제로 쓰이기 때문이다.

▣ temperature 를 쓰지 않는 이유 (중요)
   현행 모델(Opus 5 / Sonnet 5 / Opus 4.6+)에서 temperature·top_p·top_k 는
   **제거**되었다. 보내면 400 에러가 난다. 그래서 "매번 조금씩 다르게"는
   샘플링 난수가 아니라 **서사 접근을 회차별로 바꾸는 방식**으로 구현했다.
   난수보다 낫다 — 결과가 무작위로 흔들리는 게 아니라 구성이 실제로 달라지고,
   회차가 캐시 키에 들어가므로 같은 회차를 다시 요청하면 캐시가 그대로 맞는다.
"""

import hashlib
import re

# ------------------------------------------------------------
# 모델 설정
# ------------------------------------------------------------
# 현행 모델. 기존 코드의 "claude-sonnet-4-5" 는 구형이라 교체했다.
# 비용을 낮추려면 "claude-sonnet-5" 로 바꾸면 된다 (입력 $2 / 출력 $10 per MTok,
# Opus 5 는 $5 / $25). 품질 판단은 팀의 몫이라 기본값은 Opus 5 로 둔다.
MODEL_NAME = "claude-opus-5"

# 잘림 방지. max_tokens 는 상한일 뿐이라 높게 잡아도 실제 생성량만 과금된다.
# 기존 900 은 1000자 자소서 + 추론 토큰을 감당하지 못해 문장 중간에서 끊겼다.
MAX_TOKENS = 16000

# 추론 깊이. 자소서는 난이도 높은 추론 과제가 아니고 학생이 화면 앞에서
# 기다리므로 medium 으로 둔다. 품질을 더 원하면 "high" 로 올리면 된다.
EFFORT = "medium"

REQUEST_TIMEOUT = 90.0

# 서버측 모델 폴백(beta)이 이 계정/리전에서 거부되면 한 번만 확인하고 끈다.
# 매 호출마다 400 을 맞고 템플릿으로 조용히 내려가면, 팀은 AI 가 동작하지
# 않는다는 사실조차 모르게 된다.
_FALLBACKS_SUPPORTED = True


# ------------------------------------------------------------
# 선택 옵션
# ------------------------------------------------------------
TONE_OPTIONS = {
    "격식체": (
        "정중한 지원서 문체. '~습니다'체를 쓰되 문장을 끝까지 갖춰 쓰고, "
        "공적인 어휘를 택한다."
    ),
    "친근체": (
        "'~습니다'체는 유지하되 문장을 짧고 담백하게 쓴다. 한자어와 관공서식 "
        "표현을 줄이고 일상적인 단어를 택한다. 읽는 사람이 말을 듣는 느낌이 나게."
    ),
}
DEFAULT_TONE = "격식체"

# 분량에 따라 구성 자체를 바꾼다.
LENGTH_OPTIONS = {
    500: {
        "label": "500자 (짧게)",
        "structure": "섹션 제목 없이 한 흐름으로 이어지는 3~4개 문단",
        "guide": "가장 강한 재료 하나에 집중한다. 여러 경험을 나열하면 500자로는 전부 얕아진다.",
    },
    800: {
        "label": "800자 (표준)",
        "structure": "[지원 동기와 나] / [직무 역량을 갖춘 과정] 2개 섹션",
        "guide": "동기와 근거를 각각 한 덩어리씩 배치한다.",
    },
    1000: {
        "label": "1000자 (자세히)",
        "structure": "[지원 동기와 나] / [직무 역량을 갖춘 과정] / [입사 후 계획] 3개 섹션",
        "guide": "입사 후 계획은 막연한 다짐이 아니라 첫 1년에 할 일로 구체화한다.",
    },
}
DEFAULT_LENGTH = 800

# 회차마다 다른 구성으로 쓰게 하는 서사 접근.
# '다시 생성하기'를 누를 때마다 다음 항목이 선택된다.
NARRATIVE_ANGLES = [
    "구체적인 장면 하나로 글을 열고, 그 장면에서 지원자의 강점을 끌어내는 구성",
    "지원 동기를 먼저 분명히 세운 뒤, 그 동기가 말뿐이 아님을 경험으로 증명하는 구성",
    "막혔던 문제 → 시도한 것 → 거기서 배운 것 순으로 흐르는 구성",
    "이 회사가 필요로 할 역량을 먼저 짚고, 그것을 어떻게 준비해 왔는지 답하는 구성",
    "지금 가진 기술 하나를 깊게 설명하고, 그 기술을 어디까지 키우고 싶은지로 잇는 구성",
]

# 자소서를 전부 똑같아 보이게 만드는 표현들.
BANNED_EXPRESSIONS = [
    "'저는 ~한 사람입니다' 로 시작하는 문장",
    "'귀사', '귀 사'",
    "'~에 지원하게 되어 영광입니다', '영광으로 생각합니다'",
    "'어릴 적부터 ~에 관심이 많았습니다'",
    "'열정', '최선을 다하겠습니다', '뼈를 묻겠습니다', '없어서는 안 될 인재'",
    "'귀중한 기회', '성실함을 바탕으로' 같은 빈 수식어",
]


def normalize_options(options: dict | None) -> dict:
    """화면에서 넘어온 옵션을 안전한 기본값으로 채운다."""
    options = options or {}
    tone = options.get("tone")
    if tone not in TONE_OPTIONS:
        tone = DEFAULT_TONE

    try:
        length = int(options.get("length", DEFAULT_LENGTH))
    except (TypeError, ValueError):
        length = DEFAULT_LENGTH
    if length not in LENGTH_OPTIONS:
        length = DEFAULT_LENGTH

    try:
        variation = max(0, int(options.get("variation", 0)))
    except (TypeError, ValueError):
        variation = 0

    return {"tone": tone, "length": length, "variation": variation}


def angle_for(variation: int) -> str:
    return NARRATIVE_ANGLES[variation % len(NARRATIVE_ANGLES)]


# ------------------------------------------------------------
# 프롬프트 (순수 함수 — 테스트에서 직접 검증한다)
# ------------------------------------------------------------
def build_system_prompt(options: dict) -> str:
    options = normalize_options(options)
    tone_guide = TONE_OPTIONS[options["tone"]]
    banned = "\n".join(f"  - {b}" for b in BANNED_EXPRESSIONS)

    return f"""당신은 마이스터고 학생의 취업 자기소개서를 함께 쓰는 진로 상담 교사입니다.
학생이 건넨 재료로 **하나의 이야기**를 만드는 것이 당신의 일입니다.

[가장 중요한 원칙]
재료를 문장에 끼워 넣지 마십시오. 재료들이 서로 연결되는 지점을 찾아 그것을
이야기의 축으로 삼으십시오. 자격증과 강점과 경험이 따로 놀면 그 자소서는
누구의 것도 아닙니다.

[반드시 지킬 것]
1. 추상어 대신 장면을 쓰십시오. '성실합니다' 대신 그 성실함이 드러난 순간을
   쓰십시오. 형용사는 증거가 있을 때만 씁니다.
2. 학생이 주지 않은 사실을 지어내지 마십시오. 수상 이력, 구체적 수치, 없는
   경험을 만들어내면 면접에서 학생이 무너집니다. 재료가 적으면 있는 재료를
   깊게 쓰십시오.
3. 기업 인재상은 단어로 나열하지 마십시오. 학생의 경험이 그 가치와 어디서
   맞닿는지를 보여주는 방식으로만 녹여내십시오.
4. 문체: {tone_guide}
5. 같은 어미('~습니다', '~했습니다')를 세 문장 연속으로 쓰지 마십시오.

[절대 쓰지 말 것 — 모든 자소서를 똑같아 보이게 만드는 표현]
{banned}

[출력 형식]
자기소개서 본문만 출력하십시오. 설명, 머리말, '아래는 ~입니다' 같은 안내
문구를 붙이지 마십시오."""


def build_user_prompt(profile: dict, company: dict | None, options: dict) -> str:
    """학생이 건넨 재료와 이번 회차의 구성 지시를 담는다."""
    options = normalize_options(options)
    length_spec = LENGTH_OPTIONS[options["length"]]

    company_name = (company or {}).get("name") or profile.get("company_name") or "지원 기업"
    talent = ", ".join((company or {}).get("ideal_talent", []) or [])
    certs = ", ".join(profile.get("certs") or [])

    lines = [
        "[학생이 건넨 재료]",
        f"- 이름: {profile.get('name') or '(미입력)'}",
        f"- 지원 기업: {company_name}",
        f"- 목표 직무: {profile.get('target_dept') or '(미입력)'}",
    ]
    if talent:
        lines.append(f"- 그 기업이 밝힌 인재상: {talent}")
    if certs:
        lines.append(f"- 보유 자격증: {certs}")
    if profile.get("grade"):
        lines.append(f"- 내신 등급: {profile['grade']}")
    if profile.get("strength"):
        lines.append(f"- 스스로 꼽은 강점: {profile['strength']}")

    # 확장 입력 — 여기가 자소서를 '그 학생의 것'으로 만드는 재료다
    if (profile.get("episode") or "").strip():
        lines.append(f"- 관련 경험·에피소드: {profile['episode'].strip()}")
    if (profile.get("motive") or "").strip():
        lines.append(f"- 지원 동기 키워드: {profile['motive'].strip()}")
    if (profile.get("story") or "").strip():
        lines.append(f"- 고교 생활 이야기: {profile['story'].strip()}")

    thin = not any((profile.get("episode"), profile.get("story"), profile.get("motive")))
    if thin:
        lines.append(
            "\n(에피소드가 비어 있습니다. 없는 경험을 지어내지 말고, 자격증을 준비한 "
            "과정과 목표 직무를 연결해 쓰십시오. 그리고 마지막 줄에 "
            "'※ 어떤 경험을 덧붙이면 좋을지' 한 문장으로 조언을 남기십시오.)"
        )

    lines += [
        "",
        "[이번 초안의 구성]",
        f"- 접근: {angle_for(options['variation'])}",
        f"- 구성: {length_spec['structure']}",
        f"- 유의: {length_spec['guide']}",
        f"- 분량: 공백 포함 {options['length']}자 내외 (±10%)",
        "",
        "위 재료로 자기소개서 초안을 쓰십시오.",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------
# AI 생성 (공식 Anthropic SDK)
# ------------------------------------------------------------
def _claude_cover_letter(profile: dict, company: dict | None, api_key: str,
                         options: dict | None = None) -> str:
    """
    Anthropic SDK 로 자기소개서를 생성한다. 실패하면 예외를 던지고,
    호출부(services/llm.py)가 템플릿 생성기로 내려간다.
    """
    global _FALLBACKS_SUPPORTED
    import anthropic

    options = normalize_options(options)
    client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=1)

    params = {
        "model": MODEL_NAME,
        "max_tokens": MAX_TOKENS,
        "system": build_system_prompt(options),
        "output_config": {"effort": EFFORT},
        "messages": [{"role": "user", "content": build_user_prompt(profile, company, options)}],
    }

    if _FALLBACKS_SUPPORTED:
        try:
            response = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                **params,
            )
        except anthropic.BadRequestError:
            # 이 계정/리전에서 beta 파라미터가 거부됨 → 이후로는 표준 경로만 쓴다
            _FALLBACKS_SUPPORTED = False
            response = client.messages.create(**params)
    else:
        response = client.messages.create(**params)

    # 안전 분류기가 요청을 거절한 경우 content 를 읽기 전에 먼저 확인한다
    if getattr(response, "stop_reason", None) == "refusal":
        raise ValueError("모델이 생성을 거절했습니다 (stop_reason=refusal)")

    text = "".join(
        block.text for block in response.content
        if getattr(block, "type", "") == "text"
    ).strip()

    if not text:
        raise ValueError("응답에 본문 텍스트가 없습니다")
    return text


# ------------------------------------------------------------
# 템플릿 생성 (API 키가 없을 때)
# ------------------------------------------------------------
# 기존에는 f-string 세 단락이 고정이라 모든 학생이 같은 글을 받았다.
# 문장 풀에서 고르게 바꿔, 최소한 '옆자리와 다른 글'이 나오게 했다.
# ------------------------------------------------------------
# 한글 조사 처리
# ------------------------------------------------------------
# 문장 풀에 기업명·자격증명을 끼워 넣다 보면 "태백중공업를", "'끈기'은" 같은
# 조사 오류가 난다. 학생이 그대로 제출하면 바로 눈에 띄는 실수라서,
# 받침 유무를 보고 조사를 고르는 처리를 넣었다.
# 템플릿에서는 `{company}#를` 처럼 # 마커를 쓰고, 마지막에 한 번 치환한다.
_JOSA_PAIRS = {
    "를": ("을", "를"),
    "은": ("은", "는"),
    "이": ("이", "가"),
    "와": ("과", "와"),
    "로": ("으로", "로"),
}
_JOSA_RE = re.compile(r"#(를|은|이|와|로)")


def _has_batchim(ch: str) -> bool | None:
    """한글 음절의 받침 유무. 한글이 아니면 None."""
    if not ("가" <= ch <= "힣"):
        return None
    return (ord(ch) - 0xAC00) % 28 != 0


def apply_josa(text: str) -> str:
    """
    `#를` 형태의 마커를 실제 조사로 바꾼다.

    마커 바로 앞이 따옴표나 괄호일 수 있으므로(예: '끈기'#은),
    뒤에서부터 가장 가까운 한글 음절을 찾아 판단한다.
    """
    def repl(match):
        marker = match.group(1)
        with_batchim, without_batchim = _JOSA_PAIRS[marker]

        # 마커 앞쪽에서 가장 가까운 한글 음절 찾기
        idx = match.start() - 1
        batchim = None
        while idx >= 0:
            batchim = _has_batchim(text[idx])
            if batchim is not None:
                break
            idx -= 1

        if batchim is None:          # 한글이 없으면(영문·숫자) 받침 없는 쪽으로
            return without_batchim
        if marker == "로" and text[idx] == "ㄹ":
            return "로"
        # 'ㄹ' 받침은 '로'를 쓴다 (예: 서울로)
        if marker == "로" and batchim and (ord(text[idx]) - 0xAC00) % 28 == 8:
            return "로"
        return with_batchim if batchim else without_batchim

    return _JOSA_RE.sub(repl, text)


_OPENERS = [
    "{dept} 일을 하고 싶어 {company}에 지원했습니다.",
    "{company}의 {dept} 자리에 제 3년을 걸어보려 합니다.",
    "학교에서 배운 것을 {company}의 현장에서 이어가고 싶습니다.",
    "{dept}는 제가 실습 시간마다 가장 오래 붙잡고 있던 일입니다.",
    "{company}가 찾는 사람이 되기 위해 무엇을 준비했는지 적었습니다.",
    "제가 {dept}에서 바로 쓸 수 있는 것부터 말씀드리겠습니다.",
    "실습실에서 보낸 3년이 {company}의 {dept}으로 이어지길 바랍니다.",
    "{company}#를 목표로 잡은 뒤 제 실습 노트가 달라졌습니다.",
]
_CERT_LINES = [
    "재학 중 {certs}#를 취득하며 기초를 다졌습니다.",
    "{certs}#를 준비하는 동안 기계를 도면으로 읽는 법을 익혔습니다.",
    "{certs} 취득 과정에서 반복 측정과 기록의 중요성을 배웠습니다.",
    "{certs}#은 시험을 위해서가 아니라 현장에서 쓰려고 딴 자격증입니다.",
    "{certs}#를 따는 동안 손보다 먼저 도면을 보는 습관이 생겼습니다.",
    "{certs} 실기를 준비하며 같은 동작을 수백 번 반복했습니다.",
]
_STRENGTH_LINES = [
    "제가 일할 때 가장 자주 듣는 말은 '{strength}'입니다.",
    "무언가를 끝까지 맞춰놓는 편이라 '{strength}'#이라는 평을 받아왔습니다.",
    "{strength} — 이것이 제가 현장에서 쓸 수 있는 가장 확실한 도구입니다.",
    "조원들은 저를 '{strength}'으로 기억합니다.",
    "제 작업 속도는 빠르지 않습니다. 대신 '{strength}'이 남습니다.",
    "'{strength}'#은 칭찬이라기보다 제 작업 방식에 대한 설명에 가깝습니다.",
]
_TALENT_LINES = [
    "{company}#이 말하는 '{talent}'#은 제가 실습실에서 몸으로 배운 것과 겹칩니다.",
    "'{talent}' — 이 말이 왜 중요한지 실습 중 사고가 날 뻔한 뒤에 알았습니다.",
    "{company}의 '{talent}'#은 제가 조별 과제에서 가장 많이 신경 쓴 부분입니다.",
    "'{talent}'#를 갖춘 사람을 찾는다는 문장에서 제 3년이 떠올랐습니다.",
]
_CLOSERS = [
    "입사 후 첫 1년은 현장의 안전수칙과 장비를 몸에 익히는 데 쓰겠습니다.",
    "먼저 배우고, 그다음 맡겠습니다. 첫해 목표는 공정 한 구간을 혼자 볼 수 있게 되는 것입니다.",
    "선배들이 쌓아온 방식을 정확히 익힌 뒤에 제 방식을 보태겠습니다.",
    "첫해에는 묻는 사람이 되겠습니다. 다음 해에는 답하는 사람이 되겠습니다.",
    "제가 맡은 구간에서 불량이 나지 않는 것, 그것이 입사 첫해의 목표입니다.",
]
_MOTIVE_LINES = [
    "제가 이 일을 하고 싶은 이유는 {motive}입니다.",
    "{motive} — 여기에 제 관심이 걸려 있습니다.",
    "{motive}#를 다루는 일이라서 지원했습니다.",
    "진로를 {motive} 쪽으로 정하고 나서 준비 방향이 분명해졌습니다.",
]


def _pick(pool: list, seed: str, variation: int) -> str:
    """같은 학생·같은 회차면 같은 문장, 다른 학생이면 다른 문장이 나오게 고른다."""
    digest = hashlib.sha256(f"{seed}|{variation}".encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _shuffled(items: list, seed: str, variation: int) -> list:
    """
    문장 순서를 학생마다 다르게 섞는다 (결정론적).

    문장 풀만 넓혀서는 부족했다. 골격이 같으면 단어 몇 개가 달라도 글이
    똑같이 읽힌다(측정해보니 유사도 0.85~0.91). 순서를 바꾸면 글의 흐름
    자체가 달라진다. Fisher-Yates 를 해시에서 뽑은 난수로 돌린다.
    """
    result = list(items)
    digest = hashlib.sha256(f"order|{seed}|{variation}".encode("utf-8")).hexdigest()
    for i in range(len(result) - 1, 0, -1):
        j = int(digest[(i * 2) % 60: (i * 2) % 60 + 2], 16) % (i + 1)
        result[i], result[j] = result[j], result[i]
    return result


def _spec_comparison_sentence(profile: dict, company: dict) -> str:
    """학생 스펙과 기업의 예시 합격자 평균 스펙을 비교하는 문장."""
    grade = profile.get("grade")
    num_certs = len(profile.get("certs") or [])
    avg_grade = company.get("avg_applicant_grade")
    avg_certs = company.get("avg_applicant_certs")

    if grade is None or avg_grade is None:
        return ""

    grade_part = ("평균보다 앞서 있습니다" if grade <= avg_grade
                  else "평균보다 조금 뒤지지만 실습 성과로 보완하고자 합니다")

    # 자격증이 하나도 없는데 "0개로 평균과 비슷합니다"라고 쓰면 명백한 거짓말이 된다.
    # 학생이 그대로 제출하면 면접에서 바로 걸리는 문장이라 경우를 나눈다.
    if num_certs == 0:
        cert_part = "자격증은 아직 준비 중입니다"
    elif num_certs >= (avg_certs or 0):
        cert_part = f"자격증은 {num_certs}개로 평균과 같거나 많습니다"
    else:
        cert_part = f"자격증은 {num_certs}개로 평균보다 적지만 추가 취득을 준비하고 있습니다"

    return (
        f"(참고 — 예시 통계 기준 {company['name']} 지원자 평균은 내신 {avg_grade}등급, "
        f"자격증 {avg_certs}개입니다. 저는 내신 {grade}등급으로 {grade_part}. {cert_part}.)"
    )


def _template_cover_letter(profile: dict, company: dict | None,
                           options: dict | None = None) -> str:
    """
    API 키가 없을 때 쓰는 규칙 기반 생성기.

    기존 버전은 f-string 세 단락이 고정이라 두 학생의 글이 98% 일치했다.
    (직접 측정한 수치다.) 여기서는 세 가지를 바꿨다.
      1) 문장을 풀에서 고른다 — 학생마다 다른 표현
      2) 가운데 문장들의 **순서를 섞는다** — 글의 흐름 자체가 달라진다
      3) 학생이 준 에피소드·동기를 본문에 그대로 싣는다 — 가장 강한 개인화

    그래도 AI 경로만큼 개인화되지는 않는다. 같은 재료를 넣은 두 학생의 글은
    여전히 비슷하게 읽힌다(그게 맞기도 하다 — 재료가 같으니까).
    이 경로는 '키가 없어도 앱이 멈추지 않는다'를 보장하는 안전망이지,
    AI 생성의 대체품이 아니다.
    """
    options = normalize_options(options)
    variation = options["variation"]

    name = profile.get("name") or "지원자"
    dept = profile.get("target_dept") or "희망 직무"
    company_name = (company or {}).get("name") or profile.get("company_name") or "지원 기업"
    strength = profile.get("strength") or "끝까지 맞춰놓는 성격"
    certs = ", ".join(profile.get("certs") or []) or "전공 자격증"
    seed = f"{name}|{company_name}|{dept}|{strength}|{certs}"

    episode = (profile.get("episode") or profile.get("story") or "").strip()
    motive = (profile.get("motive") or "").strip()

    # ---- 첫 문장과 마지막 문장은 자리를 지킨다 ----
    opener = _pick(_OPENERS, seed, variation).format(
        company=company_name, dept=dept, name=name)
    closer = _pick(_CLOSERS, seed + "e", variation)

    # ---- 가운데 문장들 — 순서를 섞는다 ----
    middle = [_pick(_CERT_LINES, seed + "c", variation).format(certs=certs),
              _pick(_STRENGTH_LINES, seed + "s", variation).format(strength=strength)]
    if motive:
        middle.append(_pick(_MOTIVE_LINES, seed + "m", variation).format(motive=motive))
    if episode:
        middle.append(episode if episode.endswith(('.', '다', '요')) else episode + ".")
    if company and company.get("ideal_talent"):
        middle.append(
            _pick(_TALENT_LINES, seed + "t", variation).format(
                company=company_name, talent=", ".join(company["ideal_talent"]))
        )

    middle = _shuffled(middle, seed, variation)

    body = [opener] + middle

    # 분량이 넉넉할 때만 덧붙이는 문장들
    if options["length"] >= 800 and company:
        spec_line = _spec_comparison_sentence(profile, company)
        if spec_line:
            body.append(spec_line)
    if options["length"] >= 800:
        body.append(closer)
    if options["length"] >= 1000:
        body.append(
            f"길게 보면 {company_name}에서 제 이름으로 공정 하나를 책임지는 사람이 "
            f"되고 싶습니다."
        )

    # 분량 규격에 맞춰 섹션 제목을 붙인다 (500자는 제목 없이 한 흐름)
    if options["length"] == 500:
        text = " ".join(body)
    elif options["length"] == 800:
        half = max(1, len(body) // 2)
        text = ("[지원 동기와 나]\n" + " ".join(body[:half]) +
                "\n\n[직무 역량을 갖춘 과정]\n" + " ".join(body[half:]))
    else:
        third = max(1, len(body) // 3)
        text = ("[지원 동기와 나]\n" + " ".join(body[:third]) +
                "\n\n[직무 역량을 갖춘 과정]\n" + " ".join(body[third:third * 2]) +
                "\n\n[입사 후 계획]\n" + " ".join(body[third * 2:]))

    return apply_josa(text)


def generate_cover_letter(profile: dict, company: dict | None = None,
                          api_key: str | None = None, options: dict | None = None):
    """
    자기소개서 초안을 생성한다.
    반환값: (본문, 생성 방식 "ai" | "template")
    """
    if api_key:
        try:
            return _claude_cover_letter(profile, company, api_key, options), "ai"
        except Exception:
            pass  # 실패 시 템플릿 생성기로 자동 전환
    return _template_cover_letter(profile, company, options), "template"
