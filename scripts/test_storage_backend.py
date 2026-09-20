# -*- coding: utf-8 -*-
"""Supabase 백엔드 로직을 가짜 REST 서버로 검증한다 (네트워크 없이)."""
import sys, json
sys.path.insert(0, "/home/user/EMP-AI-JOB-PASS-Finder")
from services import storage_backend as sb


class FakeResponse:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status
    def json(self): return self._data
    def raise_for_status(self):
        if self.status_code >= 400: raise RuntimeError(f"HTTP {self.status_code}")


class FakeDB:
    """
    app_state 테이블 한 행을 흉내 낸다.

    REST 는 매번 JSON 을 새로 역직렬화해 돌려주므로 여기서도 깊은 복사를 한다.
    객체를 공유하면 '동시 쓰기로 데이터가 사라지는' 실패가 테스트에서 안 보인다
    (처음에 그렇게 만들었다가 통과해버렸다).
    """
    def __init__(self): self.row = None; self.calls = []

    def _copy(self, o): return json.loads(json.dumps(o))

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(("GET", params))
        return FakeResponse([self._copy(self.row)] if self.row else [])

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append(("POST", json["version"]))
        if self.row:                      # 이미 있으면 무시 (ignore-duplicates)
            return FakeResponse([])
        self.row = self._copy(json); return FakeResponse([self._copy(self.row)])

    def patch(self, url, params=None, headers=None, json=None, timeout=None):
        want = int(params["version"].split("eq.")[1])
        self.calls.append(("PATCH", want))
        if not self.row or int(self.row["version"]) != want:
            return FakeResponse([])       # 낙관적 잠금 충돌
        self.row = self._copy(json); return FakeResponse([self._copy(self.row)])


def empty(): return {"_meta": {}, "users": {}, "classes": {}}

def run():
    db = FakeDB()
    sb.requests = type("R", (), {"get": db.get, "post": db.post, "patch": db.patch})
    # 로컬 미러 쓰기는 이 테스트 범위 밖 — 무력화
    sb.LocalJsonBackend.write = lambda self, doc: True
    sb.LocalJsonBackend.read = lambda self, e: e()

    b = sb.SupabaseBackend("https://fake.supabase.co", "fakekey")

    print("[1] 빈 상태 읽기")
    doc = b.read(empty)
    assert doc == empty() and b._version == 0, doc
    print("    빈 문서 · version=0  OK")

    print("[2] 첫 저장 (INSERT)")
    doc["users"]["u1"] = {"name": "학생1"}
    assert b.write(doc) is True
    assert db.row["version"] == 1 and db.row["doc"]["users"]["u1"]["name"] == "학생1"
    print("    version=1 로 저장됨  OK")

    print("[3] 다시 읽기")
    b2 = sb.SupabaseBackend("https://fake.supabase.co", "fakekey")
    got = b2.read(empty)
    assert got["users"]["u1"]["name"] == "학생1" and b2._version == 1
    print("    저장한 내용 그대로 읽힘  OK")

    print("[4] 정상 갱신 (UPDATE)")
    got["users"]["u2"] = {"name": "학생2"}
    assert b2.write(got) is True and db.row["version"] == 2
    print("    version=2  OK")

    print("[5] 동시 쓰기 충돌 → 병합으로 복구")
    # 핵심: stale 은 '다시 읽지 않고' 오래된 문서를 그대로 쓴다.
    # 여기서 다시 읽어버리면 재시도 경로를 타지 않아 테스트가 무의미해진다.
    stale = sb.SupabaseBackend("https://fake.supabase.co", "fakekey")
    sd = stale.read(empty)                 # version=2 를 손에 쥔 상태
    # 그 사이 다른 사용자가 써서 version 이 3 이 된다
    other = sb.SupabaseBackend("https://fake.supabase.co", "fakekey")
    d = other.read(empty); d["users"]["u3"] = {"name": "학생3"}; other.write(d)
    assert db.row["version"] == 3
    sd["users"]["u4"] = {"name": "학생4"}
    assert stale.write(sd) is True
    saved = db.row["doc"]["users"]
    assert "u3" in saved and "u4" in saved, saved
    print(f"    충돌 후에도 u3·u4 모두 살아남음 (version={db.row['version']})  OK")

    print("[6] 네트워크 실패 → 로컬로 내려감")
    def boom(*a, **k): raise ConnectionError("네트워크 끊김")
    sb.requests = type("R", (), {"get": staticmethod(boom),
                                 "post": staticmethod(boom),
                                 "patch": staticmethod(boom)})
    b3 = sb.SupabaseBackend("https://fake.supabase.co", "fakekey")
    assert b3.write({"users": {}}) is True            # 로컬 미러 성공
    assert "ConnectionError" in sb.last_error()
    print(f"    앱은 계속 동작 · 사유 기록됨: {sb.last_error()[:40]}  OK")

    print("\n전부 통과")

run()
