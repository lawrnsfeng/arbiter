"""AACR-Bench (Apache-2.0): alibaba/aacr-bench dataset/v2 positive samples, scored with its file-level semantic
coverage."""

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .. import HOME, agents, harness
from ..model import Axis, Group
from .common import NON_WORD, PR_URL, RESULTS, apply_models, fbeta, gh, git, models, ratio, review, stamp, write_summary

ROOT = HOME / "eval" / "aacr"
DATA = ROOT / "data"
CACHE = ROOT / "cache"
UPSTREAM = "alibaba/aacr-bench"
DATASET = "dataset/v2/positive_samples.json"
# the PR target commits live only in AACR's repository snapshots, not on GitHub (evaluation/repo_utils.py)
SNAPSHOTS = "Alibaba-Aone/aacr-bench-repos"
DOWNLOAD_TIMEOUT_S = 600
MAINT = "Maintainability and Readability"
LANGS = {"python": "Python", "ts": "TypeScript", "go": "Go", "rust": "Rust"}


def fetch() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    sha = gh(f"repos/{UPSTREAM}/commits/main", "--jq", ".sha").strip()
    with urllib.request.urlopen(f"https://huggingface.co/api/datasets/{SNAPSHOTS}", timeout=60) as r:
        snap_rev = json.load(r)["sha"]
    raw = gh("-H", "Accept: application/vnd.github.raw", f"repos/{UPSTREAM}/contents/{DATASET}?ref={sha}")
    (DATA / "positive_samples.json").write_text(raw)
    source = {
        "repo": UPSTREAM,
        "sha": sha,
        "license": "Apache-2.0",
        "snapshots": {"repo": SNAPSHOTS, "revision": snap_rev},
        "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (DATA / "SOURCE.json").write_text(json.dumps(source, indent=1))
    print(f"fetched {len(json.loads(raw))} PRs")


def _comments(item: dict[str, Any]) -> list[dict[str, Any]]:
    c = item["comments"]
    return ast.literal_eval(c) if isinstance(c, str) else c


def _has(repo: Path, rev: str) -> bool:
    return git(repo, "cat-file", "-e", f"{rev}^{{commit}}") == 0


def _snapshot(owner: str, name: str, dest: Path) -> bool:
    """Download and extract AACR's pinned repository snapshot (a git repo) to dest."""
    rev = json.loads((DATA / "SOURCE.json").read_text())["snapshots"]["revision"]
    url = f"https://huggingface.co/datasets/{SNAPSHOTS}/resolve/{rev}/repos/{owner}__{name}.tar.gz"
    CACHE.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".extract-", dir=CACHE))
    try:
        archive = staging / "repo.tar.gz"
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as r, archive.open("wb") as out:
            shutil.copyfileobj(r, out)
        with tarfile.open(archive) as t:
            t.extractall(staging, filter="data")  # rejects absolute paths, `..` and links leaving staging
        if not (staging / dest.name / ".git").exists():
            return False
        (staging / dest.name).rename(dest)
        return True
    except (urllib.error.URLError, OSError, tarfile.TarError):
        return False
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _prepare(item: dict[str, Any]) -> tuple[Path, str] | None:
    """Check out the PR's target commit from AACR's snapshot (else a blob-less GitHub clone); returns
    (repo, base sha) or None."""
    if not (m := PR_URL.match(item["githubPrUrl"])):
        return None
    owner, name, n = m.groups()
    repo = CACHE / f"{owner}__{name}"
    if not repo.exists() and not _snapshot(owner, name, repo):
        url = f"https://github.com/{owner}/{name}"
        if subprocess.run(["git", "clone", "-q", "--filter=blob:none", url, str(repo)]).returncode:
            return None
    # the AACR converter maps source_commit to the base and target_commit to the head
    base, head = item["source_commit"], item["target_commit"]
    if not (_has(repo, head) and _has(repo, base)) and git(repo, "fetch", "-q", "origin", head, base):
        git(repo, "fetch", "-q", "origin", f"+pull/{n}/head:refs/arbiter/pr-{n}")
    if not (_has(repo, head) and _has(repo, base)) or git(repo, "checkout", "-q", "--detach", head):
        return None
    return repo, base


def _judge(f: dict[str, Any], refs: list[tuple[int, dict[str, Any]]]) -> list[int] | None:
    """Indices (into the PR's comments) of the references that express the finding's concern; None when the
    judge failed twice, so the finding is "unjudged", not a false positive."""
    listing = "\n".join(
        f"{k}. [{c['category']}] lines {c['from_line']}-{c['to_line']}: {c['note']}" for k, (_, c) in enumerate(refs, 1)
    )
    prompt = (
        "Which reference comments express the same concern as the generated review comment? Answer with only "
        '{"matches": [numbers]}, an empty list if none.\n\n'
        f"Generated: {f['file']}:{f['line']} {f['claim']} {f.get('fix', '')}\n\nReferences:\n{listing}"
    )
    for _ in range(2):
        try:
            v = agents.extract_json(harness.call("judge", prompt, cwd=HOME, timeout=300))
        except (harness.HarnessError, ValueError):
            continue
        if isinstance(v, dict) and isinstance(v.get("matches"), list):
            return [refs[k - 1][0] for k in v["matches"] if isinstance(k, int) and 1 <= k <= len(refs)]
    return None


