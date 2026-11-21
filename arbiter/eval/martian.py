"""Martian code-review-benchmark golden set (MIT): withmartian/code-review-benchmark offline/golden_comments."""

import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from .. import HOME, agents, harness

ROOT = HOME / "eval" / "martian"
GOLDEN = ROOT / "golden"
CACHE = ROOT / "cache"
RESULTS = HOME / "eval" / "results"
UPSTREAM = "withmartian/code-review-benchmark"
REPOS = ("sentry", "grafana", "cal_dot_com")
CORE = {"bug", "security", "concurrency", "data", "api", "perf", "test_gap", "doc_defect"}


def _gh(*args: str) -> str:
    p = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"gh api {' '.join(args)}: {p.stderr.strip()[:200]}")
    return p.stdout


def fetch():
    GOLDEN.mkdir(parents=True, exist_ok=True)
    sha = _gh(f"repos/{UPSTREAM}/commits/main", "--jq", ".sha").strip()
    for r in REPOS:
        meta = json.loads(_gh(f"repos/{UPSTREAM}/contents/offline/golden_comments/{r}.json?ref={sha}"))
        raw = base64.b64decode(meta["content"]) if meta.get("content") else _gh(
            "-H", "Accept: application/vnd.github.raw", f"repos/{UPSTREAM}/contents/offline/golden_comments/{r}.json?ref={sha}").encode()
        (GOLDEN / f"{r}.json").write_bytes(raw)
        print(f"fetched {r}: {len(json.loads(raw))} PRs")
    (GOLDEN / "SOURCE.json").write_text(json.dumps({"repo": UPSTREAM, "sha": sha, "license": "MIT",
                                                    "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=1))


def _judge(finding: dict, comment: str) -> bool:
    prompt = ("Do these describe the same underlying issue in a code change? Answer with only "
              '{"match": true} or {"match": false}.\n\n'
              f"A (review finding): {finding['file']}:{finding['line']} {finding['claim']}\n\nB (golden comment): {comment}")
    for _ in range(2):
        try:
            v = agents.extract_json(harness.call("judge", prompt, cwd=HOME, timeout=300))
            if isinstance(v, dict) and isinstance(v.get("match"), bool):
                return v["match"]
        except (harness.HarnessError, ValueError):
            pass
    return False


def _prepare_pr(url: str) -> tuple[Path, str] | None:
    m = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        return None
    owner, name, n = m.groups()
    try:
        pr = json.loads(_gh(f"repos/{owner}/{name}/pulls/{n}"))
    except RuntimeError:
        return None
    repo = CACHE / name
    if not repo.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", f"https://github.com/{owner}/{name}", str(repo)],
                       check=True)
    base = pr["base"]["ref"]
    for ref in (f"+refs/heads/{base}:refs/remotes/origin/{base}", f"+pull/{n}/head:refs/arbiter/pr-{n}"):
        if subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin", ref]).returncode:
            return None
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach", f"refs/arbiter/pr-{n}"], check=True)
    return repo, f"origin/{base}"


def run(a) -> dict:
    golden = json.loads((GOLDEN / f"{a.repo}.json").read_text())[: a.limit or None]
    for flag, var in (("harness", "ARBITER_HARNESS"), ("model", "ARBITER_MODEL"), ("verify_model", "ARBITER_VERIFY_MODEL")):
        if getattr(a, flag, None):
            os.environ[var] = getattr(a, flag)
    ts = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    rows = []
    for pr in golden:
        url = pr["url"]
        prep = _prepare_pr(url)
        if not prep:
            rows.append({"url": url, "status": "unavailable"})
            continue
        repo, base = prep
        out = RESULTS / "martian" / ts / re.sub(r"\W+", "-", url.split("github.com/")[1])
        p = subprocess.run([sys.executable, "-m", "arbiter.cli", "run", "--repo", str(repo), "--base", base,
                            "--effort", a.effort, "--out", str(out)], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, cwd=HOME)
        if not (out / "report.json").exists():
            rows.append({"url": url, "status": f"arbiter exit {p.returncode}", "stderr": p.stderr[-300:]})
            continue
        main = [f for f in json.loads((out / "report.json").read_text())["findings"] if f.get("placement") == "main"]
        comments = pr["comments"]
        core = [i for i, c in enumerate(comments) if str(c.get("category", "")).lower() in CORE]
        matches = {(fi, ci) for fi, f in enumerate(main) for ci, c in enumerate(comments) if _judge(f, c["comment"])}
        tp = {fi for fi, ci in matches if ci in core}
        neutral = {fi for fi, ci in matches} - tp
        fp = len(main) - len(tp) - len(neutral)
        rows.append({"url": url, "status": "ok", "findings": len(main), "tp": len(tp), "fp": fp,
                     "core": len(core), "core_hit": len({ci for _, ci in matches if ci in core}),
                     "categories": sorted({str(c.get("category")) for c in comments})})
        print(f"{url}: findings {len(main)} tp {len(tp)} core {rows[-1]['core_hit']}/{len(core)}", flush=True)
    ok = [r for r in rows if r["status"] == "ok"]
    tp, fp = sum(r["tp"] for r in ok), sum(r["fp"] for r in ok)
    hit, core = sum(r["core_hit"] for r in ok), sum(r["core"] for r in ok)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = hit / core if core else 0.0
    fb = lambda b: (1 + b * b) * prec * rec / (b * b * prec + rec) if prec + rec else 0.0
    summary = {"repo": a.repo, "prs": len(rows), "ok": len(ok), "precision": round(prec, 3), "recall": round(rec, 3),
               "f1": round(fb(1), 3), "f2": round(fb(2), 3), "model": os.environ.get("ARBITER_MODEL", "(default)"),
               "source": json.loads((GOLDEN / "SOURCE.json").read_text()), "rows": rows}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"martian-{a.repo}-{ts}.json").write_text(json.dumps(summary, indent=2))
    print(f"{a.repo}: precision {summary['precision']} recall {summary['recall']} F1 {summary['f1']} F2 {summary['f2']}")
    return summary


def main(a) -> int:
    if a.action == "fetch":
        fetch()
        return 0
    if not a.repo:
        print("arbiter: eval martian run needs --repo", file=sys.stderr)
        return 2
    run(a)
    return 0
