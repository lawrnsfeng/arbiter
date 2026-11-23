"""bubblewrap sandbox: worktrees at HEAD and base, offline execution, no credentials.

Sandbox rules: research/research-decompose-verify.md §4. Toolchain mounts are skipped when the path does not exist.
"""

import json
import shutil
import subprocess
import time
import uuid
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple, TypedDict

from .model import ExecRecord
from .tools import CACHE

H = Path.home()
TAIL = 200
WORKTREES = ("wt", "wt-base")
TIMED_OUT = frozenset({124, 137})  # timeout(1) exit codes: TERM sent, then KILL after the grace period


class State(StrEnum):
    UNAVAILABLE = "unavailable"
    PREPARED = "prepared"
    READY = "ready"
    SELFTEST_ONLY = "selftest-only"


class Fetch(TypedDict):
    wt: str
    root: str
    cmd: str
    exit_code: int


class SandboxState(TypedDict):
    status: State
    notes: list[str]
    fetch: list[Fetch]


def _state(run: Path) -> SandboxState:
    p = run / "sandbox.json"
    return json.loads(p.read_text()) if p.exists() else SandboxState(status=State.UNAVAILABLE, notes=[], fetch=[])


def _save_state(run: Path, st: SandboxState) -> None:
    (run / "sandbox.json").write_text(json.dumps(st, indent=2))


