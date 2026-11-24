"""Stage 1: base, diff, units, triggers, agent schedule, tools and repo rules -> RUN/plan.json.

Also renders the numbered diffs that agent prompts show.
"""

import functools
import os
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, TypedDict

from . import cochange, decompose, diff, maintain, tools, triggers, units
from .diff import hunk_ranges
from .findings import rule_key
from .model import Decompose, DiffFile, Effort, Lang, MaintFact, Range, Ranges, Symbol, ToolSpec, Unit
from .rundir import RunDir

ALWAYS = {
    Effort.QUICK: ("A1a", "A1b", "A2", "A3", "A6a"),
    Effort.STANDARD: ("A1a", "A1b", "A1c", "A2", "A3", "A6a", "A6b", "A6c", "A6d"),
    Effort.DEEP: ("A1a", "A1b", "A1c", "A2", "A3", "A6a", "A6b", "A6c", "A6d"),
}
CORRECTNESS = frozenset({"A1a", "A1b", "A2", "A3"})  # all that runs on files with no arbiter language skill
K3 = frozenset({"A1a", "A1b", "A2", "A3", "A4"})  # agents run 3 times in deep mode
SKIP_ORDER = ("A9", "A7", "A8", "A5", "A5b", "A4")  # dropped first when over the agent budget
RULE_FILES = ("CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md")
RULE_DIR = re.compile(r"\.claude/rules/[^/]+\.md$")
HEADING = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
RULES_CAP = 20_000
THREAT_MODELS = ("THREAT_MODEL.md", "docs/THREAT_MODEL.md")
ORDERS = 3  # deterministic file orders, one per pass
UNIT_CONTEXT = 20
RUN_DIFF_CAP = 60_000
GAP = f"{'':>6} ⋯"  # marks lines a clipped unit diff leaves out


class Task(NamedTuple):
    unit: str
    agent: str
    pass_: int


class Skip(TypedDict, total=False):
    agent: str
    unit: str
    reason: str


class Schedule(TypedDict):
    tasks: list[Task]
    once: list[str]
    skipped: list[Skip]


class Plan(TypedDict):
    repo: str
    base: str
    head: str
    effort: Effort
    langs: list[str]
    files: list[DiffFile]
    commits: list[str]
    units: list[Unit]
    supply: bool
    schedule: Schedule
    tools: list[ToolSpec]
    threat_model: str | None
    notes: list[str]
    roots: list[str]
    orders: dict[str, dict[str, list[int]]]  # pass -> unit id -> file order
    decompose: Decompose
    budget: int  # unit churn budget (hier modes)
    manifest: list[Symbol]  # hier: the PR change manifest
    maint: list[MaintFact]  # measured maintainability facts (MA-03); empty in quick
    blocking_rules: list[str]  # `path#heading` keys of repo rule headings marked [block] (MA-05)
    cochange: dict[str, list[tuple[str, int]]]  # changed path -> files often changed with it (T-04)


def _order(u: Unit, k: int) -> list[int]:
    idx = list(range(len(u["files"])))
    if k:
        random.Random(k).shuffle(idx)
    return idx


def schedule(
    us: list[Unit], effort: Effort, supply: bool, max_agents: int, notes: list[str], *, contract: bool = False
) -> Schedule:
    """Agent calls within the budget: conditional agents are skipped in SKIP_ORDER, then deep k drops to 1."""
    once = ["A0", *([] if effort == Effort.QUICK else ["SPEC"]), *(["A5b"] if supply else [])]
    once += ["CONTRACT"] if contract else []
    per_unit = {
        u["id"]: [
            *(a for a in ALWAYS[effort] if u["lang"] != Lang.OTHER or a in CORRECTNESS),
            *(a for a in u.get("triggers", []) if a != "A5b"),
        ]
        for u in us
    }
    deep_k = effort == Effort.DEEP

    def k_of(agent: str) -> int:
        return 3 if deep_k and agent in K3 else 1

    def count() -> int:
        return len(once) + sum(k_of(a) for ags in per_unit.values() for a in ags)

    skipped: list[Skip] = []
    for agent in SKIP_ORDER:
        if count() <= max_agents:
            break
        if agent == "A5b" and agent in once:
            once.remove(agent)
            skipped.append(Skip(agent=agent, reason="agent budget"))
        for uid, ags in per_unit.items():
            if agent in ags:
                ags.remove(agent)
                skipped.append(Skip(agent=agent, unit=uid, reason="agent budget"))
    if count() > max_agents and deep_k:
        deep_k = False
        notes.append("agent budget: k reduced to 1")
    tasks = [Task(uid, a, k) for uid, ags in per_unit.items() for a in ags for k in range(k_of(a))]
    if len(once) + len(tasks) > max_agents:
        notes.append(f"agent budget {max_agents} still exceeded ({len(once) + len(tasks)} calls); running all")
    return Schedule(tasks=tasks, once=once, skipped=skipped)


