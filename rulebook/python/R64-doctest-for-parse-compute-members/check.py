"""R64: str/bytes/int subclasses without a `>>>` example (or refusal example), and unskipped clock doctests."""

import ast
import re

from rulekit import Hit, Module, base_name

RULE = "R64"
FORM_BASES = {"str", "bytes", "int"}
CLOCK = re.compile(r"\b(now|utcnow|today|monotonic|perf_counter|time_ns)\(|\btime\.time\(")


def form_class(cls: ast.ClassDef) -> bool:
    names = {base_name(b) for b in cls.bases}
    return bool(names & FORM_BASES) and not any(n.endswith(("Enum", "Flag")) for n in names)


def docstring_node(node: ast.AST) -> ast.Constant | None:
    body = getattr(node, "body", None)
    if isinstance(body, list) and body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        return body[0].value if isinstance(body[0].value.value, str) else None
    return None


def refusal_hit(m: Module, cls: ast.ClassDef, doc: str) -> Hit | None:
    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef) or fn.name != "__new__":
            continue
        raised = {
            base_name(r.exc.func if isinstance(r.exc, ast.Call) else r.exc)
            for r in ast.walk(fn)
            if isinstance(r, ast.Raise) and r.exc is not None
        }
        if raised and ("Traceback" not in doc or not any(name in doc for name in raised)):
            return Hit(
                m.path, fn.lineno, f"{RULE} `{cls.name}.__new__` refuses values but no example shows the refusal"
            )
    return None


def form_hits(m: Module) -> list[Hit]:
    hits = []
    for cls in ast.walk(m.tree):
        if not isinstance(cls, ast.ClassDef) or not form_class(cls):
            continue
        doc = docstring_node(cls)
        if doc is None or ">>>" not in doc.value:
            hits.append(Hit(m.path, cls.lineno, f"{RULE} `{cls.name}` subclasses a form type without a `>>>` example"))
        elif hit := refusal_hit(m, cls, doc.value):
            hits.append(hit)
    return hits


def clock_hits(m: Module) -> list[Hit]:
    hits = []
    for node in ast.walk(m.tree):
        if (doc := docstring_node(node)) is None:
            continue
        for offset, line in enumerate(doc.value.split("\n")):
            text = line.strip()
            if text.startswith(">>>") and CLOCK.search(text) and "doctest: +SKIP" not in text:
                hits.append(Hit(m.path, doc.lineno + offset, f"{RULE} time-dependent example lacks `# doctest: +SKIP`"))
    return hits


def check(modules: list[Module]) -> list[Hit]:
    return [hit for m in modules for hit in form_hits(m) + clock_hits(m)]
