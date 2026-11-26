"""R21: a function that reads a file and keeps the result across calls (memoised or stored in a global)."""

import ast

from rulekit import Hit, Module, functions, local_nodes

RULE = "R21"
_CACHES = {"cache", "lru_cache", "cached_property"}
_READ_METHODS = {"open", "read_text", "read_bytes"}
_LOADERS = {"json", "tomllib", "yaml", "pickle"}
_PACKAGE_DATA = {"resources", "files", "get_data"}


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else None


def _reads(node: ast.AST) -> bool:
    """True for a call that reads a file."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "open"
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr in _READ_METHODS:
        return True
    return func.attr == "load" and isinstance(func.value, ast.Name) and func.value.id in _LOADERS


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for fn in functions(m.tree):
            nodes = local_nodes(fn)
            if not any(_reads(n) for n in nodes):
                continue
            if any(isinstance(n, ast.Name) and n.id == "__file__" for n in nodes) or any(
                isinstance(n, ast.Attribute) and n.attr in _PACKAGE_DATA for n in nodes
            ):
                continue  # package data: no other process mutates it
            kept = {g for n in nodes if isinstance(n, ast.Global) for g in n.names}
            stored = any(isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in kept for n in nodes)
            if any(_name(d) in _CACHES for d in fn.decorator_list) or stored:
                hits.append(
                    Hit(
                        m.path, fn.lineno, f"{RULE} `{fn.name}` keeps a file read across calls; reload it per operation"
                    )
                )
    return hits
