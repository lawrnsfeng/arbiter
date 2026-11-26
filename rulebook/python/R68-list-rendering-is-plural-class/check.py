"""R68: a call site rendering records as `items[0].<attr>` plus a join over `items[1:]` rendering each record."""

import ast

from rulekit import Hit, Module, functions, local_nodes

RULE = "R68"


def rest_of(node: ast.expr) -> str | None:
    """`X[1:]` -> dump of X."""
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
        s = node.slice
        if isinstance(s.lower, ast.Constant) and s.lower.value == 1 and s.upper is None and s.step is None:
            return ast.dump(node.value)
    return None


def joined_rest(call: ast.Call) -> str | None:
    """Subject X of `sep.join(<render r> for r in X[1:])`, where the element reads an attribute of the record."""
    if not (isinstance(call.func, ast.Attribute) and call.func.attr == "join" and len(call.args) == 1):
        return None
    arg = call.args[0]
    if not isinstance(arg, ast.GeneratorExp | ast.ListComp) or len(arg.generators) != 1:
        return None
    gen = arg.generators[0]
    if not isinstance(gen.target, ast.Name):
        return None
    record = gen.target.id
    renders = any(
        isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == record
        for n in ast.walk(arg.elt)
    )
    return rest_of(gen.iter) if renders else None


def renders_first(node: ast.AST, subject: str) -> bool:
    """`X[0].<attr>`: the first record's rendering."""
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Subscript)
        and isinstance(node.value.slice, ast.Constant)
        and node.value.slice.value == 0
        and ast.dump(node.value.value) == subject
    )


SIMPLE = (ast.Return, ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr)


def first_outside(stmt: ast.AST, subject: str, join: ast.Call) -> bool:
    inside = {id(n) for n in ast.walk(join)}
    return any(renders_first(n, subject) and id(n) not in inside for n in ast.walk(stmt))


def seeds(statements: list[ast.stmt], name: str) -> list[ast.Assign]:
    return [
        s
        for s in statements
        if isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in s.targets)
    ]


def scope_hits(m: Module, nodes: list[ast.AST]) -> list[Hit]:
    """The first record's rendering and the join over the rest meet in one statement, or `s = <first>; s += <join>`."""
    statements = [n for n in nodes if isinstance(n, SIMPLE)]
    hits = []
    for stmt in statements:
        for join in (n for n in ast.walk(stmt) if isinstance(n, ast.Call)):
            if (subject := joined_rest(join)) is None:
                continue
            combined = first_outside(stmt, subject, join)
            if not combined and isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
                combined = any(first_outside(s, subject, join) for s in seeds(statements, stmt.target.id))
            if combined:
                message = f"{RULE} first-plus-rest rendering: move it to a plural class property"
                hits.append(Hit(m.path, join.lineno, message))
    return hits


def module_nodes(tree: ast.Module) -> list[ast.AST]:
    out: list[ast.AST] = []
    for stmt in tree.body:
        if not isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            out.extend(ast.walk(stmt))
    return out


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        hits.extend(scope_hits(m, module_nodes(m.tree)))
        for fn in functions(m.tree):
            hits.extend(scope_hits(m, local_nodes(fn)))
    return hits
