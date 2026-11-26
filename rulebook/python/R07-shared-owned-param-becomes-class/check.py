"""R7: every function of a module, or every method of a class, takes a parameter of the same project-owned class."""

import ast
from collections import Counter
from pathlib import Path

from rulekit import Hit, Module, classes, foreign_imports, params_of, project_tops

RULE = "R7"
type Function = ast.FunctionDef | ast.AsyncFunctionDef


def type_name(ann: ast.expr | None) -> str | None:
    """`C`, `"C"` or `C | None` -> `C`."""
    match ann:
        case ast.Name(id=n) | ast.Constant(value=str() as n):
            return n
        case ast.BinOp(op=ast.BitOr(), left=left, right=ast.Constant(value=None)):
            return type_name(left)
    return None


def shared(fns: list[Function], owned: set[str], skip_first: bool) -> str | None:
    """The project class every function takes as a parameter, if there is one (position is irrelevant)."""
    if len(fns) < 2:
        return None
    common: set[str] | None = None
    for fn in fns:
        params = params_of(fn)[1:] if skip_first else params_of(fn)
        types = {t for p in params if (t := type_name(p.annotation)) in owned}
        common = types if common is None else common & types
    return min(common) if common else None


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    defined = {c.name for m in modules for c in classes(m.tree)}
    tops = project_tops(modules)
    method_names = Counter(
        f.name
        for m in modules
        for c in classes(m.tree)
        for f in c.body
        if isinstance(f, ast.FunctionDef | ast.AsyncFunctionDef)
    )
    for m in modules:
        name = Path(m.path).name
        if name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py":
            continue  # tests receive fixtures by parameter; that is not a missing class
        owned = defined - foreign_imports(m.tree, tops)
        fns = [
            f
            for f in m.tree.body
            if isinstance(f, ast.FunctionDef | ast.AsyncFunctionDef) and not f.name.startswith("test_")
        ]
        if cls := shared(fns, owned, skip_first=False):
            out += [
                Hit(m.path, f.lineno, f"{RULE} every function here takes a `{cls}`: make `{f.name}` its method")
                for f in fns
            ]
        for c in classes(m.tree):
            methods = [
                f
                for f in c.body
                if isinstance(f, ast.FunctionDef | ast.AsyncFunctionDef)
                and not f.name.startswith("__")
                and method_names[f.name] == 1  # a name other classes define too is an overridden or framework contract
                and not any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in f.decorator_list)
            ]
            if cls := shared(methods, owned - {c.name}, skip_first=True):
                out += [
                    Hit(m.path, f.lineno, f"{RULE} every method of `{c.name}` takes a `{cls}`: move `{f.name}` onto it")
                    for f in methods
                ]
    return out
