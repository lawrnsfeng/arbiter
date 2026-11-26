"""R28: methods named with a bare past participle (`compacted`, `finished`) instead of a verb, noun or is_ predicate."""

import ast
import re

from rulekit import Hit, Module, classes

RULE = "R28"
_PARTICIPLE = re.compile(r"^[a-z]{3,}ed$")
_NOT_ADJECTIVES = {"embed", "shred", "hundred", "kindred", "unshed", "infrared"}
_PROPERTIES = {"property", "cached_property", "setter", "getter", "deleter"}


def _last(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else None


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for cls in classes(m.tree):
            for fn in cls.body:
                if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or fn.name.startswith("__"):
                    continue
                word = fn.name.lstrip("_")
                if not _PARTICIPLE.match(word) or word.endswith("eed") or word in _NOT_ADJECTIVES:
                    continue
                if any(_last(d) in _PROPERTIES for d in fn.decorator_list):
                    continue
                hits.append(Hit(m.path, fn.lineno, f"{RULE} method `{fn.name}` is named as a state; use a verb or is_"))
    return hits
