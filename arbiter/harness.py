"""One LLM call through a headless harness CLI (omp -p or claude -p). The prompt always goes on stdin."""

import os
import subprocess
from pathlib import Path

from . import HOME, ArbiterExit

FINDER_TOOLS = {"omp": "read,grep,glob", "claude": "Read,Grep,Glob"}
PROOF_TOOLS = {"omp": "read,grep,glob,bash,edit,write", "claude": "Read,Grep,Glob,Bash,Edit,Write"}
VERIFY_ROLES = {"V", "P", "judge"}
HIGH_THINKING = {"V", "P"}
# cheap finders, a mid-tier verifier/prover/judge; the harness's own default (often Opus) is never used
DEFAULT_MODELS = {
    "omp": ("anthropic/claude-haiku-5-5", "anthropic/claude-sonnet-5-5"),
    "claude": ("haiku", "sonnet"),
    "fake": ("fake", "fake"),
}
BLOCKED_TIERS = ("opus",)  # cost ceiling: Sonnet is the most expensive model arbiter will call


class HarnessError(Exception):
    pass


def settings() -> dict:
    h = os.environ.get("ARBITER_HARNESS", "omp")
    if h not in DEFAULT_MODELS:
        raise ArbiterExit(2, f"arbiter: unknown harness {h}")
    finder, verify = DEFAULT_MODELS[h]
    model = os.environ.get("ARBITER_MODEL") or finder
    verify_model = os.environ.get("ARBITER_VERIFY_MODEL") or verify
    for m in (model, verify_model):
        if any(t in m.lower() for t in BLOCKED_TIERS):
            raise ArbiterExit(2, f"arbiter: model {m} is above the cost ceiling; use a Haiku, Sonnet or DeepSeek model")
    return {"harness": h, "model": model, "verify_model": verify_model}


def argv(role: str, tools: str) -> list[str]:
    """tools: "" (none), "finder" (read-only search) or "proof" (adds bash and file writes)."""
    s = settings()
    model = s["verify_model"] if role in VERIFY_ROLES else s["model"]
    if s["harness"] == "omp":
        # no skills, rules, context files or extensions: repo instruction files must not steer agents
        cmd = ["omp", "-p", "--no-skills", "--no-session", "--no-rules", "--no-context-files", "--no-extensions",
               "--thinking", "high" if role in HIGH_THINKING else "low"]
        cmd += ["--tools", FINDER_TOOLS["omp"] if tools == "finder" else PROOF_TOOLS["omp"],
                "--approval-mode", "yolo"] if tools else ["--no-tools"]
    elif s["harness"] == "claude":
        cmd = ["claude", "-p", "--output-format", "text", "--tools",
               {"": "", "finder": FINDER_TOOLS["claude"], "proof": PROOF_TOOLS["claude"]}[tools]]
        if tools:
            cmd += ["--permission-mode", "bypassPermissions"]
    else:
        raise HarnessError(f"unknown harness {s['harness']}")
    if model:
        cmd += ["--model", model]
    return cmd


def call(role: str, prompt: str, *, tools: str = "", cwd: Path, timeout: int = 600) -> str:
    if settings()["harness"] == "fake":
        return _fake(role)
    try:
        p = subprocess.run(argv(role, tools), input=prompt, capture_output=True, text=True, errors="replace",
                           cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HarnessError(f"timeout after {timeout}s") from None
    if p.returncode:
        out = " | ".join(x.strip().replace("\n", " ")[-400:] for x in (p.stderr, p.stdout) if x.strip())
        raise HarnessError(f"exit {p.returncode}: {out}")
    return p.stdout


def _fake(role: str) -> str:
    """Test-only harness: canned replies from ARBITER_FAKE_DIR/<role>.json (or a numbered sequence <role>.<n>.json)."""
    d = Path(os.environ.get("ARBITER_FAKE_DIR", HOME / "tests" / "fixtures" / "harness"))
    counter = d / f".{role}.count"
    n = int(counter.read_text()) + 1 if counter.exists() else 1
    seq = d / f"{role}.{n}.json"
    if seq.exists():
        counter.write_text(str(n))
        return seq.read_text()
    f = d / f"{role}.json"
    if f.exists():
        return f.read_text()
    return {"V": '{"verdict": "FALSE_POSITIVE", "severity": "nit", "reason": "fake", "cited": ["x:1"]}',
            "A0": '{"claims": [], "spec_source": "none", "threat_model_path": "none", "unit_notes": {}}',
            "P": '{"rung": "E3", "result": "not_reproduced", "before": {"exec_id": "", "cmd": "", "exit_code": 0, "output_excerpt": ""}, "artifact": ""}',
            "judge": '{"match": false}'}.get(role, '{"findings": []}')
