"""R23: two or more module constants shaped `<GROUP>_<VALUE> = "value"`: a closed set kept as bare strings."""

import ast
import re

from rulekit import Hit, Module

RULE = "R23"
_CONSTANT = re.compile(r"^[A-Z][A-Z0-9_]*$")
_WORD = re.compile(r"^[a-z][a-z0-9_-]{0,30}$")


def _group(name: str, value: str) -> tuple[str, str] | None:
    """('prefix', GROUP) for GROUP_VALUE, ('suffix', GROUP) for VALUE_GROUP, else None."""
    member = value.replace("-", "_").upper()
    if name.endswith(f"_{member}") and len(name) > len(member) + 1:
        return "prefix", name[: -len(member) - 1]
    if name.startswith(f"{member}_") and len(name) > len(member) + 1:
        return "suffix", name[len(member) + 1 :]
    return None


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        groups: dict[tuple[str, str], list[ast.Name]] = {}
        for stmt in m.tree.body:
            if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1):
                continue
            target, value = stmt.targets[0], stmt.value
            if not (isinstance(target, ast.Name) and _CONSTANT.match(target.id)):
                continue
            literal = isinstance(value, ast.Constant) and isinstance(value.value, str) and _WORD.match(value.value)
            if literal and (key := _group(target.id, value.value)):
                groups.setdefault(key, []).append(target)
        for (_, group), members in groups.items():
            if len(members) >= 2:
                hits += [
                    Hit(
                        m.path,
                        t.lineno,
                        f"{RULE} `{t.id}` is one of {len(members)} bare `{group}` strings; use a StrEnum",
                    )
                    for t in members
                ]
    return hits
