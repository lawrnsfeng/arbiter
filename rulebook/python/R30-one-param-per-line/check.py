"""R30: wrapped multi-parameter signatures that are not one parameter per line with a trailing comma."""

import ast

from rulekit import Hit, Module, functions

RULE = "R30"

type Function = ast.FunctionDef | ast.AsyncFunctionDef


def _spans(fn: Function) -> list[tuple[int, int, int]]:
    """(first line, last line, end column) of every parameter, defaults included, in source order."""
    a = fn.args
    positional = [*a.posonlyargs, *a.args]
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(a.defaults)) + list(a.defaults)
    pairs: list[tuple[ast.arg, ast.expr | None]] = list(zip(positional, defaults, strict=True))
    if a.vararg:
        pairs.append((a.vararg, None))
    pairs += list(zip(a.kwonlyargs, a.kw_defaults, strict=True))
    if a.kwarg:
        pairs.append((a.kwarg, None))
    out = []
    for arg, default in pairs:
        end = default or arg
        out.append((arg.lineno, end.end_lineno or end.lineno, end.end_col_offset or 0))
    return sorted(out)


def _close(lines: list[bytes], line: int, col: int) -> tuple[int, bool]:
    """From just after the last parameter: (line of the closing paren, whether a comma came first)."""
    comma = False
    for i in range(line - 1, len(lines)):
        text = lines[i][col:] if i == line - 1 else lines[i]  # ast columns are UTF-8 byte offsets
        for ch in text:
            if ch == ord("#"):
                break
            if ch == ord(","):
                comma = True
            elif ch == ord(")"):
                return i + 1, comma
        col = 0
    return line, comma


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        lines = m.source.encode().splitlines()
        for fn in functions(m.tree):
            spans = _spans(fn)
            if len(spans) < 2:
                continue
            _, last_line, last_col = spans[-1]
            close_line, comma = _close(lines, last_line, last_col)
            if close_line == fn.lineno:
                continue  # fits on one line
            starts = [s[0] for s in spans]
            ends = [s[1] for s in spans]
            reasons = []
            if starts[0] == fn.lineno:
                reasons.append("a parameter sits on the `def` line")
            if any(starts[i + 1] <= ends[i] for i in range(len(spans) - 1)):
                reasons.append("parameters share a line")
            if not comma:
                reasons.append("no trailing comma")
            if reasons:
                hits.append(Hit(m.path, fn.lineno, f"{RULE} `{fn.name}` signature wraps but {'; '.join(reasons)}"))
    return hits