def _uv_python_dir() -> str | None:
    try:
        return (
            subprocess.run(["uv", "python", "dir"], capture_output=True, text=True, timeout=30).stdout.strip() or None
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_common_dir(wt: Path) -> str | None:
    p = subprocess.run(
        ["git", "-C", str(wt), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
    )
    return p.stdout.strip() if p.returncode == 0 else None


def _env(net: bool) -> dict[str, str]:
    node = shutil.which("node")
    path = [
        CACHE / "bin",
        H / ".cargo/bin",
        H / "go/bin",
        H / ".local/bin",
        *([Path(node).parent] if node else []),
        Path("/usr/local/go/bin"),
        Path("/usr/local/bin"),
        Path("/usr/bin"),
        Path("/bin"),
    ]
    env = {
        "PATH": ":".join(str(p) for p in path if p.exists()),
        "HOME": str(H),
        "LANG": "C.UTF-8",
        "UV_CACHE_DIR": str(CACHE / "uv"),
        "UV_TOOL_DIR": str(CACHE / "uvtools"),
        "GOMODCACHE": str(CACHE / "gomod"),
        "GOCACHE": str(CACHE / "gobuild"),
        "GOTOOLCHAIN": "local",
        "GOFLAGS": "-mod=mod -buildvcs=false",
        "CARGO_HOME": str(CACHE / "cargo"),
        "RUSTUP_HOME": str(H / ".rustup"),
        "npm_config_cache": str(CACHE / "npm"),
        "SEMGREP_ENABLE_VERSION_CHECK": "0",
        "SEMGREP_SEND_METRICS": "off",
    }
    if not net:
        env |= {"UV_OFFLINE": "1", "GOPROXY": "off", "CARGO_NET_OFFLINE": "true", "npm_config_offline": "true"}
    return env


def bwrap_argv(run: Path, cwd: Path, net: bool) -> list[str]:
    run = run.resolve()
    ro = [H / ".cargo/bin", H / ".rustup", H / "go/bin", H / ".local/bin", H / ".nvm"]
    if py := _uv_python_dir():
        ro.append(Path(py))
    argv = [
        "bwrap",
        "--die-with-parent",
        "--unshare-pid",
        "--new-session",
        *([] if net else ["--unshare-net"]),
        "--ro-bind",
        "/",
        "/",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        str(H),
    ]
    for p in ro:
        if p.exists():
            argv += ["--ro-bind", str(p), str(p)]
    CACHE.mkdir(parents=True, exist_ok=True)
    argv += ["--bind", str(CACHE), str(CACHE), "--ro-bind", str(run), str(run)]
    for sub in (*WORKTREES, "proofs"):
        if (run / sub).exists():
            argv += ["--bind", str(run / sub), str(run / sub)]
    # worktrees point at the repo's git dir; expose it read-only so git and tools see the history
    if (gd := _git_common_dir(cwd)) and not Path(gd).is_relative_to(run):
        argv += ["--ro-bind", gd, gd]
    argv.append("--clearenv")
    for k, v in _env(net).items():
        argv += ["--setenv", k, v]
    return [*argv, "--chdir", str(cwd)]


def _tail(text: str) -> str:
    return "\n".join(text.splitlines()[-TAIL:])


def exec_(
    run: Path,
    cmd: list[str],
    *,
    base: bool = False,
    timeout: int = 300,
    net: bool = False,
    cwd: Path | None = None,
    sub: str = "",
) -> ExecRecord:
    """Run cmd in the sandbox. The record goes to RUN/exec/<exec_id>.json, arbiter's own oracle."""
    run = Path(run).resolve()
    wt = run / ("wt-base" if base else "wt")
    cwd = cwd or (wt / sub if wt.exists() else run)
    (run / "exec").mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    p = subprocess.run(
        ["timeout", "--kill-after=10", str(timeout), *bwrap_argv(run, cwd, net), *cmd],
        capture_output=True,
        text=True,
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    rec = ExecRecord(
        exec_id=f"x{uuid.uuid4().hex[:10]}",
        cmd=" ".join(cmd),
        argv=cmd,
        cwd=str(cwd),
        base=base,
        exit_code=p.returncode,
        stdout_tail=_tail(p.stdout),
        stderr_tail=_tail(p.stderr),
        duration_s=round(time.monotonic() - t0, 2),
        timed_out=p.returncode in TIMED_OUT,
    )
    # RUN/exec is outside the writable binds, so sandboxed code cannot forge records
    (run / "exec" / f"{rec['exec_id']}.json").write_text(json.dumps(rec))
    return rec


def exec_record(run: Path, exec_id: str) -> ExecRecord | None:
    if not exec_id or "/" in exec_id:
        return None
    p = Path(run) / "exec" / f"{exec_id}.json"
    return json.loads(p.read_text()) if p.exists() else None


def _worktree(repo: Path, dst: Path, rev: str, notes: list[str]) -> None:
    p = subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "--detach", str(dst), rev], capture_output=True, text=True
    )
    if p.returncode:
        notes.append(f"git worktree add failed ({p.stderr.strip()[:120]}); used git clone --shared")
        subprocess.run(["git", "clone", "-q", "--shared", str(repo), str(dst)], check=True)
        subprocess.run(["git", "-C", str(dst), "checkout", "-q", "--detach", rev], check=True)


NODE_LOCKS = (
    ("pnpm-lock.yaml", ["pnpm", "install", "--frozen-lockfile"]),
    ("yarn.lock", ["yarn", "install", "--frozen-lockfile"]),
    ("bun.lock", ["bun", "install", "--frozen-lockfile"]),
    ("package-lock.json", ["npm", "ci"]),
)


def _fetch_cmds(d: Path) -> list[list[str]]:
    cmds = []
    if (d / "uv.lock").exists():
        cmds.append(["uv", "sync", "--frozen"])
    elif (d / "pyproject.toml").exists():
        cmds.append(["uv", "sync"])
    if (d / "go.mod").exists():
        cmds.append(["go", "mod", "download"])
    if (d / "Cargo.toml").exists():
        cmds.append(["cargo", "fetch", *(["--locked"] if (d / "Cargo.lock").exists() else [])])
    if (d / "package.json").exists():
        node = next(
            ([*cmd, "--ignore-scripts"] for lock, cmd in NODE_LOCKS if (d / lock).exists()),
            ["npm", "install", "--ignore-scripts", "--no-package-lock"],
        )
        cmds.append(node)
    return cmds


def prepare(
    run: Path, repo: Path, *, base: str, head: str, roots: list[str], log: Callable[[str], None]
) -> SandboxState:
    """Create worktrees and fetch dependencies with the network on (inside bwrap) for each project root."""
    run = Path(run).resolve()
    (run / "proofs").mkdir(parents=True, exist_ok=True)
    st = SandboxState(status=State.UNAVAILABLE, notes=[], fetch=[])
    if not shutil.which("bwrap"):
        st["notes"].append("bwrap not found")
        _save_state(run, st)
        return st
    for name, rev in zip(WORKTREES, (head, base), strict=True):
        _worktree(repo, run / name, rev, st["notes"])
    st["status"] = State.PREPARED
    _save_state(run, st)
    for wtname in WORKTREES:
        for root in roots:
            d = run / wtname / root
            for cmd in _fetch_cmds(d):
                r = exec_(run, cmd, net=True, timeout=900, cwd=d)
                if r["exit_code"] and not r["timed_out"]:  # registry and shared-cache hiccups are transient
                    r = exec_(run, cmd, net=True, timeout=900, cwd=d)
                st["fetch"].append(Fetch(wt=wtname, root=root, cmd=r["cmd"], exit_code=r["exit_code"]))
                if r["exit_code"]:
                    log(
                        f"dependency fetch failed in {wtname}/{root}: {r['cmd']} -> {r['exit_code']}: "
                        f"{r['stderr_tail'][-300:]}"
                    )
    _save_state(run, st)
    return st


class Check(NamedTuple):
    name: str
    cmd: list[str]
    needs: str | None  # skip when this binary is not installed


CHECKS = (
    Check("network blocked", ["sh", "-c", "! curl -sm2 https://example.com >/dev/null 2>&1"], None),
    Check("~/.ssh hidden", ["sh", "-c", 'test ! -e "$HOME/.ssh"'], None),
    Check("GH_TOKEN empty", ["sh", "-c", 'test -z "$(printenv GH_TOKEN)"'], None),
    Check("python3 runs", ["python3", "-c", "1"], "python3"),
    Check("go runs", ["go", "version"], "go"),
    Check("cargo runs", ["cargo", "--version"], "cargo"),
    Check("node runs", ["node", "-e", "0"], "node"),
)


def selftest(run: Path) -> tuple[bool, list[tuple[str, str]]]:
    run = Path(run).resolve()
    run.mkdir(parents=True, exist_ok=True)
    if not shutil.which("bwrap"):
        return False, [("bwrap installed", "FAIL")]
    rows: list[tuple[str, str]] = []
    ok = True
    for c in CHECKS:
        if c.needs and not shutil.which(c.needs):
            rows.append((c.name, "skip (not installed)"))
            continue
        r = exec_(run, c.cmd, timeout=60)
        good = r["exit_code"] == 0
        ok &= good
        rows.append((c.name, "pass" if good else f"FAIL (exit {r['exit_code']}: {r['stderr_tail'][-120:]})"))
    st = _state(run)
    if not ok:
        st["status"] = State.UNAVAILABLE
        st["notes"].append("selftest failed: " + "; ".join(f"{n}: {s}" for n, s in rows if s.startswith("FAIL")))
    elif (run / "wt").exists():
        st["status"] = State.READY
    else:
        st["status"] = State.SELFTEST_ONLY
    _save_state(run, st)
    return ok, rows


def available(run: Path) -> bool:
    return _state(Path(run))["status"] == State.READY


def clean(run: Path, repo: Path) -> None:
    run = Path(run).resolve()
    for wt in WORKTREES:
        if (run / wt).exists():
            p = subprocess.run(
                ["git", "-C", str(repo), "worktree", "remove", "--force", str(run / wt)], capture_output=True, text=True
            )
            if p.returncode and (run / wt).exists():
                shutil.rmtree(run / wt, ignore_errors=True)
    subprocess.run(["git", "-C", str(repo), "worktree", "prune"], capture_output=True)
