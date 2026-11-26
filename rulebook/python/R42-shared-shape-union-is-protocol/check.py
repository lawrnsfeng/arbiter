"""R42: a parameter typed as a union of project classes the function never tells apart (a missing Protocol)."""

import ast

from rulekit import Hit, Module, classes, functions, local_nodes, params_of

RULE = "R42"


def _name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _members(node: ast.expr) -> list[ast.expr]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _members(node.left) + _members(node.right)
    return [node]


def _unions(annotation: ast.expr) -> list[list[str]]:
    """Member names of every union inside the annotation (`A | B`, `Union[A, B]`), None dropped."""
    out: list[list[str]] = []
    for n in ast.walk(annotation):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
            parts = _members(n)
        elif isinstance(n, ast.Subscript) and _name(n.value) == "Union" and isinstance(n.slice, ast.Tuple):
            parts = n.slice.elts
        else:
            continue
        out.append([x for p in parts if (x := _name(p)) and x != "None"] if all(map(_name, parts)) else [])
    return out


def _attributes(cls: ast.ClassDef) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(cls):
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef):
            out.add(n.name)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            out.add(n.id)
        elif isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
            out.add(n.attr)
    return out


def check(modules: list[Module]) -> list[Hit]:
    project = {c.name: c for m in modules for c in classes(m.tree)}
    shape = {name: _attributes(c) for name, c in project.items()}
    hits: list[Hit] = []
    for m in modules:
        for fn in functions(m.tree):
            nodes = local_nodes(fn)
            mentioned = {n.id for n in nodes if isinstance(n, ast.Name)}
            for p in params_of(fn):
                ann = p.annotation
                if ann is None:
                    continue
                # reads on the parameter itself only tell about the union when the union is the whole annotation
                direct = isinstance(ann, ast.BinOp) or (isinstance(ann, ast.Subscript) and _name(ann.value) == "Union")
                for union in _unions(ann):
                    if len(set(union)) < 2 or not all(u in project for u in union) or mentioned & set(union):
                        continue
                    read = {
                        n.attr
                        for n in nodes
                        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == p.arg
                    }
                    if not direct or all(read <= shape[u] for u in union):
                        msg = f"R42 `{p.arg}` takes `{' | '.join(union)}` but uses only shared members; use a Protocol"
                        hits.append(Hit(m.path, p.lineno, msg))
                        break
    return hits
