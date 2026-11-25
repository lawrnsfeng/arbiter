"""Accuracy eval: seeded corpus, the Martian golden set, SWR-Bench and AACR-Bench."""

import argparse

from ..model import Decompose
from . import aacr, martian, seeded, swr

REVIEW_FROM = "review with the arbiter checkout at DIR (its .venv), for A/B runs"
PR_HELP = "only PRs whose URL ends with this text (owner/repo/pull/N or repo/pull/N); repeatable"
DECIDE = "one capped Opus decision call per review (exports ARBITER_DECIDE)"
JUDGE = "auto (default): Clef first while the free Workers AI allowance lasts, else the LLM judge; sonnet: LLM only"
PASSES = "per-unit finder passes merged by location (exports ARBITER_FINDER_PASSES)"


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
    s.add_argument("--decide", action="store_const", const="1", help=DECIDE)
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
    m.add_argument("--pr", action="append", help=PR_HELP)
    m.add_argument("--review-from", metavar="DIR", help=REVIEW_FROM)
    m.add_argument("--decide", action="store_const", const="1", help=DECIDE)
    m.add_argument("--finder-passes", choices=("1", "2"), help=PASSES)
    m.add_argument("--judge", choices=("auto", "sonnet"), help=JUDGE)
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
    w.add_argument("--decide", action="store_const", const="1", help=DECIDE)
    r = sub.add_parser("aacr", help="AACR-Bench v2: fetch the pinned dataset, run and judge (file-level coverage)")
    r.add_argument("action", choices=("fetch", "run", "rescore"))
    r.add_argument("--runs", nargs="+", metavar="TS", help="rescore: result folders under eval/results/aacr/")
    r.add_argument("--label", action="append", help="rescore: one name per --runs folder, in order")
    r.add_argument("--lang", help="python,ts,go,rust (or a dataset language name)")
    r.add_argument("--pr", action="append", help=PR_HELP)
    r.add_argument("--limit", type=int)
    r.add_argument("--effort", default="standard", choices=("quick", "standard", "deep"))
    r.add_argument("--harness")
    r.add_argument("--model")
    r.add_argument("--verify-model")
    r.add_argument("--decompose", choices=[d.value for d in Decompose], help="review units (exports ARBITER_DECOMPOSE)")
    r.add_argument("--review-from", metavar="DIR", help=REVIEW_FROM)
    r.add_argument("--decide", action="store_const", const="1", help=DECIDE)
    r.add_argument("--finder-passes", choices=("1", "2"), help=PASSES)
    r.add_argument("--judge", choices=("auto", "sonnet"), help=JUDGE)
    a = ap.parse_args(argv)
    return {"seeded": seeded, "martian": martian, "swr": swr, "aacr": aacr}[a.suite].main(a)
