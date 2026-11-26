---
id: R13
title: Fail loudly at the source, not through a caller-side check function
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog "Replace Error Code with Exception" (https://refactoring.com/catalog/replaceErrorCodeWithException.html), Python glossary EAFP (https://docs.python.org/3/glossary.html#term-EAFP), subprocess.run check=True (https://docs.python.org/3/library/subprocess.html#subprocess.run)
---
## Rule

- The operation that can fail raises its own error at the source. (C1)
- It does not return a result that every caller must pass to a separate check function (such as
  `_raise_if_failed(result)`). (C2)
- Exception: only a deliberately tolerant probe may return a failure result instead of raising. (C3)

## Incorrect

- `receipt = courier.hand_over(parcel)` followed by `_raise_if_refused(receipt)` at two call sites.
- `status = await self.scan(code)` followed by `self._ensure_scanned(status)` inside a method.
- An operation returning an error code that callers compare by hand (model only).

## Correct

- `Courier.hand_over` raising `HandOverRefusedError` itself; a `try_hand_over` probe documented as tolerant returning a
  bool; a validation function called on caller input before an operation.
- Look-alikes: a check function called on an argument rather than on a call's result, a raising guard whose result
  is used, a library validator called as a module attribute.

## Detection

`check.py` collects every function whose body is only `if ...: raise` guards and that returns no value (a raising
check). It reports a statement calling such a check (by name, or as `self.` / `cls.` method, not imported from an
outside package) with a name bound by the immediately preceding statement to the result of a call (C1, C2).

## LLM scan

- Report operations that signal failure by returning `None`, `False`, an error code or a result object with an
  `ok` / `error` field that callers must inspect, when the operation is not a deliberately tolerant probe (C1, C2).
- Report inline caller-side checks repeated after every call of the same operation (`if result.returncode: raise`)
  (C2), including `subprocess.run` without `check=True` followed by a manual return-code check.
- Accept an operation that returns a failure value only when it is named and documented as a tolerant probe
  (`try_*`, `probe_*`, `is_*`) (C3); do not flag those, nor input validation of arguments before an operation.
