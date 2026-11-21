"""Resolve the base, parse base...HEAD into files and hunks, apply exclusions and size caps."""

import fnmatch
import re
import subprocess
from pathlib import Path, PurePosixPath

from . import ArbiterExit, lang

MAX_FILES = 500
MAX_LINES = 8000

LOCKFILES = ("uv.lock", "poetry.lock", "requirements*.txt", "go.sum", "Cargo.lock",
             "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock*")
VENDOR_DIRS = ("vendor", "node_modules", "dist", "build", "target")
GENERATED = ("*_pb2.py", "*.pb.go", "*.gen.*", "*.min.js")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def git(repo, *args: str, check: bool = True) -> str:
    p = subprocess.run(["git", "-C", str(repo), "-c", "core.quotePath=false", *args],
                       capture_output=True, text=True, errors="replace")
    if check and p.returncode:
        raise ArbiterExit(5, f"arbiter: git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def _verify(repo, ref: str) -> str | None:
    p = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                       capture_output=True, text=True)
    return p.stdout.strip() or None


def resolve_base(repo, ref: str | None) -> str:
    if ref:
        sha = _verify(repo, ref)
        if not sha:
            raise ArbiterExit(2, f"arbiter: unknown base ref {ref}")
        mb = subprocess.run(["git", "-C", str(repo), "merge-base", sha, "HEAD"], capture_output=True, text=True)
        return mb.stdout.strip() or sha
    for cand in ("origin/HEAD", "master", "main"):
        if _verify(repo, cand):
            mb = subprocess.run(["git", "-C", str(repo), "merge-base", "HEAD", cand], capture_output=True, text=True)
            if mb.returncode == 0 and mb.stdout.strip():
                return mb.stdout.strip()
    raise ArbiterExit(2, "arbiter: no base ref found (tried origin/HEAD, master, main); pass --base")


def exclusion(repo, head: str, path: str, binary: bool) -> str | None:
    p = PurePosixPath(path)
    if binary:
        return "binary"
    if any(fnmatch.fnmatch(p.name, g) for g in LOCKFILES):
        return "lockfile"
    if any(part in VENDOR_DIRS for part in p.parts[:-1]):
        return "vendored/build output"
    if any(fnmatch.fnmatch(p.name, g) for g in GENERATED):
        return "generated"
    head5 = subprocess.run(["git", "-C", str(repo), "show", f"{head}:{path}"], capture_output=True,
                           text=True, errors="replace").stdout.splitlines()[:5]
    if any("Code generated" in l and "DO NOT EDIT" in l for l in head5):
        return "generated"
    return None


def _parse_hunks(patch: str) -> dict[str, list[dict]]:
    """Parse `git diff -U0` output into {new_path: [hunk]}."""
    out: dict[str, list[dict]] = {}
    cur: list[dict] | None = None
    hunk = None
    old = new = None
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            cur, hunk, old, new = None, None, None, None
        elif line.startswith("--- ") and hunk is None:
            old = line[4:].removeprefix("a/").rstrip("\t")
        elif line.startswith("+++ ") and hunk is None:
            new = line[4:].removeprefix("b/").rstrip("\t")
            path = old if new == "/dev/null" else new
            cur = out.setdefault(path, [])
        elif (m := HUNK_RE.match(line)) and cur is not None:
            hunk = {"old_start": int(m[1]), "old_count": int(m[2] or 1 if m[2] != "0" else 0),
                    "new_start": int(m[3]), "new_count": int(m[4] or 1 if m[4] != "0" else 0),
                    "added": [], "removed": []}
            cur.append(hunk)
        elif hunk is not None and line[:1] == "+":
            hunk["added"].append([hunk["new_start"] + len(hunk["added"]), line[1:]])
        elif hunk is not None and line[:1] == "-":
            hunk["removed"].append(line[1:])
    return out


def collect(repo, base: str) -> dict:
    head = git(repo, "rev-parse", "HEAD").strip()
    notes = []
    if git(repo, "status", "--porcelain", check=False).strip():
        notes.append("uncommitted changes excluded")
    raw = git(repo, "diff", "--numstat", "-z", "-M", f"{base}...HEAD").split("\0")
    stats = []
    i = 0
    while i < len(raw):
        rec = raw[i]
        if not rec.strip():
            i += 1
            continue
        a, d, path = rec.split("\t", 2)
        old_path = None
        if path == "":  # rename: old and new follow as separate fields
            old_path, path = raw[i + 1], raw[i + 2]
            i += 2
        stats.append((a, d, path, old_path))
        i += 1
    hunks = _parse_hunks(git(repo, "diff", "-U0", "-M", f"{base}...HEAD"))
    files = []
    for a, d, path, old_path in stats:
        binary = a == "-"
        hs = hunks.get(path) or hunks.get(old_path or "") or []
        f = {"path": path, "old_path": old_path, "lang": lang.of(path),
             "added": 0 if binary else int(a), "deleted": 0 if binary else int(d),
             "binary": binary, "hunks": hs}
        f["churn"] = f["added"] + f["deleted"]
        for h in hs:
            h["churn"] = len(h["added"]) + len(h["removed"])
        f["excluded"] = exclusion(repo, head, path, binary)
        files.append(f)
    included = [f for f in files if not f["excluded"]]
    if not files:
        raise ArbiterExit(3, "arbiter: empty diff")
    lines = sum(f["churn"] for f in included)
    if len(included) > MAX_FILES or lines > MAX_LINES:
        raise ArbiterExit(4, f"arbiter: diff too large ({len(included)} files, {lines} lines); "
                           f"split it (cap {MAX_FILES} files / {MAX_LINES} lines)")
    subjects = git(repo, "log", "--format=%s%n%b%x00", f"{base}..HEAD").split("\0")
    return {"repo": str(Path(repo).resolve()), "base": base, "head": head, "files": files,
            "commits": [s.strip() for s in subjects if s.strip()], "notes": notes}
