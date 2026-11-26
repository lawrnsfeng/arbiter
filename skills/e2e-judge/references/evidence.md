# Evidence: the freeze, the evidence record, the ladder

A suite proves an obligation only when three things hold:
- the obligation's case ran on the real system through a path a user can take;
- what was observed on every channel matched the expected value taken from the requirements;
- the check that compared them is shown able to fail.

A green run alone shows the first two at best. This file defines how the judge records all three.

## Evidence ladder
Each level includes the ones below it.

| Level | Meaning | Rules out |
|---|---|---|
| E0 | Someone says so | nothing |
| E1 | A `file:line` implements it | an invented implementation |
| E2 | A test exists and maps to the obligation by stimulus and assertion | an untested case |
| E3 | That test ran green on the reviewed patch (`patch_id` below) | a stale or rebased result |
| E4 | The test is shown able to fail: it failed by assertion before the change (the freeze, or step 8), or it killed an oracle-graded mutant aimed at this obligation | tests that restate the code or cannot fail |
| E5 | The obligation's end state was captured in the running app, through the user path: screenshot, video or trace showing the action and the resulting state | a harness proving something users never see |

## Required level per obligation

| Obligation | Minimum | Also required |
|---|---|---|
| `happy`, `partition`, `boundary`, `decision`, `state`, `flow`, `combination`, `property`, `metamorphic` | E4 | every channel in `expect` asserted; boundaries at min−1, min, max, max+1 |
| `unhappy`, `fault-checklist` | E4 | `trigger_proof` observed; the assertion fails for every other action type |
| `must-not` | E4 | the absence is checked after a positive completion signal |
| any obligation with an `entry_point` that is a UI route or element | E5 | captured by the periodic UI run when the PR run cannot |
| `blocked-on Q<n>` or `na` | none | listed, never counted as covered |

An obligation below its minimum is `GAP-EVIDENCE` and appears under **Owed** in the report.

## Proof standards
- Drive the real user path: public routes, UI by role or label, the CLI. Never internal setters or test-only endpoints.
- Capture the action **and** the resulting state, not only the final screen or status.
- Check side effects (rows, files, messages, sinks) alongside what is visible.
- Mock only at a boundary that production already isolates: third parties at the network edge.
- Artifacts survive cleanup, under `$OUT/raw/O<n>/`.

## `freeze.json` (written by the design stage)
```json
{
  "requirements": "<path or URL>",
  "base": "<sha the suite was judged on>",
  "design_commit": "<sha that holds the suite, or null when uncommitted>",
  "files": [{"path": "<suite file>", "blob": "<git hash-object of the file>", "copy": "frozen/<suite file>"}],
  "tests": [
    {"id": "<file>::<test name>", "obligations": ["O4"], "expect_before": "fail | pass | either",
     "before": "fail-assertion | fail-missing: <symbol> | fail-other: <error> | pass | skip: <reason>", "channel": "<obligation's primary channel>"}
  ],
  "verdict": "STRONG | GAPS | WEAK"
}
```
- `expect_before` is `pass` for a test of behaviour that already exists (the requirements call it unchanged: "still", "keeps", "remains"), `either` for a test whose obligations are all `must-not` (the code before the change may already satisfy the absence), and `fail` for every other test.
- `before` is what the run before implementation showed. `fail-assertion` counts only when the failure is an assertion about the obligation's primary channel. A collection, import, fixture, timeout or harness error is `fail-other`.
- `fail-missing: <symbol>` is for compiled test layers: the test's build unit does not compile because `<symbol>`, which the change adds, does not exist yet. It is the right reason for a new-behaviour test, but it shows only that the test needs the change, not that its assertion can fail. Such a test reaches E4 only by a mutant kill. Unchanged-behaviour tests in the same build unit cannot run, so R11 leaves them out.

## `evidence.json` (written by the evidence stage)
One record per obligation:
```json
{
  "obligation": "O4", "clause": "C2", "example": "E2 | null", "entry_point": "EN1 | null",
  "patch": {"head": "<sha>", "base": "<sha>", "patch_id": "<patch-id of the judged worktree index vs base; see below>"},
  "stimulus": "<what the test did>",
  "observed": {"U": "<value>", "P": "<value>", "S": "<value>", "N": "<value>"},
  "oracle": "<file>::<test name>",
  "level": "E0 | E1 | E2 | E3 | E4 | E5",
  "required": "E4 | E5 | none",
  "can_fail": {"fail_before": true, "killed": ["M11"]},
  "artifacts": ["raw/O4/response.json"]
}
```
- `observed` holds the values the test saw, copied from its output or its artifacts, never from the expected value. A test that does not expose a value gets `"<not exposed>"`, and that channel cannot count as asserted.
- `patch_id` is the patch-id of what was judged, recorded in step 2 right after the suite copy and before any build: `git -C $OUT/wt add -A -- <suite paths> <scope files> && git -C $OUT/wt diff --cached <base> | git patch-id --stable`. When that includes uncommitted suite files, `patch.head` reads `<sha>+worktree`.

## The evidence table
The report's `### Evidence` section, one row per example, then one row per obligation that has no example:

```
| Example | Observed on this patch | Level | Proof |
|---|---|---|---|
| E2 rows=4 → 202 queued, jobs [{ann,4}] | 202 {"status":"queued"}; jobs [{ann,4}]; errors [] | E4 | failed before (assertion on api); kills M11 |
| E5 (blocked on Q1) | — | none | — |
```
Rows below their required level are repeated under `### Owed`, each with the cheapest step that would raise the level.
