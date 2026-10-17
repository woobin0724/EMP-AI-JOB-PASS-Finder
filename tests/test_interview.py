# -*- coding: utf-8 -*-
"""[big-patch 3단계] 모의 면접 · 인재상 연결."""

from data.company_showcase import COMPANY_SHOWCASE
from services import interview as iv
from services import talent_link as tl

PUBLIC = next(c for c in COMPANY_SHOWCASE if c["size_tag"] == "공기업")


def test_questions_deterministic_and_unique():
    a = iv.build_questions(PUBLIC, ["전기기능사"], "전기과", seed=1)
    b = iv.build_questions(PUBLIC, ["전기기능사"], "전기과", seed=1)
    assert a == b
    assert len(a) == iv.QUESTIONS_PER_SESSION
    assert len({q["q"] for q in a}) == len(a)


def test_questions_include_cert_and_major():
    qs = iv.build_questions(PUBLIC, ["전기기능사"], "전기과", seed=0, n=10)
    kinds = {q["kind"] for q in qs}
    assert "자격증" in kinds and "전공" in kinds
    assert any("전기기능사" in q["q"] for q in qs)


def test_questions_never_claim_real_past_questions():
    for c in [None] + COMPANY_SHOWCASE:
        for q in iv.build_questions(c, ["x"], "y", seed=3, n=10):
            assert "기출" not in q["q"]
            assert q["kind"]


def test_real_company_gets_no_sample_questions():
    real = {"id": "r", "name": "실제기업", "size_tag": "대기업", "data_kind": "verified",
            "interview_questions": ["지어낸 질문"]}
    qs = iv.build_questions(real, [], "", seed=0, n=10)
    assert all(q["q"] != "지어낸 질문" for q in qs)


def test_validate_answer():
    assert iv.validate_answer("")
    assert iv.validate_answer("짧음")
    assert iv.validate_answer("가" * (iv.MAX_ANSWER + 1))
    assert iv.validate_answer("가" * 50) == ""


def test_rule_feedback_detects_number_action_result_talent():
    c = {"ideal_talent": ["성실", "안전의식"]}
    ans = "실습 기간 3주 동안 매일 보호구 점검표를 확인했습니다. 그 결과 우리 조는 사고 없이 실습을 마쳤습니다."
    fb = iv.rule_feedback("q", ans, c)
    joined = " ".join(fb["good"])
    assert "3주" in joined and "인재상" in joined
    assert {l["talent"] for l in fb["links"]} == {"성실", "안전의식"}


def test_rule_feedback_suggests_when_vague():
    fb = iv.rule_feedback("q", "저는 열심히 노력하는 사람이고 항상 최선을 다하는 자세를 가지고 있어요.", {"ideal_talent": ["창의"]})
    assert any("숫자" in x for x in fb["improve"])
    assert any("창의" in x for x in fb["improve"])


def test_feedback_without_ai_is_rule_based():
    fb, source = iv.feedback("q", "가" * 40, PUBLIC, use_api=False)
    assert source == "rule" and fb["good"]


def test_copy_prompt_contains_question_answer_and_talent():
    p = iv.copy_prompt("질문입니다", "답변입니다", PUBLIC)
    assert "질문입니다" in p and "답변입니다" in p
    assert PUBLIC["ideal_talent"][0] in p


def test_parse_ai_output():
    text = "잘된 점:\n- 좋아요\n보완할 점:\n- 숫자\n- 결과\n인재상 연결:\n- 성실: 매일\n다시 말해 보기:\n고친 문장."
    fb = iv._parse(text)
    assert fb["good"] == ["좋아요"] and len(fb["improve"]) == 2
    assert fb["links"] == [{"talent": "성실", "note": "매일"}]
    assert fb["rewrite"] == "고친 문장."


def test_talent_links_per_sentence():
    text = "저는 매일 실습 기록을 남겼습니다. 친구들과 함께 팀 과제를 했습니다. 날씨가 좋았다."
    links = tl.link_sentences(text, ["성실", "협업"])
    assert len(links) == 2
    assert links[0]["links"][0] == {"talent": "성실", "cue": "매일"}
    assert links[1]["links"][0]["talent"] == "협업"
    shown, missing = tl.coverage(text, ["성실", "협업", "창의"])
    assert shown == ["성실", "협업"] and missing == ["창의"]


def test_talent_links_empty_without_talent():
    assert tl.link_sentences("아무 글", []) == []


def test_every_showcase_talent_has_cues():
    for c in COMPANY_SHOWCASE:
        for t in c["ideal_talent"]:
            assert t in tl.CUES, t
