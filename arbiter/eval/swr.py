"""SWR-Bench (ZZR0/SWRench, MIT): 1,000 real Python PRs, half with review-confirmed issues, half clean.

Scoring reuses the official judge prompts and answer parsers from `swrbench/evaluation_struct.py` at the pinned
commit, loaded from the upstream checkout rather than copied. Only the model call is arbiter's own.
"""

import importlib.util
import json
import os
import random
import subprocess
import sys
import threading
import time
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import HOME, agents, harness

UPSTREAM = "https://github.com/ZZR0/SWRench"
PIN = "67ae1d4395ac05f800d62b0e13678eadeb9fa5c7"
ROOT = HOME / "eval" / "swr"
SRC = ROOT / "upstream"            # SWRench checkout at PIN (ignored by git)
DATA = SRC / "data" / "swr_datasets_d5c5.jsonl"
SAMPLE = ROOT / "sample.json"      # tracked: the instance ids reviewed
CACHE = ROOT / "cache"             # repository clones and per-instance worktrees (ignored by git)
RESULTS = HOME / "eval" / "results"
MAX_DIFF_LINES = 300


def fetch():
    if not SRC.exists():
        subprocess.run(["git", "clone", "-q", UPSTREAM, str(SRC)], check=True)
    subprocess.run(["git", "-C", str(SRC), "checkout", "-q", PIN], check=True)
    print(f"SWRench at {PIN}: {sum(1 for _ in DATA.open())} instances")


def _load() -> dict[str, dict]:
    return {d["instance_id"]: d for d in map(json.loads, DATA.open())}


def _diff_lines(d: dict) -> int:
    return sum(1 for c in d["pr_commits"] for f in c.get("diff") or []
               for ln in (f.get("patch") or "").splitlines() if ln[:1] in "+-")


def sample(n_issue: int, n_clean: int, seed: int):
    """Deterministic, repo-stratified sample: issue PRs with at least one functional (F.*) change, plus clean PRs."""
    data = _load()
    small = [d for d in data.values() if _diff_lines(d) <= MAX_DIFF_LINES]
    issue = [d for d in small if d["change_introduced"] and any(c["change_type"].startswith("F.") for c in d["changes"])]
    clean = [d for d in small if not d["change_introduced"]]

    def strat(pool: list[dict], k: int) -> list[str]:
        rng = random.Random(seed)
        by_repo: dict[str, list[str]] = {}
        for d in sorted(pool, key=lambda d: d["instance_id"]):
            by_repo.setdefault(d["repo"], []).append(d["instance_id"])
        for ids in by_repo.values():
            rng.shuffle(ids)
        out, repos = [], sorted(by_repo)
        while len(out) < k and any(by_repo.values()):
            for r in repos:
                if by_repo[r] and len(out) < k:
                    out.append(by_repo[r].pop())
        return out

    ids = {"issue": strat(issue, n_issue), "clean": strat(clean, n_clean)}
    SAMPLE.write_text(json.dumps({"source": UPSTREAM, "pin": PIN, "seed": seed, "max_diff_lines": MAX_DIFF_LINES,
                                  "eligible": {"issue": len(issue), "clean": len(clean)}, **ids}, indent=1))
    print(f"sampled {len(ids['issue'])} issue + {len(ids['clean'])} clean from {len(issue)} + {len(clean)} eligible")


