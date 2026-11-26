"""R78: a private module-level function with a mechanical tell and no `Stays free:` reason."""

import ast
from collections import Counter

from rulekit import Hit, Module, classes, params_of

RULE = "R78"
Function = ast.FunctionDef | ast.AsyncFunctionDef


def private_free(tree: ast.Module) -> list[Function]:
    return [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
        and n.name.startswith("_")
        and not n.name.startswith("__")
    ]


def stays_free(fn: Function) -> bool:
    doc = ast.get_docstring(fn) or ""
    return any(line.strip().startswith("Stays free:") for line in doc.splitlines())


def annotation_name(arg: ast.arg) -> str | None:
    ann = arg.annotation
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        return ann.value
    return ann.id if isinstance(ann, ast.Name) else None


def reads_one_param(fn: Function) -> str | None:
    """Tell (a): attribute reads on one parameter are most of the body's name references."""
    params = {a.arg for a in params_of(fn)}
    names = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)]
    attrs = Counter(
        n.value.id
        for n in ast.walk(fn)
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in params
    )
    if not attrs:
        return None
    param, count = attrs.most_common(1)[0]
    distinct = {
        n.attr
        for n in ast.walk(fn)
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == param
    }
    return param if len(distinct) >= 2 and count * 2 > len(names) else None


def only_constructs(fn: Function, owned: set[str]) -> str | None:
    """Tell (c): every return builds the same project-owned class."""
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
    built = [
        r.value.func.id if isinstance(r.value, ast.Call) and isinstance(r.value.func, ast.Name) else None
        for r in returns
    ]
    return built[0] if built and built[0] in owned and len(set(built)) == 1 else None


def callers_in_one_class(tree: ast.Module, name: str) -> str | None:
    """Tell (e): every reference to the function is inside one class body."""
    total = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == name)
    if not total:
        return None
    for cls in classes(tree):
        inside = sum(1 for n in ast.walk(cls) if isinstance(n, ast.Name) and n.id == name)
        if inside == total:
            return cls.name
    return None


def check(modules: list[Module]) -> list[Hit]:
    owned = {c.name for m in modules for c in classes(m.tree)}
    hits: list[Hit] = []
    for mod in modules:
        fns = private_free(mod.tree)
        shared = Counter(t for fn in fns for t in {annotation_name(a) for a in params_of(fn)} if t in owned)
        for fn in fns:
            if stays_free(fn):
                continue
            family = sorted(t for t in {annotation_name(a) for a in params_of(fn)} if shared.get(t, 0) >= 2)
            if family:
                tell = f"(b) `{family[0]}` recurs across private functions: make the family one class"
            elif cls := callers_in_one_class(mod.tree, fn.name):
                tell = f"(e) only `{cls}` uses it: make it `{cls}`'s staticmethod"
            elif built := only_constructs(fn, owned):
                tell = f"(c) only builds `{built}`: make it `{built}`'s classmethod"
            elif param := reads_one_param(fn):
                tell = f"(a) mostly reads `{param}`'s fields: make it that type's method"
            else:
                continue
            hits.append(Hit(mod.path, fn.lineno, f"R78 `{fn.name}` has tell {tell}, or state `Stays free:`"))
    return hits
