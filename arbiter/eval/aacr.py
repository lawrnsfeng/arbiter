"""AACR-Bench (Apache-2.0): alibaba/aacr-bench dataset/v2 positive samples, scored with its file-level semantic
coverage."""

import argparse
import ast
import json
import re
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
from ..findings import NEAR
from ..model import Axis, Group
from . import clef
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
SHA = re.compile(r"[0-9a-f]{40}")


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


def _neutralize(git_dir: Path, origin: str) -> None:
    """A snapshot's .git is third-party: its hooks and config (core.fsmonitor, core.hooksPath, filter drivers)
    would run code on checkout, diff and status. Keep the objects and refs; replace the rest."""
    shutil.rmtree(git_dir / "hooks", ignore_errors=True)
    (git_dir / "config").write_text(
        "[core]\n\trepositoryformatversion = 0\n\tbare = false\n"
        f'[remote "origin"]\n\turl = {origin}\n\tfetch = +refs/heads/*:refs/remotes/origin/*\n'
    )


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
        if not (staging / dest.name / ".git").is_dir():
            return False
        _neutralize(staging / dest.name / ".git", f"https://github.com/{owner}/{name}")
        (staging / dest.name).rename(dest)
        return True
    except (urllib.error.URLError, OSError, tarfile.TarError):
        return False
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _prepare(item: dict[str, Any]) -> tuple[Path, str] | None:
    """Check out the PR's target commit from AACR's snapshot (else a blob-less GitHub clone); returns
    (repo, base sha) or None."""
    # the AACR converter maps source_commit to the base and target_commit to the head
    base, head = item["source_commit"], item["target_commit"]
    if not (m := PR_URL.match(item["githubPrUrl"])) or not (SHA.fullmatch(base) and SHA.fullmatch(head)):
        return None  # dataset text reaches git argv and paths
    owner, name, n = m.groups()
    repo = CACHE / f"{owner}__{name}"
    if not repo.exists() and not _snapshot(owner, name, repo):
        url = f"https://github.com/{owner}/{name}"
        if subprocess.run(["git", "clone", "-q", "--filter=blob:none", url, str(repo)]).returncode:
            return None
    if not (_has(repo, head) and _has(repo, base)) and git(repo, "fetch", "-q", "origin", head, base):
        git(repo, "fetch", "-q", "origin", f"+pull/{n}/head:refs/arbiter/pr-{n}")
    if not (_has(repo, head) and _has(repo, base)) or git(repo, "checkout", "-q", "--detach", head):
        return None
    return repo, base


def _ref_text(c: dict[str, Any]) -> str:
    return f"[{c['category']}] lines {c['from_line']}-{c['to_line']}: {c['note']}"


def _judge(f: dict[str, Any], refs: list[tuple[int, dict[str, Any]]]) -> list[int] | None:
    """Indices (into the PR's comments) of the references that express the finding's concern; None when the
    judge failed twice, so the finding is "unjudged", not a false positive. Clef answers each pair first while the
    free allowance lasts; any pair it cannot answer confidently sends the whole finding to the LLM judge."""
    finding = f"{f['file']}:{f['line']} {f['claim']} {f.get('fix', '')}".strip()
    matches = []
    for i, c in refs:
        if (same := clef.same_concern(finding, _ref_text(c))) is None:
            return _llm_judge(f, refs)
        if same:
            matches.append(i)
    return matches


def _llm_judge(f: dict[str, Any], refs: list[tuple[int, dict[str, Any]]]) -> list[int] | None:
    listing = "\n".join(f"{k}. {_ref_text(c)}" for k, (_, c) in enumerate(refs, 1))
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


def _judge_all(main: list[dict[str, Any]], comments: list[dict[str, Any]]) -> list[list[int] | None]:
    """Per finding: the reference indices it matches ([] when its file has no reference), None when unjudged."""
    by_file: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for i, c in enumerate(comments):
        by_file.setdefault(_norm(c["path"]), []).append((i, c))
    return [_judge(f, refs) if (refs := by_file.get(_norm(f["file"]))) else [] for f in main]


def _tally(
    main: list[dict[str, Any]], matches: list[list[int] | None], comments: list[dict[str, Any]]
) -> dict[str, Any]:
    """File-level semantic coverage (AACR-Bench docs/metrics.md): a finding is a true positive only when it covers a
    reference no earlier finding covered."""
    covered: set[int] = set()
    matched_new = unjudged = 0
    for m in matches:
        if m is None:
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


def _score(main: list[dict[str, Any]], comments: list[dict[str, Any]]) -> dict[str, Any]:
    return _tally(main, _judge_all(main, comments), comments)


def _dedup(main: list[dict[str, Any]], matches: list[list[int] | None]) -> tuple[list[Any], list[list[int] | None]]:
    """Findings at one file within NEAR lines become one, uniting their matches (unjudged only if all were)."""
    out: list[dict[str, Any]] = []
    out_m: list[list[int] | None] = []
    for f, m in zip(main, matches, strict=True):
        k = next((k for k, g in enumerate(out) if g["file"] == f["file"] and abs(g["line"] - f["line"]) <= NEAR), None)
        if k is None:
            out.append(f)
            out_m.append(m)
        elif m is not None:
            out_m[k] = sorted({*(out_m[k] or []), *m})
    return out, out_m


