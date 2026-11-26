"""R72: a def nested in a function, unless it has a docstring, captures an enclosing name, and is handed out."""

import ast

from rulekit import Hit, Module, functions, local_nodes, params_of

RULE = "R72"
type Function = ast.FunctionDef | ast.AsyncFunctionDef


def bound_names(fn: Function) -> set[str]:
    names = {a.arg for a in params_of(fn)}
    for node in local_nodes(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
    return names


def free_names(fn: Function) -> set[str]:
    used = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    used |= {name for n in ast.walk(fn) if isinstance(n, ast.Nonlocal) for name in n.names}
    return used - bound_names(fn)


CACHES = {"cache", "lru_cache", "cached_property"}


def decorator_name(deco: ast.expr) -> str:
    target = deco.func if isinstance(deco, ast.Call) else deco
    return target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")


def handed_out(inner: Function, outer: Function) -> bool:
    """Returned by name, passed by name as an argument, or registered by a call/attribute decorator (not a cache)."""
    if any(isinstance(d, ast.Call | ast.Attribute) and decorator_name(d) not in CACHES for d in inner.decorator_list):
        return True
    for node in local_nodes(outer):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Name) and node.value.id == inner.name:
            return True
        if isinstance(node, ast.Call):
            args = [*node.args, *(kw.value for kw in node.keywords)]
            if any(isinstance(a, ast.Name) and a.id == inner.name for a in args):
                return True
    return False


def uses(inner: Function, outer: Function) -> int:
    """Every read of the nested function's name in the enclosing body: calls, arguments, returns, assignments."""
    return sum(
        1
        for node in local_nodes(outer)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == inner.name
    )


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for outer in functions(m.tree):
            enclosing = bound_names(outer)
            for inner in local_nodes(outer):
                if not isinstance(inner, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                failed = []
                if ast.get_docstring(inner) is None:
                    failed.append("has no docstring stating the capture")
                captures = free_names(inner) & enclosing
                out = handed_out(inner, outer)
                if not captures:
                    failed.append("captures nothing from the enclosing scope")
                if not out:
                    failed.append("is not handed out as a callable")
                    if captures:
                        failed.append("its captured names could be parameters")
                if uses(inner, outer) >= 2:
                    failed.append("is a helper used more than once")
                if failed:
                    hits.append(Hit(m.path, inner.lineno, f"{RULE} nested `{inner.name}` {'; '.join(failed)}"))
    return hits
