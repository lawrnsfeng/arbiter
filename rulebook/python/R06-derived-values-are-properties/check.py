"""R6: no-argument methods returning a pure value derived from `self`, and properties doing I/O or printing."""

import ast
import builtins
from collections import Counter

from rulekit import Hit, Module, base_name, classes, local_nodes

RULE = "R6"
PURE = {
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "frozenset", "int", "isinstance", "len", "list",
    "max", "min", "repr", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip",
}  # fmt: skip
IO_NAMES = {"open", "print", "input"}
IO_ATTRS = {
    "read_text", "read_bytes", "write_text", "write_bytes", "readlines", "readline", "echo", "secho",
    "check_output", "check_call", "Popen", "urlopen", "unlink", "mkdir", "rmtree",
}  # fmt: skip
IO_MODULES = {"subprocess", "socket", "shutil"}
HTTP_MODULES = {"requests", "httpx"}
HTTP_VERBS = {"get", "post", "put", "patch", "delete", "head", "request"}
PROPERTY = {"property", "cached_property"}


NEUTRAL_BASES = {"object", "ABC", "Generic"}  # bases that impose no method hooks
BUILTINS = set(dir(builtins))
# value methods on str / Path / containers: deriving with them reads no outer state and does no I/O
PURE_METHODS = {
    "strip", "lstrip", "rstrip", "lower", "upper", "title", "replace", "split", "rsplit", "join", "format",
    "startswith", "endswith", "removeprefix", "removesuffix", "zfill", "joinpath", "with_suffix", "with_name",
    "with_stem", "relative_to", "isoformat", "strftime", "keys", "values", "items", "count", "index",
}  # fmt: skip


def deco_name(d: ast.expr) -> str:
    return d.id if isinstance(d, ast.Name) else d.attr if isinstance(d, ast.Attribute) else ""


def imported(tree: ast.Module) -> set[str]:
    return {
        (a.asname or a.name).split(".")[0]
        for n in ast.walk(tree)
        if isinstance(n, ast.Import | ast.ImportFrom)
        for a in n.names
    }


def pure_return(fn: ast.FunctionDef, stated: set[str]) -> bool:
    """A single `return` deriving from `self` that reads no outer-scope variable: every other name is a builtin, an
    imported name, an UPPER_CASE constant or a comprehension variable; calls are pure builtins, imported constructors
    (`Path(...)`) or value methods (`.strip()`, `.joinpath()`, ...)."""
    body = fn.body[1:] if ast.get_docstring(fn) is not None else fn.body
    if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
        return False
    nodes = list(ast.walk(body[0].value))
    bound = {
        t.id for n in nodes if isinstance(n, ast.comprehension) for t in ast.walk(n.target) if isinstance(t, ast.Name)
    }
    names = {n.id for n in nodes if isinstance(n, ast.Name)}
    if "self" not in names or any(not (x in stated or x in bound or x == "self" or x.isupper()) for x in names):
        return False
    for c in (n for n in nodes if isinstance(n, ast.Call)):
        f = c.func
        if isinstance(f, ast.Name) and (f.id in PURE or (f.id in stated and f.id[:1].isupper())):
            continue
        if isinstance(f, ast.Attribute) and f.attr in PURE_METHODS:
            continue
        return False
    return True


def io_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    if isinstance(f, ast.Name):
        return f.id in IO_NAMES
    if isinstance(f, ast.Attribute):
        mod = f.value.id if isinstance(f.value, ast.Name) else ""
        return f.attr in IO_ATTRS or mod in IO_MODULES or (mod in HTTP_MODULES and f.attr in HTTP_VERBS)
    return False


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    methods = [(m, c, fn) for m in modules for c in classes(m.tree) for fn in c.body if isinstance(fn, ast.FunctionDef)]
    defined = Counter(fn.name for _, _, fn in methods)
    stated = {id(m): imported(m.tree) | BUILTINS for m in modules}
    owned = {c.name for m in modules for c in classes(m.tree)} | NEUTRAL_BASES
    for m, c, fn in methods:
        # a class with an outside base may be filling that framework's method hook: only scan our own classes
        own = all(base_name(b.value if isinstance(b, ast.Subscript) else b) in owned for b in c.bases)
        decos = {deco_name(d) for d in fn.decorator_list}
        if decos & PROPERTY:
            out += [
                Hit(m.path, n.lineno, f"{RULE} property `{c.name}.{fn.name}` does I/O: make it a verb-named method")
                for n in local_nodes(fn)
                if io_call(n)
            ]
            continue
        a = fn.args
        only_self = [p.arg for p in a.args] == ["self"] and not (a.posonlyargs or a.vararg or a.kwonlyargs or a.kwarg)
        if (
            own
            and not decos
            and only_self
            and not fn.name.startswith(("__", "to_", "as_"))  # `as_dict()`-style conversions are methods by convention
            and defined[fn.name] == 1
            and pure_return(fn, stated[id(m)])
        ):
            out.append(
                Hit(m.path, fn.lineno, f"{RULE} `{c.name}.{fn.name}()` derives a value from `self`: make it a property")
            )
    return out
