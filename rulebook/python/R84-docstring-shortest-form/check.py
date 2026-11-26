"""R84: docstrings longer than their form allows: module docstrings, summaries, body paragraphs, a Raises: tail."""

import ast
import inspect
import re

from rulekit import Hit, Module

RULE = "R84"
SECTIONS = (
    "Args|Arguments|Parameters|Returns|Return|Yields|Raises|Example|Examples|Note|Notes|Attributes|See Also|Warnings?"
)
SECTION = re.compile(rf"^({SECTIONS}):\s*$")
PARAGRAPH_LINES = 4
MIGRATION_HEADER = re.compile(r"^\s*(Revision ID|Revises|Create Date):")


def paragraphs(text: str) -> list[list[str]]:
    out: list[list[str]] = [[]]
    for line in text.splitlines():
        if line.strip():
            out[-1].append(line)
        elif out[-1]:
            out.append([])
    return [p for p in out if p]


def prose(paras: list[list[str]]) -> list[list[str]]:
    """Paragraphs before the first section header, doctest paragraphs dropped."""
    out: list[list[str]] = []
    for p in paras:
        if SECTION.match(p[0].strip()):
            break
        if not any(line.lstrip().startswith(">>>") for line in p):
            out.append(p)
    return out


def raises_unterminated(raw: str) -> bool:
    """A `Raises:` section that runs to the closing quotes with no blank line after it (D413)."""
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "Raises:":
            rest = lines[i + 1 :]
            if rest and not rest[-1].strip():
                rest = rest[:-1]  # the indent before closing quotes on their own line
            return all(r.strip() for r in rest)
    return False


def compiled_patterns(tree: ast.Module) -> set[str]:
    """Module-level names bound to `re.compile(...)`: the entries a patterns module's example list may name."""
    return {
        t.id
        for n in tree.body
        if isinstance(n, ast.Assign | ast.AnnAssign)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Attribute | ast.Name)
        and (n.value.func.attr if isinstance(n.value.func, ast.Attribute) else n.value.func.id) == "compile"
        for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
        if isinstance(t, ast.Name)
    }


def is_migration(tree: ast.Module) -> bool:
    bound = {
        t.id
        for n in tree.body
        if isinstance(n, ast.Assign | ast.AnnAssign)
        for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
        if isinstance(t, ast.Name)
    }
    return {"revision", "down_revision"} <= bound


def skipped(line: str, patterns: set[str], migration: bool) -> bool:
    """A generated migration header line, or an example-list entry naming one of the module's compiled patterns."""
    if migration and MIGRATION_HEADER.match(line):
        return True
    m = re.match(r"\s*`([A-Za-z_]\w*)`", line)
    return bool(m) and m[1] in patterns


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        for node in ast.walk(mod.tree):
            if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            raw = ast.get_docstring(node, clean=False)
            if raw is None:
                continue
            line = node.body[0].end_lineno or node.body[0].lineno  # closing quotes: the one line a comment can follow
            text = inspect.cleandoc(raw)
            if isinstance(node, ast.Module):
                migration, patterns = is_migration(node), compiled_patterns(node)
                prose_lines = [ln for ln in text.splitlines() if ln.strip() and not skipped(ln, patterns, migration)]
                if len(prose_lines) > 2:
                    hits.append(
                        Hit(mod.path, line, f"R84 module docstring has {len(prose_lines)} lines; the limit is 2")
                    )
                continue
            extra = sum(len(p) for p in prose(paragraphs(text))) - 1
            if extra > PARAGRAPH_LINES:
                hits.append(
                    Hit(
                        mod.path,
                        line,
                        f"R84 `{node.name}` has {extra} prose lines beyond the summary; the limit is {PARAGRAPH_LINES}",
                    )
                )
            if raises_unterminated(raw):
                hits.append(Hit(mod.path, line, f"R84 `{node.name}` Raises: section has no blank line after it"))
    return hits
