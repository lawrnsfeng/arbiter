"""One LLM call through a headless harness CLI (omp -p or claude -p). The prompt always goes on stdin."""

import json
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
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
HARNESSES = ("omp", "claude", "fake")
# omp model roles tried in order for each arbiter role; a model is then passed explicitly, so the session
# default (often a premium model) is never used. `arbiter-finder` / `arbiter-verify` are optional custom roles.
OMP_ROLES = {"finder": ("arbiter-finder", "smol"), "verify": ("arbiter-verify",)}
# used when no environment variable, flag or omp role picks a model
FALLBACK_MODELS = {
    "omp": ("anthropic/claude-haiku-5-5", "anthropic/claude-sonnet-5-5"),
    "claude": ("haiku", "sonnet"),
    "fake": ("fake", "fake"),
}
DEFAULT_BLOCKED = "opus,fable"  # cost ceiling: Sonnet-class is the most expensive model arbiter calls by default
THINKING_SUFFIXES = frozenset({"off", "minimal", "low", "medium", "high", "xhigh", "max", "auto", "inherit"})
ROLE_DEPTH = 5


class HarnessError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Settings:
    harness: str
    model: str  # finders, A0, SPEC
    verify_model: str  # verifier, proof agent, eval judge
    model_source: str = ""  # where each model came from, for the report's Coverage section
    verify_source: str = ""

    def model_for(self, role: str) -> str:
        return self.verify_model if role in VERIFY_ROLES else self.model


def parse_roles(stdout: str) -> dict[str, str]:
    """`omp config get modelRoles --json` output -> {role: selector}; {} for anything else."""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return {}
    roles = data.get("value", data) if isinstance(data, dict) else {}
    return {k: v for k, v in roles.items() if isinstance(v, str)} if isinstance(roles, dict) else {}


@cache
def omp_roles() -> dict[str, str]:
    """omp's configured model roles, or {} when omp cannot report them."""
    try:
        p = subprocess.run(
            ["omp", "config", "get", "modelRoles", "--json"],
            capture_output=True,
            text=True,
            timeout=120,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    return parse_roles(p.stdout) if p.returncode == 0 else {}


def resolve_selector(selector: str, roles: dict[str, str]) -> str:
    """A role value to one concrete model id: first candidate, `@role` aliases followed, thinking suffix dropped."""
    for _ in range(ROLE_DEPTH):
        first = selector.split(",", maxsplit=1)[0].strip()
        if not first.startswith("@"):
            head, sep, suffix = first.rpartition(":")
            return head if sep and suffix in THINKING_SUFFIXES else first
        selector = roles.get(first[1:], "")
    return ""


def _pick(harness: str, explicit: str, role_key: str, fallback: str) -> tuple[str, str]:
    if explicit.startswith("@") and harness == "omp":  # an omp role named on the command line
        if model := resolve_selector(explicit, omp_roles()):
            return model, f"omp role {explicit[1:]}"
        raise ArbiterExit(2, f"arbiter: omp role {explicit} is not configured (omp config get modelRoles)")
    if explicit:
        return explicit, "flag or environment"
    if harness == "omp":
        roles = omp_roles()
        for role in OMP_ROLES[role_key]:
            if role in roles and (model := resolve_selector(roles[role], roles)):
                return model, f"omp role {role}"
    return fallback, "arbiter default"


@cache
def _resolve(harness: str, model: str, verify_model: str, blocked: str) -> Settings:
    if harness not in HARNESSES:
        raise ArbiterExit(2, f"arbiter: unknown harness {harness}")
    finder_fallback, verify_fallback = FALLBACK_MODELS[harness]
    m, m_src = _pick(harness, model, "finder", finder_fallback)
    v, v_src = _pick(harness, verify_model, "verify", verify_fallback)
    tiers = [t.strip().lower() for t in blocked.split(",") if t.strip()]
    for name, src in ((m, m_src), (v, v_src)):
        if any(t in name.lower() for t in tiers):
            raise ArbiterExit(
                2,
                f"arbiter: model {name} ({src}) is above the cost ceiling ({', '.join(tiers)}); "
                "pick a cheaper model with --model / --verify-model or ARBITER_BLOCKED_MODELS",
            )
    return Settings(harness, m, v, m_src, v_src)


def settings() -> Settings:
    """Models for this run: flag or environment, else an omp role, else Haiku (finders) and Sonnet (verify)."""
    env = os.environ.get
    return _resolve(
        env("ARBITER_HARNESS", "omp"),
        env("ARBITER_MODEL", ""),
        env("ARBITER_VERIFY_MODEL", ""),
        env("ARBITER_BLOCKED_MODELS", DEFAULT_BLOCKED),
    )


PREFLIGHT_TIMEOUT_S = 300


def preflight(s: Settings) -> None:
    """Before any review work: each model must answer through the harness, use the read tool and return JSON.

    An unconfigured model or one without tool use would otherwise fail every agent call. Skipped for the fake
    harness and when ARBITER_PREFLIGHT_OK already names these models (set by a parent eval process).
    """
    key = f"{s.harness}|{s.model}|{s.verify_model}"
    if s.harness == "fake" or os.environ.get("ARBITER_PREFLIGHT_OK") == key:
        return
    from .agents import extract_json  # agents imports harness

    with tempfile.TemporaryDirectory(prefix="arbiter-preflight-") as d:
        token = uuid.uuid4().hex[:12]
        (Path(d) / "token.txt").write_text(token)
        prompt = (
            "Use your read tool to read the file token.txt in the current directory. "
            'Reply with only this JSON, filling in the file content: {"token": "<content>"}'
        )
        for role, model in (("finder", s.model), ("V", s.verify_model)):
            try:
                value = extract_json(call(role, prompt, tools=Tools.FINDER, cwd=Path(d), timeout=PREFLIGHT_TIMEOUT_S))
            except (HarnessError, ValueError) as e:
                raise ArbiterExit(
                    2, f"arbiter: model {model} failed the preflight through {s.harness}: {str(e)[:300]}"
                ) from None
            if not isinstance(value, dict) or value.get("token") != token:
                raise ArbiterExit(
                    2,
                    f"arbiter: model {model} answered the preflight without reading the file "
                    f"(got {str(value)[:120]}); it needs tool use and JSON output",
                )
    os.environ["ARBITER_PREFLIGHT_OK"] = key


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
