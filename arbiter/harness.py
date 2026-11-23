"""One LLM call through a headless harness CLI (omp -p or claude -p). The prompt always goes on stdin."""

import os
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from . import HOME, ArbiterExit


class Tools(StrEnum):
    NONE = ""
    FINDER = "finder"  # read-only search: read, grep, glob
    PROOF = "proof"  # adds bash and file writes, for the proof agent only


TOOL_NAMES = {
    "omp": {Tools.FINDER: "read,grep,glob", Tools.PROOF: "read,grep,glob,bash,edit,write"},
    "claude": {Tools.NONE: "", Tools.FINDER: "Read,Grep,Glob", Tools.PROOF: "Read,Grep,Glob,Bash,Edit,Write"},
}
VERIFY_ROLES = frozenset({"V", "P", "judge"})
HIGH_THINKING = frozenset({"V", "P"})
# cheap finders, a mid-tier verifier/prover/judge; the harness's own default (often Opus) is never used
DEFAULT_MODELS = {
    "omp": ("anthropic/claude-haiku-5-5", "anthropic/claude-sonnet-5-5"),
    "claude": ("haiku", "sonnet"),
    "fake": ("fake", "fake"),
}
BLOCKED_TIERS = ("opus",)  # cost ceiling: Sonnet is the most expensive model arbiter will call


class HarnessError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Settings:
    harness: str
    model: str  # finders, A0, SPEC
    verify_model: str  # verifier, proof agent, eval judge

    def model_for(self, role: str) -> str:
        return self.verify_model if role in VERIFY_ROLES else self.model


def settings() -> Settings:
    h = os.environ.get("ARBITER_HARNESS", "omp")
    if h not in DEFAULT_MODELS:
        raise ArbiterExit(2, f"arbiter: unknown harness {h}")
    finder, verify = DEFAULT_MODELS[h]
    s = Settings(h, os.environ.get("ARBITER_MODEL") or finder, os.environ.get("ARBITER_VERIFY_MODEL") or verify)
    for m in (s.model, s.verify_model):
        if any(t in m.lower() for t in BLOCKED_TIERS):
            raise ArbiterExit(2, f"arbiter: model {m} is above the cost ceiling; use a Haiku, Sonnet or DeepSeek model")
    return s


def argv(role: str, tools: Tools | str) -> list[str]:
    s, tools = settings(), Tools(tools)
    match s.harness:
        case "omp":
            # no skills, rules, context files or extensions: repo instruction files must not steer agents
            cmd = [
                "omp",
                "-p",
                "--no-skills",
                "--no-session",
                "--no-rules",
                "--no-context-files",
                "--no-extensions",
                "--thinking",
                "high" if role in HIGH_THINKING else "low",
            ]
            cmd += ["--tools", TOOL_NAMES["omp"][tools], "--approval-mode", "yolo"] if tools else ["--no-tools"]
        case "claude":
            cmd = ["claude", "-p", "--output-format", "text", "--tools", TOOL_NAMES["claude"][tools]]
            if tools:
                cmd += ["--permission-mode", "bypassPermissions"]
        case other:
            raise HarnessError(f"no command line for harness {other}")
    return [*cmd, "--model", s.model_for(role)]


def call(role: str, prompt: str, *, tools: Tools | str = Tools.NONE, cwd: Path, timeout: int = 600) -> str:
    if settings().harness == "fake":
        return _fake(role)
    try:
        p = subprocess.run(
            argv(role, tools), input=prompt, capture_output=True, text=True, errors="replace", cwd=cwd, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise HarnessError(f"timeout after {timeout}s") from None
    if p.returncode:
        out = " | ".join(x.strip().replace("\n", " ")[-400:] for x in (p.stderr, p.stdout) if x.strip())
        raise HarnessError(f"exit {p.returncode}: {out}")
    return p.stdout


FAKE_DEFAULTS = {
    "V": '{"verdict": "FALSE_POSITIVE", "severity": "nit", "reason": "fake", "cited": ["x:1"]}',
    "A0": '{"claims": [], "spec_source": "none", "threat_model_path": "none", "unit_notes": {}}',
    "P": '{"rung": "E3", "result": "not_reproduced", "before": {"exec_id": "", "cmd": "", "exit_code": 0, '
    '"output_excerpt": ""}, "artifact": ""}',
    "judge": '{"match": false}',
}


def _fake(role: str) -> str:
    """Test-only harness: canned replies from ARBITER_FAKE_DIR/<role>.json, or a numbered sequence <role>.<n>.json."""
    d = Path(os.environ.get("ARBITER_FAKE_DIR", HOME / "tests" / "fixtures" / "harness"))
    counter = d / f".{role}.count"
    n = int(counter.read_text()) + 1 if counter.exists() else 1
    if (seq := d / f"{role}.{n}.json").exists():
        counter.write_text(str(n))
        return seq.read_text()
    if (f := d / f"{role}.json").exists():
        return f.read_text()
    return FAKE_DEFAULTS.get(role, '{"findings": []}')