def _rules(read: tools.Reader, tree: set[str], notes: list[str]) -> tuple[str, list[str]]:
    """Repo rule text for the prompts, and the `path#heading` keys of headings marked `[block]`."""
    paths = [*RULE_FILES, *sorted(p for p in tree if RULE_DIR.match(p))]
    bodies = [(path, body) for path in paths if (body := read(path))]
    blocking = [f"{path}#{rule_key(h)}" for path, body in bodies for h in HEADING.findall(body) if "[block]" in h]
    text = "\n\n".join(f"## {path}\n\n{body}" for path, body in bodies)
    if len(text) > RULES_CAP:
        notes.append(f"repo rules truncated at {RULES_CAP // 1000} KB")
        return f"{text[:RULES_CAP]}\n\n[truncated at {RULES_CAP // 1000} KB]", blocking
    return text, blocking


def _affected(repo: Path, paths: list[str]) -> list[str]:
    if not (repo / ".codegraph").is_dir() or not paths:
        return []
    p = subprocess.run(
        ["codegraph", "affected", "-q", "-p", str(repo), *paths], capture_output=True, text=True, timeout=120
    )
    if p.returncode:  # fall back to each language's whole test target, and say so
        print(f"arbiter: codegraph affected failed ({p.stderr.strip()[:200]}); running all tests", file=sys.stderr)
        return []
    return [ln.strip().removeprefix(f"{repo}/") for ln in p.stdout.splitlines() if ln.strip()]


