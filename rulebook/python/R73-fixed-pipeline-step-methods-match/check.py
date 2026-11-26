"""R73: StrEnum order comparisons, IntEnum name converters, step registries, and attributes attached to functions."""

import ast

from rulekit import Hit, Module, classes, functions, local_nodes, params_of

RULE = "R73"
ORDERING = (ast.Lt, ast.Gt, ast.LtE, ast.GtE)


def base_names(cls: ast.ClassDef) -> set[str]:
    return {b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in cls.bases}


def enum_kind(cls: ast.ClassDef) -> str | None:
    bases = base_names(cls)
    if "StrEnum" in bases or {"str", "Enum"} <= bases:
        return "str"
    if "IntEnum" in bases or {"int", "Enum"} <= bases:
        return "int"
    return None


def converts_names(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """A non-dunder method mapping members to or from their names (`self.name`, `cls[text]`, `__members__`)."""
    if fn.name.startswith("__") and fn.name.endswith("__"):
        return False
    receivers = {a.arg for a in params_of(fn)[:1]}
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Attribute | ast.Subscript) and isinstance(n.value, ast.Name)):
            continue
        if n.value.id in receivers and (isinstance(n, ast.Subscript) or n.attr in {"name", "__members__"}):
            return True
    return False


def enum_hits(m: Module, str_enums: set[str], int_enums: list[ast.ClassDef]) -> list[Hit]:
    hits = []
    for node in ast.walk(m.tree):
        if isinstance(node, ast.Compare) and any(isinstance(op, ORDERING) for op in node.ops):
            operands = [node.left, *node.comparators]
            if any(
                isinstance(o, ast.Attribute) and isinstance(o.value, ast.Name) and o.value.id in str_enums
                for o in operands
            ):
                hits.append(Hit(m.path, node.lineno, f"{RULE} StrEnum members compared with < / >: compare `.order`"))
    hits.extend(
        Hit(m.path, fn.lineno, f"{RULE} IntEnum `{cls.name}.{fn.name}` converts names: use an ordered StrEnum")
        for cls in int_enums
        for fn in cls.body
        if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) and converts_names(fn)
    )
    return hits


def registries(m: Module, defs: set[str]) -> dict[str, bool]:
    """Module-level step registries -> True when the registry is a dict."""
    found = {}
    for stmt in m.tree.body:
        if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)):
            continue
        value = stmt.value
        items = (
            value.values
            if isinstance(value, ast.Dict)
            else getattr(value, "elts", [])
            if isinstance(value, ast.Tuple | ast.List)
            else []
        )
        if sum(1 for i in items if isinstance(i, ast.Name) and i.id in defs) >= 2:
            found[stmt.targets[0].id] = isinstance(value, ast.Dict)
    return found


def registry_hits(m: Module, defs: set[str]) -> list[Hit]:
    """Loops over a step registry; key dispatch through a registry that is also iterated (a pipeline, not a table)."""
    regs = registries(m, defs)
    looped: dict[str, list[ast.AST]] = {}
    keyed: dict[str, list[ast.AST]] = {}
    for node in ast.walk(m.tree):
        if isinstance(node, ast.For | ast.AsyncFor):
            it = node.iter
            if isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute) and it.func.attr in {"items", "values"}:
                it = it.func.value
            if isinstance(it, ast.Name) and it.id in regs:
                looped.setdefault(it.id, []).append(node)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Subscript):
            target = node.func.value
            if isinstance(target, ast.Name) and regs.get(target.id):
                keyed.setdefault(target.id, []).append(node)
    hits = [
        Hit(m.path, node.lineno, f"{RULE} loop over step registry `{name}`: use one match driver")
        for name, nodes in looped.items()
        for node in nodes
    ]
    hits += [
        Hit(m.path, node.lineno, f"{RULE} string-dispatched step through `{name}`: use one match driver")
        for name, nodes in keyed.items()
        if name in looped
        for node in nodes
    ]
    return hits


def decorator_names(m: Module) -> set[str]:
    names = set()
    for fn in functions(m.tree):
        for deco in fn.decorator_list:
            target = deco.func if isinstance(deco, ast.Call) else deco
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def attached(node: ast.AST, owners: set[str]) -> bool:
    targets = (
        node.targets
        if isinstance(node, ast.Assign)
        else [node.target]
        if isinstance(node, ast.AnnAssign | ast.AugAssign)
        else []
    )
    return any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id in owners for t in targets)


def attachment_hits(m: Module, defs: set[str]) -> list[Hit]:
    hits = [
        Hit(m.path, stmt.lineno, f"{RULE} attribute attached to a function: fold it into the match arm")
        for stmt in m.tree.body
        if attached(stmt, defs)
    ]
    used = decorator_names(m)
    for fn in functions(m.tree):
        if fn.name not in used:
            continue
        params = {a.arg for a in params_of(fn)}
        hits.extend(
            Hit(m.path, node.lineno, f"{RULE} marker decorator `{fn.name}` attaches attributes to functions")
            for node in local_nodes(fn)
            if attached(node, params)
        )
    return hits


def check(modules: list[Module]) -> list[Hit]:
    all_classes = [cls for m in modules for cls in classes(m.tree)]
    str_enums = {cls.name for cls in all_classes if enum_kind(cls) == "str"}
    hits = []
    for m in modules:
        int_enums = [cls for cls in classes(m.tree) if enum_kind(cls) == "int"]
        defs = {n.name for n in m.tree.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
        hits += enum_hits(m, str_enums, int_enums) + registry_hits(m, defs) + attachment_hits(m, defs)
    return hits
