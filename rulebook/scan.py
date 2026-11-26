"""Run every rulebook rule over a set of Python files and report each rule exactly once.

Usage: python rulebook/scan.py [--rules DIR] [--json OUT] [--diff REF] PATH...
PATHs are files or directories (directories expand to every *.py recursively, sorted; nothing is ignored).
Every `ast` / `ast+semantic` detector runs on all parsed modules; `semantic` rules are reported `llm-pending` with
the rule.md the model must apply. One rule's crash is that rule's `error`, never the end of the scan.
`--diff REF` keeps only hits in code changed since REF (working tree vs REF, untracked files included): a hit counts
when the innermost def/class around it, or its own line outside any, overlaps a changed line. Detectors still see
every PATH, so cross-file rules keep their context.
Exit 2 if any rule errored or any target was unparsable, else 1 if any violation, else 0.
"""

import argparse
import ast
import json
import re
import subprocess
import sys
import traceback
from pathlib import Path

from replay import DEFAULT, detector, meta, rule_dirs
from rulekit import Hit, Module, load

HUNK = re.compile(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@")


def targets(paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in map(Path, paths):
        out += sorted(map(str, p.rglob("*.py"))) if p.is_dir() else [str(p)]
    return out


def changed(ref: str) -> dict[Path, list[tuple[int, int]]]:
    """Changed line spans per resolved .py path, working tree vs REF; an untracked file is changed throughout."""
    git = ["git", "-c", "core.quotepath=off"]
    root = Path(
        subprocess.run(
            [*git, "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
        ).stdout.strip()
    )
    diff = subprocess.run(
        [*git, "diff", "-U0", "--no-color", "--no-ext-diff", ref, "--", "*.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=root,
    ).stdout
    spans: dict[Path, list[tuple[int, int]]] = {}
    cur: list[tuple[int, int]] | None = None
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            cur = None if ln == "+++ /dev/null" else spans.setdefault((root / ln[6:]).resolve(), [])
        elif cur is not None and (h := HUNK.match(ln)):
            start, n = int(h[1]), int(h[2] or 1)
            cur.append((start, start + max(n, 1) - 1))  # n == 0: pure deletion just after line `start`
    new = subprocess.run(
        [*git, "ls-files", "--others", "--exclude-standard", "--", "*.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=root,
    ).stdout
    spans |= {(root / f).resolve(): [(1, sys.maxsize)] for f in new.splitlines()}
    return spans


def in_scope(hits: list[Hit], modules: list[Module], spans: dict[Path, list[tuple[int, int]]]) -> list[Hit]:
    trees = {Path(m.path).resolve(): m.tree for m in modules}
    kept = []
    for h in hits:
        path = Path(h.path).resolve()
        if not (sp := spans.get(path)):
            continue
        scopes = [
            n
            for n in ast.walk(trees[path])
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and n.lineno <= h.line <= (n.end_lineno or n.lineno)
        ]
        lo, hi = (h.line, h.line)
        if scopes:
            inner = max(scopes, key=lambda n: n.lineno)
            lo, hi = inner.lineno, inner.end_lineno or inner.lineno
        if any(a <= hi and lo <= b for a, b in sp):
            kept.append(h)
    return kept


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rules", default=str(DEFAULT), help="rule folders directory (default: rulebook/python)")
    ap.add_argument("--json", help="write the JSON report here instead of stdout")
    ap.add_argument("--diff", metavar="REF", help="report only hits in code changed since REF (e.g. HEAD)")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args(argv)

    files = targets(args.paths)
    modules, unparsable = load(files)
    spans = changed(args.diff) if args.diff else None
    report: list[dict] = []
    for rule in rule_dirs([args.rules]):
        m = meta(rule)
        tier = m.get("tier", "")
        entry: dict = {"id": m.get("id", rule.name), "title": m.get("title", ""), "tier": tier}
        if "ast" in tier:
            try:
                hits = sorted(detector(rule)(modules))
                if spans is not None:
                    hits = in_scope(hits, modules, spans)
                entry["status"] = "violation" if hits else "clean"
                entry["hits"] = [h._asdict() for h in hits]
            except Exception:
                entry |= {"status": "error", "hits": [], "error": traceback.format_exc().strip().splitlines()[-1]}
        else:
            entry |= {"status": "llm-pending", "hits": []}
        if "semantic" in tier:
            entry["llm"] = str(rule / "rule.md")
        report.append(entry)
        print(f"{entry['id']} {tier} {entry['status']} {len(entry['hits'])}", file=sys.stderr)

    summary: dict = {"targets": len(files), "parsed": len(modules), "unparsable": unparsable}
    if spans is not None:
        # the changed code the model must read for semantic rules: spans of every scanned file that changed
        here = {Path(f).resolve(): f for f in files}
        summary |= {"diff": args.diff, "changed": {here[p]: s for p, s in spans.items() if p in here}}
    out = json.dumps(summary | {"rules": report}, indent=1)
    if args.json:
        Path(args.json).write_text(out + "\n")
    else:
        print(out)
    if unparsable or any(r["status"] == "error" for r in report):
        return 2
    return 1 if any(r["status"] == "violation" for r in report) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
