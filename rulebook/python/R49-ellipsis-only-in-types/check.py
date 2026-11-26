"""R49: an `...` outside a type position (a stub body, a placeholder statement or value) needs the owner's approval."""

import ast

from rulekit import Hit, Module

RULE = "R49"


def _type_roots(node: ast.AST) -> list[ast.AST]:
    """Sub-trees of `node` that are type positions: subscripts (`tuple[int, ...]`) and annotations."""
    match node:
        case ast.Subscript():
            return [node.slice]
        case ast.arg() if node.annotation:
            return [node.annotation]
        case ast.FunctionDef() | ast.AsyncFunctionDef() if node.returns:
            return [node.returns]
        case ast.AnnAssign():
            return [node.annotation]
        case ast.TypeAlias():
            return [node.value]
        case _:
            return []


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        allowed: set[int] = {id(x) for n in ast.walk(m.tree) for root in _type_roots(n) for x in ast.walk(root)}
        statements: set[int] = {id(n.value) for n in ast.walk(m.tree) if isinstance(n, ast.Expr)}
        for node in ast.walk(m.tree):
            if isinstance(node, ast.Constant) and node.value is Ellipsis and id(node) not in allowed:
                role: str = "a body or placeholder statement" if id(node) in statements else "a value"
                out.append(
                    Hit(m.path, node.lineno, f"R49 `...` as {role}, outside a type position: ask before adding it")
                )
    return out
