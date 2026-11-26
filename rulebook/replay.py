"""Curation check for the owner's rulebook: replay every detector on its own examples and validate rule folders.

`ast` / `ast+semantic`: every `# expect: <ID>` line in bad.py must be hit, nothing else, and good.py must have no hit
(`# expect-llm: <ID>` lines are for the model and ignored here). `semantic`: not run (needs a model call); an owner
rule must still carry an `## LLM scan` section and at least one `# expect-llm: <ID>` case. `semgrep`: feasibility
samples only.

Usage: python rulebook/replay.py [RULES_DIR ...]   (default: rulebook/python)
Exit 1 when any rule fails.
"""

import ast
import importlib.util
import json
import re
import subprocess
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

sys.path.insert(0, str(Path(__file__).parent))
import rulekit

DEFAULT = Path(__file__).parent / "python"
SEMGREP = Path.home() / ".cache/arbiter/bin/semgrep"
EXPECT = re.compile(r"#\s*expect:\s*([\w-]+)")
EXPECT_LLM = re.compile(r"#\s*expect-llm:\s*([\w-]+)")
FIELD = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)
OWNER = re.compile(r"^R\d+$")
KEYS = {"id", "title", "tier", "severity", "status", "refs"}
TIERS = {"ast", "semantic", "ast+semantic"}

type Check = Callable[[list[rulekit.Module]], list[rulekit.Hit]]


def meta(rule: Path) -> dict[str, str]:
    head = (rule / "rule.md").read_text().split("---")[1]
    return dict(FIELD.findall(head))


def rule_dirs(dirs: list[str]) -> list[Path]:
    """Rule folders in lexical order (zero-padded R01..R89 makes that numeric); `_`-prefixed folders are skipped.

    An argument that is itself a rule folder is taken as is, so `replay.py rulebook/python/R0*` replays a slice."""
    found = set()
    for d in map(Path, dirs):
        for r in [d] if (d / "rule.md").exists() else d.iterdir():
            if r.is_dir() and not r.name.startswith("_") and (r / "rule.md").exists():
                found.add(r)
    return sorted(found)


def detector(rule: Path) -> Check:
    """Import the rule's check.py under a name unique to its folder and return its `check`."""
    spec = importlib.util.spec_from_file_location(f"rulebook_check_{rule.name.replace('-', '_')}", rule / "check.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {rule / 'check.py'}")
    mod: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check


def semgrep(rule: Path, paths: list[str]) -> set[tuple[str, int]]:
    """Hits as (path, line). Raises when semgrep skipped a target: a silent skip is a missed occurrence."""
    # explicit targets, no size or time limit: semgrep's default ignores skip e.g. build/ directories
    cmd = [SEMGREP, "--quiet", "--json", "--metrics=off", "--disable-nosem", "--timeout", "0"]
    cmd += ["--max-target-bytes", "0", "--config", rule / "check.yml", *paths]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    data = json.loads(out.stdout)
    if data.get("errors") or len(data["paths"]["scanned"]) != len(paths):
        raise RuntimeError(
            f"{rule.name}: semgrep scanned {len(data['paths']['scanned'])}/{len(paths)}, "
            f"errors {[e.get('message', '')[:120] for e in data.get('errors', [])]}"
        )
    # one occurrence = one region: drop matches nested inside another match of the same rule
    spans = [(r["path"], r["start"]["offset"], r["end"]["offset"], r["start"]["line"]) for r in data["results"]]
    return {
        (p, ln)
        for p, s, e, ln in spans
        if not any(q == p and qs <= s and e <= qe and (qs, qe) != (s, e) for q, qs, qe, _ in spans)
    }


def run_ast(rule: Path, path: str) -> set[tuple[str, int]]:
    modules, failed = rulekit.load([path])
    if failed:
        raise RuntimeError(f"unparsable: {failed}")
    return {(h.path, h.line) for h in detector(rule)(modules)}


def structure(rule: Path, m: dict[str, str]) -> list[str]:
    """Layout defects of an owner rule folder (see rulebook/README.md)."""
    errs = []
    if set(m) != KEYS:
        errs.append(f"front matter keys {sorted(m)} != {sorted(KEYS)}")
    tier = m.get("tier", "")
    if tier not in TIERS:
        errs.append(f"tier {tier!r} not in {sorted(TIERS)}")
    if m.get("severity") != "should-fix":
        errs.append("severity must be should-fix")
    if m.get("status") not in {"ok", "unclear"}:
        errs.append(f"status {m.get('status')!r} not ok|unclear")
    num = re.match(r"^R(\d{2})-[a-z0-9]+(-[a-z0-9]+)*$", rule.name)
    if not num or f"R{int(num[1])}" != m.get("id"):
        errs.append(f"folder {rule.name} does not match id {m.get('id')}")
    if (rule / "check.py").exists() != ("ast" in tier):
        errs.append("check.py must exist iff tier contains ast")
    body = (rule / "rule.md").read_text().split("---", 2)[2]
    heads = re.findall(r"^## (.+?)\s*$", body, re.MULTILINE)
    errs += [f"missing ## {h}" for h in ("Rule", "Incorrect", "Correct") if h not in heads]
    if ("LLM scan" in heads) != ("semantic" in tier):
        errs.append("## LLM scan must exist iff tier contains semantic")
    for f in ("bad.py", "good.py"):
        try:
            ast.parse((rule / f).read_text(encoding="utf-8"), f)
        except (OSError, SyntaxError, ValueError) as e:
            errs.append(f"{f}: {e}")
    return errs


def replay(rule: Path) -> bool:
    m = meta(rule)
    rid, tier = m["id"], m["tier"]
    owner = bool(OWNER.match(rid))
    if owner and (errs := structure(rule, m)):
        print(f"{rid} [{tier}]: FAIL")
        for e in errs:
            print(f"  {e}")
        return False
    bad, good = rule / "bad.py", rule / "good.py"
    lines = bad.read_text().splitlines()
    if tier == "semantic":
        if not owner:
            print(f"{rid} [semantic]: model-checked, not replayed here -> PASS")
            return True
        llm = sum(1 for ln in lines if (x := EXPECT_LLM.search(ln)) and x[1] == rid)
        print(f"{rid} [semantic]: {llm} expect-llm case(s) -> {'PASS' if llm else 'FAIL'}")
        return llm > 0
    want = {(str(bad), i) for i, ln in enumerate(lines, 1) if (x := EXPECT.search(ln)) and x[1] == rid}
    try:
        if tier == "semgrep":
            got_bad, got_good = semgrep(rule, [str(bad)]), semgrep(rule, [str(good)])
        else:
            got_bad, got_good = run_ast(rule, str(bad)), run_ast(rule, str(good))
    except Exception:
        print(f"{rid} [{tier}]: FAIL {traceback.format_exc().strip().splitlines()[-1]}")
        return False
    ok = got_bad == want and not got_good
    print(
        f"{rid} [{tier}]: bad {len(got_bad & want)}/{len(want)} hit, extra {len(got_bad - want)}, "
        f"good {len(got_good)} false hit(s) -> {'PASS' if ok else 'FAIL'}"
    )
    for p, ln in sorted((want - got_bad) | (got_bad - want) | got_good):
        print(f"  {'missed' if (p, ln) in want else 'unexpected'} {p}:{ln}")
    return ok


def main(dirs: list[str]) -> int:
    rules = rule_dirs(dirs or [str(DEFAULT)])
    results = [replay(r) for r in rules]
    passed = sum(results)
    print(f"{len(results)} rules: {passed} pass, {len(results) - passed} fail")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
