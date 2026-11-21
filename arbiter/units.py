"""Split the included diff files into small review units (OCR sizing defaults)."""

from pathlib import PurePosixPath

FILE_SPLIT = 200   # a file/group above this churn is split
CHUNK = 150        # chunk and merge ceiling
MERGE_FILES = 10
MARKERS = ("pyproject.toml", "setup.py", "go.mod", "Cargo.toml", "package.json")


def _project_root(path: str, tree: set[str]) -> str:
    p = PurePosixPath(path).parent
    while True:
        if any(str(p / m).removeprefix("./") in tree for m in MARKERS):
            return "" if str(p) == "." else str(p)
        if str(p) in (".", ""):
            return ""
        p = p.parent


def _piece(f: dict, hunk_idx: list[int]) -> dict:
    churn = sum(f["hunks"][i]["churn"] for i in hunk_idx) if f["hunks"] else f["churn"]
    return {"path": f["path"], "lang": f["lang"], "hunks": hunk_idx, "churn": churn, "file_churn": f["churn"]}


def _pieces(f: dict) -> list[dict]:
    """Whole file, or chunks of consecutive hunks <= CHUNK churn when the file exceeds FILE_SPLIT."""
    idx = list(range(len(f["hunks"])))
    if f["churn"] <= FILE_SPLIT or len(idx) <= 1:
        return [_piece(f, idx)]
    chunks, cur, cur_churn = [], [], 0
    for i in idx:
        c = f["hunks"][i]["churn"]
        if cur and cur_churn + c > CHUNK:
            chunks.append(cur)
            cur, cur_churn = [], 0
        cur.append(i)
        cur_churn += c
    chunks.append(cur)
    return [_piece(f, ch) for ch in chunks]


def _unit(pieces: list[dict]) -> dict:
    by_lang: dict[str, int] = {}
    for p in pieces:
        by_lang[p["lang"]] = by_lang.get(p["lang"], 0) + p["churn"]
    churn = sum(p["churn"] for p in pieces)
    return {"lang": max(by_lang, key=by_lang.get), "langs": sorted(by_lang), "files": pieces, "churn": churn,
            "plan_required": churn >= 100 or any(p["file_churn"] >= 50 for p in pieces)}


def build(files: list[dict], tree: set[str]) -> list[dict]:
    """files: included diff files (diff.collect entries); tree: every path in HEAD (for project markers)."""
    files = sorted(files, key=lambda f: f["path"])
    if len(files) < 4:
        if sum(f["churn"] for f in files) <= FILE_SPLIT:
            groups = [[_piece(f, list(range(len(f["hunks"])))) for f in files]]
        else:
            groups = [[p] for f in files for p in _pieces(f)]
    else:
        by_key: dict[tuple, list[dict]] = {}
        for f in files:
            key = (_project_root(f["path"], tree), str(PurePosixPath(f["path"]).parent), f["lang"])
            by_key.setdefault(key, []).append(f)
        groups = []
        for key in sorted(by_key):
            fs = by_key[key]
            if sum(f["churn"] for f in fs) > FILE_SPLIT:
                groups.extend([p] for f in fs for p in _pieces(f))
            else:
                groups.append([p for f in fs for p in _pieces(f)])
        merged: list[list[dict]] = []
        for g in groups:
            if merged:
                last = merged[-1]
                same_lang = {p["lang"] for p in last} == {p["lang"] for p in g}
                if (same_lang and sum(p["churn"] for p in last + g) <= CHUNK
                        and len({p["path"] for p in last + g}) <= MERGE_FILES):
                    last.extend(g)
                    continue
            merged.append(list(g))
        groups = merged
    units = [_unit(g) for g in groups if g]
    for n, u in enumerate(units, 1):
        u["id"] = f"u{n:02d}"
    return units
