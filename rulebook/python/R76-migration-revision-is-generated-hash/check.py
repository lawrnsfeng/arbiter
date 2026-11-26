"""R76: migration ids that are not 12-hex hashes, and docstring/filename ids that disagree with them."""

import ast
import re
from pathlib import Path

from rulekit import Hit, Module

RULE = "R76"
HASH = re.compile(r"^[0-9a-f]{12}$")


def header(tree: ast.Module) -> dict[str, ast.stmt]:
    """Module-level `revision` / `down_revision` bindings, plain or annotated."""
    out: dict[str, ast.stmt] = {}
    for node in tree.body:
        targets = (
            node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        )
        for t in targets:
            if isinstance(t, ast.Name) and t.id in {"revision", "down_revision"}:
                out[t.id] = node
    return out


def strings(node: ast.expr | None) -> list[str] | None:
    """The id strings of a binding value; None when the value is not literal."""
    if isinstance(node, ast.Constant) and (node.value is None or isinstance(node.value, str)):
        return [] if node.value is None else [node.value]
    if isinstance(node, ast.Tuple | ast.List) and all(
        isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts
    ):
        return [e.value for e in node.elts]
    return None


def docstring_ids(tree: ast.Module, key: str) -> list[str] | None:
    doc = ast.get_docstring(tree) or ""
    m = re.search(rf"^{key}:[ \t]*(.*)$", doc, re.MULTILINE)
    return None if m is None else [s.strip() for s in m[1].split(",") if s.strip()]


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        head = header(mod.tree)
        if set(head) != {"revision", "down_revision"}:
            continue
        rev_node, down_node = head["revision"], head["down_revision"]
        rev = strings(rev_node.value)
        down = strings(down_node.value)
        if rev and len(rev) == 1:
            if not HASH.match(rev[0]):
                hits.append(Hit(mod.path, rev_node.lineno, f"R76 revision `{rev[0]}` is not a generated 12-hex id"))
            doc = docstring_ids(mod.tree, "Revision ID")
            if doc is not None and doc != rev:
                hits.append(
                    Hit(mod.path, rev_node.lineno, f"R76 docstring `Revision ID: {', '.join(doc)}` != revision")
                )
            stem = Path(mod.path).stem
            if "_" in stem and stem.split("_", 1)[0] != rev[0]:
                hits.append(
                    Hit(mod.path, rev_node.lineno, f"R76 filename prefix `{stem.split('_', 1)[0]}` != revision")
                )
        if down is not None:
            hits.extend(
                Hit(mod.path, down_node.lineno, f"R76 down_revision `{d}` is not a generated 12-hex id")
                for d in down
                if not HASH.match(d)
            )
            doc = docstring_ids(mod.tree, "Revises")
            if doc is not None and doc != down:
                hits.append(
                    Hit(mod.path, down_node.lineno, f"R76 docstring `Revises: {', '.join(doc)}` != down_revision")
                )
    return hits
