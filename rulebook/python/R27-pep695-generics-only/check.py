"""R27: TypeVar/ParamSpec/TypeVarTuple declarations and Generic[...] / Protocol[...] bases."""

import ast

from rulekit import Hit, Module, classes

RULE = "R27"
_DECLARATIONS = {"TypeVar", "ParamSpec", "TypeVarTuple"}
_TYPING = {"typing", "typing_extensions"}


def _typing_name(node: ast.AST) -> str | None:
    """`X` for `X` or `typing.X` / `typing_extensions.X`, else None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in _TYPING:
        return node.attr
    return None


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        hits += [
            Hit(m.path, n.lineno, f"{RULE} `{name}(...)`; use PEP 695 type parameters")
            for n in ast.walk(m.tree)
            if isinstance(n, ast.Call) and (name := _typing_name(n.func)) in _DECLARATIONS
        ]
        hits += [
            Hit(m.path, cls.lineno, f"{RULE} `{cls.name}` subclasses `{ast.unparse(base)}`; use `class {cls.name}[T]`")
            for cls in classes(m.tree)
            for base in cls.bases
            if _typing_name(base) == "Generic"
            or (isinstance(base, ast.Subscript) and _typing_name(base.value) in {"Generic", "Protocol"})
        ]
    return hits
