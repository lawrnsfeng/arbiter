"""R26: data-only never-dumped BaseModel, unfrozen pydantic dataclasses, per-call TypeAdapter, isinstance ladders,
nested raw access, bare ValueError in validators.
"""

import ast
from collections.abc import Iterator

from rulekit import Hit, Module, classes, functions, local_nodes

RULE = "R26"
_VALIDATOR_DECORATORS = {"field_validator", "model_validator", "validator", "root_validator"}
_VALIDATOR_WRAPPERS = {"BeforeValidator", "AfterValidator", "PlainValidator", "WrapValidator"}
_DUMPS = {"model_dump", "model_dump_json", "dict", "json", "model_json_schema"}
_CONSTRAINTS = {
    "gt", "ge", "lt", "le", "multiple_of", "min_length", "max_length", "pattern", "max_digits", "decimal_places",
    "strict", "allow_inf_nan", "union_mode",
}  # fmt: skip


def _last(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else None


def _str_key(node: ast.AST) -> tuple[ast.expr, str] | None:
    """(target, key) for `x["k"]` (load) or `x.get("k", ...)`, else None."""
    if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load):
        key, target = node.slice, node.value
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
        key, target = node.args[0], node.func.value
    else:
        return None
    return (target, key.value) if isinstance(key, ast.Constant) and isinstance(key.value, str) else None


def _imports_pydantic(tree: ast.Module) -> tuple[bool, set[str]]:
    """Whether the module imports pydantic, and the local names bound to pydantic's dataclass decorator."""
    uses, dataclass_names = False, set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "pydantic" for a in n.names):
            uses = True
        elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "pydantic":
            uses = True
            if n.module == "pydantic.dataclasses":
                dataclass_names |= {a.asname or a.name for a in n.names if a.name == "dataclass"}
    return uses, dataclass_names


def _pydantic_dataclass(dec: ast.expr, names: set[str]) -> bool:
    target = dec.func if isinstance(dec, ast.Call) else dec
    if isinstance(target, ast.Name):
        return target.id in names
    return ast.unparse(target).endswith("pydantic.dataclasses.dataclass")


def _frozen(dec: ast.expr) -> bool:
    return isinstance(dec, ast.Call) and any(
        k.arg == "frozen" and isinstance(k.value, ast.Constant) and k.value.value is True for k in dec.keywords
    )


def _ladder(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int | None:
    """Line of the first isinstance check when two or more check different keys of one dict."""
    nodes = local_nodes(fn)
    bound: dict[str, tuple[str, str]] = {}
    for n in nodes:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            found = _str_key(n.value)
            if found and isinstance(found[0], ast.Name):
                bound[n.targets[0].id] = (found[0].id, found[1])
    keys: dict[str, dict[str, int]] = {}
    for n in nodes:
        if not (isinstance(n, ast.Call) and _last(n.func) == "isinstance" and n.args):
            continue
        arg = n.args[0]
        found = _str_key(arg)
        if found and isinstance(found[0], ast.Name):
            ref = (found[0].id, found[1])
        elif isinstance(arg, ast.Name) and arg.id in bound:
            ref = bound[arg.id]
        else:
            continue
        keys.setdefault(ref[0], {}).setdefault(ref[1], n.lineno)
    lines = [min(seen.values()) for seen in keys.values() if len(seen) >= 2]
    return min(lines) if lines else None


def _validators(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    wrapped = {
        a.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and _last(n.func) in _VALIDATOR_WRAPPERS
        for a in n.args
        if isinstance(a, ast.Name)
    }
    return [
        fn
        for fn in functions(tree)
        if fn.name in wrapped or any(_last(d) in _VALIDATOR_DECORATORS for d in fn.decorator_list)
    ]


def _nested(tree: ast.Module) -> list[ast.Subscript]:
    """Outermost `x["a"]["b"]` chains."""
    chains = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Subscript) and _str_key(n) and isinstance(n.value, ast.Subscript) and _str_key(n.value)
    ]
    inner = {id(n.value) for n in chains}
    return [n for n in chains if id(n) not in inner]


