"""The review pipeline: plan -> sandbox -> gates -> intent -> finders -> merge -> verify -> proofs -> gate -> report.

Every stage reads and writes JSON in the RUN directory, so any stage can be rerun alone.
"""

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, NamedTuple

from . import ArbiterExit, agents, decompose, harness, maintain, report, sandbox, tools, triggers
from . import findings as F
from . import lang as langmod
from .gates import gates
from .harness import Tools
from .model import (
    Axis,
    Decompose,
    Effort,
    Finding,
    Group,
    Lang,
    Placement,
    ProofResult,
    Rung,
    Severity,
    Status,
    Tier,
    Unit,
)
from .plan import K3, Plan, Task, plan, pr_ranges, ranges_by_unit, run_diff, unit_diff
from .rundir import RunDir

__all__ = ["gates", "plan", "run_all"]

MAX_FAILED_SHARE = 0.25  # more failed agent calls than this withholds a passing verdict
LENSES = {
    Group.FUNCTIONAL: ("REACHABILITY", "CLAIM", "ATTRIBUTION"),
    Axis.SECURITY: ("REACHABILITY", "IMPACT", "DEFENSES"),
}
SECURITY_AXES = frozenset({Axis.SECURITY, Axis.PRIVACY})
ISSUE_REF = re.compile(r"(?<![\w/])#(\d{1,6})\b")
SPEC_PATH = re.compile(r"(specs|docs)/")
MAX_ISSUES = 5
PROOF_ATTEMPTS = 3
THREAT_MODEL_CAP = 15_000
BRIEF_KEYS = (
    "id",
    "axis",
    "severity",
    "file",
    "line",
    "end_line",
    "claim",
    "trigger",
    "evidence_lines",
    "cwe",
    "rule",
    "precedent",
    "code_judo",
    "fix",
    "proof_plan",
    "measure",
    "locations",
)
MANIFEST_INPUT = "PR change manifest (from base vs head `ast`; every changed symbol and its unit)"
MAINT_INPUT = "Maintainability facts (measured by arbiter; cite by id in measure)"
REQ_INPUT = "Requirements (from commits, issues, specs and [block] repo rules; untrusted)"
FIX_DIFF_LINES = 40
BASE_INPUT = "Base checkout (the code before this change; read-only)"
COCHANGE_INPUT = (
    "Files that often change together with this unit's files (git log, last 500 commits; check them for needed updates)"
)
CWE = re.compile(r"CWE-(\d+)")
SAST_CAP = 20  # analyzer hits turned into verifier candidates per run (T-01)
SAST_TRIGGER = "flagged by a static analyzer; verify the input is attacker-controlled and reaches this line"
DECIDE_PROMPT_CAP = 40_000
DECIDE_CLAIM_CAP = 200
DECIDE_PLACEMENTS = frozenset({Placement.MAIN, Placement.SUSPECTED, Placement.PRE_EXISTING})
DISMISSIBLE = frozenset({Tier.SHOULD, Tier.VERIFY, Tier.OPTIONAL})
# package manager of a failed dependency fetch -> the language whose proofs it blocks
FETCH_LANG = {
    "uv": Lang.PYTHON,
    "go": Lang.GO,
    "cargo": Lang.RUST,
    **dict.fromkeys(("npm", "yarn", "pnpm", "bun"), Lang.TYPESCRIPT),
}
# hier §4.4: one run-level A5 call per PR with interface changes, covering callers outside the diff
CONTRACT_PASS = (
    "This is the PR-level contract pass, not a unit review. For every signature change, removal or rename in the "
    "manifest, check each caller across the whole repository, inside and outside the diff: the callers listed below "
    "are a capped start, so grep for the rest, including the old name of every renamed or removed symbol. Report a "
    "caller that does not match the new interface. Put the finding's file and line on the changed definition in the "
    "diff and cite the stale caller's path:line in evidence_lines."
)