def _arm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    findings, unjudged = sum(r["findings"] for r in rows), sum(r["unjudged"] for r in rows)
    matched, covered, refs = (sum(r[k] for r in rows) for k in ("matched_new", "covered", "refs"))
    precision, recall = ratio(matched, findings - unjudged), ratio(covered, refs)
    return {
        "findings": findings,
        "unjudged": unjudged,
        "matched_new": matched,
        "covered": covered,
        "refs": refs,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": fbeta(precision, recall, 1),
        "f2": fbeta(precision, recall, 2),
    }


def rescore(a: argparse.Namespace) -> int:
    """Judge several finished runs in one pass (same judge, same day), plus the union of the first two."""
    labels: list[str] = a.label or []
    if not a.runs or len(labels) != len(a.runs):
        print("arbiter: rescore needs --runs TS... and one --label per run", file=sys.stderr)
        return 2
    items = {
        NON_WORD.sub("-", i["githubPrUrl"].split("github.com/")[1]): i
        for i in json.loads((DATA / "positive_samples.json").read_text())
    }
    dirs = dict(zip(labels, (RESULTS / "aacr" / ts for ts in a.runs), strict=True))
    names = {lab: {p.name for p in d.iterdir() if (p / "report.json").exists()} for lab, d in dirs.items()}
    keep = []
    for name in sorted(set().union(*names.values())):
        if name not in items:
            print(f"skipped {name}: not an AACR v2 PR")
        elif missing := [lab for lab in labels if name not in names[lab]]:
            print(f"skipped {name}: missing in {missing[0]}")
        else:
            keep.append(name)
    settings = apply_models(a)
    judged: dict[str, dict[str, tuple[list[Any], list[list[int] | None]]]] = {}
    dismissed: dict[str, int] = {}
    dismissed_matched: dict[str, int] = {}
    for lab, d in dirs.items():
        for name in keep:
            findings = json.loads((d / name / "report.json").read_text()).get("findings", [])
            main = [f for f in findings if f.get("placement") == "main"]
            judged.setdefault(lab, {})[name] = (main, _judge_all(main, _comments(items[name])))
            # a decide dismissal that matches a reference is a decide error
            final = json.loads(p.read_text()) if (p := d / name / "final.json").exists() else []
            gone = [f for f in final if str(f.get("placement_reason", "")).startswith("decision: ")]
            dismissed[lab] = dismissed.get(lab, 0) + len(gone)
            dismissed_matched[lab] = dismissed_matched.get(lab, 0) + sum(
                bool(m) for m in _judge_all(gone, _comments(items[name]))
            )
    arms = {lab: {n: _tally(*judged[lab][n], _comments(items[n])) for n in keep} for lab in labels}
    if len(labels) >= 2:
        x, y = labels[:2]
        union = {n: ([*judged[x][n][0], *judged[y][n][0]], [*judged[x][n][1], *judged[y][n][1]]) for n in keep}
        arms["union"] = {n: _tally(*union[n], _comments(items[n])) for n in keep}
        arms["union_dedup"] = {n: _tally(*_dedup(*union[n]), _comments(items[n])) for n in keep}
    scored = {lab: _arm(list(rows.values())) | {"rows": rows} for lab, rows in arms.items()}
    summary = {
        "benchmark": "AACR-Bench rescore",
        "runs": dict(zip(labels, a.runs, strict=True)),
        "prs": keep,
        "arms": scored,
        "decide_dismissed": {
            lab: {"dismissed": n, "matched_a_reference": dismissed_matched[lab]} for lab, n in dismissed.items()
        },
        **models(settings),
    }
    write_summary(f"aacr-rescore-{stamp()}", summary)
    print("| Arm | Findings | Matched | Precision | Recall | F1 | F2 |\n|---|---|---|---|---|---|---|")
    for lab, s in scored.items():
        cells = [lab, *(s[k] for k in ("findings", "matched_new", "precision", "recall", "f1", "f2"))]
        print("| " + " | ".join(map(str, cells)) + " |")
    return 0


def _recall(ok: list[dict[str, Any]], keep: Any) -> float | None:
    pairs = [hc for r in ok for cat, hc in r["by_category"].items() if keep(cat)]
    return share(sum(h for h, _ in pairs), sum(t for _, t in pairs))


def run(a: argparse.Namespace) -> int:
    if not (DATA / "positive_samples.json").exists():
        print("arbiter: run `arbiter eval aacr fetch` first", file=sys.stderr)
        return 2
    items = json.loads((DATA / "positive_samples.json").read_text())
    if a.lang:
        langs = {LANGS.get(x, x) for x in a.lang.split(",")}
        items = [i for i in items if i["project_main_language"] in langs]
    if a.pr:
        items = [i for i in items if any(i["githubPrUrl"].endswith(s) for s in a.pr)]
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
        case "rescore":
            return rescore(a)
        case _:
            return run(a)
