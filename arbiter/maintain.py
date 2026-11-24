"""Deterministic maintainability facts (ledger MA-03): base vs head `ast` metrics on Python code the change added.

Zero model calls. A fact is a threshold crossed or worsened by this change; `block` marks a regression into the
block band, which is the only measured way a maintainability finding may block (MA-05).
"""

import ast
from collections.abc import Callable, Iterator
from pathlib import Path

from . import diff
from .model import DiffFile, Lang, MaintFact, Metric

# (warn, block); None never blocks. radon ranks C (11-20) and D (21+), pylint max-nested-blocks and max-args
# defaults, and the pstack "file pushed over 1k lines" presumptive blocker.
LIMITS: dict[Metric, tuple[int, int | None]] = {
    Metric.COMPLEXITY: (10, 20),
    Metric.NESTING: (4, 6),
    Metric.LENGTH: (60, 120),
    Metric.PARAMS: (6, None),
    Metric.FILE_LINES: (1000, 1000),
}
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
BRANCHES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.match_case)
BLOCKS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.TryStar, ast.Match)

type Def = ast.FunctionDef | ast.AsyncFunctionDef


def _walk(node: ast.AST) -> Iterator[ast.AST]:
    """Every node inside a function body, without descending into nested functions, lambdas or classes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPES):
            continue
        yield child
        yield from _walk(child)


def complexity(fn: Def) -> int:
    n = 1
    for x in _walk(fn):
        if isinstance(x, BRANCHES):
            n += 1
        elif isinstance(x, ast.comprehension):
            n += len(x.ifs)
        elif isinstance(x, ast.BoolOp):
            n += len(x.values) - 1
    return n


def _depth(stmts: list[ast.stmt], d: int) -> int:
    best = d
    for s in stmts:
        if isinstance(s, SCOPES) or not isinstance(s, BLOCKS):
            continue
        inner: list[list[ast.stmt]] = []
        match s:
            case ast.If(body=body, orelse=[ast.If() as elif_]):
                inner.append(body)
                best = max(best, _depth([elif_], d))  # an elif sits at its if's depth
            case ast.Match(cases=cases):
                inner += [c.body for c in cases]
            case (
                ast.Try(body=body, handlers=hs, orelse=orelse, finalbody=fin)
                | ast.TryStar(body=body, handlers=hs, orelse=orelse, finalbody=fin)
            ):
                inner += [body, orelse, fin, *(h.body for h in hs if isinstance(h, ast.ExceptHandler))]
            case _:
                inner += [getattr(s, "body", []), getattr(s, "orelse", [])]
        best = max(best, *(_depth(b, d + 1) for b in inner))
    return best


def nesting(fn: Def) -> int:
    return _depth(fn.body, 0)


def params(fn: Def, *, method: bool) -> int:
    a = fn.args
    names = [x.arg for x in (*a.posonlyargs, *a.args)]
    n = len(names) + len(a.kwonlyargs) + (a.vararg is not None) + (a.kwarg is not None)
    return n - (method and bool(names) and names[0] in ("self", "cls"))


def _measure(fn: Def, *, method: bool) -> dict[Metric, int]:
    return {
        Metric.COMPLEXITY: complexity(fn),
        Metric.NESTING: nesting(fn),
        Metric.LENGTH: (fn.end_lineno or fn.lineno) - fn.lineno + 1,
        Metric.PARAMS: params(fn, method=method),
    }


def _defs(mod: ast.Module) -> dict[str, tuple[Def, bool]]:
    """Top-level functions and methods of top-level classes by qualname; the flag marks methods."""
    out: dict[str, tuple[Def, bool]] = {}
    for n in mod.body:
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef):
            out[n.name] = (n, False)
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef):
                    out[f"{n.name}.{m.name}"] = (m, True)
    return out


def _parse(src: str | None) -> ast.Module | None:
    if src is None:
        return None
    try:
        return ast.parse(src)
    except (SyntaxError, ValueError):
        return None


def _fact(metric: Metric, base: int | None, head: int, *, path: str, q: str, lo: int, hi: int) -> MaintFact | None:
    warn, block = LIMITS[metric]
    if head <= warn or (base is not None and head <= base):
        return None
    eligible = block is not None and head > block and (base is None or base <= block)
    return MaintFact(
        id="",
        path=path,
        qualname=q,
        line=lo,
        end_line=hi,
        metric=metric,
        base=base,
        head=head,
        warn=warn,
        block=eligible,
    )


def facts(repo: Path, base: str, files: list[DiffFile], read: Callable[[str], str | None]) -> list[MaintFact]:
    out: list[MaintFact] = []
    for f in files:
        if f["lang"] != Lang.PYTHON or f["excluded"]:
            continue
        src = read(f["path"])
        head = _parse(src)
        if src is None or head is None:
            continue
        old_src = diff.git(repo, "show", f"{base}:{f['old_path'] or f['path']}", check=False)
        old = _parse(old_src)
        added = {n for h in f["hunks"] for n, _ in h["added"]}
        if not added:
            continue
        base_defs = _defs(old) if old else {}
        for q, (fn, method) in _defs(head).items():
            lo, hi = fn.lineno, fn.end_lineno or fn.lineno
            if not any(lo <= n <= hi for n in added):
                continue
            was = _measure(base_defs[q][0], method=base_defs[q][1]) if q in base_defs else None
            for metric, value in _measure(fn, method=method).items():
                if m := _fact(metric, was[metric] if was else None, value, path=f["path"], q=q, lo=lo, hi=hi):
                    out.append(m)
        n_head = len(src.splitlines())
        n_base = len(old_src.splitlines()) if old is not None else 0
        warn = LIMITS[Metric.FILE_LINES][0]
        if n_head > warn >= n_base and (
            m := _fact(Metric.FILE_LINES, n_base, n_head, path=f["path"], q="", lo=1, hi=n_head)
        ):
            out.append(m)
    out.sort(key=lambda m: (m["path"], m["line"], list(Metric).index(m["metric"])))
    for i, m in enumerate(out, 1):
        m["id"] = f"m{i:02d}"
    return out


def facts_text(fs: list[MaintFact]) -> str:
    """One line per fact for the A6d prompt: `m03 src/x.py:40-130 Foo.bar complexity 7→24 (warn >10, block >20)`."""
    rows = []
    for m in fs:
        warn, block = LIMITS[m["metric"]]
        was = "new" if m["base"] is None else m["base"]
        limits = f"warn >{warn}" + (f", block >{block}" if block is not None else "")
        tag = ", block-eligible" if m["block"] else ""
        rows.append(
            f"{m['id']} {m['path']}:{m['line']}-{m['end_line']} {m['qualname'] or '(file)'} "
            f"{m['metric']} {was}→{m['head']} ({limits}{tag})"
        )
    return "\n".join(rows)
