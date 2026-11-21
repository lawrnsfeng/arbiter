"""Schemas (hand-written validators), merge/dedup, vote tally, and the evidence gate."""

import re
from pathlib import Path

FUNCTIONAL = ("logic edge tests errors resources observability security privacy concurrency api data portability "
              "deps performance ops a11y spec").split()
EVOLVABILITY = ("maintainability", "idiom", "design", "docs")
# representative axis when several agents flag one location (most consequential first)
PRIORITY = ("security privacy data concurrency logic edge errors resources api spec deps portability performance "
            "observability ops a11y tests design maintainability idiom docs").split()
AXES = (*FUNCTIONAL, *EVOLVABILITY)
SEVERITY = ("block", "should-fix", "nit")  # rank 0 is most severe
VERDICTS = ("TRUE_POSITIVE", "FALSE_POSITIVE", "PREDATES_CHANGE")
RUNGS = tuple(f"E{i}" for i in range(10))
ACCEPTED = {
    "logic": {"E3", "E4", "E6"}, "edge": {"E3", "E4", "E6"}, "errors": {"E3", "E4"}, "resources": {"E4", "E5"},
    "concurrency": {"E4", "E5"}, "security": {"E3", "E4"}, "privacy": {"E3", "E4"}, "performance": {"E8"},
    "api": {"E1", "E4"}, "data": {"E4", "E9"}, "tests": {"E4", "E7"}, "deps": {"E1"}, "observability": {"E4"},
    "ops": {"E1"}, "portability": {"E1", "E4"}, "a11y": {"E1"}, "spec": {"E4", "E9"},
}
EFFORT_RUNGS = {"quick": {"E1", "E3"}, "standard": {"E1", "E2", "E3", "E4", "E5", "E6", "E8"},
                "deep": {f"E{i}" for i in range(1, 10)}}
NEVER_DISMISS_CWE = {78, 77, 89, 94, 79, 22, 502, 918, 862, 863, 639, 287, 306}
LOC = re.compile(r"^[^\s:]+:\d+$")
# linter ids: ruff/flake8/staticcheck (E501, SA4006), clippy::x, eslint (plugin/rule, no-x, prefer-x)
LINT_ID = re.compile(r"^([A-Z]{1,4}\d{3,4}|clippy::\w+|(@[\w-]+/)?[\w-]+/[\w-]+|(no|prefer)-[\w-]+)$")
NIT_CAP = 10


class Invalid(ValueError):
    pass


def _need(cond, msg):
    if not cond:
        raise Invalid(msg)


def validate_candidate(c: dict) -> dict:
    _need(isinstance(c, dict), "candidate is not an object")
    _need(c.get("axis") in AXES, f"axis must be one of {' '.join(AXES)}")
    _need(c.get("severity") in SEVERITY, "severity must be block|should-fix|nit")
    _need(isinstance(c.get("file"), str) and c["file"], "file required")
    _need(isinstance(c.get("line"), int) and c["line"] > 0, "line must be a positive int")
    c.setdefault("end_line", c["line"])
    _need(isinstance(c["end_line"], int) and c["end_line"] >= c["line"], "end_line must be an int >= line")
    _need(isinstance(c.get("claim"), str) and c["claim"].strip(), "claim required")
    ev = c.get("evidence_lines")
    _need(isinstance(ev, list) and ev and all(isinstance(e, str) and LOC.match(e) for e in ev),
          "evidence_lines must be a non-empty list of path:line")
    c["group"] = "functional" if c["axis"] in FUNCTIONAL else "evolvability"
    c.setdefault("type", "defect")
    if c["group"] == "functional":
        _need(isinstance(c.get("trigger"), str) and c["trigger"].strip(), "trigger required for functional axes")
        pp = c.get("proof_plan")
        _need(isinstance(pp, dict) and pp.get("rung") in RUNGS and pp.get("idea"),
              "proof_plan {rung E0-E9, idea} required for functional axes")
    else:
        _need(isinstance(c.get("rule"), str) and c["rule"].strip(), "rule required for evolvability axes")
    if c["axis"] in ("security", "privacy"):
        _need(isinstance(c.get("cwe"), int), "cwe (int) required for security and privacy")
    if c.get("precedent") is not None:
        _need(isinstance(c["precedent"], str) and LOC.match(c["precedent"]), "precedent must be path:line")
    return c


