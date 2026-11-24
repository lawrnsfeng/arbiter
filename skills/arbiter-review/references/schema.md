# Output schemas

Reply with exactly one JSON value and nothing else. arbiter validates it. Invalid output gets one retry, then the agent is recorded as failed.
Fields marked "arbiter" are filled in by arbiter; omit them.

## Candidate

Finder agents (`output: findings`, also SPEC) reply with `{"findings": [Candidate, ...]}`. An empty list is a valid answer.

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | string | yes | Repo-relative path. |
| `line` | int | yes | First line of the issue, on the new side. Must fall inside the unit's changed hunks ±3 lines. |
| `end_line` | int | no | Last line, ≥ `line`. |
| `quote` | string | no | The exact text of the first flagged line, copied from the code; arbiter uses it to fix a wrong `line`. Recommended for every finding. |
| `trigger` | string | functional axes | The input or state that makes the defect happen. Write it before `claim`. |
| `evidence_lines` | list of string | yes | ≥1 `"path:line"` you read that supports the claim. Write them before `claim`. |
| `claim` | string | yes | One sentence: what is wrong. |
| `axis` | string | yes | One of `logic edge tests errors resources observability security privacy concurrency api data portability deps performance ops a11y spec` (functional) or `maintainability idiom design docs` (evolvability). |
| `severity` | string | yes | `block`, `should-fix` or `nit`. Evolvability is capped at `should-fix` unless a block-eligible `measure` or a `[block]` repo rule backs it. |
| `type` | string | no | `defect`, `refactor` or `nit`. Default `defect`. |
| `measure` | string | no | Id of an arbiter maintainability fact (`m03`) the finding reports. |
| `cwe` | int | `security`, `privacy` | CWE number, e.g. `89`. |
| `rule` | string | evolvability axes | Canon key (`P8`, `EP3 Item 37`, `C-GOOD-ERR`, `GSD`), repo rule `file#heading`, or a linter rule id. |
| `precedent` | string | no | `"path:line"` in this repo that follows the rule. Evolvability needs `precedent` unless `rule` is a linter id or `measure` names an arbiter fact. |
| `code_judo` | bool | no | `true` only for a pstack code-judo item (A6b). |
| `fix` | string | no | The smallest fix, in one or two sentences. |
| `proof_plan` | object | functional axes | `{"rung": "E1".."E9", "idea": "<how to prove it>"}`. |
| `addresses` | string | no | Requirement id from the Requirements input, e.g. `R2`, when the finding puts that requirement at risk. |
| `patches` | list of object | no | At most 2 GitHub-suggestion patches replacing lines `start_line`–`end_line` of `file`: `{"title", "start_line", "end_line", "code"}`, at most 10 lines each. |
| `agent`, `pass`, `group`, `id` | — | arbiter | Filled in by arbiter. |

```json
{"findings": [
  {"file": "src/pager.py", "line": 42, "end_line": 42,
   "quote": "    return items[start:end + 1]",
   "trigger": "page(items=list(range(10)), size=3, n=0) returns 4 items",
   "evidence_lines": ["src/pager.py:42", "src/pager.py:12"],
   "claim": "page() returns one item too many because the slice end is end+1.",
   "axis": "logic", "severity": "block", "type": "defect",
   "fix": "Use items[start:end].",
   "proof_plan": {"rung": "E4", "idea": "Test that page(range(10), 3, 0) has length 3, per the docstring at src/pager.py:12."}}
]}
```

## Vote

The verifier V replies with one Vote object.

| Field | Type | Required | Notes |
|---|---|---|---|
| `verdict` | string | yes | `TRUE_POSITIVE`, `FALSE_POSITIVE` or `PREDATES_CHANGE`. |
| `severity` | string | yes | `block`, `should-fix` or `nit`. Never higher than the finder's severity. |
| `reason` | string | yes | Short reasoning that names the decisive `path:line`. |
| `cited` | list of string | yes | ≥1 `"path:line"` you read. |
| `finding_id`, `lens` | — | arbiter | Filled in by arbiter. |

```json
{"verdict": "FALSE_POSITIVE", "severity": "should-fix",
 "reason": "The only caller at src/api.py:88 validates size > 0 before calling page(), so the empty case cannot occur.",
 "cited": ["src/api.py:88", "src/pager.py:40"]}
```

