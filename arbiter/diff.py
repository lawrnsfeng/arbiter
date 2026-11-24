"""Resolve the base, parse base...HEAD into files and hunks, apply exclusions and size caps."""

import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import TypedDict

from . import ArbiterExit, lang
from .model import DiffFile, Hunk, Range

MAX_FILES = 500
MAX_LINES = 8000

LOCKFILES = (
    "uv.lock",
    "poetry.lock",
    "requirements*.txt",
    "go.sum",
    "Cargo.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock*",
)
VENDOR_DIRS = frozenset({"vendor", "node_modules", "dist", "build", "target"})
GENERATED = ("*_pb2.py", "*.pb.go", "*.gen.*", "*.min.js")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

type Repo = Path | str


class Change(TypedDict):
    repo: str
    base: str
    head: str
    files: list[DiffFile]
    commits: list[str]
    notes: list[str]


def hunk_ranges(hunks: list[Hunk]) -> list[Range]:
    return [(h["new_start"], h["new_start"] + max(h["new_count"], 1) - 1) for h in hunks]


def git(repo: Repo, *args: str, check: bool = True) -> str:
    p = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.quotePath=false", *args], capture_output=True, text=True, errors="replace"
    )
    if check and p.returncode:
        raise ArbiterExit(5, f"arbiter: git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def _verify(repo: Repo, ref: str) -> str | None:
    return git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False).strip() or None


def _merge_base(repo: Repo, a: str, b: str) -> str | None:
    return git(repo, "merge-base", a, b, check=False).strip() or None


def resolve_base(repo: Repo, ref: str | None) -> str:
    if ref:
        if not (sha := _verify(repo, ref)):
            raise ArbiterExit(2, f"arbiter: unknown base ref {ref}")
        return _merge_base(repo, sha, "HEAD") or sha
    for cand in ("origin/HEAD", "master", "main"):
        if _verify(repo, cand) and (mb := _merge_base(repo, "HEAD", cand)):
            return mb
    raise ArbiterExit(2, "arbiter: no base ref found (tried origin/HEAD, master, main); pass --base")


def exclusion(repo: Repo, head: str, path: str, binary: bool) -> str | None:
    p = PurePosixPath(path)
    if binary:
        return "binary"
    if any(fnmatch(p.name, g) for g in LOCKFILES):
        return "lockfile"
    if VENDOR_DIRS.intersection(p.parts[:-1]):
        return "vendored/build output"
    if any(fnmatch(p.name, g) for g in GENERATED):
        return "generated"
    head5 = git(repo, "show", f"{head}:{path}", check=False).splitlines()[:5]
    if any("Code generated" in ln and "DO NOT EDIT" in ln for ln in head5):
        return "generated"
    return None


def _count(group: str | None) -> int:
    """A missing hunk count means 1; an explicit 0 means an empty side."""
    return 1 if group is None else int(group)


def _parse_hunks(patch: str) -> dict[str, list[Hunk]]:
    """Parse `git diff -U0` output into {new_path: [hunk]}."""
    out: dict[str, list[Hunk]] = {}
    cur: list[Hunk] | None = None
    hunk: Hunk | None = None
    old: str | None = None
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            cur, hunk, old = None, None, None
        elif line.startswith("--- ") and hunk is None:
            old = line[4:].removeprefix("a/").rstrip("\t")
        elif line.startswith("+++ ") and hunk is None:
            new = line[4:].removeprefix("b/").rstrip("\t")
            cur = out.setdefault(old if new == "/dev/null" and old else new, [])
        elif (m := HUNK_RE.match(line)) and cur is not None:
            hunk = Hunk(
                old_start=int(m[1]),
                old_count=_count(m[2]),
                new_start=int(m[3]),
                new_count=_count(m[4]),
                added=[],
                removed=[],
            )
            cur.append(hunk)
        elif hunk is not None and line.startswith("+"):
            hunk["added"].append((hunk["new_start"] + len(hunk["added"]), line[1:]))
        elif hunk is not None and line.startswith("-"):
            hunk["removed"].append(line[1:])
    return out


def _numstat(repo: Repo, base: str) -> list[tuple[str, str, str, str | None]]:
    """(added, deleted, path, old_path) per file; renames arrive as two extra NUL-separated fields."""
    fields = iter(git(repo, "diff", "--numstat", "-z", "-M", f"{base}...HEAD").split("\0"))
    stats = []
    for rec in fields:
        if not rec.strip():
            continue
        added, deleted, path = rec.split("\t", 2)
        old_path = None
        if not path:
            old_path, path = next(fields), next(fields)
        stats.append((added, deleted, path, old_path))
    return stats


def collect(repo: Repo, base: str) -> Change:
    head = git(repo, "rev-parse", "HEAD").strip()
    notes = ["uncommitted changes excluded"] if git(repo, "status", "--porcelain", check=False).strip() else []
    hunks = _parse_hunks(git(repo, "diff", "-U0", "-M", f"{base}...HEAD"))
    files: list[DiffFile] = []
    for a, d, path, old_path in _numstat(repo, base):
        binary = a == "-"
        hs = hunks.get(path) or hunks.get(old_path or "") or []
        for h in hs:
            h["churn"] = len(h["added"]) + len(h["removed"])
        added, deleted = (0, 0) if binary else (int(a), int(d))
        files.append(
            DiffFile(
                path=path,
                old_path=old_path,
                lang=lang.of(path),
                added=added,
                deleted=deleted,
                churn=added + deleted,
                binary=binary,
                hunks=hs,
                excluded=exclusion(repo, head, path, binary),
            )
        )
    if not files:
        raise ArbiterExit(3, "arbiter: empty diff")
    included = [f for f in files if not f["excluded"]]
    lines = sum(f["churn"] for f in included)
    if len(included) > MAX_FILES or lines > MAX_LINES:
        raise ArbiterExit(
            4,
            f"arbiter: diff too large ({len(included)} files, {lines} lines); "
            f"split it (cap {MAX_FILES} files / {MAX_LINES} lines)",
        )
    subjects = git(repo, "log", "--format=%s%n%b%x00", f"{base}..HEAD").split("\0")
    return Change(
        repo=str(Path(repo).resolve()),
        base=base,
        head=head,
        files=files,
        commits=[s.strip() for s in subjects if s.strip()],
        notes=notes,
    )
