"""RUN/report.json (machine) and RUN/report.md (human): requirements first, then findings by action tier."""

from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from . import findings as F
from .agents import axis_owners
from .model import AXIS_PRIORITY, Axis, Effort, Finding, Placement, ProofResult, Severity, Tier
from .plan import Plan
from .rundir import RunDir

REPORTED = frozenset({Placement.MAIN, Placement.SUSPECTED, Placement.PRE_EXISTING, Placement.NIT_OVERFLOW})
EXCERPT_LINES = 3
OPTIONAL_SHOWN = 10
SARIF = {Tier.MUST: "error", Tier.SHOULD: "warning", Tier.VERIFY: "warning", Tier.OPTIONAL: "note", Tier.FYI: "note"}
NUMBERED = (Tier.MUST, Tier.SHOULD, Tier.VERIFY)
TIER_TITLES = {
    Tier.MUST: "Must fix",
    Tier.SHOULD: "Should fix: fix, or reply `decision: <why>`",
    Tier.VERIFY: "Verify: unproven, a human decides",
}
NEXT_ACTION = {
    "block": "fix every must-fix item, then fix or reply `decision: <why>` to each should-fix item.",
    "follow-ups": "fix or reply `decision: <why>` to each should-fix item; a human checks each verify item.",
    "pass": "none required.",
    "incomplete": "rerun; too many agent calls failed to give a verdict.",
}


def tier(f: Finding) -> Tier:
    match f.get("placement"):
        case Placement.MAIN if f["severity"] == Severity.BLOCK:
            return Tier.MUST
        case Placement.MAIN if f["severity"] == Severity.SHOULD_FIX:
            return Tier.SHOULD
        case Placement.SUSPECTED:
            return Tier.VERIFY
        case Placement.PRE_EXISTING:
            return Tier.FYI
        case _:
            return Tier.OPTIONAL


def _confirmed(f: Finding) -> bool:
    return bool(p := f.get("proof")) and p["result"] == ProofResult.CONFIRMED  # type: ignore[index]


def _evidence(f: Finding) -> str:
    if _confirmed(f):
        return f"proven {f['proof']['rung']}"
    if f.get("measure"):
        return "measured"
    if f.get("placement_reason", "").startswith(F.UNPROVABLE):
        return F.UNPROVABLE
    return "verified" if f.get("placement") == Placement.MAIN else "unproven"


def _sources(f: Finding) -> list[str]:
    src = [x for x in (f.get("rule"), f"CWE-{f['cwe']}" if f.get("cwe") else None, f.get("precedent")) if x]
    return src + [
        f"{x.get('rung')} {x.get('tool')}: {x.get('rule') or str(x.get('msg', ''))[:80]}" for x in f.get("support", [])
    ]


def _details(f: Finding) -> list[str]:
    out = []
    if trig := f.get("trigger"):
        out.append(f"Trigger: {trig}")
    if _confirmed(f):
        proof = f["proof"]
        b = proof.get("before", {})
        s = f"Proof: `{b.get('cmd', '')}` → exit {b.get('exit_code')}"
        if a := proof.get("after"):
            s += f"; after fix `{a.get('cmd', '')}` → exit {a.get('exit_code')}"
        if artifact := proof.get("artifact"):
            s += f" ({artifact})"
        out.append(s)
        if excerpt := b.get("output_excerpt"):
            out += ["", "```", *excerpt.strip().splitlines()[-EXCERPT_LINES:], "```", ""]
    if src := _sources(f):
        out.append(f"Sources: {'; '.join(src)}")
    if locs := f.get("locations"):
        out.append(f"Also at: {', '.join(f'`{x}`' for x in locs)}")
    if reason := f.get("status_reason") or f.get("placement_reason"):
        out.append(f"Placement: {reason}")
    if diff := f.get("proof_fix_diff"):
        out += ["", "Fix (proven in sandbox):", "", "```diff", *diff.splitlines(), "```", ""]
    for p in f.get("patches", []):
        out += ["", f"**{p['title']}** (lines {p['start_line']}-{p['end_line']})", "", "```suggestion"]
        out += [*str(p["code"]).splitlines(), "```", ""]
    if not f.get("patches") and (fix := f.get("fix")):
        out.append(f"Fix: {fix}")
    return out


def _item(n: int, f: Finding) -> list[str]:
    tag = f.get("addresses") or Axis(f["axis"]).group
    md = [f"**#{n} · {tag} · {f['axis']} · {_evidence(f)}** `{f['file']}:{f['line']}`: {f['claim']}"]
    if why := f.get("challenge"):
        md += ["", f"Challenged by decision model: {why}"]
    if body := _details(f):
        md += ["", "<details><summary>Evidence and fix</summary>", "", *body, "", "</details>"]
    return [*md, ""]