## Proof

The proof agent P replies with one Proof object. arbiter re-reads exit codes from its own exec log by `exec_id`; exit codes you claim are ignored.

| Field | Type | Required | Notes |
|---|---|---|---|
| `rung` | string | yes | `E1` … `E9`; must be in the run's ALLOWED_RUNGS. |
| `oracle_source` | string | E4, E6 | `path:line` of the spec, docstring, type or caller that defines correct behaviour, or a spec quote. |
| `before` | object | yes | `{"exec_id": str, "cmd": str, "exit_code": int, "output_excerpt": str}` from `arbiter sandbox exec`. |
| `after` | object | E4 | Same shape; the run with the minimal fix applied. |
| `artifact` | string | no | Path of the proof file or log under `RUN/proofs/` or `RUN/wt/arbiter_proofs/`. |
| `result` | string | yes | `confirmed`, `not_reproduced` or `error`. |
| `finding_id` | — | arbiter | Filled in by arbiter. |

```json
{"rung": "E4", "oracle_source": "src/pager.py:12 docstring: returns at most size items",
 "before": {"exec_id": "x0007", "cmd": "uv run pytest -q arbiter_proofs/test_arbiter_proof_f03.py", "exit_code": 1, "output_excerpt": "AssertionError: assert 4 == 3"},
 "after": {"exec_id": "x0008", "cmd": "uv run pytest -q arbiter_proofs/test_arbiter_proof_f03.py", "exit_code": 0, "output_excerpt": "1 passed"},
 "artifact": "RUN/wt/arbiter_proofs/test_arbiter_proof_f03.py", "result": "confirmed"}
```

## Intent

The intent agent A0 replies with one Intent object.

| Field | Type | Required | Notes |
|---|---|---|---|
| `claims` | list of string | yes | Each behaviour the change claims to deliver, one per item. May be empty. |
| `spec_source` | string | yes | Path or issue ref the claims came from, or `none`. |
| `threat_model_path` | string | yes | Path of the repo's threat model, or `none`. |
| `unit_notes` | object | yes | Unit id → one-line risk note, for `plan_required` units. May be `{}`. |
| `threat_model_draft` | string | no | Markdown using the threat-model template headings. Give it only when the inputs contain no threat model. arbiter writes it to `RUN/THREAT_MODEL.draft.md`. |

```json
{"claims": ["page() returns at most size items", "adds --page-size CLI flag"],
 "spec_source": "docs/specs/paging.md",
 "threat_model_path": "none",
 "unit_notes": {"u02": "Changes the SQL paging query used by the public /items endpoint."},
 "threat_model_draft": "## Assets\nItem records in SQLite.\n## Entry points\nCLI `items list`.\n## Trust boundaries\nCLI user → process.\n## Trusted inputs\nCLI flags, env vars.\n## In-scope classes\nSQL injection, path traversal.\n## Out-of-scope classes\nDoS.\n## DoS policy\nOut of scope: local CLI."}
```

## Decision

The decision agent DECIDE replies with one Decision object. Finding ids are the `id` values in the Findings input.

| Field | Type | Required | Notes |
|---|---|---|---|
| `summary` | string | yes | The merge decision in at most 300 characters. |
| `next_action` | string | yes | What the author should do next, at most 200 characters. |
| `links` | object | yes | Finding id → requirement id (`R2`, `B1`) it puts at risk, or `null`; only for findings without `addresses`. May be `{}`. |
| `dismiss` | list of object | yes | `{"id", "reason"}` for should-fix, verify or optional findings that would not change a merge decision or are clearly wrong. May be empty. |
| `challenge` | list of object | yes | `{"id", "reason"}` for must-fix findings you doubt; they stay must-fix. May be empty. |
| `missed` | list of object | yes | At most 3: `{"file", "line", "axis", "claim", "addresses"}` on changed lines. May be empty. |

```json
{"summary": "Blocks on the proven off-by-one in page(); the rest is minor.",
 "next_action": "Fix #1, then answer the should-fix item.",
 "links": {"f002": "R1"},
 "dismiss": [{"id": "f004", "reason": "Style preference with no effect on behaviour."}],
 "challenge": [],
 "missed": [{"file": "src/pager.py", "line": 50, "axis": "edge", "claim": "size=0 divides by zero.", "addresses": "R1"}]}
```
