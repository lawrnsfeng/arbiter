"""R53: code->object dispatch as an `==` ladder, or as a module-level dict read by a free function."""

import ast

from rulekit import Hit, Module

RULE = "R53"
ENUMERATING_METHODS = {"items", "keys", "values"}
ENUMERATING_CALLS = {"list", "tuple", "set", "sorted", "frozenset", "iter", "enumerate", "len"}


def _code_test(test: ast.expr) -> str | None:
    """The subject of `subject == <literal>` (either side); None otherwise."""
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
        return None
    left, right = test.left, test.comparators[0]
    if isinstance(right, ast.Constant) and not isinstance(left, ast.Constant):
        return ast.dump(left)
    if isinstance(left, ast.Constant) and not isinstance(right, ast.Constant):
        return ast.dump(right)
    return None


def _selects(body: list[ast.stmt]) -> bool:
    """A branch that does nothing but return or raise the selected object: an exception, a class, a builder, a member.

    Returning a number, `None`, a bool or arithmetic (`return 0`, `return n * 2`) computes a value, as in a
    recursion's base cases; a returned string is a message or label the code selects."""
    if len(body) != 1:
        return False
    stmt: ast.stmt = body[0]
    if isinstance(stmt, ast.Raise):
        return stmt.exc is not None
    value: ast.expr | None = stmt.value if isinstance(stmt, ast.Return) else None
    if isinstance(value, ast.Constant):
        return isinstance(value.value, str | bytes)  # a message or label selected by the code
    return isinstance(value, ast.Name | ast.Attribute | ast.Call)


def _branches(stmt: ast.If) -> list[ast.If]:
    chain: list[ast.If] = [stmt]
    while len(chain[-1].orelse) == 1 and isinstance(chain[-1].orelse[0], ast.If):
        chain.append(chain[-1].orelse[0])
    return chain


def _ladders(m: Module, stmts: list[ast.stmt]) -> list[Hit]:
    """Runs of two or more `subject == literal` branches (elif chains and sibling ifs) that each return/raise."""
    out: list[Hit] = []
    key: str | None = None
    start: ast.If | None = None
    length: int = 0
    for stmt in [*stmts, None]:
        for branch in _branches(stmt) if isinstance(stmt, ast.If) else [None]:
            subject: str | None = _code_test(branch.test) if branch and _selects(branch.body) else None
            if subject is not None and subject == key:
                length += 1
                continue
            if start is not None and length >= 2:
                out.append(
                    Hit(m.path, start.lineno, f"R53 {length}-arm `==` dispatch ladder: one named `match` owns it")
                )
            key, start, length = subject, branch if subject else None, 1
    return out


def _enumerated(modules: list[Module]) -> set[str]:
    """Names iterated as a whole anywhere: `for _ in NAME`, `NAME.items()`, `list(NAME)`, ..."""
    names: set[str] = set()
    for m in modules:
        for n in ast.walk(m.tree):
            if isinstance(n, ast.For | ast.comprehension) and isinstance(n.iter, ast.Name):
                names.add(n.iter.id)
            elif isinstance(n, ast.Call):
                f: ast.expr = n.func
                if isinstance(f, ast.Attribute) and f.attr in ENUMERATING_METHODS and isinstance(f.value, ast.Name):
                    names.add(f.value.id)
                elif isinstance(f, ast.Name) and f.id in ENUMERATING_CALLS:
                    names |= {a.id for a in n.args if isinstance(a, ast.Name)}
    return names


def _reader_of(fn: ast.stmt, dicts: dict[str, ast.Dict]) -> tuple[str, bool] | None:
    """(dict name, read with a default/fallback) when `fn` only returns `NAME.get(...)` or `NAME[...]`."""
    if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
        return None
    body: list[ast.stmt] = fn.body[1:] if ast.get_docstring(fn) is not None else fn.body
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return None
    value: ast.expr | None = body[0].value
    if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name) and value.value.id in dicts:
        return value.value.id, False
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "get"
        and isinstance(value.func.value, ast.Name)
        and value.func.value.id in dicts
    ):
        return value.func.value.id, True
    return None


def _pairs(m: Module, enumerated: set[str]) -> list[Hit]:
    out: list[Hit] = []
    dicts: dict[str, ast.Dict] = {}
    for stmt in m.tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target, value = stmt.targets[0], stmt.value
        elif isinstance(stmt, ast.AnnAssign):
            target, value = stmt.target, stmt.value
        else:
            continue
        if isinstance(target, ast.Name) and isinstance(value, ast.Dict):
            dicts[target.id] = value
    for stmt in m.tree.body:
        found: tuple[str, bool] | None = _reader_of(stmt, dicts)
        if found is None or found[0] in enumerated:
            continue
        name, fallback = found
        if len(dicts[name].keys) > 8 and not fallback:
            continue  # pure data lookup table: allowed
        out.append(
            Hit(m.path, stmt.lineno, f"R53 free function only reads mapping `{name}`: one `match` on the owning type")
        )
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    enumerated: set[str] = _enumerated(modules)
    for m in modules:
        elifs: set[int] = {
            id(n.orelse[0])
            for n in ast.walk(m.tree)
            if isinstance(n, ast.If) and len(n.orelse) == 1 and isinstance(n.orelse[0], ast.If)
        }
        for node in ast.walk(m.tree):
            for field in ("body", "orelse", "finalbody"):
                stmts: object = getattr(node, field, None)
                if isinstance(stmts, list) and stmts and isinstance(stmts[0], ast.stmt) and id(stmts[0]) not in elifs:
                    out += _ladders(m, stmts)
        out += _pairs(m, enumerated)
    return out
