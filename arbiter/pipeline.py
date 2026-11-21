"""The deterministic review pipeline. Every stage reads/writes JSON in RUN so stages can be rerun alone."""

import json
import random
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import ArbiterExit, agents, diff, findings as F, harness, lang as langmod, sandbox, tools, triggers, units

ALWAYS = {"quick": ["A1a", "A1b", "A2", "A3", "A6a"],
          "standard": ["A1a", "A1b", "A1c", "A2", "A3", "A6a", "A6b", "A6c"]}
ALWAYS["deep"] = ALWAYS["standard"]
CORRECTNESS = {"A1a", "A1b", "A2", "A3"}  # all that runs on files with no arbiter language skill
K3 = {"A1a", "A1b", "A2", "A3", "A4"}
SKIP_ORDER = ("A9", "A7", "A8", "A5", "A5b", "A4")
MAX_FAILED_SHARE = 0.25
LENSES = {"functional": ["REACHABILITY", "CLAIM", "ATTRIBUTION"], "security": ["REACHABILITY", "IMPACT", "DEFENSES"]}
RULE_FILES = ("CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md")
THREAT_MODELS = ("THREAT_MODEL.md", "docs/THREAT_MODEL.md")


def load(run: Path, name: str, default=None):
    p = run / name
    return json.loads(p.read_text()) if p.exists() else default


def save(run: Path, name: str, data):
    (run / name).write_text(json.dumps(data, indent=2, default=sorted))


def cov(run: Path, **kv):
    """Merge keys into RUN/coverage.json (lists extend, dicts update)."""
    c = load(run, "coverage.json", {})
    for k, v in kv.items():
        if isinstance(v, list):
            c.setdefault(k, []).extend(v)
        elif isinstance(v, dict):
            c.setdefault(k, {}).update(v)
        else:
            c[k] = v
    save(run, "coverage.json", c)


def log(msg: str):
    print(f"arbiter: {msg}", flush=True)


def default_run(repo: Path) -> Path:
    head = diff.git(repo, "rev-parse", "--short=7", "HEAD").strip()
    return Path(f"/tmp/arbiter-{repo.resolve().name}-{head}-{time.strftime('%Y%m%d%H%M%S', time.gmtime())}")


# ---------------------------------------------------------------- plan

def _ranges(hunks: list[dict]) -> list[tuple[int, int]]:
    return [(h["new_start"], h["new_start"] + max(h["new_count"], 1) - 1) for h in hunks]


