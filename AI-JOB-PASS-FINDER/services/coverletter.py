# -*- coding: utf-8 -*-
"""
services/coverletter.py
기업 맞춤형 자기소개서 초안 생성 로직 (링커리어 합격데이터 + 캐치 인재상 참고 방식)

동작 방식
---------
1) 기본값: API 키 없이도 동작하는 규칙 기반 템플릿 생성기 사용 (항상 100% 동작 보장)
2) (선택) ANTHROPIC_API_KEY가 secrets에 있으면 실제 Claude 모델을 호출해 더 자연스러운
   초안을 생성 시도하고, 실패하면 템플릿 생성기로 자동 대체(fallback)한다.

※ 자소서에 등장하는 "합격자 평균 스펙 비교" 문구는 기업의 avg_applicant_grade /
   avg_applicant_certs (예시 데이터, data/company_showcase.py)를 근거로 생성되며,
   실제 해당 기업의 공식 통계가 아닙니다.
"""

import requests

MODEL_NAME = "claude-sonnet-4-5"  # 최신 모델명은 Anthropic 문서에서 확인 후 교체
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def _spec_comparison_sentence(profile: dict, company: dict) -> str:
    """학생 스펙과 기업의 예시 합격자 평균 스펙을 비교하는 문장을 생성한다."""
    grade = profile.get("grade")
    num_certs = len(profile.get("certs") or [])
    avg_grade = company.get("avg_applicant_grade")
    avg_certs = company.get("avg_applicant_certs")

    if grade is None or avg_grade is None:
        return ""

    grade_cmp = "우수한 편" if grade <= avg_grade else "다소 낮지만 자격증으로 보완 가능한 수준"
    cert_cmp = "동일하거나 더 많은" if num_certs >= (avg_certs or 0) else "비슷한 수준의"

    return (
        f"(참고: 예시 통계 기준 {company['name']} 지원자 평균 내신은 {avg_grade}등급, "
        f"평균 보유 자격증은 {avg_certs}개 수준으로, 제 스펙은 내신 {grade}등급으로 평균 대비 {grade_cmp}이며 "
        f"자격증 {num_certs}개로 평균과 {cert_cmp} 수준입니다.)"
    )


def _template_cover_letter(profile: dict, company: dict | None) -> str:
    """API 키가 없을 때 사용하는 규칙 기반 자기소개서 초안 생성기."""
    name = profile.get("name") or "지원자"
    target_dept = profile.get("target_dept") or "희망 직무"
    company_name = company["name"] if company else (profile.get("company_name") or "지원 기업")
    story = profile.get("story") or "성실함과 책임감을 바탕으로 학교생활에 임해왔습니다."
    strength = profile.get("strength") or "꾸준함과 문제 해결 능력"
    certs = profile.get("certs") or []
    certs_str = ", ".join(certs) if certs else "전공 관련 자격증"

    talent_str = ""
    if company and company.get("ideal_talent"):
        talent_str = f" 특히 {company_name}이 강조하는 '{', '.join(company['ideal_talent'])}'의 가치와 저의 강점이 맞닿아 있다고 생각합니다."

    spec_line = _spec_comparison_sentence(profile, company) if company else ""

    section1 = (
        f"안녕하십니까. 마이스터고등학교에서 전공 역량을 쌓아온 {name}입니다. "
        f"재학 기간 동안 {story} 이러한 경험을 바탕으로 {target_dept} 직무에 필요한 "
        f"기초 역량을 다져왔습니다."
    )
    section2 = (
        f"{company_name}의 {target_dept} 직무에 지원한 이유는 전공 지식을 실무에 바로 "
        f"적용하고 성장하고 싶기 때문입니다. 재학 중 취득한 {certs_str} 등을 통해 "
        f"직무에 필요한 기술 기초를 다졌으며, 저의 핵심 강점인 '{strength}'을 바탕으로 "
        f"빠르게 현장에 적응할 자신이 있습니다.{talent_str} {spec_line}"
    )
    section3 = (
        f"입사 후에는 선배 사원의 지도를 적극적으로 흡수하며 현장 매뉴얼과 안전수칙을 "
        f"체득하는 것을 단기 목표로 삼겠습니다. 장기적으로는 '{strength}'을 바탕으로 "
        f"{company_name}에서 없어서는 안 될 전문 기술 인재로 성장하겠습니다."
    )

    return (
        "[1. 자기소개 및 학교생활]\n" + section1 + "\n\n" +
        "[2. 지원 동기 및 전공 핵심 역량]\n" + section2 + "\n\n" +
        "[3. 입사 후 직무 계획]\n" + section3
    )


def _claude_cover_letter(profile: dict, company: dict | None, api_key: str, timeout: int = 15) -> str:
    """Anthropic API를 호출해 자기소개서 초안을 생성한다. 실패 시 예외를 던진다."""
    company_name = company["name"] if company else profile.get("company_name", "")
    talent = ", ".join(company.get("ideal_talent", [])) if company else ""

    prompt = f"""
다음 정보를 바탕으로 마이스터고 학생의 취업 자기소개서 초안을 작성해줘.
- 이름: {profile.get('name')}
- 목표 직무: {profile.get('target_dept')}
- 지원 기업: {company_name}
- 기업 인재상 키워드: {talent}
- 고교 스토리: {profile.get('story')}
- 핵심 강점: {profile.get('strength')}
- 보유 자격증: {', '.join(profile.get('certs') or [])}

[1. 자기소개 및 학교생활] [2. 지원 동기 및 전공 핵심 역량] [3. 입사 후 직무 계획]
3개 섹션으로 나눠서, 기업 인재상 키워드가 자연스럽게 녹아들도록, 과장 없이 담백하고
성실한 톤으로 작성해줘.
""".strip()

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "max_tokens": 900,
        "messages": [{"role": "user", "content": prompt}],
    }
    res = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=timeout)
    res.raise_for_status()
    data = res.json()

    text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )
    if not text.strip():
        raise ValueError("Claude API 응답에 텍스트가 없음")
    return text


def generate_cover_letter(profile: dict, company: dict | None = None, api_key: str | None = None):
    """
    자기소개서 초안을 생성한다.
    반환값: (본문, 생성 방식 "ai" | "template")
    """
    if api_key:
        try:
            return _claude_cover_letter(profile, company, api_key), "ai"
        except Exception:
            pass  # 실패 시 템플릿 생성기로 자동 전환
    return _template_cover_letter(profile, company), "template"
