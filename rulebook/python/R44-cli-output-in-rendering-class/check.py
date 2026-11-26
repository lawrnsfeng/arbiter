"""R44: a commands module whose private helpers all print: a renderer without a class."""

import ast

from rulekit import Hit, Module, local_nodes

RULE = "R44"
OUTPUT = {"print", "echo", "secho", "prompt", "confirm", "pause"}


def _is_command(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for d in fn.decorator_list:
        target = d.func if isinstance(d, ast.Call) else d
        if (isinstance(target, ast.Attribute) and target.attr == "command") or (
            isinstance(target, ast.Name) and target.id == "command"
        ):
            return True
    return fn.name.startswith("cmd_")


def _prints(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for n in local_nodes(fn):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            if name in OUTPUT:
                return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in modules:
        fns = [s for s in m.tree.body if isinstance(s, ast.FunctionDef | ast.AsyncFunctionDef)]
        private = [f for f in fns if f.name.startswith("_") and not f.name.startswith("__")]
        if len(private) < 2 or not any(map(_is_command, fns)) or not all(map(_prints, private)):
            continue
        for fn in private:
            msg = f"R44 `{fn.name}` is a loose output helper; group the rendering in a view class"
            hits.append(Hit(m.path, fn.lineno, msg))
    return hits
