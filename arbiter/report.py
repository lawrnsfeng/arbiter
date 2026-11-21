"""RUN/report.json (machine) and RUN/report.md (human)."""

import json
from pathlib import Path

from . import findings as F


def _line(f: dict) -> str:
    proof = f.get("proof") or {}
    tag = proof.get("rung") if proof.get("result") == "confirmed" else (f.get("rule") or (f.get("proof_plan") or {}).get("rung", "E0"))
    s = f"- [{f['severity']}][{f['axis']}][{tag}] `{f['file']}:{f['line']}` {f['claim']}"
    if f.get("fix"):
        s += f" · Fix: {f['fix']}"
    if proof.get("result") == "confirmed":
        b = proof["before"]
        s += f" · Proof: `{b.get('cmd', '')}` → exit {b.get('exit_code')}"
        if proof.get("after"):
            a = proof["after"]
            s += f"; after fix `{a.get('cmd', '')}` → exit {a.get('exit_code')}"
        if proof.get("artifact"):
            s += f" ({proof['artifact']})"
    src = [x for x in (f.get("rule"), f"CWE-{f['cwe']}" if f.get("cwe") else None, f.get("precedent")) if x]
    src += [f"{x.get('rung')} {x.get('tool')}: {x.get('rule') or x.get('msg', '')[:80]}" for x in f.get("support", [])]
    if src:
        s += f" · Source: {'; '.join(src)}"
    if f.get("status_reason") or f.get("placement_reason"):
        s += f" · ({f.get('status_reason') or f.get('placement_reason')})"
    b = proof.get("before") or {}
    if proof.get("result") == "confirmed" and b.get("output_excerpt"):
        excerpt = b["output_excerpt"].strip().splitlines()[-3:]
        s += "\n  ```\n" + "\n".join("  " + x for x in excerpt) + "\n  ```"
    return s


def write(run: Path, p: dict, allf: list[dict], verdict: str):
    cov = json.loads((run / "coverage.json").read_text()) if (run / "coverage.json").exists() else {}
    gates = json.loads((run / "gates.json").read_text()) if (run / "gates.json").exists() else {}
    intent = json.loads((run / "intent.json").read_text()) if (run / "intent.json").exists() else {}
    main = [f for f in allf if f.get("placement") == "main"]
    spec = [f for f in main if f["axis"] == "spec"]
    func = [f for f in main if f["group"] == "functional" and f["axis"] != "spec"]
    evo = [f for f in main if f["group"] == "evolvability"]
    sections = {
        "Block (proven)": [f for f in func if f["severity"] == "block"],
        "Should-fix (proven)": [f for f in func if f["severity"] != "block"],
        "Evolvability (idiom · design · docs)": evo,
        "Suspected (unproven, non-blocking)": [f for f in allf if f.get("placement") == "suspected"],
        "Pre-existing": [f for f in allf if f.get("placement") == "pre-existing"],
    }
    repo = Path(p["repo"]).name
    md = [f"# arbiter review {repo} {p['base'][:7]}..{p['head'][:7]} · {p['effort']} · verdict {verdict.upper()}", ""]
    md += ["## Gates", ""]
    for r in gates.get("results", []):
        md.append(f"- {r['name']}: {r['status']}" + (f", exit {r['exit_code']}" if "exit_code" in r else ""))
    for x in gates.get("preexisting", []):
        md.append(f"- pre-existing failure: `{x['cmd']}` exits {x['exit_code']} on HEAD and {x['base_exit_code']} on base")
    md.append("")
    for title, fs in sections.items():
        md += [f"## {title}", ""] + ([_line(f) for f in fs] or ["- none"])
        if title.startswith("Pre-existing"):
            md += [f"- gate: `{x['cmd']}` also fails on base" for x in gates.get("preexisting", [])]
        md.append("")
    overflow = sum(f.get("placement") == "nit-overflow" for f in allf)
    if overflow:
        md += [f"{overflow} more nits not shown (cap {F.NIT_CAP}).", ""]
    md += ["## Spec", ""]
    md += [f"- claim: {c}" for c in intent.get("claims", [])] or ["- no claims extracted"]
    md += [_line(f) for f in spec] + [""]
    md += ["## Coverage", ""]
    md.append(f"- units: {len(cov.get('units', []))} — " + "; ".join(
        f"{u['id']} {u['lang']} churn {u['churn']} [{', '.join(u['files'])}]"
        + (f" triggers {','.join(u['triggers'])}" if u["triggers"] else "") for u in cov.get("units", [])))
    md.append(f"- agents run: {len(cov.get('agents_run', []))}; verifier calls: {cov.get('verifier_calls', 0)}")
    for e in cov.get("agent_failures", []):
        md.append(f"- agent failed: {e}")
    for s in cov.get("agents_skipped", []):
        md.append(f"- agent skipped: {s['agent']} {s.get('unit', '')} ({s['reason']})")
    if p["effort"] == "deep":
        md.append("- deep: k=3 passes for A1a, A1b, A2, A3, A4")
    for t in cov.get("tools", []):
        ver = cov.get("tool_versions", {}).get(t["name"].split()[0], "")
        md.append(f"- tool {t['name']} ({t['lang']}): {'available' if t['available'] else 'missing'}, {t['source']}"
                  + (f", {ver}" if ver else ""))
    pr = cov.get("proofs", {})
    md.append(f"- proofs: {pr.get('attempted', 0)} attempted, {pr.get('confirmed', 0)} confirmed")
    md.append(f"- sandbox: {cov.get('sandbox', 'unknown')}" + "".join(f"; {n}" for n in cov.get("sandbox_notes", [])))
    tm = cov.get("threat_model", {})
    md.append(f"- threat model: {tm.get('path') or 'none'}{' (drafted by arbiter)' if tm.get('drafted') else ''}")
    md.append(f"- harness: {cov.get('harness')}; models: {cov.get('models')}")
    for x in cov.get("excluded", []):
        md.append(f"- excluded from units: {x['path']} ({x['reason']})")
    for n in cov.get("notes", []):
        md.append(f"- note: {n}")
    md.append(f"- wall time: {cov.get('wall_time_s', '?')} s")
    (run / "report.md").write_text("\n".join(md) + "\n")
    (run / "report.json").write_text(json.dumps({
        "verdict": verdict, "repo": p["repo"], "base": p["base"], "head": p["head"], "effort": p["effort"],
        "findings": [f for f in allf if f.get("placement") in ("main", "suspected", "pre-existing", "nit-overflow")],
        "coverage": cov}, indent=2, default=sorted))
