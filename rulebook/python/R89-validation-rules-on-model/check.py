"""R89: a small helper that checks one value and raises a stringly ValueError/TypeError, in a pydantic project."""

import ast

from rulekit import Hit, Module, classes, local_nodes, params_of

RULE = "R89"
Function = ast.FunctionDef | ast.AsyncFunctionDef
STRINGLY = {"ValueError", "TypeError"}
VALIDATOR_DECORATORS = {"field_validator", "model_validator", "validator", "root_validator"}
MAX_PARAMS = 2


def uses_pydantic(modules: list[Module]) -> bool:
    return any(
        (isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "pydantic")
        or (isinstance(n, ast.Import) and any(a.name.split(".")[0] == "pydantic" for a in n.names))
        for m in modules
        for n in ast.walk(m.tree)
    )


def name_of(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Call):
        expr = expr.func
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return expr.id if isinstance(expr, ast.Name) else None


def is_text(expr: ast.expr, texts: set[str]) -> bool:
    """A string literal, f-string, `"..." % x`, `"...".format(x)`, or a local bound to one of those."""
    if isinstance(expr, ast.JoinedStr) or (isinstance(expr, ast.Constant) and isinstance(expr.value, str)):
        return True
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Mod | ast.Add):
        return is_text(expr.left, texts)
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "format":
        return is_text(expr.func.value, texts)
    return isinstance(expr, ast.Name) and expr.id in texts


def stringly_raise(fn: Function) -> ast.Raise | None:
    """The first `raise ValueError("..."/f"..."/message)` guarded by a test on a parameter or in an except handler."""
    params = {a.arg for a in params_of(fn)} - {"self", "cls"}
    texts = {
        t.id
        for n in local_nodes(fn)
        if isinstance(n, ast.Assign) and is_text(n.value, set())
        for t in n.targets
        if isinstance(t, ast.Name)
    }
    for node in local_nodes(fn):
        guarded = isinstance(node, ast.ExceptHandler) or (
            isinstance(node, ast.If) and any(isinstance(n, ast.Name) and n.id in params for n in ast.walk(node.test))
        )
        if not guarded:
            continue
        for stmt in [*node.body, *(node.orelse if isinstance(node, ast.If) else [])]:
            if (
                isinstance(stmt, ast.Raise)
                and isinstance(stmt.exc, ast.Call)
                and name_of(stmt.exc) in STRINGLY
                and stmt.exc.args
                and is_text(stmt.exc.args[0], texts)
            ):
                return stmt
    return None


def check(modules: list[Module]) -> list[Hit]:
    if not uses_pydantic(modules):
        return []
    hits: list[Hit] = []
    for mod in modules:
        in_models = {
            id(fn) for cls in classes(mod.tree) if any(name_of(b) == "BaseModel" for b in cls.bases) for fn in cls.body
        }
        candidates = [n for n in mod.tree.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]
        candidates += [
            fn for cls in classes(mod.tree) for fn in cls.body if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef)
        ]
        for fn in candidates:
            if id(fn) in in_models or fn.name.startswith("__"):
                continue
            if any(name_of(d) in VALIDATOR_DECORATORS for d in fn.decorator_list):
                continue
            if not 1 <= len({a.arg for a in params_of(fn)} - {"self", "cls"}) <= MAX_PARAMS:
                continue
            if raise_node := stringly_raise(fn):
                kind = name_of(raise_node.exc)
                hits.append(
                    Hit(mod.path, raise_node.lineno, f"R89 `{fn.name}` raises a stringly {kind}: model the rule")
                )
    return hits
