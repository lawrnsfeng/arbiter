# Rulebook

The owner's own refactoring and design rules, Python first (`python/R01-…` … `python/R89-…`). Each rule is a set
of clauses, examples of the incorrect approach (`bad.py`) and of the correct one (`good.py`), and a detector
(`check.py`, stdlib `ast`) and/or instructions for a model scan. Rules are curated with `replay.py` and run over code
with `scan.py`; arbiter's review run does not traverse them yet (ledger R-08, plan in
[research/rulebook-feasibility/README.md](../research/rulebook-feasibility/README.md)).

## Layout

```
rulebook/
  rulekit.py                  shared detector contract: Module, Hit, load, functions, classes, local_nodes, params_of
  replay.py                   curation check: every detector on its own examples + folder validation
  scan.py                     traversal: every rule over a codebase, JSON report
  python/R46-<kebab-slug>/    two-digit folder number, slug of at most 5 words
    rule.md                   front matter + sections below
    bad.py                    incorrect variants; markers on the lines to report
    good.py                   the correct approach and look-alikes that must stay silent
    check.py                  exists iff tier contains `ast`
```

Copy `python/_template/` to start. Folders starting with `_` are skipped.

`rule.md` front matter has exactly these keys:

| Key | Value |
|---|---|
| `id` | `R1` … `R89`, the owner's numbering, no zero padding; must match the folder number |
| `title` | generalised one-line name |
| `tier` | `ast`, `semantic` or `ast+semantic` |
| `severity` | `should-fix` |
| `status` | `ok`, or `unclear` when the rule's meaning is in question |
| `refs` | comma-separated public sources, or `owner convention` |

Body sections, in order: `## Rule` (one bullet per clause, ending with its clause id, e.g. `(C3)`), `## Incorrect`,
`## Correct` (one-line summaries of the example files), `## Detection` (exactly what `check.py` reports; omitted for
`semantic`), `## LLM scan` (present iff the tier contains `semantic`: what the model must look for beyond the
detector, and what not to flag).

`bad.py` and `good.py` must parse with `ast.parse`; they are never executed, so undefined names are fine. In
`bad.py` a line the detector must report ends with `# expect: R46`; a line only the model can catch ends with
`# expect-llm: R46`.

## Tiers

| Tier | When | Guarantee |
|---|---|---|
| `ast` | every clause is decidable from syntax and structure: counts, names, call shapes, where a node lives, cross-module facts | every occurrence in every file that parses |
| `ast+semantic` | a detector finds a definite subset or the candidates; some clauses need judgement | the detector's subset as for `ast`; the rest is the model's, per `## LLM scan` |
| `semantic` | no syntactic signal at all | none by construction: a model judges every symbol against `## LLM scan` |

Prefer `ast`. A regex/grep rule is not a tier: on the feasibility run a regex for accessors matched 805 lines of
which 59 were accessors. `semgrep` (`check.yml`) remains supported only for the feasibility samples in
`research/rulebook-feasibility/rules/`.

## Detector contract

```python
from rulekit import Hit, Module, classes, functions, local_nodes, params_of

RULE = "R46"


def check(modules: list[Module]) -> list[Hit]: ...
```

`check` receives every scanned module at once, so cross-file rules ("is this class subclassed anywhere") work. It
imports only the stdlib and `rulekit`, and returns one `Hit(path, line, message)` per occurrence, at the line of the
offending node; the message starts with the rule id. Add a helper to `rulekit.py` only when two or more detectors
need it.

## Curation loop

1. Write the rule's clauses, `bad.py` and `good.py`.
2. Write `check.py`, then `python rulebook/replay.py rulebook/python/R46-*` until it passes: every `# expect:` line
   hit, nothing else, `good.py` silent. Replay also validates the folder layout above.
3. Scan real code; each false hit becomes a case in `good.py`, each miss a case in `bad.py`; replay again.

`python rulebook/replay.py` replays every rule and ends with `N rules: P pass, F fail` (exit 1 on any fail).

## Scanning code

```
python rulebook/scan.py [--rules DIR] [--json OUT] PATH...
```

Directories expand to every `*.py` below them, sorted; nothing is ignored. Every rule appears exactly once in the
report, whatever happens to the others:

```json
{"targets": 3819, "parsed": 3817, "unparsable": ["path"],
 "rules": [{"id": "R46", "title": "...", "tier": "ast",
            "status": "violation|clean|error|llm-pending",
            "hits": [{"path": "...", "line": 12, "message": "..."}],
            "error": "only when status is error",
            "llm": "rulebook/python/R46-.../rule.md, only when the tier contains semantic"}]}
```

`ast+semantic` rules carry their detector status and `llm`; `semantic` rules are `llm-pending`. A one-line summary
per rule goes to stderr. Exit 2 if any rule errored or any target was unparsable, else 1 if any violation, else 0.
