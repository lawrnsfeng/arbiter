"""Schemas (hand-written validators), merge and dedup, the vote tally, and the evidence gate."""

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .model import (
    AXIS_PRIORITY,
    Axis,
    Effort,
    ExecRecord,
    Finding,
    Group,
    MaintFact,
    Placement,
    Proof,
    ProofResult,
    Ranges,
    Rung,
    Severity,
    Status,
    Symbol,
    SymbolChange,
    Verdict,
    VoteRecord,
    least_severe,
)

# accepted proof rungs per functional axis (research-decompose-verify.md §3b)
ACCEPTED: dict[Axis, frozenset[Rung]] = {
    axis: frozenset(map(Rung, rungs.split()))
    for axis, rungs in {
        Axis.LOGIC: "E3 E4 E6",
        Axis.EDGE: "E3 E4 E6",
        Axis.ERRORS: "E3 E4",
        Axis.RESOURCES: "E4 E5",
        Axis.CONCURRENCY: "E4 E5",
        Axis.SECURITY: "E3 E4",
        Axis.PRIVACY: "E3 E4",
        Axis.PERFORMANCE: "E8",
        Axis.API: "E1 E4",
        Axis.DATA: "E4 E9",
        Axis.TESTS: "E4 E7",
        Axis.DEPS: "E1",
        Axis.OBSERVABILITY: "E4",
        Axis.OPS: "E1",
        Axis.PORTABILITY: "E1 E4",
        Axis.A11Y: "E1",
        Axis.SPEC: "E4 E9",
    }.items()
}
EFFORT_RUNGS: dict[Effort, frozenset[Rung]] = {
    Effort.QUICK: frozenset({Rung.E1, Rung.E3}),
    Effort.STANDARD: frozenset({Rung.E1, Rung.E2, Rung.E3, Rung.E4, Rung.E5, Rung.E6, Rung.E8}),
    Effort.DEEP: frozenset(Rung) - {Rung.E0},
}
NEVER_DISMISS_CWE = frozenset({78, 77, 89, 94, 79, 22, 502, 918, 862, 863, 639, 287, 306})
LOC = re.compile(r"^[^\s:]+:\d+$")
# linter ids: ruff/flake8/staticcheck (E501, SA4006), clippy::x, eslint (plugin/rule, no-x, prefer-x)
LINT_ID = re.compile(r"^([A-Z]{1,4}\d{3,4}|clippy::\w+|(@[\w-]+/)?[\w-]+/[\w-]+|(no|prefer)-[\w-]+)$")
NIT_CAP = 10
UNPROVABLE = "verified; no proof possible here"  # placement reason prefix: verified, proof blocked by environment
NEAR = 3  # lines of slack for hunk membership and dedup
CLUSTERED = frozenset({SymbolChange.SIGNATURE, SymbolChange.RENAMED})  # interface changes with a head-side span

type ExecLookup = Callable[[str], ExecRecord | None]


class Invalid(ValueError):
    pass


def _need(cond: object, msg: str) -> None:
    if not cond:
        raise Invalid(msg)


def _enum[E: (Axis, Severity, Verdict, Rung, ProofResult)](kind: type[E], value: Any, msg: str) -> E:
    try:
        return kind(value)
    except ValueError:
        raise Invalid(msg) from None


def _locs(v: object) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(e, str) and LOC.match(e) for e in v)


