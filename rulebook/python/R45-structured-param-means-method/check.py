"""R45: a free function named after its one structured first parameter's class, other params primitive."""

import ast
import re

from rulekit import Hit, Module, classes, local_nodes

RULE = "R45"
PRIMITIVES = {"int", "str", "float", "bool", "bytes", "complex", "dict", "list", "set", "frozenset", "tuple", "None"}


def _words(class_name: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z0-9]+", class_name)]


def _prefixes(class_name: str) -> list[str]:
    """`ParcelRoute` -> `parcel_route_`, `route_`: the class name or its trailing words."""
    words = _words(class_name)
    return ["_".join(words[i:]) + "_" for i in range(len(words))]


def _primitive(annotation: ast.expr | None) -> bool:
    if isinstance(annotation, ast.Subscript):
        annotation = annotation.value
    if isinstance(annotation, ast.BinOp):  # `int | None`
        return _primitive(annotation.left) and _primitive(annotation.right)
    if isinstance(annotation, ast.Constant) and annotation.value is None:
        return True
    return isinstance(annotation, ast.Name) and annotation.id in PRIMITIVES


def check(modules: list[Module]) -> list[Hit]:
    project = {c.name for m in modules for c in classes(m.tree)}
    hits: list[Hit] = []
    for m in modules:
        for fn in m.tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or fn.decorator_list:
                continue
            a = fn.args
            params = [*a.posonlyargs, *a.args, *a.kwonlyargs]
            if not params or a.vararg or a.kwarg:
                continue
            first, rest = params[0], params[1:]
            ann = first.annotation
            cls = ann.id if isinstance(ann, ast.Name) else ann.value if isinstance(ann, ast.Constant) else None
            if cls not in project or not all(_primitive(p.annotation) for p in rest):
                continue
            if not any(fn.name.lstrip("_").startswith(p) for p in _prefixes(str(cls))):
                continue
            reads = [
                n
                for n in local_nodes(fn)
                if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == first.arg
            ]
            if reads:
                msg = f"R45 `{fn.name}` works on `{cls}` and repeats its name; make it a `{cls}` method"
                hits.append(Hit(m.path, fn.lineno, msg))
    return hits
