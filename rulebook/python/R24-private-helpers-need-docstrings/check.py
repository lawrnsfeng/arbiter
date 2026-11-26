"""R24: `_`-prefixed functions and methods without a docstring."""

import ast

from rulekit import Hit, Module, functions

RULE = "R24"


def _overload(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True for an `@overload` / `@typing.overload` stub."""
    for d in fn.decorator_list:
        if (isinstance(d, ast.Name) and d.id == "overload") or (isinstance(d, ast.Attribute) and d.attr == "overload"):
            return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for fn in functions(m.tree):
            name = fn.name
            if not name.startswith("_") or (name.startswith("__") and name.endswith("__")) or _overload(fn):
                continue
            if not (ast.get_docstring(fn) or "").strip():
                hits.append(Hit(m.path, fn.lineno, f"{RULE} private `{name}` has no docstring"))
    return hits
