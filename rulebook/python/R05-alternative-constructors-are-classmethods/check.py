"""R5: free functions constructing a project class, and constructor classmethods not named `from_*`."""

import ast

from rulekit import Hit, Module, classes, foreign_imports, local_nodes, project_tops

RULE = "R5"


def annotated_class(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    r = fn.returns
    if isinstance(r, ast.Name):
        return r.id
    if isinstance(r, ast.Constant) and isinstance(r.value, str):
        return r.value
    return None


def returns_call_of(fn: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    return any(
        isinstance(n, ast.Return)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Name)
        and n.value.func.id == name
        for n in local_nodes(fn)
    )


def is_classmethod(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(isinstance(d, ast.Name) and d.id == "classmethod" for d in fn.decorator_list)


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    defined = {c.name for m in modules for c in classes(m.tree)}
    tops = project_tops(modules)
    for m in modules:
        owned = defined - foreign_imports(m.tree, tops)
        for fn in m.tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or fn.decorator_list:
                continue
            cls = annotated_class(fn)
            if cls in owned and returns_call_of(fn, cls):
                out.append(
                    Hit(m.path, fn.lineno, f"{RULE} `{fn.name}` constructs `{cls}`: make it `{cls}.from_*` classmethod")
                )
        out += [
            Hit(m.path, fn.lineno, f"{RULE} constructor classmethod `{c.name}.{fn.name}` is not named `from_*`")
            for c in classes(m.tree)
            for fn in c.body
            if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef)
            and is_classmethod(fn)
            and not fn.name.startswith(("from_", "__"))
            and len(fn.args.args) + len(fn.args.kwonlyargs) + bool(fn.args.vararg) > 1
            and returns_call_of(fn, "cls")
        ]
    return out
