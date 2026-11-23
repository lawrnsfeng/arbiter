"""Conditional agents: regexes over added lines, declarations and paths."""

import re
from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import PurePosixPath

from .model import DiffFile, Lang, Unit

A4 = {
    Lang.PYTHON: re.compile(r"\b(threading|asyncio|concurrent\.futures|multiprocessing)\b|async def|\bawait\b|Lock\("),
    Lang.GO: re.compile(r"\bgo (func|[A-Za-z_][\w.]*\()|\bchan\b|\bsync\.|\batomic\.|select \{|errgroup"),
    Lang.RUST: re.compile(
        r"thread::spawn|tokio|async fn|\.await|Mutex|RwLock|Arc<|Atomic|unsafe impl (Send|Sync)"
        r"|rayon|crossbeam"
    ),
    Lang.TYPESCRIPT: re.compile(
        r"Promise\.(all|race|any|allSettled)|new Worker|SharedArrayBuffer|Atomics\.|\bawait\b"
        r"|setInterval"
    ),
}
A5_PATH = re.compile(
    r"(^|/)(migrations?|schema)/|\.sql$|\.proto$|openapi|\.graphql$|\.github/workflows/|Dockerfile"
    r"|rust-toolchain"
)
A5_PUBLIC = {
    Lang.PYTHON: re.compile(r"^(def|class) [A-Za-z]"),
    Lang.GO: re.compile(r"^func (\([^)]*\) )?[A-Z]|^type [A-Z]"),
    Lang.RUST: re.compile(r"^\s*pub(\(crate\))? "),
    Lang.TYPESCRIPT: re.compile(r"^export "),
}
A5_MANIFEST = re.compile(r"requires-python|^go \d|rust-version|\"engines\"")
MANIFESTS = frozenset({"pyproject.toml", "go.mod", "Cargo.toml", "package.json"})
SUPPLY = (
    "pyproject.toml",
    "requirements*.txt",
    "uv.lock",
    "poetry.lock",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "build.rs",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock*",
    ".npmrc",
)
A7_LOOP = re.compile(r"\b(for|while)\b|\.(map|forEach|for_each|iter)\(|range ")
A7_IO = re.compile(r"\b(query|execute|exec|fetch|request|get|find|select|load|read|write|send)\w*\(", re.IGNORECASE)
A7_SUBJECT = re.compile(r"perf|optimi|latency|slow|fast|cache", re.IGNORECASE)
A8_PATH = re.compile(r"Dockerfile|docker-compose|helm|k8s|\.tf$|\.env|(^|/)config/|\.github/workflows/|Makefile")
A8_LINE = re.compile(r"os\.environ|getenv|os\.Getenv|env::var|process\.env")
A9_PATH = re.compile(r"\.(tsx|jsx|html|vue|svelte|css)$")
PRIORITY = ("A4", "A5b", "A5", "A8", "A7", "A9")  # skip order under the agent budget is the reverse


def supply_chain(path: str) -> bool:
    name = PurePosixPath(path).name
    return any(fnmatch(name, g) for g in SUPPLY) or path.startswith(".github/workflows/")


def _any(rx: re.Pattern[str], lines: Iterable[str]) -> bool:
    return any(rx.search(t) for t in lines)


def for_unit(unit: Unit, files: dict[str, DiffFile], commits: list[str]) -> list[str]:
    """The conditional agent ids (A4 A5 A7 A8 A9) this unit fires. A5b is run-level (see run_level)."""
    fired: set[str] = set()
    perf_subject = any(A7_SUBJECT.search(c.splitlines()[0]) for c in commits if c)
    for piece in unit["files"]:
        path, lang = piece["path"], piece["lang"]
        hunks = [files[path]["hunks"][i] for i in piece["hunks"]]
        added = [t for h in hunks for _, t in h["added"]]
        removed = [t for h in hunks for t in h["removed"]]
        name = PurePosixPath(path).name
        if lang in A4 and _any(A4[lang], added):
            fired.add("A4")
        public = lang in A5_PUBLIC and not (lang == Lang.PYTHON and name.startswith("_"))
        if (
            A5_PATH.search(path)
            or (public and _any(A5_PUBLIC[lang], added + removed))
            or (name in MANIFESTS and _any(A5_MANIFEST, added + removed))
        ):
            fired.add("A5")
        loop_io = any(
            A7_LOOP.search(text) and A7_IO.search(text) for text in ("\n".join(t for _, t in h["added"]) for h in hunks)
        )
        if perf_subject or loop_io:
            fired.add("A7")
        if A8_PATH.search(path) or _any(A8_LINE, added):
            fired.add("A8")
        if A9_PATH.search(path) or (lang == Lang.RUST and any("rsx!" in t for t in added)):
            fired.add("A9")
    return sorted(fired)


def run_level(all_files: Iterable[DiffFile]) -> bool:
    """A5b fires once per run when any dependency manifest, lockfile, build.rs or CI workflow changed."""
    return any(supply_chain(f["path"]) for f in all_files)
