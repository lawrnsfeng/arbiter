"""Hierarchical, syntax-aware review units and their shared context (research-decompose-hierarchical.md §4).

Behind `--decompose hier|hier-split`; `ocr` (units.py alone) stays the default until the §5 A/B passes.
Python only, with stdlib `ast` on HEAD (and on base for the change manifest); every other file, and any Python
file that does not parse, keeps today's hunk chunking.
"""

import ast
import copy
import json
import os
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from . import ArbiterExit, diff, units
from .model import DiffFile, Lang, Piece, Range, Ranges, Symbol, SymbolChange, Unit

BUDGET = 150  # churn per unit, the existing cap (units.CHUNK); ARBITER_UNIT_BUDGET sets the §5 B=75 arm
FLOOR = 40  # a unit under this merges into a sibling that can absorb it within the budget
AFFINITY = 4 / 3  # a definition and its in-diff call sites stay together up to this multiple of the budget
CALLERS_CAP = 10
CALLEES_CAP = 20
CODEGRAPH_SYMBOLS = 5  # `codegraph callees` lookups per unit; each one takes seconds
LIST_CAP = 100
LINE_CAP = 160
PROMPT_CAP = 24_000  # non-whitespace characters of unit diff + context map ([INFERENCE] in research §4.1)
INTERFACE = frozenset({SymbolChange.SIGNATURE, SymbolChange.REMOVED, SymbolChange.RENAMED})
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)
DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
CONSTRUCTORS = frozenset({"__init__", "__new__"})  # their callers call the class
DEF_LINE = re.compile(r"\s*(async\s+)?def\s")

type Def = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
type Group = list[Piece]


def budget() -> int:
    raw = os.environ.get("ARBITER_UNIT_BUDGET", str(BUDGET))
    if not raw.isdigit() or int(raw) < 1:
        raise ArbiterExit(2, f"arbiter: ARBITER_UNIT_BUDGET must be a positive integer, got {raw!r}")
    return int(raw)


@dataclass(slots=True)
class Code:
    """HEAD sources (through `read`) and their parse trees, parsed once per path."""

    tree: set[str]
    read: units.Reader
    _asts: dict[str, ast.Module | None] = field(default_factory=dict)
    _files: dict[tuple[str, str | None, int], str | None] = field(default_factory=dict)
    _by_name: dict[str, list[str]] = field(default_factory=dict)  # file name -> HEAD paths (absolute imports)

    def module(self, path: str) -> ast.Module | None:
        """The parsed HEAD file, or None when it is not Python, missing or a syntax error."""
        if path not in self._asts:
            src = self.read(path) if path.endswith(".py") else None
            try:
                self._asts[path] = ast.parse(src) if src is not None else None
            except (SyntaxError, ValueError):
                self._asts[path] = None
        return self._asts[path]

    def resolve(self, path: str, module: str | None, level: int) -> str | None:
        """The repo file a Python import in `path` names, or None (stdlib, third party, not found)."""
        key = (path, module, level)
        if key not in self._files:
            parts = module.split(".") if module else []
            if level:
                base = PurePosixPath(path).parents[level - 1]
                parts = [*(p for p in base.parts if p != "."), *parts]
            rel = "/".join(parts)
            found = None
            if not level and not self._by_name:
                for p in self.tree:
                    if p.endswith(".py"):
                        self._by_name.setdefault(PurePosixPath(p).name, []).append(p)
            for cand in (f"{rel}.py", f"{rel}/__init__.py") if rel else ():
                # absolute imports may sit under a source root (src/, a project dir): the shortest match wins
                name = PurePosixPath(cand).name
                hits = (
                    [cand]
                    if cand in self.tree
                    else []
                    if level
                    else [p for p in self._by_name.get(name, []) if p.endswith(f"/{cand}")]
                )
                if hits:
                    found = min(hits, key=len)
                    break
            self._files[key] = found
        return self._files[key]


# ---------------------------------------------------------------- split (§4.1)


def _start(s: ast.stmt) -> int:
    return min([s.lineno, *(d.lineno for d in getattr(s, "decorator_list", []))])


def _end(s: ast.stmt) -> int:
    return s.end_lineno or s.lineno


