# -*- coding: utf-8 -*-
"""[big-patch 4·5단계] 하루 AI 한도 · 모델 등급 · 사용 지표 (개인정보 없음)."""

from services import ai_models, ai_quota, usage_log

def test_model_tiers_are_distinct():
    assert ai_models.model_for(ai_models.TIER_DRAFT) != ai_models.model_for(ai_models.TIER_FINAL)
    assert ai_models.model_for("unknown") == ai_models.DEFAULT_MODELS[ai_models.TIER_DRAFT]

def test_review_uses_final_tier_others_draft():
    from services import coverletter, review, score_explain
    assert review.MODEL_NAME == ai_models.DEFAULT_MODELS[ai_models.TIER_FINAL]
    assert coverletter.MODEL_NAME == ai_models.DEFAULT_MODELS[ai_models.TIER_DRAFT]
    assert score_explain.MODEL_NAME == ai_models.DEFAULT_MODELS[ai_models.TIER_DRAFT]

def test_record_ai_call_counts_and_prunes(usage_tmp):
    usage_log.record_ai_call("kakao_1", "write", "review", "2026-10-16")
    usage_log.record_ai_call("kakao_1", "write", "review", "2026-10-17")
    usage_log.record_ai_call("kakao_1", "write", "interview", "2026-10-17")
    usage_log.record_ai_call("kakao_2", "explain", "explain", "2026-10-17")
    doc = usage_log.load()
    me = doc["ai_quota"][usage_log.anon_id("kakao_1")]
    assert me == {"2026-10-17": {"write": 2}}          # 지난 날짜는 지워진다
    assert doc["ai_quota"][usage_log.anon_id("kakao_2")]["2026-10-17"] == {"explain": 1}
    assert sum(1 for e in doc["events"] if e["type"] == "ai") == 4

def test_no_raw_user_id_in_usage_doc(usage_tmp):
    usage_log.record_ai_call("guest_ABC123", "write", "review", "2026-10-17")
    raw = (usage_tmp / "usage.json").read_text(encoding="utf-8")
    assert "guest_ABC123" not in raw and "ABC123" not in raw

def test_quota_remaining_uses_stored_count(usage_tmp, monkeypatch):
    monkeypatch.setattr(ai_quota, "_today", lambda: "2026-10-17")
    monkeypatch.setattr(ai_quota, "_session_counts", lambda: {})
    for _ in range(3):
        usage_log.record_ai_call("kakao_9", "write", "review", "2026-10-17")
    assert ai_quota.used("write", "kakao_9") == 3
    assert ai_quota.remaining("write", "kakao_9") == ai_quota.DEFAULT_LIMITS["write"] - 3
    assert ai_quota.remaining("explain", "kakao_9") == ai_quota.DEFAULT_LIMITS["explain"]

def test_quota_blocks_when_exhausted(usage_tmp, monkeypatch):
    monkeypatch.setattr(ai_quota, "_today", lambda: "2026-10-17")
    monkeypatch.setattr(ai_quota, "_session_counts", lambda: {})
    monkeypatch.setattr(ai_quota.premium, "ai_enabled", lambda: True)
    monkeypatch.setattr(ai_quota.ss, "user_id", lambda: "kakao_7")
    assert ai_quota.can_use("review")
    for _ in range(ai_quota.DEFAULT_LIMITS["write"]):
        usage_log.record_ai_call("kakao_7", "write", "interview", "2026-10-17")
    assert not ai_quota.can_use("review")
    assert not ai_quota.can_use("coverletter")
    assert ai_quota.can_use("explain")                 # 묶음이 다르다
    assert "다 썼어요" in ai_quota.status_line("review")

def test_quota_off_without_premium(monkeypatch):
    monkeypatch.setattr(ai_quota.premium, "ai_enabled", lambda: False)
    assert not ai_quota.can_use("review")

def _ev(uid, kind, **kw):
    return {"uid": uid, "type": kind, "at": "2026-10-17T00:00:00+00:00", "is_test": False, **kw}

def test_summarize_metrics():
    doc = {
        "visitors": {"a": {"days": ["d1", "d2"]}, "b": {"days": ["d1"]},
                     "c": {"days": ["d1"]}, "t": {"days": ["d1"], "is_test": True}},
        "events": [
            _ev("a", "page", page="spec"), _ev("b", "page", page="spec"), _ev("c", "page", page="hub"),
            _ev("a", "feature", feature="spec_done"), _ev("a", "feature", feature="spec_done"),
            _ev("a", "feature", feature="interview"), _ev("b", "feature", feature="coverletter"),
            _ev("a", "ai", feature="interview"),
            {**_ev("t", "feature", feature="review"), "is_test": True},
        ],
    }
    s = usage_log.summarize(doc)
    assert s["users"] == 3 and s["returning"] == 1
    assert s["spec_visitors"] == 2 and s["spec_done"] == 1 and s["spec_done_rate"] == 0.5
    assert s["features"]["모의 면접 피드백"] == 1
    assert s["features"]["자소서 생성"] == 1
    assert s["features"]["자소서 첨삭"] == 0          # 테스트 기록은 뺀다
    assert s["ai_calls"] == {"interview": 1}