def plan(run: Path, repo: Path, base_ref: str | None, effort: str, langs: list[str] | None, max_agents: int) -> dict:
    repo = repo.resolve()
    base = diff.resolve_base(repo, base_ref)
    d = diff.collect(repo, base)
    tree = set(diff.git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
    included = [f for f in d["files"] if not f["excluded"]]
    notes = list(d["notes"])
    if langs:
        skipped = [f["path"] for f in included if f["lang"] not in langs]
        if skipped:
            notes.append(f"--lang {','.join(langs)}: {len(skipped)} other-language files not reviewed")
        included = [f for f in included if f["lang"] in langs]
    for ext in sorted({Path(f["path"]).suffix or Path(f["path"]).name for f in included if f["lang"] == "other"}):
        notes.append(f"no arbiter language skill for {ext}")
    us = units.build(included, tree)
    by_path = {f["path"]: f for f in d["files"]}
    for u in us:
        u["triggers"] = [] if effort == "quick" else triggers.for_unit(u, by_path, d["commits"])
        u["ranges"] = {p["path"]: _ranges([by_path[p["path"]]["hunks"][i] for i in p["hunks"]]) for p in u["files"]}
    supply = effort != "quick" and triggers.run_level(d["files"]) and (not langs or included)
    schedule = _schedule(us, effort, supply, max_agents, notes)

    def read(path: str):
        p = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{path}"], capture_output=True, text=True, errors="replace")
        return p.stdout if p.returncode == 0 else None

    changed: dict[str, list[str]] = {}
    for f in included:
        changed.setdefault(f["lang"], []).append(f["path"])
    affected = []
    if (repo / ".codegraph").is_dir() and included:
        p = subprocess.run(["codegraph", "affected", "-q", "-p", str(repo), *[f["path"] for f in included]],
                           capture_output=True, text=True, timeout=120)
        affected = [ln.strip().removeprefix(str(repo) + "/") for ln in p.stdout.splitlines() if ln.strip()]
    specs = tools.detect(tree, read, changed, affected)
    rules, size = [], 0
    for path in [*RULE_FILES, *sorted(p for p in tree if re.match(r"\.claude/rules/[^/]+\.md$", p))]:
        if (text := read(path)):
            rules.append(f"## {path}\n\n{text}")
    rules_text = "\n\n".join(rules)
    if len(rules_text) > 20_000:
        rules_text = rules_text[:20_000] + "\n\n[truncated at 20 KB]"
        notes.append("repo rules truncated at 20 KB")
    run.mkdir(parents=True, exist_ok=True)
    (run / "rules.md").write_text(rules_text)
    threat = next((t for t in THREAT_MODELS if t in tree), None)
    p = {"repo": str(repo), "base": base, "head": d["head"], "effort": effort, "langs": langs or [],
         "files": d["files"], "commits": d["commits"], "units": us, "supply": bool(supply), "schedule": schedule,
         "tools": specs, "threat_model": threat, "notes": notes,
         "roots": sorted({s["root"] for s in specs} | ({""} if not specs else set())),
         "orders": {str(k): {u["id"]: _order(u, k) for u in us} for k in range(3)}}
    save(run, "plan.json", p)
    cov(run, units=[{"id": u["id"], "lang": u["lang"], "files": [x["path"] for x in u["files"]], "churn": u["churn"],
                     "plan_required": u["plan_required"], "triggers": u["triggers"]} for u in us],
        notes=notes, excluded=[{"path": f["path"], "reason": f["excluded"]} for f in d["files"] if f["excluded"]])
    return p


def _order(u: dict, k: int) -> list[int]:
    idx = list(range(len(u["files"])))
    if k:
        random.Random(k).shuffle(idx)
    return idx


def _schedule(us: list[dict], effort: str, supply: bool, max_agents: int, notes: list[str]) -> dict:
    """-> {"tasks": [[unit, agent, pass]], "once": [...], "skipped": [...]} within the agent budget."""
    once = ["A0"] + ([] if effort == "quick" else ["SPEC"]) + (["A5b"] if supply else [])
    per_unit = {}
    for u in us:
        base = [a for a in ALWAYS[effort] if u["lang"] != "other" or a in CORRECTNESS]
        per_unit[u["id"]] = base + [a for a in u["triggers"] if a != "A5b"]
    k_of = (lambda a: 3 if effort == "deep" and a in K3 else 1)
    skipped = []

    def count():
        return len(once) + sum(k_of(a) for ags in per_unit.values() for a in ags)

    for agent in SKIP_ORDER:
        if count() <= max_agents:
            break
        if agent == "A5b" and "A5b" in once:
            once.remove("A5b")
            skipped.append({"agent": "A5b", "reason": "agent budget"})
        for uid, ags in per_unit.items():
            if agent in ags:
                ags.remove(agent)
                skipped.append({"agent": agent, "unit": uid, "reason": "agent budget"})
    if count() > max_agents and effort == "deep":
        k_of = (lambda a: 1)
        notes.append("agent budget: k reduced to 1")
    tasks = [[uid, a, p] for uid, ags in per_unit.items() for a in ags for p in range(k_of(a))]
    if len(once) + len(tasks) > max_agents:
        notes.append(f"agent budget {max_agents} still exceeded ({len(once) + len(tasks)} calls); running all")
    return {"tasks": tasks, "once": once, "skipped": skipped}


# ---------------------------------------------------------------- diffs for prompts

def _numbered_diff(repo: str, base: str, head: str, path: str, keep: list[tuple[int, int]] | None, ctx: int = 20) -> str:
    """git diff -U<ctx> for one file with new-side line numbers; keep only hunks overlapping `keep` ranges."""
    text = diff.git(repo, "diff", f"-U{ctx}", "-M", f"{base}..{head}", "--", path, check=False)
    out, block, keep_block, new = [], [], False, 0
    for ln in text.splitlines():
        if m := diff.HUNK_RE.match(ln):
            if block and keep_block:
                out.extend(block)
            new = int(m[3])
            cnt = int(m[4]) if m[4] is not None else 1
            hi = new + max(cnt, 1) - 1
            keep_block = keep is None or any(lo <= hi and new <= h for lo, h in keep)
            block = [ln]
        elif block:
            if ln.startswith("-"):
                block.append(f"{'':>6} {ln}")
            elif ln.startswith(("+", " ")):
                block.append(f"{new:>6} {ln}")
                new += 1
    if block and keep_block:
        out.extend(block)
    return f"### {path}\n```diff\n" + "\n".join(out) + "\n```" if out else ""


def unit_diff(p: dict, u: dict, order: list[int] | None = None) -> str:
    pieces = [u["files"][i] for i in (order or range(len(u["files"])))]
    return "\n\n".join(_numbered_diff(p["repo"], p["base"], p["head"], x["path"], u["ranges"][x["path"]]) for x in pieces)


def _pseudo_units(p: dict) -> dict[str, dict]:
    """Run-level agents: 'run' covers every unit's hunks; 'supply' covers manifests and lockfiles."""
    run_ranges: dict[str, list] = {}
    for u in p["units"]:
        for k, v in u["ranges"].items():
            run_ranges.setdefault(k, []).extend(v)
    supply = {f["path"]: _ranges(f["hunks"]) for f in p["files"] if triggers.supply_chain(f["path"])}
    return {"run": {"id": "run", "ranges": run_ranges}, "supply": {"id": "supply", "ranges": supply}}


def _run_diff(p: dict, paths, limit: int = 60_000, ctx: int = 3) -> str:
    out = "\n\n".join(_numbered_diff(p["repo"], p["base"], p["head"], x, None, ctx) for x in paths)
    return out if len(out) <= limit else out[:limit] + "\n[diff truncated]"


def ranges_by_unit(p: dict) -> dict[str, dict]:
    r = {u["id"]: u["ranges"] for u in p["units"]}
    r.update({k: v["ranges"] for k, v in _pseudo_units(p).items()})
    return r


# ---------------------------------------------------------------- sandbox + gates

def prepare(run: Path, p: dict) -> dict:
    versions = tools.prefetch(lambda m: cov(run, notes=[m]))
    st = sandbox.prepare(run, Path(p["repo"]), p["base"], p["head"], p["roots"], lambda m: cov(run, notes=[m]))
    if st["status"] == "prepared":
        ok, rows = sandbox.selftest(run)
        if not ok:
            cov(run, notes=["sandbox selftest failed: execution proofs disabled"])
    st = load(run, "sandbox.json", st)
    specs = [tools.resolve(s) for s in p["tools"]]
    p["tools"] = specs
    save(run, "plan.json", p)
    cov(run, sandbox=st["status"], sandbox_notes=st.get("notes", []),
        tools=[{"name": s["name"], "lang": s["lang"], "available": s["available"], "source": s["source"]} for s in specs],
        tool_versions=versions)
    return st


STATIC_OK = {"ruff", "eslint", "bandit", "gosec"}  # may run without the sandbox (no repo code executed)


def _exec_tool(run: Path, s: dict, base: bool = False) -> dict | None:
    wt = run / ("wt-base" if base else "wt")
    if not wt.exists():
        return None
    if s.get("net") or (not sandbox.available(run) and (s["name"] in STATIC_OK or s["name"].startswith("semgrep"))):
        t0 = time.monotonic()
        try:
            r = subprocess.run(s["cmd"], cwd=wt / s["root"], capture_output=True, text=True, errors="replace",
                               timeout=600, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired) as e:
            return {"exit_code": -1, "stdout_tail": "", "stderr_tail": str(e), "timed_out": True, "cmd": " ".join(s["cmd"]),
                    "exec_id": "", "stdout": ""}
        return {"exit_code": r.returncode, "stdout": r.stdout, "stdout_tail": r.stdout[-20000:], "stderr_tail": r.stderr[-20000:],
                "timed_out": False, "cmd": " ".join(s["cmd"]), "exec_id": "", "duration_s": round(time.monotonic() - t0, 2)}
    if not sandbox.available(run):
        return None
    timeout = 900 if s["kind"] in ("test", "analyzer") else 600
    return sandbox.exec_(run, s["cmd"], base=base, timeout=timeout, sub=s["root"])


def gates(run: Path, p: dict) -> dict:
    added = {f["path"]: {n for h in f["hunks"] for n, _ in h["added"]} for f in p["files"] if not f["excluded"]}
    first_line = next(((f, min(ls)) for f, ls in added.items() if ls), (None, 1))
    out = {"findings": [], "preexisting": [], "results": [], "analyzer_hits": []}
    # roots whose HEAD or base dependency fetch failed: a HEAD/base gate difference there may be environmental
    fetch_failed = {f["root"] for f in load(run, "sandbox.json", {}).get("fetch", []) if f["exit_code"]}
    (run / "tools").mkdir(exist_ok=True)

    def finding(s, r, path, line, claim, axis, sev, rung, rule, after=None):
        excerpt = "\n".join((r["stdout_tail"] + "\n" + r["stderr_tail"]).strip().splitlines()[-15:])
        out["findings"].append({
            "id": f"g{len(out['findings']) + 1:02d}", "source": "gate", "agents": [s["name"]], "axis": axis,
            "group": "functional" if axis in F.FUNCTIONAL else "evolvability", "severity": sev, "file": path,
            "line": line, "end_line": line, "claim": claim, "rule": rule, "status": "verified", "placement": "main",
            "proof": {"rung": rung, "result": "confirmed",
                      "before": {"exec_id": r["exec_id"], "cmd": r["cmd"], "exit_code": r["exit_code"],
                                 "output_excerpt": excerpt[-1500:]},
                      **({"after": after} if after else {})}})

    for s in p["tools"]:
        if not s.get("available"):
            out["results"].append({"name": s["name"], "status": "missing"})
            continue
        r = _exec_tool(run, s)
        if r is None:
            out["results"].append({"name": s["name"], "status": "skipped (sandbox unavailable)"})
            continue
        stdout = r.get("stdout", r["stdout_tail"])
        safe = re.sub(r"\W+", "_", s["name"])
        (run / "tools" / f"{safe}.out").write_text(stdout + "\n--- stderr ---\n" + r["stderr_tail"])
        out["results"].append({"name": s["name"], "status": "ran", "exit_code": r["exit_code"], "cmd": r["cmd"],
                               "timed_out": r["timed_out"], "exec_id": r["exec_id"]})
        wt = str((run / "wt").resolve())
        if s["kind"] == "analyzer":
            out["analyzer_hits"].extend({**h, "tool": s["name"]} for h in tools.analyzer_hits(s, stdout, wt))
            continue
        if r["timed_out"]:
            cov(run, notes=[f"gate {s['name']} timed out"])
            continue
        if s["kind"] == "test" and r["exit_code"] in (5,) and s["name"] == "pytest":
            continue  # no tests collected
        diags = tools.diagnostics(s, r["stdout_tail"], r["stderr_tail"], wt)
        hits = [dg for dg in diags if dg["line"] in added.get(dg["path"], set())]
        for dg in hits if s["kind"] != "test" else []:
            is_err = s["kind"] == "build" or (s["kind"] == "type" and re.search(r"\berror\b", dg["msg"], re.I))
            sev = "block" if is_err else ("nit" if s["name"] == "rustfmt" else "should-fix")
            finding(s, r, dg["path"], dg["line"], f"{s['name']}: {dg['msg']}", "logic" if is_err else "idiom",
                    sev, "E1", dg["rule"] or s["name"])
        if r["exit_code"] and s["kind"] in ("build", "type", "test") and not hits and s["root"] in fetch_failed:
            cov(run, notes=[f"gate {s['name']} fails, but dependency fetch failed in {s['root'] or '.'}: "
                            "HEAD-vs-base comparison skipped"])
        elif r["exit_code"] and s["kind"] in ("build", "type", "test") and not hits:
            rb = _exec_tool(run, s, base=True)
            if rb and rb["exit_code"] == 0:
                loc = next(((dg["path"], dg["line"]) for dg in diags if dg["path"] in added), first_line)
                after = {"exec_id": rb["exec_id"], "cmd": rb["cmd"] + " (on base)", "exit_code": 0}
                finding(s, r, loc[0], loc[1], f"`{r['cmd']}` fails on HEAD (exit {r['exit_code']}) and passes on base",
                        "logic", "block", "E4" if s["kind"] == "test" else "E1", s["name"], after)
            elif rb:
                out["preexisting"].append({"name": s["name"], "cmd": r["cmd"], "exit_code": r["exit_code"],
                                           "base_exit_code": rb["exit_code"]})
    save(run, "gates.json", out)
    return out


# ---------------------------------------------------------------- agents

def _cwd(run: Path, p: dict) -> Path:
    return run / "wt" if (run / "wt").exists() else Path(p["repo"])


def _facts(p: dict, u: dict | None = None) -> str:
    lines = [f"repo: {Path(p['repo']).name}", f"base: {p['base'][:12]}", f"head: {p['head'][:12]}",
             f"effort: {p['effort']}", "Paths are relative to the repository root (your working directory)."]
    if u and u.get("plan_required"):
        lines.append("This unit is large: first list the behaviours it changes, then check each.")
    return "\n".join(lines)


def intent(run: Path, p: dict, jobs: int) -> dict:
    issues = []
    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0:
        for n in sorted({int(x) for c in p["commits"] for x in re.findall(r"(?<![\w/])#(\d{1,6})\b", c)})[:5]:
            r = subprocess.run(["gh", "issue", "view", str(n), "--json", "title,body"], cwd=p["repo"],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                issues.append(f"#{n}: {r.stdout[:4000]}")
    specs = [f["path"] for f in p["files"] if re.match(r"(specs|docs)/", f["path"])]
    tm = p["threat_model"]
    inputs = {
        "EFFORT": p["effort"], "Run facts": _facts(p),
        "Commit messages": "\n\n".join(p["commits"]) or "(none)",
        "Changed files": "\n".join(f"{f['path']} (+{f['added']} -{f['deleted']})" for f in p["files"]),
        "Spec or docs files changed": "\n".join(specs) or "(none)",
        "Linked issues": "\n\n".join(issues) or "(none fetched)",
        "Units": "\n".join(f"{u['id']}: {', '.join(x['path'] for x in u['files'])} "
                           f"(churn {u['churn']}{', plan_required' if u['plan_required'] else ''})" for u in p["units"]),
        "Threat model": f"exists at {tm}; do not draft one" if tm else
        "none exists; add threat_model_draft using the template headings: Assets, Entry points, Trust boundaries, "
        "Trusted inputs, In-scope classes, Out-of-scope classes, DoS policy",
    }
    prompt, _ = agents.build_prompt("A0", [], inputs)
    val, err = agents.run("A0", "A0", prompt, F.validate_intent, tools="finder", cwd=_cwd(run, p))
    val = val or {"claims": [], "spec_source": "none", "threat_model_path": tm or "none", "unit_notes": {}}
    tm_text, tm_path, drafted = "", tm, False
    if tm and (_cwd(run, p) / tm).exists():
        tm_text = (_cwd(run, p) / tm).read_text(errors="replace")[:15_000]
    elif val.get("threat_model_draft"):
        (run / "THREAT_MODEL.draft.md").write_text(val["threat_model_draft"])
        tm_text, tm_path, drafted = val["threat_model_draft"], str(run / "THREAT_MODEL.draft.md"), True
    val["threat_model_text"], val["threat_model_path"], val["threat_model_drafted"] = tm_text, tm_path, drafted
    save(run, "intent.json", val)
    cov(run, agents_run=["A0"], agent_failures=[err] if err else [],
        threat_model={"path": tm_path, "drafted": drafted})
    return val


def finders(run: Path, p: dict, it: dict, jobs: int) -> list[dict]:
    rules = (run / "rules.md").read_text() if (run / "rules.md").exists() else ""
    units_by = {u["id"]: u for u in p["units"]}
    jobs_list = []
    for uid, agent, k in p["schedule"]["tasks"]:
        u = units_by[uid]
        inputs = {"EFFORT": p["effort"], "UNIT": uid, "Run facts": _facts(p, u),
                  "Risk notes from intent": it.get("unit_notes", {}).get(uid, ""),
                  "Files": "\n".join(x["path"] for x in u["files"]),
                  "Unit diff (new-side line numbers on the left; review + lines only)":
                      unit_diff(p, u, p["orders"][str(k)][uid]),
                  "Repo rules": rules,
                  "Threat model": it.get("threat_model_text", "") if agent == "A3" else ""}
        jobs_list.append((uid, agent, k, u["langs"], inputs))
    once = p["schedule"]["once"]
    included = [f["path"] for f in p["files"] if not f["excluded"]]
    all_langs = sorted({u["lang"] for u in p["units"]})
    if "SPEC" in once:
        jobs_list.append(("run", "SPEC", 0, all_langs, {
            "EFFORT": p["effort"], "Run facts": _facts(p),
            "Claims to check (from commits, issues, specs; untrusted)": json.dumps(it.get("claims", []), indent=1),
            "Spec source": str(it.get("spec_source", "none")),
            "Diff (new-side line numbers)": _run_diff(p, included)}))
    if "A5b" in once:
        sup = [f["path"] for f in p["files"] if triggers.supply_chain(f["path"])]
        jobs_list.append(("supply", "A5b", 0, all_langs, {
            "EFFORT": p["effort"], "Run facts": _facts(p), "Files": "\n".join(sup),
            "Supply-chain diff (new-side line numbers)": _run_diff(p, sup, ctx=3)}))

    def one(job):
        uid, agent, k, langs, inputs = job
        prompt, _ = agents.build_prompt(agent, langs, inputs)
        (run / "prompts").mkdir(exist_ok=True)
        (run / "prompts" / f"{uid}-{agent}-{k}.md").write_text(prompt)
        val, err = agents.run(agent, agent, prompt, F.validate_findings, tools="finder", cwd=_cwd(run, p))
        return [{**c, "agent": agent, "pass": k, "unit": uid} for c in (val or {}).get("findings", [])
                if isinstance(c, dict)], err, f"{agent}@{uid}#{k}"

    raw, fails, ran = [], [], []
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for cands, err, name in ex.map(one, jobs_list):
            raw.extend(cands)
            ran.append(name)
            if err:
                fails.append(err)
    save(run, "raw.json", raw)
    cov(run, agents_run=ran, agent_failures=fails, agents_skipped=p["schedule"]["skipped"])
    return raw


def merge(run: Path, p: dict) -> list[dict]:
    raw = load(run, "raw.json", [])
    k3 = K3 if p["effort"] == "deep" else set()
    merged, rejected = F.merge(raw, ranges_by_unit(p), k3)
    save(run, "candidates.json", merged)
    save(run, "rejected.json", rejected)
    return merged


def _finding_brief(f: dict) -> str:
    keep = ("id", "axis", "severity", "file", "line", "end_line", "claim", "trigger", "evidence_lines", "cwe", "rule",
            "precedent", "code_judo", "fix", "proof_plan")
    return json.dumps({k: f[k] for k in keep if k in f}, indent=1)


def _diff_for(p: dict, f: dict) -> str:
    u = next((u for u in p["units"] if u["id"] == f["unit"]), None)
    if u:
        return unit_diff(p, u)
    return _run_diff(p, [f["file"]])


def verify(run: Path, p: dict, it: dict, jobs: int) -> list[dict]:
    cands = load(run, "candidates.json", [])
    rules = (run / "rules.md").read_text() if (run / "rules.md").exists() else ""
    jobs_list = []
    for f in cands:
        sec = f["axis"] in ("security", "privacy")
        lenses = (["REACHABILITY" if sec else "CLAIM"] if p["effort"] == "quick"
                  else LENSES["security" if sec else "functional"])
        for lens in lenses:
            jobs_list.append((f, lens))

    def one(job):
        f, lens = job
        langs = [langmod.of(f["file"])]
        inputs = {"LENS": lens, "Run facts": _facts(p), "Finding to judge (untrusted claim)": _finding_brief(f),
                  "Diff (new-side line numbers; base side shown as - lines)": _diff_for(p, f), "Repo rules": rules,
                  "Threat model": it.get("threat_model_text", "") if f["axis"] in ("security", "privacy") else ""}
        prompt, _ = agents.build_prompt("V", langs, inputs)
        val, err = agents.run("V", "V", prompt, F.validate_vote, tools="finder", cwd=_cwd(run, p))
        return f["id"], lens, val, err

    votes: dict[str, list] = {f["id"]: [] for f in cands}
    fails = []
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for fid, lens, val, err in ex.map(one, jobs_list):
            votes[fid].append({**val, "lens": lens, "finding_id": fid} if val else None)
            if err:
                fails.append(err)
    save(run, "votes.json", votes)
    for f in cands:
        F.tally(f, votes[f["id"]], p["effort"])
    save(run, "tallied.json", cands)
    cov(run, verifier_calls=len(jobs_list), agent_failures=fails)
    return cands


def proofs(run: Path, p: dict, jobs: int) -> list[dict]:
    """Serial: proof agents edit RUN/wt, so two at once would corrupt each other's fail/pass runs."""
    cands = load(run, "tallied.json", [])
    allowed_effort = F.EFFORT_RUNGS[p["effort"]]
    attempted = confirmed = 0
    fails = []
    wt = run / "wt"
    for f in cands:
        if f.get("status") != "verified":
            continue
        if f["group"] == "functional":
            allowed = F.ACCEPTED[f["axis"]] & allowed_effort
        elif p["effort"] == "deep" and f.get("code_judo"):
            allowed = {"E1"}
        else:
            continue
        if not allowed:
            f["proof_note"] = f"no accepted rung for {f['axis']} at {p['effort']} effort"
            continue
        if not sandbox.available(run):
            f["proof_note"] = "sandbox unavailable: execution proofs disabled"
            continue
        f["proof_attempts"] = []
        for attempt in range(3):
            attempted += 1
            inputs = {"RUN": str(run), "ALLOWED_RUNGS": " ".join(sorted(allowed)), "FINDING_ID": f["id"],
                      "EFFORT": p["effort"], "Run facts": _facts(p) + f"\nattempt {attempt + 1} of 3 (independent)",
                      "Finding to prove": _finding_brief(f), "Diff": _diff_for(p, f)}
            prompt, _ = agents.build_prompt("P", [langmod.of(f["file"])], inputs)
            val, err = agents.run("P", "P", prompt, F.validate_proof, tools="proof", cwd=wt, timeout=900)
            subprocess.run(["git", "-C", str(wt), "checkout", "--", "."], capture_output=True)  # revert any minimal fix
            if err:
                fails.append(err)
                f["proof_attempts"].append({"error": err})
                continue
            if val["result"] == "confirmed":
                if val["rung"] not in allowed:
                    val["result"], val["check"] = "error", f"rung {val['rung']} not in {sorted(allowed)}"
                elif (bad := F.check_proof(val, lambda x: sandbox.exec_record(run, x))):
                    val["result"], val["check"] = "error", bad
            f["proof_attempts"].append(val)
            if val["result"] == "confirmed":
                f["proof"] = val
                confirmed += 1
                break
    save(run, "proved.json", cands)
    cov(run, proofs={"attempted": attempted, "confirmed": confirmed}, agent_failures=fails)
    return cands


def final_gate(run: Path, p: dict) -> list[dict]:
    cands = load(run, "proved.json") or load(run, "tallied.json", [])
    g = load(run, "gates.json", {"findings": [], "analyzer_hits": []})
    wt = run / "wt" if (run / "wt").exists() else None
    for f in cands:
        f.setdefault("source", "agent")
        F.gate(f, p["effort"], wt)
        sup = [h for h in g.get("analyzer_hits", []) if h["path"] == f["file"] and abs(h["line"] - f["line"]) <= 3]
        if sup:
            f["support"] = [{"rung": "E2", **h} for h in sup]
    # an agent finding in main absorbs an overlapping gate lint hit (one finding per issue)
    main = [f for f in cands if f.get("placement") == "main"]
    gate_f = []
    for gf in g.get("findings", []):
        hit = next((f for f in main if f["file"] == gf["file"] and abs(f["line"] - gf["line"]) <= 3), None)
        if hit and gf["severity"] != "block":
            hit.setdefault("support", []).append({"rung": "E1", "tool": gf["agents"][0], "msg": gf["claim"]})
        else:
            gate_f.append(gf)
    allf = gate_f + cands
    nits = sorted((f for f in allf if f.get("placement") == "main" and f["severity"] == "nit"),
                  key=lambda f: (f["axis"] in F.EVOLVABILITY, -len(f.get("agents", []))))
    for f in nits[F.NIT_CAP:]:
        f["placement"] = "nit-overflow"
    save(run, "final.json", allf)
    return allf


# ---------------------------------------------------------------- entry

def run_all(repo: Path, base: str | None, effort: str, langs: list[str] | None, run: Path | None, jobs: int,
            max_agents: int) -> tuple[Path, str]:
    t0 = time.monotonic()
    run = run or default_run(repo)
    run.mkdir(parents=True, exist_ok=True)
    print(run, flush=True)
    s = harness.settings()
    p = plan(run, repo, base, effort, langs, max_agents)
    cov(run, harness=s["harness"], models={"finder": s["model"] or "(harness default)",
                                           "verify": s["verify_model"] or "(harness default)"}, effort=effort)
    try:
        prepare(run, p)
        gates(run, p)
        it = intent(run, p, jobs)
        finders(run, p, it, jobs)
        merge(run, p)
        verify(run, p, it, jobs)
        proofs(run, p, jobs)
        allf = final_gate(run, p)
    finally:
        sandbox.clean(run, Path(p["repo"]))
        cov(run, wall_time_s=round(time.monotonic() - t0, 1))
    from . import report
    v = F.verdict(allf)
    c = load(run, "coverage.json", {})
    failed, ran = len(c.get("agent_failures", [])), len(c.get("agents_run", [])) + c.get("verifier_calls", 0)
    if v == "pass" and ran and failed > MAX_FAILED_SHARE * ran:
        # a gate must not pass on silence: too many agents produced nothing
        report.write(run, p, allf, "incomplete")
        raise ArbiterExit(5, f"arbiter: {failed} of {ran} agent calls failed; verdict withheld "
                             f"(report {run / 'report.md'})")
    report.write(run, p, allf, v)
    return run, v
