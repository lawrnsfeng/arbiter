"""R65: a frozen dataclass constructed at three or more sites that repeat the same two or more arguments.

Arguments are compared by meaning, not spelling: a name bound by a function (parameter or local) counts as the
same argument only inside that function, an attribute of `self` only inside one class, and a module-level name
anywhere in its module.
"""

import ast
from collections import Counter
from functools import cache
from itertools import combinations

from rulekit import Hit, Module, local_nodes, params_of

RULE = "R65"
MIN_SITES = 3
MIN_SHARED = 2
type Scope = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module
type Arg = tuple[int, str, str]


def is_frozen_dataclass(cls: ast.ClassDef) -> bool:
    for deco in cls.decorator_list:
        if not isinstance(deco, ast.Call):
            continue
        name = deco.func.id if isinstance(deco.func, ast.Name) else getattr(deco.func, "attr", "")
        frozen = any(
            kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in deco.keywords
        )
        if name == "dataclass" and frozen:
            return True
    return False


def root(node: ast.expr) -> str | None:
    while isinstance(node, ast.Attribute | ast.Subscript | ast.Call):
        node = node.func if isinstance(node, ast.Call) else node.value
    return node.id if isinstance(node, ast.Name) else None


class Sites:
    """Every call to a frozen dataclass, with each argument keyed by the scope its value comes from."""

    def __init__(self, frozen: set[str]) -> None:
        self.frozen = frozen
        self.calls: dict[str, list[tuple[str, ast.Call, frozenset[Arg]]]] = {}

    def scan(self, m: Module) -> None:
        self.walk(m, m.tree, [m.tree])

    def walk(self, m: Module, node: ast.AST, scopes: list[Scope]) -> None:
        for child in ast.iter_child_nodes(node):
            inner = (
                [*scopes, child] if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) else scopes
            )
            if isinstance(child, ast.Call):
                name = child.func.id if isinstance(child.func, ast.Name) else getattr(child.func, "attr", None)
                if name in self.frozen:
                    self.calls.setdefault(name, []).append((m.path, child, self.arguments(child, scopes)))
            self.walk(m, child, inner)

    @staticmethod
    def arguments(call: ast.Call, scopes: list[Scope]) -> frozenset[Arg]:
        functions = [s for s in scopes if isinstance(s, ast.FunctionDef | ast.AsyncFunctionDef)]
        classes = [s for s in scopes if isinstance(s, ast.ClassDef)]
        slots = [(str(i), a) for i, a in enumerate(call.args)] + [(kw.arg or "**", kw.value) for kw in call.keywords]
        out = set()
        for slot, value in slots:
            if isinstance(value, ast.Constant):
                continue
            base = root(value)
            if base in {"self", "cls"} and classes:
                owner: Scope = classes[-1]
            else:
                owner = next((f for f in reversed(functions) if base in binds(f)), scopes[0])
            out.add((id(owner), slot, ast.dump(value)))
        return frozenset(out)


@cache
def binds(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Names a function binds itself (parameters and local stores); any other name comes from an outer scope."""
    names = {a.arg for a in params_of(fn)}
    names |= {n.id for n in local_nodes(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    return names


def check(modules: list[Module]) -> list[Hit]:
    frozen = {
        cls.name
        for m in modules
        for cls in ast.walk(m.tree)
        if isinstance(cls, ast.ClassDef) and is_frozen_dataclass(cls)
    }
    sites = Sites(frozen)
    for m in modules:
        sites.scan(m)
    hits = []
    for name, calls in sites.calls.items():
        if len(calls) < MIN_SITES:
            continue
        common = {arg for arg, n in Counter(a for _, _, args in calls for a in args).items() if n >= MIN_SITES}
        flagged: set[int] = set()
        for pair in combinations(sorted(common), MIN_SHARED):
            members = [i for i, (_, _, args) in enumerate(calls) if set(pair) <= args]
            if len(members) >= MIN_SITES:
                flagged.update(members)
        message = f"{RULE} `{name}(...)` repeats arguments shared with other sites: build it through a builder"
        hits.extend(Hit(calls[i][0], calls[i][1].lineno, message) for i in sorted(flagged))
    return hits
