"""arbiter command line. Exit codes: 0 pass, 1 block, 2 usage/config, 3 empty diff, 4 diff too large, 5 internal."""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

from . import ArbiterExit, findings as F, pipeline as P, sandbox


def _common_models(a):
    for flag, env in (("harness", "ARBITER_HARNESS"), ("model", "ARBITER_MODEL"), ("verify_model", "ARBITER_VERIFY_MODEL")):
        if getattr(a, flag, None):
            os.environ[env] = getattr(a, flag)


def _plan(run: Path) -> dict:
    p = P.load(run, "plan.json")
    if p is None:
        raise ArbiterExit(2, f"arbiter: no plan.json in {run}")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="arbiter")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="full review pipeline")
    r.add_argument("base_pos", nargs="?", help=argparse.SUPPRESS)
    r.add_argument("--repo", default=".")
    r.add_argument("--base")
    r.add_argument("--effort", choices=("quick", "standard", "deep"), default="standard")
    r.add_argument("--lang", help="comma list: python,go,rust,typescript")
    r.add_argument("--harness", choices=("omp", "claude", "fake"))
    r.add_argument("--model")
    r.add_argument("--verify-model")
    r.add_argument("--out", type=Path)
    r.add_argument("--jobs", type=int, default=int(os.environ.get("ARBITER_JOBS", 8)))
    r.add_argument("--max-agents", type=int, default=300)
    pl = sub.add_parser("plan", help="plan only (writes RUN/plan.json)")
    pl.add_argument("run", type=Path)
    pl.add_argument("--repo", default=".")
    pl.add_argument("--base")
    pl.add_argument("--effort", choices=("quick", "standard", "deep"), default="standard")
    pl.add_argument("--lang")
    pl.add_argument("--max-agents", type=int, default=300)
    for name in ("gates", "merge", "tally", "gate", "report"):
        s = sub.add_parser(name)
        s.add_argument("run", type=Path)
    sb = sub.add_parser("sandbox")
    sb.add_argument("action", choices=("prepare", "exec", "clean", "selftest"))
    sb.add_argument("run", type=Path)
    sb.add_argument("--base", action="store_true", help="exec: run in the base worktree")
    sb.add_argument("--timeout", type=int, default=300)
    sb.add_argument("rest", nargs=argparse.REMAINDER)
    ev = sub.add_parser("eval")
    ev.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    try:
        return _dispatch(a)
    except ArbiterExit as e:
        print(e.message, file=sys.stderr)
        return e.code
    except KeyboardInterrupt:
        raise
    except Exception:
        traceback.print_exc()
        print("arbiter: internal failure", file=sys.stderr)
        return 5


def _langs(s: str | None) -> list[str] | None:
    if not s:
        return None
    langs = [x.strip() for x in s.split(",") if x.strip()]
    bad = [x for x in langs if x not in ("python", "go", "rust", "typescript")]
    if bad:
        raise ArbiterExit(2, f"arbiter: unknown language {','.join(bad)} (python, go, rust, typescript)")
    return langs


def _dispatch(a) -> int:
    if a.cmd == "run":
        _common_models(a)
        if os.environ.get("ARBITER_HARNESS", "omp") not in ("omp", "claude", "fake"):
            raise ArbiterExit(2, f"arbiter: unknown harness {os.environ['ARBITER_HARNESS']}")
        run, v = P.run_all(Path(a.repo), a.base or a.base_pos, a.effort, _langs(a.lang), a.out, a.jobs, a.max_agents)
        print(f"verdict {v.upper()} · report {run / 'report.md'}")
        return 1 if v == "block" else 0
    if a.cmd == "plan":
        p = P.plan(a.run, Path(a.repo), a.base, a.effort, _langs(a.lang), a.max_agents)
        print(json.dumps({"units": len(p["units"]), "tasks": len(p["schedule"]["tasks"]), "once": p["schedule"]["once"],
                          "tools": [t["name"] for t in p["tools"]]}, indent=1))
        return 0
    if a.cmd == "sandbox":
        return _sandbox(a)
    if a.cmd == "eval":
        from .eval import main as eval_main
        return eval_main(a.rest)
    p = _plan(a.run)
    if a.cmd == "gates":
        P.gates(a.run, p)
    elif a.cmd == "merge":
        P.merge(a.run, p)
    elif a.cmd == "tally":
        votes = P.load(a.run, "votes.json", {})
        cands = P.load(a.run, "candidates.json", [])
        for f in cands:
            F.tally(f, votes.get(f["id"], []), p["effort"])
        P.save(a.run, "tallied.json", cands)
    elif a.cmd == "gate":
        P.final_gate(a.run, p)
    elif a.cmd == "report":
        from . import report
        allf = P.load(a.run, "final.json", [])
        v = F.verdict(allf)
        report.write(a.run, p, allf, v)
        print(f"verdict {v.upper()} · report {a.run / 'report.md'}")
        return 1 if v == "block" else 0
    return 0


def _sandbox(a) -> int:
    run = a.run.resolve()
    if a.action == "selftest":
        ok, rows = sandbox.selftest(run)
        w = max(len(n) for n, _ in rows)
        for n, s in rows:
            print(f"{n:<{w}}  {s}")
        return 0 if ok else 1
    if a.action == "exec":
        cmd = a.rest[1:] if a.rest[:1] == ["--"] else a.rest
        if not cmd:
            raise ArbiterExit(2, "arbiter: sandbox exec needs -- CMD...")
        if not sandbox.available(run):
            raise ArbiterExit(2, f"arbiter: sandbox not ready in {run}")
        rec = sandbox.exec_(run, cmd, base=a.base, timeout=a.timeout)
        print(json.dumps({k: rec[k] for k in ("exec_id", "cmd", "exit_code", "stdout_tail", "stderr_tail",
                                                "duration_s", "timed_out")}, indent=1))
        return 0
    p = _plan(run)
    if a.action == "prepare":
        st = P.prepare(run, p)
        print(st["status"])
        return 0
    sandbox.clean(run, Path(p["repo"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
