import ast
import subprocess
from pathlib import Path

from arbiter import diff, maintain
from arbiter.model import Metric


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        check=True,
        capture_output=True,
    )


def _branches(name: str, n: int, extra: str = "") -> str:
    body = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(n))
    return f"def {name}(x):\n{body}{extra}    return x\n"


def _facts(tmp_path: Path, base: str, head: str) -> list:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "master")
    for text, msg in ((base, "base"), (head, "head")):
        (repo / "m.py").write_text(text)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", msg)
    b = diff.resolve_base(repo, "HEAD~1")
    files = [f for f in diff.collect(repo, b)["files"] if not f["excluded"]]
    return maintain.facts(repo, b, files, lambda p: (repo / p).read_text())


def test_complexity_regression_into_block_band_is_block_eligible(tmp_path):
    fs = _facts(tmp_path, "def f(x):\n    return x\n", _branches("f", 22))
    (c,) = [m for m in fs if m["metric"] == Metric.COMPLEXITY]
    assert c["qualname"] == "f" and c["base"] == 1 and c["head"] >= 22 and c["block"] is True
    assert "block-eligible" in maintain.facts_text(fs)


def test_already_over_block_line_is_not_a_regression_into_it(tmp_path):
    fs = _facts(tmp_path, _branches("f", 24), _branches("f", 25))
    (c,) = [m for m in fs if m["metric"] == Metric.COMPLEXITY]
    assert c["base"] == 25 and c["head"] == 26 and c["block"] is False


def test_unchanged_complex_function_has_no_fact(tmp_path):
    base = _branches("g", 22) + "\n\ndef h():\n    return 1\n"
    head = _branches("g", 22) + "\n\ndef h():\n    return 2\n"
    assert _facts(tmp_path, base, head) == []


def test_nesting_counts_elif_at_its_if_depth():
    src = (
        "def f(x):\n    if x:\n        pass\n    elif x > 1:\n        pass\n"
        "    elif x > 2:\n        for i in x:\n            pass\n"
    )
    fn = ast.parse(src).body[0]
    assert maintain.nesting(fn) == 2
