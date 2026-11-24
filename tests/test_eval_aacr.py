import argparse
import json

from arbiter.eval import aacr, martian


def _ref(path: str, category: str) -> dict:
    return {"path": path, "category": category, "from_line": 1, "to_line": 2, "note": "n"}


def _finding(file: str) -> dict:
    return {"file": file, "line": 1, "claim": "c", "axis": "logic"}


def test_score_counts_a_reference_once_and_skips_files_without_refs(monkeypatch):
    calls = []

    def judge(f, refs):
        calls.append(f["file"])
        return [refs[0][0]]

    monkeypatch.setattr(aacr, "_judge", judge)
    comments = [_ref("a.py", "Code Defect"), _ref("./a.py", aacr.MAINT), _ref("b.py", aacr.MAINT)]
    s = aacr._score([_finding("a.py"), _finding("a.py"), _finding("c.py")], comments)
    assert s["matched_new"] == 1 and s["covered"] == 1 and s["refs"] == 3
    assert calls == ["a.py", "a.py"]
    assert s["by_category"] == {"Code Defect": [1, 1], aacr.MAINT: [0, 2]}


def test_score_unjudged_is_not_a_false_positive(monkeypatch):
    monkeypatch.setattr(aacr, "_judge", lambda f, refs: None)
    s = aacr._score([_finding("a.py")], [_ref("a.py", "Code Defect")])
    assert s["unjudged"] == 1 and s["matched_new"] == 0


def test_martian_pr_filter(monkeypatch, tmp_path):
    golden = tmp_path / "golden"
    golden.mkdir()
    rows = [{"url": f"https://github.com/o/r/pull/{n}", "comments": []} for n in (3, 30, 4)]
    (golden / "sentry.json").write_text(json.dumps(rows))
    (golden / "SOURCE.json").write_text("{}")
    seen = []
    monkeypatch.setattr(martian, "GOLDEN", golden)
    monkeypatch.setattr(martian, "_prepare_pr", seen.append)  # records the URL, returns None (unavailable)
    monkeypatch.setattr(martian, "apply_models", lambda a: martian.harness.Settings("fake", "m", "v"))
    monkeypatch.setattr(martian, "write_summary", lambda *a: None)
    a = argparse.Namespace(repo="sentry", offset=0, limit=None, pr=["r/pull/3"], effort="standard")
    martian.run(a)
    assert seen == ["https://github.com/o/r/pull/3", "https://github.com/o/r/pull/30"]
