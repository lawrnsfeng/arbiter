"""Seeded corpus: eval/seeded/<lang>/<NN-slug>/{base/, change.patch, expected.json}."""

import argparse
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from .. import HOME
from ..findings import NEAR
from ..model import EVOLVABILITY
from .common import RESULTS, apply_models, models, ratio, review, stamp, write_summary

CORPUS = HOME / "eval" / "seeded"
REPOS = RESULTS / "repos"


class Expected(TypedDict):
    file: str
    line: int
    axes: list[str]
    must: NotRequired[bool]
    note: NotRequired[str]


def _git(repo: Path, *args: str) -> None:
    # fixture repos are throwaway eval inputs; they are not signed
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.name=arbiter-eval",
            "-c",
            "user.email=arbiter-eval@localhost",
            *args,
        ],
        check=True,
        capture_output=True,
    )


def case_name(case: Path) -> str:
    return f"{case.parent.name}-{case.name}"


def cases(lang: str | None, case: str | None) -> list[Path]:
    out = sorted(p for p in CORPUS.glob("*/*") if (p / "expected.json").exists())
    if lang:
        out = [p for p in out if p.parent.name in lang.split(",")]
    if case:
        out = [p for p in out if case in case_name(p)]
    return out


def build(cs: list[Path]) -> None:
    REPOS.mkdir(parents=True, exist_ok=True)
    for c in cs:
        dst = REPOS / case_name(c)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(c / "base", dst)
        subprocess.run(["git", "init", "-q", "-b", "master", str(dst)], check=True)
        _git(dst, "add", "-A")
        _git(dst, "commit", "-q", "-m", "chore: initial project")
        _git(dst, "apply", str((c / "change.patch").resolve()))
        _git(dst, "add", "-A")
        _git(dst, "commit", "-q", "-m", "feat: extend the project")
        print(f"built {dst}")


def _matches(f: dict[str, Any], expected: list[Expected]) -> list[int]:
    """Same file, within NEAR lines, and one of the finding's axes is expected there."""
    axes = set(f.get("axes") or [f["axis"]])
    return [
        i
        for i, e in enumerate(expected)
        if e["file"] == f["file"] and abs(e["line"] - f["line"]) <= NEAR and axes & set(e["axes"])
    ]


def score(case: Path, report: dict[str, Any] | None) -> dict[str, Any]:
    expected: list[Expected] = json.loads((case / "expected.json").read_text())
    if report is None:
        return {"case": case_name(case), "error": "no report", "expected": len(expected)}
    main = [f for f in report["findings"] if f.get("placement") == "main"]
    hit = {i for f in main for i in _matches(f, expected)}
    must = [i for i, e in enumerate(expected) if e.get("must", True)]
    evo = [i for i in must if set(expected[i]["axes"]) & EVOLVABILITY]
    unmatched = [f for f in main if not _matches(f, expected)]
    return {
        "case": case_name(case),
        "clean": not expected,
        "verdict": report["verdict"],
        "main": len(main),
        "matched": len(main) - len(unmatched),
        "fp": len(unmatched),
        "must": len(must),
        "must_hit": sum(i in hit for i in must),
        "evo_must": len(evo),
        "evo_hit": sum(i in hit for i in evo),
        "suspected": sum(f.get("placement") == "suspected" for f in report["findings"]),
        "fp_findings": [f"{f['file']}:{f['line']} [{f['axis']}] {f['claim'][:100]}" for f in unmatched],
    }


def run(cs: list[Path], a: argparse.Namespace) -> dict[str, Any]:
    ts = stamp()
    out_dir = RESULTS / "runs" / ts
    settings = apply_models(a)

    def one(c: Path) -> dict[str, Any]:
        repo = REPOS / case_name(c)
        if not repo.exists():
            return {"case": repo.name, "error": "not built; run `arbiter eval seeded build`"}
        r = review(repo, "HEAD~1", a.effort, out_dir / repo.name)
        row = score(c, r.report) | {"exit_code": r.exit_code, "wall_s": r.wall_s}
        print(
            f"{row['case']}: exit {r.exit_code} main {row.get('main')} matched {row.get('matched')} "
            f"must {row.get('must_hit')}/{row.get('must')}",
            flush=True,
        )
        return row

    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        rows = list(ex.map(one, cs))
    scored = [r for r in rows if "error" not in r]
    bug, clean = [r for r in scored if not r["clean"]], [r for r in scored if r["clean"]]
    summary = {
        "effort": a.effort,
        **models(settings),
        "precision": round(ratio(sum(r["matched"] for r in bug), sum(r["main"] for r in scored)), 3),
        "recall": round(ratio(sum(r["must_hit"] for r in bug), sum(r["must"] for r in bug)), 3),
        "evolvability_recall": round(ratio(sum(r["evo_hit"] for r in bug), sum(r["evo_must"] for r in bug)), 3),
        "clean_case_findings": sum(r["main"] for r in clean),
        "suspected": sum(r["suspected"] for r in scored),
        "errors": [r for r in rows if "error" in r],
        "rows": rows,
        "runs": str(out_dir),
    }
    path = write_summary(f"seeded-{ts}", summary)
    print("\n| case | verdict | main | matched | must hit | suspected |\n|---|---|---|---|---|---|")
    for r in rows:
        print(
            f"| {r['case']} | {r.get('verdict', r.get('error'))} | {r.get('main')} | {r.get('matched')} | "
            f"{r.get('must_hit')}/{r.get('must')} | {r.get('suspected')} |"
        )
    print(
        f"\nprecision {summary['precision']} · recall {summary['recall']} · "
        f"evolvability recall {summary['evolvability_recall']} · "
        f"clean-case findings {summary['clean_case_findings']} · results {path}"
    )
    return summary


def main(a: argparse.Namespace) -> int:
    cs = cases(a.lang, a.case)
    match a.action:
        case "build":
            build(cs)
        case _:
            run(cs, a)
    return 0
