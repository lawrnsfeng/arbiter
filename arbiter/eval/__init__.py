"""Accuracy eval: seeded corpus, the Martian golden set, SWR-Bench and AACR-Bench."""

import argparse

from ..model import Decompose
from . import aacr, martian, seeded, swr

REVIEW_FROM = "review with the arbiter checkout at DIR (its .venv), for A/B runs"


def _non_negative(text: str) -> int:
    if not text.isdigit():
        raise argparse.ArgumentTypeError(f"expected a non-negative integer, got {text!r}")
    return int(text)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="arbiter eval")
    sub = ap.add_subparsers(dest="suite", required=True)
    s = sub.add_parser("seeded")
    s.add_argument("action", choices=("build", "run"))
    s.add_argument("--lang", help="python,go,rust,ts")
    s.add_argument("--case", help="substring filter on <lang>-<slug>")
    s.add_argument("--effort", default="standard", choices=("quick", "standard", "deep"))
    s.add_argument("--harness")
    s.add_argument("--model")
    s.add_argument("--verify-model")
    s.add_argument("--decompose", choices=[d.value for d in Decompose], help="review units (exports ARBITER_DECOMPOSE)")
    s.add_argument("--parallel", type=int, default=2, help="cases reviewed at once")
    s.add_argument("--review-from", metavar="DIR", help=REVIEW_FROM)
    m = sub.add_parser("martian")
    m.add_argument("action", choices=("fetch", "run"))
    m.add_argument("--repo", choices=("sentry", "grafana", "cal_dot_com"))
    m.add_argument("--limit", type=int)
    m.add_argument("--offset", type=_non_negative, default=0, help="skip the first N PRs (continue an earlier sample)")
    m.add_argument("--effort", default="standard", choices=("quick", "standard", "deep"))
    m.add_argument("--harness")
    m.add_argument("--model")
    m.add_argument("--verify-model")
    m.add_argument("--decompose", choices=[d.value for d in Decompose], help="review units (exports ARBITER_DECOMPOSE)")
    m.add_argument("--pr", action="append", help="only PRs whose URL contains this text; repeatable")
    m.add_argument("--review-from", metavar="DIR", help=REVIEW_FROM)
    w = sub.add_parser("swr", help="SWR-Bench: fetch the pinned upstream, draw the sample, run and judge")
    w.add_argument("action", choices=("fetch", "sample", "run"))
    w.add_argument("--issue", type=int, default=28, help="sample: PRs with a functional issue")
    w.add_argument("--clean", type=int, default=12, help="sample: clean PRs")
    w.add_argument("--seed", type=int, default=20261122)
    w.add_argument("--limit", type=int)
    w.add_argument("--skip-scored", metavar="SCORE_FILE", help="run only the PRs that file did not score")
    w.add_argument("--parallel", type=int, default=2, help="PRs reviewed at once")
    w.add_argument("--effort", default="standard", choices=("quick", "standard", "deep"))
    w.add_argument("--harness")
    w.add_argument("--model")
    w.add_argument("--verify-model")
    w.add_argument("--decompose", choices=[d.value for d in Decompose], help="review units (exports ARBITER_DECOMPOSE)")
    w.add_argument("--review-from", metavar="DIR", help=REVIEW_FROM)
    r = sub.add_parser("aacr", help="AACR-Bench v2: fetch the pinned dataset, run and judge (file-level coverage)")
    r.add_argument("action", choices=("fetch", "run"))
    r.add_argument("--lang", help="python,ts,go,rust (or a dataset language name)")
    r.add_argument("--pr", action="append", help="only PRs whose URL contains this text; repeatable")
    r.add_argument("--limit", type=int)
    r.add_argument("--effort", default="standard", choices=("quick", "standard", "deep"))
    r.add_argument("--harness")
    r.add_argument("--model")
    r.add_argument("--verify-model")
    r.add_argument("--decompose", choices=[d.value for d in Decompose], help="review units (exports ARBITER_DECOMPOSE)")
    r.add_argument("--review-from", metavar="DIR", help=REVIEW_FROM)
    a = ap.parse_args(argv)
    return {"seeded": seeded, "martian": martian, "swr": swr, "aacr": aacr}[a.suite].main(a)
