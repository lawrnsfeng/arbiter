"""bubblewrap sandbox: worktrees at HEAD and base, offline execution, no credentials.

Sandbox rules: research/research-decompose-verify.md §4. Toolchain mounts are skipped when the path does not exist.
"""

import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from .tools import CACHE

H = Path.home()
TAIL = 200


def _state(run: Path) -> dict:
    p = run / "sandbox.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _save_state(run: Path, st: dict):
    (run / "sandbox.json").write_text(json.dumps(st, indent=2))


def _uv_python_dir() -> str | None:
    try:
        return subprocess.run(["uv", "python", "dir"], capture_output=True, text=True, timeout=30).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_common_dir(wt: Path) -> str | None:
    p = subprocess.run(["git", "-C", str(wt), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def bwrap_argv(run: Path, cwd: Path, net: bool) -> list[str]:
    run = run.resolve()
    ro = [H / ".cargo/bin", H / ".rustup", H / "go/bin", H / ".local/bin", H / ".nvm"]
    if (py := _uv_python_dir()):
        ro.append(Path(py))
    node = shutil.which("node")
    path = [CACHE / "bin", H / ".cargo/bin", H / "go/bin", H / ".local/bin",
            *([Path(node).parent] if node else []), Path("/usr/local/go/bin"), Path("/usr/local/bin"),
            Path("/usr/bin"), Path("/bin")]
    argv = ["bwrap", "--die-with-parent", "--unshare-pid", "--new-session",
            *([] if net else ["--unshare-net"]),
            "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", str(H)]
    for p in ro:
        if p.exists():
            argv += ["--ro-bind", str(p), str(p)]
    CACHE.mkdir(parents=True, exist_ok=True)
    argv += ["--bind", str(CACHE), str(CACHE), "--ro-bind", str(run), str(run)]
    for sub in ("wt", "wt-base", "proofs"):
        if (run / sub).exists():
            argv += ["--bind", str(run / sub), str(run / sub)]
    # worktrees point at the repo's git dir; expose it read-only so git/tools see the history
    if (gd := _git_common_dir(cwd)) and not gd.startswith(str(run)):
        argv += ["--ro-bind", gd, gd]
    env = {
        "PATH": ":".join(str(p) for p in path if p.exists()), "HOME": str(H), "LANG": "C.UTF-8",
        "UV_CACHE_DIR": str(CACHE / "uv"), "UV_TOOL_DIR": str(CACHE / "uvtools"),
        "GOMODCACHE": str(CACHE / "gomod"), "GOCACHE": str(CACHE / "gobuild"), "GOTOOLCHAIN": "local",
        "GOFLAGS": "-mod=mod -buildvcs=false",
        "CARGO_HOME": str(CACHE / "cargo"), "RUSTUP_HOME": str(H / ".rustup"),
        "npm_config_cache": str(CACHE / "npm"), "SEMGREP_ENABLE_VERSION_CHECK": "0", "SEMGREP_SEND_METRICS": "off",
    }
    if not net:
        env.update(UV_OFFLINE="1", GOPROXY="off", CARGO_NET_OFFLINE="true", npm_config_offline="true")
    argv.append("--clearenv")
    for k, v in env.items():
        argv += ["--setenv", k, v]
    argv += ["--chdir", str(cwd)]
    return argv


def exec_(run: Path, cmd: list[str], *, base: bool = False, timeout: int = 300, net: bool = False,
          cwd: Path | None = None, sub: str = "") -> dict:
    """Run cmd in the sandbox; the record is stored under RUN/exec/<exec_id>.json (arbiter's oracle)."""
    run = Path(run).resolve()
    wt = run / ("wt-base" if base else "wt")
    cwd = cwd or (wt / sub if wt.exists() else run)
    (run / "exec").mkdir(parents=True, exist_ok=True)
    argv = ["timeout", "--kill-after=10", str(timeout), *bwrap_argv(run, cwd, net), *cmd]
    t0 = time.monotonic()
    p = subprocess.run(argv, capture_output=True, text=True, errors="replace", stdin=subprocess.DEVNULL)
    rec = {"exec_id": f"x{uuid.uuid4().hex[:10]}", "cmd": " ".join(cmd), "argv": cmd, "cwd": str(cwd),
           "base": base, "exit_code": p.returncode,
           "stdout_tail": "\n".join(p.stdout.splitlines()[-TAIL:]), "stderr_tail": "\n".join(p.stderr.splitlines()[-TAIL:]),
           "duration_s": round(time.monotonic() - t0, 2), "timed_out": p.returncode in (124, 137)}
    # RUN/exec is outside the writable binds, so sandboxed code cannot forge records
    (run / "exec" / f"{rec['exec_id']}.json").write_text(json.dumps(rec))
    return rec


def exec_record(run: Path, exec_id: str) -> dict | None:
    p = Path(run) / "exec" / f"{exec_id}.json"
    if not exec_id or "/" in exec_id or not p.exists():
        return None
    return json.loads(p.read_text())


def _worktree(repo: Path, dst: Path, rev: str, notes: list[str]):
    p = subprocess.run(["git", "-C", str(repo), "worktree", "add", "--detach", str(dst), rev], capture_output=True, text=True)
    if p.returncode:
        notes.append(f"git worktree add failed ({p.stderr.strip()[:120]}); used git clone --shared")
        subprocess.run(["git", "clone", "-q", "--shared", str(repo), str(dst)], check=True)
        subprocess.run(["git", "-C", str(dst), "checkout", "-q", "--detach", rev], check=True)


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
        for lock, cmd in (("pnpm-lock.yaml", ["pnpm", "install", "--frozen-lockfile"]),
                          ("yarn.lock", ["yarn", "install", "--frozen-lockfile"]),
                          ("bun.lock", ["bun", "install", "--frozen-lockfile"]),
                          ("package-lock.json", ["npm", "ci"])):
            if (d / lock).exists():
                cmds.append([*cmd, "--ignore-scripts"])
                break
        else:
            cmds.append(["npm", "install", "--ignore-scripts", "--no-package-lock"])
    return cmds


def prepare(run: Path, repo: Path, base: str, head: str, roots: list[str], log) -> dict:
    """Create worktrees and fetch dependencies with network (inside bwrap) for each project root."""
    run = Path(run).resolve()
    (run / "proofs").mkdir(parents=True, exist_ok=True)
    st = {"status": "unavailable", "notes": [], "fetch": []}
    if not shutil.which("bwrap"):
        st["notes"].append("bwrap not found")
        _save_state(run, st)
        return st
    _worktree(repo, run / "wt", head, st["notes"])
    _worktree(repo, run / "wt-base", base, st["notes"])
    st["status"] = "prepared"
    _save_state(run, st)
    for wtname in ("wt", "wt-base"):
        for root in roots:
            d = run / wtname / root
            for cmd in _fetch_cmds(d):
                r = exec_(run, cmd, net=True, timeout=900, cwd=d)
                if r["exit_code"] and not r["timed_out"]:  # registry and shared-cache hiccups are transient
                    r = exec_(run, cmd, net=True, timeout=900, cwd=d)
                st["fetch"].append({"wt": wtname, "root": root, "cmd": r["cmd"], "exit_code": r["exit_code"]})
                if r["exit_code"]:
                    log(f"dependency fetch failed in {wtname}/{root}: {r['cmd']} -> {r['exit_code']}: "
                        f"{r['stderr_tail'][-300:]}")
    _save_state(run, st)
    return st


CHECKS = [
    ("network blocked", ["sh", "-c", "! curl -sm2 https://example.com >/dev/null 2>&1"], None),
    ("~/.ssh hidden", ["sh", "-c", 'test ! -e "$HOME/.ssh"'], None),
    ("GH_TOKEN empty", ["sh", "-c", 'test -z "$(printenv GH_TOKEN)"'], None),
    ("python3 runs", ["python3", "-c", "1"], "python3"),
    ("go runs", ["go", "version"], "go"),
    ("cargo runs", ["cargo", "--version"], "cargo"),
    ("node runs", ["node", "-e", "0"], "node"),
]


def selftest(run: Path) -> tuple[bool, list[tuple[str, str]]]:
    run = Path(run).resolve()
    run.mkdir(parents=True, exist_ok=True)
    if not shutil.which("bwrap"):
        return False, [("bwrap installed", "FAIL")]
    rows, ok = [], True
    for name, cmd, needs in CHECKS:
        if needs and not shutil.which(needs):
            rows.append((name, "skip (not installed)"))
            continue
        r = exec_(run, cmd, timeout=60)
        good = r["exit_code"] == 0
        ok &= good
        rows.append((name, "pass" if good else f"FAIL (exit {r['exit_code']}: {r['stderr_tail'][-120:]})"))
    st = _state(run)
    if st.get("status") in ("prepared", "ready", "unavailable") or not st:
        st["status"] = "ready" if ok and (run / "wt").exists() else ("unavailable" if not ok else st.get("status", "selftest-only"))
        st.setdefault("notes", [])
        if not ok:
            st["notes"].append("selftest failed: " + "; ".join(f"{n}: {s}" for n, s in rows if s.startswith("FAIL")))
        _save_state(run, st)
    return ok, rows


def available(run: Path) -> bool:
    return _state(Path(run)).get("status") == "ready"


def clean(run: Path, repo: Path):
    run = Path(run).resolve()
    for wt in ("wt", "wt-base"):
        if (run / wt).exists():
            p = subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(run / wt)],
                               capture_output=True, text=True)
            if p.returncode and (run / wt).exists():
                shutil.rmtree(run / wt, ignore_errors=True)
    subprocess.run(["git", "-C", str(repo), "worktree", "prune"], capture_output=True)
