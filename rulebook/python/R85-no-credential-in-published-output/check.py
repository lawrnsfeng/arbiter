"""R85: a credential-named value rendered into a log line, print, exception message, or stringified into a dict."""

import ast
import re

from rulekit import Hit, Module, classes, functions, local_nodes

RULE = "R85"
CREDENTIAL = re.compile(
    r"(^|_)(password|passwd|secret|api_?key|token|dsn|cookie|credentials?)$"
    r"|(^|_)(database|db|conn|connection)_?(url|uri|string|str)$"
)
# pagination and sync cursors are named `*_token` but grant nothing
CURSOR = re.compile(r"(page|next|prev|previous|continuation|cursor|sync|resume)_?token$")
LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}


def terminal(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    return expr.attr if isinstance(expr, ast.Attribute) else None


def credential(name: str | None) -> bool:
    return bool(name) and bool(CREDENTIAL.search(name.lower())) and not CURSOR.search(name.lower())


def leaks(expr: ast.expr | None, bound: dict[str, str]) -> str | None:
    """The credential `expr` renders as text, or None. bool()/len()/hash() and other calls hide it.

    `bound` maps locals already holding a rendered credential (`msg = f"...{dsn}"`) to that credential.
    """
    match expr:
        case ast.Name() if expr.id in bound:
            return bound[expr.id]
        case ast.Name() | ast.Attribute():
            name = terminal(expr)
            return name if credential(name) else None
        case ast.JoinedStr():
            values = [v.value for v in expr.values if isinstance(v, ast.FormattedValue)]
            return next((n for v in values if (n := leaks(v, bound))), None)
        case ast.BinOp(op=ast.Add() | ast.Mod()):
            return leaks(expr.left, bound) or leaks(expr.right, bound)
        case ast.Tuple():
            return next((n for e in expr.elts if (n := leaks(e, bound))), None)
        case ast.Dict():
            return next((n for v in expr.values if (n := leaks(v, bound))), None)
        case ast.Call(func=ast.Name(id="str" | "repr")) if expr.args:
            return leaks(expr.args[0], bound)
        case ast.Call(func=ast.Attribute(attr="format")):
            return next((n for a in [*expr.args, *(k.value for k in expr.keywords)] if (n := leaks(a, bound))), None)
    return None


def is_sink(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id == "print"
    if isinstance(func, ast.Attribute) and func.attr in LOG_METHODS:
        owner = terminal(func.value) or ""
        return "log" in owner.lower()
    return False


def scan(path: str, nodes: list[ast.AST]) -> list[Hit]:
    """One scope's statements, in source order, so message locals are bound before their sink."""
    hits: list[Hit] = []
    bound: dict[str, str] = {}
    for node in nodes:
        name = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value = node.value
            if not isinstance(value, ast.Name | ast.Attribute) and (cred := leaks(value, bound)):
                bound[node.targets[0].id] = cred
        elif isinstance(node, ast.Call) and is_sink(node):
            args = [*node.args, *(k.value for k in node.keywords)]
            name = next((n for a in args if (n := leaks(a, bound))), None)
            where = "a log line"
        elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            args = [*node.exc.args, *(k.value for k in node.exc.keywords)]
            name = next((n for a in args if (n := leaks(a, bound))), None)
            where = "an exception message"
        elif isinstance(node, ast.Dict):
            strs = [v for v in node.values if isinstance(v, ast.Call) and terminal(v.func) == "str"]
            name = next((n for v in strs if (n := leaks(v, bound))), None)
            where = "an emitted dict"
        if name:
            hits.append(Hit(path, node.lineno, f"R85 credential `{name}` is written into {where}: emit its parts"))
    return hits


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        scopes = [mod.tree, *functions(mod.tree), *classes(mod.tree)]
        for scope in scopes:
            hits += scan(mod.path, local_nodes(scope))  # type: ignore[arg-type]  # any node with a body
    return hits
