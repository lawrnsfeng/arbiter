"""R50: `re.compile` without `re.VERBOSE`, verbose pattern parts without a `#` comment, unescaped literal spaces."""

import ast
import re

from rulekit import Hit, Module

RULE = "R50"
FLAGS = {
    "VERBOSE", "X", "IGNORECASE", "I", "MULTILINE", "M", "DOTALL", "S", "ASCII", "A", "UNICODE", "U", "LOCALE", "L",
    "NOFLAG", "DEBUG",
}  # fmt: skip
INLINE_VERBOSE = re.compile(
    r"""
    ^\(\?                 # an inline flag group at the start of the pattern
    [aiLmsu]*x            # whose flags include x (verbose)
    """,
    re.VERBOSE,
)


def _is_compile(call: ast.Call) -> bool:
    func: ast.expr = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "compile"
        and isinstance(func.value, ast.Name)
        and func.value.id in {"re", "regex"}
    )


def _flag_names(node: ast.expr) -> list[str] | None:
    """The flag names of `re.I | VERBOSE | 0`; None when an operand is not a flag name (a variable, a call)."""
    match node:
        case ast.BinOp(op=ast.BitOr()):
            left, right = _flag_names(node.left), _flag_names(node.right)
            return None if left is None or right is None else left + right
        case ast.Name(id=name) | ast.Attribute(attr=name) if name in FLAGS:
            return [name]
        case ast.Constant(value=0):
            return []
        case _:
            return None


def _verbose(call: ast.Call, pattern: str | None) -> bool | None:
    """Whether the call passes `VERBOSE` / `X` (as `re.X` or imported), or the pattern opens with an inline `(?x)`.

    None when a flag operand is not a flag name, so the flags cannot be read from the call."""
    if pattern and INLINE_VERBOSE.match(pattern):
        return True
    operands: list[ast.expr] = [*call.args[1:], *(kw.value for kw in call.keywords if kw.arg in {None, "flags"})]
    names: list[str] = []
    for op in operands:
        found: list[str] | None = _flag_names(op)
        if found is None:
            return None
        names += found
    return any(n in {"VERBOSE", "X"} for n in names)


def _code_and_comment(line: str) -> tuple[str, bool]:
    """Split a verbose pattern line at its first unescaped `#` outside a character class."""
    escaped: bool = False
    in_class: bool = False
    for i, ch in enumerate(line):
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif in_class:
            in_class = ch != "]"
        elif ch == "[":
            in_class = True
        elif ch == "#":
            return line[:i], True
    return line, False


def _literal_space(code: str) -> bool:
    """An unescaped space between two literal word characters (`from (`, not `GET | POST`), outside a class.

    Spaces next to operators or brackets are layout in verbose mode; between two plain letters or digits a space
    can only have been meant literally, and verbose mode silently drops it."""
    tokens: list[tuple[str, bool]] = []  # (character, is plain: unescaped and outside a character class)
    escaped: bool = False
    in_class: bool = False
    for ch in code:
        plain: bool = not escaped and not in_class
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif in_class:
            in_class = ch != "]"
        elif ch == "[":
            in_class = True
        tokens.append((ch, plain and ch != "\\"))
    for i, (ch, plain) in enumerate(tokens):
        if ch != " " or not plain:
            continue
        before = next((t for t in reversed(tokens[:i]) if t[0] != " "), None)
        after = next((t for t in tokens[i + 1 :] if t[0] != " "), None)
        if before and after and all(t[1] and t[0].isalnum() for t in (before, after)):
            return True
    return False


def _parts(m: Module, call: ast.Call, arg: ast.Constant) -> list[Hit]:
    out: list[Hit] = []
    lines: list[str] = arg.value.split("\n")
    exact: bool = arg.end_lineno is not None and arg.end_lineno - arg.lineno == len(lines) - 1
    uncommented: int = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        code, commented = _code_and_comment(line)
        uncommented += not commented and bool(code.strip())
        if _literal_space(code):
            where: int = arg.lineno + i if exact else call.lineno
            out.append(Hit(m.path, where, "R50 unescaped literal space in a verbose pattern: write `\\ `"))
    if uncommented:
        out.append(Hit(m.path, call.lineno, f"R50 {uncommented} pattern part(s) without a trailing `#` comment"))
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        strings: dict[str, str] = {
            t.id: n.value.value
            for n in m.tree.body
            if isinstance(n, ast.Assign | ast.AnnAssign)
            and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str)
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
            if isinstance(t, ast.Name)
        }  # plain and annotated module-level string constants
        for call in ast.walk(m.tree):
            if not (isinstance(call, ast.Call) and _is_compile(call) and call.args):
                continue
            arg: ast.expr = call.args[0]
            literal: str | None = arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None
            text: str | None = strings.get(arg.id) if isinstance(arg, ast.Name) else literal
            verbose: bool | None = _verbose(call, text)
            if verbose is False and text is None:
                continue  # a computed pattern may open with `(?x)`: left to the model
            if verbose is False:
                out.append(Hit(m.path, call.lineno, "R50 regex compiled without `re.VERBOSE`"))
            elif literal is not None and verbose:
                out += _parts(m, call, arg)
    return out
