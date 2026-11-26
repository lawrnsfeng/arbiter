"""R22: SQL text written inline at an execute() call, or as a constant, outside the queries module."""

import ast
import re
from pathlib import Path

from rulekit import Hit, Module, functions, local_nodes

RULE = "R22"
_VERBS = "select|insert|update|delete|with|create|alter|drop|grant|revoke|truncate|merge"
_CLAUSES = "from|into|set|table|where|values|schema|on|to|index|view|as|select"
_SQL = re.compile(rf"^\s*({_VERBS})\b.*\b({_CLAUSES})\b", re.IGNORECASE | re.DOTALL)
_SQL_UPPER = re.compile(rf"^\s*({_VERBS.upper()})\b.*\b({_CLAUSES.upper()})\b", re.DOTALL)
_EXECUTE = {"execute", "executemany", "executescript", "mogrify"}
_WRAPPERS = {"SQL", "text"}


def _text(node: ast.AST) -> str | None:
    """Literal text of a string-ish expression (formatted parts blanked), else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else " x " for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Mod):
        return _text(node.left)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        return _text(node.func.value)
    return None


def _wrapped(node: ast.AST) -> str | None:
    """The literal inside `SQL("...")` / `text("...")`, possibly followed by `.format(...)`, else None."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        node = node.func.value
    if not isinstance(node, ast.Call) or not node.args:
        return None
    func = node.func
    name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
    return _text(node.args[0]) if name in _WRAPPERS else None


def _is_sql(node: ast.AST, pattern: re.Pattern[str], any_wrapped: bool) -> bool:
    """SQL text by `pattern`; at an execute() call (`any_wrapped`) every SQL()/text() wrapper counts."""
    wrapped = _wrapped(node)
    if wrapped is not None:
        return any_wrapped or bool(_SQL.match(wrapped))
    text = _text(node)
    return text is not None and bool(pattern.match(text))


def _executes(path: str, nodes: list[ast.AST]) -> list[Hit]:
    """execute() calls given SQL text inline or via a name bound to SQL text in the same scope."""
    bound = {
        t.id
        for n in nodes
        if isinstance(n, ast.Assign) and _is_sql(n.value, _SQL, any_wrapped=False)
        for t in n.targets
        if isinstance(t, ast.Name)
    }
    hits = []
    for n in nodes:
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in _EXECUTE and n.args):
            continue
        arg = n.args[0]
        if _is_sql(arg, _SQL, any_wrapped=True) or (isinstance(arg, ast.Name) and arg.id in bound):
            hits.append(Hit(path, n.lineno, f"{RULE} inline SQL at `{n.func.attr}()`; call a queries-module function"))
    return hits


def _exempt(path: str) -> bool:
    """The queries module itself, and migrations (their framework runs SQL inline)."""
    p = Path(path)
    return p.name == "queries.py" or bool({"queries", "migrations"} & set(p.parent.parts))


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        if _exempt(m.path):
            continue
        for fn in functions(m.tree):
            hits += _executes(m.path, local_nodes(fn))
        hits += _executes(m.path, local_nodes(m.tree))
        holders = [m.tree, *(n for n in ast.walk(m.tree) if isinstance(n, ast.ClassDef))]
        hits += [
            Hit(m.path, stmt.lineno, f"{RULE} SQL constant outside the queries module")
            for holder in holders
            for stmt in holder.body
            if isinstance(stmt, ast.Assign | ast.AnnAssign)
            and stmt.value is not None
            and _is_sql(stmt.value, _SQL_UPPER, any_wrapped=False)
        ]
    return hits
