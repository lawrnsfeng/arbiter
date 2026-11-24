import json

import pytest

from arbiter import ArbiterExit, harness
from arbiter import findings as F
from arbiter import pipeline as P
from arbiter.harness import Tools
from arbiter.rundir import RunDir

HUNK = {"old_start": 1, "old_count": 0, "new_start": 1, "new_count": 20, "added": [], "removed": []}
PLAN = {
    "repo": "/tmp/x",
    "base": "a" * 40,
    "head": "b" * 40,
    "effort": "standard",
    "files": [{"path": "a.py", "excluded": None, "hunks": [HUNK]}],
}


def _f(fid, severity, placement):
    return {
        "id": fid,
        "axis": "logic",
        "group": "functional",
        "severity": severity,
        "file": "a.py",
        "line": 3,
        "claim": f"claim {fid}",
        "placement": placement,
    }


@pytest.fixture
def decide_run(tmp_path, monkeypatch):
    fake = tmp_path / "fake"
    fake.mkdir()
    monkeypatch.setenv("ARBITER_HARNESS", "fake")
    monkeypatch.setenv("ARBITER_FAKE_DIR", str(fake))
    for k in ("ARBITER_DECIDE_MODEL", "ARBITER_DECIDE_MAX_USD"):
        monkeypatch.delenv(k, raising=False)
    harness._resolve.cache_clear()
    run = tmp_path / "run"
    run.mkdir()
    yield RunDir(run), fake
    harness._resolve.cache_clear()


def test_decide_runs_once_per_run(decide_run):
    run, _ = decide_run
    allf = [_f("f001", "should-fix", "main")]
    P.decide(run, PLAN, {}, allf)
    assert run.load("coverage.json")["decide"]["called"] is True
    again = P.decide(run, PLAN, {}, allf)
    assert again is allf
    assert "decide: already called for this RUN; not called again" in run.load("coverage.json")["notes"]


def test_decide_effects_never_touch_blocks(decide_run):
    run, fake = decide_run
    reply = {
        "summary": "s",
        "next_action": "n",
        "links": {"f002": "R1"},
        "dismiss": [{"id": "f001", "reason": "doubt"}, {"id": "f002", "reason": "noise"}],
        "challenge": [{"id": "f001", "reason": "maybe wrong"}],
        "missed": [{"file": "a.py", "line": 5, "axis": "edge", "claim": "empty input", "addresses": "R1"}],
    }
    (fake / "decide.json").write_text(json.dumps(reply))
    must = _f("f001", "block", "main")
    should = _f("f002", "should-fix", "main")
    allf = P.decide(run, PLAN, {}, [must, should])
    assert must["placement"] == "main" and must["challenge"] == "maybe wrong"
    assert should["placement"] == "dropped" and should["addresses"] == "R1"
    missed = allf[-1]
    assert (missed["source"], missed["placement"], missed["severity"]) == ("decide", "suspected", "should-fix")
    assert F.verdict(allf) == "block"
    assert F.verdict([should, missed]) == "pass"


@pytest.mark.parametrize("model", ["anthropic/claude-fable-5", "anthropic/claude-sonnet-5-5"])
def test_decide_model_only_opus(monkeypatch, model):
    monkeypatch.setenv("ARBITER_DECIDE_MODEL", model)
    with pytest.raises(ArbiterExit) as e:
        harness.decide_model()
    assert e.value.code == 2


@pytest.fixture
def omp(monkeypatch):
    monkeypatch.setattr(harness, "omp_roles", dict)
    harness._resolve.cache_clear()
    for k in ("ARBITER_HARNESS", "ARBITER_MODEL", "ARBITER_VERIFY_MODEL", "ARBITER_DECIDE_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("ARBITER_DECIDE_MAX_USD", raising=False)
    yield
    harness._resolve.cache_clear()


def test_decide_argv_is_capped_toolless_and_advisor_off(omp):
    cmd = harness.argv("decide", Tools.NONE)
    assert cmd[cmd.index("--max-cost") + 1] == "1.00"
    assert "--no-tools" in cmd
    assert cmd[cmd.index("--config") + 1].endswith("omp-overlay.yml")


def test_finder_argv_has_overlay_and_no_opus(omp):
    cmd = harness.argv("finder", Tools.FINDER)
    assert "--config" in cmd
    assert not any("opus" in x for x in cmd)
