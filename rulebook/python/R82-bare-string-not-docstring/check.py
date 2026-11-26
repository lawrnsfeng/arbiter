"""R82: a bare string literal at statement position that is not a module, class, or function docstring."""

import ast

from rulekit import Hit, Module

RULE = "R82"
DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def is_bare_string(stmt: ast.stmt) -> bool:
    return isinstance(stmt, ast.Expr) and (
        isinstance(stmt.value, ast.JoinedStr)
        or (isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
    )


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        for node in ast.walk(mod.tree):
            for field in ("body", "orelse", "finalbody"):
                block = getattr(node, field, None)
                if not isinstance(block, list):
                    continue
                for i, stmt in enumerate(block):
                    if not isinstance(stmt, ast.stmt) or not is_bare_string(stmt):
                        continue
                    docstring = isinstance(stmt.value, ast.Constant)  # an f-string is never a docstring
                    if docstring and i == 0 and field == "body" and isinstance(node, DOCSTRING_OWNERS):
                        continue
                    hits.append(
                        Hit(mod.path, stmt.lineno, "R82 bare string literal is not a docstring: no tool reads it")
                    )
    return hits
