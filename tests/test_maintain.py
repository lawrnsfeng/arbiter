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


def _facts(tmp_path: Path, base: str | dict, head: str | dict) -> list:
    """base/head: m.py's text, or {path: text}; a path missing from head is deleted."""
    base, head = ({"m.py": x} if isinstance(x, str) else x for x in (base, head))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "master")
    for files, msg in ((base, "base"), (head, "head")):
        for p in set(base) - set(files):
            (repo / p).unlink(missing_ok=True)
        for p, text in files.items():
            (repo / p).write_text(text)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", msg)
    b = diff.resolve_base(repo, "HEAD~1")
    files = [f for f in diff.collect(repo, b)["files"] if not f["excluded"]]
    return maintain.facts(repo, b, files, lambda p: (repo / p).read_text() if (repo / p).exists() else None)


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


def test_file_pushed_over_1000_lines_is_block_eligible(tmp_path):
    fs = _facts(tmp_path, "x = 1\n" * 990, "x = 1\n" * 1010)
    (f,) = [m for m in fs if m["metric"] == Metric.FILE_LINES]
    assert (f["base"], f["head"], f["block"]) == (990, 1010, True)


def test_moved_function_is_measured_against_its_old_home(tmp_path):
    base = {"a.py": _branches("dispatch", 24), "b.py": "y = 2\n"}
    head = {"b.py": "y = 2\n\n\n" + _branches("dispatch", 25)}
    (c,) = [m for m in _facts(tmp_path, base, head) if m["metric"] == Metric.COMPLEXITY]
    assert c["path"] == "b.py" and c["base"] == 25 and c["block"] is False


def test_renamed_file_keeps_its_base(tmp_path):
    body = "\n".join(f"v{i} = {i}" for i in range(40)) + "\n\n\n"
    base = {"m.py": body + _branches("f", 24)}
    head = {"n.py": body + _branches("f", 25)}
    (c,) = [m for m in _facts(tmp_path, base, head) if m["metric"] == Metric.COMPLEXITY]
    assert c["path"] == "n.py" and c["base"] == 25 and c["block"] is False


def test_unparseable_base_yields_no_facts(tmp_path):
    assert _facts(tmp_path, "def f(:\n", _branches("f", 25)) == []
