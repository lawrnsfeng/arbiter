"""R54: copied helpers (identical function bodies), and `<pkg>/utils/` modules importing a subsystem."""

import ast
from collections import defaultdict
from pathlib import Path

from rulekit import Hit, Module, functions

RULE = "R54"
MIN_NODES = 20  # smaller identical bodies (`return self.name`) are idioms, not copied helpers
UTILS_MAY_IMPORT = {"errors", "messages", "utils"}


def _body_key(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    body: list[ast.stmt] = fn.body[1:] if ast.get_docstring(fn) is not None else fn.body
    if sum(1 for stmt in body for _ in ast.walk(stmt)) < MIN_NODES:
        return None
    return "\n".join(ast.dump(stmt) for stmt in body)


def _copies(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    seen: defaultdict[str, list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]] = defaultdict(list)
    for m in modules:
        for fn in functions(m.tree):
            if (key := _body_key(fn)) is not None:
                seen[key].append((m.path, fn))
    for group in seen.values():
        (path, first), *rest = sorted(group, key=lambda pf: (pf[0], pf[1].lineno))
        out += [
            Hit(
                p,
                fn.lineno,
                f"R54 `{fn.name}` copies `{first.name}` ({path}:{first.lineno}): share one helper in <pkg>/utils/",
            )
            for p, fn in rest
        ]
    return out


def _utils_root(path: str) -> int | None:
    """Index of the `utils` directory in `path` when it is the top-level package's `<pkg>/utils/`."""
    parts: tuple[str, ...] = Path(path).parts
    for i, part in enumerate(parts[:-1]):
        if part == "utils" and i >= 1:
            pkg: Path = Path(*parts[:i])
            if (pkg / "__init__.py").exists() and not (pkg.parent / "__init__.py").exists():
                return i
    return None


def _imported(node: ast.Import | ast.ImportFrom, dirs: list[str], u: int) -> list[list[str]]:
    """Every imported dotted target as a list of segments, relative imports resolved against `dirs`."""
    if isinstance(node, ast.Import):
        return [alias.name.split(".") for alias in node.names]
    base: list[str] = dirs[: len(dirs) - node.level + 1] if node.level else []
    module: list[str] = node.module.split(".") if node.module else []
    if node.level and len(base) > u:
        return []  # stays inside utils/
    prefix: list[str] = [*base[u - 1 :], *module] if node.level else module
    return [[*prefix, alias.name] for alias in node.names] if len(prefix) < 2 else [prefix]


def _utils_imports(m: Module) -> list[Hit]:
    out: list[Hit] = []
    u: int | None = _utils_root(m.path)
    if u is None:
        return out
    dirs: list[str] = list(Path(m.path).parts[:-1])
    pkg: str = dirs[u - 1]
    for node in ast.walk(m.tree):
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue
        out += [
            Hit(m.path, node.lineno, f"R54 utils module imports subsystem `{pkg}.{target[1]}`")
            for target in _imported(node, dirs, u)
            if len(target) >= 2 and target[0] == pkg and target[1] not in UTILS_MAY_IMPORT
        ]
    return out


def check(modules: list[Module]) -> list[Hit]:
    return _copies(modules) + [hit for m in modules for hit in _utils_imports(m)]
