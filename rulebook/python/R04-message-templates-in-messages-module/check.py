"""R4: message templates defined outside messages.py, and multi-line exception messages assembled inline."""

import ast
from pathlib import Path

from rulekit import Hit, Module, functions, local_nodes

RULE = "R4"


def multiline(node: ast.AST) -> bool:
    """A string or f-string whose text holds a newline, or a `"\\n".join(...)`; a long line wrapped in source is not."""
    match node:
        case ast.Constant(value=str() as s):
            return "\n" in s
        case ast.JoinedStr():
            return any(multiline(v) for v in node.values)
        case ast.Call(func=ast.Attribute(attr="join", value=ast.Constant(value=str() as sep))):
            return "\n" in sep
    return False


def template_def(node: ast.stmt) -> str | None:
    if not isinstance(node, ast.Assign | ast.AnnAssign) or node.value is None:
        return None
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    name = next((t.id for t in targets if isinstance(t, ast.Name)), None)
    v = node.value
    is_template = isinstance(v, ast.Call) and getattr(v.func, "id", getattr(v.func, "attr", "")) == "Template"
    named = name is not None and name.upper().endswith("TEMPLATE") and isinstance(v, ast.Constant | ast.JoinedStr)
    return name if name and (is_template or named) else None


def receivers(nodes: list[ast.AST]) -> list[ast.Call]:
    """Calls that carry an exception message: raised calls and `__init__` / `super().__init__` calls."""
    out = [n.exc for n in nodes if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call)]
    out += [
        n for n in nodes if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "__init__"
    ]
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        if Path(m.path).name == "messages.py":
            continue
        out += [
            Hit(m.path, stmt.lineno, f"{RULE} template `{name}` belongs in the messages module")
            for stmt in m.tree.body
            if (name := template_def(stmt))
        ]
        for fn in functions(m.tree):
            nodes = local_nodes(fn)
            built = {
                n.targets[0].id: n
                for n in nodes
                if isinstance(n, ast.Assign)
                and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)
                and multiline(n.value)
            }
            for call in receivers(nodes):
                args = [*call.args, *(k.value for k in call.keywords)]
                if any(multiline(a) for a in args):
                    out.append(
                        Hit(
                            m.path,
                            call.lineno,
                            f"{RULE} multi-line message assembled inline: use a messages-module template",
                        )
                    )
                for a in args:
                    if isinstance(a, ast.Name) and a.id in built:
                        line = built.pop(a.id).lineno
                        out.append(
                            Hit(
                                m.path,
                                line,
                                f"{RULE} multi-line message `{a.id}` assembled inline: use a messages-module template",
                            )
                        )
    return out
