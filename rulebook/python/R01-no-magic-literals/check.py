"""R1: magic literals inline outside the constants module: hosts, ports, file names, the program name, thresholds and
business-number keywords."""

import ast
import re
from pathlib import Path

from rulekit import Hit, Module, functions, local_nodes

RULE = "R1"
IP = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$|^::1$")
FILENAME = re.compile(
    r"^[\w.-]*\w\.(json|jsonl|toml|ya?ml|ini|cfg|conf|txt|log|csv|tsv|db|sqlite3?|pid|lock|sock|env)$"
)
HOST_KW = {"host", "hostname"}
PROG_KW = re.compile(r"^prog(_name)?$")  # argparse `prog=`, click's program-name keyword
FILE_KW = {"filename", "file", "path"}
PATH_CALLS = {"open", "Path", "PurePath", "joinpath", "join"}
BUSINESS_KW = re.compile(
    r"^(timeout|limit|ttl|delay|interval|threshold|rate|cap|retries|size|expires?|expiry|max_\w+|min_\w+"
    r"|\w+_(timeout|limit|ttl|interval|threshold|rate|delay|size|seconds|secs))$"
)
ORDERING = (ast.Lt, ast.Gt, ast.LtE, ast.GtE)
NEUTRAL = {0, 1, -1}


def call_name(call: ast.Call) -> str:
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""


def is_str(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def magic_number(node: ast.AST) -> ast.Constant | None:
    """A numeric literal other than the neutral 0, 1, -1 (a leading minus included)."""
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        node, sign = node.operand, -1
    if isinstance(node, ast.Constant) and type(node.value) in {int, float} and sign * node.value not in NEUTRAL:
        return node
    return None


def is_test(path: str) -> bool:
    p = Path(path)
    return (
        p.name.startswith("test_")
        or p.name.endswith("_test.py")
        or p.name == "conftest.py"
        or bool({"tests", "testutils"} & set(p.parts))
    )


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        if Path(m.path).name == "constants.py" or is_test(m.path):
            continue
        found: dict[int, tuple[ast.AST, str]] = {}  # one hit per literal node

        def report(node: ast.AST, what: str, found: dict[int, tuple[ast.AST, str]] = found) -> None:
            found.setdefault(id(node), (node, what))

        for node in ast.walk(m.tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                if is_str(node.right) and FILENAME.match(node.right.value):
                    report(node.right, f"file name `{node.right.value}` is an inline literal")
            elif isinstance(node, ast.Call):
                # an IP passed at a call site, also inside a tuple/list argument; a config-field default is not a call
                for arg in [*node.args, *(k.value for k in node.keywords)]:
                    for lit in ast.walk(arg):
                        if is_str(lit) and IP.match(lit.value):
                            report(lit, f"host `{lit.value}` is an inline literal")
                if call_name(node) in PATH_CALLS:
                    for a in node.args:
                        if is_str(a) and FILENAME.match(a.value):
                            report(a, f"file name `{a.value}` is an inline literal")
                for kw in node.keywords:
                    v = kw.value
                    if kw.arg is None:
                        continue
                    if not isinstance(v, ast.Constant):
                        continue
                    if kw.arg in HOST_KW and is_str(v) and v.value:
                        report(v, f"host `{v.value}` is an inline literal")
                    elif kw.arg == "port" and type(v.value) is int:
                        report(v, f"port `{v.value}` is an inline literal")
                    elif PROG_KW.match(kw.arg) and is_str(v):
                        report(v, f"program name `{v.value}` is an inline literal")
                    elif kw.arg in FILE_KW and is_str(v) and FILENAME.match(v.value):
                        report(v, f"file name `{v.value}` is an inline literal")
        for fn in functions(m.tree):
            if fn.name.startswith("test_"):
                continue
            for node in local_nodes(fn):
                if isinstance(node, ast.Compare) and any(isinstance(o, ORDERING) for o in node.ops):
                    for side in [node.left, *node.comparators]:
                        if num := magic_number(side):
                            report(num, f"threshold `{ast.unparse(side)}` is an inline literal")
                # business numbers in logic; declarative class/module-level field specs are left to the model
                elif isinstance(node, ast.Call):
                    for kw in node.keywords:
                        if kw.arg and BUSINESS_KW.match(kw.arg) and (num := magic_number(kw.value)):
                            report(num, f"`{kw.arg}={num.value}` is an inline business number")
        out += [Hit(m.path, n.lineno, f"{RULE} {what}: name it as a constant") for n, what in found.values()]
    return out
