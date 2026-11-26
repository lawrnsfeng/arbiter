"""R18: string-key access on a dict read straight from I/O, outside a from_*/as_*/to_* conversion."""

import ast

from rulekit import Hit, Module, functions, local_nodes

RULE = "R18"
_READERS = {
    ("json", "load"),
    ("json", "loads"),
    ("tomllib", "load"),
    ("tomllib", "loads"),
    ("toml", "load"),
    ("toml", "loads"),
    ("yaml", "load"),
    ("yaml", "safe_load"),
}
_CONVERTERS = ("from_", "as_", "to_")


def _is_read(node: ast.AST) -> bool:
    """True for a call that returns a raw dict from I/O."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    func = node.func
    if func.attr == "json" and not node.args and not node.keywords:
        return True  # HTTP response body
    return isinstance(func.value, ast.Name) and (func.value.id, func.attr) in _READERS


def _keyed(node: ast.AST) -> ast.expr | None:
    """The indexed object of `x["k"]` (load) or `x.get("k", ...)`, else None."""
    if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load):
        key = node.slice
        target = node.value
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
        key = node.args[0]
        target = node.func.value
    else:
        return None
    return target if isinstance(key, ast.Constant) and isinstance(key.value, str) else None


def _scope(path: str, nodes: list[ast.AST]) -> list[Hit]:
    raw: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None and _is_read(node.value):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            raw |= {t.id for t in targets if isinstance(t, ast.Name)}
    hits = []
    for node in nodes:
        target = _keyed(node)
        if target is not None and (_is_read(target) or (isinstance(target, ast.Name) and target.id in raw)):
            hits.append(
                Hit(path, node.lineno, f"{RULE} `{ast.unparse(node)}` indexes a raw I/O dict; convert it at the read")
            )
    return hits


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        hits += _scope(m.path, local_nodes(m.tree))  # module level: same walk, nested defs excluded
        for fn in functions(m.tree):
            if not fn.name.startswith(_CONVERTERS):
                hits += _scope(m.path, local_nodes(fn))
    return hits
