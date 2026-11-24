"""SWR-Bench (ZZR0/SWRench, MIT): 1,000 real Python PRs, half with review-confirmed issues, half clean.

Scoring reuses the official judge prompts and answer parsers from `swrbench/evaluation_struct.py` at the pinned
commit, loaded from the upstream checkout rather than copied. Only the model call is arbiter's own.
"""

import argparse
import importlib.util
import json
import random
import subprocess
import sys
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .. import HOME, agents, harness
from .common import RESULTS, apply_models, fbeta, models, ratio, review, share, stamp, write_summary

UPSTREAM = "https://github.com/ZZR0/SWRench"
PIN = "67ae1d4395ac05f800d62b0e13678eadeb9fa5c7"
ROOT = HOME / "eval" / "swr"
SRC = ROOT / "upstream"  # SWRench checkout at PIN (ignored by git)
DATA = SRC / "data" / "swr_datasets_d5c5.jsonl"
SAMPLE = ROOT / "sample.json"  # tracked: the instance ids reviewed
CACHE = ROOT / "cache"  # repository clones and per-instance worktrees (ignored by git)
MAX_DIFF_LINES = 300
JUDGE_ATTEMPTS = 3

type Instance = dict[str, Any]


def fetch() -> None:
    if not SRC.exists():
        subprocess.run(["git", "clone", "-q", UPSTREAM, str(SRC)], check=True)
    subprocess.run(["git", "-C", str(SRC), "checkout", "-q", PIN], check=True)
    with DATA.open() as f:
        print(f"SWRench at {PIN}: {sum(1 for _ in f)} instances")


def _load() -> dict[str, Instance]:
    with DATA.open() as f:
        return {d["instance_id"]: d for d in map(json.loads, f)}


def _diff_lines(d: Instance) -> int:
    return sum(
        1
        for c in d["pr_commits"]
        for f in c.get("diff") or []
        for ln in (f.get("patch") or "").splitlines()
        if ln.startswith(("+", "-"))
    )


def _stratified(pool: list[Instance], k: int, seed: int) -> list[str]:
    """Round-robin over repositories, each repository's PRs shuffled with the fixed seed."""
    rng = random.Random(seed)
    by_repo: dict[str, list[str]] = {}
    for d in sorted(pool, key=lambda d: d["instance_id"]):
        by_repo.setdefault(d["repo"], []).append(d["instance_id"])
    for ids in by_repo.values():
        rng.shuffle(ids)
    out: list[str] = []
    while len(out) < k and any(by_repo.values()):
        for repo in sorted(by_repo):
            if by_repo[repo] and len(out) < k:
                out.append(by_repo[repo].pop())
    return out


def sample(n_issue: int, n_clean: int, seed: int) -> None:
    """Issue PRs with at least one functional (F.*) change, plus clean PRs; small diffs only."""
    small = [d for d in _load().values() if _diff_lines(d) <= MAX_DIFF_LINES]
    issue = [
        d for d in small if d["change_introduced"] and any(c["change_type"].startswith("F.") for c in d["changes"])
    ]
    clean = [d for d in small if not d["change_introduced"]]
    ids = {"issue": _stratified(issue, n_issue, seed), "clean": _stratified(clean, n_clean, seed)}
    SAMPLE.write_text(
        json.dumps(
            {
                "source": UPSTREAM,
                "pin": PIN,
                "seed": seed,
                "max_diff_lines": MAX_DIFF_LINES,
                "eligible": {"issue": len(issue), "clean": len(clean)},
                **ids,
            },
            indent=1,
        )
    )
    print(f"sampled {len(ids['issue'])} issue + {len(ids['clean'])} clean from {len(issue)} + {len(clean)} eligible")


