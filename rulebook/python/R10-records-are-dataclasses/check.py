"""R10: dict aliases, TypedDicts, and functions returning fixed-key dict literals as records."""

import ast
from collections import Counter

from rulekit import Hit, Module, classes, functions, local_nodes

RULE = "R10"
DICTS = {"dict", "Dict", "Mapping", "MutableMapping"}
CONVERTERS = {"asdict", "dict", "_asdict"}  # plus every `to_*` / `as_*` name


def last_name(node: ast.expr) -> str:
    return node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""


def loose(value: ast.expr) -> bool:
    """A value type that only a record would need: `object`, `Any`, or a union of types."""
    if isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr):
        return True
    if isinstance(value, ast.Subscript) and last_name(value.value) in {"Union", "Optional"}:
        return True
    return last_name(value) in {"object", "Any"}


def alias_of_dict(value: ast.expr | None) -> bool:
    """`dict[str, object | Any | union]`: string keys name fields of mixed values. `dict[str, Book]` is a lookup map."""
    if not isinstance(value, ast.Subscript) or last_name(value.value) not in DICTS:
        return False
    args = value.slice.elts if isinstance(value.slice, ast.Tuple) else [value.slice]
    return len(args) == 2 and isinstance(args[0], ast.Name) and args[0].id == "str" and loose(args[1])


def fixed_record(node: ast.expr | None) -> bool:
    return (
        isinstance(node, ast.Dict)
        and len(node.keys) >= 2
        and all(isinstance(k, ast.Constant) and isinstance(k.value, str) for k in node.keys)
    )


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    methods = Counter(
        f.name
        for m in modules
        for c in classes(m.tree)
        for f in c.body
        if isinstance(f, ast.FunctionDef | ast.AsyncFunctionDef)
    )
    for m in modules:
        for s in m.tree.body:
            if isinstance(s, ast.TypeAlias) and alias_of_dict(s.value):
                out.append(Hit(m.path, s.lineno, f"{RULE} `{s.name.id}` aliases a dict: make it a dataclass"))
            elif isinstance(s, ast.Assign | ast.AnnAssign) and alias_of_dict(s.value):
                target = s.targets[0] if isinstance(s, ast.Assign) else s.target
                if isinstance(target, ast.Name):
                    out.append(Hit(m.path, s.lineno, f"{RULE} `{target.id}` aliases a dict: make it a dataclass"))
        for n in ast.walk(m.tree):
            if isinstance(n, ast.ClassDef) and any(last_name(b) == "TypedDict" for b in n.bases):
                out.append(Hit(m.path, n.lineno, f"{RULE} `{n.name}` is a TypedDict: make it a dataclass"))
            elif isinstance(n, ast.Call) and last_name(n.func) == "TypedDict":
                out.append(Hit(m.path, n.lineno, f"{RULE} functional TypedDict: make it a dataclass"))
        for fn in functions(m.tree):
            converter = fn.name in CONVERTERS or fn.name.startswith(("to_", "as_"))
            if converter or methods[fn.name] > 1:  # a name several classes define is a framework contract
                continue
            out += [
                Hit(m.path, n.lineno, f"{RULE} `{fn.name}` returns a fixed-key dict: return a dataclass")
                for n in local_nodes(fn)
                if isinstance(n, ast.Return) and fixed_record(n.value)
            ]
    return out
