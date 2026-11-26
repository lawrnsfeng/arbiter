"""R37: a method chain is half-wrapped, or fully split although its one-line form fits the line limit."""

import ast

from rulekit import Hit, Module

RULE = "R37"
LIMIT = 120  # the project's line-length limit (ruff `line-length`)
STATEMENTS = (ast.Expr, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Return)


def _segments(top: ast.expr) -> tuple[list[ast.Attribute], int]:
    """Attributes after the head call (`Builder(x)` or `Model.objects.filter(...)`), in source order, and how many of
    them are called."""
    spine: list[tuple[ast.Attribute, bool]] = []
    node, called = top, False
    while isinstance(node, ast.Call | ast.Attribute):
        if isinstance(node, ast.Call):
            node, called = node.func, True
        else:
            spine.append((node, called))
            node, called = node.value, False
    spine.reverse()
    first = next((i for i, (a, _) in enumerate(spine) if isinstance(a.value, ast.Call)), len(spine))
    segs = spine[first:]
    return [a for a, _ in segs], sum(1 for _, c in segs if c)


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in modules:
        inner: set[int] = set()
        stmt_of: dict[int, ast.stmt] = {}
        for n in ast.walk(m.tree):
            if isinstance(n, ast.Call):
                inner.add(id(n.func))
            elif isinstance(n, ast.Attribute):
                inner.add(id(n.value))
            if isinstance(n, STATEMENTS) and n.value is not None:
                stmt_of[id(n.value)] = n
        for top in ast.walk(m.tree):
            if not isinstance(top, ast.Call | ast.Attribute) or id(top) in inner:
                continue
            segs, calls = _segments(top)
            if len(segs) < 2 or calls < 2:
                continue
            breaks = [s.end_lineno > s.value.end_lineno for s in segs]
            if any(breaks) and not all(breaks):
                hits.append(Hit(m.path, top.lineno, "R37 method chain is half-wrapped; one line or one call per line"))
            elif all(breaks) and (stmt := stmt_of.get(id(top))):
                width = stmt.col_offset + len(ast.unparse(stmt))
                if width <= LIMIT:
                    msg = f"R37 method chain is split but fits one line ({width} <= {LIMIT} columns)"
                    hits.append(Hit(m.path, top.lineno, msg))
    return hits
