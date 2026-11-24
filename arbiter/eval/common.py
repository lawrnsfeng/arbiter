"""Helpers shared by every eval suite: model settings, one review run, and the scores."""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import HOME, harness

RESULTS = HOME / "eval" / "results"
PR_URL = re.compile(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)")
NON_WORD = re.compile(r"\W+")
GIT_TIMEOUT_S = 900
# exported to every child `arbiter run` (and the judge)
RUN_FLAGS = (
    ("harness", "ARBITER_HARNESS"),
    ("model", "ARBITER_MODEL"),
    ("verify_model", "ARBITER_VERIFY_MODEL"),
    ("decompose", "ARBITER_DECOMPOSE"),
    ("review_from", "ARBITER_REVIEW_FROM"),
)


def gh(*args: str) -> str:
    p = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"gh api {' '.join(args)}: {p.stderr.strip()[:200]}")
    return p.stdout


def git(repo: Path, *args: str) -> int:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], timeout=GIT_TIMEOUT_S).returncode
    except subprocess.TimeoutExpired:
        return 124


def _review_home() -> Path:
    """The arbiter checkout that reviews: --review-from DIR (an A/B arm), else this one."""
    d = os.environ.get("ARBITER_REVIEW_FROM")
    return Path(d).expanduser().resolve() if d else HOME


def apply_models(a: argparse.Namespace) -> harness.Settings:
    """Resolve and preflight the models once, then export them and --decompose to the child `arbiter run`
    processes and the judge."""
    for flag, var in RUN_FLAGS:
        if value := getattr(a, flag, None):
            os.environ[var] = value
    if (home := _review_home()) != HOME and not (home / ".venv/bin/python").exists():
        raise SystemExit(f"arbiter: --review-from {home}: no .venv/bin/python (run uv sync there)")
    s = harness.settings()
    harness.preflight(s)  # sets ARBITER_PREFLIGHT_OK, so the children skip it
    os.environ |= {"ARBITER_HARNESS": s.harness, "ARBITER_MODEL": s.model, "ARBITER_VERIFY_MODEL": s.verify_model}
    return s


def models(s: harness.Settings) -> dict[str, str]:
    """The settings an eval summary records: the models and the unit decomposition its runs used."""
    return {
        "harness": s.harness,
        "model": s.model,
        "verify_model": s.verify_model,
        "decompose": os.environ.get("ARBITER_DECOMPOSE", "ocr"),
        "review_from": os.environ.get("ARBITER_REVIEW_FROM", ""),
    }


def stamp() -> str:
    return time.strftime("%Y%m%d%H%M%S", time.gmtime())


@dataclass(frozen=True, slots=True)
class Review:
    exit_code: int
    report: dict[str, Any] | None  # None when the run did not reach a verdict (exit 2-5)
    stdout: str
    stderr: str
    wall_s: int

    @property
    def main(self) -> list[dict[str, Any]]:
        return [f for f in (self.report or {}).get("findings", []) if f.get("placement") == "main"]


def review(repo: Path, base: str, effort: str, out: Path) -> Review:
    """One `arbiter run` in a child process (stdin closed: it must never wait for input). With --review-from,
    the other checkout's interpreter runs its own code (cwd puts its package first on the path)."""
    t0 = time.monotonic()
    home = _review_home()
    p = subprocess.run(
        [
            str(home / ".venv/bin/python") if home != HOME else sys.executable,
            "-m",
            "arbiter.cli",
            "run",
            "--repo",
            str(repo),
            "--base",
            base,
            "--effort",
            effort,
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        cwd=home,
    )
    if out.exists():
        (out / "arbiter.log").write_text(f"{p.stdout}\n--- stderr ---\n{p.stderr}")
    report = None
    if p.returncode in (0, 1) and (out / "report.json").exists():
        report = json.loads((out / "report.json").read_text())
    return Review(p.returncode, report, p.stdout, p.stderr, round(time.monotonic() - t0))


def ratio(num: int, den: int) -> float:
    return num / den if den else 0.0


def share(num: int, den: int) -> float | None:
    """A recall over a subset that may be empty: None (no references of that kind), not 0.0 (all missed)."""
    return round(num / den, 3) if den else None


def fbeta(precision: float, recall: float, beta: float) -> float:
    b2 = beta * beta
    den = b2 * precision + recall
    return round((1 + b2) * precision * recall / den, 3) if den else 0.0


def write_summary(name: str, summary: dict[str, Any]) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(summary, indent=2))
    return path
