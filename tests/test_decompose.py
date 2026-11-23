"""Hierarchical units (--decompose hier|hier-split): deterministic, no model calls."""

import subprocess
from itertools import pairwise

import pytest
from test_core import RANGES, cand, ffile, mkrepo

from arbiter import cli, decompose, diff, plan, units
from arbiter import findings as F
from arbiter.model import Decompose, SymbolChange


def func(name: str, lines: int) -> str:
    """A function of exactly `lines` lines, the last one blank."""
    return f"def {name}(x):\n" + "    x += 1\n" * (lines - 3) + "    return x\n\n"


def build(tmp_path, head: dict[str, str], base: dict[str, str] | None = None, mode=Decompose.HIER_SPLIT):
    repo = mkrepo(tmp_path, base or {"README": "x\n"}, head)
    d = diff.collect(repo, "master~1")
    tree = set(diff.git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())

    def read(path: str) -> str | None:
        p = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{path}"], capture_output=True, text=True)
        return p.stdout if p.returncode == 0 else None

    files = [f for f in d["files"] if not f["excluded"]]
    us = units.build(files, tree, mode=mode, read=read, budget=150)
    return repo, d, files, us, read


def lines_of(us, path):
    return [r for u in us for p in u["files"] if p["path"] == path for r in p.get("lines", [])]


def test_single_hunk_new_file_split_into_sub_ranges(tmp_path):
    src = "".join(func(f"f{i}", 20) for i in range(20))  # 400 lines, one hunk
    repo, d, files, us, _ = build(tmp_path, {"pkg/__init__.py": "", "pkg/big.py": src})
    big = [u for u in us if any(p["path"] == "pkg/big.py" for p in u["files"])]
    assert len(big) >= 3 and all(u["churn"] <= 150 for u in us)
    rs = sorted(lines_of(big, "pkg/big.py"))
    assert rs[0][0] == 1 and rs[-1][1] == 400  # covers the hunk exactly once, no gap or overlap
    assert all(a[1] + 1 == b[0] for a, b in pairwise(rs))
    assert all((lo - 1) % 20 == 0 for lo, _ in rs)  # every split falls on a definition boundary
    # the rendered unit diff shows its own sub-range plus context, not the whole 400-line hunk
    p = {"repo": str(repo), "base": d["base"], "head": d["head"]}
    u = big[1]
    f = next(f for f in files if f["path"] == "pkg/big.py")
    u["ranges"] = {x["path"]: decompose.piece_ranges(x, f) for x in u["files"]}
    lo, hi = u["ranges"]["pkg/big.py"][0]
    text = plan.unit_diff(p, u)
    shown = [int(ln.split()[0]) for ln in text.splitlines() if ln.strip()[:1].isdigit()]
    assert min(shown) == max(lo - plan.UNIT_CONTEXT, 1) and max(shown) == min(hi + plan.UNIT_CONTEXT, 400)
    assert plan.GAP in text


def test_class_over_budget_splits_by_method(tmp_path):
    methods = "".join(
        f"    def m{i}(self):\n" + "        self.x += 1\n" * 22 + "        return 1\n\n" for i in range(8)
    )
    src = "class Big:\n    x = 0\n\n" + methods  # 3 header lines + 8 methods of 25 lines
    repo, _, files, us, read = build(tmp_path, {"big.py": src})
    assert len(us) >= 2 and all(u["churn"] <= 150 for u in us)
    method_starts = {4 + 25 * i for i in range(8)}
    assert all(lo in method_starts | {1} for lo, _ in lines_of(us, "big.py"))
    # a method-level unit carries the class header as read-only context: signatures, never bodies
    u = next(u for u in us if lines_of([u], "big.py")[0][0] != 1)
    u["ranges"] = {"big.py": decompose.piece_ranges(u["files"][0], files[0])}
    ctx = decompose.context_map(repo, decompose.Code(set(), read), u, {"big.py": files[0]}, [])
    assert "enclosing class header" in ctx and "class Big():" in ctx and "x = 0" in ctx
    assert "self.x += 1" not in ctx


def test_floor_merges_small_sibling(tmp_path):
    # greedy packing leaves [100] [140] [20]; the 20-line leftover joins the 100-line sibling
    *_, us, _ = build(tmp_path, {"m.py": func("a", 100) + func("b", 140) + func("c", 20)})
    assert sorted(u["churn"] for u in us) == [120, 140]


def test_syntax_error_falls_back_to_hunks(tmp_path):
    *_, us, _ = build(tmp_path, {"bad.py": "def broken(:\n" + "    x = 1\n" * 299})
    assert len(us) == 1 and us[0]["churn"] == 300 and "lines" not in us[0]["files"][0]


