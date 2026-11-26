"""R48: two or more counting/summing passes over the same sequence on one path through a function."""

import ast
from collections import defaultdict

from rulekit import Hit, Module, functions

RULE = "R48"
COMPREHENSIONS = (ast.GeneratorExp, ast.ListComp, ast.SetComp)
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
TERMINAL = (ast.Return, ast.Raise, ast.Continue, ast.Break)

type Path = tuple[tuple[int, int], ...]  # (branching node id, branch taken)


def _pass_over(node: ast.AST) -> str | None:
    """The sequence a counting/summing call walks: `sum(... for x in S)`, `len([... for x in S])`, `S.count(v)`."""
    if not isinstance(node, ast.Call) or node.keywords:
        return None
    func: ast.expr = node.func
    if isinstance(func, ast.Name) and func.id in {"sum", "len"} and len(node.args) == 1:
        arg: ast.expr = node.args[0]
        if isinstance(arg, COMPREHENSIONS):
            return ast.dump(arg.generators[0].iter)
    if (
        isinstance(func, ast.Attribute)
        and func.attr == "count"
        and len(node.args) == 1
        and isinstance(func.value, ast.Name | ast.Attribute)
    ):
        return ast.dump(func.value)
    return None


class _Walker:
    """Every counting call of one function scope with the branch path that reaches it."""

    def __init__(self) -> None:
        self.calls: list[tuple[ast.Call, str, Path]] = []

    def block(self, stmts: list[ast.stmt], path: Path) -> None:
        for stmt in stmts:
            self.node(stmt, path)
            if isinstance(stmt, ast.If) and not stmt.orelse and stmt.body and isinstance(stmt.body[-1], TERMINAL):
                path = (*path, (id(stmt), 1))  # code after `if c: return ...` is the implicit else branch

    def node(self, node: ast.AST, path: Path) -> None:
        if isinstance(node, SCOPES):
            return
        if isinstance(node, ast.Call) and (seq := _pass_over(node)) is not None:
            self.calls.append((node, seq, path))
        match node:
            case ast.If() | ast.IfExp():
                self.node(node.test, path)
                for branch, part in enumerate((node.body, node.orelse)):
                    self.branch(part, (*path, (id(node), branch)))
            case ast.Match():
                self.node(node.subject, path)
                for i, case in enumerate(node.cases):
                    self.branch(case.body, (*path, (id(node), i)))
            case _:
                for _field, value in ast.iter_fields(node):
                    self.branch(value, path)

    def branch(self, value: object, path: Path) -> None:
        if isinstance(value, list) and value and isinstance(value[0], ast.stmt):
            self.block(value, path)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, ast.AST):
                    self.node(item, path)
        elif isinstance(value, ast.AST):
            self.node(value, path)


def _exclusive(a: Path, b: Path) -> bool:
    """Two paths that part at some branching node can never both run."""
    taken: dict[int, int] = dict(a)
    return any(k in taken and taken[k] != v for k, v in b)


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        for fn in functions(m.tree):
            walker: _Walker = _Walker()
            walker.block(fn.body, ())
            passes: defaultdict[str, list[tuple[ast.Call, Path]]] = defaultdict(list)
            for call, seq, path in walker.calls:
                passes[seq].append((call, path))
            for group in passes.values():
                together: list[ast.Call] = [
                    c for c, p in group if any(d is not c and not _exclusive(p, q) for d, q in group)
                ]
                out += [
                    Hit(
                        m.path, c.lineno, f"R48 one of {len(together)} passes over the same sequence: count in one pass"
                    )
                    for c in together
                ]
    return out
