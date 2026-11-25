"""The decision ledger: docs/decisions.jsonl is the source; docs/decisions.md and the README's review-technique table
are rendered from it."""

import argparse
import json
import re

from . import HOME, ArbiterExit

LEDGER = HOME / "docs" / "decisions.jsonl"
RENDERED = HOME / "docs" / "decisions.md"
HEADER = HOME / "docs" / "decisions.header.md"
README = HOME / "README.md"
TECH_BEGIN, TECH_END = "<!-- techniques:begin (arbiter ledger render) -->", "<!-- techniques:end -->"
TECH_AREAS = ("architecture", "models", "units", "accuracy", "leader", "maintainability")  # review technique, not eval

AREAS = {
    "architecture": "1. Architecture and pipeline",
    "models": "2. Models and cost",
    "units": "3. Decomposition (review units)",
    "accuracy": "4. Accuracy techniques (beyond decomposition)",
    "leader": "4b. From the leader study",
    "maintainability": "4c. Maintainability",
    "rules": "5. Learned rules from past PRs and MRs",
    "tools": "6. External tools and platforms",
    "eval": "7. Evaluation and process",
    "rejected": "8. Rejected approaches",
}
AREA_INTRO: dict[str, str] = {
    "architecture": "",
    "models": "",
    "units": "",
    "accuracy": "Ranked in `research/research-accuracy-techniques.md`. Every gain is extrapolated from the literature, "
    "not measured on arbiter.",
    "leader": "Source: `research/research-leader-approaches.md` (Augment, Qodo 2.0, cubic, alibaba OpenCodeReview and "
    "AACR-Bench).",
    "maintainability": "",
    "rules": "Design and evidence: `research/research-learned-rules.md`. Verdict: it works mostly through learned "
    "suppression and validated deterministic checks; rule text in prompts is the weakest part.",
    "tools": "Evaluation: `research/research-code-quality-platforms.md`.",
    "eval": "",
    "rejected": "Every dropped idea, with where it came from and why that source uses it. "
    "Rows keep their original IDs.",
}
STATUSES = ("adopted", "switch", "proposed", "deferred", "dropped", "open")
REJECTED_FIELDS = ("source", "what", "why_source", "why_dropped")
ID_RE = re.compile(r"^[A-Z]{1,2}-\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TABLE = "| ID | Date | Idea or concern | Status | Evidence | Where / next |\n|---|---|---|---|---|---|"
REJECTED_TABLE = (
    "| ID | Date | Source (tool, framework or paper) | What it is | Why the source uses it | Why arbiter dropped it |\n"
    "|---|---|---|---|---|---|"
)


def load() -> list[dict[str, str | None]]:
    return [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]


def save(rows: list[dict[str, str | None]]) -> None:
    LEDGER.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def check(rows: list[dict[str, str | None]]) -> list[str]:
    errors, seen = [], set()
    for r in rows:
        rid = r.get("id") or "?"
        if rid in seen:
            errors.append(f"{rid}: duplicate id")
        seen.add(rid)
        if not ID_RE.match(rid):
            errors.append(f"{rid}: id must match {ID_RE.pattern}")
        if r.get("area") not in AREAS:
            errors.append(f"{rid}: unknown area {r.get('area')!r}")
        if r.get("status") not in STATUSES:
            errors.append(f"{rid}: unknown status {r.get('status')!r}")
        if (d := r.get("date")) is not None and not DATE_RE.match(d):
            errors.append(f"{rid}: date must be YYYY-MM-DD or null")
        if not r.get("title"):
            errors.append(f"{rid}: empty title")
        if r.get("area") == "rejected":
            if missing := [k for k in REJECTED_FIELDS if not r.get(k)]:
                errors.append(f"{rid}: rejected row missing {', '.join(missing)}")
            if r.get("status") != "dropped":
                errors.append(f"{rid}: rejected row must have status dropped")
    return errors


def _cell(v: str | None) -> str:
    return (v or "").replace("|", "\\|")


def _line(r: dict[str, str | None]) -> str:
    if r["area"] == "rejected":
        cells = [r["id"], r.get("date") or "—", *(r.get(k) for k in REJECTED_FIELDS)]
    else:
        status = f"{r['status']}" + (f", {note}" if (note := r.get("status_note")) else "")
        where = (r.get("where") or "") + (f" · next: {nxt}" if (nxt := r.get("next")) else "")
        cells = [r["id"], r.get("date") or "—", r["title"], status, r.get("evidence"), where]
    return "| " + " | ".join(_cell(c) for c in cells) + " |"


def render(rows: list[dict[str, str | None]]) -> str:
    out = [HEADER.read_text().rstrip("\n")]
    for area, heading in AREAS.items():
        out += ["", f"## {heading}", ""]
        if intro := AREA_INTRO[area]:
            out += [intro, ""]
        out.append(REJECTED_TABLE if area == "rejected" else TABLE)
        out += [_line(r) for r in rows if r["area"] == area]
    return "\n".join(out) + "\n"


def techniques(rows: list[dict[str, str | None]]) -> str:
    """README table: every adopted or switched review technique, so the README never lags the ledger."""
    out = ["| ID | Technique | Status |", "|---|---|---|"]
    for area in TECH_AREAS:
        for r in rows:
            if r["area"] == area and r["status"] in ("adopted", "switch"):
                status = r["status"] + (f": {n}" if (n := r.get("status_note")) else "")
                out.append("| " + " | ".join(_cell(c) for c in (r["id"], r["title"], status)) + " |")
    return "\n".join(out)


def readme_with(rows: list[dict[str, str | None]], text: str) -> str:
    head, sep, rest = text.partition(TECH_BEGIN)
    _, sep2, tail = rest.partition(TECH_END)
    if not (sep and sep2):
        raise ArbiterExit(2, f"arbiter: README.md lacks the {TECH_BEGIN} … {TECH_END} markers")
    return f"{head}{TECH_BEGIN}\n{techniques(rows)}\n{TECH_END}{tail}"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="arbiter ledger")
    ap.add_argument("action", choices=("list", "show", "render", "check"))
    ap.add_argument("id", nargs="?")
    ap.add_argument("--status", choices=STATUSES)
    ap.add_argument("--area", choices=list(AREAS))
    ap.add_argument("--since", help="YYYY-MM-DD")
    a = ap.parse_args(argv)
    rows = load()
    match a.action:
        case "list":
            for r in rows:
                if (a.status and r["status"] != a.status) or (a.area and r["area"] != a.area):
                    continue
                if a.since and not (r.get("date") and r["date"] >= a.since):
                    continue
                print(f"{r['id']}  {r['status']}  {r['title']}")
        case "show":
            if not (hit := next((r for r in rows if r["id"] == a.id), None)):
                raise ArbiterExit(2, f"arbiter: no ledger row {a.id}")
            print(json.dumps(hit, indent=2, ensure_ascii=False))
        case "render":
            RENDERED.write_text(render(rows))
            README.write_text(readme_with(rows, README.read_text()))
        case "check":
            errors = check(rows)
            for e in errors:
                print(e)
            stale = not RENDERED.exists() or RENDERED.read_text() != render(rows)
            if stale:
                print("docs/decisions.md is stale: run arbiter ledger render")
            if (readme := README.read_text()) != readme_with(rows, readme):
                stale = True
                print("README.md review techniques are stale: run arbiter ledger render")
            return 1 if errors or stale else 0
    return 0