def _weights(f: DiffFile, skip: list[Range]) -> dict[int, int]:
    """Churn per new-side line: an added line counts 1, removed lines count at their hunk's new-side position."""
    w: dict[int, int] = {}
    for h in f["hunks"]:
        for n, _ in h["added"]:
            w[n] = w.get(n, 0) + 1
        if h["removed"]:
            w[h["new_start"]] = w.get(h["new_start"], 0) + len(h["removed"])
    return {n: c for n, c in w.items() if not any(a <= n <= b for a, b in skip)}


def _churn(w: dict[int, int], a: int, b: int) -> int:
    return sum(c for n, c in w.items() if a <= n <= b)


def _nodes(stmts: list[ast.stmt], lo: int, hi: int, *, runs: bool) -> list[tuple[int, int, list[ast.stmt]]]:
    """A block's children as spans covering [lo, hi] in source order: each def or class alone and, with `runs`,
    consecutive other statements together. Lines before a child (comments, blanks) go to the child before it."""
    heads: list[tuple[int, list[ast.stmt]]] = []
    for s in stmts:
        if runs and heads and not isinstance(s, DEFS) and not isinstance(heads[-1][1][-1], DEFS):
            heads[-1][1].append(s)
        else:
            heads.append((_start(s), [s]))
    return [
        (lo if i == 0 else start, heads[i + 1][0] - 1 if i + 1 < len(heads) else hi, ss)
        for i, (start, ss) in enumerate(heads)
    ]


def _split(stmts: list[ast.stmt], lo: int, hi: int, w: dict[int, int], limit: int, *, runs: bool = True) -> list[Range]:
    """Spans of at most `limit` churn where the syntax allows: definition -> method -> statement."""
    out: list[Range] = []
    for a, b, ss in _nodes(stmts, lo, hi, runs=runs):
        c = _churn(w, a, b)
        if not c:
            continue
        s = ss[0]
        if c <= limit:
            out.append((a, b))
        elif len(ss) > 1:  # module-level statements between definitions: one span per statement
            out += _split(ss, a, b, w, limit, runs=False)
        elif isinstance(s, DEFS) and s.body:
            body = _start(s.body[0])
            if _churn(w, a, body - 1):  # the header: decorators, def/class line, signature
                out.append((a, body - 1))
            if isinstance(s, ast.ClassDef):
                out += _split(s.body, body, b, w, limit)
            else:  # a function over budget: its body's top-level statements are the floor of the hierarchy
                out += [(x, y) for x, y, _ in _nodes(s.body, body, b, runs=False) if _churn(w, x, y)]
        else:
            out.append((a, b))  # one statement over budget cannot be split further
    return out


def _coalesce(rs: Iterable[Range]) -> list[Range]:
    out: list[Range] = []
    for a, b in sorted(rs):
        if out and a <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _pack(spans: list[Range], w: dict[int, int], limit: int) -> list[list[Range]]:
    """Greedy-merge adjacent spans in source order up to `limit` churn."""
    packs: list[list[Range]] = []
    churn = 0
    for s in spans:
        c = _churn(w, *s)
        if packs and churn + c <= limit:
            packs[-1].append(s)
            churn += c
        else:
            packs.append([s])
            churn = c
    return packs


def _sub_piece(f: DiffFile, spans: list[Range], w: dict[int, int]) -> Piece:
    """The hunks a set of spans touches, with `lines` clipped to the spans (a piece may cover part of one hunk)."""
    hr = diff.hunk_ranges(f["hunks"])
    hit = [(i, lo, hi) for i, (lo, hi) in enumerate(hr) if any(lo <= b and a <= hi for a, b in spans)]
    return Piece(
        path=f["path"],
        lang=f["lang"],
        hunks=[i for i, _, _ in hit],
        churn=sum(_churn(w, a, b) for a, b in spans),
        file_churn=f["churn"],
        lines=_coalesce((max(lo, a), min(hi, b)) for _, lo, hi in hit for a, b in spans if lo <= b and a <= hi),
    )


