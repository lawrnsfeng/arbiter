"""R14: compiled regexes outside a patterns-only module; in a patterns module, unnamed or undocumented patterns."""

import ast
import re

from rulekit import Hit, Module

RULE = "R14"
REGEX_MODULES = {"re", "regex"}
EXAMPLE = re.compile(r"`([^`]+)`")


def compile_call(node: ast.AST, direct: set[str]) -> bool:
    """`re.compile("literal", ...)` or `compile("literal")` imported from `re`; a computed pattern cannot move."""
    if not isinstance(node, ast.Call) or not node.args or not isinstance(node.args[0], ast.Constant | ast.JoinedStr):
        return False
    f = node.func
    return (
        isinstance(f, ast.Attribute)
        and f.attr == "compile"
        and isinstance(f.value, ast.Name)
        and f.value.id in REGEX_MODULES
    ) or (isinstance(f, ast.Name) and f.id in direct)


def imported_flags(tree: ast.Module) -> dict[str, re.RegexFlag]:
    """Flags bound by `from re import VERBOSE [as V]`, by local name."""
    return {
        a.asname or a.name: flag
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module in REGEX_MODULES
        for a in n.names
        if isinstance(flag := getattr(re, a.name, None), re.RegexFlag)
    }


def static_pattern(call: ast.Call, names: dict[str, re.RegexFlag]) -> re.Pattern[str] | None:
    """The compiled pattern when the pattern and flags are literal, else None. Flags count as `re.X`, as a name
    imported from `re`, or inline (`(?x)`, which `re.compile` reads itself)."""
    pat = call.args[0]
    if not (isinstance(pat, ast.Constant) and isinstance(pat.value, str)):
        return None
    flags = 0
    for f in [*call.args[1:2], *(k.value for k in call.keywords if k.arg == "flags")]:
        for part in ast.walk(f):
            if isinstance(part, ast.Attribute) and isinstance(getattr(re, part.attr, None), re.RegexFlag):
                flags |= getattr(re, part.attr)
            elif isinstance(part, ast.Name) and part.id in names:
                flags |= names[part.id]
    try:
        return re.compile(pat.value, flags)
    except re.error:
        return None


def pattern_hits(m: Module, direct: set[str]) -> list[Hit]:
    """Checks on a patterns-only module: UPPER_CASE names, examples in docstrings that the pattern matches."""
    out: list[Hit] = []
    lines = m.source.splitlines()
    module_doc = ast.get_docstring(m.tree) or ""
    body = m.tree.body
    names = imported_flags(m.tree)
    for s in body:
        if not (isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name)):
            continue
        if not compile_call(s.value, direct):
            continue
        name = s.targets[0].id
        if not name.isupper():
            out.append(Hit(m.path, s.lineno, f"{RULE} pattern `{name}` is not an UPPER_CASE name for what it matches"))
        if s.lineno >= 2 and lines[s.lineno - 2].lstrip().startswith("#"):
            out.append(
                Hit(
                    m.path,
                    s.lineno,
                    f"{RULE} pattern `{name}` is explained by a comment: put the example in its docstring",
                )
            )
        # the example sits on a module-docstring line naming the constant; a bare string after it is no docstring
        doc = "\n".join(ln for ln in module_doc.splitlines() if name in ln)
        examples = EXAMPLE.findall(doc)
        if not examples:
            out.append(Hit(m.path, s.lineno, f"{RULE} pattern `{name}` has no example in the module docstring"))
        elif (compiled := static_pattern(s.value, names)) and not any(compiled.search(e) for e in examples):
            out.append(Hit(m.path, s.lineno, f"{RULE} pattern `{name}` does not match its docstring example"))
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        direct = {
            a.asname or a.name
            for n in ast.walk(m.tree)
            if isinstance(n, ast.ImportFrom) and n.module in REGEX_MODULES
            for a in n.names
            if a.name == "compile"
        }
        has_code = any(isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) for n in ast.walk(m.tree))
        if not has_code:
            out += pattern_hits(m, direct)
            continue
        for n in ast.walk(m.tree):
            if compile_call(n, direct):
                out.append(
                    Hit(m.path, n.lineno, f"{RULE} regex compiled beside code: move it, named, to the patterns module")
                )
    return out
