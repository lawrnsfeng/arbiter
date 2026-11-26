"""R13: a result handed straight to a caller-side check function that only raises."""

import ast
import builtins
import itertools

from rulekit import Hit, Module, foreign_imports, functions, project_tops

RULE = "R13"
BUILTINS = set(dir(builtins))
type Function = ast.FunctionDef | ast.AsyncFunctionDef


def raising_check(fn: Function) -> bool:
    """Body is only `if ...: raise` guards (after an optional docstring) and returns no value."""
    body = fn.body[1:] if ast.get_docstring(fn) is not None else fn.body
    return (
        bool(body)
        and all(isinstance(s, ast.If) and any(isinstance(n, ast.Raise) for n in ast.walk(s)) for s in body)
        and not any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(fn))
    )


def callee(call: ast.Call) -> str:
    """`check(...)` or `self.check(...)` / `cls.check(...)`; a module attribute (`lib.validate`) is not ours."""
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in {"self", "cls"}:
        return f.attr
    return ""


def operation(value: ast.expr) -> bool:
    """A call whose receiver chain does not start at a builtin (`set(...).union(...)` builds a value, not a result)."""
    node = value.value if isinstance(value, ast.Await) else value
    while isinstance(node, ast.Call | ast.Attribute):
        node = node.func if isinstance(node, ast.Call) else node.value
        if isinstance(node, ast.Name) and node.id in BUILTINS:
            return False
    return isinstance(value, ast.Call | ast.Await)


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    every = {fn.name for m in modules for fn in functions(m.tree) if raising_check(fn)}
    tops = project_tops(modules)
    for m in modules:
        checks = every - foreign_imports(m.tree, tops)
        for node in ast.walk(m.tree):
            for body in (getattr(node, f, None) for f in ("body", "orelse", "finalbody")):
                if not isinstance(body, list):
                    continue
                for prev, stmt in itertools.pairwise(body):
                    if not (
                        isinstance(prev, ast.Assign)
                        and operation(prev.value)
                        and isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Call)
                        and callee(stmt.value) in checks
                    ):
                        continue
                    bound = {t.id for t in prev.targets if isinstance(t, ast.Name)}
                    if any(isinstance(a, ast.Name) and a.id in bound for a in stmt.value.args):
                        name = callee(stmt.value)
                        out.append(
                            Hit(
                                m.path,
                                stmt.lineno,
                                f"{RULE} result checked by `{name}` at the call site: raise at the source",
                            )
                        )
    return out