def _file_groups(f: DiffFile, code: Code, limit: int, skip: list[Range]) -> list[Group]:
    """One file's groups: whole when within budget, else by syntax, else (unparseable) by hunks as today."""
    if not f["hunks"]:
        return [[units._piece(f, [])]]
    w = _weights(f, skip)
    if not (total := sum(w.values())):
        return []  # only pure renames: they stay in the manifest, with no finder unit (§4.4)
    if total <= limit:
        p = units._piece(f, list(range(len(f["hunks"]))))
        p["churn"] = total
        return [[p]]
    mod = code.module(f["path"]) if f["lang"] == Lang.PYTHON else None
    if mod is None or not mod.body:
        return [[p] for p in units._pieces(f, limit, limit)]
    hi = max([*w, *(_end(s) for s in mod.body)])
    spans = _split(mod.body, 0, hi, w, limit)
    return [[_sub_piece(f, _coalesce(pk), w)] for pk in _pack(spans, w, limit)]


def _package(path: str, tree: set[str]) -> str:
    """The nearest directory holding `__init__.py` (the import package), else the file's directory."""
    for d in PurePosixPath(path).parents:
        if str(d / "__init__.py").removeprefix("./") in tree:
            return str(d)
    return str(PurePosixPath(path).parent)


def _join(a: Piece, b: Piece) -> Piece:
    out = Piece(
        path=a["path"],
        lang=a["lang"],
        hunks=sorted({*a["hunks"], *b["hunks"]}),
        churn=a["churn"] + b["churn"],
        file_churn=a["file_churn"],
    )
    if "lines" in a or "lines" in b:
        out["lines"] = _coalesce([*a.get("lines", []), *b.get("lines", [])])
    return out


def _absorb(g: Group, h: Group) -> None:
    """Add h's pieces to g; two pieces of one file become one piece."""
    for p in h:
        i = next((k for k, q in enumerate(g) if q["path"] == p["path"]), None)
        if i is None:
            g.append(p)
        else:
            g[i] = _join(g[i], p)


def _churn_of(g: Group) -> int:
    return sum(p["churn"] for p in g)


def piece_ranges(p: Piece, f: DiffFile) -> list[Range]:
    return p.get("lines") or diff.hunk_ranges([f["hunks"][i] for i in p["hunks"]])


def _changed(p: Piece, f: DiffFile) -> set[int]:
    rs = piece_ranges(p, f)
    return {n for h in f["hunks"] for n, _ in h["added"] if any(a <= n <= b for a, b in rs)}


@dataclass(slots=True)
class _Links:
    files: set[str] = field(default_factory=set)
    packages: set[str] = field(default_factory=set)
    defined: set[tuple[str, str]] = field(default_factory=set)  # (path, qualname) of definitions with changed lines
    called: set[tuple[str, str]] = field(default_factory=set)  # (path, qualname) resolved from calls on changed lines
    imports: set[str] = field(default_factory=set)  # repo files the group's modules import

    def __ior__(self, o: "_Links") -> "_Links":
        self.files |= o.files
        self.packages |= o.packages
        self.defined |= o.defined
        self.called |= o.called
        self.imports |= o.imports
        return self


def _links(g: Group, code: Code, by_path: dict[str, DiffFile]) -> _Links:
    out = _Links()
    for p in g:
        out.files.add(p["path"])
        out.packages.add(_package(p["path"], code.tree))
        if (mod := code.module(p["path"])) is None:
            continue
        changed = _changed(p, by_path[p["path"]])
        for s in mod.body:
            if isinstance(s, DEFS) and _touches(s, changed):
                out.defined.add((p["path"], s.name))
                if isinstance(s, ast.ClassDef):
                    out.defined |= {
                        (p["path"], f"{s.name}.{m.name}")
                        for m in s.body
                        if isinstance(m, FUNCS) and _touches(m, changed)
                    }
            if isinstance(s, ast.ImportFrom):
                out.imports |= {f for a in s.names if (f := _import_file(code, p["path"], s, a.name))}
            elif isinstance(s, ast.Import):
                out.imports |= {f for a in s.names if (f := code.resolve(p["path"], a.name, 0))}
        out.called |= {(file, q) for (file, _), (q, _) in _callees(code, p["path"], mod, changed).items()}
    return out


def _touches(n: ast.stmt, lines: set[int]) -> bool:
    return any(_start(n) <= x <= _end(n) for x in lines)