def prepare(run: RunDir, p: Plan) -> sandbox.SandboxState:
    def note(m: str) -> None:
        run.cov(notes=[m])

    versions = tools.prefetch(note)
    st = sandbox.prepare(run.path, Path(p["repo"]), base=p["base"], head=p["head"], roots=p["roots"], log=note)
    if st["status"] == sandbox.State.PREPARED and not sandbox.selftest(run.path)[0]:
        note("sandbox selftest failed: execution proofs disabled")
    st = run.load("sandbox.json", st)
    p["tools"] = [tools.resolve(s) for s in p["tools"]]
    run.save("plan.json", p)
    run.cov(
        sandbox=st["status"],
        sandbox_notes=st.get("notes", []),
        tool_versions=versions,
        tools=[
            {"name": s["name"], "lang": s.get("lang"), "available": s.get("available"), "source": s.get("source")}
            for s in p["tools"]
        ],
    )
    return st


# ---------------------------------------------------------------- agent stages


class Job(NamedTuple):
    unit: str
    agent: str
    pass_: int
    langs: Sequence[str]
    inputs: dict[str, str]


def _cwd(run: RunDir, p: Plan) -> Path:
    return run.worktree or Path(p["repo"])


def _facts(p: Plan, u: Unit | None = None) -> str:
    lines = [
        f"repo: {Path(p['repo']).name}",
        f"base: {p['base'][:12]}",
        f"head: {p['head'][:12]}",
        f"effort: {p['effort']}",
        "Paths are relative to the repository root (your working directory).",
    ]
    if u and u["plan_required"]:
        lines.append("This unit is large: first list the behaviours it changes, then check each.")
    return "\n".join(lines)


def _parallel[T, R](jobs: int, fn: Callable[[T], R], items: Iterable[T]) -> list[R]:
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        return list(ex.map(fn, items))


