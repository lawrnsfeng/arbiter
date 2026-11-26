"""R61: a subprocess spawn whose argv is spelled out as a literal (list, tuple or loose arguments) at the call site."""

import ast

from rulekit import Hit, Module

RULE = "R61"
LIST_ARGV = {
    "subprocess": dict.fromkeys(("run", "call", "check_call", "check_output", "Popen"), 0),
    "os": dict.fromkeys(("execv", "execve", "execvp", "execvpe", "posix_spawn", "posix_spawnp"), 1)
    | dict.fromkeys(("spawnv", "spawnve", "spawnvp", "spawnvpe"), 2),
}
VARARG_ARGV = {
    "asyncio": {"create_subprocess_exec": 1},
    "os": dict.fromkeys(("execl", "execle", "execlp", "execlpe"), 1)
    | dict.fromkeys(("spawnl", "spawnle", "spawnlp", "spawnlpe"), 2),
}
MODULES = set(LIST_ARGV) | set(VARARG_ARGV)


def spawns(module: str, name: str) -> bool:
    return name in LIST_ARGV.get(module, {}) or name in VARARG_ARGV.get(module, {})


class Imports:
    """Local names bound to the spawn modules (`import os as o`) and to their functions (`from os import execlp`)."""

    def __init__(self, tree: ast.Module) -> None:
        self.modules: dict[str, str] = {}
        self.functions: dict[str, tuple[str, str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in MODULES:
                        self.modules[alias.asname or alias.name] = alias.name
            elif isinstance(node, ast.ImportFrom) and node.module in MODULES:
                for alias in node.names:
                    if spawns(node.module, alias.name):
                        self.functions[alias.asname or alias.name] = (node.module, alias.name)

    def target(self, func: ast.expr) -> tuple[str, str] | None:
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module = self.modules.get(func.value.id)
            return (module, func.attr) if module and spawns(module, func.attr) else None
        if isinstance(func, ast.Name):
            return self.functions.get(func.id)
        return None


def is_literal(node: ast.expr) -> bool:
    if isinstance(node, ast.Starred):
        node = node.value
    return isinstance(node, ast.List | ast.Tuple)


def bare_argv(call: ast.Call, module: str, name: str) -> bool:
    if (start := VARARG_ARGV.get(module, {}).get(name)) is not None:
        loose = any(not isinstance(a, ast.Starred) for a in call.args[start:])
        return loose or any(isinstance(a, ast.Starred) and is_literal(a) for a in call.args)
    index = LIST_ARGV[module][name]
    argv = [kw.value for kw in call.keywords if kw.arg == "args"] or call.args[index : index + 1]
    return any(is_literal(a) for a in argv)


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        imports = Imports(m.tree)
        for node in ast.walk(m.tree):
            if not isinstance(node, ast.Call) or not (target := imports.target(node.func)):
                continue
            module, name = target
            if bare_argv(node, module, name):
                hits.append(Hit(m.path, node.lineno, f"{RULE} `{module}.{name}` gets a hand-written argv"))
    return hits
