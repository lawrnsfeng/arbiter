"""R60: a parameter named as the lower-case twin of a module constant (`root_dir` beside `ROOT_DIR`)."""

import ast
import sys

from rulekit import Hit, Module, functions, params_of

RULE = "R60"


TYPE_FACTORIES = {"TypeVar", "ParamSpec", "TypeVarTuple", "NewType"}


def _type_variable(value: ast.expr) -> bool:
    """`T = TypeVar("T")` and the like: a type, not a constant a parameter could override."""
    f: ast.expr | None = value.func if isinstance(value, ast.Call) else None
    return (isinstance(f, ast.Name) and f.id in TYPE_FACTORIES) or (
        isinstance(f, ast.Attribute) and f.attr in TYPE_FACTORIES
    )


def _constants(tree: ast.Module) -> set[str]:
    """Upper-case names bound at module level or imported into the module."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and not _type_variable(node.value):
            names |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] not in sys.stdlib_module_names:
            names |= {a.asname or a.name for a in node.names}  # stdlib acronyms (`UUID`) are classes, not constants
    return {n for n in names if n.isupper() and len(n) > 1}  # one-letter names are type variables, not constants


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        constants: set[str] = _constants(m.tree)
        for fn in functions(m.tree):
            for arg in params_of(fn):
                twin: str = arg.arg.upper()
                if twin != arg.arg and twin in constants:
                    out.append(
                        Hit(
                            m.path,
                            arg.lineno,
                            f"R60 parameter `{arg.arg}` is the case-twin of `{twin}`: name the concept",
                        )
                    )
    return out
