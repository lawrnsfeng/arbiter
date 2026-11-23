"""Detect gates (build, lint, type, test) and analyzers per language; parse their diagnostics."""

import json
import os
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, TypedDict

from .model import Lang, ToolKind, ToolSpec
from .units import project_root

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
SEMGREP_PACKS = {Lang.PYTHON: "p/python", Lang.RUST: "p/rust", Lang.TYPESCRIPT: "p/typescript"}
MARKER = {Lang.PYTHON: "pyproject.toml", Lang.GO: "go.mod", Lang.RUST: "Cargo.toml", Lang.TYPESCRIPT: "package.json"}
PY_TEST_FILE = re.compile(r"(^|/)(test_[^/]*|[^/]*_test)\.py$")
GOLANGCI_CONFIG = re.compile(r"\.golangci\.(ya?ml|toml|json)")
ESLINT_CONFIG = re.compile(r"(eslint\.config\.[cm]?[jt]s|\.eslintrc(\.\w+)?)")

type Reader = Callable[[str], str | None]


class Diagnostic(TypedDict):
    path: str
    line: int
    msg: str
    rule: str | None


@dataclass(frozen=True, slots=True)
class Project:
    """One project root of one language, as the detectors see it at HEAD."""

    tree: set[str]
    read: Reader
    root: str
    changed: list[str]  # changed files, relative to root
    affected: list[str]  # affected test files, relative to root

    def path(self, p: str) -> str:
        return f"{self.root}/{p}" if self.root else p

    def has(self, p: str) -> bool:
        return self.path(p) in self.tree

    def any_name(self, rx: re.Pattern[str]) -> bool:
        return any(rx.fullmatch(PurePosixPath(p).name) for p in self.tree)


def _rel(files: list[str], root: str) -> list[str]:
    return [f.removeprefix(f"{root}/") if root else f for f in files]


def _spec(name: str, kind: ToolKind, cmd: list[str], **extra: Any) -> ToolSpec:
    return ToolSpec(name=name, kind=kind, cmd=cmd, **extra)  # type: ignore[typeddict-item]


def _semgrep(lang: Lang, files: list[str]) -> ToolSpec:
    pack = SEMGREP_PACKS[lang]
    rules = SEMGREP_RULES / f"{pack.replace('/', '-')}.yml"
    return _spec(
        f"semgrep {pack}",
        ToolKind.ANALYZER,
        [
            "semgrep",
            "scan",
            "--config",
            str(rules),
            "--json",
            "--dataflow-traces",
            "--metrics=off",
            "--disable-version-check",
            *files,
        ],
        parse="semgrep",
        needs="semgrep",
    )


def _toml(text: str | None) -> dict[str, Any]:
    try:
        return tomllib.loads(text or "")
    except tomllib.TOMLDecodeError:
        return {}


def _declares(pyproject: dict[str, Any], package: str) -> bool:
    """Whether `package` is a dependency anywhere in pyproject (project, optional or dependency groups)."""
    proj = pyproject.get("project", {})
    specs = [
        *proj.get("dependencies", []),
        *(d for ds in proj.get("optional-dependencies", {}).values() for d in ds),
        *(d for ds in pyproject.get("dependency-groups", {}).values() for d in ds if isinstance(d, str)),
    ]
    return any(re.match(rf"{re.escape(package)}\b", s.strip(), re.IGNORECASE) for s in specs)


def _python(p: Project) -> list[ToolSpec]:
    pyproject = _toml(p.read(p.path("pyproject.toml")))
    tool = pyproject.get("tool", {})
    out: list[ToolSpec] = []
    if _declares(pyproject, "ruff"):
        out.append(_spec("ruff", ToolKind.LINT, ["uv", "run", "ruff", "check", "--output-format=concise", *p.changed]))
    elif "ruff" in tool or p.has("ruff.toml") or p.has(".ruff.toml"):
        out.append(_spec("ruff", ToolKind.LINT, ["ruff", "check", "--output-format=concise", *p.changed], needs="ruff"))
    if "mypy" in tool or p.has("mypy.ini"):
        out.append(_spec("mypy", ToolKind.TYPE, ["uv", "run", "mypy", *p.changed]))
    if "pyright" in tool or p.has("pyrightconfig.json"):
        out.append(_spec("pyright", ToolKind.TYPE, ["uv", "run", "pyright", *p.changed]))
    if any(PY_TEST_FILE.search(f) for f in p.tree):
        out.append(_spec("pytest", ToolKind.TEST, ["uv", "run", "pytest", "-q", "-x", *p.affected]))
    out.append(
        _spec("bandit", ToolKind.ANALYZER, ["bandit", "-f", "json", "-q", *p.changed], parse="bandit", needs="bandit")
    )
    out.append(_semgrep(Lang.PYTHON, p.changed))
    return out