def validate_findings(v) -> list[dict]:
    """Wrapper-level check (triggers the retry); per-candidate problems are rejected later, not retried."""
    _need(isinstance(v, dict) and isinstance(v.get("findings"), list), 'expected {"findings": [...]}')
    return v["findings"]


def validate_vote(v) -> dict:
    _need(isinstance(v, dict), "vote must be an object")
    _need(v.get("verdict") in VERDICTS, "verdict must be TRUE_POSITIVE|FALSE_POSITIVE|PREDATES_CHANGE")
    _need(v.get("severity") in SEVERITY, "severity must be block|should-fix|nit")
    _need(isinstance(v.get("reason"), str), "reason required")
    _need(isinstance(v.get("cited"), list) and v["cited"] and all(isinstance(x, str) for x in v["cited"]),
          "cited must be a non-empty list of path:line")
    return v


def validate_proof(v) -> dict:
    _need(isinstance(v, dict), "proof must be an object")
    _need(v.get("rung") in RUNGS, "rung must be E0-E9")
    _need(v.get("result") in ("confirmed", "not_reproduced", "error"), "result must be confirmed|not_reproduced|error")
    if v["result"] == "confirmed":
        _need(isinstance(v.get("before"), dict) and v["before"].get("exec_id"), "before.exec_id required")
        if v["rung"] in ("E4", "E6"):
            _need(v.get("oracle_source"), "oracle_source required for E4/E6")
        if v["rung"] == "E4":
            _need(isinstance(v.get("after"), dict) and v["after"].get("exec_id"), "after.exec_id required for E4")
    return v


def validate_intent(v) -> dict:
    _need(isinstance(v, dict) and isinstance(v.get("claims"), list), "intent needs claims[]")
    v.setdefault("unit_notes", {})
    return v


def check_proof(proof: dict, exec_record) -> str | None:
    """Cross-check a 'confirmed' proof against arbiter's own exec records. Returns an error or None."""
    before = exec_record(proof["before"]["exec_id"])
    if not before:
        return f"unknown exec_id {proof['before']['exec_id']}"
    if before.get("base"):
        return "before run must be on HEAD (wt)"
    rung = proof["rung"]
    if rung == "E4":
        after = exec_record(proof["after"]["exec_id"])
        if not after:
            return f"unknown exec_id {proof['after']['exec_id']}"
        if before["exit_code"] == 0 or before["timed_out"]:
            return "E4 before run did not fail"
        if after["exit_code"] != 0:
            return "E4 after run did not pass"
    elif rung in ("E5", "E6", "E7") and (before["exit_code"] == 0 or before["timed_out"]):
        return f"{rung} run exited 0: no detector/counterexample/surviving-mutant signal"
    elif before["timed_out"]:
        return "run timed out"
    proof["before"]["exit_code"] = before["exit_code"]
    proof["before"]["cmd"] = before["cmd"]
    if rung == "E4":
        proof["after"]["exit_code"] = after["exit_code"]
        proof["after"]["cmd"] = after["cmd"]
    return None


def in_hunks(c: dict, ranges: dict[str, list[tuple[int, int]]]) -> bool:
    return any(lo - 3 <= c["line"] <= hi + 3 or lo - 3 <= c["end_line"] <= hi + 3
               for lo, hi in ranges.get(c["file"], []))


def merge(raw: list[dict], ranges_by_unit: dict[str, dict], deep_k3: set[str]) -> tuple[list[dict], list[dict]]:
    """raw: candidates tagged with agent, pass, unit. Returns (merged, rejected)."""
    rejected, kept = [], []
    for c in raw:
        try:
            validate_candidate(c)
        except Invalid as e:
            rejected.append({**c, "reject_reason": str(e)})
            continue
        if not in_hunks(c, ranges_by_unit.get(c["unit"], {})):
            rejected.append({**c, "reject_reason": "line outside the unit's changed hunks ±3"})
            continue
        kept.append(c)
    merged: list[dict] = []
    for c in kept:
        for m in merged:
            if (m["file"] == c["file"] and m["group"] == c["group"]
                    and c["line"] <= m["end_line"] + 3 and m["line"] - 3 <= c["end_line"]):
                if PRIORITY.index(c["axis"]) < PRIORITY.index(m["axis"]):
                    # one issue per location: the highest-priority axis describes it (an injection beats the
                    # malformed-query logic bug and the missing test on the same line)
                    m.update({k: v for k, v in c.items() if k not in ("agent", "pass", "evidence_lines")})
                m["axes"] = sorted(set(m["axes"]) | {c["axis"]})
                m["evidence_lines"] = sorted(set(m["evidence_lines"]) | set(c["evidence_lines"]))
                m["agents"] = sorted(set(m["agents"]) | {c["agent"]})
                m["passes"].setdefault(c["agent"], set()).add(c["pass"])
                break
        else:
            merged.append({**c, "axes": [c["axis"]], "agents": [c["agent"]], "passes": {c["agent"]: {c["pass"]}}})
    out = []
    for m in merged:
        # deep mode: a finding raised only by k=3 agents needs >=2 of their passes
        if deep_k3 and all(a in deep_k3 for a in m["agents"]) and max(len(p) for p in m["passes"].values()) < 2:
            rejected.append({**m, "passes": {}, "reject_reason": "deep: fewer than 2 of 3 passes"})
            continue
        m["passes"] = {a: sorted(p) for a, p in m["passes"].items()}
        out.append(m)
    for n, m in enumerate(out, 1):
        m["id"] = f"f{n:03d}"
    return out, rejected


