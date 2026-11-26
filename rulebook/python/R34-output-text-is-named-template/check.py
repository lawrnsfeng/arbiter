"""R34: interpolated text built at an output call site instead of a keyword-invoked messages template."""

import ast

from rulekit import Hit, Module

RULE = "R34"
OUTPUT = {"print", "echo", "secho"}
MESSAGES = {"Msg", "Messages"}


def _is_output(call: ast.Call) -> bool:
    f = call.func
    return (isinstance(f, ast.Name) and f.id in OUTPUT) or (
        isinstance(f, ast.Attribute) and f.attr in OUTPUT - {"print"}
    )


def _inline(arg: ast.expr) -> str | None:
    if isinstance(arg, ast.JoinedStr) and any(isinstance(v, ast.FormattedValue) for v in arg.values):
        return "an inline f-string"
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "format":
        return "`.format(...)`"
    if (
        isinstance(arg, ast.BinOp)
        and isinstance(arg.op, ast.Mod)
        and isinstance(arg.left, ast.Constant | ast.JoinedStr)
    ):
        return "`%`-interpolation"
    return None


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in modules:
        for call in (n for n in ast.walk(m.tree) if isinstance(n, ast.Call)):
            f = call.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in MESSAGES and call.args:
                msg = f"R34 template `{f.value.id}.{f.attr}` called with positional arguments; pass keywords"
                hits.append(Hit(m.path, call.lineno, msg))
            if _is_output(call) and call.args and (what := _inline(call.args[0])):
                hits.append(Hit(m.path, call.lineno, f"R34 output built with {what}; use a named messages template"))
    return hits