def _go(p: Project) -> list[ToolSpec]:
    pkgs = sorted({f"./{PurePosixPath(a).parent}" for a in p.affected}) or ["./..."]
    out = [
        _spec("go build", ToolKind.BUILD, ["go", "build", "./..."]),
        _spec("go vet", ToolKind.TYPE, ["go", "vet", "./..."]),
    ]
    if p.any_name(GOLANGCI_CONFIG):
        out.append(_spec("golangci-lint", ToolKind.LINT, ["golangci-lint", "run"], source="installed"))
    else:
        out.append(_spec("staticcheck", ToolKind.LINT, ["staticcheck", "./..."], needs="staticcheck"))
    if any(f.endswith("_test.go") for f in p.tree):
        out.append(_spec("go test", ToolKind.TEST, ["go", "test", "-count=1", *pkgs]))
    out.append(
        _spec("gosec", ToolKind.ANALYZER, ["gosec", "-fmt=json", "-quiet", "./..."], parse="gosec", needs="gosec")
    )
    out.append(
        _spec(
            "govulncheck",
            ToolKind.ANALYZER,
            ["govulncheck", "-json", "./..."],
            parse="raw",
            net=True,
            source="installed",
        )
    )
    return out


def _rust(p: Project) -> list[ToolSpec]:
    out = [
        _spec("clippy", ToolKind.TYPE, ["cargo", "clippy", "--all-targets", "--locked", "--message-format=short"]),
        _spec("rustfmt", ToolKind.LINT, ["cargo", "fmt", "--check"]),
        _spec("cargo test", ToolKind.TEST, ["cargo", "test", "--locked"]),
    ]
    if p.has("deny.toml"):
        out.append(
            _spec(
                "cargo-deny", ToolKind.ANALYZER, ["cargo", "deny", "check"], parse="raw", net=True, source="installed"
            )
        )
    out.append(_semgrep(Lang.RUST, p.changed))
    return out


LOCK_TO_PM = (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lock", "bun"), ("bun.lockb", "bun"))


def _package_manager(p: Project) -> str:
    return next((pm for lock, pm in LOCK_TO_PM if p.has(lock)), "npm")


def _typescript(p: Project) -> list[ToolSpec]:
    pm = _package_manager(p)
    out: list[ToolSpec] = []
    if p.has("tsconfig.json"):
        out.append(_spec("tsc", ToolKind.TYPE, ["npx", "--no-install", "tsc", "--noEmit", "-p", "."]))
    if p.any_name(ESLINT_CONFIG):
        out.append(
            _spec("eslint", ToolKind.LINT, ["npx", "--no-install", "eslint", "-f", "json", *p.changed], parse="eslint")
        )
    try:
        test = json.loads(p.read(p.path("package.json")) or "{}").get("scripts", {}).get("test")
    except json.JSONDecodeError:
        test = None
    if test:
        match test:
            case str() if "vitest" in test and p.affected:
                cmd = ["npx", "--no-install", "vitest", "run", *p.affected]
            case str() if "jest" in test and p.affected:
                cmd = ["npx", "--no-install", "jest", *p.affected]
            case _:
                cmd = [pm, "test"]
        out.append(_spec(f"{pm} test", ToolKind.TEST, cmd))
    out.append(_semgrep(Lang.TYPESCRIPT, p.changed))
    for s in out:
        s.setdefault("pm", pm)
    return out


DETECTORS: dict[Lang, Callable[[Project], list[ToolSpec]]] = {
    Lang.PYTHON: _python,
    Lang.GO: _go,
    Lang.RUST: _rust,
    Lang.TYPESCRIPT: _typescript,
}


def detect(tree: set[str], read: Reader, changed: dict[str, list[str]], affected: list[str]) -> list[ToolSpec]:
    """tree: HEAD paths; read(path): file text at HEAD or None; changed: lang -> changed file paths;
    affected: test files from codegraph (may be empty). Returns tool specs whose cmd runs from `root`."""
    out: list[ToolSpec] = []
    for lang_name, files in changed.items():
        if lang_name not in DETECTORS:
            continue
        lang = Lang(lang_name)
        roots: dict[str, list[str]] = {}
        for f in files:
            roots.setdefault(project_root(f, tree, (MARKER[lang],)), []).append(f)
        for root, fs in sorted(roots.items()):
            aff = [a for a in _rel([a for a in affected if a.startswith(root)], root) if a]
            for s in DETECTORS[lang](Project(tree, read, root, _rel(fs, root), aff)):
                s["lang"], s["root"] = lang, root
                s.setdefault("source", "ephemeral" if s.get("needs") else "project")
                out.append(s)
    return out


def resolve(spec: ToolSpec) -> ToolSpec:
    """Mark a spec available or not, now that ephemeral tools may be installed."""
    if needs := spec.get("needs"):
        spec["available"] = (BIN / needs).exists()
        if spec["available"]:
            spec["cmd"] = [str(BIN / spec["cmd"][0]), *spec["cmd"][1:]]
    else:
        spec["available"] = shutil.which(spec["cmd"][0], path=os.environ.get("PATH")) is not None
    return spec


def prefetch(log: Callable[[str], None]) -> dict[str, str]:
    """Install ephemeral analyzers into CACHE (network on, outside the reviewed repo). Returns name -> version."""
    BIN.mkdir(parents=True, exist_ok=True)
    SEMGREP_RULES.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "UV_TOOL_DIR": str(CACHE / "uvtools"), "UV_TOOL_BIN_DIR": str(BIN), "GOBIN": str(BIN)}
    versions = {}
    for name, (installer, pkg) in EPHEMERAL.items():
        if not (BIN / name).exists():
            cmd = ["uv", "tool", "install", "--quiet", pkg] if installer == "uv" else ["go", "install", pkg]
            p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
            if p.returncode:
                log(f"prefetch {name} failed: {p.stderr.strip()[-300:]}")
                continue
        versions[name] = _version([str(BIN / name)])
    for pack in SEMGREP_PACKS.values():
        dst = SEMGREP_RULES / f"{pack.replace('/', '-')}.yml"
        if dst.exists():
            continue
        if subprocess.run(
            ["curl", "-sfL", "-o", str(dst), f"https://semgrep.dev/c/{pack}"], capture_output=True
        ).returncode:
            dst.unlink(missing_ok=True)
            log(f"prefetch semgrep rules {pack} failed")
    versions |= {name: _version([name]) for name in INSTALLED if shutil.which(name)}
    return versions