def _import_file(code: Code, path: str, s: ast.ImportFrom, name: str) -> str | None:
    """`from m import name`: the submodule m.name when it is one, else the module m."""
    sub = f"{s.module}.{name}" if s.module else name
    return code.resolve(path, sub, s.level) or code.resolve(path, s.module, s.level)


def _link_limit(a: _Links, b: _Links, limit: int) -> int:
    """The churn two groups may reach together: 1.33·B for a changed definition and its in-diff call sites,
    B for sibling modules (one package) that import each other, else 0 (no link)."""
    if a.defined & b.called or b.defined & a.called:
        return int(limit * AFFINITY)
    if a.packages & b.packages and (a.imports & b.files or b.imports & a.files):
        return limit
    return 0


def groups(files: list[DiffFile], tree: set[str], code: Code, limit: int, skip: Ranges) -> list[Group]:
    """Package -> module -> definition -> method -> statement, then greedy, affinity and floor merges."""
    by_key: dict[tuple[str, str, Lang], list[DiffFile]] = {}
    for f in files:
        pkg = _package(f["path"], tree) if f["lang"] == Lang.PYTHON else str(PurePosixPath(f["path"]).parent)
        by_key.setdefault((units.project_root(f["path"], tree), pkg, f["lang"]), []).append(f)
    gs: list[Group] = []
    for key in sorted(by_key):
        fgs = [g for f in by_key[key] for g in _file_groups(f, code, limit, skip.get(f["path"], []))]
        if fgs and sum(map(_churn_of, fgs)) <= limit:
            gs.append([p for g in fgs for p in g])
        else:
            gs.extend(fgs)
    merged: list[Group] = []
    for g in gs:
        if merged and units._mergeable(merged[-1], g, limit):
            _absorb(merged[-1], g)
        else:
            merged.append(list(g))
    by_path = {f["path"]: f for f in files}
    links = [_links(g, code, by_path) for g in merged]
    i = 0
    while i < len(merged):
        for j in range(i + 1, len(merged)):
            if (lim := _link_limit(links[i], links[j], limit)) and units._mergeable(merged[i], merged[j], lim):
                _absorb(merged[i], merged.pop(j))
                links[i] |= links.pop(j)
                break
        else:
            i += 1
    _floor(merged, links, limit)
    return merged


def _floor(gs: list[Group], links: list[_Links], limit: int) -> None:
    """A unit under FLOOR churn merges into the smallest sibling (same file or package) that can absorb it
    within the budget, wherever that sibling sits; greedy merging only ever tries the unit before it."""
    i = 0
    while i < len(gs):
        small = _churn_of(gs[i]) < FLOOR
        sib = [
            j
            for j in range(len(gs))
            if small and j != i and links[i].packages & links[j].packages and units._mergeable(gs[j], gs[i], limit)
        ]
        if not sib:
            i += 1
            continue
        j = min(sib, key=lambda k: _churn_of(gs[k]))
        _absorb(gs[j], gs[i])
        links[j] |= links[i]
        del gs[i], links[i]
        i = 0


# ---------------------------------------------------------------- change manifest (§4.2, §4.4)


def signature(n: Def) -> str:
    deco = "".join(f"@{ast.unparse(d)} " for d in n.decorator_list)
    if isinstance(n, ast.ClassDef):
        return f"{deco}class {n.name}({', '.join(map(ast.unparse, [*n.bases, *n.keywords]))})"
    ret = f" -> {ast.unparse(n.returns)}" if n.returns else ""
    kw = "async def" if isinstance(n, ast.AsyncFunctionDef) else "def"
    return f"{deco}{kw} {n.name}({ast.unparse(n.args)}){ret}"


def _key(n: Def, *, own: bool) -> str:
    """Line-free dump without the name: equal keys mean the same body. `own` drops a class's methods."""
    c = copy.copy(n)
    c.name = ""
    if own and isinstance(c, ast.ClassDef):
        c.body = [s for s in c.body if not isinstance(s, FUNCS)]
    return ast.dump(c)


