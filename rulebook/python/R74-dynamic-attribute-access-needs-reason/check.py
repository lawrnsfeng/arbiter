"""R74: `getattr`/`hasattr` on the own instance or class, outside attribute-protocol methods.

The own object is `self`, `cls`, `type(<own>)`, `<own>.__class__`, or the enclosing class's name.
"""

import ast

from rulekit import Hit, Module, functions, local_nodes

RULE = "R74"
PROTOCOL = {"__getattr__", "__getattribute__", "__setattr__", "__delattr__", "__dir__"}


def own_object(node: ast.expr, own: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in own
    if isinstance(node, ast.Attribute) and node.attr == "__class__":
        return own_object(node.value, own)
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "type"
        and len(node.args) == 1
        and own_object(node.args[0], own)
    )


def owners(tree: ast.Module) -> dict[int, str]:
    """Function node id -> name of the class whose body defines it directly."""
    return {
        id(fn): cls.name
        for cls in ast.walk(tree)
        if isinstance(cls, ast.ClassDef)
        for fn in cls.body
        if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        classes = owners(m.tree)
        for fn in functions(m.tree):
            if fn.name in PROTOCOL:
                continue
            own = {"self", "cls"} | ({classes[id(fn)]} if id(fn) in classes else set())
            for node in local_nodes(fn):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in {"getattr", "hasattr"}
                    and node.args
                    and own_object(node.args[0], own)
                ):
                    text = ast.unparse(node.args[0])
                    hits.append(Hit(m.path, node.lineno, f"{RULE} `{node.func.id}` on `{text}`: dispatch with `match`"))
    return hits
