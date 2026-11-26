"""R12: the same chained-call one-liner written twice or more in a module."""

import ast
from collections import defaultdict

from rulekit import Hit, Module

RULE = "R12"


def chain_length(node: ast.AST) -> int:
    """Calls in a method chain such as `name.strip("/").replace("/", "-")` (2)."""
    n = 0
    while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        n += 1
        node = node.func.value
    return n


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        inner = {
            id(n.value) for n in ast.walk(m.tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Call)
        }  # a call that is itself the receiver of a longer chain
        seen: dict[str, list[ast.Call]] = defaultdict(list)
        for n in ast.walk(m.tree):
            if isinstance(n, ast.Call) and id(n) not in inner and chain_length(n) >= 2:
                seen[ast.dump(n)].append(n)
        for calls in seen.values():
            if len(calls) > 1:
                first = min(c.lineno for c in calls)
                out += [
                    Hit(
                        m.path,
                        c.lineno,
                        f"{RULE} `{ast.unparse(c)[:60]}` repeats (first at line {first}): extract a helper",
                    )
                    for c in calls
                ]
    return out
