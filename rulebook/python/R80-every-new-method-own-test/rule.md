---
id: R80
title: Every new method gets its own test, against a stand-in when it calls another class
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs unittest.mock (assert_called_with, autospec), Fowler "Mocks Aren't Stubs", Fowler "UnitTest", Google Testing Blog "Testing on the Toilet: Don't Overuse Mocks", pytest docs
---
## Rule

- Every method a change adds has its own test. (C1)
- A method added to a dataclass, value object, or any behaviour-bearing class is unit-tested in that class's own test module; this obligation is absolute. (C2)
- That test constructs the object directly, calls the method directly, and asserts the returned value, the raised error, or the mutated field. (C3)
- `@dataclass` grants no exemption: a dataclass with a method holds domain logic and needs a test. (C4)
- The obligation covers properties, classmethods, `__post_init__`, and dunders the change adds. (C5)
- A method whose body calls another class is tested with that collaborator replaced by a mock, stub, or fake, one per boundary. (C6)
- Such a test asserts behaviour the method owns: the call made and its arguments, the branch taken on the collaborator's answer, the error mapped, the value returned. (C7)
- A test that lets the real collaborator run (an integration test under a unit test's name) does not satisfy C6. (C8)
- A test whose only assertion is that a mock was called (e.g. `assert_called_once()`) does not satisfy C6. (C9)
- A boundary that truly cannot be faked is stated in the test's docstring with what faking it would take. (C10)
- A test references the method's qualified name (`Class.method`) so a scan can count it. (C11)
- Methods a scan cannot see (dynamic `__getattr__` dispatch, names reachable only through a decorator) are named in the report; silence is not clean. (C12)

## Incorrect

- A test whose only assertion is `bank.reserve.assert_called_once()`.
- A test whose only assertion is `assert bank.reserve.called`.
- A unittest test whose only assertion is `self.assertEqual(bank.reserve.call_count, 1)`.
- A unittest test whose only assertion is `self.assertTrue(bank.reserve.called)`.
- A frozen dataclass gaining a method with no test anywhere (model only).
- A unit test that builds the real HTTP-backed collaborator and lets it hit the network (model only).

## Correct

- A test constructing a locker slot directly and asserting the method's result at its boundary.
- Tests driving the desk through a stub that answers from a fixed list, asserting the branch taken and the returned slot.
- Look-alikes: `assert_called_once_with(...)` beside a return-value assertion; `assert not m.called` and `assertEqual(m.call_count, 0)` asserting the branch where nothing is reserved.

## Detection

`check.py` reports a test function (`test*`) whose every assertion only says a mock was called and nothing else:
`.assert_called()`, `.assert_called_once()`, `.assert_awaited()`, `.assert_awaited_once()`, `assert m.called`,
`assert m.called is True`, `assert` on any `call_count`/`await_count` comparison except one saying "not called"
(`== 0`, `<= 0`, `< 1`, read in either operand order, so `1 > m.call_count` counts as not called), so `== 1`, `> 0`
and `0 < m.call_count` are reported, or a unittest `assertTrue`/`assertEqual`/`assertGreater`/`assertIs` on a
`called`/`call_count` value, with no other assertion and no `pytest.raises` (C9). `assert not m.called`, `is False`,
`is not True` and the not-called comparisons assert the branch taken (C7) and count as real assertions.

## LLM scan

- For each method, property, classmethod, `__post_init__` or dunder a change adds (C1, C5), look for a test that
  references `Class.method` (C11), constructs the object directly and asserts a return value, raised error, or mutated
  field (C2, C3); a dataclass is not exempt (C4). Report every one without such a test.
- For each added method whose body calls another class, check the test replaces that collaborator with a mock, stub or
  fake (C6) and asserts the call arguments, branch, mapped error, or return value (C7). Report tests that build the
  real collaborator (C8). A boundary left real must be justified in the test's docstring (C10).
- Name the methods you cannot resolve statically (`__getattr__` dispatch, decorator-registered names) in the report (C12).
- Do not flag tests that assert call arguments (`assert_called_once_with`) or outcomes alongside a called-check.
