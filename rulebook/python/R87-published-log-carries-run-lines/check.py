"""R87: test code publishing a whole log file instead of the slice the scenario produced."""

import ast
import re
from pathlib import Path

from rulekit import Hit, Module, functions, local_nodes

RULE = "R87"
SHUTIL_COPIES = {"copy", "copy2", "copyfile", "copyfileobj"}
BARE_COPIES = {"copy2", "copyfile", "copyfileobj"}  # `copy` alone is too often `copy.copy`
READS = {"read_text": "write_text", "read_bytes": "write_bytes"}
LOG_WORDS = {"log", "logs", "logfile"}
FILE_WORDS = LOG_WORDS | {"path", "file", "location", "filename"}
PUBLISHED = {"evidence", "artifact", "artifacts", "report", "reports", "publish", "published", "results", "outputs"}


def names_log_file(text: str) -> bool:
    """`log_path`, `service_log`, `logfile`: a log word, and the identifier ends in a file word."""
    words = [w for w in re.split(r"[^a-z]+", text.lower()) if w]
    return bool(words) and bool(LOG_WORDS & set(words)) and words[-1] in FILE_WORDS


def is_log_file(expr: ast.expr) -> bool:
    for n in ast.walk(expr):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.endswith(".log"):
            return True
        if (isinstance(n, ast.Name) and names_log_file(n.id)) or (
            isinstance(n, ast.Attribute) and names_log_file(n.attr)
        ):
            return True
    return False


def whole_read(expr: ast.expr | None) -> str | None:
    """`<log file>.read_text()` / `.read_bytes()`: the read method's name, else None."""
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr in READS
        and not expr.args
        and is_log_file(expr.func.value)
    ):
        return expr.func.attr
    return None


def is_copy(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr in SHUTIL_COPIES and isinstance(func.value, ast.Name) and func.value.id == "shutil"
    return isinstance(func, ast.Name) and func.id in BARE_COPIES


def is_test_code(path: str, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    name = Path(path).name
    if name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py":
        return True
    fixture = any("fixture" in ast.unparse(d) for d in fn.decorator_list)
    return fn.name.startswith("test") or fixture


def is_evidence(expr: ast.expr) -> bool:
    """The destination is a published place: a name, attribute or string with an evidence/artifact/report word."""
    for n in ast.walk(expr):
        text = n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else None
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            text = n.value
        if text and PUBLISHED & set(re.split(r"[^a-z]+", text.lower())):
            return True
    return False


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        for fn in functions(mod.tree):
            if not is_test_code(mod.path, fn):
                continue
            whole: dict[str, str] = {}  # locals holding a whole log read -> the read method
            for node in local_nodes(fn):
                target = node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else None
                if isinstance(target, ast.Name) and (read := whole_read(node.value)):
                    whole[target.id] = read
                if not isinstance(node, ast.Call):
                    continue
                published = (
                    is_copy(node) and len(node.args) >= 2 and is_log_file(node.args[0]) and is_evidence(node.args[1])
                )
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in READS.values()
                    and node.args
                    and is_evidence(node.func.value)
                ):
                    arg = node.args[0]
                    read = whole_read(arg) or (whole.get(arg.id) if isinstance(arg, ast.Name) else None)
                    published = published or READS.get(read or "") == node.func.attr
                if published:
                    msg = f"R87 `{fn.name}` publishes the whole log file: publish the slice since the mark"
                    hits.append(Hit(mod.path, node.lineno, msg))
    return hits
