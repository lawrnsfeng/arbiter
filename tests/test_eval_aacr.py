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
    assert seen == ["https://github.com/o/r/pull/3"]  # not pull/30


def test_prepare_refuses_non_sha_commits_before_any_git_call(monkeypatch):
    monkeypatch.setattr(aacr, "git", lambda *a: (_ for _ in ()).throw(AssertionError("git called")))
    monkeypatch.setattr(aacr, "_snapshot", lambda *a: (_ for _ in ()).throw(AssertionError("download")))
    item = {"githubPrUrl": "https://github.com/o/r/pull/1", "source_commit": "--upload-pack=touch /tmp/x"}
    assert aacr._prepare(item | {"target_commit": "a" * 40}) is None


def test_rescore_arms_and_union_dedup(monkeypatch, tmp_path):
    data, results = tmp_path / "data", tmp_path / "results"
    data.mkdir()
    items = [
        {"githubPrUrl": "https://github.com/o/r/pull/1", "comments": [_ref("a.py", "Code Defect")] * 2},
        {"githubPrUrl": "https://github.com/o/r/pull/2", "comments": [_ref("b.py", "Code Defect")]},
    ]
    (data / "positive_samples.json").write_text(json.dumps(items))
    monkeypatch.setattr(aacr, "DATA", data)
    monkeypatch.setattr(aacr, "RESULTS", results)
    monkeypatch.setattr("arbiter.eval.common.RESULTS", results)
    runs = {
        "old": {"o-r-pull-1": [("a.py", 10, "x")], "o-r-pull-2": [("b.py", 1, "z")]},
        "new": {"o-r-pull-1": [("a.py", 11, "x2"), ("a.py", 50, "y")], "o-r-pull-2": []},
    }
    for ts, prs in runs.items():
        for name, fs in prs.items():
            d = results / "aacr" / ts / name
            d.mkdir(parents=True)
            main = [{"file": f, "line": n, "claim": c, "axis": "logic", "placement": "main"} for f, n, c in fs]
            (d / "report.json").write_text(json.dumps({"findings": main}))
    matches = {"x": [0], "x2": [0], "y": [1], "z": []}
    monkeypatch.setattr(aacr, "_judge", lambda f, refs: matches[f["claim"]])
    a = argparse.Namespace(runs=["old", "new"], label=["old", "new"], harness="fake")
    assert aacr.rescore(a) == 0
    out = json.loads(next((results).glob("aacr-rescore-*.json")).read_text())["arms"]
    got = {k: (v["findings"], v["matched_new"], v["precision"], v["recall"], v["f2"]) for k, v in out.items()}
    assert got == {
        "old": (2, 1, 0.5, 0.333, 0.357),
        "new": (2, 2, 1.0, 0.667, 0.714),
        "union": (4, 2, 0.5, 0.667, 0.625),
        "union_dedup": (3, 2, 0.667, 0.667, 0.667),
    }
