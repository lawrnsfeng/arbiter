"""R35: a str subclass converts one plain str through a sole from_* classmethod, or does setup-only work in __new__."""

import ast

from rulekit import Hit, Module, classes, local_nodes

RULE = "R35"


def _is_str_subclass(cls: ast.ClassDef) -> bool:
    return any(isinstance(b, ast.Name) and b.id == "str" for b in cls.bases)


def _is_classmethod(fn: ast.FunctionDef) -> bool:
    return any(isinstance(d, ast.Name) and d.id == "classmethod" for d in fn.decorator_list)


def _plain_str_converter(fn: ast.FunctionDef) -> bool:
    a = fn.args
    if a.posonlyargs or a.vararg or a.kwonlyargs or a.kwarg or len(a.args) != 2:
        return False
    ann = a.args[1].annotation
    if not (isinstance(ann, ast.Name) and ann.id == "str"):
        return False
    cls_name = a.args[0].arg
    return any(
        isinstance(n, ast.Return)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name)
        and n.value.func.id == cls_name
        for n in local_nodes(fn)
    )


def _unchanged_new(fn: ast.FunctionDef) -> bool:
    params = {a.arg for a in fn.args.args[1:]}
    nodes = local_nodes(fn)
    stored = {n.id for n in nodes if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    for n in nodes:
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "__new__":
            owner = n.func.value
            from_str = isinstance(owner, ast.Name) and owner.id == "str"
            from_super = isinstance(owner, ast.Call) and isinstance(owner.func, ast.Name) and owner.func.id == "super"
            value = n.args[1] if len(n.args) == 2 else None
            if (from_str or from_super) and isinstance(value, ast.Name) and value.id in params - stored:
                return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in modules:
        for cls in filter(_is_str_subclass, classes(m.tree)):
            methods = [f for f in cls.body if isinstance(f, ast.FunctionDef)]
            factories = [f for f in methods if f.name.startswith("from_") and _is_classmethod(f)]
            if len(factories) == 1 and _plain_str_converter(factories[0]):
                fn = factories[0]
                msg = f"R35 `{cls.name}.{fn.name}` converts one plain str; put the logic in `__new__`"
                hits.append(Hit(m.path, fn.lineno, msg))
            for fn in methods:
                if fn.name == "__new__" and _unchanged_new(fn):
                    msg = f"R35 `{cls.name}.__new__` keeps the value unchanged; setup-only work belongs in `__init__`"
                    hits.append(Hit(m.path, fn.lineno, msg))
    return hits
