"""R46: a local's first assignment, and a class attribute's first declaration, state the type."""

import ast

from rulekit import Hit, Module, classes, functions, local_nodes, params_of

RULE = "R46"


def _named(node: ast.expr, name: str) -> bool:
    """`name` or `anything.name`."""
    return (isinstance(node, ast.Name) and node.id == name) or (isinstance(node, ast.Attribute) and node.attr == name)


def _is_classvar(annotation: ast.expr) -> bool:
    return _named(annotation.value if isinstance(annotation, ast.Subscript) else annotation, "ClassVar")


def _is_dataclass(cls: ast.ClassDef) -> bool:
    return any(_named(d.func if isinstance(d, ast.Call) else d, "dataclass") for d in cls.decorator_list)


def _is_enum(cls: ast.ClassDef) -> bool:
    """Enum members must stay unannotated (typing spec), so enum bodies are skipped."""
    names: list[str] = [
        b.id if isinstance(b, ast.Name) else b.attr for b in cls.bases if isinstance(b, ast.Name | ast.Attribute)
    ]
    return any(n.endswith(("Enum", "Flag")) for n in names)


def _is_constant(name: str) -> bool:
    return name.upper() == name and any(c.isalpha() for c in name)


def _single_name(node: ast.AST) -> str | None:
    """The target name of `name = value`; None for tuple, attribute, subscript and chained targets."""
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def _locals(m: Module, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[Hit]:
    out: list[Hit] = []
    nodes: list[ast.AST] = local_nodes(fn)
    stated: set[str] = {a.arg for a in params_of(fn)}
    stated |= {n for node in nodes if isinstance(node, ast.Global | ast.Nonlocal) for n in node.names}
    comprehension_vars: set[int] = {
        id(n) for c in nodes if isinstance(c, ast.comprehension) for n in ast.walk(c.target)
    }  # scoped to their comprehension
    for node in nodes:  # pre-order, so a binding is seen before anything after it
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            stated.add(node.target.id)
        elif (name := _single_name(node)) and name not in stated:
            stated.add(name)
            out.append(
                Hit(m.path, node.lineno, f"R46 `{name}` is first assigned unannotated: the annotation is the contract")
            )
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and id(node) not in comprehension_vars:
            stated.add(node.id)  # tuple, `for`, `with ... as` and walrus targets: no annotation syntax exists
        elif isinstance(node, ast.ExceptHandler) and node.name:
            stated.add(node.name)
        elif isinstance(node, ast.Import | ast.ImportFrom):
            stated |= {(a.asname or a.name).split(".")[0] for a in node.names}
    return out


def _attributes(m: Module, cls: ast.ClassDef) -> list[Hit]:
    out: list[Hit] = []
    dataclass: bool = _is_dataclass(cls)
    enum: bool = _is_enum(cls)
    stated: set[str] = set()
    for node in cls.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name: str = node.target.id
            if dataclass and _is_constant(name) and not _is_classvar(node.annotation):
                out.append(
                    Hit(
                        m.path,
                        node.lineno,
                        f"R46 dataclass constant `{name}` is not `ClassVar[...]`: it becomes a field",
                    )
                )
            stated.add(name)
        elif (name := _single_name(node)) and not enum and name not in stated and not name.startswith("__"):
            stated.add(name)
            out.append(Hit(m.path, node.lineno, f"R46 class attribute `{name}` is first declared unannotated"))
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        for fn in functions(m.tree):
            out += _locals(m, fn)
        for cls in classes(m.tree):
            out += _attributes(m, cls)
    return out
