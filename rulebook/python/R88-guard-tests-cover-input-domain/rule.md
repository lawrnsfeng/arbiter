---
id: R88
title: A guard is tested across its input domain, not against the inputs that came to mind
tier: semantic
severity: should-fix
status: ok
refs: ISTQB / ISO 29119-4 equivalence partitioning and boundary value analysis, Hypothesis docs (property-based testing), pytest docs parametrize, Python docs dataclasses (mutable default values)
---
## Rule

- A guard's tests cover its input domain, not a single bad value. (C1)
- For each guard, name the value classes it must decide: absent, empty, wrong type, unknown member, over a bound, under a bound, and the mutable default. (C2)
- Every value class gets one assertion; a class with no assertion is an untested refusal and a violation. (C3)
- A guard runs before any side effect; a guard that fires after a side effect has landed is not a guard. (C4)
- Refusal tests assert the side-effect count is zero as well as the exception. (C5)
- A guard is scoped to the branch that consumes the value; it does not fire on a branch that never uses the value. (C6)
- Every guard path (e.g. a malformed-body path) is reached by at least one test. (C7)

## Incorrect

- A shelf-selector guard tested only with one unknown shelf code, never with an empty list.
- A refusal test asserting the exception while the guard runs after the first loan was already recorded.
- A renewal guard checking the fine cap on the email branch, which never reads the fine.
- A webhook handler whose malformed-body branch no test reaches.

## Correct

- A parametrized test naming absent, empty, wrong type, unknown member, over the title bound, and under and over the day bound, each asserting the refusal and zero ledger records; a test that the omitted (default) selection is refused and the default is not shared; all guards run before the first record.
- A fine guard placed only on the letter branch that prints the fine, with one test that the email branch ignores the fine and one that the letter branch refuses it with nothing sent.
- Look-alike: a pure function with no guard, tested by examples.

## LLM scan

- For each guard (a check that raises or refuses on bad input) a change adds or edits, list the value classes it
  must decide (C2) and find an assertion per class in the tests (C1, C3); report each class with none.
- Report guards placed after a side effect (write, send, enqueue, append to shared state) (C4) and refusal tests that
  assert only the exception, not that the side effect did not happen (C5).
- Report guards evaluated on a branch that never consumes the value they check (C6), and guard paths (malformed body,
  missing header) no test reaches (C7).
- Do not flag validation enforced by a schema model whose tests exercise the model, nor functions without a refusal path.
