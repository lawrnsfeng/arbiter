"""Martian code-review-benchmark golden set (MIT): withmartian/code-review-benchmark offline/golden_comments."""

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .. import HOME, agents, harness
from ..model import Axis, Group
from .common import (
    NON_WORD,
    PR_URL,
    RESULTS,
    apply_models,
    fbeta,
    gh,
    git,
    models,
    ratio,
    review,
    share,
    stamp,
    write_summary,
)

ROOT = HOME / "eval" / "martian"
GOLDEN = ROOT / "golden"
CACHE = ROOT / "cache"
UPSTREAM = "withmartian/code-review-benchmark"
REPOS = ("sentry", "grafana", "cal_dot_com")
CORE = frozenset({"bug", "security", "concurrency", "data", "api", "perf", "test_gap", "doc_defect"})
MAINT = frozenset({"style"})  # golden categories scored as maintainability recall (ledger MA-02)


def fetch() -> None:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    sha = gh(f"repos/{UPSTREAM}/commits/main", "--jq", ".sha").strip()
    for r in REPOS:
        path = f"repos/{UPSTREAM}/contents/offline/golden_comments/{r}.json?ref={sha}"
        meta = json.loads(gh(path))
        raw = (
            base64.b64decode(meta["content"])
            if meta.get("content")
            else gh("-H", "Accept: application/vnd.github.raw", path).encode()
        )
        (GOLDEN / f"{r}.json").write_bytes(raw)
        print(f"fetched {r}: {len(json.loads(raw))} PRs")
    source = {
        "repo": UPSTREAM,
        "sha": sha,
        "license": "MIT",
        "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (GOLDEN / "SOURCE.json").write_text(json.dumps(source, indent=1))


def _judge(finding: dict[str, Any], comment: str) -> bool | None:
    """True or False from the judge; None when the judge failed, so the pair is not scored."""
    prompt = (
        "Do these describe the same underlying issue in a code change? Answer with only "
        '{"match": true} or {"match": false}.\n\n'
        f"A (review finding): {finding['file']}:{finding['line']} {finding['claim']}\n\n"
        f"B (golden comment): {comment}"
    )
    for _ in range(2):
        try:
            v = agents.extract_json(harness.call("judge", prompt, cwd=HOME, timeout=300))
        except (harness.HarnessError, ValueError):
            continue
        if isinstance(v, dict) and isinstance(v.get("match"), bool):
            return v["match"]
    return None


def _prepare_pr(url: str) -> tuple[Path, str] | None:
    """Check out the PR head in a cached blob-less clone; returns (repo, base ref) or None if unavailable."""
    if not (m := PR_URL.match(url)):
        return None
    owner, name, n = m.groups()
    try:
        pr = json.loads(gh(f"repos/{owner}/{name}/pulls/{n}"))
    except RuntimeError:
        return None
    repo = CACHE / name
    if not repo.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "-q", "--filter=blob:none", f"https://github.com/{owner}/{name}", str(repo)], check=True
        )
    base = pr["base"]["ref"]
    for ref in (f"+refs/heads/{base}:refs/remotes/origin/{base}", f"+pull/{n}/head:refs/arbiter/pr-{n}"):
        if git(repo, "fetch", "-q", "origin", ref):
            return None
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach", f"refs/arbiter/pr-{n}"], check=True)
    return repo, f"origin/{base}"


def _score_pr(main: list[dict[str, Any]], comments: list[dict[str, Any]]) -> dict[str, Any]:
    """Core profile: a match to a non-Core comment is neutral, neither a true nor a false positive.

    A finding the judge could not assess against some comment, and that matched nothing, is "unjudged":
    a judge outage is not counted as a false positive.
    """
    core = {i for i, c in enumerate(comments) if str(c.get("category", "")).lower() in CORE}
    mi = {i for i, c in enumerate(comments) if str(c.get("category", "")).lower() in MAINT}
    verdicts = {(fi, ci): _judge(f, c["comment"]) for fi, f in enumerate(main) for ci, c in enumerate(comments)}
    matches = {pair for pair, v in verdicts.items() if v}
    matched = {fi for fi, _ in matches}
    tp = {fi for fi, ci in matches if ci in core}
    unjudged = {fi for (fi, _), v in verdicts.items() if v is None} - matched
    return {
        "findings": len(main),
        "tp": len(tp),
        "fp": len(main) - len(matched) - len(unjudged),
        "unjudged": len(unjudged),
        "core": len(core),
        "core_hit": len({ci for _, ci in matches if ci in core}),
        "maint": len(mi),
        "maint_hit": len({ci for _, ci in matches if ci in mi}),
        "evolvability_findings": sum(Axis(f["axis"]).group == Group.EVOLVABILITY for f in main),
        "categories": sorted({str(c.get("category")) for c in comments}),
    }


def run(a: argparse.Namespace) -> dict[str, Any]:
    golden = json.loads((GOLDEN / f"{a.repo}.json").read_text())[a.offset :][: a.limit or None]
    if a.pr:
        golden = [g for g in golden if any(g["url"].endswith(s) for s in a.pr)]
    settings = apply_models(a)
    ts = stamp()
    rows = []
    for pr in golden:
        url = pr["url"]
        if not (prep := _prepare_pr(url)):
            rows.append({"url": url, "status": "unavailable"})
            continue
        repo, base = prep
        r = review(repo, base, a.effort, RESULTS / "martian" / ts / NON_WORD.sub("-", url.split("github.com/")[1]))
        if r.report is None:
            rows.append({"url": url, "status": f"arbiter exit {r.exit_code}", "stderr": r.stderr[-300:]})
            continue
        rows.append({"url": url, "status": "ok", **_score_pr(r.main, pr["comments"])})
        print(
            f"{url}: findings {rows[-1]['findings']} tp {rows[-1]['tp']} "
            f"core {rows[-1]['core_hit']}/{rows[-1]['core']}",
            flush=True,
        )
    ok = [r for r in rows if r["status"] == "ok"]
    tp, fp = sum(r["tp"] for r in ok), sum(r["fp"] for r in ok)
    precision, recall = ratio(tp, tp + fp), ratio(sum(r["core_hit"] for r in ok), sum(r["core"] for r in ok))
    summary = {
        "repo": a.repo,
        "prs": len(rows),
        "ok": len(ok),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "maintainability_recall": share(sum(r["maint_hit"] for r in ok), sum(r["maint"] for r in ok)),
        "f1": fbeta(precision, recall, 1),
        "f2": fbeta(precision, recall, 2),
        **models(settings),
        "source": json.loads((GOLDEN / "SOURCE.json").read_text()),
        "rows": rows,
    }
    write_summary(f"martian-{a.repo}-{ts}", summary)
    print(
        f"{a.repo}: precision {summary['precision']} recall {summary['recall']} F1 {summary['f1']} F2 {summary['f2']}"
        f" · maintainability recall {summary['maintainability_recall']}"
    )
    return summary


def main(a: argparse.Namespace) -> int:
    match a.action:
        case "fetch":
            fetch()
        case _ if not a.repo:
            print("arbiter: eval martian run needs --repo", file=sys.stderr)
            return 2
        case _:
            run(a)
    return 0