def _defs(mod: ast.Module, peers: ast.Module) -> dict[str, tuple[str, Def]]:
    """qualname -> (kind, node): top-level definitions, and methods of classes both sides define."""
    shared = {s.name for s in peers.body if isinstance(s, ast.ClassDef)}
    out: dict[str, tuple[str, Def]] = {}
    for s in mod.body:
        if isinstance(s, DEFS):
            out[s.name] = ("class" if isinstance(s, ast.ClassDef) else "function", s)
        if isinstance(s, ast.ClassDef) and s.name in shared:
            out |= {f"{s.name}.{m.name}": ("method", m) for m in s.body if isinstance(m, FUNCS)}
    return out


def _entry(path: str, q: str, kind: str, change: SymbolChange, *, old: Def | None, new: Def | None) -> Symbol:
    s = Symbol(
        path=path,
        qualname=q,
        kind=kind,
        change=change,
        old_sig=signature(old) if old else "",
        new_sig=signature(new) if new else "",
        unit="",
    )
    if new:
        s["lines"] = (_start(new), _end(new))
    return s


def manifest(repo: Path | str, base: str, files: list[DiffFile], code: Code) -> list[Symbol]:
    """Changed Python symbols, base vs HEAD `ast`, zero model calls. A pure rename keeps its body (same key)."""
    out: list[Symbol] = []
    gone: list[tuple[str, str, str, Def]] = []  # (path, qualname, kind, node) only in base
    added: list[tuple[str, Symbol]] = []  # (body key, entry) only in head
    for f in files:
        if f["lang"] != Lang.PYTHON:
            continue
        head = code.module(f["path"]) or (
            ast.Module(body=[], type_ignores=[]) if code.read(f["path"]) is None else None
        )
        try:
            old = ast.parse(diff.git(repo, "show", f"{base}:{f['old_path'] or f['path']}", check=False))
        except (SyntaxError, ValueError):
            continue
        if head is None:
            continue
        hd, bd = _defs(head, old), _defs(old, head)
        for q, (kind, n) in hd.items():
            if q not in bd:
                added.append((_key(n, own=False), _entry(f["path"], q, kind, SymbolChange.ADDED, old=None, new=n)))
            elif signature(o := bd[q][1]) != signature(n):
                out.append(_entry(f["path"], q, kind, SymbolChange.SIGNATURE, old=o, new=n))
            elif _key(o, own=True) != _key(n, own=True):
                out.append(_entry(f["path"], q, kind, SymbolChange.MODIFIED, old=o, new=n))
        gone += [(f["old_path"] or f["path"], q, kind, n) for q, (kind, n) in bd.items() if q not in hd]
    for path, q, kind, n in gone:
        k = _key(n, own=False)
        if a := next((e for ek, e in added if ek == k and e["kind"] == kind and "old_qualname" not in e), None):
            a["change"], a["old_sig"], a["old_qualname"] = SymbolChange.RENAMED, signature(n), q
            if path != a["path"]:
                a["old_path"] = path
        else:
            out.append(_entry(path, q, kind, SymbolChange.REMOVED, old=n, new=None))
    out += [e for _, e in added]
    return sorted(out, key=lambda s: (s["path"], s.get("lines", (0, 0)), s["qualname"]))


def rename_spans(syms: list[Symbol]) -> Ranges:
    out: Ranges = {}
    for s in syms:
        if s["change"] == SymbolChange.RENAMED and "lines" in s:
            out.setdefault(s["path"], []).append(s["lines"])
    return out


def assign(syms: list[Symbol], us: list[Unit]) -> None:
    """Each symbol's unit: the one whose ranges cover its span (removed symbols: any unit with the file)."""
    for s in syms:
        lo, hi = s.get("lines", (0, 0))
        s["unit"] = next(
            (
                u["id"]
                for u in us
                for a, b in u.get("ranges", {}).get(s["path"], [])
                if "lines" in s and a <= hi and lo <= b
            ),
            "",
        )
        if not s["unit"] and s["change"] == SymbolChange.REMOVED:
            s["unit"] = next((u["id"] for u in us if s["path"] in u.get("ranges", {})), "")


def _clip(text: str) -> str:
    return text if len(text) <= LINE_CAP else f"{text[:LINE_CAP]}…"


