"""R66: a loop inside a command function that calls something per item, one item at a time."""

import ast

from rulekit import Hit, Module, functions, local_nodes

RULE = "R66"
QUIET = {
    "print", "echo", "secho", "append", "add", "extend", "update", "write", "len", "str", "repr", "format", "join",
    "sorted", "debug", "info", "warning", "warn", "error", "exception", "critical", "log",
}  # fmt: skip


def is_command(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if fn.name.startswith("cmd_"):
        return True
    for deco in fn.decorator_list:
        target = deco.func if isinstance(deco, ast.Call) else deco
        if (target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")) == "command":
            return True
    return False


def loop_names(target: ast.expr) -> set[str]:
    return {n.id for n in ast.walk(target) if isinstance(n, ast.Name)}


def statement_call(stmt: ast.stmt) -> ast.Call | None:
    value = stmt.value if isinstance(stmt, ast.Expr | ast.Assign | ast.AnnAssign | ast.AugAssign) else None
    if isinstance(value, ast.Await):
        value = value.value
    return value if isinstance(value, ast.Call) else None


def rebound(loop: ast.For | ast.AsyncFor) -> set[str]:
    """Names the loop body rebinds: a call reading one of them depends on the previous iteration."""
    return {
        n.id for stmt in loop.body for n in ast.walk(stmt) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
    }


def per_item_call(loop: ast.For | ast.AsyncFor) -> bool:
    names = loop_names(loop.target)
    carried = rebound(loop) - names
    for stmt in loop.body:
        call = statement_call(stmt)
        if call is None:
            continue
        callee = call.func.id if isinstance(call.func, ast.Name) else getattr(call.func, "attr", "")
        args = [*call.args, *(kw.value for kw in call.keywords)]
        reads = {n.id for a in args for n in ast.walk(a) if isinstance(n, ast.Name)}
        if callee in QUIET or reads & carried:
            continue
        if any(isinstance(a, ast.Name) and a.id in names for a in args):
            return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for fn in functions(m.tree):
            if not is_command(fn):
                continue
            for node in local_nodes(fn):
                if isinstance(node, ast.For | ast.AsyncFor) and per_item_call(node):
                    message = f"{RULE} command `{fn.name}` runs per-item IO in a sequential loop: use the task tree"
                    hits.append(Hit(m.path, node.lineno, message))
    return hits