def _official():
    """Import upstream evaluation_struct with its heavy imports stubbed (only prompts and parsers are used)."""
    for name in ("numpy", "tqdm", "utils", "loguru"):
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["tqdm"].tqdm = lambda x, **k: x
    sys.modules["utils"].run_chat = None
    sys.modules["loguru"].logger = None
    spec = importlib.util.spec_from_file_location("swr_eval", SRC / "swrbench" / "evaluation_struct.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Log:
    def error(self, *a): pass
    warning = error


def _git(*args, cwd: Path | None = None, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _prepare(d: dict) -> tuple[Path, str] | None:
    with _LOCKS_GUARD:
        lock = _LOCKS.setdefault(d["repo"], threading.Lock())
    with lock:  # one git operation per clone at a time
        return _prepare_locked(d)


def _prepare_locked(d: dict) -> tuple[Path, str] | None:
    """Worktree at the PR head (the state reviewers saw); base = parent of the first PR commit (upstream build_dataset)."""
    owner_repo = d["repo"]
    clone = CACHE / owner_repo.replace("/", "__")
    head, first = d["pr_commits"][-1]["sha"], d["pr_commits"][0]["sha"]
    if not clone.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        _git("clone", "-q", "--filter=blob:none", "--no-checkout", f"https://github.com/{owner_repo}", str(clone))
    n = d["instance_id"].rsplit("-", 1)[1]
    for ref in (head, f"+pull/{n}/head:refs/arbiter/pr-{n}"):
        if _git("cat-file", "-e", f"{head}^{{commit}}", cwd=clone, check=False).returncode == 0:
            break
        _git("fetch", "-q", "origin", ref, cwd=clone, check=False)
    if _git("cat-file", "-e", f"{head}^{{commit}}", cwd=clone, check=False).returncode:
        return None
    if _git("cat-file", "-e", f"{first}~1", cwd=clone, check=False).returncode:
        _git("fetch", "-q", "origin", first, cwd=clone, check=False)
    wt = CACHE / "wt" / d["instance_id"]
    if wt.exists():
        _git("worktree", "remove", "--force", str(wt), cwd=clone, check=False)
    _git("worktree", "add", "-q", "--detach", str(wt), head, cwd=clone)
    base = _git("rev-parse", "--verify", "--quiet", f"{first}~1", cwd=wt, check=False).stdout.strip()
    return (wt, base) if base else None


def render(report: dict) -> str:
    """arbiter's main-section findings as a plain review (what a human would read before merging)."""
    main = [f for f in report["findings"] if f.get("placement") == "main"]
    if not main:
        return "LGTM. No issues found; this PR looks good and is ready to merge."
    lines = [f"Verdict: {report['verdict'].upper()}. Issues found:"]
    for f in main:
        lines.append(f"- [{f['severity']}] {f['file']}:{f['line']}: {f['claim']}" + (f" Suggested fix: {f['fix']}" if f.get("fix") else ""))
    return "\n".join(lines)


def judge(off, d: dict, review: str) -> dict | None:
    item = {"instance": json.loads(json.dumps(d)), "pred": {"review": review.replace("\u2019", "'")}}
    item["instance"] = off.fix_change_type(item["instance"])
    issue = d["change_introduced"]
    prompt, _ = (off.create_change_pr_prompt if issue else off.create_clean_pr_prompt)(item)
    for _ in range(3):
        try:
            text = harness.call("judge", prompt, cwd=HOME, timeout=600)
            value = json.dumps(agents.extract_json(text))
        except (harness.HarnessError, ValueError):
            continue
        res = off.verify_change_pr_answer(value, item["instance"], _Log()) if issue else off.verify_clean_pr_answer(value, _Log())
        if res is not None:
            return res
    return None


def _prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return round(p, 3), round(r, 3), round(2 * p * r / (p + r), 3) if p + r else 0.0


def run(a) -> dict:
    data, smp = _load(), json.loads(SAMPLE.read_text())
    ids = (smp["issue"] + smp["clean"])[: a.limit or None]
    off = _official()
    ts = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    out_dir = RESULTS / "swr" / ts
    for flag, var in (("harness", "ARBITER_HARNESS"), ("model", "ARBITER_MODEL"), ("verify_model", "ARBITER_VERIFY_MODEL")):
        if getattr(a, flag, None):
            os.environ[var] = getattr(a, flag)

    def one(iid: str) -> dict:
        d = data[iid]
        prep = _prepare(d)
        if not prep:
            return {"instance_id": iid, "status": "unavailable"}
        wt, base = prep
        rd = out_dir / iid
        p = subprocess.run([sys.executable, "-m", "arbiter.cli", "run", "--repo", str(wt), "--base", base,
                            "--effort", a.effort, "--out", str(rd)], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, cwd=HOME)
        if p.returncode not in (0, 1) or not (rd / "report.json").exists():
            return {"instance_id": iid, "status": f"arbiter exit {p.returncode}", "stderr": p.stderr[-300:]}
        rep = json.loads((rd / "report.json").read_text())
        review = render(rep)
        res = judge(off, d, review)
        if res is None:
            return {"instance_id": iid, "status": "judge failed"}
        row = {"instance_id": iid, "status": "ok", "issue": d["change_introduced"], "verdict": rep["verdict"],
               "main": sum(f.get("placement") == "main" for f in rep["findings"]), "review": review,
               "identified_as_good": res["identified_as_good"], "pred_points": len(res["pred_points"])}
        if d["change_introduced"]:
            hit_by = {g["hit_by"] for g in res["gt_points"] if g["hit"] == "YES"}
            row.update(tp=len(hit_by), fp=len(res["pred_points"]) - len(hit_by), fn=len(res["gt_points"]) - len(hit_by),
                       gt=[{"type": g["change_category"], "hit": g["hit"]} for g in res["gt_points"]])
        print(f"{iid}: {row['verdict']} main {row['main']}" + (f" tp {row['tp']} fp {row['fp']} fn {row['fn']}"
                                                                   if row["issue"] else f" points {row['pred_points']}"), flush=True)
        return row

    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        rows = list(ex.map(one, ids))
    ok = [r for r in rows if r["status"] == "ok"]
    iss, cln = [r for r in ok if r["issue"]], [r for r in ok if not r["issue"]]
    tp, fp, fn = (sum(r[k] for r in iss) for k in ("tp", "fp", "fn"))
    f_gt = [g for r in iss for g in r["gt"] if g["type"].startswith("F.")]
    p, r_, f1 = _prf(tp, fp, fn)
    summary = {
        "benchmark": "SWR-Bench", "pin": PIN, "effort": a.effort, "model": harness.settings()["model"] or "(default)",
        "verify_model": harness.settings()["verify_model"] or "(default)", "items": len(rows), "ok": len(ok),
        "issue_prs": len(iss), "clean_prs": len(cln),
        "precision": p, "recall": r_, "f1": f1, "tp": tp, "fp": fp, "fn": fn,
        "functional_recall": round(sum(g["hit"] == "YES" for g in f_gt) / len(f_gt), 3) if f_gt else None,
        "clean_identified_good": round(sum(r["identified_as_good"] == "YES" or r["pred_points"] == 0 for r in cln) / len(cln), 3) if cln else None,
        "clean_false_points": sum(r["pred_points"] for r in cln),
        "clean_blocked": sum(r["verdict"] == "block" for r in cln), "issue_blocked": sum(r["verdict"] == "block" for r in iss),
        "unavailable": [r for r in rows if r["status"] != "ok"], "rows": rows, "runs": str(out_dir)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"swr-{ts}.json").write_text(json.dumps(summary, indent=2))
    print(f"SWR-Bench: precision {p} recall {r_} F1 {f1} · functional recall {summary['functional_recall']} · "
          f"clean judged good {summary['clean_identified_good']} ({summary['clean_false_points']} points, "
          f"{summary['clean_blocked']} blocked) · {len(ok)}/{len(rows)} ok")
    return summary


def main(a) -> int:
    if a.action == "fetch":
        fetch()
    elif a.action == "sample":
        sample(a.issue, a.clean, a.seed)
    else:
        run(a)
    return 0
