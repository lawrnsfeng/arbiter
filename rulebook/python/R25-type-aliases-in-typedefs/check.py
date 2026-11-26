"""R25: type aliases outside typedefs.py, and annotations that are missing an alias (deep, wrapped, wide tuple)."""

import ast
from pathlib import Path

from rulekit import Hit, Module, functions, params_of

RULE = "R25"
_GENERICS = {
    "dict", "list", "tuple", "set", "frozenset", "type",
    "Dict", "List", "Tuple", "Set", "FrozenSet", "Type",
    "Callable", "Mapping", "MutableMapping", "Sequence", "MutableSequence", "Iterable", "Iterator",
    "Generator", "AsyncIterator", "AsyncGenerator", "Awaitable", "Coroutine",
    "Optional", "Union", "Literal", "Annotated",
}  # fmt: skip
_BUILTIN_TYPES = {"int", "str", "float", "bool", "bytes", "complex", "object"}
_ALIAS_CALLS = {"NewType", "TypeAliasType"}
_DEPTH = 3
_TUPLE_MEMBERS = 4


def _last(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else None


def _generic(node: ast.AST) -> bool:
    return isinstance(node, ast.Subscript) and _last(node.value) in _GENERICS


def _type_expr(node: ast.AST) -> bool:
    """A value that can only be a type: a subscripted generic, or a `|` union with at least one such or a builtin."""
    if _generic(node):
        return True
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr)):
        return False
    parts: list[ast.AST] = []
    stack: list[ast.AST] = [node]
    while stack:
        n = stack.pop()
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
            stack += [n.left, n.right]
        else:
            parts.append(n)
    typed = [
        p
        for p in parts
        if _generic(p) or _last(p) in _BUILTIN_TYPES or (isinstance(p, ast.Constant) and p.value is None)
    ]
    return bool(typed) and all(p in typed or isinstance(p, ast.Name | ast.Attribute) for p in parts)


def _alias(stmt: ast.stmt) -> str | None:
    """Name of the alias a module-level statement defines, else None."""
    if isinstance(stmt, ast.TypeAlias):
        return stmt.name.id
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and _last(stmt.annotation) == "TypeAlias":
        return stmt.target.id
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        value = stmt.value
        if isinstance(value, ast.Call) and _last(value.func) in _ALIAS_CALLS:
            return stmt.targets[0].id
        if _type_expr(value):
            return stmt.targets[0].id
    return None


def _depth(node: ast.AST) -> int:
    """Subscript nesting depth of an annotation."""
    inner = max((_depth(c) for c in ast.iter_child_nodes(node)), default=0)
    return inner + 1 if isinstance(node, ast.Subscript) else inner


def _wide_tuple(node: ast.AST) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Subscript) and _last(n.value) in {"tuple", "Tuple"} and isinstance(n.slice, ast.Tuple):
            members = [e for e in n.slice.elts if not (isinstance(e, ast.Constant) and e.value is Ellipsis)]
            if len(members) >= _TUPLE_MEMBERS:
                return True
    return False


def _annotations(tree: ast.Module) -> list[ast.expr]:
    out: list[ast.expr] = []
    for fn in functions(tree):
        out += [p.annotation for p in params_of(fn) if p.annotation is not None]
        if fn.returns is not None:
            out.append(fn.returns)
    out += [n.annotation for n in ast.walk(tree) if isinstance(n, ast.AnnAssign) and _last(n.annotation) != "TypeAlias"]
    return out


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        name = Path(m.path).name
        if name == "typedefs.py":
            continue
        where = "a module named types.py (rename it typedefs.py)" if name == "types.py" else "the module using it"
        hits += [
            Hit(m.path, stmt.lineno, f"{RULE} alias `{alias}` defined in {where}; move it to typedefs.py")
            for stmt in m.tree.body
            if (alias := _alias(stmt))
        ]
        for ann in _annotations(m.tree):
            reasons = []
            if _depth(ann) >= _DEPTH:
                reasons.append(f"nests {_depth(ann)} levels")
            if (ann.end_lineno or ann.lineno) > ann.lineno:
                reasons.append("wraps")
            if _wide_tuple(ann):
                reasons.append(f"has a tuple of {_TUPLE_MEMBERS}+ members")
            if reasons:
                hits.append(Hit(m.path, ann.lineno, f"{RULE} annotation {', '.join(reasons)}; name it in typedefs.py"))
    return hits
