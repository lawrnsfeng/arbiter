"""R58: a loose module-level rendering function (`render_*`) instead of a construct from the rendering taxonomy."""

import ast
import re

from rulekit import Hit, Module

RULE = "R58"
RENDER_NAME = re.compile(
    r"""
    ^_*render             # render, _render, render_x, ...
    (?:_|$)               # as a whole word, not renderer or rendering
    """,
    re.VERBOSE,
)


CLI_DECORATORS = {"command", "group", "callback"}


def _text(node: ast.expr) -> bool:
    """A string literal or an f-string: an operand that makes `+` / `%` build text."""
    return isinstance(node, ast.JoinedStr) or (isinstance(node, ast.Constant) and isinstance(node.value, str))


def _hands_over(stmt: ast.stmt) -> bool:
    """The statement calls a renderer (`.render(...)`, a `from_*` constructor, a `*Renderer`/`*Template` class) and
    assembles no text itself (no f-string, `%`/`+` on a string or f-string, `.join` or `.format`)."""
    calls: list[ast.Call] = [n for n in ast.walk(stmt) if isinstance(n, ast.Call)]
    names: list[str] = [
        c.func.attr if isinstance(c.func, ast.Attribute) else c.func.id if isinstance(c.func, ast.Name) else ""
        for c in calls
    ]
    renders: bool = any(n == "render" or n.startswith("from_") or n.endswith(("Renderer", "Template")) for n in names)
    assembles: bool = any(n in {"join", "format"} for n in names) or any(
        isinstance(n, ast.JoinedStr)
        or (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod | ast.Add) and (_text(n.left) or _text(n.right)))
        for n in ast.walk(stmt)
    )  # `margin + 20` is arithmetic, not text building
    return renders and not assembles


def _cli_entry(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """A click/typer command (`@click.command()`, `@app.command()`) whose body is one statement handing over to a
    renderer: an entry point, not a rendering function. A command that renders inline is still reported."""
    body: list[ast.stmt] = fn.body[1:] if ast.get_docstring(fn) is not None else fn.body
    if len(body) != 1 or not isinstance(body[0], ast.Expr | ast.Return) or not _hands_over(body[0]):
        return False
    for d in fn.decorator_list:
        target: ast.expr = d.func if isinstance(d, ast.Call) else d
        name: str = (
            target.attr if isinstance(target, ast.Attribute) else target.id if isinstance(target, ast.Name) else ""
        )
        if name in CLI_DECORATORS:
            return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    return [
        Hit(
            m.path,
            node.lineno,
            f"R58 loose rendering function `{node.name}`: use a template, renderer, str subclass or property",
        )
        for m in modules
        for node in m.tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and RENDER_NAME.match(node.name)
        and not _cli_entry(node)
    ]
