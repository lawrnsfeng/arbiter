---
id: R74
title: Dynamic attribute access (`getattr`/`hasattr`) needs a structural reason
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/functions.html#getattr, https://docs.python.org/3/reference/datamodel.html#object.__getattr__, https://peps.python.org/pep-0634/, Google Python Style Guide 2.19 (Power Features), owner convention
---
## Rule

- `getattr`/`hasattr` on your own class (stringly-typed dispatch the type checker cannot see, which breaks silently on renames) is a violation. (C1)
- Every `getattr` and `hasattr` is questionable and needs a structural reason. (C2)
- Allowed reason (a): external or validated names: database column maps, log-record extras read with a default, proxy delegation through `__getattr__`. (C3)
- Allowed reason (b): generic frameworks (e.g. plugin registries). (C4)
- Dispatch over a closed set on your own type is a `match` naming the members. (C5)
- Building method names from enum values or names so that method names must mirror enum values is a violation; on a dataclass a method name can collide with a field name and break the class at definition time. (C6)

## Incorrect

- `getattr(self, f"bake_{stage.value}")` in a dataclass: method names mirror enum values.
- `if hasattr(self, "_oven"):`: lazy-state probe on the own instance.
- `getattr(cls, name.upper())` in a classmethod.
- `getattr(type(self), kind)`: the same through the own type.
- `getattr(self.__class__, ...)` and `hasattr(Loaf, ...)` inside `Loaf`'s own methods: the own class reached by `__class__` or by name.
- (LLM) `getattr(oven, mode)()` dispatching over a closed set of another project class's methods.

## Correct

- `match stage: case Stage.PROOF: self.proof() ...` with no name coupling.
- Look-alikes: `getattr(record, "trace_id", None)` at a logging boundary, `getattr(self._inner, name)` inside `__getattr__` proxy delegation, `getattr(plugin, "register", None)` in a plugin loader.

## Detection

Reports every `getattr(...)`/`hasattr(...)` call whose object argument is the own instance or class: `self`, `cls`, `type(...)` or `....__class__` of those, or the name of the class whose body defines the method, except inside `__getattr__`, `__getattribute__`, `__setattr__`, `__delattr__` and `__dir__` (proxy delegation). Covers C1 and C6 (the enum-mirroring case is a `getattr` on `self`).

## LLM scan

- Review every other `getattr`/`hasattr` (C2): keep it only for external/validated names (C3) or generic frameworks (C4); flag dispatch over a closed set on a project type, which must be a `match` naming the members (C5).
- Flag method names built from enum values or names on any project type (C6).
- Do not flag `getattr` with a default on objects from outside the project (log records, third-party responses, module objects in plugin loaders).
