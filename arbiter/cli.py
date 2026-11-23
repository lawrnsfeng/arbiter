"""arbiter command line. Exit codes: 0 pass, 1 block, 2 usage/config, 3 empty diff, 4 diff too large, 5 internal."""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

from . import ArbiterExit, harness, report, sandbox
from . import findings as F
from . import pipeline as P
from .lang import REVIEWED
from .model import Decompose, Effort
from .rundir import RunDir

EFFORTS = [e.value for e in Effort]
DECOMPOSE = [d.value for d in Decompose]
STAGES = ("gates", "merge", "tally", "gate", "report")
EXEC_KEYS = ("exec_id", "cmd", "exit_code", "stdout_tail", "stderr_tail", "duration_s", "timed_out")


def _positive(text: str) -> int:
    """argparse type: a bad --jobs or ARBITER_JOBS is a usage error (exit 2), not a crash."""
    if not text.isdigit() or int(text) < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {text!r}")
    return int(text)


def _decompose(text: str) -> str:
    """argparse type, applied to the ARBITER_DECOMPOSE default too: a bad mode is a usage error (exit 2)."""
    if text not in DECOMPOSE:
        raise argparse.ArgumentTypeError(f"expected one of {', '.join(DECOMPOSE)}, got {text!r}")
    return text


def _decompose_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--decompose",
        type=_decompose,
        default=os.environ.get("ARBITER_DECOMPOSE", Decompose.OCR.value),
        help=f"review units: {' | '.join(DECOMPOSE)} (default ocr, or ARBITER_DECOMPOSE)",
    )


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="arbiter")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="full review pipeline")
    r.add_argument("base_pos", nargs="?", help=argparse.SUPPRESS)
    r.add_argument("--repo", default=".")
    r.add_argument("--base")
    r.add_argument("--effort", choices=EFFORTS, default=Effort.STANDARD.value)
    r.add_argument("--lang", help="comma list: python,go,rust,typescript")
    r.add_argument("--harness", choices=harness.HARNESSES)
    r.add_argument("--model", help="finders, A0 and SPEC (default: Haiku)")
    r.add_argument("--verify-model", help="verifier, proof agent and eval judge (default: Sonnet)")
    r.add_argument("--out", type=Path)
    r.add_argument("--jobs", type=_positive, default=os.environ.get("ARBITER_JOBS", "8"), help="agent calls at once")
    r.add_argument("--max-agents", type=int, default=300)
    _decompose_arg(r)
    pl = sub.add_parser("plan", help="plan only (writes RUN/plan.json)")
    pl.add_argument("run", type=Path)
    pl.add_argument("--repo", default=".")
    pl.add_argument("--base")
    pl.add_argument("--effort", choices=EFFORTS, default=Effort.STANDARD.value)
    pl.add_argument("--lang")
    pl.add_argument("--max-agents", type=int, default=300)
    _decompose_arg(pl)
    for name in STAGES:
        sub.add_parser(name).add_argument("run", type=Path)
    sb = sub.add_parser("sandbox")
    sb.add_argument("action", choices=("prepare", "exec", "clean", "selftest"))
    sb.add_argument("run", type=Path)
    sb.add_argument("--base", action="store_true", help="exec: run in the base worktree")
    sb.add_argument("--timeout", type=int, default=300)
    sb.add_argument("rest", nargs=argparse.REMAINDER)
    sub.add_parser("eval").add_argument("rest", nargs=argparse.REMAINDER)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = _parser().parse_args(argv)
    try:
        return _dispatch(a)
    except ArbiterExit as e:
        print(e.message, file=sys.stderr)
        return e.code
    except KeyboardInterrupt:
        raise
    except Exception:  # the exit-code contract: any unexpected failure is 5, never a silent pass
        traceback.print_exc()
        print("arbiter: internal failure", file=sys.stderr)
        return 5


