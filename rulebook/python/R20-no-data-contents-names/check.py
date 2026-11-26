"""R20: variables and attributes bound to the name `data` or `contents`."""

import ast

from rulekit import Hit, Module

RULE = "R20"
_NAMES = {"data", "contents"}


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for node in ast.walk(m.tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in _NAMES:
                kind, name = "variable", node.id
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and node.attr in _NAMES:
                kind, name = "attribute", node.attr
            elif isinstance(node, ast.ExceptHandler) and node.name in _NAMES:
                kind, name = "variable", node.name
            else:
                continue
            hits.append(
                Hit(m.path, node.lineno, f"{RULE} {kind} `{name}` says nothing about the value; name what it is")
            )
    return hits
