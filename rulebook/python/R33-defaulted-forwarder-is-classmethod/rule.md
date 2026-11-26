---
id: R33
title: A private wrapper that pre-fills a constructor's leading argument is a from_* classmethod
tier: ast
severity: should-fix
status: ok
refs: https://refactoring.com/catalog/replaceConstructorWithFactoryFunction.html, https://refactoring.com/catalog/moveFunction.html, https://docs.python.org/3/library/functions.html#classmethod
---
## Rule

- A private module-level function whose whole body is a single call to one constructor or classmethod of a class,
  pre-filling a default leading argument, is not allowed as a free function. (C1)
- It becomes a `from_*` `@classmethod` on that class, placed next to the constructor it forwards to. (C2)

## Incorrect

- A private function forwarding to a classmethod with a configured origin pre-filled and a keyword-only flag passed on.
- A private function calling the constructor with a module constant pre-filled and two parameters passed on.
- An async private function pre-filling the constructor from a configuration attribute chain.

## Correct

- The configured default lives in a `from_hub` classmethod beside the `from_origin` constructor it forwards to.
- Look-alikes: a public factory, a private pass-through without a pre-filled argument, a wrapper around a third-party
  class, a wrapper whose leading argument is derived from its parameters, and a multi-statement helper.

## Detection

Reports a module-level function named `_x` (not dunder) whose body, docstring aside, is one `return Cls(...)` or
`return Cls.method(...)` where `Cls` is a class defined in the scanned modules, the first positional argument uses
none of the function's parameters (the pre-filled default) and at least one parameter is passed through (C1, C2).