def _constrained_field(stmt: ast.stmt) -> bool:
    """A field whose value or `Annotated[...]` metadata is `Field(...)` with a validation constraint."""
    if not isinstance(stmt, ast.AnnAssign):
        return False
    parts = [stmt.annotation, *([stmt.value] if stmt.value is not None else [])]
    return any(
        isinstance(n, ast.Call) and _last(n.func) == "Field" and any(k.arg in _CONSTRAINTS for k in n.keywords)
        for part in parts
        for n in ast.walk(part)
    )


def _needs_model(cls: ast.ClassDef) -> bool:
    """True when the class body shows a BaseModel need: validators, `model_config`, an inner `Config`, or `Field`
    constraints on its fields."""
    for stmt in cls.body:
        if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef) and any(
            _last(d) in _VALIDATOR_DECORATORS for d in stmt.decorator_list
        ):
            return True
        if isinstance(stmt, ast.ClassDef) and stmt.name == "Config":
            return True
        if _constrained_field(stmt):
            return True
        targets = (
            stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target] if isinstance(stmt, ast.AnnAssign) else []
        )
        if any(isinstance(t, ast.Name) and t.id == "model_config" for t in targets):
            return True
    return False


def _dumped(modules: list[Module]) -> set[str]:
    """Names of models that get dumped: every name in a module calling `.model_dump()` / `.dict()` / `.json()` ...,
    every name in a `response_model=` keyword, and every name in a decorated (route) function's return annotation."""
    names: set[str] = set()
    for m in modules:
        nodes = list(ast.walk(m.tree))
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in _DUMPS for n in nodes):
            names |= {n.id for n in nodes if isinstance(n, ast.Name)}
            names |= {n.name for n in nodes if isinstance(n, ast.ClassDef)}
        framework: list[ast.AST] = [n.value for n in nodes if isinstance(n, ast.keyword) and n.arg == "response_model"]
        framework += [
            n.returns
            for n in nodes
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
            and n.returns is not None
            and any(isinstance(d, ast.Call) for d in n.decorator_list)
        ]
        names |= {x.id for f in framework for x in ast.walk(f) if isinstance(x, ast.Name)}
        names |= {x.attr for f in framework for x in ast.walk(f) if isinstance(x, ast.Attribute)}
    return names


def _module_hits(m: Module, dumped: set[str]) -> Iterator[Hit]:
    uses, dc_names = _imports_pydantic(m.tree)
    for cls in classes(m.tree):
        base_model = uses and any(_last(b) == "BaseModel" for b in cls.bases)
        if base_model and cls.name not in dumped and not _needs_model(cls):
            yield Hit(m.path, cls.lineno, f"{RULE} data-only `{cls.name}` is never dumped; use a pydantic dataclass")
        for dec in cls.decorator_list:
            if _pydantic_dataclass(dec, dc_names) and not _frozen(dec):
                yield Hit(m.path, cls.lineno, f"{RULE} pydantic dataclass `{cls.name}` is not frozen")
    for fn in functions(m.tree):
        for n in local_nodes(fn):
            if isinstance(n, ast.Call) and _last(n.func) == "TypeAdapter":
                yield Hit(m.path, n.lineno, f"{RULE} TypeAdapter built per call in `{fn.name}`; build it once")
        if (line := _ladder(fn)) is not None:
            yield Hit(m.path, line, f"{RULE} isinstance ladder over dict keys in `{fn.name}`; parse into a record")
    for n in _nested(m.tree):
        yield Hit(m.path, n.lineno, f"{RULE} blind nested access `{ast.unparse(n)}`; parse into a record")
    for fn in _validators(m.tree):
        for n in local_nodes(fn):
            if isinstance(n, ast.Raise) and n.exc is not None and _last(n.exc) == "ValueError":
                yield Hit(m.path, n.lineno, f"{RULE} bare ValueError in validator `{fn.name}`; raise a subclass")


def check(modules: list[Module]) -> list[Hit]:
    dumped = _dumped(modules)
    return [hit for m in modules for hit in _module_hits(m, dumped)]
