"""R81: a method on a model-like class that hand-builds a dict of the object's own fields."""

import ast

from rulekit import Hit, Module, classes

RULE = "R81"
Function = ast.FunctionDef | ast.AsyncFunctionDef


def uses_pydantic(modules: list[Module]) -> bool:
    for mod in modules:
        for node in ast.walk(mod.tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "pydantic":
                return True
            if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "pydantic" for a in node.names):
                return True
    return False


def own_fields(cls: ast.ClassDef) -> set[str]:
    fields = {n.target.id for n in cls.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
    for fn in cls.body:
        if isinstance(fn, ast.FunctionDef) and fn.name == "__init__":
            fields |= {
                t.attr
                for n in ast.walk(fn)
                if isinstance(n, ast.Assign | ast.AnnAssign)
                for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self"
            }
    return fields


def reads_field(expr: ast.expr, fields: set[str]) -> bool:
    return any(
        isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self" and n.attr in fields
        for n in ast.walk(expr)
    )


def is_dump(expr: ast.expr | None) -> bool:
    return (
        isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr in {"model_dump", "dict"}
    )


def field_dict(expr: ast.expr | None, fields: set[str]) -> str | None:
    """Why `expr` is a hand-built dict of own fields, or None."""
    if isinstance(expr, ast.Dict):
        if any(k is None and is_dump(v) for k, v in zip(expr.keys, expr.values, strict=True)) and any(expr.keys):
            return "spreads model_dump and overwrites fields"
        values = [v for k, v in zip(expr.keys, expr.values, strict=True) if k is not None]
    elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "dict" and not expr.args:
        values = [k.value for k in expr.keywords if k.arg]
    else:
        return None
    own = sum(reads_field(v, fields) for v in values)
    return "returns a dict literal of its own fields" if own >= 2 and own * 2 >= len(values) else None


def shape(fn: Function, fields: set[str]) -> str | None:
    bound: dict[str, str] = {}
    patched: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if why := field_dict(node.value, fields):
                bound[name] = why
            elif is_dump(node.value):
                bound[name] = "re-dumps the model and overwrites fields"
        elif isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name):
            patched.add(node.value.id)
        elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.BitOr) and isinstance(node.target, ast.Name):
            patched.add(node.target.id)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"update", "setdefault", "pop"}
            and isinstance(node.func.value, ast.Name)
        ):
            patched.add(node.func.value.id)
    for node in ast.walk(fn):
        if not isinstance(node, ast.Return):
            continue
        if why := field_dict(node.value, fields):
            return why
        if isinstance(node.value, ast.Name) and (why := bound.get(node.value.id)):
            if why.startswith("re-dumps") and node.value.id not in patched:
                continue
            return why
    return None


def check(modules: list[Module]) -> list[Hit]:
    if not uses_pydantic(modules):
        return []
    hits: list[Hit] = []
    for mod in modules:
        for cls in classes(mod.tree):
            fields = own_fields(cls)
            if len(fields) < 2:
                continue
            for fn in cls.body:
                is_method = isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) and not fn.name.startswith("__")
                if is_method and (why := shape(fn, fields)):
                    hits.append(Hit(mod.path, fn.lineno, f"R81 `{cls.name}.{fn.name}` {why}: use model_dump"))
    hits += dumped_pydantic_dataclasses(modules)
    return hits


def is_pydantic_dataclass(cls: ast.ClassDef, local_names: set[str]) -> bool:
    """Decorated `@pydantic.dataclasses.dataclass` or with a name imported from `pydantic.dataclasses`."""
    for dec in cls.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Name) and target.id in local_names:
            return True
        if isinstance(target, ast.Attribute) and ast.unparse(target).endswith("dataclasses.dataclass"):
            return "pydantic" in ast.unparse(target)
    return False


def adapted_name(expr: ast.expr | None, adapters: dict[str, str], pdc: set[str]) -> str | None:
    """The pydantic dataclass a `TypeAdapter(...)` expression (or a name bound to one) adapts.

    Generic arguments resolve to the dataclass inside them: `list[X]`, `tuple[X, ...]`, `dict[str, X]`, `X | None`.
    """
    if isinstance(expr, ast.Name):
        return adapters.get(expr.id)
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name | ast.Attribute)
        and (expr.func.id if isinstance(expr.func, ast.Name) else expr.func.attr) == "TypeAdapter"
        and expr.args
    ):
        return next((n.id for n in ast.walk(expr.args[0]) if isinstance(n, ast.Name) and n.id in pdc), None)
    return None


def dumped_pydantic_dataclasses(modules: list[Module]) -> list[Hit]:
    """Owner ruling: a pydantic dataclass that gets dumped (`TypeAdapter(Cls).dump_python/dump_json`) is a BaseModel."""
    pdc: set[str] = set()
    for mod in modules:
        local_names = {
            a.asname or a.name
            for n in ast.walk(mod.tree)
            if isinstance(n, ast.ImportFrom) and n.module == "pydantic.dataclasses"
            for a in n.names
            if a.name == "dataclass"
        }
        pdc |= {c.name for c in classes(mod.tree) if is_pydantic_dataclass(c, local_names)}
    hits: list[Hit] = []
    for mod in modules:
        adapters: dict[str, str] = {}
        for n in ast.walk(mod.tree):
            if isinstance(n, ast.Assign | ast.AnnAssign) and (cls := adapted_name(n.value, {}, pdc)):
                for t in n.targets if isinstance(n, ast.Assign) else [n.target]:
                    if isinstance(t, ast.Name):
                        adapters[t.id] = cls
        for n in ast.walk(mod.tree):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                continue
            if n.func.attr in {"dump_python", "dump_json"} and (cls := adapted_name(n.func.value, adapters, pdc)):
                msg = f"R81 pydantic dataclass `{cls}` is dumped: a dumped model is a BaseModel with model_dump"
                hits.append(Hit(mod.path, n.lineno, msg))
    return hits
