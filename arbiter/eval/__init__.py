"""Accuracy eval: seeded corpus, the Martian golden set and SWR-Bench."""

import argparse

from . import martian, seeded, swr


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
    s.add_argument("--parallel", type=int, default=2, help="cases reviewed at once")
    m = sub.add_parser("martian")
    m.add_argument("action", choices=("fetch", "run"))
    m.add_argument("--repo", choices=("sentry", "grafana", "cal_dot_com"))
    m.add_argument("--limit", type=int)
    m.add_argument("--offset", type=_non_negative, default=0, help="skip the first N PRs (continue an earlier sample)")
    m.add_argument("--effort", default="standard", choices=("quick", "standard", "deep"))
    m.add_argument("--harness")
    m.add_argument("--model")
    m.add_argument("--verify-model")
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
    a = ap.parse_args(argv)
    return {"seeded": seeded, "martian": martian, "swr": swr}[a.suite].main(a)
