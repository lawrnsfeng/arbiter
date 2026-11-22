"""Detect gates (build/lint/type/test) and analyzers per language; parse their diagnostics."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

CACHE = Path(os.environ.get("ARBITER_CACHE", Path.home() / ".cache" / "arbiter"))
BIN = CACHE / "bin"
SEMGREP_RULES = CACHE / "semgrep"
# name -> (installer, package); installed into CACHE, never into the reviewed project
EPHEMERAL = {
    "ruff": ("uv", "ruff"),
    "bandit": ("uv", "bandit"),
    "semgrep": ("uv", "semgrep"),
    "staticcheck": ("go", "honnef.co/go/tools/cmd/staticcheck@latest"),
    "gosec": ("go", "github.com/securego/gosec/v2/cmd/gosec@latest"),
}
INSTALLED = ("golangci-lint", "govulncheck", "cargo-deny")
SEMGREP_PACKS = {"python": "p/python", "rust": "p/rust", "typescript": "p/typescript"}
MARKER = {"python": "pyproject.toml", "go": "go.mod", "rust": "Cargo.toml", "typescript": "package.json"}


def _root(path: str, marker: str, tree: set[str]) -> str:
    p = PurePosixPath(path).parent
    while True:
        cand = str(p / marker).removeprefix("./")
        if cand in tree:
            return "" if str(p) == "." else str(p)
        if str(p) in (".", ""):
            return ""
        p = p.parent


def _rel(files: list[str], root: str) -> list[str]:
    return [f[len(root) + 1:] if root and f.startswith(root + "/") else f for f in files]


def _semgrep(lang: str, root: str, files: list[str]) -> dict:
    rules = SEMGREP_RULES / (SEMGREP_PACKS[lang].replace("/", "-") + ".yml")
    return {"name": f"semgrep {SEMGREP_PACKS[lang]}", "kind": "analyzer", "parse": "semgrep", "needs": "semgrep",
            "cmd": ["semgrep", "scan", "--config", str(rules), "--json", "--dataflow-traces", "--metrics=off",
                    "--disable-version-check", *files]}


def detect(tree: set[str], read, changed: dict[str, list[str]], affected: list[str]) -> list[dict]:
    """tree: HEAD paths; read(path) -> str|None at HEAD; changed: lang -> changed file paths;
    affected: test files from codegraph (may be empty). Returns tool specs (cmd relative to `root`)."""
    out = []
    for lang, files in changed.items():
        if lang not in MARKER:
            continue
        roots: dict[str, list[str]] = {}
        for f in files:
            roots.setdefault(_root(f, MARKER[lang], tree), []).append(f)
        for root, fs in sorted(roots.items()):
            rel = _rel(fs, root)
            j = (lambda p: f"{root}/{p}" if root else p)
            aff = [a for a in _rel([a for a in affected if a.startswith(root)], root) if a]
            specs = globals()[f"_{lang}"](tree, read, j, rel, aff)
            for s in specs:
                s.update(lang=lang, root=root)
            out.extend(specs)
    for s in out:
        s.setdefault("source", "ephemeral" if s.get("needs") else "project")
    return out


def _python(tree, read, j, rel, aff):
    py = read(j("pyproject.toml")) or ""
    lock = read(j("uv.lock")) or ""
    out = []
    if re.search(r"""["']ruff\b""", py) or 'name = "ruff"' in lock:
        out.append({"name": "ruff", "kind": "lint", "cmd": ["uv", "run", "ruff", "check", "--output-format=concise", *rel]})
    elif "[tool.ruff]" in py or j("ruff.toml") in tree or j(".ruff.toml") in tree:
        out.append({"name": "ruff", "kind": "lint", "needs": "ruff",
                    "cmd": ["ruff", "check", "--output-format=concise", *rel]})
    if "[tool.mypy]" in py or j("mypy.ini") in tree:
        out.append({"name": "mypy", "kind": "type", "cmd": ["uv", "run", "mypy", *rel]})
    if "[tool.pyright]" in py or j("pyrightconfig.json") in tree:
        out.append({"name": "pyright", "kind": "type", "cmd": ["uv", "run", "pyright", *rel]})
    if any(re.search(r"(^|/)(test_[^/]*|[^/]*_test)\.py$", p) for p in tree):
        out.append({"name": "pytest", "kind": "test", "cmd": ["uv", "run", "pytest", "-q", "-x", *aff]})
    out.append({"name": "bandit", "kind": "analyzer", "parse": "bandit", "needs": "bandit",
                "cmd": ["bandit", "-f", "json", "-q", *rel]})
    out.append(_semgrep("python", "", rel))
    return out


