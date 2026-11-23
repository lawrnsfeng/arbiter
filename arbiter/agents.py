"""Prompt assembly, JSON extraction and the one-retry contract for every agent call."""

import json
import re
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from . import SKILLS, harness
from . import lang as langmod
from .harness import Tools

REFS = SKILLS / "arbiter-review" / "references"
# label -> stem groups tried in order; the first group matching any row wins (languages name areas differently)
AREA_STEMS = {
    "errors": [["error"]],
    "resources": [["resource"]],
    "performance": [["perf"]],
    "modules": [["module"]],
    "types": [["type"]],
    "docs": [["doc"]],
    "control flow": [["control flow", "loop", "iterator"], ["type"]],
    "mutability": [["mutab"], ["data model"]],
}
HEADING = re.compile(r"^(#+) ")
MISSION = re.compile(r"^## Mission\n(.+?)(?=\n## )", re.DOTALL | re.MULTILINE)
FENCE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)
RETRY_PAUSE_S = 30


class Output(StrEnum):
    FINDINGS = "findings"
    VOTE = "vote"
    PROOF = "proof"
    INTENT = "intent"

    @property
    def schema_heading(self) -> str:
        return {"findings": "Candidate", "vote": "Vote", "proof": "Proof", "intent": "Intent"}[self]

    @property
    def wrapper(self) -> str:
        return '{"findings": [...]}' if self is Output.FINDINGS else f"one {self.schema_heading} JSON object"


class Ref(TypedDict):
    """A language reference a brief asks for: the whole file, some table rows, or one section."""

    file: str
    rows: NotRequired[list[str]]
    section: NotRequired[str]


@dataclass(frozen=True, slots=True)
class Brief:
    id: str
    output: Output
    refs: list[Ref] = field(default_factory=list)
    body: str = ""

    @property
    def mission(self) -> str:
        return mission(self.body)


def brief(agent_id: str) -> Brief:
    text = (REFS / "agents" / f"{agent_id}.md").read_text()
    meta: dict[str, Any] = {}
    if text.startswith("---\n"):
        head, text = text[4:].split("\n---\n", 1)
        for line in head.splitlines():
            k, _, v = line.partition(":")
            v = v.split("  #")[0].strip()
            meta[k.strip()] = json.loads(v) if v.startswith(("[", "{")) else v
    return Brief(
        id=meta.get("id", agent_id),
        output=Output(meta.get("output", Output.FINDINGS)),
        refs=meta.get("refs") or [],
        body=text.strip(),
    )


def mission(body: str) -> str:
    return m[1].strip() if (m := MISSION.search(body)) else ""


def _tables(text: str) -> list[tuple[list[str], list[str]]]:
    """Markdown tables as (header + separator, data rows); tables without data rows are skipped."""
    tables, cur = [], []
    for ln in [*text.splitlines(), ""]:
        if ln.lstrip().startswith("|"):
            cur.append(ln)
        elif cur:
            tables.append(cur)
            cur = []
    return [(t[:2], t[2:]) for t in tables if len(t) > 2]


def _first_cell(row: str) -> str:
    return row.strip().strip("|").split("|")[0].strip().lower()


def select_rows(text: str, labels: Iterable[str]) -> str:
    """Keep markdown table rows whose first cell matches a label, plus each kept table's header."""
    tables = _tables(text)
    keep: dict[int, list[str]] = {}
    for label in labels:
        for stems in AREA_STEMS.get(label.lower(), [[label.lower()]]):
            hits = [
                (i, r) for i, (_, rows) in enumerate(tables) for r in rows if any(s in _first_cell(r) for s in stems)
            ]
            for i, r in hits:
                if r not in (kept := keep.setdefault(i, [])):
                    kept.append(r)
            if hits:
                break
    return "\n\n".join("\n".join([*tables[i][0], *(r for r in tables[i][1] if r in keep[i])]) for i in sorted(keep))


