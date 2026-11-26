"""R69: verb-named properties and participle-named methods."""

import ast
import re

from rulekit import Hit, Module, classes

RULE = "R69"
VERBS = {
    "render", "compute", "calculate", "fetch", "get", "make", "create", "parse", "convert", "generate", "validate",
    "resolve", "collect", "execute", "normalize", "serialize", "extract",
}  # fmt: skip
EXACT_ONLY = {"apply", "send", "save", "build", "load", "run", "process", "check"}


def decorator_names(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = set()
    for deco in fn.decorator_list:
        target = deco.func if isinstance(deco, ast.Call) else deco
        names.add(target.id if isinstance(target, ast.Name) else getattr(target, "attr", ""))
    return names


def verb_property(name: str) -> bool:
    words = name.lstrip("_").split("_")
    return words[0] in VERBS or (len(words) == 1 and words[0] in EXACT_ONLY)


def participle_method(name: str) -> bool:
    """`normalized`, `sorted_by_due`: an `-ed` first word with a 4+ letter stem; `-eed` verbs (`proceed`) excluded."""
    first = re.match(r"[a-z]*", name.lstrip("_").split("_")[0])[0]
    return len(first) >= 6 and first.endswith("ed") and not first.endswith("eed")


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        for cls in classes(m.tree):
            for fn in cls.body:
                if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or fn.name.startswith("__"):
                    continue
                decos = decorator_names(fn)
                if decos & {"setter", "deleter", "getter"}:
                    continue
                if decos & {"property", "cached_property"}:
                    if verb_property(fn.name):
                        hits.append(Hit(m.path, fn.lineno, f"{RULE} property `{fn.name}` is named with a verb"))
                elif participle_method(fn.name):
                    hits.append(Hit(m.path, fn.lineno, f"{RULE} method `{fn.name}` is named with a participle"))
    return hits
