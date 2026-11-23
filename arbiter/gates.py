"""Stage 3: the project's own build, lint, type and test commands, plus analyzers kept as oracles.

Diagnostics on added lines become E1 findings. A failing build or test counts only if base passes (E1/E4).
Analyzer output is never shown to finders (SAST in prompts cut precision to 2.8%, research-decompose-verify.md §3a);
it is attached later as E2 supporting evidence.
"""

import re
import subprocess
import time
from typing import Any, TypedDict

from . import sandbox, tools
from .model import (
    Axis,
    ExecRecord,
    Finding,
    Placement,
    Proof,
    ProofResult,
    ProofRun,
    Rung,
    Severity,
    Status,
    ToolKind,
    ToolSpec,
)
from .plan import Plan
from .rundir import RunDir

STATIC_OK = frozenset({"ruff", "eslint", "bandit", "gosec"})  # may run without the sandbox (no repo code executed)
FAILING_KINDS = frozenset({ToolKind.BUILD, ToolKind.TYPE, ToolKind.TEST})
PYTEST_NO_TESTS = 5
ERROR_WORD = re.compile(r"\berror\b", re.IGNORECASE)
UNSAFE_NAME = re.compile(r"\W+")
EXCERPT_LINES = 15
HOST_TAIL = 20_000


class GateResult(TypedDict, total=False):
    name: str
    status: str
    exit_code: int
    cmd: str
    timed_out: bool
    exec_id: str


class PreExisting(TypedDict):
    name: str
    cmd: str
    exit_code: int
    base_exit_code: int


class AnalyzerHit(tools.Diagnostic):
    tool: str


class Gates(TypedDict):
    findings: list[Finding]
    preexisting: list[PreExisting]
    results: list[GateResult]
    analyzer_hits: list[AnalyzerHit]


def _host_run(s: ToolSpec, cwd: Any) -> dict[str, Any]:
    """Static tools and network-needing analyzers run outside bwrap: none of them executes repo code."""
    cmd = " ".join(s["cmd"])
    t0 = time.monotonic()
    try:
        r = subprocess.run(
            s["cmd"], cwd=cwd, capture_output=True, text=True, errors="replace", timeout=600, stdin=subprocess.DEVNULL
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stdout_tail": "",
            "stderr_tail": str(e),
            "timed_out": True,
            "cmd": cmd,
            "exec_id": "",
        }
    return {
        "exit_code": r.returncode,
        "stdout": r.stdout,
        "stdout_tail": r.stdout[-HOST_TAIL:],
        "stderr_tail": r.stderr[-HOST_TAIL:],
        "timed_out": False,
        "cmd": cmd,
        "exec_id": "",
        "duration_s": round(time.monotonic() - t0, 2),
    }


def exec_tool(run: RunDir, s: ToolSpec, base: bool = False) -> ExecRecord | dict[str, Any] | None:
    wt = run / ("wt-base" if base else "wt")
    if not wt.exists():
        return None
    ready = sandbox.available(run.path)
    root = s.get("root", "")
    if s.get("net") or (not ready and (s["name"] in STATIC_OK or s["name"].startswith("semgrep"))):
        return _host_run(s, wt / root)
    if not ready:
        return None
    timeout = 900 if s["kind"] in (ToolKind.TEST, ToolKind.ANALYZER) else 600
    return sandbox.exec_(run.path, s["cmd"], base=base, timeout=timeout, sub=root)


def _gate_finding(
    n: int,
    s: ToolSpec,
    r: ExecRecord | dict[str, Any],
    *,
    path: str,
    line: int,
    claim: str,
    axis: Axis,
    sev: Severity,
    rung: Rung,
    rule: str,
    after: ProofRun | None = None,
) -> Finding:
    excerpt = "\n".join(f"{r['stdout_tail']}\n{r['stderr_tail']}".strip().splitlines()[-EXCERPT_LINES:])
    proof = Proof(
        rung=rung,
        result=ProofResult.CONFIRMED,
        before=ProofRun(exec_id=r["exec_id"], cmd=r["cmd"], exit_code=r["exit_code"], output_excerpt=excerpt[-1500:]),
    )
    if after:
        proof["after"] = after
    return Finding(
        id=f"g{n:02d}",
        source="gate",
        agents=[s["name"]],
        axis=axis,
        group=axis.group,
        severity=sev,
        file=path,
        line=line,
        end_line=line,
        claim=claim,
        rule=rule,
        status=Status.VERIFIED,
        placement=Placement.MAIN,
        proof=proof,
    )


