"""Helpers shared by every eval suite: model settings, one review run, and the scores."""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import HOME, harness

RESULTS = HOME / "eval" / "results"
MODEL_FLAGS = (("harness", "ARBITER_HARNESS"), ("model", "ARBITER_MODEL"), ("verify_model", "ARBITER_VERIFY_MODEL"))


def apply_models(a: argparse.Namespace) -> harness.Settings:
    """Export --harness/--model/--verify-model for the child `arbiter run` processes and the judge."""
    for flag, var in MODEL_FLAGS:
        if value := getattr(a, flag, None):
            os.environ[var] = value
    return harness.settings()


def models(s: harness.Settings) -> dict[str, str]:
    return {"harness": s.harness, "model": s.model, "verify_model": s.verify_model}


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
    """One `arbiter run` in a child process (stdin closed: it must never wait for input)."""
    t0 = time.monotonic()
    p = subprocess.run(
        [
            sys.executable,
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
        cwd=HOME,
    )
    if out.exists():
        (out / "arbiter.log").write_text(f"{p.stdout}\n--- stderr ---\n{p.stderr}")
    report = None
    if p.returncode in (0, 1) and (out / "report.json").exists():
        report = json.loads((out / "report.json").read_text())
    return Review(p.returncode, report, p.stdout, p.stderr, round(time.monotonic() - t0))


def ratio(num: int, den: int) -> float:
    return num / den if den else 0.0


def fbeta(precision: float, recall: float, beta: float) -> float:
    b2 = beta * beta
    den = b2 * precision + recall
    return round((1 + b2) * precision * recall / den, 3) if den else 0.0


def write_summary(name: str, summary: dict[str, Any]) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(summary, indent=2))
    return path
