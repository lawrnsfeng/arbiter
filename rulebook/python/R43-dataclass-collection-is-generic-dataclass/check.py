"""R43: free functions threading a list of one dataclass, or a list subclass standing in for its collection class."""

import ast

from rulekit import Hit, Module, classes

RULE = "R43"
SEQUENCES = {"list", "List", "Sequence", "Iterable", "Collection", "tuple", "Tuple"}


def _name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_dataclass(cls: ast.ClassDef) -> bool:
    return any(_name(d.func if isinstance(d, ast.Call) else d) == "dataclass" for d in cls.decorator_list)


def _element(annotation: ast.expr | None) -> str | None:
    """`X` of `list[X]`, `Sequence[X]`, `tuple[X, ...]` and friends."""
    if not (isinstance(annotation, ast.Subscript) and _name(annotation.value) in SEQUENCES):
        return None
    inner = annotation.slice
    if isinstance(inner, ast.Tuple):
        if len(inner.elts) != 2 or not (isinstance(inner.elts[1], ast.Constant) and inner.elts[1].value is ...):
            return None
        inner = inner.elts[0]
    if isinstance(inner, ast.Subscript):  # a generic item, e.g. list[Edit[T]]
        inner = inner.value
    return _name(inner)


def check(modules: list[Module]) -> list[Hit]:
    records = {c.name for m in modules for c in classes(m.tree) if _is_dataclass(c)}
    hits: list[Hit] = []
    for m in modules:
        by_record: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        for fn in m.tree.body:
            if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                params = [*fn.args.posonlyargs, *fn.args.args]
                if params and (item := _element(params[0].annotation)) in records:
                    by_record.setdefault(item, []).append(fn)
        for item, fns in by_record.items():
            if len(fns) < 2:
                continue
            for fn in fns:
                msg = f"R43 `{fn.name}` is one of {len(fns)} free functions over a list of `{item}`; make them methods"
                hits.append(Hit(m.path, fn.lineno, msg))
        for cls in classes(m.tree):
            for base in cls.bases:
                item = _element(base) if isinstance(base, ast.Subscript) and _name(base.value) == "list" else None
                if item == "object" or item in records:
                    msg = f"R43 `{cls.name}` subclasses `list[{item}]`; use a frozen generic dataclass holding a tuple"
                    hits.append(Hit(m.path, cls.lineno, msg))
    return hits
