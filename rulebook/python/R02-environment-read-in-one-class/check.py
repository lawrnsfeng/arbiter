"""R2: environment reads outside the environment class (env.py), bar XDG roots in paths.py and dict pass-through."""

import ast
from pathlib import Path

from rulekit import Hit, Module, classes

RULE = "R2"
WRITES = {"update", "pop", "clear", "popitem"}


def is_environ(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute):
        return node.attr == "environ" and isinstance(node.value, ast.Name) and node.value.id == "os"
    return isinstance(node, ast.Name) and node.id == "environ"


def is_getenv(node: ast.AST) -> bool:
    f = node.func if isinstance(node, ast.Call) else None
    return (
        isinstance(f, ast.Attribute) and f.attr == "getenv" and isinstance(f.value, ast.Name) and f.value.id == "os"
    ) or (isinstance(f, ast.Name) and f.id == "getenv")


def read_key(node: ast.AST, parent: dict[int, ast.AST]) -> str | None:
    """The constant key of `os.environ[...]`, `os.environ.get(...)` or `os.getenv(...)`, if any."""
    up = parent.get(id(node))
    if isinstance(node, ast.Call):
        arg = node.args[0] if node.args else None
    elif isinstance(up, ast.Subscript):
        arg = up.slice
    elif isinstance(up, ast.Attribute) and isinstance(call := parent.get(id(up)), ast.Call) and call.args:
        arg = call.args[0]
    else:
        return None
    return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None


def allowed(node: ast.AST, parent: dict[int, ast.AST]) -> bool:
    up = parent.get(id(node))
    if isinstance(up, ast.Dict) and any(k is None and v is node for k, v in zip(up.keys, up.values, strict=True)):
        return True  # {**os.environ, **extra}: subprocess pass-through
    if isinstance(up, ast.Subscript) and not isinstance(up.ctx, ast.Load):
        return True  # write or delete
    if isinstance(up, ast.Attribute) and up.attr in WRITES:
        return True
    return isinstance(up, ast.Call) and isinstance(up.func, ast.Attribute) and up.func.attr == "dict"  # patch.dict


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        name = Path(m.path).name
        parent = {id(c): p for p in ast.walk(m.tree) for c in ast.iter_child_nodes(p)}
        exempt = {id(n) for c in classes(m.tree) for n in ast.walk(c)} if name == "env.py" else set()
        for node in ast.walk(m.tree):
            if id(node) in exempt or not (is_environ(node) or is_getenv(node)) or allowed(node, parent):
                continue
            key = read_key(node, parent)
            if name == "paths.py" and key and key.startswith("XDG_"):
                continue
            what = f"`{key}`" if key else "the environment"
            out.append(Hit(m.path, node.lineno, f"{RULE} reads {what} outside the environment class: use its accessor"))
    return out
