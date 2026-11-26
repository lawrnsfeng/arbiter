"""R57: bare-word boolean names, positional `bool` parameters, and bare `True`/`False` passed positionally."""

import ast

from rulekit import Hit, Module, classes, functions, local_nodes

RULE = "R57"
# callees whose positional bool is a stored value, not a flag that changes behaviour
VALUE_SINKS = {
    "get", "pop", "setdefault", "getattr", "setattr", "append", "add", "appendleft", "insert", "extend", "put", "set",
    "remove", "discard", "index", "count", "isinstance", "bool", "print", "object", "assertEqual", "assertIs",
    "assertNotEqual", "Value", "Constant", "Literal", "fill", "full", "repeat", "where", "send", "update", "write",
}  # fmt: skip


def _is_bool(annotation: ast.expr | None) -> bool:
    """`bool`, `bool | None`, `Optional[bool]`."""
    match annotation:
        case ast.Name(id="bool"):
            return True
        case ast.BinOp(op=ast.BitOr()):
            return _is_bool(annotation.left) or _is_bool(annotation.right)
        case ast.Subscript(value=ast.Name(id="Optional")):
            return _is_bool(annotation.slice)
        case _:
            return False


def _bare(name: str) -> bool:
    """A single lower-case word that does not say what it gates (`off`, `enabled`, `force`)."""
    word: str = name.strip("_")
    return bool(word) and "_" not in word and word.islower()


def _fixed_signature(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """A signature the protocol fixes: a property setter (`@x.setter`) or an `@override`."""
    names: list[str] = [
        d.attr if isinstance(d, ast.Attribute) else d.id if isinstance(d, ast.Name) else "" for d in fn.decorator_list
    ]
    return any(n in {"setter", "override"} for n in names)


def _params(m: Module, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[Hit]:
    out: list[Hit] = []
    positional: list[ast.arg] = [*fn.args.posonlyargs, *fn.args.args]
    for arg in [*positional, *fn.args.kwonlyargs]:
        if not _is_bool(arg.annotation):
            continue
        problems: list[str] = ["is a bare word, not `is_*` or a precise compound"] if _bare(arg.arg) else []
        problems += ["is not keyword-only"] if arg in positional else []
        if problems:
            out.append(Hit(m.path, arg.lineno, f"R57 bool parameter `{arg.arg}` {' and '.join(problems)}"))
    return out


def _attributes(m: Module, cls: ast.ClassDef) -> list[Hit]:
    """First declaration per class of a bare-word boolean attribute: `self.x = True`, `x: bool`, `x = False`."""
    out: list[Hit] = []
    seen: set[str] = set()
    methods: list[ast.AST] = [
        n for fn in cls.body if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) for n in local_nodes(fn)
    ]
    body: set[int] = {id(s) for s in cls.body}
    for node in [*cls.body, *methods]:
        target: ast.expr | None = None
        if isinstance(node, ast.AnnAssign) and _is_bool(node.annotation):
            target = node.target
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, bool)
        ):
            target = node.targets[0]
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
            name: str = target.attr
        elif isinstance(target, ast.Name) and id(node) in body:
            name = target.id
        else:
            continue
        if _bare(name) and name not in seen:
            seen.add(name)
            out.append(Hit(m.path, node.lineno, f"R57 bool attribute `{name}` is a bare word: name what it gates"))
    return out


def _calls(m: Module) -> list[Hit]:
    out: list[Hit] = []
    for call in ast.walk(m.tree):
        if not isinstance(call, ast.Call):
            continue
        f: ast.expr = call.func
        callee: str = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
        if callee in VALUE_SINKS:
            continue
        out += [
            Hit(m.path, arg.lineno, f"R57 positional `{arg.value}` passed to `{callee}`: pass it by keyword")
            for arg in call.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, bool)
        ]
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        for fn in functions(m.tree):
            if not _fixed_signature(fn):
                out += _params(m, fn)
        for cls in classes(m.tree):
            out += _attributes(m, cls)
        out += _calls(m)
    return out