def _norm(path: str) -> str:
    return path.removeprefix("./")


def _score(main: list[dict[str, Any]], comments: list[dict[str, Any]]) -> dict[str, Any]:
    """File-level semantic coverage (AACR-Bench docs/metrics.md): a finding matches the references in its file
    the judge names; a finding is a true positive only when it covers a reference no earlier finding covered."""
    by_file: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for i, c in enumerate(comments):
        by_file.setdefault(_norm(c["path"]), []).append((i, c))
    covered: set[int] = set()
    matched_new = unjudged = 0
    for f in main:
        if not (refs := by_file.get(_norm(f["file"]))):
            continue
        if (m := _judge(f, refs)) is None:
            unjudged += 1
            continue
        matched_new += bool(set(m) - covered)
        covered |= set(m)
    by_category: dict[str, list[int]] = {}
    for i, c in enumerate(comments):
        hit_total = by_category.setdefault(c["category"], [0, 0])
        hit_total[0] += i in covered
        hit_total[1] += 1
    return {
        "findings": len(main),
        "matched_new": matched_new,
        "unjudged": unjudged,
        "refs": len(comments),
        "covered": len(covered),
        "by_category": by_category,
        "evolvability_findings": sum(Axis(f["axis"]).group == Group.EVOLVABILITY for f in main),
    }


def _recall(ok: list[dict[str, Any]], keep: Any) -> float:
    pairs = [hc for r in ok for cat, hc in r["by_category"].items() if keep(cat)]
    return round(ratio(sum(h for h, _ in pairs), sum(t for _, t in pairs)), 3)


def run(a: argparse.Namespace) -> int:
    if not (DATA / "positive_samples.json").exists():
        print("arbiter: run `arbiter eval aacr fetch` first", file=sys.stderr)
        return 2
    items = json.loads((DATA / "positive_samples.json").read_text())
    if a.lang:
        langs = {LANGS.get(x, x) for x in a.lang.split(",")}
        items = [i for i in items if i["project_main_language"] in langs]
    if a.pr:
        items = [i for i in items if any(s in i["githubPrUrl"] for s in a.pr)]
    items = items[: a.limit or None]
    settings = apply_models(a)
    ts = stamp()
    rows = []
    for item in items:
        url = item["githubPrUrl"]
        if not (prep := _prepare(item)):
            rows.append({"url": url, "status": "unavailable"})
            continue
        repo, base = prep
        r = review(repo, base, a.effort, RESULTS / "aacr" / ts / NON_WORD.sub("-", url.split("github.com/")[1]))
        if r.report is None:
            rows.append({"url": url, "status": f"arbiter exit {r.exit_code}", "stderr": r.stderr[-300:]})
            continue
        rows.append({"url": url, "status": "ok", "verdict": r.report.get("verdict"), "wall_s": r.wall_s})
        rows[-1] |= _score(r.main, _comments(item))
        print(
            f"{url}: findings {rows[-1]['findings']} new {rows[-1]['matched_new']} "
            f"covered {rows[-1]['covered']}/{rows[-1]['refs']}",
            flush=True,
        )
    ok = [r for r in rows if r["status"] == "ok"]
    precision = ratio(sum(r["matched_new"] for r in ok), sum(r["findings"] - r["unjudged"] for r in ok))
    recall = ratio(sum(r["covered"] for r in ok), sum(r["refs"] for r in ok))
    cats = sorted({c for r in ok for c in r["by_category"]})
    summary = {
        "benchmark": "AACR-Bench",
        "effort": a.effort,
        "prs": len(rows),
        "ok": len(ok),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": fbeta(precision, recall, 1),
        "f2": fbeta(precision, recall, 2),
        "recall_by_category": {c: _recall(ok, lambda x, c=c: x == c) for c in cats},
        "maintainability_recall": _recall(ok, lambda x: x == MAINT),
        "functional_recall": _recall(ok, lambda x: x != MAINT),
        "evolvability_findings": sum(r["evolvability_findings"] for r in ok),
        **models(settings),
        "source": json.loads((DATA / "SOURCE.json").read_text()),
        "rows": rows,
    }
    write_summary(f"aacr-{ts}", summary)
    print(
        f"AACR: precision {summary['precision']} recall {summary['recall']} F1 {summary['f1']} F2 {summary['f2']} · "
        f"maintainability recall {summary['maintainability_recall']} · "
        f"functional recall {summary['functional_recall']}"
    )
    return 0


def main(a: argparse.Namespace) -> int:
    match a.action:
        case "fetch":
            fetch()
            return 0
        case _:
            return run(a)
