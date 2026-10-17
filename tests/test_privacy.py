# -*- coding: utf-8 -*-
"""[big-patch 6단계] 처리방침이 실제 저장 항목과 맞는지 · 내 기록 지우기."""

from services import reactions, store, usage_log
from views import privacy


def test_policy_mentions_every_stored_user_key():
    text = " ".join(items for _, items, _ in privacy.STORED)
    labels = {
        "display_name": "표시 이름", "email": "이메일", "role": "역할", "class_code": "반 코드",
        "provider": "로그인 방식", "bookmarks": "찜", "viewed": "열람", "score_history": "점수 기록",
        "milestones": "로드맵",
    }
    for key in store._default_user("x"):
        if key in ("user_id", "created_at", "class_skipped", "profile"):
            continue
        assert labels[key] in text, key
    for word in ("학과", "내신", "자격증", "강점", "목표 기업"):     # profile 스냅샷
        assert word in text


def test_policy_says_drafts_are_not_stored():
    joined = " ".join(privacy.NOT_STORED)
    assert "자소서" in joined and "면접 답변" in joined and "초안" in joined


def test_delete_user_tombstone(tmp_path, monkeypatch):
    from services import storage_backend
    monkeypatch.setattr(storage_backend, "STORE_PATH", str(tmp_path / "store.json"))
    storage_backend.reset_backend()
    store.upsert_user("guest_AAA111", display_name="학생", email="a@b.c", role="student")
    store.save_profile("guest_AAA111", dept="기계과", grade=2.0, certs=["x"])
    teacher = store.upsert_user("kakao_T", role="teacher")
    k = store.create_class(teacher["user_id"], "고", "3", "1")
    store.join_class("guest_AAA111", k["class_code"])

    assert store.delete_user("guest_AAA111") is True
    raw = (tmp_path / "store.json").read_text(encoding="utf-8")
    assert "a@b.c" not in raw and "기계과" not in raw and "학생" not in raw
    assert store.get_user("guest_AAA111") is None
    assert store.class_students(k["class_code"]) == []
    assert store.delete_user("kakao_T") is False                 # 선생님은 화면에서 못 지운다
    again = store.upsert_user("guest_AAA111", display_name="새로")  # 같은 코드로 다시 오면 새 계정
    assert again["display_name"] == "새로" and again["profile"] == {} and "deleted_at" not in again
    storage_backend.reset_backend()


def test_usage_forget(usage_tmp):
    usage_log.record_ai_call("guest_B", "write", "review", "2026-10-17")
    usage_log.record_ai_call("guest_C", "write", "review", "2026-10-17")
    usage_log.forget("guest_B")
    doc = usage_log.load()
    assert usage_log.anon_id("guest_B") not in doc.get("ai_quota", {})
    assert all(e["uid"] != usage_log.anon_id("guest_B") for e in doc["events"])
    assert any(e["uid"] == usage_log.anon_id("guest_C") for e in doc["events"])


def test_reactions_forget_does_not_create_file(tmp_path, monkeypatch):
    path = tmp_path / "reactions.json"
    monkeypatch.setattr(reactions, "REACTIONS_PATH", str(path))
    monkeypatch.setattr(reactions, "_state", lambda: {})
    reactions.forget("guest_X")
    assert not path.exists()
