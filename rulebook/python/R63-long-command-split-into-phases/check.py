"""R63: a command function (`cmd_*` or `@...command`) whose body runs past 30 lines."""

import ast

from rulekit import Hit, Module, functions

RULE = "R63"
LIMIT = 30


def is_command(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if fn.name.startswith("cmd_"):
        return True
    for deco in fn.decorator_list:
        target = deco.func if isinstance(deco, ast.Call) else deco
        if (target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")) == "command":
            return True
    return False


LITERALS = (ast.Dict, ast.List, ast.Tuple, ast.Set, ast.Constant, ast.JoinedStr)


def body_lines(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Source lines the body spans, docstring excluded; a multi-line literal counts as its first line only."""
    body = fn.body
    if (
        isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if not body:
        return 0
    lines = set(range(body[0].lineno, (body[-1].end_lineno or body[-1].lineno) + 1))
    for node in (n for stmt in body for n in ast.walk(stmt)):
        if isinstance(node, LITERALS) and node.end_lineno and node.end_lineno > node.lineno:
            lines.difference_update(range(node.lineno + 1, node.end_lineno + 1))
    return len(lines)


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for fn in functions(m.tree):
            if is_command(fn) and (n := body_lines(fn)) > LIMIT:
                message = f"{RULE} command `{fn.name}` body is {n} lines: move it onto a record class with phases"
                hits.append(Hit(m.path, fn.lineno, message))
    return hits
