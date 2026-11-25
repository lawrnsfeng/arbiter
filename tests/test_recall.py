import json
import subprocess

from arbiter import cochange
from arbiter import pipeline as P
from arbiter.rundir import RunDir


def _commit(repo, *files):
    for f in files:
        p = repo / f
        p.write_text(p.read_text() + "x\n" if p.exists() else "x\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "c"], check=True)


def test_cochange_counts_and_min_count(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "commit.gpgsign", "false"], check=True)
    for _ in range(3):
        _commit(tmp_path, "a.py", "b.py")
    _commit(tmp_path, "a.py", "c.py")
    tree = {"a.py", "b.py", "c.py"}
    assert cochange.neighbours(tmp_path, ["a.py"], tree) == {"a.py": [("b.py", 3)]}


HUNK = {"old_start": 1, "old_count": 0, "new_start": 1, "new_count": 20, "added": [], "removed": []}
PLAN = {
    "effort": "standard",
    "decompose": "ocr",
    "files": [{"path": "a.py", "excluded": None, "hunks": [HUNK]}],
    "units": [{"id": "u01", "ranges": {"a.py": [[1, 20]]}}],
}
HIT = {"path": "a.py", "line": 5, "tool": "bandit", "rule": "B602", "msg": "subprocess call with shell=True"}
AGENT = {
    "axis": "logic",
    "severity": "should-fix",
    "file": "a.py",
    "line": 6,
    "claim": "c",
    "trigger": "t",
    "evidence_lines": ["a.py:6"],
    "proof_plan": {"rung": "E4", "idea": "i"},
    "agent": "A1a",
    "pass": 0,
    "unit": "u01",
}


def _merge(tmp_path, raw):
    run = RunDir(tmp_path)
    run.save("gates.json", {"findings": [], "analyzer_hits": [HIT]})
    run.save("raw.json", raw)
    P.merge(run, PLAN)
    return json.loads((tmp_path / "candidates.json").read_text())


def test_sast_hit_becomes_candidate(tmp_path, monkeypatch):
    monkeypatch.setenv("ARBITER_SAST_CANDIDATES", "1")
    cands = _merge(tmp_path, [])
    assert [c["agents"] for c in cands] == [["sast"]]
    assert cands[0]["axis"] == "security" and cands[0]["id"] == "f001"


def test_sast_candidates_off_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("ARBITER_SAST_CANDIDATES", raising=False)
    assert _merge(tmp_path, []) == []


def test_sast_hit_covered_by_agent_finding_adds_none(tmp_path, monkeypatch):
    monkeypatch.setenv("ARBITER_SAST_CANDIDATES", "1")
    cands = _merge(tmp_path, [AGENT])
    assert [c["agents"] for c in cands] == [["A1a"]]
