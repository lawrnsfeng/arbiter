# Obligation format (shared by e2e-design and e2e-judge)

An **obligation** is one thing the system must do, or must not do, that one e2e test can check. It is a clause × coverage item × required action, with an expected outcome on every channel.
The designer writes the obligations and then the tests. The judge re-derives them without looking, then grades the suite against them. Both use this file's format and IDs, so their outputs can be diffed.

## IDs
- `C<n>`: atomic requirement clause, numbered in order of appearance in the requirements.
- `Q<n>`: open question: a requirement is ambiguous or silent.
- `O<n>`: obligation.
- `M<n>`: code mutant (judge only).
- `SM<n>`: spec mutant (judge only).
- Test titles start with the obligation IDs they cover, joined by `+`, then a colon. Runners whose test names must be identifiers (pytest, Go, Rust) use `test_o7_o8_<summary>` / `TestO7O8_<Summary>` instead:
  `O7+O8: expired card returns 402 and creates no order`.
  - One test covers **at most one** invalid or unhappy obligation (no masking).
  - It may cover several valid ones.

## Clause grammar (EARS)
Rewrite every clause into one EARS pattern, and keep the verbatim source sentence in `quote`:
- Ubiquitous: `THE SYSTEM SHALL <response>`
- Event: `WHEN <trigger> THE SYSTEM SHALL <response>`
- State: `WHILE <state> THE SYSTEM SHALL <response>`
- Unwanted behaviour: `IF <unwanted trigger> THEN THE SYSTEM SHALL <response>`
- Optional feature: `WHERE <feature> THE SYSTEM SHALL <response>`

Rules:
- Every conditional clause gets its complement clause. Mark it `"origin": "derived"`.
- If the requirements do not state the complement's response, raise a `Q`.
- Never fill a response in from the code, from the running app, or from "reasonable" defaults.

## Actions
Every obligation names exactly one primary action:

| `action` | Meaning | Primary channel |
|---|---|---|
| `none` | happy path: the specified result | U and P |
| `default` | early return or fallback with a specified value | U (exact default value) |
| `error` | specified error: status, machine-readable code, message | U (API status + code, UI message) |
| `delegate` | hands off to another component: retry, fallback provider, compensation | S (request journal: count, order, payload) |
| `user-message` | failure shown to the user | U (by role `alert`/`status` or accessible error message) |
| `emit` | failure sent to a sink: log, metric, span, error tracker, DLQ, outbox, mail, webhook | S (the named sink) |

## Channels
Every expected outcome is written per channel:
- **U** user-visible: UI text by role, HTTP status, body, error code.
- **P** persisted: state read back via reload or public API. Raw storage only when no public read exists; say why.
- **S** side-effect: the sinks named in the feature's channel inventory.
- **N** negative: what must not happen, over every channel in the inventory.

The **channel inventory** lists every DB table, queue, outbox, mail sink, webhook, third party, error tracker, metric and audit log the feature can touch. It is written once per feature.

## `obligations.json`
```json
{
  "source": "<path or issue URL of the requirements>",
  "slug": "<kebab-case feature name>",
  "channels": ["ui", "api", "db:orders", "queue:exports", "log", "tracker", "mail"],
  "clauses": [
    {"id": "C1", "origin": "explicit", "quote": "<verbatim requirement text>",
     "ears": "IF <trigger> THEN THE SYSTEM SHALL <response>"}
  ],
  "questions": [
    {"id": "Q1", "text": "<question>", "blocks": ["O4"], "answer": null}
  ],
  "obligations": [
    {
      "id": "O1",
      "clause": "C1",
      "kind": "happy | partition | boundary | decision | state | flow | combination | unhappy | must-not | property | metamorphic | fault-checklist",
      "technique": "EP | BVA | DT | CE | ST | UC | PICT | EG | PBT | MR",
      "unhappy_class": null,
      "action": "none | default | error | delegate | user-message | emit",
      "precondition": "<seeded state>",
      "stimulus": "<the single When action or command sequence>",
      "expect": {"U": "<exact>", "P": "<exact>", "S": "<exact or empty>", "N": "<forbidden effects>"},
      "trigger_proof": "<for injected faults: how the test proves the fault fired, else empty>",
      "risk": "H | M | L",
      "status": "open | blocked-on Q1 | na: <reason>"
    }
  ]
}
```

Field rules:
- `unhappy_class` is the class number 1–14 from `unhappy.md` §10, or `null`.
- `expect.N` is empty only for `kind: happy` obligations whose clause names no forbidden effect.

The designer adds `"tests": [{"id": "T1", "file": "<path>", "title": "<title>", "obligations": ["O1"]}]` at top level.

The judge adds these fields to each obligation in its own copy:
`"tests": ["T1"]`, `"grade": "O0|O1|O2|O3"`, `"coverage": "hit|miss|not measured: <reason>"`,
`"mutants": {"killed_oracle": ["M3"], "killed_incidental": [], "survived": ["M4"]}`,
`"spec_mutants": {"distinguished": ["SM2"], "missed": []}`,
`"gap": null | "GAP-MISSING" | "GAP-ORACLE" | "GAP-UNREACHED" | "GAP-PSEUDO" | "GAP-QUESTION" | "GAP-FLAKY"`,
`"needed": "<exact assertion on which channel that would close the gap>"`.

## `<slug>.matrix.md`
One table rendered from `obligations.json`, one row per obligation:

| Obligation | Clause | Kind / technique | Action | Test | U | P | S | N | Determinism (seed · clock · fault) | Risk | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|

After the table:
- **per-technique coverage**: covered items / identified items, as a %;
- the open questions;
- the channel inventory.
