"""R83: threads in a module that runs on an event loop, loops created inside threads, module-level daemon threads."""

import ast

from rulekit import Hit, Module, functions, local_nodes

RULE = "R83"
LOOP_LIBS = {"asyncio", "anyio", "trio", "fastapi", "starlette", "aiohttp", "uvicorn"}
THREADS = {"Thread", "Timer"}


def runs_on_loop(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            return True
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] in LOOP_LIBS for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in LOOP_LIBS:
            return True
    return False


def short(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.id if isinstance(node, ast.Name) else None


def is_daemon(node: ast.Call) -> bool:
    return any(k.arg == "daemon" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords)


def thread_bodies(tree: ast.Module) -> set[str]:
    """Names of functions a thread runs: `Thread(target=f)`, `Timer(t, f)`, and `run` of a Thread subclass."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and short(node) in THREADS:
            target = next((k.value for k in node.keywords if k.arg in {"target", "function"}), None)
            if target is None and short(node) == "Timer" and len(node.args) > 1:
                target = node.args[1]
            if name := short(target):
                names.add(name)
    return names


def thread_classes(tree: ast.Module) -> list[ast.ClassDef]:
    return [c for c in ast.walk(tree) if isinstance(c, ast.ClassDef) and any(short(b) in THREADS for b in c.bases)]


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        top = {
            id(n)
            for stmt in mod.tree.body
            if not isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            for n in ast.walk(stmt)
        }
        on_loop = runs_on_loop(mod.tree)
        for node in ast.walk(mod.tree):
            if not isinstance(node, ast.Call) or short(node) not in THREADS:
                continue
            if id(node) in top and is_daemon(node):
                hits.append(Hit(mod.path, node.lineno, "R83 module-level daemon thread: never drained on shutdown"))
            elif on_loop:
                msg = f"R83 {short(node)} spawned in a module that runs on an event loop: use a task or to_thread"
                hits.append(Hit(mod.path, node.lineno, msg))
        classes = thread_classes(mod.tree)
        if on_loop:
            hits.extend(
                Hit(mod.path, c.lineno, f"R83 `{c.name}` subclasses Thread in a module that runs on an event loop")
                for c in classes
            )
        in_thread = thread_bodies(mod.tree)
        run_methods = {id(f) for c in classes for f in c.body if isinstance(f, ast.FunctionDef) and f.name == "run"}
        for fn in functions(mod.tree):
            if fn.name not in in_thread and id(fn) not in run_methods:
                continue
            hits.extend(
                Hit(mod.path, n.lineno, f"R83 `{fn.name}` runs in a thread and opens a second event loop")
                for n in local_nodes(fn)
                if isinstance(n, ast.Call) and short(n) == "new_event_loop"
            )
    return hits
