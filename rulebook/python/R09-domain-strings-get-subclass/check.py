"""R9: a free function taking one `str` / `bytes` value and parsing it - the missing property of a named subclass."""

import ast

from rulekit import Hit, Module, local_nodes, params_of

RULE = "R9"
PARSE_METHODS = {"split", "rsplit", "partition", "rpartition", "removeprefix", "removesuffix"}
PARSE_CALLS = {"match", "fullmatch", "search", "findall", "finditer", "loads", "strptime", "fromisoformat"}
# `splitlines` is left out: line-splitting fits any text (`first_line(text)`), it is not a domain parse


def is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def parses(fn: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> bool:
    """A structural parse of `name`: a split at a given delimiter, a fixed-position field `v[2:12]`, a regex or
    date/JSON parse. Whitespace `split()` and truncation `v[:80]` fit any text and do not count."""
    for n in local_nodes(fn):
        if isinstance(n, ast.Subscript) and is_name(n.value, name):
            s = n.slice
            if isinstance(s, ast.Slice) and s.lower is not None and s.upper is not None:
                return True
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr in PARSE_METHODS and is_name(n.func.value, name) and n.args:
                return True
            if n.func.attr in PARSE_CALLS and any(is_name(a, name) for a in n.args):
                return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        for fn in m.tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or fn.decorator_list:
                continue
            params = params_of(fn)
            if (
                len(params) != 1
                or not isinstance(ann := params[0].annotation, ast.Name)
                or ann.id not in {"str", "bytes"}
            ):
                continue
            if parses(fn, params[0].arg):
                out.append(
                    Hit(
                        m.path,
                        fn.lineno,
                        f"{RULE} `{fn.name}` parses a plain `{ann.id}`: make it a property of a `{ann.id}` subclass",
                    )
                )
    return out
