"""R67: two or more `isinstance` tests on one subject in an if-ladder; a class-pattern `match` without `case _`."""

import ast

from rulekit import Hit, Module, functions, local_nodes, params_of

RULE = "R67"


def isinstance_subject(test: ast.expr) -> str | None:
    call = test if isinstance(test, ast.Call) and isinstance(test.func, ast.Name) else None
    if call is not None and call.func.id == "isinstance" and len(call.args) == 2:
        return ast.dump(call.args[0])
    return None


def chain(node: ast.If) -> list[ast.If]:
    out = [node]
    while len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
        node = node.orelse[0]
        out.append(node)
    return out


def terminates(node: ast.If) -> bool:
    """Every branch of the chain leaves the block, so a following `if` behaves as an `elif`."""
    return all(
        n.body and isinstance(n.body[-1], ast.Return | ast.Raise | ast.Continue | ast.Break) for n in chain(node)
    )


def ladder_hits(m: Module, body: list[ast.stmt], seen: set[int]) -> list[Hit]:
    hits = []
    runs: list[list[ast.If]] = [[]]
    for stmt in body:
        if isinstance(stmt, ast.If) and id(stmt) not in seen:
            runs[-1].extend(chain(stmt))
            if terminates(stmt):
                continue
        runs.append([])
    for run in runs:
        seen.update(id(node) for node in run)
        first: dict[str, ast.If] = {}
        count: dict[str, int] = {}
        for node in run:
            if (subject := isinstance_subject(node.test)) is not None:
                first.setdefault(subject, node)
                count[subject] = count.get(subject, 0) + 1
        for subject, node in first.items():
            if count[subject] >= 2:
                text = ast.unparse(node.test.args[0])
                hits.append(
                    Hit(m.path, node.lineno, f"{RULE} isinstance ladder on `{text}`: use `match` with class patterns")
                )
    return hits


def is_wildcard(case: ast.match_case) -> bool:
    return isinstance(case.pattern, ast.MatchAs) and case.pattern.pattern is None and case.guard is None


def closed_unions(modules: list[Module]) -> set[str]:
    """Names bound to a union of types (`type Shape = A | B`, `Shape = Union[A, B]`): a closed set R52 decides."""
    names = set()
    for m in modules:
        for node in ast.walk(m.tree):
            if isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
                target, value = node.name.id, node.value
            elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target, value = node.targets[0].id, node.value
            else:
                continue
            union = isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr)
            if union or (isinstance(value, ast.Subscript) and getattr(value.value, "id", "") == "Union"):
                names.add(target)
    return names


def open_subject(fn: ast.FunctionDef | ast.AsyncFunctionDef, node: ast.Match, closed: set[str]) -> bool:
    """The subject is a parameter whose annotation is missing or not a union: its type is not a closed set."""
    if not isinstance(node.subject, ast.Name):
        return False
    param = next((p for p in params_of(fn) if p.arg == node.subject.id), None)
    if param is None:
        return False
    ann = param.annotation
    if ann is None:
        return True
    if isinstance(ann, ast.BinOp) or (isinstance(ann, ast.Name) and ann.id in closed):
        return False
    return not (isinstance(ann, ast.Subscript) and getattr(ann.value, "id", "") in {"Union", "Literal"})


def match_hits(m: Module, closed: set[str]) -> list[Hit]:
    hits = []
    for fn in functions(m.tree):
        for node in local_nodes(fn):
            if not isinstance(node, ast.Match) or not open_subject(fn, node, closed):
                continue
            has_class = any(isinstance(p, ast.MatchClass) for case in node.cases for p in ast.walk(case.pattern))
            if has_class and not any(is_wildcard(case) for case in node.cases):
                hits.append(
                    Hit(m.path, node.lineno, f"{RULE} class-pattern `match` on an open type has no `case _:` arm")
                )
    return hits


def check(modules: list[Module]) -> list[Hit]:
    closed = closed_unions(modules)
    hits = []
    for m in modules:
        seen: set[int] = set()
        for node in ast.walk(m.tree):
            for field in ("body", "orelse", "finalbody"):
                body = getattr(node, field, None)
                if isinstance(body, list) and body and isinstance(body[0], ast.stmt):
                    hits.extend(ladder_hits(m, body, seen))
        hits.extend(match_hits(m, closed))
    return hits