def validate_candidate(c: Any) -> Finding:
    _need(isinstance(c, dict), "candidate is not an object")
    c["axis"] = _enum(Axis, c.get("axis"), f"axis must be one of {' '.join(Axis)}")
    c["severity"] = _enum(Severity, c.get("severity"), "severity must be block|should-fix|nit")
    _need(isinstance(c.get("file"), str) and c["file"], "file required")
    _need(isinstance(c.get("line"), int) and c["line"] > 0, "line must be a positive int")
    c.setdefault("end_line", c["line"])
    _need(isinstance(c["end_line"], int) and c["end_line"] >= c["line"], "end_line must be an int >= line")
    _need(isinstance(c.get("claim"), str) and c["claim"].strip(), "claim required")
    _need(_locs(c.get("evidence_lines")), "evidence_lines must be a non-empty list of path:line")
    c["group"] = c["axis"].group
    c.setdefault("type", "defect")
    match c["group"]:
        case Group.FUNCTIONAL:
            _need(isinstance(c.get("trigger"), str) and c["trigger"].strip(), "trigger required for functional axes")
            pp = c.get("proof_plan")
            _need(
                isinstance(pp, dict) and pp.get("rung") in Rung and pp.get("idea"),
                "proof_plan {rung E0-E9, idea} required for functional axes",
            )
        case Group.EVOLVABILITY:
            _need(isinstance(c.get("rule"), str) and c["rule"].strip(), "rule required for evolvability axes")
    if c["axis"] in (Axis.SECURITY, Axis.PRIVACY):
        _need(isinstance(c.get("cwe"), int), "cwe (int) required for security and privacy")
    if c.get("precedent") is not None:
        _need(isinstance(c["precedent"], str) and LOC.match(c["precedent"]), "precedent must be path:line")
    return c


def validate_findings(v: Any) -> list[Any]:
    """Wrapper-level check (triggers the retry); per-candidate problems are rejected later, not retried."""
    _need(isinstance(v, dict) and isinstance(v.get("findings"), list), 'expected {"findings": [...]}')
    return v["findings"]


def validate_vote(v: Any) -> VoteRecord:
    _need(isinstance(v, dict), "vote must be an object")
    v["verdict"] = _enum(Verdict, v.get("verdict"), "verdict must be TRUE_POSITIVE|FALSE_POSITIVE|PREDATES_CHANGE")
    v["severity"] = _enum(Severity, v.get("severity"), "severity must be block|should-fix|nit")
    _need(isinstance(v.get("reason"), str), "reason required")
    _need(
        isinstance(v.get("cited"), list) and v["cited"] and all(isinstance(x, str) for x in v["cited"]),
        "cited must be a non-empty list of path:line",
    )
    return v


def validate_proof(v: Any) -> Proof:
    _need(isinstance(v, dict), "proof must be an object")
    v["rung"] = _enum(Rung, v.get("rung"), "rung must be E0-E9")
    v["result"] = _enum(ProofResult, v.get("result"), "result must be confirmed|not_reproduced|error")
    if v["result"] == ProofResult.CONFIRMED:
        _need(isinstance(v.get("before"), dict) and v["before"].get("exec_id"), "before.exec_id required")
        if v["rung"] in (Rung.E4, Rung.E6):
            _need(v.get("oracle_source"), "oracle_source required for E4/E6")
        if v["rung"] == Rung.E4:
            _need(isinstance(v.get("after"), dict) and v["after"].get("exec_id"), "after.exec_id required for E4")
    return v


def validate_intent(v: Any) -> dict[str, Any]:
    _need(isinstance(v, dict) and isinstance(v.get("claims"), list), "intent needs claims[]")
    v.setdefault("unit_notes", {})
    return v


def check_proof(proof: Proof, exec_record: ExecLookup) -> str | None:
    """Cross-check a 'confirmed' proof against arbiter's own exec records. Returns an error or None."""
    run_before = proof["before"]
    before = exec_record(run_before["exec_id"])
    if not before:
        return f"unknown exec_id {run_before['exec_id']}"
    if before["base"]:
        return "before run must be on HEAD (wt)"
    after = None
    match proof["rung"]:
        case Rung.E4:
            after = exec_record(proof["after"]["exec_id"])
            if not after:
                return f"unknown exec_id {proof['after']['exec_id']}"
            if before["exit_code"] == 0 or before["timed_out"]:
                return "E4 before run did not fail"
            if after["exit_code"] != 0:
                return "E4 after run did not pass"
        case Rung.E5 | Rung.E6 | Rung.E7 if before["exit_code"] == 0 or before["timed_out"]:
            return f"{proof['rung']} run exited 0: no detector/counterexample/surviving-mutant signal"
        case _ if before["timed_out"]:
            return "run timed out"
    # the agent's claimed commands and exit codes are replaced by arbiter's own record
    run_before["exit_code"], run_before["cmd"] = before["exit_code"], before["cmd"]
    if after:
        proof["after"]["exit_code"], proof["after"]["cmd"] = after["exit_code"], after["cmd"]
    return None


