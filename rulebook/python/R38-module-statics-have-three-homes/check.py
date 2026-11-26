"""R38: a constants module holds a flat wall of prefix-named constants instead of category classes."""

import ast
import re
from pathlib import Path

from rulekit import Hit, Module

RULE = "R38"
CONSTANT = re.compile(r"^([A-Z][A-Z0-9]*)_[A-Z0-9_]+$")
WALL = 3  # two constants sharing a prefix are often a cross-cutting pair (C7), e.g. two remote names


def _constant(stmt: ast.stmt) -> str | None:
    target = stmt.targets[0] if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 else None
    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        target = stmt.target
    return target.id if isinstance(target, ast.Name) and target.id.isupper() else None


def _only_data(cls: ast.ClassDef) -> bool:
    return all(isinstance(s, ast.Assign | ast.AnnAssign | ast.Expr | ast.Pass) for s in cls.body)


def _is_constants_module(m: Module) -> bool:
    """Named constants.py, or holding nothing but imports, constants and data-only classes."""
    if Path(m.path).name == "constants.py":
        return True
    body = m.tree.body[1:] if ast.get_docstring(m.tree) is not None else m.tree.body
    allowed = (ast.Import, ast.ImportFrom)
    return any(_constant(s) for s in body) and all(
        isinstance(s, allowed) or _constant(s) or (isinstance(s, ast.ClassDef) and _only_data(s)) for s in body
    )


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in filter(_is_constants_module, modules):
        groups: dict[str, list[ast.stmt]] = {}
        for stmt in m.tree.body:
            if (name := _constant(stmt)) and (match := CONSTANT.match(name)):
                groups.setdefault(match[1], []).append(stmt)
        for prefix, stmts in groups.items():
            if len(stmts) < WALL:
                continue
            for stmt in stmts:
                msg = f"R38 `{_constant(stmt)}` is one of a flat `{prefix}_*` wall; group them in a category class"
                hits.append(Hit(m.path, stmt.lineno, msg))
    return hits