def select_section(text: str, needle: str) -> str:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if (m := HEADING.match(ln)) and needle.lower() in ln.lower():
            level = len(m[1])
            end = next(
                (j for j in range(i + 1, len(lines)) if (h := HEADING.match(lines[j])) and len(h[1]) <= level),
                len(lines),
            )
            return "\n".join(lines[i:end]).strip()
    return ""


def lang_refs(refs: list[Ref], langs: Iterable[str]) -> str:
    parts = []
    for lg in langs:
        if lg not in langmod.SKILL_DIR:
            continue
        d = SKILLS / f"{langmod.SKILL_DIR[langmod.Lang(lg)]}-review" / "references"
        for ref in refs:
            if not (p := d / ref["file"]).exists():
                continue
            text = p.read_text()
            if rows := ref.get("rows"):
                text, what = select_rows(text, rows), f"rows {', '.join(rows)}"
            elif section := ref.get("section"):
                text, what = select_section(text, section), f"section {section}"
            else:
                what = "whole file"
            if text.strip():
                parts.append(f"## {lg} reference: {ref['file']} ({what})\n\n{text.strip()}")
    return "\n\n".join(parts)


def schema_section(output: Output) -> str:
    return select_section((REFS / "schema.md").read_text(), output.schema_heading)


def build_prompt(agent_id: str, langs: Iterable[str], inputs: dict[str, str]) -> tuple[str, Brief]:
    """Task first and last (lost-in-the-middle), then preamble, brief, references, inputs and schema."""
    b = brief(agent_id)
    task = b.mission
    sections = [f"TASK: {task}", (REFS / "agent-preamble.md").read_text().strip(), b.body]
    if refs := lang_refs(b.refs, langs):
        sections.append(f"# Language references\n\n{refs}")
    sections.append("# Inputs\n\n" + "\n\n".join(f"## {k}\n\n{v}" for k, v in inputs.items() if v))
    sections.append(f"# Output schema\n\n{schema_section(b.output)}")
    sections.append(f"TASK (repeated): {task}\nReply with only {b.output.wrapper}.")
    return "\n\n---\n\n".join(sections), b


def extract_json(text: str) -> Any:
    """The last fenced ```json block, else the last top-level JSON object or array in the text."""
    for cand in reversed(FENCE.findall(text)):
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue
    dec = json.JSONDecoder()
    last, i = None, 0
    while i < len(text):
        if text[i] in "{[":
            try:
                last, i = dec.raw_decode(text, i)
                continue
            except json.JSONDecodeError:
                pass
        i += 1
    if last is None:
        raise ValueError("no JSON value found")
    return last


def _call(role: str, prompt: str, tools: Tools | str, cwd: Path, timeout: int) -> str:
    try:
        return harness.call(role, prompt, tools=tools, cwd=cwd, timeout=timeout)
    except harness.HarnessError as e:
        if "timeout" in str(e):
            raise
        print(f"arbiter: {role} harness error, retrying in {RETRY_PAUSE_S}s: {str(e)[:200]}", file=sys.stderr)
        time.sleep(RETRY_PAUSE_S)  # provider hiccups and rate limits are transient; one paced retry
        return harness.call(role, prompt, tools=tools, cwd=cwd, timeout=timeout)


def run(
    agent_id: str,
    role: str,
    prompt: str,
    validate: Callable[[Any], object],
    *,
    tools: Tools | str,
    cwd: Path,
    timeout: int = 600,
) -> tuple[Any, str | None]:
    """Call, parse and validate, with one retry that carries the error. Returns (value, error or None)."""
    err = None
    for attempt in (1, 2):
        p = (
            prompt
            if attempt == 1
            else f"{prompt}\n\nYour previous output was invalid: {err}. Reply with only the JSON."
        )
        try:
            value = extract_json(_call(role, p, tools, cwd, timeout))
            validate(value)
            return value, None
        except harness.HarnessError as e:
            return None, f"{agent_id}: harness {e}"
        except (ValueError, TypeError, KeyError) as e:
            err = str(e)[:300]
    return None, f"{agent_id}: invalid output twice: {err}"
