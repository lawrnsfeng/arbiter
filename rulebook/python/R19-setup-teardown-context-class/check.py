"""R19: a @contextmanager generator whose callers each repeat the same first steps on the yielded value."""

import ast
from collections import Counter

from rulekit import Hit, Module, functions

RULE = "R19"
_DECORATORS = {"contextmanager", "asynccontextmanager"}
_STEPS = 2  # repeated leading steps that make a caller pattern


def _name(node: ast.AST) -> str | None:
    """Last name of a (called) dotted expression: `contextlib.contextmanager` -> `contextmanager`."""
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else None


def _steps(body: list[ast.stmt], bound: str) -> tuple[str, ...]:
    """The first calls the block makes on `bound`: `.method` calls on it, or calls that receive it."""
    calls = sorted(
        (n for stmt in body for n in ast.walk(stmt) if isinstance(n, ast.Call)),
        key=lambda n: (n.lineno, n.col_offset),
    )
    steps = []
    for call in calls:
        func = call.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == bound:
            steps.append(f".{func.attr}()")
        elif any(isinstance(a, ast.Name) and a.id == bound for a in call.args):
            steps.append(f"{ast.unparse(func)}()")
    return tuple(steps[:_STEPS])


def check(modules: list[Module]) -> list[Hit]:
    generators: dict[str, tuple[str, int]] = {}
    for m in modules:
        for fn in functions(m.tree):
            if any(_name(d) in _DECORATORS for d in fn.decorator_list):
                generators[fn.name] = (m.path, fn.lineno)

    uses: dict[str, Counter[tuple[str, ...]]] = {}
    for m in modules:
        for node in ast.walk(m.tree):
            if not isinstance(node, ast.With | ast.AsyncWith):
                continue
            for item in node.items:
                name = _name(item.context_expr) if isinstance(item.context_expr, ast.Call) else None
                if name in generators and isinstance(item.optional_vars, ast.Name):
                    steps = _steps(node.body, item.optional_vars.id)
                    if len(steps) == _STEPS:
                        uses.setdefault(name, Counter())[steps] += 1

    hits = []
    for name, seen in uses.items():
        steps, count = seen.most_common(1)[0]
        if count >= 2:
            path, line = generators[name]
            hits.append(Hit(path, line, f"{RULE} `{name}` callers each repeat {' then '.join(steps)}; make it a class"))
    return hits
