"""T-04: files that historically change together with the changed files (git log; zero model calls)."""

from collections import Counter
from pathlib import Path

from . import diff


def neighbours(
    repo: Path,
    paths: list[str],
    tree: set[str],
    *,
    commits: int = 500,
    top: int = 5,
    min_count: int = 2,
    max_commit_files: int = 50,
) -> dict[str, list[tuple[str, int]]]:
    """Changed path -> up to `top` (path, commits together) for files in `tree` outside the change.

    Commits touching more than `max_commit_files` files (bulk renames, formatting) are skipped.
    """
    out = diff.git(repo, "log", "-n", str(commits), "--name-only", "--format=%x00", "HEAD", check=False)
    changed = set(paths)
    counts: dict[str, Counter[str]] = {}
    for chunk in out.split("\x00"):
        files = {ln for ln in chunk.splitlines() if ln}
        if not files or len(files) > max_commit_files:
            continue
        others = [f for f in files if f in tree and f not in changed]
        for path in files & changed:
            counts.setdefault(path, Counter()).update(others)
    result = {}
    for path, c in counts.items():
        ranked = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:top]  # name breaks ties: set order is random
        if near := [(f, n) for f, n in ranked if n >= min_count]:
            result[path] = near
    return result
