"""Conditional agents: regexes over added lines, declarations and paths."""

import re
from pathlib import PurePosixPath

A4 = {
    "python": r"\b(threading|asyncio|concurrent\.futures|multiprocessing)\b|async def|\bawait\b|Lock\(",
    "go": r"\bgo (func|[A-Za-z_][\w.]*\()|\bchan\b|\bsync\.|\batomic\.|select \{|errgroup",
    "rust": r"thread::spawn|tokio|async fn|\.await|Mutex|RwLock|Arc<|Atomic|unsafe impl (Send|Sync)|rayon|crossbeam",
    "typescript": r"Promise\.(all|race|any|allSettled)|new Worker|SharedArrayBuffer|Atomics\.|\bawait\b|setInterval",
}
A5_PATH = r"(^|/)(migrations?|schema)/|\.sql$|\.proto$|openapi|\.graphql$|\.github/workflows/|Dockerfile|rust-toolchain"
A5_PUBLIC = {
    "python": r"^(def|class) [A-Za-z]",
    "go": r"^func (\([^)]*\) )?[A-Z]|^type [A-Z]",
    "rust": r"^\s*pub(\(crate\))? ",
    "typescript": r"^export ",
}
A5_MANIFEST = r"requires-python|^go \d|rust-version|\"engines\""
MANIFESTS = ("pyproject.toml", "go.mod", "Cargo.toml", "package.json")
SUPPLY = ("pyproject.toml", "requirements*.txt", "uv.lock", "poetry.lock", "go.mod", "go.sum", "Cargo.toml",
          "Cargo.lock", "build.rs", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock*",
          ".npmrc")
A7_LOOP = r"\b(for|while)\b|\.(map|forEach|for_each|iter)\(|range "
A7_IO = r"(?i)\b(query|execute|exec|fetch|request|get|find|select|load|read|write|send)\w*\("
A7_SUBJECT = r"(?i)perf|optimi|latency|slow|fast|cache"
A8_PATH = r"Dockerfile|docker-compose|helm|k8s|\.tf$|\.env|(^|/)config/|\.github/workflows/|Makefile"
A8_LINE = r"os\.environ|getenv|os\.Getenv|env::var|process\.env"
A9_PATH = r"\.(tsx|jsx|html|vue|svelte|css)$"
PRIORITY = ("A4", "A5b", "A5", "A8", "A7", "A9")  # skip order under budget is the reverse


def supply_chain(path: str) -> bool:
    import fnmatch
    p = PurePosixPath(path)
    return any(fnmatch.fnmatch(p.name, g) for g in SUPPLY) or path.startswith(".github/workflows/")


def for_unit(unit: dict, files: dict[str, dict], commits: list[str]) -> list[str]:
    """Return the conditional agent ids (A4 A5 A7 A8 A9) this unit fires. A5b is run-level (see run_level)."""
    fired = set()
    subj = any(re.search(A7_SUBJECT, c.splitlines()[0]) for c in commits if c)
    for piece in unit["files"]:
        path, lang = piece["path"], piece["lang"]
        hunks = [files[path]["hunks"][i] for i in piece["hunks"]]
        added = [t for h in hunks for _, t in h["added"]]
        removed = [t for h in hunks for t in h["removed"]]
        name = PurePosixPath(path).name
        if lang in A4 and any(re.search(A4[lang], t) for t in added):
            fired.add("A4")
        if re.search(A5_PATH, path):
            fired.add("A5")
        if lang in A5_PUBLIC and not (lang == "python" and name.startswith("_")):
            if any(re.search(A5_PUBLIC[lang], t) for t in added + removed):
                fired.add("A5")
        if name in MANIFESTS and any(re.search(A5_MANIFEST, t) for t in added + removed):
            fired.add("A5")
        if subj or any(re.search(A7_LOOP, "\n".join(h_added)) and re.search(A7_IO, "\n".join(h_added))
                       for h_added in ([t for _, t in h["added"]] for h in hunks)):
            fired.add("A7")
        if re.search(A8_PATH, path) or any(re.search(A8_LINE, t) for t in added):
            fired.add("A8")
        if re.search(A9_PATH, path) or (lang == "rust" and any("rsx!" in t for t in added)):
            fired.add("A9")
    return sorted(fired)


def run_level(all_files: list[dict]) -> bool:
    """A5b fires once per run when any dependency manifest, lockfile, build.rs or CI workflow changed."""
    return any(supply_chain(f["path"]) for f in all_files)