def _official() -> types.ModuleType:
    """Import upstream evaluation_struct with its heavy imports stubbed: only its prompts and parsers are used."""
    stubs: dict[str, dict[str, object]] = {
        "numpy": {},
        "tqdm": {"tqdm": lambda x, **_: x},
        "utils": {"run_chat": None},
        "loguru": {"logger": None},
    }
    for name, attrs in stubs.items():
        mod = sys.modules.setdefault(name, types.ModuleType(name))
        for k, v in attrs.items():
            setattr(mod, k, v)
    spec = importlib.util.spec_from_file_location("swr_eval", SRC / "swrbench" / "evaluation_struct.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Quiet:
    """Logger stand-in for the upstream parsers."""

    def error(self, *_: object) -> None:
        pass

    warning = error


GIT_TIMEOUT_S = 900


class Unavailable(Exception):
    """The instance cannot be reviewed: its repository, commits or worktree could not be prepared."""


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=GIT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(["git", *args], 124, "", f"timed out after {GIT_TIMEOUT_S}s")


def _must(p: subprocess.CompletedProcess[str], what: str) -> subprocess.CompletedProcess[str]:
    if p.returncode:
        raise Unavailable(f"{what}: {p.stderr.strip()[:200]}")
    return p


def _has(clone: Path, rev: str) -> bool:
    return _git("cat-file", "-e", rev, cwd=clone).returncode == 0


_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _prepare(d: Instance) -> tuple[Path, str]:
    with _LOCKS_GUARD:
        lock = _LOCKS.setdefault(d["repo"], threading.Lock())
    with lock:  # one git operation per clone at a time
        return _prepare_locked(d)


def _prepare_locked(d: Instance) -> tuple[Path, str]:
    """Worktree at the PR head (the state reviewers saw); base = parent of the first PR commit (upstream build)."""
    clone = CACHE / d["repo"].replace("/", "__")
    head, first = d["pr_commits"][-1]["sha"], d["pr_commits"][0]["sha"]
    if not clone.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/{d['repo']}"
        _must(_git("clone", "-q", "--filter=blob:none", "--no-checkout", url, str(clone)), "clone")
    n = d["instance_id"].rsplit("-", 1)[1]
    for ref in (head, f"+pull/{n}/head:refs/arbiter/pr-{n}"):
        if _has(clone, f"{head}^{{commit}}"):
            break
        _git("fetch", "-q", "origin", ref, cwd=clone)
    if not _has(clone, f"{head}^{{commit}}"):
        raise Unavailable(f"head {head[:12]} not fetchable")
    if not _has(clone, f"{first}~1"):
        _git("fetch", "-q", "origin", first, cwd=clone)
    wt = CACHE / "wt" / d["instance_id"]
    _git("worktree", "remove", "--force", str(wt), cwd=clone)
    _git("worktree", "prune", cwd=clone)
    _must(_git("worktree", "add", "-q", "--detach", str(wt), head, cwd=clone), "worktree add")
    base = _git("rev-parse", "--verify", "--quiet", f"{first}~1", cwd=wt).stdout.strip()
    if not base:
        raise Unavailable(f"parent of first PR commit {first[:12]} not fetchable")
    return wt, base


def render(report: dict[str, Any]) -> str:
    """arbiter's main-section findings as a plain review (what a human would read before merging)."""
    main = [f for f in report["findings"] if f.get("placement") == "main"]
    if not main:
        return "LGTM. No issues found; this PR looks good and is ready to merge."
    lines = [f"Verdict: {report['verdict'].upper()}. Issues found:"]
    lines += [
        f"- [{f['severity']}] {f['file']}:{f['line']}: {f['claim']}"
        + (f" Suggested fix: {f['fix']}" if f.get("fix") else "")
        for f in main
    ]
    return "\n".join(lines)


def judge(off: types.ModuleType, d: Instance, review_text: str) -> dict[str, Any] | str:
    """The parsed official judge answer, or the last failure reason after JUDGE_ATTEMPTS tries."""
    item = {
        "instance": off.fix_change_type(json.loads(json.dumps(d))),
        "pred": {"review": review_text.replace("\u2019", "'")},
    }
    issue = d["change_introduced"]
    prompt, _ = (off.create_change_pr_prompt if issue else off.create_clean_pr_prompt)(item)
    reason = "no attempt"
    for _ in range(JUDGE_ATTEMPTS):
        try:
            value = json.dumps(agents.extract_json(harness.call("judge", prompt, cwd=HOME, timeout=600)))
        except (harness.HarnessError, ValueError) as e:
            reason = str(e)[:200]
            continue
        res = (
            off.verify_change_pr_answer(value, item["instance"], _Quiet())
            if issue
            else off.verify_clean_pr_answer(value, _Quiet())
        )
        if res is not None:
            return res
        reason = "answer failed the official parser"
    return reason


def _row(iid: str, d: Instance, report: dict[str, Any], review_text: str, res: dict[str, Any]) -> dict[str, Any]:
    row = {
        "instance_id": iid,
        "status": "ok",
        "issue": d["change_introduced"],
        "verdict": report["verdict"],
        "main": sum(f.get("placement") == "main" for f in report["findings"]),
        "review": review_text,
        "identified_as_good": res["identified_as_good"],
        "pred_points": len(res["pred_points"]),
    }
    if d["change_introduced"]:
        hit_by = {g["hit_by"] for g in res["gt_points"] if g["hit"] == "YES"}
        row |= {
            "tp": len(hit_by),
            "fp": len(res["pred_points"]) - len(hit_by),
            "fn": len(res["gt_points"]) - len(hit_by),
            "gt": [{"type": g["change_category"], "hit": g["hit"]} for g in res["gt_points"]],
        }
    return row


def run(a: argparse.Namespace) -> dict[str, Any]:
    data, smp = _load(), json.loads(SAMPLE.read_text())
    ids = [*smp["issue"], *smp["clean"]]
    if a.skip_scored:  # continue an earlier run: only the PRs it did not score
        done = {r["instance_id"] for r in json.loads(Path(a.skip_scored).read_text())["rows"] if r["status"] == "ok"}
        ids = [i for i in ids if i not in done]
    ids = ids[: a.limit or None]
    off = _official()
    settings = apply_models(a)
    ts = stamp()
    out_dir = RESULTS / "swr" / ts

    def one(iid: str) -> dict[str, Any]:
        d = data[iid]
        try:
            prep = _prepare(d)
        except Unavailable as e:
            return {"instance_id": iid, "status": "unavailable", "reason": str(e)}
        r = review(*prep, a.effort, out_dir / iid)
        if r.report is None:
            return {"instance_id": iid, "status": f"arbiter exit {r.exit_code}", "stderr": r.stderr[-300:]}
        text = render(r.report)
        if isinstance(res := judge(off, d, text), str):
            return {"instance_id": iid, "status": "judge failed", "reason": res}
        row = _row(iid, d, r.report, text, res)
        detail = f"tp {row['tp']} fp {row['fp']} fn {row['fn']}" if row["issue"] else f"points {row['pred_points']}"
        print(f"{iid}: {row['verdict']} main {row['main']} {detail}", flush=True)
        return row

    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        rows = list(ex.map(one, ids))
    ok = [r for r in rows if r["status"] == "ok"]
    iss, cln = [r for r in ok if r["issue"]], [r for r in ok if not r["issue"]]
    tp, fp, fn = (sum(r[k] for r in iss) for k in ("tp", "fp", "fn"))
    functional = [g for r in iss for g in r["gt"] if g["type"].startswith("F.")]
    evolvability = [g for r in iss for g in r["gt"] if g["type"].startswith("E.")]
    precision, recall = ratio(tp, tp + fp), ratio(tp, tp + fn)
    summary = {
        "benchmark": "SWR-Bench",
        "pin": PIN,
        "effort": a.effort,
        **models(settings),
        "items": len(rows),
        "ok": len(ok),
        "issue_prs": len(iss),
        "clean_prs": len(cln),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": fbeta(precision, recall, 1),
        "functional_recall": round(ratio(sum(g["hit"] == "YES" for g in functional), len(functional)), 3),
        "evolvability_recall": share(sum(g["hit"] == "YES" for g in evolvability), len(evolvability)),
        "clean_identified_good": round(
            ratio(sum(r["identified_as_good"] == "YES" or not r["pred_points"] for r in cln), len(cln)), 3
        ),
        "clean_false_points": sum(r["pred_points"] for r in cln),
        "clean_blocked": sum(r["verdict"] == "block" for r in cln),
        "issue_blocked": sum(r["verdict"] == "block" for r in iss),
        "unavailable": [r for r in rows if r["status"] != "ok"],
        "rows": rows,
        "runs": str(out_dir),
    }
    write_summary(f"swr-{ts}", summary)
    print(
        f"SWR-Bench: precision {summary['precision']} recall {summary['recall']} F1 {summary['f1']} · "
        f"functional recall {summary['functional_recall']} · evolvability recall {summary['evolvability_recall']} · "
        f"clean judged good {summary['clean_identified_good']} "
        f"({summary['clean_false_points']} points, {summary['clean_blocked']} blocked) · {len(ok)}/{len(rows)} ok"
    )
    return summary


def main(a: argparse.Namespace) -> int:
    match a.action:
        case "fetch":
            fetch()
        case "sample":
            sample(a.issue, a.clean, a.seed)
        case _:
            run(a)
    return 0