def gates(run: RunDir, p: Plan) -> Gates:
    added = {f["path"]: {n for h in f["hunks"] for n, _ in h["added"]} for f in p["files"] if not f["excluded"]}
    first_line = next(((f, min(ls)) for f, ls in added.items() if ls), ("", 1))
    out = Gates(findings=[], preexisting=[], results=[], analyzer_hits=[])
    # roots whose HEAD or base dependency fetch failed: a HEAD/base gate difference there may be environmental
    fetch_failed = {f["root"] for f in run.load("sandbox.json", {}).get("fetch", []) if f["exit_code"]}
    (run / "tools").mkdir(exist_ok=True)
    wt = str((run / "wt").resolve())

    def add(*args: Any, **kw: Any) -> None:
        out["findings"].append(_gate_finding(len(out["findings"]) + 1, *args, **kw))

    for s in p["tools"]:
        name, kind = s["name"], ToolKind(s["kind"])
        if not s.get("available"):
            out["results"].append(GateResult(name=name, status="missing"))
            continue
        if (r := exec_tool(run, s)) is None:
            out["results"].append(GateResult(name=name, status="skipped (sandbox unavailable)"))
            continue
        stdout = str(r.get("stdout", r["stdout_tail"]))
        (run / "tools" / f"{UNSAFE_NAME.sub('_', name)}.out").write_text(
            f"{stdout}\n--- stderr ---\n{r['stderr_tail']}"
        )
        out["results"].append(
            GateResult(
                name=name,
                status="ran",
                exit_code=r["exit_code"],
                cmd=r["cmd"],
                timed_out=r["timed_out"],
                exec_id=r["exec_id"],
            )
        )
        match kind:
            case ToolKind.ANALYZER:
                out["analyzer_hits"] += [AnalyzerHit(**h, tool=name) for h in tools.analyzer_hits(s, stdout, wt)]
                continue
            case _ if r["timed_out"]:
                run.cov(notes=[f"gate {name} timed out"])
                continue
            case ToolKind.TEST if name == "pytest" and r["exit_code"] == PYTEST_NO_TESTS:
                continue  # no tests collected
        diags = tools.diagnostics(s, r["stdout_tail"], r["stderr_tail"], wt)
        hits = [dg for dg in diags if dg["line"] in added.get(dg["path"], set())]
        for dg in [] if kind == ToolKind.TEST else hits:
            is_err = kind == ToolKind.BUILD or (kind == ToolKind.TYPE and ERROR_WORD.search(dg["msg"]))
            sev = Severity.BLOCK if is_err else Severity.NIT if name == "rustfmt" else Severity.SHOULD_FIX
            msg = dg["msg"] or "the code differs from the formatter's output here"
            add(
                s,
                r,
                path=dg["path"],
                line=dg["line"],
                claim=f"{name}: {msg}",
                axis=Axis.LOGIC if is_err else Axis.IDIOM,
                sev=sev,
                rung=Rung.E1,
                rule=dg["rule"] or name,
            )
        if not r["exit_code"] or kind not in FAILING_KINDS or hits:
            continue
        if s.get("root", "") in fetch_failed:
            run.cov(
                notes=[
                    f"gate {name} fails, but dependency fetch failed in {s.get('root') or '.'}: "
                    "HEAD-vs-base comparison skipped"
                ]
            )
            continue
        if not (rb := exec_tool(run, s, base=True)):
            continue
        if rb["exit_code"] == 0:
            path, line = next(((dg["path"], dg["line"]) for dg in diags if dg["path"] in added), first_line)
            add(
                s,
                r,
                path=path,
                line=line,
                claim=f"`{r['cmd']}` fails on HEAD (exit {r['exit_code']}) and passes on base",
                axis=Axis.LOGIC,
                sev=Severity.BLOCK,
                rung=Rung.E4 if kind == ToolKind.TEST else Rung.E1,
                rule=name,
                after=ProofRun(exec_id=rb["exec_id"], cmd=f"{rb['cmd']} (on base)", exit_code=0),
            )
        else:
            out["preexisting"].append(
                PreExisting(name=name, cmd=r["cmd"], exit_code=r["exit_code"], base_exit_code=rb["exit_code"])
            )
    run.save("gates.json", out)
    return out
