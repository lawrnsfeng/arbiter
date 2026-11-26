"""R33: a private module function only forwards to a project class's constructor with a pre-filled leading arg."""

import ast

from rulekit import Hit, Module, classes, params_of

RULE = "R33"


def _names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def check(modules: list[Module]) -> list[Hit]:
    defined = {c.name for m in modules for c in classes(m.tree)}
    hits: list[Hit] = []
    for m in modules:
        for fn in m.tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or not fn.name.startswith("_"):
                continue
            if fn.name.startswith("__"):
                continue
            body = fn.body[1:] if ast.get_docstring(fn) is not None else fn.body
            if len(body) != 1 or not isinstance(body[0], ast.Return) or not isinstance(body[0].value, ast.Call):
                continue
            call = body[0].value
            func = call.func.value if isinstance(call.func, ast.Attribute) else call.func
            if not (isinstance(func, ast.Name) and func.id in defined) or not call.args:
                continue
            params = {p.arg for p in params_of(fn)}
            if not _names(call.args[0]) & params and _names(call) & params:
                msg = f"R33 `{fn.name}` pre-fills `{func.id}`'s leading argument; make it a `from_*` classmethod"
                hits.append(Hit(m.path, fn.lineno, msg))
    return hits
