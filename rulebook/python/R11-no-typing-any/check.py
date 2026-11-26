"""R11: every use of `typing.Any`."""

import ast

from rulekit import Hit, Module

RULE = "R11"
TYPING = {"typing", "typing_extensions"}


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        names: set[str] = set()
        mods: set[str] = set()
        for n in ast.walk(m.tree):
            if isinstance(n, ast.ImportFrom) and n.module in TYPING:
                names |= {a.asname or a.name for a in n.names if a.name == "Any"}
            elif isinstance(n, ast.Import):
                mods |= {a.asname or a.name for a in n.names if a.name in TYPING}
        if not (names or mods):
            continue
        for n in ast.walk(m.tree):
            if isinstance(n, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) and n.name in names:
                names.discard(n.name)  # the module rebinds the name to its own class or function
        for n in ast.walk(m.tree):
            hit = (isinstance(n, ast.Name) and n.id in names) or (
                isinstance(n, ast.Attribute)
                and n.attr == "Any"
                and isinstance(n.value, ast.Name)
                and n.value.id in mods
            )
            if hit:
                out.append(Hit(m.path, n.lineno, f"{RULE} `typing.Any` used: state a concrete type or a dataclass"))
    return out
