import io
import json
import urllib.error

import pytest

from arbiter.eval import aacr, clef


@pytest.fixture
def cf(tmp_path, monkeypatch):
    monkeypatch.setattr(clef, "USAGE", tmp_path / "usage.json")
    monkeypatch.setattr(clef, "CONFIG", tmp_path / "none.env")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")
    monkeypatch.setenv("CLOUDFLARE_AUTH_TOKEN", "tok")
    monkeypatch.delenv("ARBITER_JUDGE", raising=False)
    clef.STATS.clear()
    return tmp_path


def test_spent_budget_never_calls_the_api(cf, monkeypatch):
    (cf / "usage.json").write_text(json.dumps({clef._today(): clef.BUDGET}))

    def boom(*a, **k):
        raise AssertionError("network call past the free budget")

    monkeypatch.setattr(clef.urllib.request, "urlopen", boom)
    assert clef.same_concern("a.py:1 x", "[Code Defect] lines 1-2: y") is None
    assert clef.STATS["quota"] == 1


@pytest.mark.parametrize(("body", "calls_made"), [(b"daily free allocation used up", 1), (b"rate limited", 2)])
def test_only_the_daily_quota_error_stops_clef_for_the_day(cf, monkeypatch, body, calls_made):
    calls = []

    def fail(req, timeout):
        calls.append(req)
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, io.BytesIO(body))

    monkeypatch.setattr(clef.urllib.request, "urlopen", fail)
    assert clef.same_concern("f", "r") is None
    assert clef.same_concern("f", "r") is None
    assert len(calls) == calls_made


def test_aacr_judge_falls_back_per_finding(monkeypatch):
    refs = [(0, {"category": "Code Defect", "from_line": 1, "to_line": 2, "note": "a"}), (3, {**_ref(), "note": "b"})]
    f = {"file": "a.py", "line": 1, "claim": "c"}
    llm = []
    monkeypatch.setattr(aacr, "_llm_judge", lambda f, refs: llm.append(1) or [3])
    monkeypatch.setattr(clef, "same_concern", lambda a, b: b.endswith(": a"))
    assert aacr._judge(f, refs) == [0] and not llm
    monkeypatch.setattr(clef, "same_concern", lambda a, b: True if b.endswith(": a") else None)
    assert aacr._judge(f, refs) == [3] and llm == [1]


def _ref():
    return {"category": "Code Defect", "from_line": 1, "to_line": 2, "note": ""}
