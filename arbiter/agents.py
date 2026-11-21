"""Prompt assembly, JSON extraction and the one-retry contract for every agent call."""

import json
import re
import time
from pathlib import Path

from . import SKILLS, harness, lang as langmod

REFS = SKILLS / "arbiter-review" / "references"
# label -> stem groups tried in order; the first group matching any row wins (languages name areas differently)
AREA_STEMS = {
    "errors": [["error"]], "resources": [["resource"]], "performance": [["perf"]], "modules": [["module"]],
    "types": [["type"]], "docs": [["doc"]],
    "control flow": [["control flow", "loop", "iterator"], ["type"]],
    "mutability": [["mutab"], ["data model"]],
}


def brief(agent_id: str) -> tuple[dict, str]:
    text = (REFS / "agents" / f"{agent_id}.md").read_text()
    meta = {}
    if text.startswith("---\n"):
        head, text = text[4:].split("\n---\n", 1)
        for line in head.splitlines():
            k, _, v = line.partition(":")
            v = v.split("  #")[0].strip()
            meta[k.strip()] = json.loads(v) if v.startswith(("[", "{")) else v
    return meta, text.strip()


def mission(body: str) -> str:
    m = re.search(r"^## Mission\n(.+?)(?=\n## )", body, re.S | re.M)
    return m[1].strip() if m else ""


def _stems(label: str) -> list[list[str]]:
    key = label.lower()
    return AREA_STEMS.get(key, [[key]])


def select_rows(text: str, labels: list[str]) -> str:
    """Keep markdown table rows whose first cell matches a label (plus each kept table's header)."""
    lines = text.splitlines()
    tables, cur = [], []
    for ln in lines + [""]:
        if ln.lstrip().startswith("|"):
            cur.append(ln)
        elif cur:
            tables.append(cur)
            cur = []
    rows_of = [(t[:2], t[2:]) for t in tables if len(t) > 2]

    def first(row: str) -> str:
        return row.strip().strip("|").split("|")[0].strip().lower()

    keep: dict[int, list[str]] = {}
    for label in labels:
        for group in _stems(label):
            hits = [(i, r) for i, (_, rows) in enumerate(rows_of) for r in rows if any(s in first(r) for s in group)]
            if hits:
                for i, r in hits:
                    keep.setdefault(i, [])
                    if r not in keep[i]:
                        keep[i].append(r)
                break
    out = []
    for i in sorted(keep):
        head, rows = rows_of[i]
        out.append("\n".join(head + [r for r in rows if r in keep[i]]))
    return "\n\n".join(out)


def select_section(text: str, needle: str) -> str:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"^(#+) ", ln)
        if m and needle.lower() in ln.lower():
            level = len(m[1])
            end = next((j for j in range(i + 1, len(lines))
                        if (h := re.match(r"^(#+) ", lines[j])) and len(h[1]) <= level), len(lines))
            return "\n".join(lines[i:end]).strip()
    return ""


def lang_refs(refs: list[dict], langs: list[str]) -> str:
    parts = []
    for lg in langs:
        if lg not in langmod.SKILL_DIR:
            continue
        d = SKILLS / f"{langmod.SKILL_DIR[lg]}-review" / "references"
        for ref in refs:
            p = d / ref["file"]
            if not p.exists():
                continue
            text = p.read_text()
            if "rows" in ref:
                text = select_rows(text, ref["rows"])
                what = f"rows {', '.join(ref['rows'])}"
            elif "section" in ref:
                text = select_section(text, ref["section"])
                what = f"section {ref['section']}"
            else:
                what = "whole file"
            if text.strip():
                parts.append(f"## {lg} reference: {ref['file']} ({what})\n\n{text.strip()}")
    return "\n\n".join(parts)


def schema_section(output: str) -> str:
    text = (REFS / "schema.md").read_text()
    return select_section(text, {"findings": "Candidate", "vote": "Vote", "proof": "Proof", "intent": "Intent"}[output])


def build_prompt(agent_id: str, langs: list[str], inputs: dict[str, str]) -> tuple[str, dict]:
    meta, body = brief(agent_id)
    task = mission(body)
    out = meta.get("output", "findings")
    wrapper = {"findings": '{"findings": [...]}', "vote": "one Vote JSON object", "proof": "one Proof JSON object",
               "intent": "one Intent JSON object"}[out]
    sections = [f"TASK: {task}", (REFS / "agent-preamble.md").read_text().strip(), body]
    if (refs := lang_refs(meta.get("refs") or [], langs)):
        sections.append("# Language references\n\n" + refs)
    sections.append("# Inputs\n\n" + "\n\n".join(f"## {k}\n\n{v}" for k, v in inputs.items() if v))
    sections.append("# Output schema\n\n" + schema_section(out))
    sections.append(f"TASK (repeated): {task}\nReply with only {wrapper}.")
    return "\n\n---\n\n".join(sections), meta


def extract_json(text: str):
    """The last fenced ```json block, else the last top-level JSON object/array in the text."""
    fences = re.findall(r"```(?:json)?\s*\n(.*?)\n```", text, re.S)
    for cand in reversed(fences):
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue
    dec = json.JSONDecoder()
    last, i = None, 0
    while i < len(text):
        if text[i] in "{[":
            try:
                val, end = dec.raw_decode(text, i)
                last, i = val, end
                continue
            except json.JSONDecodeError:
                pass
        i += 1
    if last is None:
        raise ValueError("no JSON value found")
    return last


def run(agent_id: str, role: str, prompt: str, validate, *, tools: str, cwd: Path, timeout: int = 600):
    """Call, parse, validate; one retry with the error appended. Returns (value, error|None)."""
    err = None
    for attempt in (1, 2):
        p = prompt if attempt == 1 else f"{prompt}\n\nYour previous output was invalid: {err}. Reply with only the JSON."
        try:
            try:
                text = harness.call(role, p, tools=tools, cwd=cwd, timeout=timeout)
            except harness.HarnessError as e:
                if "timeout" in str(e):
                    raise
                time.sleep(30)  # provider hiccups and rate limits are transient; one paced retry
                text = harness.call(role, p, tools=tools, cwd=cwd, timeout=timeout)
            value = extract_json(text)
            validate(value)
            return value, None
        except harness.HarnessError as e:
            return None, f"{agent_id}: harness {e}"
        except (ValueError, TypeError, KeyError) as e:
            err = str(e)[:300]
    return None, f"{agent_id}: invalid output twice: {err}"