def in_hunks(c: Finding, ranges: Ranges) -> bool:
    return any(
        lo - NEAR <= c["line"] <= hi + NEAR or lo - NEAR <= c["end_line"] <= hi + NEAR
        for lo, hi in ranges.get(c["file"], [])
    )


def _overlaps(a: Finding, b: Finding) -> bool:
    return (
        a["file"] == b["file"]
        and a["group"] == b["group"]
        and b["line"] <= a["end_line"] + NEAR
        and a["line"] - NEAR <= b["end_line"]
    )


def _cited_symbol(f: Finding, symbols: Sequence[Symbol]) -> tuple[str, str] | None:
    """The changed interface a finding cites from elsewhere: an evidence line inside the symbol's definition
    while the finding itself sits outside it (the "stale caller of f" shape)."""
    cited = [(p, int(n)) for p, n in (e.rsplit(":", 1) for e in f["evidence_lines"])]
    for s in symbols:
        if s["change"] not in CLUSTERED or "lines" not in s:
            continue
        lo, hi = s["lines"]
        own = f["file"] == s["path"] and lo <= f["line"] <= hi
        if not own and any(p == s["path"] and lo <= n <= hi for p, n in cited):
            return s["path"], s["qualname"]
    return None


def _norm(s: str) -> str:
    return " ".join(s.split())


def _relocate(c: Finding, added: Mapping[str, Sequence[tuple[int, str]]]) -> bool:
    """OCR-style anchoring: move a finding to the added line its `quote` names. True when it moved."""
    want = _norm(c.get("quote") or "")
    if not want:
        return False
    lines = added.get(c["file"], ())
    hits = [n for n, text in lines if _norm(text) == want]
    if not hits and len(want) >= 12:
        hits = [n for n, text in lines if want in _norm(text)]
    if not hits:
        return False
    # shortcut: no LLM relocation stage (OCR stage 3); add it if relocation misses show up in rejected.json
    n = min(hits, key=lambda x: abs(x - c["line"]))
    delta = n - c["line"]
    c["relocated_from"] = c["line"]
    c["end_line"] = c.get("end_line", c["line"]) + delta
    c["line"] = n
    return True


def _repair(c: Any) -> None:
    """Fill empty or malformed evidence_lines from the finding's own file:line instead of rejecting it."""
    if (
        isinstance(c, dict)
        and isinstance(c.get("file"), str)
        and c["file"]
        and isinstance(c.get("line"), int)
        and c["line"] > 0
        and not _locs(c.get("evidence_lines"))
    ):
        c["evidence_lines"] = [f"{c['file']}:{c['line']}"]
        c["repaired"] = "evidence_lines set from file:line"