def _go(tree, read, j, rel, aff):
    pkgs = sorted({"./" + str(PurePosixPath(a).parent) for a in aff}) or ["./..."]
    out = [{"name": "go build", "kind": "build", "cmd": ["go", "build", "./..."]},
           {"name": "go vet", "kind": "type", "cmd": ["go", "vet", "./..."]}]
    if any(re.fullmatch(r"\.golangci\.(ya?ml|toml|json)", p.rsplit("/", 1)[-1]) for p in tree):
        out.append({"name": "golangci-lint", "kind": "lint", "source": "installed", "cmd": ["golangci-lint", "run"]})
    else:
        out.append({"name": "staticcheck", "kind": "lint", "needs": "staticcheck", "cmd": ["staticcheck", "./..."]})
    if any(p.endswith("_test.go") for p in tree):
        out.append({"name": "go test", "kind": "test", "cmd": ["go", "test", "-count=1", *pkgs]})
    out.append({"name": "gosec", "kind": "analyzer", "parse": "gosec", "needs": "gosec",
                "cmd": ["gosec", "-fmt=json", "-quiet", "./..."]})
    out.append({"name": "govulncheck", "kind": "analyzer", "parse": "raw", "net": True, "source": "installed",
                "cmd": ["govulncheck", "-json", "./..."]})
    return out


def _rust(tree, read, j, rel, aff):
    out = [{"name": "clippy", "kind": "type", "cmd": ["cargo", "clippy", "--all-targets", "--locked",
                                                         "--message-format=short"]},
           {"name": "rustfmt", "kind": "lint", "cmd": ["cargo", "fmt", "--check"]},
           {"name": "cargo test", "kind": "test", "cmd": ["cargo", "test", "--locked"]}]
    if j("deny.toml") in tree:
        out.append({"name": "cargo-deny", "kind": "analyzer", "parse": "raw", "net": True, "source": "installed",
                    "cmd": ["cargo", "deny", "check"]})
    out.append(_semgrep("rust", "", rel))
    return out


def _typescript(tree, read, j, rel, aff):
    pm = ("pnpm" if j("pnpm-lock.yaml") in tree else "yarn" if j("yarn.lock") in tree
          else "bun" if any(p in tree for p in (j("bun.lock"), j("bun.lockb"))) else "npm")
    out = []
    if j("tsconfig.json") in tree:
        out.append({"name": "tsc", "kind": "type", "cmd": ["npx", "--no-install", "tsc", "--noEmit", "-p", "."]})
    if any(re.fullmatch(r"(eslint\.config\.[cm]?[jt]s|\.eslintrc(\.\w+)?)", p.rsplit("/", 1)[-1]) for p in tree):
        out.append({"name": "eslint", "kind": "lint", "parse": "eslint",
                    "cmd": ["npx", "--no-install", "eslint", "-f", "json", *rel]})
    try:
        test = json.loads(read(j("package.json")) or "{}").get("scripts", {}).get("test")
    except json.JSONDecodeError:
        test = None
    if test:
        if "vitest" in test and aff:
            cmd = ["npx", "--no-install", "vitest", "run", *aff]
        elif "jest" in test and aff:
            cmd = ["npx", "--no-install", "jest", *aff]
        else:
            cmd = [pm, "test"]
        out.append({"name": f"{pm} test", "kind": "test", "cmd": cmd, "pm": pm})
    out.append(_semgrep("typescript", "", rel))
    for s in out:
        s.setdefault("pm", pm)
    return out


def resolve(spec: dict) -> dict:
    """Mark a spec available/unavailable now that ephemeral tools may be installed."""
    if spec.get("needs"):
        spec["available"] = (BIN / spec["needs"]).exists()
        if spec["available"]:
            spec["cmd"] = [str(BIN / spec["cmd"][0]), *spec["cmd"][1:]]
    else:
        spec["available"] = bool(shutil.which(spec["cmd"][0], path=os.environ.get("PATH")))
    return spec


