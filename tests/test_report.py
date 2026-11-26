import json

from arbiter import findings as F
from arbiter import report
from arbiter.agents import axis_owners
from arbiter.model import Axis


def _f(fid, severity, placement, **kw):
    base = {"id": fid, "axis": "logic", "group": "functional", "severity": severity, "file": "a.py", "line": 3}
    return base | {"claim": f"claim {fid}", "placement": placement} | kw


def test_report_tiers_requirements_and_patches(tmp_path):
    plan = {"repo": str(tmp_path), "base": "a" * 40, "head": "b" * 40, "effort": "standard"}
    reqs = [
        {"id": "R1", "text": "pages hold size items", "source": "none"},
        {"id": "R2", "text": "x", "source": "none"},
    ]
    (tmp_path / "intent.json").write_text(json.dumps({"claims": [], "requirements": reqs}))
    proof = {"rung": "E4", "result": "confirmed", "before": {"cmd": "pytest", "exit_code": 1}}
    patch = {"title": "minimal", "start_line": 5, "end_line": 5, "code": "x = 1"}
    allf = [
        _f("f001", "block", "main", proof=proof, addresses="R1"),
        _f("f002", "should-fix", "main", line=5, patches=[patch, patch | {"title": "cleaner"}]),
        _f("f003", "should-fix", "suspected", line=9),
        *(_f(f"n{i:02d}", "nit", "main", axis="idiom", line=20 + i, rule="E501") for i in range(12)),
    ]
    report.write(tmp_path, plan, allf, "block")
    md = (tmp_path / "report.md").read_text()
    assert "🔴 BLOCK: 1 must fix · 1 should · 1 verify · 12 optional" in md
    assert "| R1 | pages hold size items (none) | ⚠ #1 |" in md
    assert "| R2 | x (none) | ✓ no finding |" in md
    assert md.count("```suggestion") == 2
    assert "+2 more" in md
    out = json.loads((tmp_path / "report.json").read_text())
    assert out["refactor"]["needed"] is False  # idiom nits alone do not call the refactorer
    assert "## Refactor needed" not in md
    assert {(f["id"], f["tier"], f["sarif_level"]) for f in out["findings"][:3]} == {
        ("f001", "must-fix", "error"),
        ("f002", "should-fix", "warning"),
        ("f003", "verify", "warning"),
    }


def test_report_hands_clean_code_findings_to_refactorer(tmp_path):
    plan = {"repo": str(tmp_path), "base": "c" * 40, "head": "d" * 40, "effort": "standard"}
    allf = [
        _f("f001", "should-fix", "main"),
        _f("f002", "should-fix", "main", axis="design", group="evolvability", line=7),
        _f("f003", "should-fix", "suspected", axis="maintainability", group="evolvability", file="ui.ts"),
    ]
    report.write(tmp_path, plan, allf, "pass")
    md = (tmp_path / "report.md").read_text()
    assert "1 clean-code finding(s) (#2): hand off to the refactorer" in md
    assert f"--scope branch --base {'c' * 12}" in md
    out = json.loads((tmp_path / "report.json").read_text())
    assert out["refactor"] == {"needed": True, "findings": ["f002"], "scope": "branch", "base": "c" * 40}


def test_validate_candidate_drops_bad_extras():
    c = {
        "axis": "logic",
        "severity": "should-fix",
        "file": "a.py",
        "line": 3,
        "claim": "c",
        "trigger": "t",
        "evidence_lines": ["a.py:3"],
        "proof_plan": {"rung": "E4", "idea": "i"},
        "addresses": "requirement 1",
        "patches": [{"title": "t", "start_line": 3, "end_line": 3, "code": "\n".join(["x"] * 12)}],
    }
    out = F.validate_candidate(c)
    assert "addresses" not in out
    assert "patches" not in out


def test_axis_owners_reads_briefs():
    assert "A3" in axis_owners()[Axis.SECURITY]