def _linked_issues(p: Plan) -> list[str]:
    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode:
        return []
    refs = sorted({int(n) for c in p["commits"] for n in ISSUE_REF.findall(c)})[:MAX_ISSUES]
    issues = []
    for n in refs:
        r = subprocess.run(
            ["gh", "issue", "view", str(n), "--json", "title,body"],
            cwd=p["repo"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode == 0:
            issues.append(f"#{n}: {r.stdout[:4000]}")
    return issues


def intent(run: RunDir, p: Plan) -> dict[str, Any]:
    """A0: claims to verify (never trusted) and the threat model, drafted when the repo has none."""
    tm = p["threat_model"]
    inputs = {
        "EFFORT": p["effort"],
        "Run facts": _facts(p),
        "Commit messages": "\n\n".join(p["commits"]) or "(none)",
        "Changed files": "\n".join(f"{f['path']} (+{f['added']} -{f['deleted']})" for f in p["files"]),
        "Spec or docs files changed": "\n".join(f["path"] for f in p["files"] if SPEC_PATH.match(f["path"]))
        or "(none)",
        "Linked issues": "\n\n".join(_linked_issues(p)) or "(none fetched)",
        "Units": "\n".join(
            f"{u['id']}: {', '.join(x['path'] for x in u['files'])} "
            f"(churn {u['churn']}{', plan_required' if u['plan_required'] else ''})"
            for u in p["units"]
        ),
        "Threat model": f"exists at {tm}; do not draft one"
        if tm
        else "none exists; add threat_model_draft using the template headings: Assets, Entry points, Trust boundaries, "
        "Trusted inputs, In-scope classes, Out-of-scope classes, DoS policy",
    }
    prompt, _ = agents.build_prompt("A0", [], inputs)
    val, err = agents.run("A0", "A0", prompt, F.validate_intent, tools=Tools.FINDER, cwd=_cwd(run, p))
    val = val or {"claims": [], "spec_source": "none", "threat_model_path": tm or "none", "unit_notes": {}}
    tm_text, tm_path, drafted = "", tm, False
    if tm and (src := _cwd(run, p) / tm).exists():
        tm_text = src.read_text(errors="replace")[:THREAT_MODEL_CAP]
    elif draft := val.get("threat_model_draft"):
        (run / "THREAT_MODEL.draft.md").write_text(draft)
        tm_text, tm_path, drafted = draft, str(run / "THREAT_MODEL.draft.md"), True
    val |= {"threat_model_text": tm_text, "threat_model_path": tm_path, "threat_model_drafted": drafted}
    val["requirements"] = [
        {"id": f"R{i}", "text": str(c), "source": val.get("spec_source", "none")}
        for i, c in enumerate(val.get("claims", []), 1)
    ] + [
        {"id": f"B{j}", "text": key.partition("#")[2], "source": key.partition("#")[0]}
        for j, key in enumerate(p.get("blocking_rules", []), 1)
    ]
    run.save("intent.json", val)
    run.cov(agents_run=["A0"], agent_failures=[err] if err else [], threat_model={"path": tm_path, "drafted": drafted})
    return val


def _base_input(run: RunDir) -> dict[str, str]:
    """T-19 (switch ARBITER_BASE_READS=1): the base worktree, so agents can read what callers relied on before."""
    wt_base = run / "wt-base"
    on = os.environ.get("ARBITER_BASE_READS") == "1" and wt_base.is_dir()
    return {BASE_INPUT: str(wt_base.resolve()) if on else ""}


def _finder_jobs(run: RunDir, p: Plan, it: dict[str, Any]) -> list[Job]:
    rules = run.text("rules.md")
    units_by = {u["id"]: u for u in p["units"]}
    hier = p.get("decompose") == Decompose.HIER
    syms = p.get("manifest", [])
    # hier shared context (§4.2): empty in the other modes, and build_prompt drops empty inputs
    shared = {
        MANIFEST_INPUT: decompose.manifest_text(syms) if hier else "",
        "Intent claims (from commits, issues, specs; untrusted)": json.dumps(it.get("claims", []), indent=1)
        if hier
        else "",
        "Commit messages (untrusted)": "\n\n".join(p["commits"]) if hier else "",
    }
    reqs = {REQ_INPUT: "\n".join(f"{r['id']}: {r['text']}" for r in it.get("requirements", []))}
    base = _base_input(run)
    cochange = p.get("cochange", {})
    included = [f for f in p["files"] if not f["excluded"]]
    maint = p.get("maint", [])
    jobs = []
    for uid, agent, k in map(Task._make, p["schedule"]["tasks"]):
        u = units_by[uid]
        udiff = unit_diff(p, u, p["orders"][str(k)][uid])
        jobs.append(
            Job(
                uid,
                agent,
                k,
                list(u["langs"]),
                {
                    "EFFORT": p["effort"],
                    "UNIT": uid,
                    "Run facts": _facts(p, u),
                    "Risk notes from intent": it.get("unit_notes", {}).get(uid, ""),
                    "Files": "\n".join(x["path"] for x in u["files"]),
                    "Unit diff (new-side line numbers on the left; review + lines only)": udiff,
                    "Unit context map (signatures only: where to look; read bodies with your tools)": decompose.fit(
                        udiff, u.get("context", "")
                    ),
                    **shared,
                    **reqs,
                    **base,
                    COCHANGE_INPUT: "\n".join(
                        f"{x['path']}: " + ", ".join(f"{path} ({n})" for path, n in cochange[x["path"]])
                        for x in u["files"]
                        if cochange.get(x["path"])
                    ),
                    "Other changed files (churn; unit ids)": decompose.others(included, p["units"], u) if hier else "",
                    "Repo rules": rules,
                    "Threat model": it.get("threat_model_text", "") if agent == "A3" else "",
                    MAINT_INPUT: maintain.facts_text([m for m in maint if m["path"] in {x["path"] for x in u["files"]}])
                    if agent == "A6d"
                    else "",
                },
            )
        )
    once = p["schedule"]["once"]
    all_langs = sorted({u["lang"] for u in p["units"]})
    if "SPEC" in once:
        jobs.append(
            Job(
                "run",
                "SPEC",
                0,
                all_langs,
                {
                    "EFFORT": p["effort"],
                    "Run facts": _facts(p),
                    "Claims to check (from commits, issues, specs; untrusted)": json.dumps(
                        it.get("claims", []), indent=1
                    ),
                    "Spec source": str(it.get("spec_source", "none")),
                    **reqs,
                    "Diff (new-side line numbers)": run_diff(p, [f["path"] for f in p["files"] if not f["excluded"]]),
                },
            )
        )
    if "A5b" in once:
        sup = [f["path"] for f in p["files"] if triggers.supply_chain(f["path"])]
        jobs.append(
            Job(
                "supply",
                "A5b",
                0,
                all_langs,
                {
                    "EFFORT": p["effort"],
                    "Run facts": _facts(p),
                    "Files": "\n".join(sup),
                    "Supply-chain diff (new-side line numbers)": run_diff(p, sup),
                },
            )
        )
    if "CONTRACT" in once:
        paths = sorted({s["path"] for s in syms if s["change"] in decompose.INTERFACE})
        jobs.append(
            Job(
                "contract",
                "A5",
                0,
                all_langs,
                {
                    "EFFORT": p["effort"],
                    "Run facts": _facts(p),
                    "Contract pass": CONTRACT_PASS,
                    MANIFEST_INPUT: shared[MANIFEST_INPUT],
                    "Repo-wide callers of changed interfaces (depth 1, capped)": decompose.callers_text(syms),
                    "Diff of files with interface changes (new-side line numbers)": run_diff(p, paths),
                    "Repo rules": rules,
                    **reqs,
                    **base,
                },
            )
        )
    return jobs


def finders(run: RunDir, p: Plan, it: dict[str, Any], jobs: int) -> list[dict[str, Any]]:
    (run / "prompts").mkdir(exist_ok=True)

    def one(job: Job) -> tuple[list[dict[str, Any]], str | None, str]:
        prompt, _ = agents.build_prompt(job.agent, job.langs, job.inputs)
        (run / "prompts" / f"{job.unit}-{job.agent}-{job.pass_}.md").write_text(prompt)
        val, err = agents.run(job.agent, job.agent, prompt, F.validate_findings, tools=Tools.FINDER, cwd=_cwd(run, p))
        cands = [
            {**c, "agent": job.agent, "pass": job.pass_, "unit": job.unit}
            for c in (val or {}).get("findings", [])
            if isinstance(c, dict)
        ]
        return cands, err, f"{job.agent}@{job.unit}#{job.pass_}"

    results = _parallel(jobs, one, _finder_jobs(run, p, it))
    raw = [c for cands, _, _ in results for c in cands]
    run.save("raw.json", raw)
    run.cov(
        agents_run=[name for *_, name in results],
        agent_failures=[e for _, e, _ in results if e],
        agents_skipped=p["schedule"]["skipped"],
    )
    return raw


def _sast_candidates(run: RunDir, p: Plan, merged: list[Finding]) -> list[dict[str, Any]]:
    """T-01: analyzer hits on added lines that no agent finding covers become verifier candidates."""
    ranges = pr_ranges(p)
    hits = sorted(run.load("gates.json", {}).get("analyzer_hits", []), key=lambda h: (h["tool"], h["path"], h["line"]))
    out: list[dict[str, Any]] = []
    for h in hits:
        if not any(lo <= h["line"] <= hi for lo, hi in ranges.get(h["path"], [])):
            continue
        if any(f["file"] == h["path"] and abs(f["line"] - h["line"]) <= F.NEAR for f in merged):
            continue
        rule = h.get("rule") or ""
        out.append(
            {
                "axis": "security",
                "severity": "should-fix",
                "file": h["path"],
                "line": h["line"],
                "claim": f"{h['tool']} {rule}: {str(h.get('msg', ''))[:200]}",
                "trigger": SAST_TRIGGER,
                "evidence_lines": [f"{h['path']}:{h['line']}"],
                "cwe": int(m[1]) if (m := CWE.search(f"{rule} {h.get('msg', '')}")) else 0,
                "proof_plan": {"rung": "E3", "idea": "run the flagged code path with attacker-controlled input"},
                "agent": "sast",
                "pass": 0,
                "unit": "run",
            }
        )
        if len(out) == SAST_CAP:
            break
    return out


def merge(run: RunDir, p: Plan) -> list[Finding]:
    hier = p.get("decompose") == Decompose.HIER
    merged, rejected = F.merge(
        run.load("raw.json", []),
        ranges_by_unit(p),
        set(K3) if p["effort"] == Effort.DEEP else set(),
        widen=pr_ranges(p) if hier else None,
        symbols=p.get("manifest", []) if hier else (),
        added={f["path"]: [(n, t) for h in f["hunks"] for n, t in h["added"]] for f in p["files"] if not f["excluded"]},
    )
    sast_raw = _sast_candidates(run, p, merged) if os.environ.get("ARBITER_SAST_CANDIDATES") == "1" else []
    sast, sast_rejected = F.merge(sast_raw, {"run": pr_ranges(p)}, set())
    merged += sast
    for n, m in enumerate(merged, 1):
        m["id"] = f"f{n:03d}"
    run.save("candidates.json", merged)
    run.save("rejected.json", rejected + sast_rejected)
    return merged


def _finding_brief(f: Finding) -> str:
    return json.dumps({k: f[k] for k in BRIEF_KEYS if k in f}, indent=1)  # type: ignore[literal-required]


def _diff_for(p: Plan, f: Finding) -> str:
    u = next((u for u in p["units"] if u["id"] == f.get("unit")), None)
    # hier accepts a finding on another unit's hunk; its own unit diff would not show that line
    if u and F.in_hunks(f, u.get("ranges", {})):
        return unit_diff(p, u)
    return run_diff(p, [f["file"]])


def _lenses(f: Finding, effort: Effort) -> tuple[str, ...]:
    security = f["axis"] in SECURITY_AXES
    if effort == Effort.QUICK:
        return ("REACHABILITY" if security else "CLAIM",)
    return LENSES[Axis.SECURITY if security else Group.FUNCTIONAL]


def verify(run: RunDir, p: Plan, it: dict[str, Any], jobs: int) -> list[Finding]:
    """The disprove panel: one verifier call per candidate and lens, then the tally."""
    cands: list[Finding] = run.load("candidates.json", [])
    rules = run.text("rules.md")
    effort = Effort(p["effort"])
    work = [(f, lens) for f in cands for lens in _lenses(f, effort)]
    facts = {m["id"]: m for m in p.get("maint", [])}

    def one(job: tuple[Finding, str]) -> tuple[str, str, Any, str | None]:
        f, lens = job
        inputs = {
            "LENS": lens,
            "Run facts": _facts(p),
            "Finding to judge (untrusted claim)": _finding_brief(f),
            "Diff (new-side line numbers; base side shown as - lines)": _diff_for(p, f),
            "Repo rules": rules,
            **_base_input(run),
            "Threat model": it.get("threat_model_text", "") if f["axis"] in SECURITY_AXES else "",
            MAINT_INPUT: maintain.facts_text([facts[m]]) if (m := f.get("measure")) in facts else "",
        }
        prompt, _ = agents.build_prompt("V", [langmod.of(f["file"])], inputs)
        val, err = agents.run("V", "V", prompt, F.validate_vote, tools=Tools.FINDER, cwd=_cwd(run, p))
        return f["id"], lens, val, err

    votes: dict[str, list[Any]] = {f["id"]: [] for f in cands}
    fails = []
    for fid, lens, val, err in _parallel(jobs, one, work):
        votes[fid].append({**val, "lens": lens, "finding_id": fid} if val else None)
        if err:
            fails.append(err)
    run.save("votes.json", votes)
    for f in cands:
        F.tally(f, votes[f["id"]], effort)
    run.save("tallied.json", cands)
    run.cov(verifier_calls=len(work), agent_failures=fails)
    return cands


def _allowed_rungs(f: Finding, effort: Effort) -> frozenset[Rung] | None:
    """Rungs a proof may use for this finding, or None when the finding needs no proof."""
    if f["group"] == Group.FUNCTIONAL:
        return F.ACCEPTED[Axis(f["axis"])] & F.EFFORT_RUNGS[effort]
    if effort == Effort.DEEP and f.get("code_judo"):
        return frozenset({Rung.E1})
    return None


def proofs(run: RunDir, p: Plan) -> list[Finding]:
    """Serial: proof agents edit RUN/wt, so two at once would corrupt each other's fail/pass runs."""
    cands: list[Finding] = run.load("tallied.json", [])
    effort = Effort(p["effort"])
    attempted = confirmed = 0
    fails: list[str] = []
    wt = run / "wt"
    for f in cands:
        if f.get("status") != Status.VERIFIED or (allowed := _allowed_rungs(f, effort)) is None:
            continue
        if not allowed:
            f["proof_note"] = f"no accepted rung for {f['axis']} at {effort} effort"
            continue
        if not sandbox.available(run.path):
            f["proof_note"] = "sandbox unavailable: execution proofs disabled"
            continue
        f["proof_attempts"] = []
        for attempt in range(1, PROOF_ATTEMPTS + 1):
            attempted += 1
            inputs = {
                "RUN": str(run.path),
                # the exact interpreter running this review, so the proof agent needs no install or path guess
                "SANDBOX": f"{sys.executable} -P -m arbiter.cli sandbox exec {run.path}",
                "ALLOWED_RUNGS": " ".join(sorted(allowed)),
                "FINDING_ID": f["id"],
                "EFFORT": effort,
                "Run facts": f"{_facts(p)}\nattempt {attempt} of {PROOF_ATTEMPTS} (independent)",
                "Finding to prove": _finding_brief(f),
                "Diff": _diff_for(p, f),
            }
            prompt, _ = agents.build_prompt("P", [langmod.of(f["file"])], inputs)
            val, err = agents.run("P", "P", prompt, F.validate_proof, tools=Tools.PROOF, cwd=wt, timeout=900)
            # the minimal fix an E4 proof applied, kept for the report before the revert below
            fix_diff = subprocess.run(
                ["git", "-C", str(wt), "diff", "--", ".", ":(exclude)arbiter_proofs"], capture_output=True, text=True
            ).stdout
            subprocess.run(["git", "-C", str(wt), "checkout", "--", "."], capture_output=True)  # revert any minimal fix
            if err:
                fails.append(err)
                f["proof_attempts"].append({"error": err})
                continue
            if val["result"] == ProofResult.CONFIRMED:
                if val["rung"] not in allowed:
                    val["result"], val["check"] = ProofResult.ERROR, f"rung {val['rung']} not in {sorted(allowed)}"
                elif bad := F.check_proof(val, lambda x: sandbox.exec_record(run.path, x)):
                    val["result"], val["check"] = ProofResult.ERROR, bad
            f["proof_attempts"].append(val)
            if val["result"] == ProofResult.CONFIRMED:
                f["proof"] = val
                if fix_diff.strip():
                    f["proof_fix_diff"] = "\n".join(fix_diff.splitlines()[:FIX_DIFF_LINES])
                confirmed += 1
                break
    run.save("proved.json", cands)
    run.cov(proofs={"attempted": attempted, "confirmed": confirmed}, agent_failures=fails)
    return cands


def _env_gap(run: RunDir, f: Finding) -> str | None:
    """Why no proof could run for f in this environment, or None. A policy limit (no accepted rung at this
    effort) is not an environment gap, and a failed fetch counts only for the finding's own ecosystem."""
    note = f.get("proof_note", "")
    if note.startswith("sandbox unavailable"):
        return "sandbox unavailable"
    if note.startswith("no accepted rung"):
        return None
    lang = langmod.of(f["file"])
    for e in run.load("sandbox.json", {}).get("fetch", []):
        root = e["root"]
        in_root = root in ("", ".") or f["file"].startswith(root.rstrip("/") + "/")
        tool = e.get("cmd", "").split(" ", 1)[0]
        if e["wt"] == "wt" and e["exit_code"] and in_root and FETCH_LANG.get(tool) == lang:
            return f"dependency fetch failed in {root or '.'} ({tool})"
    return None


def final_gate(run: RunDir, p: Plan) -> list[Finding]:
    cands: list[Finding] = run.load("proved.json") or run.load("tallied.json", [])
    g = run.load("gates.json", {"findings": [], "analyzer_hits": []})
    facts = {m["id"]: m for m in p.get("maint", [])}
    blocking = frozenset(p.get("blocking_rules", []))
    for f in cands:
        f.setdefault("source", "agent")
        F.gate(
            f,
            p["effort"],
            run.worktree,
            env_gap=_env_gap(run, f) if f.get("status") == Status.VERIFIED else None,
            facts=facts,
            blocking_rules=blocking,
        )
        if sup := [
            h for h in g.get("analyzer_hits", []) if h["path"] == f["file"] and abs(h["line"] - f["line"]) <= F.NEAR
        ]:
            f["support"] = [*f.get("support", []), *({"rung": Rung.E2, **h} for h in sup)]
    # an agent finding in main absorbs an overlapping non-blocking gate hit (one finding per issue)
    main = [f for f in cands if f.get("placement") == Placement.MAIN]
    gate_findings = []
    for gf in g.get("findings", []):
        hit = next((f for f in main if f["file"] == gf["file"] and abs(f["line"] - gf["line"]) <= F.NEAR), None)
        if hit and gf["severity"] != Severity.BLOCK:
            hit.setdefault("support", []).append({"rung": Rung.E1, "tool": gf["agents"][0], "msg": gf["claim"]})
        else:
            gate_findings.append(gf)
    allf = gate_findings + cands
    nits = sorted(
        (f for f in allf if f.get("placement") == Placement.MAIN and f["severity"] == Severity.NIT),
        key=lambda f: (Axis(f["axis"]).group == Group.EVOLVABILITY, -len(f.get("agents", []))),
    )
    for f in nits[F.NIT_CAP :]:
        f["placement"] = Placement.NIT_OVERFLOW
    run.save("final.json", allf)
    return allf


def _decide_prompt(inputs: dict[str, str], items: list[dict[str, Any]]) -> str:
    return agents.build_prompt("DECIDE", [], {**inputs, "Findings": json.dumps(items, indent=1)})[0]


def decide(run: RunDir, p: Plan, it: dict[str, Any], allf: list[Finding]) -> list[Finding]:
    """One end-of-run call to the decide model (Opus). Strict: once per RUN (claim file), no retry, no tools,
    an omp cost cap. Its output only links, dismisses non-blocking findings, challenges and adds unverified
    concerns; it never adds or removes a block."""
    model, cap = harness.decide_model(), harness.decide_max_usd()
    try:
        os.close(os.open(run / "decide.claim", os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        run.cov(notes=["decide: already called for this RUN; not called again"])
        return allf
    order = list(Tier)  # most urgent first, so clipping from the end drops the least urgent
    shown = sorted(
        (f for f in allf if f.get("placement") in DECIDE_PLACEMENTS), key=lambda f: order.index(report.tier(f))
    )
    tiers = {f["id"]: report.tier(f) for f in shown}
    items: list[dict[str, Any]] = [
        {
            "id": f["id"],
            "tier": tiers[f["id"]],
            "axis": f["axis"],
            "file": f["file"],
            "line": f["line"],
            "claim": f["claim"],
            "trigger": f.get("trigger", ""),
            "evidence": p_["rung"] if (p_ := f.get("proof")) and p_["result"] == ProofResult.CONFIRMED else "none",
            "addresses": f.get("addresses"),
        }
        for f in shown
    ]
    inputs = {
        "Requirements": "\n".join(f"{r['id']}: {r['text']}" for r in it.get("requirements", [])) or "(none)",
        "Axes checked": "\n".join(report.axes_rows(shown, run.load("coverage.json", {}))),
        "Run facts": _facts(p),
    }
    prompt = _decide_prompt(inputs, items)
    for step in (Tier.OPTIONAL, Tier.FYI, "claims"):
        if len(prompt) <= DECIDE_PROMPT_CAP:
            break
        if step == "claims":
            items = [{**x, "claim": x["claim"][:DECIDE_CLAIM_CAP]} for x in items]
        else:
            items = [x for x in items if x["tier"] != step]
        prompt = _decide_prompt(inputs, items)
    while len(prompt) > DECIDE_PROMPT_CAP and items:  # least urgent tier last, so it goes first
        items.pop()
        prompt = _decide_prompt(inputs, items)
    (run / "prompts").mkdir(exist_ok=True)
    (run / "prompts" / "decide.md").write_text(prompt)
    cov: dict[str, Any] = {"model": model, "called": True, "ok": False, "max_usd": float(cap)}
    try:  # harness.call directly: agents.run and agents._call both retry
        val = F.validate_decision(
            agents.extract_json(harness.call(harness.DECIDE, prompt, tools=Tools.NONE, cwd=run.path, timeout=600))
        )
    except (harness.HarnessError, ValueError, TypeError, KeyError) as e:
        run.cov(notes=[f"decide: {str(e)[:300]}"], decide=cov)
        return allf
    by_id = {f["id"]: f for f in shown}
    for fid, rid in val["links"].items():
        if (f := by_id.get(fid)) and "addresses" not in f and isinstance(rid, str) and F.REQ_ID.match(rid):
            f["addresses"] = rid
    dismissed = challenged = 0
    for d in val["dismiss"]:
        if (f := by_id.get(d["id"])) and tiers[d["id"]] in DISMISSIBLE:
            f["placement"], f["placement_reason"] = Placement.DROPPED, f"decision: {d['reason']}"
            dismissed += 1
    for c in val["challenge"]:
        if (f := by_id.get(c["id"])) and tiers[c["id"]] == Tier.MUST:
            f["challenge"] = c["reason"]
            challenged += 1
    ranges = pr_ranges(p)
    missed = 0
    for m in val["missed"]:
        axis = Axis(m["axis"])
        nf = Finding(
            id=f"d{missed + 1:02d}",
            source="decide",
            agents=["DECIDE"],
            axis=axis,
            axes=[axis],
            group=axis.group,
            severity=Severity.SHOULD_FIX,
            status=Status.SUSPECTED,
            placement=Placement.SUSPECTED,
            placement_reason="raised by the decision model; unverified",
            file=m["file"],
            line=m["line"],
            end_line=m["line"],
            claim=m["claim"],
            evidence_lines=[f"{m['file']}:{m['line']}"],
        )
        if not F.in_hunks(nf, ranges):  # the brief allows changed lines only
            continue
        if rid := m.get("addresses"):
            nf["addresses"] = rid
        allf.append(nf)
        missed += 1
    run.save("decision.json", val)
    run.save("final.json", allf)
    run.cov(decide=cov | {"ok": True, "dismissed": dismissed, "challenged": challenged, "missed": missed})
    return allf


def _withhold(run: RunDir) -> str | None:
    """A gate must not pass on silence: too many failed agent calls withhold a passing verdict."""
    c = run.load("coverage.json", {})
    failed = len(c.get("agent_failures", []))
    ran = len(c.get("agents_run", [])) + c.get("verifier_calls", 0)
    return f"{failed} of {ran} agent calls failed" if ran and failed > MAX_FAILED_SHARE * ran else None


def run_all(
    repo: Path,
    *,
    base: str | None,
    effort: str,
    langs: list[str] | None,
    out: Path | None,
    jobs: int,
    max_agents: int,
    decompose_mode: str = Decompose.OCR,
) -> tuple[Path, str]:
    t0 = time.monotonic()
    run = RunDir(out) if out else RunDir.default_for(repo)
    run.path.mkdir(parents=True, exist_ok=True)
    print(run.path, flush=True)
    s = harness.settings()
    p = plan(run, repo, base_ref=base, effort=effort, langs=langs, max_agents=max_agents, decompose_mode=decompose_mode)
    run.cov(
        harness=s.harness,
        models={"finder": f"{s.model} ({s.model_source})", "verify": f"{s.verify_model} ({s.verify_source})"},
        effort=effort,
    )
    try:
        prepare(run, p)
        gates(run, p)
        it = intent(run, p)
        finders(run, p, it, jobs)
        merge(run, p)
        verify(run, p, it, jobs)
        proofs(run, p)
        allf = final_gate(run, p)
        if os.environ.get("ARBITER_DECIDE") == "1":
            allf = decide(run, p, it, allf)
    finally:
        sandbox.clean(run.path, Path(p["repo"]))
        run.cov(wall_time_s=round(time.monotonic() - t0, 1))
    v = F.verdict(allf)
    if v == "pass" and (why := _withhold(run)):
        report.write(run.path, p, allf, "incomplete")
        raise ArbiterExit(5, f"arbiter: {why}; verdict withheld (report {run / 'report.md'})")
    report.write(run.path, p, allf, v)
    return run.path, v
