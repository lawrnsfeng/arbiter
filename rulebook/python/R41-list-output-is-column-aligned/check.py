"""R41: a literal text listing same-shaped items is hand-spaced instead of padded into columns."""

import ast
import re

from rulekit import Hit, Module

RULE = "R41"
# `label:  value` (label of words, then colon) and `label  value` (two or more spaces between short columns)
COLON = re.compile(r"^( *)([A-Za-z][\w .-]{0,40}?):( +)\S")
SPACED = re.compile(r"^( *)([\w-]+(?: [\w-]+){0,3})( {2,})\S")
PLACEHOLDER = "X"


def _docstrings(tree: ast.Module) -> set[int]:
    out: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant | ast.JoinedStr):
                out.add(id(first.value))
    return out


def _text(node: ast.expr) -> str:
    if isinstance(node, ast.Constant):
        return node.value
    return "".join(v.value if isinstance(v, ast.Constant) else PLACEHOLDER for v in node.values)


def _misaligned(text: str) -> bool:
    for pattern in (COLON, SPACED):
        columns: dict[str, set[int]] = {}
        padded = False
        for line in text.splitlines():
            if match := pattern.match(line):
                columns.setdefault(match[1], set()).add(match.end(3))
                padded |= len(match[3]) >= 2
        groups = [cols for cols in columns.values() if len(cols) > 1]
        if padded and groups:
            return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for m in modules:
        skip = _docstrings(m.tree)
        inner = {id(v) for n in ast.walk(m.tree) if isinstance(n, ast.JoinedStr) for v in n.values}
        for node in ast.walk(m.tree):
            if id(node) in skip or id(node) in inner:
                continue
            is_text = isinstance(node, ast.Constant) and isinstance(node.value, str)
            if (is_text or isinstance(node, ast.JoinedStr)) and "\n" in _text(node) and _misaligned(_text(node)):
                msg = "R41 listed items are hand-spaced; pad each column to the widest entry"
                hits.append(Hit(m.path, node.lineno, msg))
    return hits
