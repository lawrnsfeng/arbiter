"""R39: templates flat at module level, Messages without its Msg alias, or labels and templates mixed."""

import ast
from pathlib import Path

from rulekit import Hit, Module

RULE = "R39"


def _value(stmt: ast.stmt) -> tuple[str, ast.expr] | None:
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id, stmt.value
    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None and isinstance(stmt.target, ast.Name):
        return stmt.target.id, stmt.value
    return None


def _is_template(value: ast.expr) -> bool:
    f = value.func if isinstance(value, ast.Call) else None
    return (isinstance(f, ast.Name) and f.id == "Template") or (isinstance(f, ast.Attribute) and f.attr == "Template")


def _is_text(value: ast.expr) -> bool:
    return isinstance(value, ast.Constant) and isinstance(value.value, str)


def _is_messages_module(m: Module) -> bool:
    """Named messages.py, or defining the top-level `Messages` / `Labels` classes a messages module holds."""
    names = {s.name for s in m.tree.body if isinstance(s, ast.ClassDef)}
    return Path(m.path).name == "messages.py" or bool(names & {"Messages", "Labels"})


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in filter(_is_messages_module, modules):
        aliased = False
        for stmt in m.tree.body:
            pair = _value(stmt)
            if pair and isinstance(pair[1], ast.Name) and pair[1].id == "Messages" and pair[0] == "Msg":
                aliased = True
            elif pair and _is_template(pair[1]):
                hits.append(Hit(m.path, stmt.lineno, f"R39 template `{pair[0]}` is a flat module constant"))
        for cls in (s for s in m.tree.body if isinstance(s, ast.ClassDef)):
            if cls.name == "Messages" and not aliased:
                hits.append(Hit(m.path, cls.lineno, "R39 `Messages` has no `Msg = Messages` alias"))
            wrong, kind = {"Messages": (_is_text, "plain label"), "Labels": (_is_template, "template")}.get(
                cls.name, (lambda _: False, "")
            )
            pairs = (pair for stmt in cls.body if (pair := _value(stmt)))
            hits.extend(Hit(m.path, v.lineno, f"R39 {kind} `{n}` is in `{cls.name}`") for n, v in pairs if wrong(v))
    return hits
