"""R29: `*_path` members built as strings, str() conversions of them in subprocess argv, and self-only `*_path`
methods that should be properties.
"""

import ast
import builtins

from rulekit import Hit, Module, functions, local_nodes, params_of

RULE = "R29"
_SUBPROCESS = {"run", "call", "check_call", "check_output", "Popen"}
_SEPARATORS = ("/", "\\")


def _path_name(node: ast.AST) -> str | None:
    """The `*_path` name an expression refers to (`x_path`, `self.x_path`, `self.x_path()`), else None."""
    if isinstance(node, ast.Call):
        node = node.func
    name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else ""
    return name if name.endswith("_path") else None


def _pathlike(node: ast.AST) -> bool:
    """A pathlib value: `a / b`, `Path(...)`, or a name ending in `_path` / `_dir`."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return True
    if isinstance(node, ast.Call):
        return ast.unparse(node.func).rsplit(".", 1)[-1] in {"Path", "PurePath", "PosixPath", "WindowsPath"}
    name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else ""
    return name.endswith(("_path", "_dir"))


def _string_path(node: ast.AST | None) -> bool:
    """True for a filesystem path built as a str, rooted at a value (a route starting with a literal `/` is not)."""
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "str":
            return bool(node.args) and _pathlike(node.args[0])
        return isinstance(func, ast.Attribute) and ast.unparse(func.value) == "os.path"
    if isinstance(node, ast.JoinedStr):
        parts = node.values
        return (
            bool(parts)
            and isinstance(parts[0], ast.FormattedValue)
            and any(
                isinstance(p, ast.Constant) and isinstance(p.value, str) and p.value.startswith(_SEPARATORS)
                for p in parts[1:]
            )
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        right = node.right
        return (
            not isinstance(node.left, ast.Constant)
            and isinstance(right, ast.Constant)
            and isinstance(right.value, str)
            and right.value.startswith(_SEPARATORS)
        )
    return False


def _member_target(node: ast.expr, module_level: bool) -> str | None:
    """`*_path` attribute targets anywhere; plain names only at module or class level."""
    if isinstance(node, ast.Attribute) or (module_level and isinstance(node, ast.Name)):
        return _path_name(node)
    return None


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for fn in functions(m.tree):
            nodes = local_nodes(fn)
            if fn.name.endswith("_path"):
                hits += [
                    Hit(m.path, n.lineno, f"{RULE} `{fn.name}` builds its path as a str; return a pathlib.Path")
                    for n in nodes
                    if isinstance(n, ast.Return) and _string_path(n.value)
                ]
            for n in nodes:
                if isinstance(n, ast.Assign) and _string_path(n.value):
                    for t in n.targets:
                        if name := _member_target(t, module_level=False):
                            hits.append(
                                Hit(m.path, n.lineno, f"{RULE} `{name}` holds a str path; store a pathlib.Path")
                            )
        holders = [m.tree, *(n for n in ast.walk(m.tree) if isinstance(n, ast.ClassDef))]
        for holder in holders:
            for stmt in holder.body:
                if isinstance(stmt, ast.Assign) and _string_path(stmt.value):
                    for t in stmt.targets:
                        if name := _member_target(t, module_level=True):
                            hits.append(
                                Hit(m.path, stmt.lineno, f"{RULE} `{name}` holds a str path; store a pathlib.Path")
                            )
        for n in ast.walk(m.tree):
            if not (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "subprocess"
                and n.func.attr in _SUBPROCESS
                and n.args
                and isinstance(n.args[0], ast.List | ast.Tuple)
            ):
                continue
            for arg in n.args[0].elts:
                if (
                    isinstance(arg, ast.Call)
                    and ast.unparse(arg.func) in {"str", "os.fspath"}
                    and arg.args
                    and _path_name(arg.args[0])
                ):
                    hits.append(
                        Hit(m.path, arg.lineno, f"{RULE} `{ast.unparse(arg)}` in subprocess argv; pass the Path")
                    )
        hits += _should_be_property(m)
    return hits


def _module_names(tree: ast.Module) -> set[str]:
    """Module names a property may read: imports, defs, classes and UPPER_CASE constants."""
    names = set(dir(builtins))
    for stmt in tree.body:
        if isinstance(stmt, ast.Import | ast.ImportFrom):
            names |= {(a.asname or a.name).split(".")[0] for a in stmt.names}
        elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(stmt.name)
        elif isinstance(stmt, ast.Assign | ast.AnnAssign):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            names |= {t.id for t in targets if isinstance(t, ast.Name) and t.id.isupper()}
    return names


_PURE_BUILTINS = {
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "frozenset", "int", "isinstance", "len", "list",
    "max", "min", "repr", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip",
}  # fmt: skip
_VALUE_METHODS = {
    "strip", "lstrip", "rstrip", "lower", "upper", "title", "replace", "split", "rsplit", "join", "format",
    "startswith", "endswith", "removeprefix", "removesuffix", "zfill", "joinpath", "with_suffix", "with_name",
    "with_stem", "relative_to", "isoformat", "strftime", "keys", "values", "items", "count", "index",
}  # fmt: skip


def _pure_call(call: ast.Call, allowed: set[str]) -> bool:
    """A call a pure derivation may make: a pure builtin, an imported/defined constructor (`Path(...)`), or a value
    method (`.with_suffix()`, `.joinpath()`, ...). Anything else may do I/O, so the member stays a method."""
    f = call.func
    if isinstance(f, ast.Name):
        return f.id in _PURE_BUILTINS or (f.id in allowed and f.id[:1].isupper())
    return isinstance(f, ast.Attribute) and f.attr in _VALUE_METHODS


def _should_be_property(m: Module) -> list[Hit]:
    """Undecorated `*_path` methods taking only `self` and reading no outer-scope variable (owner ruling)."""
    allowed = _module_names(m.tree)
    hits = []
    for cls in (n for n in ast.walk(m.tree) if isinstance(n, ast.ClassDef)):
        for fn in cls.body:
            if not isinstance(fn, ast.FunctionDef) or not fn.name.endswith("_path") or fn.decorator_list:
                continue
            a = fn.args
            if a.posonlyargs or a.vararg or a.kwonlyargs or a.kwarg or len(a.args) != 1:
                continue
            nodes = [n for n in ast.walk(fn) if n is not fn]
            local = {a.args[0].arg} | {
                n.id for n in nodes if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store | ast.Del)
            }
            local |= {p.arg for n in nodes if isinstance(n, ast.Lambda) for p in params_of(n)}
            reads = {n.id for n in nodes if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
            if reads <= local | allowed and all(_pure_call(c, allowed) for c in nodes if isinstance(c, ast.Call)):
                hits.append(Hit(m.path, fn.lineno, f"{RULE} `{fn.name}` derives only from self; make it a @property"))
    return hits
