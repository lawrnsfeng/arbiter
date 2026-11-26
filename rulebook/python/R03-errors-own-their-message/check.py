"""R3: messages built outside the exception's constructor, message-choosing constructors, `.format` templates,
silent leaf constructors, and HTTP error responses repeated per status code."""

import ast
import builtins
from collections import defaultdict

from rulekit import Hit, Module, base_name, classes, functions, local_nodes

RULE = "R3"
BUILTIN_EXC = {n for n, v in vars(builtins).items() if isinstance(v, type) and issubclass(v, BaseException)}
# not refusals: abstract stubs and control flow
NOT_ERRORS = {
    "NotImplementedError",
    "StopIteration",
    "StopAsyncIteration",
    "SystemExit",
    "KeyboardInterrupt",
    "GeneratorExit",
}


def exception_classes(modules: list[Module]) -> set[str]:
    """Names of classes deriving, by name and transitively across modules, from an exception."""
    bases = {c.name: {base_name(b) for b in c.bases} for m in modules for c in classes(m.tree)}
    known = {
        n
        for n, bs in bases.items()
        if any(b in BUILTIN_EXC or b.endswith(("Error", "Exception", "Warning")) for b in bs)
    }
    grew = True
    while grew:
        new = {n for n, bs in bases.items() if bs & known} - known
        known |= new
        grew = bool(new)
    return known


def is_text(node: ast.AST) -> bool:
    """A string literal, f-string, string `+` / `%`, or a `.format(...)` / `.join(...)` call."""
    match node:
        case ast.Constant(value=str()) | ast.JoinedStr():
            return True
        case ast.BinOp(op=ast.Add() | ast.Mod()):
            return is_text(node.left) or is_text(node.right)
        case ast.Call(func=ast.Attribute(attr="format" | "join")):
            return True
    return False


def is_init_call(node: ast.AST) -> bool:
    """`super().__init__(...)` or `Base.__init__(self, ...)`."""
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "__init__"


def text_locals(nodes: list[ast.AST]) -> set[str]:
    out: set[str] = set()
    for n in nodes:
        if (
            isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and is_text(n.value)
        ):
            out.add(n.targets[0].id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value and is_text(n.value):
            out.add(n.target.id)
    return out


def passed(call: ast.Call, names: set[str]) -> str | None:
    return next((a.id for a in call.args if isinstance(a, ast.Name) and a.id in names), None)


def init_hits(m: Module, cls: ast.ClassDef, init: ast.FunctionDef | ast.AsyncFunctionDef) -> list[Hit]:
    out: list[Hit] = []
    nodes = local_nodes(init)
    texts = text_locals(nodes)
    calls = [n for n in nodes if is_init_call(n)]
    deciding = [n for n in nodes if isinstance(n, ast.If) and any(is_init_call(c) for c in ast.walk(n))]
    in_if = {id(c) for n in deciding for c in ast.walk(n) if is_init_call(c)}
    tested = {t.id for n in deciding for t in ast.walk(n.test) if isinstance(t, ast.Name)}
    a = init.args
    defaults = [
        *zip(a.args[len(a.args) - len(a.defaults) :], a.defaults, strict=True),
        *zip(a.kwonlyargs, a.kw_defaults, strict=True),
    ]
    # a flag counts only when it decides which `super().__init__` runs; `retryable=False` stored aside is fine
    flags = [
        p.arg for p, d in defaults if isinstance(d, ast.Constant) and isinstance(d.value, bool) and p.arg in tested
    ]
    if flags:
        out.append(
            Hit(
                m.path,
                init.lineno,
                f"{RULE} `{cls.name}.__init__` chooses its message with flag `{flags[0]}`: one class per refusal",
            )
        )
    if not calls:
        out.append(
            Hit(
                m.path,
                init.lineno,
                f"{RULE} `{cls.name}.__init__` never calls `super().__init__`: `str(error)` is empty",
            )
        )
    for c in calls:
        if name := passed(c, texts):
            out.append(
                Hit(
                    m.path,
                    c.lineno,
                    f"{RULE} `{cls.name}` builds its message in local `{name}` before `super().__init__`",
                )
            )
        elif id(c) in in_if:
            out.append(
                Hit(m.path, c.lineno, f"{RULE} `{cls.name}.__init__` picks a message by branch: one class per refusal")
            )
        elif (
            not c.args
            and not c.keywords
            and [p.arg for p in a.args] == ["self"]
            and not (a.vararg or a.kwarg or a.kwonlyargs)
        ):
            out.append(Hit(m.path, c.lineno, f"{RULE} `{cls.name}` passes nothing: drop the `__init__`"))
    return out


def status_of(call: ast.Call) -> object:
    for kw in call.keywords:
        if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
            return kw.value.value
    if call.args and isinstance(call.args[0], ast.Constant):
        return call.args[0].value
    return None


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    excs = exception_classes(modules)
    http: dict[object, list[tuple[str, ast.Call]]] = defaultdict(list)
    defined = {c.name for m in modules for c in classes(m.tree)}
    raisable = BUILTIN_EXC - NOT_ERRORS - defined  # a project class shadowing a builtin name is the project's own
    for m in modules:
        for n in ast.walk(m.tree):
            exc = n.exc.func if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) else getattr(n, "exc", None)
            if isinstance(n, ast.Raise) and isinstance(exc, ast.Name) and exc.id in raisable:
                out.append(Hit(m.path, n.lineno, f"{RULE} raises builtin `{exc.id}`: raise a project error subclass"))
        for fn in functions(m.tree):
            nodes = local_nodes(fn)
            texts = text_locals(nodes)
            out += [
                Hit(m.path, n.lineno, f"{RULE} message `{name}` is built at the raise site: the exception owns it")
                for n in nodes
                if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call) and (name := passed(n.exc, texts))
            ]
        for cls in classes(m.tree):
            if cls.name not in excs:
                continue
            for item in cls.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name == "__init__":
                    out += init_hits(m, cls, item)
            for n in ast.walk(cls):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "format":
                    out.append(
                        Hit(
                            m.path,
                            n.lineno,
                            f"{RULE} `{cls.name}` renders with `.format`: use `string.Template.substitute`",
                        )
                    )
        for n in ast.walk(m.tree):
            if isinstance(n, ast.Call) and base_name(n.func) == "HTTPException" and (code := status_of(n)) is not None:
                http[code].append((m.path, n))
    for code, sites in http.items():
        if len(sites) > 1:
            out += [
                Hit(p, c.lineno, f"{RULE} HTTPException({code}) is built at {len(sites)} sites: subclass it once")
                for p, c in sites
            ]
    return out