def _codegraph(repo: Path, cmd: str, name: str, path: str) -> list[dict[str, Any]]:
    """`codegraph callers|callees` for one definition as JSON `definitions`, or [] (no index, no match, failure)."""
    if not (repo / ".codegraph").is_dir():
        return []
    try:
        p = subprocess.run(
            ["codegraph", cmd, "-p", str(repo), "-j", "-l", str(CALLEES_CAP), "-f", path, name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        d = json.loads(p.stdout) if p.returncode == 0 else {}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []
    return [x for x in d.get("definitions", []) if isinstance(x, dict)] if isinstance(d, dict) else []


def _grep(repo: Path, pattern: list[str], skip: tuple[str, Range] | None) -> list[str]:
    """`git grep` of HEAD's Python files, leaving out definition lines and the symbol's own span."""
    out = diff.git(repo, "grep", "-n", "-I", *pattern, "HEAD", "--", "*.py", check=False)
    hits = []
    for ln in out.splitlines():
        parts = ln.split(":", 3)
        if len(parts) < 4 or not parts[2].isdigit() or DEF_LINE.match(parts[3]):
            continue
        path, n = parts[1], int(parts[2])
        if skip and path == skip[0] and skip[1][0] <= n <= skip[1][1]:
            continue
        hits.append(f"{path}:{n} {_clip(parts[3].strip())}")
    return hits


def _caller_search(s: Symbol) -> tuple[str, list[str]] | None:
    """(codegraph symbol, git grep pattern) for one changed interface, or None for a dunder other than
    __init__/__new__ (called implicitly, so a text search finds nothing useful)."""
    cls, _, name = (s.get("old_qualname") or s["qualname"]).rpartition(".")
    if s["change"] != SymbolChange.SIGNATURE:  # removed or renamed: any straggling reference to the old name
        return name, ["-w", "-e", cls if cls and name in CONSTRUCTORS else name]
    if cls and name in CONSTRUCTORS:
        return cls, ["-E", "-e", rf"(^|[^[:alnum:]_.]){cls}[[:space:]]*\("]
    if name.startswith("__"):
        return None
    if cls:  # a method is called through an attribute
        return name, ["-E", "-e", rf"\.{name}[[:space:]]*\("]
    return name, ["-E", "-e", rf"(^|[^[:alnum:]_.]){name}[[:space:]]*\("]


def add_callers(repo: Path, syms: list[Symbol]) -> None:
    """Depth-1 callers of every changed interface: codegraph for a changed signature, else a `git grep` of HEAD
    (removed and renamed names have no definition left to resolve; the grep finds their stragglers)."""
    for s in syms:
        if s["change"] not in INTERFACE or (search := _caller_search(s)) is None:
            continue
        name, pattern = search
        sites: list[str] = []
        more = 0
        if s["change"] == SymbolChange.SIGNATURE:
            for d in _codegraph(repo, "callers", name, s["path"]):
                callers = {c.get("id"): c for c in d.get("callers", []) if isinstance(c, dict)}
                sites += [
                    f"{c.get('filePath')}:{e.get('line', c.get('startLine'))} (in {c.get('name')})"
                    for e in d.get("edges", [])
                    if isinstance(e, dict) and (c := callers.get(e.get("source")))
                ]
                more += max(int(d.get("total", 0)) - len(callers), 0)
        if not sites:
            sites = _grep(repo, pattern, (s["path"], s["lines"]) if "lines" in s else None)
        s["callers"], s["callers_more"] = sites[:CALLERS_CAP], more + max(len(sites) - CALLERS_CAP, 0)


# ---------------------------------------------------------------- rendered inputs (§4.2)


def manifest_text(syms: list[Symbol]) -> str:
    rows = []
    for s in syms[:LIST_CAP]:
        was = f" (was {s.get('old_path', s['path'])}::{s['old_qualname']})" if "old_qualname" in s else ""
        sig = f"{s['old_sig'] or '-'} → {s['new_sig'] or '-'}" if s["old_sig"] != s["new_sig"] else s["new_sig"]
        unit = s["unit"] or ("no unit (pure rename)" if s["change"] == SymbolChange.RENAMED else "-")
        rows.append(f"- {s['path']}::{s['qualname']}{was} | {s['kind']} | {s['change']} | {_clip(sig)} | {unit}")
    if len(syms) > LIST_CAP:
        rows.append(f"- … {len(syms) - LIST_CAP} more (truncated)")
    return "\n".join(rows)


def callers_text(syms: list[Symbol]) -> str:
    out = []
    for s in syms:
        if "callers" not in s:
            continue
        name = s.get("old_qualname") or s["qualname"]
        out.append(f"{s['change']} {s['path']}::{name}:")
        out += [f"  - {c}" for c in s["callers"]] or ["  - none found"]
        if s.get("callers_more"):
            out.append(f"  - … {s['callers_more']} more (truncated at {CALLERS_CAP}; grep for the rest)")
    return "\n".join(out)


def _dense(text: str) -> int:
    return sum(not c.isspace() for c in text)


def fit(udiff: str, ctx: str) -> str:
    """The context map cut to keep diff + map within PROMPT_CAP non-whitespace characters (§4.1 guard).
    The diff is never cut; a unit is already within the churn budget."""
    room = PROMPT_CAP - _dense(udiff)
    if not ctx or _dense(ctx) <= room:
        return ctx
    kept: list[str] = []
    for ln in ctx.splitlines():
        if (room := room - _dense(ln)) < 0:
            break
        kept.append(ln)
    return "\n".join([*kept, f"[context map truncated: unit prompt cap {PROMPT_CAP // 1000}k characters]"])


def others(files: list[DiffFile], us: list[Unit], u: Unit) -> str:
    """The PR's other changed files with churn and unit ids, so a finder knows where to look next."""
    mine = {p["path"] for p in u["files"]}
    rows = []
    for f in files:
        if f["path"] in mine:
            continue
        ids = [v["id"] for v in us if any(p["path"] == f["path"] for p in v["files"])]
        rows.append(f"- {f['path']} (churn {f['churn']}; {', '.join(ids) or 'no unit'})")
    return "\n".join(rows[:LIST_CAP] + ([f"- … {len(rows) - LIST_CAP} more"] if len(rows) > LIST_CAP else []))


def _doc1(n: Def) -> str:
    doc = ast.get_docstring(n)
    return f" — {_clip(doc.strip().splitlines()[0])}" if doc and doc.strip() else ""


def _class_header(c: ast.ClassDef) -> list[str]:
    out = [signature(c) + ":"]
    for s in c.body:
        if isinstance(s, ast.Assign | ast.AnnAssign):
            out.append(f"    {_clip(ast.unparse(s))}")
        elif isinstance(s, FUNCS) and s.name == "__init__":
            out.append(f"    {signature(s)}")
    return out[:LIST_CAP]


def _find(mod: ast.Module, name: str) -> Def | None:
    return next((s for s in mod.body if isinstance(s, DEFS) and s.name == name), None)


def _method(c: ast.ClassDef, name: str) -> Def | None:
    return next((s for s in c.body if isinstance(s, FUNCS) and s.name == name), None)


def _callees(code: Code, path: str, mod: ast.Module, changed: set[int]) -> dict[tuple[str, int], tuple[str, Def]]:
    """Repo definitions called on changed lines, by `ast` name resolution in the module and its imports."""
    imported: dict[str, tuple[str | None, str | None, int]] = {}  # alias -> (module, name or None, level)
    for s in mod.body:
        if isinstance(s, ast.ImportFrom):
            imported |= {a.asname or a.name: (s.module, a.name, s.level) for a in s.names}
        elif isinstance(s, ast.Import):  # `import a.b` binds `a`, not the module it names: only aliases and plain names
            imported |= {a.asname or a.name: (a.name, None, 0) for a in s.names if a.asname or "." not in a.name}
    classes = [s for s in mod.body if isinstance(s, ast.ClassDef)]
    found: dict[tuple[str, int], tuple[str, Def]] = {}

    def add(file: str | None, q: str) -> bool:
        m = code.module(file) if file else None
        head, _, attr = q.partition(".")
        n = _find(m, head) if m else None
        if n and attr:
            n = _method(n, attr) if isinstance(n, ast.ClassDef) else None
        if file and n:
            found.setdefault((file, n.lineno), (q, n))
        return n is not None

    for node in ast.walk(mod):
        if len(found) >= CALLEES_CAP:
            break
        if not isinstance(node, ast.Call) or node.lineno not in changed:
            continue
        match node.func:
            case ast.Name(id=name) if _find(mod, name):
                add(path, name)
            case ast.Name(id=name) if name in imported and imported[name][1]:
                m, orig, lvl = imported[name]
                add(code.resolve(path, m, lvl), orig or name)
            case ast.Attribute(value=ast.Name(id="self" | "cls"), attr=attr):
                if c := next((c for c in classes if c.lineno <= node.lineno <= _end(c)), None):
                    add(path, f"{c.name}.{attr}")
            case ast.Attribute(value=ast.Name(id=v), attr=attr) if isinstance(_find(mod, v), ast.ClassDef):
                add(path, f"{v}.{attr}")
            case ast.Attribute(value=ast.Name(id=v), attr=attr) if v in imported:
                m, orig, lvl = imported[v]
                # `from m import x; x.f()`: x is a submodule, or a class defined in m
                sub = f"{m}.{orig}" if m and orig else orig or m
                if not add(code.resolve(path, sub, lvl), attr) and orig:
                    add(code.resolve(path, m, lvl), f"{orig}.{attr}")
    return found


def context_map(repo: Path, code: Code, u: Unit, files: dict[str, DiffFile], syms: list[Symbol]) -> str:
    """The unit's read-only context: module docstring and imports, class headers, callee signatures and the
    callers of interfaces it changes. Signatures only; finders fetch bodies with their tools (D10)."""
    by_q = {(s["path"], s["qualname"]): s for s in syms}
    out: list[str] = []
    for p in u["files"]:
        mod = code.module(p["path"]) if p["lang"] == Lang.PYTHON else None
        if mod is None:
            continue
        rs = piece_ranges(p, files[p["path"]])
        changed = _changed(p, files[p["path"]])
        lines = [f"### {p['path']}"]
        if doc := ast.get_docstring(mod):
            lines.append(f"module docstring: {_clip(doc.strip().splitlines()[0])}")
        if imports := [_clip(ast.unparse(s)) for s in mod.body if isinstance(s, ast.Import | ast.ImportFrom)]:
            lines += ["imports:", *(f"  {x}" for x in imports[:LIST_CAP])]
        for c in mod.body:
            if (
                isinstance(c, ast.ClassDef)
                and any(a <= _end(c) and _start(c) <= b for a, b in rs)
                and not any(a <= c.lineno <= b for a, b in rs)
            ):
                lines += ["enclosing class header:", *(f"  {x}" for x in _class_header(c))]
        callees = _callees(code, p["path"], mod, changed)
        enclosing = [
            s.name for s in ast.walk(mod) if isinstance(s, FUNCS) and any(_start(s) <= n <= _end(s) for n in changed)
        ]
        for name in enclosing[:CODEGRAPH_SYMBOLS]:
            for d in _codegraph(repo, "callees", name, p["path"]):
                for c in d.get("callees", []):
                    if not isinstance(c, dict) or (m := code.module(str(c.get("filePath", "")))) is None:
                        continue
                    file, line = str(c["filePath"]), c.get("startLine")
                    n = next((x for x in ast.walk(m) if isinstance(x, DEFS) and x.lineno == line), None)
                    if n and len(callees) < CALLEES_CAP:
                        callees.setdefault((file, n.lineno), (n.name, n))
        if callees:
            lines.append("callees on changed lines (signature — docstring; read the body if it matters):")
            for (file, line), (q, n) in sorted(callees.items()):
                s = by_q.get((file, q))
                note = f" [{s['change']}: {s['old_sig']} → {s['new_sig']}]" if s and s["change"] in INTERFACE else ""
                lines.append(f"  - {file}:{line} {_clip(signature(n))}{_doc1(n)}{note}")
        if mine := [s for s in syms if s["path"] == p["path"] and s["unit"] == u["id"] and "callers" in s]:
            lines += ["callers of interfaces this unit changes:", *(f"  {x}" for x in callers_text(mine).splitlines())]
        out.append("\n".join(lines))
    return "\n\n".join(out)