def test_manifest_signature_change_and_pure_rename(tmp_path):
    base = {"m.py": "def a(x):\n    return x + 1\n\n\ndef old(y):\n    return y * 2\n"}
    head = {"m.py": "def a(x, z=0):\n    return x + 1\n\n\ndef new(y):\n    return y * 2\n"}
    repo, d, files, _, read = build(tmp_path, head, base)
    syms = {s["qualname"]: s for s in decompose.manifest(repo, d["base"], files, decompose.Code(set(), read))}
    assert set(syms) == {"a", "new"}  # the rename is one entry, not a removal plus an addition
    assert syms["a"]["change"] == SymbolChange.SIGNATURE
    assert (syms["a"]["old_sig"], syms["a"]["new_sig"]) == ("def a(x)", "def a(x, z=0)")
    assert syms["new"]["change"] == SymbolChange.RENAMED and syms["new"]["old_qualname"] == "old"


def test_pure_rename_gets_no_finder_unit(tmp_path):
    repo, d, files, _, read = build(
        tmp_path, {"r.py": "def new(y):\n    return y * 2\n"}, {"r.py": "def old(y):\n    return y * 2\n"}
    )
    syms = decompose.manifest(repo, d["base"], files, decompose.Code(set(), read))
    assert [s["change"] for s in syms] == [SymbolChange.RENAMED]
    skip = decompose.rename_spans(syms)
    assert units.build(files, {"r.py"}, mode=Decompose.HIER, read=read, skip=skip) == []


def test_widened_merge_accepts_cross_unit_finding_only_in_hier():
    ranges = {**RANGES, "u02": {"b.py": [(20, 30)]}}
    c = cand(file="b.py", line=25, evidence_lines=["b.py:25"])  # raised by u01's finder, on u02's hunk
    ocr, rejected = F.merge([dict(c)], ranges, set())
    assert not ocr and "outside the unit" in rejected[0]["reject_reason"]
    pr = {"a.py": [(8, 12)], "b.py": [(20, 30)]}
    hier, _ = F.merge([dict(c)], ranges, set(), widen=pr)
    assert len(hier) == 1 and hier[0]["unit"] == "u01"
    outside, rejected = F.merge([cand(file="b.py", line=90, evidence_lines=["b.py:90"])], ranges, set(), widen=pr)
    assert not outside and "every changed hunk" in rejected[0]["reject_reason"]


def test_root_cause_clustering_on_changed_signature():
    sym = {"path": "a.py", "qualname": "f", "kind": "function", "change": SymbolChange.SIGNATURE, "lines": (8, 12)}
    pr = {"a.py": [(8, 12)], "b.py": [(20, 30)], "c.py": [(1, 5)]}
    stale = [
        cand(file="b.py", line=22, evidence_lines=["b.py:22", "a.py:8"], unit="u02"),
        cand(file="c.py", line=3, evidence_lines=["c.py:3", "a.py:9"], unit="u03", agent="A2"),
    ]
    merged, _ = F.merge([dict(c) for c in stale], {}, set(), widen=pr, symbols=[sym])
    assert len(merged) == 1 and merged[0]["locations"] == ["c.py:3"] and merged[0]["agents"] == ["A1a", "A2"]
    plain, _ = F.merge([dict(c) for c in stale], {}, set(), widen=pr)
    assert len(plain) == 2


@pytest.mark.parametrize(
    "files",
    [
        [ffile(f"a{i}.py", [50]) for i in range(3)],
        [ffile("a.py", [100]), ffile("b.py", [100]), ffile("c.py", [100])],
        [ffile("a.py", [100, 100, 100, 100])],
        [ffile(f"m{i // 4}/f{i}.py", [10]) for i in range(12)],
    ],
)
def test_ocr_mode_is_todays_units(files):
    us = units.build(files, set(), mode=Decompose.OCR, read=lambda _: "x = 1\n")
    assert us == units.build(files, set()) and not any("lines" in p for u in us for p in u["files"])


def test_decompose_flag_and_env(monkeypatch):
    assert cli._parser().parse_args(["plan", "r"]).decompose == "ocr"
    monkeypatch.setenv("ARBITER_DECOMPOSE", "hier")
    assert cli._parser().parse_args(["plan", "r"]).decompose == "hier"
    with pytest.raises(SystemExit) as e:
        cli._parser().parse_args(["run", "--decompose", "bogus"])
    assert e.value.code == 2