def axes_rows(reported: list[Finding], cov: dict[str, Any]) -> list[str]:
    ran = {name.split("@", 1)[0] for name in cov.get("agents_run", [])}
    owners = axis_owners()
    rows = ["| Axis | Must | Should | Verify | Optional | Checked |", "|---|---|---|---|---|---|"]
    for axis in AXIS_PRIORITY:
        n = Counter(tier(f) for f in reported if axis in (f.get("axes") or [f["axis"]]))
        checked = "✓" if owners.get(axis, set()) & ran else "– not triggered"  # noqa: RUF001
        rows.append(
            f"| {axis} | {n[Tier.MUST]} | {n[Tier.SHOULD]} | {n[Tier.VERIFY]} | {n[Tier.OPTIONAL]} | {checked} |"
        )
    return rows


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
    if d := cov.get("decide"):
        yield (
            f"- decide: {d.get('model')}, ok {d.get('ok')}, dismissed {d.get('dismissed', 0)}, "
            f"challenged {d.get('challenged', 0)}, missed {d.get('missed', 0)}, cap ${d.get('max_usd')}"
        )
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
    decision = run.load("decision.json")
    reqs = intent.get("requirements", [])
    reported = [f for f in allf if f.get("placement") in REPORTED]
    by_tier: dict[Tier, list[Finding]] = {t: [f for f in reported if tier(f) == t] for t in Tier}
    n = {t: len(fs) for t, fs in by_tier.items()}
    numbered = [f for t in NUMBERED for f in by_tier[t]]
    num = {id(f): i for i, f in enumerate(numbered, 1)}
    key = "follow-ups" if verdict == "pass" and (n[Tier.SHOULD] or n[Tier.VERIFY]) else verdict
    label = {
        "block": "🔴 BLOCK",
        "pass": "🟢 PASS",
        "follow-ups": "🟡 PASS with follow-ups",
        "incomplete": "⚪ INCOMPLETE",
    }[key]
    md = [
        f"# Review: {Path(p['repo']).name} {p['base'][:7]}..{p['head'][:7]} · {p['effort']} · {label}: "
        f"{n[Tier.MUST]} must fix · {n[Tier.SHOULD]} should · {n[Tier.VERIFY]} verify · {n[Tier.OPTIONAL]} optional",
        "",
        f"**Next action:** {NEXT_ACTION[key]}",
    ]
    if decision and (summary := decision.get("summary")):
        md += ["", f"> {summary}"]
    md += ["", "## What this change must do", ""]
    if reqs:
        md += ["| ID | Requirement (source) | Status |", "|---|---|---|"]
        for r in reqs:
            hits = [
                f"#{num[id(f)]}"
                for f in numbered
                if f.get("addresses") == r["id"] and f.get("placement") in (Placement.MAIN, Placement.SUSPECTED)
            ]
            status = f"⚠ {', '.join(hits)}" if hits else "✓ no finding"
            text = str(r["text"]).replace("|", "\\|")
            md.append(f"| {r['id']} | {text} ({r['source']}) | {status} |")
    else:
        md.append("- no requirements extracted (no commit or issue text)")
    md.append("")
    for t in NUMBERED:
        if by_tier[t]:
            md += [f"## {TIER_TITLES[t]}", ""]
            for f in by_tier[t]:
                md += _item(num[id(f)], f)
    if opt := by_tier[Tier.OPTIONAL]:
        shown = [f"`{f['file']}:{f['line']}` {f.get('rule') or f['axis']}" for f in opt[:OPTIONAL_SHOWN]]
        more = f", +{len(opt) - OPTIONAL_SHOWN} more" if len(opt) > OPTIONAL_SHOWN else ""
        md += [f"## Optional ({len(opt)})", "", ", ".join(shown) + more, ""]
    pre_gates = gates.get("preexisting", [])
    if (pre := by_tier[Tier.FYI]) or pre_gates:
        md += [f"## Pre-existing ({len(pre) + len(pre_gates)}): ticket it, not this PR", ""]
        md += [f"- `{f['file']}:{f['line']}` {f['axis']}: {f['claim']}" for f in pre]
        md += [f"- gate: `{x['cmd']}` also fails on base" for x in pre_gates]
        md.append("")
    md += [f"<details><summary>Axes checked ({len(AXIS_PRIORITY)})</summary>", "", *axes_rows(reported, cov), ""]
    md += ["</details>", "", "<details><summary>Coverage</summary>", ""]
    md += [
        f"- gate {r['name']}: {r['status']}" + (f", exit {r['exit_code']}" if "exit_code" in r else "")
        for r in gates.get("results", [])
    ]
    md += [f"- claim: {c}" for c in intent.get("claims", [])] or ["- no claims extracted"]
    md += [*_coverage(p, cov), "", "</details>"]
    (run / "report.md").write_text("\n".join(md) + "\n")
    run.save(
        "report.json",
        {
            "verdict": verdict,
            "repo": p["repo"],
            "base": p["base"],
            "head": p["head"],
            "effort": p["effort"],
            "requirements": reqs,
            "decision": decision,
            "findings": [{**f, "tier": tier(f), "sarif_level": SARIF[tier(f)]} for f in reported],
            "coverage": cov,
        },
    )
