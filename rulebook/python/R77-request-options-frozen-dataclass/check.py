"""R77: a method with more than five defaulted parameters all forwarded into one call or dict."""

import ast

from rulekit import Hit, Module, classes, local_nodes

RULE = "R77"
LIMIT = 5


def defaulted(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    a = fn.args
    positional = [*a.posonlyargs, *a.args]
    with_default = positional[len(positional) - len(a.defaults) :] if a.defaults else []
    kw = [arg for arg, d in zip(a.kwonlyargs, a.kw_defaults, strict=True) if d is not None]
    return {arg.arg for arg in [*with_default, *kw]}


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        for cls in classes(mod.tree):
            for fn in cls.body:
                if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if fn.name in {"__init__", "__new__"} or fn.name.startswith("create"):
                    continue
                names = defaulted(fn)
                if len(names) <= LIMIT:
                    continue
                # one call or dict naming every defaulted parameter: they all describe the request it forwards
                carriers = [n for n in local_nodes(fn) if isinstance(n, ast.Call | ast.Dict)]
                for node in carriers:
                    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
                    if names <= used:
                        hits.append(
                            Hit(
                                mod.path,
                                fn.lineno,
                                f"R77 `{fn.name}` forwards {len(names)} keyword parameters as one request",
                            )
                        )
                        break
    return hits
