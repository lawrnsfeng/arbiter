"""R71: calls sharing a three-name argument prefix and varying on an enumerated tail or callee-name suffix."""

import ast

from rulekit import Hit, Module

RULE = "R71"
PREFIX = 3


def dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and (head := dotted(node.value)):
        return f"{head}.{node.attr}"
    return None


def stem(callee: str) -> str:
    head, _, last = callee.rpartition(".")
    base, sep, _ = last.rpartition("_")
    return f"{head}.{base}" if sep and base else callee


def tail(call: ast.Call) -> dict[str, ast.expr]:
    slots = {str(i): a for i, a in enumerate(call.args[PREFIX:], PREFIX)}
    slots.update({kw.arg: kw.value for kw in call.keywords if kw.arg})
    return slots


def enumerated(node: ast.expr | None) -> bool:
    """A flag-like value: a string, bool or None literal, or a dotted name such as an enum member; numbers are data."""
    if isinstance(node, ast.Constant):
        return node.value is None or isinstance(node.value, str | bool)
    return isinstance(node, ast.Attribute) and dotted(node) is not None


def enum_varies(calls: list[tuple[str, ast.Call]]) -> bool:
    tails = [tail(c) for _, c in calls]
    for slot in set().union(*tails):
        values = [t.get(slot) for t in tails]
        if all(enumerated(v) for v in values) and len({ast.dump(v) for v in values if v}) > 1:
            return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        groups: dict[tuple[str, ...], list[tuple[str, ast.Call]]] = {}
        for node in ast.walk(m.tree):
            if not isinstance(node, ast.Call) or len(node.args) < PREFIX or (callee := dotted(node.func)) is None:
                continue
            prefix = [dotted(a) for a in node.args[:PREFIX]]
            if all(prefix):
                groups.setdefault((stem(callee), *map(str, prefix)), []).append((callee, node))
        for calls in groups.values():
            if len(calls) < 2:
                continue
            if len({name for name, _ in calls}) > 1 or enum_varies(calls):
                for name, call in calls:
                    message = f"{RULE} `{name}` repeats a shared argument prefix: dispatch on the enum in one class"
                    hits.append(Hit(m.path, call.lineno, message))
    return hits
