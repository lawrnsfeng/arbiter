"""Seeded corpus: eval/seeded/<lang>/<NN-slug>/{base/, change.patch, expected.json}."""

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import HOME

CORPUS = HOME / "eval" / "seeded"
RESULTS = HOME / "eval" / "results"
REPOS = RESULTS / "repos"


def _git(repo: Path, *args: str):
    # fixture repos are throwaway eval inputs; they are not signed
    subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "user.name=arbiter-eval",
                    "-c", "user.email=arbiter-eval@localhost", *args], check=True, capture_output=True)


def cases(lang: str | None, case: str | None) -> list[Path]:
    out = sorted(p for p in CORPUS.glob("*/*") if (p / "expected.json").exists())
    if lang:
        out = [p for p in out if p.parent.name in lang.split(",")]
    if case:
        out = [p for p in out if case in f"{p.parent.name}-{p.name}"]
    return out


def build(cs: list[Path]):
    REPOS.mkdir(parents=True, exist_ok=True)
    for c in cs:
        dst = REPOS / f"{c.parent.name}-{c.name}"
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


def _match(f: dict, exp: list[dict]) -> list[int]:
    return [i for i, e in enumerate(exp) if e["file"] == f["file"] and abs(e["line"] - f["line"]) <= 3
            and set(f.get("axes") or [f["axis"]]) & set(e["axes"])]


def score(case: Path, report: dict | None) -> dict:
    exp = json.loads((case / "expected.json").read_text())
    if report is None:
        return {"case": f"{case.parent.name}-{case.name}", "error": "no report", "expected": len(exp)}
    main = [f for f in report["findings"] if f.get("placement") == "main"]
    matched = [f for f in main if _match(f, exp)]
    hit = {i for f in main for i in _match(f, exp)}
    must = [i for i, e in enumerate(exp) if e.get("must", True)]
    return {"case": f"{case.parent.name}-{case.name}", "clean": not exp, "verdict": report["verdict"],
            "main": len(main), "matched": len(matched), "fp": len(main) - len(matched),
            "must": len(must), "must_hit": len([i for i in must if i in hit]),
            "suspected": sum(f.get("placement") == "suspected" for f in report["findings"]),
            "fp_findings": [f"{f['file']}:{f['line']} [{f['axis']}] {f['claim'][:100]}" for f in main if not _match(f, exp)]}


def run(cs: list[Path], a) -> dict:
    ts = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    out_dir = RESULTS / "runs" / ts
    env = dict(os.environ)
    for flag, var in (("harness", "ARBITER_HARNESS"), ("model", "ARBITER_MODEL"), ("verify_model", "ARBITER_VERIFY_MODEL")):
        if getattr(a, flag, None):
            env[var] = getattr(a, flag)

    def one(c: Path) -> dict:
        repo = REPOS / f"{c.parent.name}-{c.name}"
        if not repo.exists():
            return {"case": repo.name, "error": "not built; run `arbiter eval seeded build`"}
        rd = out_dir / repo.name
        t0 = time.monotonic()
        p = subprocess.run([sys.executable, "-m", "arbiter.cli", "run", "--repo", str(repo), "--base", "HEAD~1",
                            "--effort", a.effort, "--out", str(rd)], env=env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, cwd=HOME)
        (rd / "arbiter.log").write_text(p.stdout + "\n--- stderr ---\n" + p.stderr) if rd.exists() else None
        rep = json.loads((rd / "report.json").read_text()) if (rd / "report.json").exists() else None
        row = score(c, rep)
        row.update(exit_code=p.returncode, wall_s=round(time.monotonic() - t0))
        print(f"{row['case']}: exit {p.returncode} main {row.get('main')} matched {row.get('matched')} "
              f"must {row.get('must_hit')}/{row.get('must')}", flush=True)
        return row

    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        rows = list(ex.map(one, cs))
    bug = [r for r in rows if not r.get("clean") and "error" not in r]
    clean = [r for r in rows if r.get("clean") and "error" not in r]
    main = sum(r["main"] for r in bug + clean)
    matched = sum(r["matched"] for r in bug)
    must = sum(r["must"] for r in bug)
    summary = {
        "effort": a.effort, "harness": env.get("ARBITER_HARNESS", "omp"),
        "model": env.get("ARBITER_MODEL", "(default)"), "verify_model": env.get("ARBITER_VERIFY_MODEL", "") or env.get("ARBITER_MODEL", "(default)"),
        "precision": round(matched / main, 3) if main else None,
        "recall": round(sum(r["must_hit"] for r in bug) / must, 3) if must else None,
        "clean_case_findings": sum(r["main"] for r in clean), "suspected": sum(r.get("suspected", 0) for r in rows),
        "errors": [r for r in rows if "error" in r], "rows": rows, "runs": str(out_dir)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"seeded-{ts}.json").write_text(json.dumps(summary, indent=2))
    print(f"\n| case | verdict | main | matched | must hit | suspected |\n|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['case']} | {r.get('verdict', r.get('error'))} | {r.get('main')} | {r.get('matched')} | "
              f"{r.get('must_hit')}/{r.get('must')} | {r.get('suspected')} |")
    print(f"\nprecision {summary['precision']} · recall {summary['recall']} · "
          f"clean-case findings {summary['clean_case_findings']} · results {RESULTS / f'seeded-{ts}.json'}")
    return summary


def main(a) -> int:
    cs = cases(a.lang, a.case)
    if a.action == "build":
        build(cs)
        return 0
    run(cs, a)
    return 0
