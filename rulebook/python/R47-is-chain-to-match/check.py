"""R47: two or more `subject is Kind.MEMBER` tests over one scanned Enum, in a row, instead of a `match`."""

import ast

from rulekit import Hit, Module, classes

RULE = "R47"


def _enum_names(modules: list[Module]) -> set[str]:
    """Names of every Enum/Flag subclass defined in the scanned modules: the closed sets the detector can prove."""
    return {
        cls.name
        for m in modules
        for cls in classes(m.tree)
        for b in cls.bases
        if (b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else "").endswith(
            ("Enum", "Flag")
        )
    }


def _member_test(test: ast.expr, enums: set[str]) -> tuple[str, str] | None:
    """(subject, set) for `subject is Kind.MEMBER` where `Kind` is a scanned Enum; None otherwise."""
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Is)):
        return None
    member: ast.expr = test.comparators[0]
    if not isinstance(member, ast.Attribute):
        return None
    owner: ast.expr = member.value
    name: str = owner.id if isinstance(owner, ast.Name) else owner.attr if isinstance(owner, ast.Attribute) else ""
    return (ast.dump(test.left), ast.dump(owner)) if name in enums else None


def _elif_chain(node: ast.If) -> list[ast.If]:
    chain: list[ast.If] = [node]
    while len(chain[-1].orelse) == 1 and isinstance(chain[-1].orelse[0], ast.If):
        chain.append(chain[-1].orelse[0])
    return chain


def _ladders(m: Module, stmts: list[ast.stmt], enums: set[str]) -> list[Hit]:
    out: list[Hit] = []
    run_key: tuple[str, str] | None = None
    run_start: ast.If | None = None
    run_len: int = 0

    def close() -> None:
        if run_start is not None and run_len >= 2:
            out.append(Hit(m.path, run_start.lineno, f"R47 {run_len} `is` tests over one closed set: write a `match`"))

    for stmt in stmts:
        for branch in _elif_chain(stmt) if isinstance(stmt, ast.If) else [None]:
            key: tuple[str, str] | None = _member_test(branch.test, enums) if branch else None
            if key is not None and key == run_key:
                run_len += 1
                continue
            close()
            run_key, run_start, run_len = key, branch if key else None, 1 if key else 0
    close()
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    enums: set[str] = _enum_names(modules)
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
                    out += _ladders(m, stmts, enums)
    return out