def _min_sev(*sevs: str) -> str:
    return max(sevs, key=SEVERITY.index)


def never_dismiss(f: dict) -> bool:
    return f["axis"] == "data" or (f["axis"] == "security" and f.get("cwe") in NEVER_DISMISS_CWE)


def tally(f: dict, votes: list[dict | None], effort: str) -> dict:
    """Sets f['status'] in verified|pre-existing|suspected|dropped and lowers severity per TRUE votes."""
    need = 1 if effort == "quick" else 3
    if len(votes) < need or any(v is None for v in votes):
        f["status"], f["status_reason"] = "suspected", "panel incomplete"
        return f
    count = {k: sum(v["verdict"] == k for v in votes) for k in VERDICTS}
    quorum = 1 if effort == "quick" else 2
    if count["TRUE_POSITIVE"] >= quorum:
        f["status"] = "verified"
        f["severity"] = _min_sev(f["severity"], *(v["severity"] for v in votes if v["verdict"] == "TRUE_POSITIVE"))
    elif count["PREDATES_CHANGE"] >= quorum:
        f["status"] = "pre-existing"
    elif never_dismiss(f):
        f["status"], f["status_reason"] = "suspected", "disputed"
    else:
        f["status"] = "dropped"
    return f


def _precedent_ok(prec: str | None, wt: Path | None) -> bool:
    if not prec or not LOC.match(prec):
        return False
    if wt is None:
        return True
    path, line = prec.rsplit(":", 1)
    p = (wt / path).resolve()
    if not p.is_file() or not str(p).startswith(str(wt.resolve())):
        return False
    return 1 <= int(line) <= len(p.read_text(errors="replace").splitlines())


def gate(f: dict, effort: str, wt: Path | None) -> dict:
    """Final placement for a tallied finding: main | suspected | dropped | pre-existing."""
    if f.get("status") != "verified":
        if f.get("status") == "suspected" and f.get("severity") == "block":
            f["severity"] = "should-fix"
        f["placement"] = f.get("status")
        return f
    if f["group"] == "evolvability":
        lint = bool(LINT_ID.match(f.get("rule") or ""))
        if not f.get("rule") or not (lint or _precedent_ok(f.get("precedent"), wt)):
            f["placement"], f["placement_reason"] = "dropped", "evolvability needs rule + precedent or lint id"
            return f
        if f.get("code_judo") and effort == "quick":
            f["placement"], f["placement_reason"] = "dropped", "code judo off in quick"
            return f
        proof = f.get("proof") or {}
        judo_block = (effort == "deep" and f.get("code_judo") and proof.get("result") == "confirmed"
                      and proof.get("rung") == "E1")
        if f["severity"] == "block" and not judo_block:
            f["severity"] = "should-fix"
        f["placement"] = "main"
        return f
    proof = f.get("proof") or {}
    if proof.get("result") == "confirmed" and proof.get("rung") in ACCEPTED[f["axis"]] & EFFORT_RUNGS[effort]:
        f["placement"] = "main"
    elif f["axis"] == "performance":
        f["placement"], f["placement_reason"] = "dropped", "performance needs E8"
    else:
        f["placement"], f["placement_reason"] = "suspected", "verified but unproven"
        if f["severity"] == "block":
            f["severity"] = "should-fix"  # suspected never blocks
    return f


def verdict(findings: list[dict]) -> str:
    return "block" if any(f.get("placement") == "main" and f["severity"] == "block" for f in findings) else "pass"
