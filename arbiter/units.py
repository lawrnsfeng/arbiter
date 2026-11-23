"""Split the included diff files into small review units (OCR sizing defaults)."""

from collections import Counter
from collections.abc import Callable, Iterable
from itertools import chain
from pathlib import PurePosixPath

from .model import Decompose, DiffFile, Lang, Piece, Ranges, Unit

FILE_SPLIT = 200  # a file or group above this churn is split
CHUNK = 150  # chunk and merge ceiling
MERGE_FILES = 10
MARKERS = ("pyproject.toml", "setup.py", "go.mod", "Cargo.toml", "package.json")
PLAN_UNIT_CHURN = 100
PLAN_FILE_CHURN = 50

type Group = list[Piece]
type Reader = Callable[[str], str | None]  # a HEAD file's text, or None when it does not exist


def project_root(path: str, tree: set[str], markers: Iterable[str] = MARKERS) -> str:
    """Nearest ancestor directory of `path` holding a project marker ("" for the repo root)."""
    for d in PurePosixPath(path).parents:
        if any(str(d / m).removeprefix("./") in tree for m in markers):
            return "" if str(d) == "." else str(d)
    return ""


def _piece(f: DiffFile, hunk_idx: list[int]) -> Piece:
    churn = sum(f["hunks"][i].get("churn", 0) for i in hunk_idx) if f["hunks"] else f["churn"]
    return Piece(path=f["path"], lang=f["lang"], hunks=hunk_idx, churn=churn, file_churn=f["churn"])


def _pieces(f: DiffFile, split: int = FILE_SPLIT, chunk: int = CHUNK) -> list[Piece]:
    """The whole file, or chunks of consecutive hunks of at most `chunk` churn when the file exceeds `split`."""
    idx = list(range(len(f["hunks"])))
    if f["churn"] <= split or len(idx) <= 1:
        return [_piece(f, idx)]
    chunks: list[list[int]] = [[]]
    churn = 0
    for i in idx:
        c = f["hunks"][i].get("churn", 0)
        if chunks[-1] and churn + c > chunk:
            chunks.append([])
            churn = 0
        chunks[-1].append(i)
        churn += c
    return [_piece(f, ch) for ch in chunks]


def _unit(pieces: Group) -> Unit:
    by_lang: Counter[Lang] = Counter()
    for p in pieces:
        by_lang[p["lang"]] += p["churn"]
    churn = sum(p["churn"] for p in pieces)
    return Unit(
        id="",
        lang=by_lang.most_common(1)[0][0],
        langs=sorted(by_lang),
        files=pieces,
        churn=churn,
        plan_required=churn >= PLAN_UNIT_CHURN or any(p["file_churn"] >= PLAN_FILE_CHURN for p in pieces),
    )


def _mergeable(a: Group, b: Group, limit: int = CHUNK) -> bool:
    return (
        {p["lang"] for p in a} == {p["lang"] for p in b}
        and sum(p["churn"] for p in chain(a, b)) <= limit
        and len({p["path"] for p in chain(a, b)}) <= MERGE_FILES
    )


def _groups(files: list[DiffFile], tree: set[str]) -> list[Group]:
    if len(files) < 4:
        if sum(f["churn"] for f in files) <= FILE_SPLIT:
            return [[_piece(f, list(range(len(f["hunks"])))) for f in files]]
        return [[p] for f in files for p in _pieces(f)]
    by_key: dict[tuple[str, str, Lang], list[DiffFile]] = {}
    for f in files:
        key = (project_root(f["path"], tree), str(PurePosixPath(f["path"]).parent), f["lang"])
        by_key.setdefault(key, []).append(f)
    groups: list[Group] = []
    for key in sorted(by_key):
        fs = by_key[key]
        if sum(f["churn"] for f in fs) > FILE_SPLIT:
            groups.extend([p] for f in fs for p in _pieces(f))
        else:
            groups.append([p for f in fs for p in _pieces(f)])
    merged: list[Group] = []
    for g in groups:
        if merged and _mergeable(merged[-1], g):
            merged[-1].extend(g)
        else:
            merged.append(list(g))
    return merged


def build(
    files: list[DiffFile],
    tree: set[str],
    *,
    mode: Decompose = Decompose.OCR,
    read: Reader | None = None,
    budget: int = CHUNK,
    skip: Ranges | None = None,
) -> list[Unit]:
    """files: included diff files (diff.collect entries); tree: every path in HEAD (for project markers).

    Non-OCR modes split Python files by syntax (`read` returns a HEAD file); `skip` holds pure-rename spans.
    """
    ordered = sorted(files, key=lambda f: f["path"])
    if mode == Decompose.OCR or read is None:
        groups = _groups(ordered, tree)
    else:
        from . import decompose  # local import: decompose builds on this module's pieces and groups

        groups = decompose.groups(ordered, tree, decompose.Code(tree, read), budget, skip or {})
    units = [_unit(g) for g in groups if g]
    for n, u in enumerate(units, 1):
        u["id"] = f"u{n:02d}"
    return units
