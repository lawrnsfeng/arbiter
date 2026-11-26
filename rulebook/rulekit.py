"""Shared contract for rulebook detectors: parsed modules in, hits out. Stdlib only.

A detector is `rulebook/python/<folder>/check.py` defining `RULE = "R46"` and
`def check(modules: list[Module]) -> list[Hit]`.
"""

import ast
import os
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import NamedTuple

type Function = ast.FunctionDef | ast.AsyncFunctionDef
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


class Module(NamedTuple):
    path: str
    source: str
    tree: ast.Module


class Hit(NamedTuple):
    path: str
    line: int
    message: str  # "R46 `name` is first assigned unannotated"


def load(paths: Iterable[str]) -> tuple[list[Module], list[str]]:
    """Parse every path; return parsed modules and the paths that failed to read or parse (never dropped silently)."""
    modules: list[Module] = []
    failed: list[str] = []
    for path in paths:
        try:
            source = Path(path).read_text(encoding="utf-8")
            modules.append(Module(path, source, ast.parse(source, path)))
        except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
            failed.append(path)
    return modules, failed


def functions(tree: ast.AST) -> Iterator[Function]:
    """Every def and async def in the tree, nested ones included."""
    return (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef))


def classes(tree: ast.AST) -> Iterator[ast.ClassDef]:
    """Every class in the tree, nested ones included."""
    return (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef))


def local_nodes(fn: Function) -> list[ast.AST]:
    """Every node in the body that is not inside a nested def/async def/class (the nested def node itself is kept)."""
    out: list[ast.AST] = []
    stack: list[ast.AST] = list(reversed(fn.body))
    while stack:
        node = stack.pop()
        out.append(node)
        if not isinstance(node, _SCOPES):
            stack.extend(reversed(list(ast.iter_child_nodes(node))))
    return out


def params_of(fn: Function) -> list[ast.arg]:
    """Every parameter: positional-only, positional, *args, keyword-only, **kwargs."""
    a = fn.args
    return [*a.posonlyargs, *a.args, *([a.vararg] if a.vararg else []), *a.kwonlyargs, *([a.kwarg] if a.kwarg else [])]


def base_name(node: ast.expr) -> str:
    """Last dotted segment of a name or attribute (`a.b.C` -> `C`); empty for anything else."""
    return node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""


def project_tops(modules: list[Module]) -> set[str]:
    """Top-level package or module names of the scanned files, relative to their common directory."""
    paths = [Path(m.path).resolve() for m in modules]
    root = Path(os.path.commonpath([p.parent for p in paths])) if paths else Path()
    return {p.relative_to(root).parts[0].removesuffix(".py") for p in paths}


def foreign_imports(tree: ast.Module, tops: set[str]) -> set[str]:
    """Names this module imports from packages outside the scanned project (a same-named project class is not meant)."""
    return {
        a.asname or a.name
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and not n.level and n.module and n.module.split(".")[0] not in tops
        for a in n.names
    }
