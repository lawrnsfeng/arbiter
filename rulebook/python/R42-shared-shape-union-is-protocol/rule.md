---
id: R42
title: A union of types used through their shared shape is a Protocol, not a base class
tier: ast+semantic
severity: should-fix
status: ok
refs: https://peps.python.org/pep-0544/, https://typing.python.org/en/latest/spec/protocol.html, https://docs.python.org/3/library/typing.html#typing.Protocol
---
## Rule

- A function parameter typed as a union of types, where the function touches only members those types share, is typed
  with a named `typing.Protocol` instead of the union. (C1)
- The Protocol lives in the package's type-definitions module (`typedefs.py`). (C2)
- Read-only members of the Protocol are declared as `@property`. (C3)
- No common base class is introduced for this: it couples unrelated hierarchies. (C4)

## Incorrect

- A parameter typed `GaugeA | GaugeB` reading only their shared attribute and method.
- The union as the value type of a `dict` the function loops over.
- `typing.Union` of three project classes reading one shared attribute.
- A base class introduced only so unrelated classes share a parameter type (model only).

## Correct

- A `Protocol` with `@property` members in the type-definitions module, used as the parameter type.
- Look-alikes: a union narrowed with `isinstance`, an optional scalar, a union with a class the codebase does not define.

## Detection

Reports a parameter whose annotation contains a union (`A | B` or `Union[A, B]`, `None` ignored) of two or more
classes all defined in the scanned modules, when the function body never names any of those classes (no `isinstance`,
`match` or constructor narrowing) and, when the union is the whole annotation, every attribute it reads directly from
the parameter is defined on every member (C1). For a union nested in a container (`dict[str, A | B]`), the attribute
check is skipped.

## LLM scan

- Flag Protocols that are defined outside the type-definitions module (C2), and Protocols declaring read-only members
  as plain annotated attributes instead of `@property` (C3).
- Flag a base class introduced, or a base list extended, only so unrelated classes can share a parameter type (C4).
- Flag unions behind type aliases used the same way (C1).
- Do not flag unions the function narrows by type, unions with `None` or scalars, or genuine class hierarchies.
