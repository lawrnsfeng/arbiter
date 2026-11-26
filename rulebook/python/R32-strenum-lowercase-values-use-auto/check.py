"""R32: a StrEnum member spells out its own lowercased name instead of auto()."""

import ast

from rulekit import Hit, Module, classes

RULE = "R32"


def _is_strenum(cls: ast.ClassDef) -> bool:
    return any(isinstance(b, ast.Name | ast.Attribute) and ast.unparse(b).endswith("StrEnum") for b in cls.bases)


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in modules:
        for cls in filter(_is_strenum, classes(m.tree)):
            for stmt in cls.body:
                if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1):
                    continue
                target, value = stmt.targets[0], stmt.value
                if (
                    isinstance(target, ast.Name)
                    and isinstance(value, ast.Constant)
                    and value.value == target.id.lower()
                ):
                    hits.append(Hit(m.path, stmt.lineno, f"R32 `{cls.name}.{target.id}` repeats its name; use auto()"))
    return hits
