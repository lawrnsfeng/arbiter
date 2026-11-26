"""R55: running a script or a shell from Python instead of the binary with explicit argv (and captured output)."""

import ast
import re

from rulekit import Hit, Module

RULE = "R55"
SUBPROCESS = {"run", "call", "check_call", "check_output", "Popen"}
NEEDS_CAPTURE = {"run", "call", "check_call"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "/bin/sh", "/bin/bash", "/bin/zsh", "/usr/bin/bash"}
ENV = {"env", "/usr/bin/env"}
WORD = re.compile(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])")  # identifier words: `run_script`, `syncScript`, `SCRIPT_DIR`
SCRIPT_SUFFIXES = (".sh", ".bash", ".zsh", ".ksh")
OS_SHELL = {"system", "popen"}


def _qualified(call: ast.Call, module: str, names: set[str]) -> str | None:
    f: ast.expr = call.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == module and f.attr in names:
        return f.attr
    return None


def _scriptish(node: ast.expr) -> bool:
    """A script path: a `*.sh` / `./x` literal, or an expression naming a script."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.endswith(SCRIPT_SUFFIXES) or node.value.startswith("./")
    names: list[str] = [n.id for n in ast.walk(node) if isinstance(n, ast.Name)]
    names += [n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)]
    strings: list[str] = [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    words: set[str] = {w.lower() for name in names for w in WORD.findall(name)}  # `transcript` is not `script`
    return bool(words & {"script", "scripts"}) or any(v.endswith(SCRIPT_SUFFIXES) for v in strings)


def _program(elts: list[ast.expr]) -> ast.expr:
    """The program an argv runs: past `env` and its `NAME=value` / `-x` arguments."""
    i: int = 0
    if isinstance(elts[0], ast.Constant) and elts[0].value in ENV:
        i = 1
        while (
            i < len(elts) - 1
            and isinstance(elts[i], ast.Constant)
            and ("=" in str(elts[i].value) or str(elts[i].value).startswith("-"))
        ):
            i += 1
    return elts[min(i, len(elts) - 1)]


def _captured(kw: dict[str | None, ast.expr]) -> bool:
    """`capture_output=` not literally False, or `stdout=` not literally None."""
    capture: ast.expr | None = kw.get("capture_output")
    stdout: ast.expr | None = kw.get("stdout")
    return any(
        v is not None and not (isinstance(v, ast.Constant) and v.value in {False, None}) for v in (capture, stdout)
    )


def _problems(call: ast.Call, name: str) -> list[str]:
    kw: dict[str | None, ast.expr] = {k.arg: k.value for k in call.keywords}
    argv: ast.expr | None = call.args[0] if call.args else kw.get("args")
    problems: list[str] = []
    shell: ast.expr | None = kw.get("shell")
    if isinstance(shell, ast.Constant) and shell.value is True:
        problems.append("runs through a shell")
    if isinstance(argv, ast.List | ast.Tuple) and argv.elts:
        head: ast.expr = _program(argv.elts)
        if isinstance(head, ast.Constant) and head.value in SHELLS:
            problems.append("runs a script through an interpreter")
        elif _scriptish(head):
            problems.append("runs a wrapper script")
    elif isinstance(argv, ast.Constant | ast.JoinedStr):
        problems.append("argv is one string, not an explicit list")
    elif argv is not None and _scriptish(argv):
        problems.append("runs a wrapper script")
    if problems and name in NEEDS_CAPTURE and not _captured(kw):
        problems.append("output is not captured")  # C4 binds the call that replaces a script, not interactive tools
    return problems


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        for call in ast.walk(m.tree):
            if not isinstance(call, ast.Call):
                continue
            if (name := _qualified(call, "subprocess", SUBPROCESS)) and (problems := _problems(call, name)):
                out.append(Hit(m.path, call.lineno, f"R55 subprocess.{name} {', '.join(problems)}"))
            elif name := _qualified(call, "os", OS_SHELL):
                out.append(Hit(m.path, call.lineno, f"R55 os.{name} shells out: run the binary with explicit argv"))
    return out
