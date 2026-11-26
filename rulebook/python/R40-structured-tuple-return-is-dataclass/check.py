"""R40: a function's return annotation is a tuple of two or more structured project classes."""

import ast

from rulekit import Hit, Module, classes, functions

RULE = "R40"
# bases that make a class a scalar value (C5): str/number subclasses and enums
SCALAR_BASES = {"str", "int", "float", "bytes", "bool", "complex", "Enum", "StrEnum", "IntEnum", "Flag", "IntFlag"}


def _name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.rsplit(".", 1)[-1]
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _structured(modules: list[Module]) -> set[str]:
    """Classes defined in the scanned modules that are not scalar values, directly or through a scanned base."""
    bases = {c.name: {_name(b) for b in c.bases} for m in modules for c in classes(m.tree)}
    scalar = set(SCALAR_BASES)
    changed = True
    while changed:
        grown = {name for name, bs in bases.items() if bs & scalar}
        changed = not grown <= scalar
        scalar |= grown
    return bases.keys() - scalar


def check(modules: list[Module]) -> list[Hit]:
    structured = _structured(modules)
    hits: list[Hit] = []
    for m in modules:
        for fn in functions(m.tree):
            ret = fn.returns
            if not (isinstance(ret, ast.Subscript) and _name(ret.value) in {"tuple", "Tuple"}):
                continue
            elts = ret.slice.elts if isinstance(ret.slice, ast.Tuple) else [ret.slice]
            names = [_name(e) for e in elts]
            if len(names) >= 2 and all(n in structured for n in names):
                msg = f"R40 `{fn.name}` returns a tuple of {', '.join(map(str, names))}; return a frozen dataclass"
                hits.append(Hit(m.path, fn.lineno, msg))
    return hits