def plan(
    run: RunDir,
    repo: Path,
    *,
    base_ref: str | None,
    effort: str,
    langs: list[str] | None,
    max_agents: int,
    decompose_mode: str = Decompose.OCR,
) -> Plan:
    repo, eff, mode = repo.resolve(), Effort(effort), Decompose(decompose_mode)
    base = diff.resolve_base(repo, base_ref)
    d = diff.collect(repo, base)
    tree = set(diff.git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
    included = [f for f in d["files"] if not f["excluded"]]
    notes = list(d["notes"])
    if langs:
        if skipped := [f["path"] for f in included if f["lang"] not in langs]:
            notes.append(f"--lang {','.join(langs)}: {len(skipped)} other-language files not reviewed")
        included = [f for f in included if f["lang"] in langs]
    notes += [
        f"no arbiter language skill for {ext}"
        for ext in sorted({Path(f["path"]).suffix or Path(f["path"]).name for f in included if f["lang"] == Lang.OTHER})
    ]

    @functools.cache
    def read(path: str) -> str | None:
        p = subprocess.run(
            ["git", "-C", str(repo), "show", f"HEAD:{path}"], capture_output=True, text=True, errors="replace"
        )
        return p.stdout if p.returncode == 0 else None

    budget = decompose.budget() if mode != Decompose.OCR else units.CHUNK
    code = decompose.Code(tree, read)
    syms = decompose.manifest(repo, base, included, code) if mode == Decompose.HIER else []
    us = units.build(included, tree, mode=mode, read=read, budget=budget, skip=decompose.rename_spans(syms))
    by_path = {f["path"]: f for f in d["files"]}
    for u in us:
        u["triggers"] = [] if eff == Effort.QUICK else triggers.for_unit(u, by_path, d["commits"])
        u["ranges"] = {p["path"]: decompose.piece_ranges(p, by_path[p["path"]]) for p in u["files"]}
    if mode == Decompose.HIER:
        decompose.assign(syms, us)
        decompose.add_callers(repo, syms)
        for u in us:
            u["context"] = decompose.context_map(repo, code, u, by_path, syms)
    supply = eff != Effort.QUICK and triggers.run_level(d["files"]) and (not langs or bool(included))
    contract = any(s["change"] in decompose.INTERFACE for s in syms)

    changed: dict[str, list[str]] = {}
    for f in included:
        changed.setdefault(f["lang"], []).append(f["path"])
    specs = tools.detect(tree, read, changed, _affected(repo, [f["path"] for f in included]))
    maint = [] if eff == Effort.QUICK else maintain.facts(repo, base, included, read)
    run.path.mkdir(parents=True, exist_ok=True)
    rules, blocking = _rules(read, tree, notes)
    (run / "rules.md").write_text(rules)
    p = Plan(
        repo=str(repo),
        base=base,
        head=d["head"],
        effort=eff,
        langs=langs or [],
        files=d["files"],
        commits=d["commits"],
        units=us,
        supply=supply,
        schedule=schedule(us, eff, supply, max_agents, notes, contract=contract),
        tools=specs,
        threat_model=next((t for t in THREAT_MODELS if t in tree), None),
        notes=notes,
        roots=sorted({s.get("root", "") for s in specs} or {""}),
        orders={str(k): {u["id"]: _order(u, k) for u in us} for k in range(ORDERS)},
        decompose=mode,
        budget=budget,
        manifest=syms,
        maint=maint,
        blocking_rules=blocking,
        cochange=cochange.neighbours(repo, [f["path"] for f in included], tree)
        if eff != Effort.QUICK and os.environ.get("ARBITER_COCHANGE") == "1"
        else {},
    )
    run.save("plan.json", p)
    run.cov(
        units=[
            {
                "id": u["id"],
                "lang": u["lang"],
                "files": [x["path"] for x in u["files"]],
                "churn": u["churn"],
                "plan_required": u["plan_required"],
                "triggers": u["triggers"],
            }
            for u in us
        ],
        decompose={
            "mode": mode,
            "budget": budget,
            "interface_changes": sum(s["change"] in decompose.INTERFACE for s in syms),
        },
        notes=notes,
        maint_facts=len(maint),
        excluded=[{"path": f["path"], "reason": f["excluded"]} for f in d["files"] if f["excluded"]],
    )
    return p


# ---------------------------------------------------------------- diffs shown to agents


def numbered_diff(
    repo: str, base: str, head: str, path: str, *, keep: list[Range] | None, ctx: int = UNIT_CONTEXT, clip: bool = False
) -> str:
    """`git diff -U<ctx>` for one file with new-side line numbers; only hunks overlapping `keep` ranges.

    `clip` also drops lines more than `ctx` away from every `keep` range, for a piece covering part of a hunk.
    """
    text = diff.git(repo, "diff", f"-U{ctx}", "-M", f"{base}..{head}", "--", path, check=False)
    out: list[str] = []
    block: list[str] = []
    keep_block, new = False, 0

    def near(n: int) -> bool:
        return not clip or keep is None or any(lo - ctx <= n <= hi + ctx for lo, hi in keep)

    for ln in text.splitlines():
        if m := diff.HUNK_RE.match(ln):
            if block and keep_block:
                out.extend(_gaps(block) if clip else block)
            new = int(m[3])
            hi = new + max(int(m[4]) if m[4] is not None else 1, 1) - 1
            keep_block = keep is None or any(lo <= hi and new <= h for lo, h in keep)
            block = [ln]
        elif block:
            if ln.startswith("-"):
                block.append(f"{'':>6} {ln}" if near(new) else "")
            elif ln.startswith(("+", " ")):
                block.append(f"{new:>6} {ln}" if near(new) else "")
                new += 1
    if block and keep_block:
        out.extend(_gaps(block) if clip else block)
    return f"### {path}\n```diff\n" + "\n".join(out) + "\n```" if out else ""


def _gaps(block: list[str]) -> list[str]:
    """Clipped lines ("") collapse to one marker per gap."""
    out: list[str] = []
    for ln in block:
        if ln or (out and out[-1] != GAP):
            out.append(ln or GAP)
    return out


def unit_diff(p: Plan, u: Unit, order: list[int] | None = None) -> str:
    pieces = [u["files"][i] for i in (order or range(len(u["files"])))]
    ranges = u.get("ranges", {})
    return "\n\n".join(
        numbered_diff(p["repo"], p["base"], p["head"], x["path"], keep=ranges.get(x["path"], []), clip="lines" in x)
        for x in pieces
    )


def run_diff(p: Plan, paths: list[str], limit: int = RUN_DIFF_CAP, ctx: int = 3) -> str:
    out = "\n\n".join(numbered_diff(p["repo"], p["base"], p["head"], x, keep=None, ctx=ctx) for x in paths)
    return out if len(out) <= limit else f"{out[:limit]}\n[diff truncated]"


def pr_ranges(p: Plan) -> Ranges:
    """Every changed hunk of the PR (included files): the widened acceptance rule of hier mode (§4.3)."""
    return {f["path"]: hunk_ranges(f["hunks"]) for f in p["files"] if not f["excluded"]}


def ranges_by_unit(p: Plan) -> dict[str, Ranges]:
    """Each unit's hunks, plus the run-level pseudo units: 'run' (every unit) and 'supply' (manifests, lockfiles),
    and in hier mode 'contract' (the whole PR)."""
    r = {u["id"]: u.get("ranges", {}) for u in p["units"]}
    run_ranges: Ranges = {}
    for u in p["units"]:
        for path, rs in u.get("ranges", {}).items():
            run_ranges.setdefault(path, []).extend(rs)
    r["run"] = run_ranges
    r["supply"] = {f["path"]: hunk_ranges(f["hunks"]) for f in p["files"] if triggers.supply_chain(f["path"])}
    if p.get("decompose") == Decompose.HIER:
        r["contract"] = pr_ranges(p)
    return r
