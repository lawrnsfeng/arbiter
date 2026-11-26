"""R16: get_/set_ functions and methods that are plain accessors of one stored value."""

import ast

from rulekit import Hit, Module, classes, params_of

RULE = "R16"
_NEUTRAL_BASES = {"object", "ABC", "Protocol", "Generic"}

type Function = ast.FunctionDef | ast.AsyncFunctionDef


def _body(fn: Function) -> list[ast.stmt]:
    """The body without its docstring and `global` statements."""
    body = [s for s in fn.body if not isinstance(s, ast.Global)]
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return body


def _root(node: ast.expr) -> str | None:
    """Name at the root of an attribute/subscript chain (optionally ending in `.get(...)`), else None."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
        node = node.func.value
    while isinstance(node, ast.Attribute | ast.Subscript):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _stored(node: ast.expr, fn: Function, is_method: bool) -> bool:
    """True when `node` names stored state: rooted at self/cls in a method, at a non-parameter name elsewhere."""
    root = _root(node)
    params = [p.arg for p in params_of(fn)]
    if is_method:
        return bool(params) and root == params[0] and not isinstance(node, ast.Name)
    if root is None or root in params:
        return False
    if isinstance(node, ast.Name):
        return any(isinstance(s, ast.Global) and root in s.names for s in fn.body) or not isinstance(
            node.ctx, ast.Store
        )
    return True


def _accessor(fn: Function, is_method: bool) -> str | None:
    """'get' or 'set' when `fn` is a plain accessor with that prefix."""
    if fn.decorator_list:
        return None
    body = _body(fn)
    if len(body) != 1:
        return None
    stmt = body[0]
    if fn.name.startswith("get_") and isinstance(stmt, ast.Return) and stmt.value is not None:
        return "get" if _stored(stmt.value, fn, is_method) else None
    if fn.name.startswith("set_") and isinstance(stmt, ast.Assign | ast.AnnAssign):
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        return "set" if len(targets) == 1 and _stored(targets[0], fn, is_method) else None
    return None


def _base_name(base: ast.expr) -> str | None:
    if isinstance(base, ast.Subscript):
        base = base.value
    if isinstance(base, ast.Attribute):
        return base.attr
    return base.id if isinstance(base, ast.Name) else None


def check(modules: list[Module]) -> list[Hit]:
    local: dict[str, list[ast.ClassDef]] = {}
    for m in modules:
        for cls in classes(m.tree):
            local.setdefault(cls.name, []).append(cls)

    memo: dict[str, bool] = {}

    def own(name: str | None) -> bool:
        """True when the class's whole base chain is defined in the scanned code."""
        if name in _NEUTRAL_BASES:
            return True
        if name is None or name not in local:
            return False
        if name not in memo:
            memo[name] = False  # cycle guard
            memo[name] = all(own(_base_name(b)) for c in local[name] for b in c.bases)
        return memo[name]

    hits = []
    for m in modules:
        candidates: list[tuple[Function, bool]] = [
            (s, False) for s in m.tree.body if isinstance(s, ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        for cls in classes(m.tree):
            if all(own(_base_name(b)) for b in cls.bases):
                candidates += [(s, True) for s in cls.body if isinstance(s, ast.FunctionDef | ast.AsyncFunctionDef)]
        for fn, is_method in candidates:
            if kind := _accessor(fn, is_method):
                hits.append(
                    Hit(
                        m.path, fn.lineno, f"{RULE} `{fn.name}` is a {kind}_ accessor; use a property, a noun or a verb"
                    )
                )
    return hits
