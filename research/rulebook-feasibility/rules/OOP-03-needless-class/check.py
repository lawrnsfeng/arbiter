"""OOP-03: a class that should be a function. One hit per such class."""

import ast

from rulekit import Hit, Module

RULE = "OOP-03"


def _stores_only(init: ast.FunctionDef) -> bool:
    body = [s for s in init.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    return all(
        isinstance(s, ast.Assign | ast.AnnAssign)
        and all(isinstance(t, ast.Attribute) for t in (s.targets if isinstance(s, ast.Assign) else [s.target]))
        for s in body
    )


def hits(tree: ast.AST) -> list[tuple[int, str]]:
    out = []
    for c in ast.walk(tree):
        if not isinstance(c, ast.ClassDef) or c.bases or c.keywords or c.decorator_list:
            continue
        defs = [d for d in c.body if isinstance(d, ast.FunctionDef)]
        init = next((d for d in defs if d.name == "__init__"), None)
        public = [d for d in defs if not d.name.startswith("_")]
        if init and _stores_only(init) and len(public) == 1 and len(defs) == 2:
            out.append((c.lineno, c.name))
    return out


def check(modules: list[Module]) -> list[Hit]:
    return [
        Hit(m.path, line, f"{RULE} `{name}` stores its arguments and has one public method: make it a function")
        for m in modules
        for line, name in hits(m.tree)
    ]