def merge(
    raw: Iterable[Any],
    ranges_by_unit: dict[str, Ranges],
    deep_k3: set[str],
    *,
    widen: Ranges | None = None,
    symbols: Sequence[Symbol] = (),
    added: Mapping[str, Sequence[tuple[int, str]]] | None = None,
) -> tuple[list[Finding], list[Any]]:
    """raw: candidates tagged with agent, pass and unit. Returns (merged, rejected).

    hier mode: `widen` (every changed hunk of the PR) replaces the unit's own hunks as the acceptance rule, and
    `symbols` (the change manifest) clusters findings citing one changed interface into one finding.
    `added` (path -> added (line, text)) lets a finding with a wrong line move to the line its `quote` names.
    """
    rejected: list[Any] = []
    kept: list[Finding] = []
    for c in raw:
        _repair(c)
        try:
            validate_candidate(c)
        except Invalid as e:
            rejected.append({**c, "reject_reason": str(e)})
            continue
        ranges = widen if widen is not None else ranges_by_unit.get(c["unit"], {})
        if not in_hunks(c, ranges) and not (added is not None and _relocate(c, added) and in_hunks(c, ranges)):
            where = "every changed hunk of the PR" if widen is not None else "the unit's changed hunks"
            rejected.append({**c, "reject_reason": f"line outside {where} ±{NEAR}"})
            continue
        kept.append(c)
    merged: list[Finding] = []
    passes: list[dict[str, set[int]]] = []
    for c in kept:
        for m, mp in zip(merged, passes, strict=True):
            if _overlaps(m, c):
                if AXIS_PRIORITY.index(c["axis"]) < AXIS_PRIORITY.index(m["axis"]):
                    # one issue per location: the highest-priority axis describes it (an injection beats the
                    # malformed-query logic bug and the missing test on the same line)
                    m.update({k: v for k, v in c.items() if k not in ("agent", "pass", "evidence_lines")})  # type: ignore[typeddict-item]
                m["axes"] = sorted({*m["axes"], c["axis"]})
                m["evidence_lines"] = sorted({*m["evidence_lines"], *c["evidence_lines"]})
                m["agents"] = sorted({*m["agents"], c["agent"]})
                mp.setdefault(c["agent"], set()).add(c["pass"])
                break
        else:
            merged.append({**c, "axes": [c["axis"]], "agents": [c["agent"]]})
            passes.append({c["agent"]: {c["pass"]}})
    if symbols:
        merged, passes = _cluster(merged, passes, symbols)
    out: list[Finding] = []
    for m, mp in zip(merged, passes, strict=True):
        # deep mode: a finding raised only by k=3 agents needs >=2 of their passes
        if deep_k3 and all(a in deep_k3 for a in m["agents"]) and max(map(len, mp.values())) < 2:
            rejected.append({**m, "passes": {}, "reject_reason": "deep: fewer than 2 of 3 passes"})
            continue
        m["passes"] = {a: sorted(p) for a, p in mp.items()}
        out.append(m)
    for n, m in enumerate(out, 1):
        m["id"] = f"f{n:03d}"
    return out, rejected


def _cluster(
    merged: list[Finding], passes: list[dict[str, set[int]]], symbols: Sequence[Symbol]
) -> tuple[list[Finding], list[dict[str, set[int]]]]:
    """Root-cause dedup (§4.3): findings of one group citing the same changed interface become one finding,
    the first one, with the others' sites in `locations`."""
    first: dict[tuple[str, str, str], int] = {}
    out: list[Finding] = []
    out_p: list[dict[str, set[int]]] = []
    for m, mp in zip(merged, passes, strict=True):
        sym = _cited_symbol(m, symbols)
        key = (m["group"], *sym) if sym else None
        if key is None or key not in first:
            if key:
                first[key] = len(out)
            out.append(m)
            out_p.append(mp)
            continue
        t, tp = out[first[key]], out_p[first[key]]
        t["locations"] = [*t.get("locations", []), f"{m['file']}:{m['line']}"]
        t["axes"] = sorted({*t["axes"], *m["axes"]})
        t["evidence_lines"] = sorted({*t["evidence_lines"], *m["evidence_lines"]})
        t["agents"] = sorted({*t["agents"], *m["agents"]})
        for a, ps in mp.items():
            tp.setdefault(a, set()).update(ps)
    return out, out_p


def never_dismiss(f: Finding) -> bool:
    return f["axis"] == Axis.DATA or (f["axis"] == Axis.SECURITY and f.get("cwe") in NEVER_DISMISS_CWE)


def tally(f: Finding, votes: list[VoteRecord | None], effort: str) -> Finding:
    """Set f['status'] from the panel's votes; TRUE votes can only lower the severity."""
    quick = Effort(effort) is Effort.QUICK
    if len(votes) < (1 if quick else 3) or any(v is None for v in votes):
        f["status"], f["status_reason"] = Status.SUSPECTED, "panel incomplete"
        return f
    cast = [v for v in votes if v is not None]
    quorum = 1 if quick else 2
    true = [v for v in cast if v["verdict"] == Verdict.TRUE_POSITIVE]
    if len(true) >= quorum:
        f["status"] = Status.VERIFIED
        f["severity"] = least_severe(f["severity"], *(v["severity"] for v in true))
    elif sum(v["verdict"] == Verdict.PREDATES_CHANGE for v in cast) >= quorum:
        f["status"] = Status.PRE_EXISTING
    elif never_dismiss(f):
        f["status"], f["status_reason"] = Status.SUSPECTED, "disputed"
    else:
        f["status"] = Status.DROPPED
    return f


