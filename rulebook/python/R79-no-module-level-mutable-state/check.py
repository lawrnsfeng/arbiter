"""R79: module-level mutable state: `global` rebinding, runtime-filled containers, cached singletons, module clients."""

import ast

from rulekit import Hit, Module, functions, params_of

RULE = "R79"
CONTAINERS = {
    "dict",
    "list",
    "set",
    "defaultdict",
    "OrderedDict",
    "Counter",
    "deque",
    "WeakValueDictionary",
    "WeakKeyDictionary",
}
MUTATORS = {
    "append",
    "add",
    "update",
    "setdefault",
    "extend",
    "insert",
    "pop",
    "popitem",
    "clear",
    "remove",
    "discard",
    "appendleft",
}
CACHES = {"cache", "lru_cache"}
CLIENT_SUFFIXES = ("Client", "Session", "Pool", "Engine", "Connection")
CLIENT_FACTORIES = {"create_engine", "create_async_engine", "connect", "client", "resource"}


def called_name(node: ast.expr) -> str | None:
    func = node.func if isinstance(node, ast.Call) else node
    if isinstance(func, ast.Attribute):
        return func.attr
    return func.id if isinstance(func, ast.Name) else None


def is_container(value: ast.expr | None) -> bool:
    if isinstance(value, ast.Dict | ast.List | ast.Set | ast.DictComp | ast.ListComp | ast.SetComp):
        return True
    return isinstance(value, ast.Call) and called_name(value) in CONTAINERS


def is_client(value: ast.expr | None) -> bool:
    if not isinstance(value, ast.Call):
        return False
    name = called_name(value) or ""
    return name.endswith(CLIENT_SUFFIXES) or name in CLIENT_FACTORIES


def module_bindings(tree: ast.Module) -> list[tuple[str, ast.stmt]]:
    out: list[tuple[str, ast.stmt]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            out += [(t.id, node) for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            out.append((node.target.id, node))
    return out


def mutated_in_functions(tree: ast.Module) -> set[str]:
    """Names whose object a function body mutates: `X[k] = v`, `del X[k]`, `X.append(...)`, ..."""
    out: set[str] = set()
    for fn in functions(tree):
        declared = {name for g in ast.walk(fn) if isinstance(g, ast.Global) for name in g.names}
        local = {a.arg for a in params_of(fn)} | {
            n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
        }
        found: set[str] = set()
        for node in ast.walk(fn):
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.ctx, ast.Store | ast.Del)
                and isinstance(node.value, ast.Name)
            ):
                found.add(node.value.id)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATORS
                and isinstance(node.func.value, ast.Name)
            ):
                found.add(node.func.value.id)
        out |= found - (local - declared)  # a local of the same name shadows the module binding
    return out


def returns_client(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """The return annotation names a client-like type, or a `return` builds one."""
    ann = fn.returns
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        name = ann.value.rsplit(".", 1)[-1]
    else:
        name = (ann.attr if isinstance(ann, ast.Attribute) else getattr(ann, "id", "")) or ""
    if name.endswith(CLIENT_SUFFIXES):
        return True
    return any(isinstance(n, ast.Return) and is_client(n.value) for n in ast.walk(fn))


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        tree = mod.tree
        for fn in functions(tree):
            declared = {name: g for g in ast.walk(fn) if isinstance(g, ast.Global) for name in g.names}
            stored = {
                n.id
                for n in ast.walk(fn)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in declared
            }
            hits.extend(
                Hit(mod.path, declared[name].lineno, f"R79 `{fn.name}` rebinds module global `{name}`")
                for name in sorted(stored)
            )
        mutated = mutated_in_functions(tree)
        for name, node in module_bindings(tree):
            if is_container(node.value) and name in mutated:
                hits.append(Hit(mod.path, node.lineno, f"R79 module-level container `{name}` is filled at runtime"))
            elif is_client(node.value):
                hits.append(Hit(mod.path, node.lineno, f"R79 module-level client `{name}` has no owner or lifecycle"))
        for fn in tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if any(called_name(d) in CACHES for d in fn.decorator_list) and returns_client(fn):
                hits.append(Hit(mod.path, fn.lineno, f"R79 `{fn.name}` caches a client it can never close or evict"))
    return hits