def _langs(s: str | None) -> list[str] | None:
    if not s:
        return None
    langs = [x.strip() for x in s.split(",") if x.strip()]
    if bad := [x for x in langs if x not in REVIEWED]:
        raise ArbiterExit(2, f"arbiter: unknown language {','.join(bad)} ({', '.join(REVIEWED)})")
    return langs


def _plan(run: RunDir) -> P.Plan:
    if (p := run.load("plan.json")) is None:
        raise ArbiterExit(2, f"arbiter: no plan.json in {run.path}")
    return p


def _verdict_exit(run: RunDir, v: str) -> int:
    print(f"verdict {v.upper()} · report {run / 'report.md'}")
    return 1 if v == "block" else 0


def _dispatch(a: argparse.Namespace) -> int:
    match a.cmd:
        case "run":
            for flag, env in (
                ("harness", "ARBITER_HARNESS"),
                ("model", "ARBITER_MODEL"),
                ("verify_model", "ARBITER_VERIFY_MODEL"),
            ):
                if value := getattr(a, flag):
                    os.environ[env] = value
            # resolve models (cost ceiling included) and check each one answers, before any review work
            harness.preflight(harness.settings())
            path, v = P.run_all(
                Path(a.repo),
                base=a.base or a.base_pos,
                effort=a.effort,
                langs=_langs(a.lang),
                out=a.out,
                jobs=a.jobs,
                max_agents=a.max_agents,
                decompose_mode=a.decompose,
            )
            return _verdict_exit(RunDir(path), v)
        case "plan":
            p = P.plan(
                RunDir(a.run),
                Path(a.repo),
                base_ref=a.base,
                effort=a.effort,
                langs=_langs(a.lang),
                max_agents=a.max_agents,
                decompose_mode=a.decompose,
            )
            print(
                json.dumps(
                    {
                        "units": len(p["units"]),
                        "decompose": p["decompose"],
                        "churn": [u["churn"] for u in p["units"]],
                        "tasks": len(p["schedule"]["tasks"]),
                        "once": p["schedule"]["once"],
                        "tools": [t["name"] for t in p["tools"]],
                    },
                    indent=1,
                )
            )
            return 0
        case "sandbox":
            return _sandbox(a)
        case "eval":
            from .eval import main as eval_main

            return eval_main(a.rest)
    run = RunDir(a.run)
    p = _plan(run)
    match a.cmd:
        case "gates":
            P.gates(run, p)
        case "merge":
            P.merge(run, p)
        case "tally":
            votes = run.load("votes.json", {})
            cands = run.load("candidates.json", [])
            for f in cands:
                F.tally(f, votes.get(f["id"], []), p["effort"])
            run.save("tallied.json", cands)
        case "gate":
            P.final_gate(run, p)
        case "report":
            allf = run.load("final.json", [])
            v = F.verdict(allf)
            report.write(run.path, p, allf, v)
            return _verdict_exit(run, v)
    return 0


def _sandbox(a: argparse.Namespace) -> int:
    path = a.run.resolve()
    match a.action:
        case "selftest":
            ok, rows = sandbox.selftest(path)
            width = max(len(n) for n, _ in rows)
            for n, s in rows:
                print(f"{n:<{width}}  {s}")
            return 0 if ok else 1
        case "exec":
            cmd = a.rest[1:] if a.rest[:1] == ["--"] else a.rest
            if not cmd:
                raise ArbiterExit(2, "arbiter: sandbox exec needs -- CMD...")
            if not sandbox.available(path):
                raise ArbiterExit(2, f"arbiter: sandbox not ready in {path}")
            rec = sandbox.exec_(path, cmd, base=a.base, timeout=a.timeout)
            print(json.dumps({k: rec[k] for k in EXEC_KEYS}, indent=1))  # type: ignore[literal-required]
            return 0
        case "prepare":
            print(P.prepare(RunDir(path), _plan(RunDir(path)))["status"])
            return 0
        case _:
            sandbox.clean(path, Path(_plan(RunDir(path))["repo"]))
            return 0


if __name__ == "__main__":
    sys.exit(main())
