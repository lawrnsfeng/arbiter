"""Accuracy eval: seeded corpus and the Martian golden set."""

import argparse

from . import martian, seeded


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
    m.add_argument("--offset", type=int, default=0, help="skip the first N PRs (continue an earlier sample)")
    m.add_argument("--effort", default="standard", choices=("quick", "standard", "deep"))
    m.add_argument("--harness")
    m.add_argument("--model")
    m.add_argument("--verify-model")
    a = ap.parse_args(argv)
    return (seeded if a.suite == "seeded" else martian).main(a)
