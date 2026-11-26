"""R8: free functions that create a third-party type internally and operate on it."""

import ast
import re
import sys

from rulekit import Hit, Module, local_nodes, project_tops

RULE = "R8"
FACTORIES = {"connect", "client", "session", "resource"}
# a type named like a connection or service handle; value types (data frames, parsed documents) are not wrapped
RESOURCE = re.compile(
    r"(Client|Session|Connection|Connector|Pool|Transport|Channel|Producer|Consumer|Publisher|Driver|Engine|Socket|Bot)$"
)


def third_party(tree: ast.Module, tops: set[str]) -> tuple[set[str], set[str]]:
    """(module aliases from `import X`, names from `from X import n`) whose top-level package is third-party."""
    mods: set[str] = set()
    names: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                top = a.name.split(".")[0]
                if top not in sys.stdlib_module_names and top not in tops:
                    mods.add(a.asname or top)
        elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
            top = n.module.split(".")[0]
            if top not in sys.stdlib_module_names and top not in tops:
                names |= {a.asname or a.name for a in n.names}
    return mods, names


def made_type(call: ast.expr, mods: set[str], names: set[str]) -> tuple[str, bool] | None:
    """(label, is a resource by name) when the call builds a third-party type: `Type(...)`, `mod.Type(...)`,
    `mod.connect(...)`, or a classmethod factory `Type.from_url(...)` / `mod.Type.from_env(...)`."""
    if not isinstance(call, ast.Call):
        return None
    f = call.func
    if isinstance(f, ast.Name) and f.id in names:
        typ, final = f.id, f.id
    elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in mods:
        typ, final = f.attr, f.attr
    elif isinstance(f, ast.Attribute) and f.attr.startswith("from_"):
        owner = f.value
        if isinstance(owner, ast.Name) and owner.id in names:
            typ, final = owner.id, f.attr
        elif isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id in mods:
            typ, final = owner.attr, f.attr
        else:
            return None
    else:
        return None
    if not (typ[:1].isupper() or final in FACTORIES):
        return None
    return typ, final in FACTORIES or bool(RESOURCE.search(typ))


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    tops = project_tops(modules)
    for m in modules:
        mods, names = third_party(m.tree, tops)
        if not (mods or names):
            continue
        for fn in m.tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or fn.decorator_list:
                continue
            nodes = local_nodes(fn)
            made: dict[str, tuple[int, str, bool]] = {}
            for n in nodes:
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                    if t := made_type(n.value, mods, names):
                        made[n.targets[0].id] = (n.lineno, *t)
                elif (
                    isinstance(n, ast.withitem)
                    and isinstance(n.optional_vars, ast.Name)
                    and (t := made_type(n.context_expr, mods, names))
                ):
                    made[n.optional_vars.id] = (n.context_expr.lineno, t[0], True)  # a context manager is a resource
            returned = {r.value.id for r in nodes if isinstance(r, ast.Return) and isinstance(r.value, ast.Name)}
            calls = [
                (n.func.value.id, n.func.attr)
                for n in nodes
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
            ]
            used = {name for name, _ in calls}
            closed = {name for name, attr in calls if attr == "close"}
            out += [
                Hit(m.path, line, f"{RULE} `{fn.name}` wraps `{t}` in a free function: subclass it, make this a method")
                for name, (line, t, resource) in made.items()
                if name in used and name not in returned and (resource or name in closed)
            ]
    return out
