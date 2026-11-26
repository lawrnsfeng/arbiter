"""R31: a concrete error subclasses the root error directly although its subsystem has a base error."""

import ast

from rulekit import Hit, Module, classes

RULE = "R31"


def _bases(cls: ast.ClassDef) -> list[str]:
    return [b.id if isinstance(b, ast.Name) else b.attr for b in cls.bases if isinstance(b, ast.Name | ast.Attribute)]


def check(modules: list[Module]) -> list[Hit]:
    found = [(m, c) for m in modules for c in classes(m.tree)]
    defined = {c.name for _, c in found}
    children: dict[str, list[tuple[Module, ast.ClassDef]]] = {}
    for m, c in found:
        for base in _bases(c):
            children.setdefault(base, []).append((m, c))
    hits: list[Hit] = []
    for root, kids in children.items():
        if root not in defined or not root.endswith("Error"):
            continue
        # a subsystem base: a direct child of the root named <Prefix>Error that has subclasses itself
        prefixes = [c.name.removesuffix("Error") for _, c in kids if c.name.endswith("Error") and c.name in children]
        for m, c in kids:
            for prefix in prefixes:
                rest = c.name.removeprefix(prefix)
                if prefix and c.name not in (f"{prefix}Error", rest) and rest[:1].isupper():
                    msg = f"R31 `{c.name}` subclasses `{root}` directly; subclass the subsystem base `{prefix}Error`"
                    hits.append(Hit(m.path, c.lineno, msg))
                    break
    return hits
