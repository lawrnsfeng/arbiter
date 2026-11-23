"""RUN/report.json (machine) and RUN/report.md (human)."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from . import findings as F
from .model import Axis, Effort, Finding, Group, Placement, ProofResult, Severity
from .plan import Plan
from .rundir import RunDir

REPORTED = frozenset({Placement.MAIN, Placement.SUSPECTED, Placement.PRE_EXISTING, Placement.NIT_OVERFLOW})
EXCERPT_LINES = 3


def _tag(f: Finding) -> str:
    proof = f.get("proof")
    if proof and proof["result"] == ProofResult.CONFIRMED:
        return proof["rung"]
    return f.get("rule") or f.get("proof_plan", {}).get("rung", "E0")


def _line(f: Finding) -> str:
    proof = f.get("proof")
    confirmed = bool(proof) and proof["result"] == ProofResult.CONFIRMED  # type: ignore[index]
    s = f"- [{f['severity']}][{f['axis']}][{_tag(f)}] `{f['file']}:{f['line']}` {f['claim']}"
    if fix := f.get("fix"):
        s += f" · Fix: {fix}"
    if locs := f.get("locations"):
        s += f" · Also at: {', '.join(f'`{x}`' for x in locs)}"
    if confirmed and proof:
        b = proof.get("before", {})
        s += f" · Proof: `{b.get('cmd', '')}` → exit {b.get('exit_code')}"
        if a := proof.get("after"):
            s += f"; after fix `{a.get('cmd', '')}` → exit {a.get('exit_code')}"
        if artifact := proof.get("artifact"):
            s += f" ({artifact})"
    src = [x for x in (f.get("rule"), f"CWE-{f['cwe']}" if f.get("cwe") else None, f.get("precedent")) if x]
    src += [
        f"{x.get('rung')} {x.get('tool')}: {x.get('rule') or str(x.get('msg', ''))[:80]}" for x in f.get("support", [])
    ]
    if src:
        s += f" · Source: {'; '.join(src)}"
    if reason := f.get("status_reason") or f.get("placement_reason"):
        s += f" · ({reason})"
    if confirmed and proof and (excerpt := proof.get("before", {}).get("output_excerpt")):
        s += "\n  ```\n" + "\n".join(f"  {x}" for x in excerpt.strip().splitlines()[-EXCERPT_LINES:]) + "\n  ```"
    return s


def _sections(allf: list[Finding]) -> dict[str, list[Finding]]:
    main = [f for f in allf if f.get("placement") == Placement.MAIN]
    functional = [f for f in main if Axis(f["axis"]).group == Group.FUNCTIONAL and f["axis"] != Axis.SPEC]
    return {
        "Block (proven)": [f for f in functional if f["severity"] == Severity.BLOCK],
        "Should-fix (proven)": [f for f in functional if f["severity"] != Severity.BLOCK],
        "Evolvability (idiom · design · docs)": [f for f in main if Axis(f["axis"]).group == Group.EVOLVABILITY],
        "Suspected (unproven, non-blocking)": [f for f in allf if f.get("placement") == Placement.SUSPECTED],
        "Pre-existing": [f for f in allf if f.get("placement") == Placement.PRE_EXISTING],
    }


def _coverage(p: Plan, cov: dict[str, Any]) -> Iterator[str]:
    units = cov.get("units", [])
    dec = cov.get("decompose", {})
    yield f"- decompose: {dec.get('mode', 'ocr')}" + (
        f" (budget {dec['budget']}, {dec.get('interface_changes', 0)} interface changes)"
        if dec.get("mode", "ocr") != "ocr"
        else ""
    )
    yield f"- units: {len(units)} — " + "; ".join(
        f"{u['id']} {u['lang']} churn {u['churn']} [{', '.join(u['files'])}]"
        + (f" triggers {','.join(u['triggers'])}" if u["triggers"] else "")
        for u in units
    )
    yield f"- agents run: {len(cov.get('agents_run', []))}; verifier calls: {cov.get('verifier_calls', 0)}"
    yield from (f"- agent failed: {e}" for e in cov.get("agent_failures", []))
    yield from (
        f"- agent skipped: {s['agent']} {s.get('unit', '')} ({s['reason']})" for s in cov.get("agents_skipped", [])
    )
    if p["effort"] == Effort.DEEP:
        yield "- deep: k=3 passes for A1a, A1b, A2, A3, A4"
    for t in cov.get("tools", []):
        ver = cov.get("tool_versions", {}).get(t["name"].split()[0], "")
        yield (
            f"- tool {t['name']} ({t['lang']}): {'available' if t['available'] else 'missing'}, {t['source']}"
            + (f", {ver}" if ver else "")
        )
    pr = cov.get("proofs", {})
    yield f"- proofs: {pr.get('attempted', 0)} attempted, {pr.get('confirmed', 0)} confirmed"
    yield f"- sandbox: {cov.get('sandbox', 'unknown')}" + "".join(f"; {n}" for n in cov.get("sandbox_notes", []))
    tm = cov.get("threat_model", {})
    yield f"- threat model: {tm.get('path') or 'none'}{' (drafted by arbiter)' if tm.get('drafted') else ''}"
    yield f"- harness: {cov.get('harness')}; models: {cov.get('models')}"
    yield from (f"- excluded from units: {x['path']} ({x['reason']})" for x in cov.get("excluded", []))
    yield from (f"- note: {n}" for n in cov.get("notes", []))
    yield f"- wall time: {cov.get('wall_time_s', '?')} s"


def write(run_path: Path, p: Plan, allf: list[Finding], verdict: str) -> None:
    run = RunDir(run_path)
    cov, gates, intent = run.load("coverage.json", {}), run.load("gates.json", {}), run.load("intent.json", {})
    md = [
        f"# arbiter review {Path(p['repo']).name} {p['base'][:7]}..{p['head'][:7]} · {p['effort']} · "
        f"verdict {verdict.upper()}",
        "",
        "## Gates",
        "",
    ]
    md += [
        f"- {r['name']}: {r['status']}" + (f", exit {r['exit_code']}" if "exit_code" in r else "")
        for r in gates.get("results", [])
    ]
    md += [
        f"- pre-existing failure: `{x['cmd']}` exits {x['exit_code']} on HEAD and {x['base_exit_code']} on base"
        for x in gates.get("preexisting", [])
    ]
    md.append("")
    for title, fs in _sections(allf).items():
        md += [f"## {title}", "", *([_line(f) for f in fs] or ["- none"])]
        if title == "Pre-existing":
            md += [f"- gate: `{x['cmd']}` also fails on base" for x in gates.get("preexisting", [])]
        md.append("")
    if overflow := sum(f.get("placement") == Placement.NIT_OVERFLOW for f in allf):
        md += [f"{overflow} more nits not shown (cap {F.NIT_CAP}).", ""]
    md += ["## Spec", "", *([f"- claim: {c}" for c in intent.get("claims", [])] or ["- no claims extracted"])]
    md += [_line(f) for f in allf if f.get("placement") == Placement.MAIN and f["axis"] == Axis.SPEC]
    md += ["", "## Coverage", "", *_coverage(p, cov)]
    (run / "report.md").write_text("\n".join(md) + "\n")
    run.save(
        "report.json",
        {
            "verdict": verdict,
            "repo": p["repo"],
            "base": p["base"],
            "head": p["head"],
            "effort": p["effort"],
            "findings": [f for f in allf if f.get("placement") in REPORTED],
            "coverage": cov,
        },
    )