def _version(cmd: list[str]) -> str:
    for flag in ("--version", "-version", "version"):
        try:
            p = subprocess.run([*cmd, flag], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if p.returncode == 0 and (lines := (p.stdout or p.stderr).strip().splitlines()):
            return lines[0][:80]
    return "unknown"


DIAG_RE = re.compile(
    r"^\s*(?:Diff in )?(?P<path>[^\s:()][^:()]*?)"
    r"(?::(?P<line>\d+)(?::\d+)?|\((?P<line2>\d+),\d+\))\s*(?:[:\-]\s*)?(?P<msg>.*)$"
)
HAS_EXT = re.compile(r"\.\w+$")
LINT_CODE = re.compile(r"([A-Z]{1,4}\d{3,4})\b")
LINT_TAG = re.compile(r"\(([a-z][\w-]+)\)$")


def _repo_path(path: str, wt: str, root: str) -> str:
    """A tool-reported path made repo-relative (tools run from the project root inside the worktree)."""
    path = path.removeprefix(wt.rstrip("/") + "/").removeprefix("./")
    return f"{root}/{path}" if root and not path.startswith(f"{root}/") else path


def diagnostics(spec: ToolSpec, stdout: str, stderr: str, wt: str) -> list[Diagnostic]:
    """Gate output as repo-relative diagnostics."""
    root = spec.get("root", "")

    def diag(path: str, line: int, msg: str, rule: str | None) -> Diagnostic:
        return Diagnostic(path=_repo_path(path, wt, root), line=line, msg=msg.strip()[:300], rule=rule)

    if spec.get("parse") == "eslint":
        try:
            return [
                diag(f["filePath"], m.get("line") or 0, m.get("message", ""), m.get("ruleId"))
                for f in json.loads(stdout or "[]")
                for m in f.get("messages", [])
            ]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []
    out = []
    for ln in (*stdout.splitlines(), *stderr.splitlines()):
        if (m := DIAG_RE.match(ln)) and HAS_EXT.search(m["path"]):
            msg = m["msg"]
            rule = c[1] if (c := LINT_CODE.match(msg)) else t[1] if (t := LINT_TAG.search(msg)) else None
            out.append(diag(m["path"], int(m["line"] or m["line2"]), msg, rule))
    return out


def analyzer_hits(spec: ToolSpec, stdout: str, wt: str) -> list[Diagnostic]:
    """Findings of semgrep, bandit or gosec JSON output, as repo-relative diagnostics."""
    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return []
    match spec.get("parse"):
        case "semgrep":
            rows = [
                (r["path"], r["start"]["line"], r.get("check_id"), r.get("extra", {}).get("message", ""))
                for r in data.get("results", [])
            ]
        case "bandit":
            rows = [
                (r["filename"], r["line_number"], r.get("test_id"), r.get("issue_text", ""))
                for r in data.get("results", [])
            ]
        case "gosec":
            rows = [
                (r["file"], int(str(r["line"]).split("-")[0]), r.get("rule_id"), r.get("details", ""))
                for r in data.get("Issues") or []
            ]
        case _:
            rows = []
    root = spec.get("root", "")
    return [
        Diagnostic(path=_repo_path(path, wt, root), line=int(line), rule=rule, msg=str(msg)[:300])
        for path, line, rule, msg in rows
    ]