def _precedent_ok(prec: str | None, wt: Path | None) -> bool:
    if not prec or not LOC.match(prec):
        return False
    if wt is None:
        return True
    path, line = prec.rsplit(":", 1)
    p = (wt / path).resolve()
    if not p.is_file() or not p.is_relative_to(wt.resolve()):
        return False
    return 1 <= int(line) <= len(p.read_text(errors="replace").splitlines())


def _place(f: Finding, placement: Placement, reason: str | None = None) -> Finding:
    f["placement"] = placement
    if reason:
        f["placement_reason"] = reason
    return f


def rule_key(s: str) -> str:
    """Normalized repo-rule heading: `[block]` marker removed, lower case, single spaces."""
    return " ".join(s.replace("[block]", "").lower().split())


def _rule_blocks(rule: str, blocking_rules: frozenset[str]) -> bool:
    path, sep, heading = rule.partition("#")
    return bool(sep) and f"{path}#{rule_key(heading)}" in blocking_rules


def gate(
    f: Finding,
    effort: str,
    wt: Path | None,
    *,
    env_gap: str | None = None,
    facts: Mapping[str, MaintFact] | None = None,
    blocking_rules: frozenset[str] = frozenset(),
) -> Finding:
    """Final placement for a tallied finding: main, suspected, dropped or pre-existing.

    env_gap: why no proof could run here (dependency fetch failed, no sandbox); a verified functional finding
    then goes to the main section as should-fix instead of Suspected. facts: arbiter's maintainability facts by
    id. blocking_rules: `path#heading` keys of repo rules marked `[block]`.
    """
    eff = Effort(effort)
    status = f.get("status")
    if status != Status.VERIFIED:
        if status == Status.SUSPECTED and f.get("severity") == Severity.BLOCK:
            f["severity"] = Severity.SHOULD_FIX
        return _place(f, Placement(status or Placement.DROPPED))
    proof = f.get("proof")
    confirmed_rung = proof["rung"] if proof and proof["result"] == ProofResult.CONFIRMED else None
    if f["group"] == Group.EVOLVABILITY:
        rule = f.get("rule") or ""
        fact = (facts or {}).get(f.get("measure") or "")
        if fact is not None and not (
            fact["path"] == f["file"] and fact["line"] - NEAR <= f["line"] <= fact["end_line"] + NEAR
        ):
            fact = None
        lint = bool(LINT_ID.match(rule))
        if not rule or not (lint or _precedent_ok(f.get("precedent"), wt) or fact is not None):
            return _place(f, Placement.DROPPED, "evolvability needs rule + precedent, lint id or measured fact")
        if f.get("code_judo") and eff is Effort.QUICK:
            return _place(f, Placement.DROPPED, "code judo off in quick")
        measured_block = fact is not None and fact["block"]
        judo_block = eff is Effort.DEEP and f.get("code_judo") and confirmed_rung == Rung.E1
        if f["severity"] == Severity.BLOCK and not (measured_block or _rule_blocks(rule, blocking_rules) or judo_block):
            f["severity"] = Severity.SHOULD_FIX
        if f["severity"] == Severity.BLOCK and measured_block and fact is not None:
            was = fact["base"] if fact["base"] is not None else "new"
            f["support"] = [
                *f.get("support", []),
                {"rung": Rung.E1, "tool": "arbiter-maintain", "msg": f"{fact['metric']} {was}→{fact['head']}"},
            ]
        return _place(f, Placement.MAIN)
    if confirmed_rung in ACCEPTED[Axis(f["axis"])] & EFFORT_RUNGS[eff]:
        return _place(f, Placement.MAIN)
    if f["axis"] == Axis.PERFORMANCE:
        return _place(f, Placement.DROPPED, "performance needs E8")
    if f["severity"] == Severity.BLOCK:
        f["severity"] = Severity.SHOULD_FIX  # only a proof blocks
    if env_gap:
        return _place(f, Placement.MAIN, f"{UNPROVABLE}: {env_gap}")
    return _place(f, Placement.SUSPECTED, "verified but unproven")


def verdict(findings: Iterable[Finding]) -> str:
    blocked = any(f.get("placement") == Placement.MAIN and f["severity"] == Severity.BLOCK for f in findings)
    return "block" if blocked else "pass"
