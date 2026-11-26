"""R36: a module constant read by exactly one class, or a class constant named with a leading underscore."""

import ast
import re
from collections import Counter

from rulekit import Hit, Module, classes

RULE = "R36"
CONSTANT = re.compile(r"^_?[A-Z][A-Z0-9_]*$")


def _assigned(stmt: ast.stmt) -> str | None:
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        target = stmt.targets[0]
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        target = stmt.target
    else:
        return None
    return target.id if isinstance(target, ast.Name) and CONSTANT.match(target.id) else None


def _reads(nodes: list[ast.AST]) -> set[str]:
    return {n.id for node in nodes for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _exported(m: Module) -> set[str]:
    """Names this module imports from elsewhere or accesses as attributes."""
    out: set[str] = set()
    for n in ast.walk(m.tree):
        if isinstance(n, ast.ImportFrom):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def check(modules: list[Module]) -> list[Hit]:
    seen = [_exported(m) for m in modules]
    reach = Counter(name for names in seen for name in names)
    hits: list[Hit] = []
    for m, own in zip(modules, seen, strict=True):
        constants = {name: stmt for stmt in m.tree.body if (name := _assigned(stmt))}
        users: dict[str, set[str | None]] = {name: set() for name in constants}
        for stmt in m.tree.body:
            if isinstance(stmt, ast.ClassDef):
                inner, outer = stmt.body, [*stmt.bases, *stmt.keywords, *stmt.decorator_list]
                for name in _reads(inner) & users.keys():
                    users[name].add(stmt.name)
            else:
                outer = [stmt]
            for name in _reads(outer) & users.keys():
                users[name].add(None)
        # another module imports or accesses the name: it is not this class's alone
        candidates = {
            name
            for name, owners in users.items()
            if len(owners) == 1 and None not in owners and reach[name] == (name in own)
        }
        for name in candidates:
            (owner,) = users[name]
            if owner in _reads([constants[name]]):
                continue  # built from the class itself (e.g. a cached adapter of it): cannot live inside it
            msg = f"R36 `{name}` is used only by `{owner}`; make it a class attribute without underscore"
            hits.append(Hit(m.path, constants[name].lineno, msg))
        for cls in classes(m.tree):
            for stmt in cls.body:
                if (name := _assigned(stmt)) and name.startswith("_"):
                    msg = f"R36 class constant `{cls.name}.{name}` carries a leading underscore"
                    hits.append(Hit(m.path, stmt.lineno, msg))
    return hits