def prefetch(log) -> dict[str, str]:
    """Install ephemeral analyzers into CACHE (network on, outside the reviewed repo). Returns name -> version."""
    BIN.mkdir(parents=True, exist_ok=True)
    SEMGREP_RULES.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "UV_TOOL_DIR": str(CACHE / "uvtools"), "UV_TOOL_BIN_DIR": str(BIN), "GOBIN": str(BIN)}
    versions = {}
    for name, (kind, pkg) in EPHEMERAL.items():
        if not (BIN / name).exists():
            cmd = ["uv", "tool", "install", "--quiet", pkg] if kind == "uv" else ["go", "install", pkg]
            p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
            if p.returncode:
                log(f"prefetch {name} failed: {p.stderr.strip()[-300:]}")
                continue
        versions[name] = _version([str(BIN / name)])
    for pack in SEMGREP_PACKS.values():
        dst = SEMGREP_RULES / (pack.replace("/", "-") + ".yml")
        if not dst.exists():
            p = subprocess.run(["curl", "-sfL", "-o", str(dst), f"https://semgrep.dev/c/{pack}"], capture_output=True)
            if p.returncode:
                dst.unlink(missing_ok=True)
                log(f"prefetch semgrep rules {pack} failed")
    for name in INSTALLED:
        if shutil.which(name):
            versions[name] = _version([name])
    return versions


def _version(cmd: list[str]) -> str:
    for flag in ("--version", "-version", "version"):
        try:
            p = subprocess.run([*cmd, flag], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            continue
        out = (p.stdout or p.stderr).strip().splitlines()
        if p.returncode == 0 and out:
            return out[0][:80]
    return "unknown"


DIAG_RE = re.compile(r"^\s*(?:Diff in )?(?P<path>[^\s:()][^:()]*?)"
                     r"(?::(?P<line>\d+)(?::\d+)?|\((?P<line2>\d+),\d+\))\s*(?:[:\-]\s*)?(?P<msg>.*)$")


def diagnostics(spec: dict, stdout: str, stderr: str, wt: str) -> list[dict]:
    """-> [{path (repo-relative), line, msg, rule}] for gate output."""
    root = spec.get("root", "")
    out = []

    def add(path: str, line: int, msg: str, rule: str | None = None):
        path = path.removeprefix(wt.rstrip("/") + "/").removeprefix("./")
        if root and not path.startswith(root + "/"):
            path = f"{root}/{path}"
        out.append({"path": path, "line": line, "msg": msg.strip()[:300], "rule": rule})

    if spec.get("parse") == "eslint":
        try:
            for f in json.loads(stdout or "[]"):
                for m in f.get("messages", []):
                    add(f["filePath"], m.get("line") or 0, m.get("message", ""), m.get("ruleId"))
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        return out
    for text in (stdout, stderr):
        for ln in text.splitlines():
            m = DIAG_RE.match(ln)
            if m and re.search(r"\.\w+$", m["path"]):
                msg = m["msg"]
                code = re.match(r"([A-Z]{1,4}\d{3,4})\b", msg)
                tag = re.search(r"\(([a-z][\w-]+)\)$", msg)
                add(m["path"], int(m["line"] or m["line2"]), msg, code[1] if code else tag[1] if tag else None)
    return out


def analyzer_hits(spec: dict, stdout: str, wt: str) -> list[dict]:
    """-> [{path, line, rule, msg}] from semgrep/bandit/gosec JSON."""
    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return []
    rows = []
    if spec.get("parse") == "semgrep":
        rows = [(r["path"], r["start"]["line"], r.get("check_id"), r.get("extra", {}).get("message", ""))
                for r in data.get("results", [])]
    elif spec.get("parse") == "bandit":
        rows = [(r["filename"], r["line_number"], r.get("test_id"), r.get("issue_text", ""))
                for r in data.get("results", [])]
    elif spec.get("parse") == "gosec":
        rows = [(r["file"], int(str(r["line"]).split("-")[0]), r.get("rule_id"), r.get("details", ""))
                for r in data.get("Issues") or []]
    root = spec.get("root", "")
    out = []
    for path, line, rule, msg in rows:
        path = path.removeprefix(wt.rstrip("/") + "/").removeprefix("./")
        if root and not path.startswith(root + "/"):
            path = f"{root}/{path}"
        out.append({"path": path, "line": int(line), "rule": rule, "msg": str(msg)[:300]})
    return out
