"""Shared vocabulary and record shapes.

Enums are `StrEnum`, so their members compare equal to, and serialize as, the plain strings that agents emit and
stage files store. Records that round-trip through `RUN/*.json` are `TypedDict`s: the JSON stays the
machine contract, and the type checker sees the field names.
"""

from enum import StrEnum
from typing import NotRequired, TypedDict


class Effort(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class Lang(StrEnum):
    PYTHON = "python"
    GO = "go"
    RUST = "rust"
    TYPESCRIPT = "typescript"
    OTHER = "other"


class Group(StrEnum):
    FUNCTIONAL = "functional"
    EVOLVABILITY = "evolvability"


class Axis(StrEnum):
    LOGIC = "logic"
    EDGE = "edge"
    TESTS = "tests"
    ERRORS = "errors"
    RESOURCES = "resources"
    OBSERVABILITY = "observability"
    SECURITY = "security"
    PRIVACY = "privacy"
    CONCURRENCY = "concurrency"
    API = "api"
    DATA = "data"
    PORTABILITY = "portability"
    DEPS = "deps"
    PERFORMANCE = "performance"
    OPS = "ops"
    A11Y = "a11y"
    SPEC = "spec"
    MAINTAINABILITY = "maintainability"
    IDIOM = "idiom"
    DESIGN = "design"
    DOCS = "docs"

    @property
    def group(self) -> Group:
        return Group.EVOLVABILITY if self in EVOLVABILITY else Group.FUNCTIONAL


EVOLVABILITY = frozenset({Axis.MAINTAINABILITY, Axis.IDIOM, Axis.DESIGN, Axis.DOCS})
# representative axis when several agents flag one location (most consequential first)
AXIS_PRIORITY = (
    Axis.SECURITY,
    Axis.PRIVACY,
    Axis.DATA,
    Axis.CONCURRENCY,
    Axis.LOGIC,
    Axis.EDGE,
    Axis.ERRORS,
    Axis.RESOURCES,
    Axis.API,
    Axis.SPEC,
    Axis.DEPS,
    Axis.PORTABILITY,
    Axis.PERFORMANCE,
    Axis.OBSERVABILITY,
    Axis.OPS,
    Axis.A11Y,
    Axis.TESTS,
    Axis.DESIGN,
    Axis.MAINTAINABILITY,
    Axis.IDIOM,
    Axis.DOCS,
)


class Severity(StrEnum):
    """Declared most severe first; `rank` orders them."""

    BLOCK = "block"
    SHOULD_FIX = "should-fix"
    NIT = "nit"

    @property
    def rank(self) -> int:
        return list(Severity).index(self)


def least_severe(*sevs: str) -> Severity:
    return max(map(Severity, sevs), key=lambda s: s.rank)


class Verdict(StrEnum):
    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    PREDATES_CHANGE = "PREDATES_CHANGE"


class Rung(StrEnum):
    E0 = "E0"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"
    E7 = "E7"
    E8 = "E8"
    E9 = "E9"


class ProofResult(StrEnum):
    CONFIRMED = "confirmed"
    NOT_REPRODUCED = "not_reproduced"
    ERROR = "error"


class Status(StrEnum):
    """Outcome of the verifier tally."""

    VERIFIED = "verified"
    PRE_EXISTING = "pre-existing"
    SUSPECTED = "suspected"
    DROPPED = "dropped"


class Placement(StrEnum):
    """Report section after the evidence gate."""

    MAIN = "main"
    SUSPECTED = "suspected"
    PRE_EXISTING = "pre-existing"
    DROPPED = "dropped"
    NIT_OVERFLOW = "nit-overflow"


class Decompose(StrEnum):
    """How the diff is split into review units (research-decompose-hierarchical.md §4, §5)."""

    OCR = "ocr"  # hunk chunking (default)
    HIER = "hier"  # syntax-aware split + shared context + widened merge + contract pass
    HIER_SPLIT = "hier-split"  # the syntax-aware split alone (the §5 ablation arm)


class SymbolChange(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    SIGNATURE = "signature-changed"
    RENAMED = "renamed"


class ToolKind(StrEnum):
    BUILD = "build"
    TYPE = "type"
    LINT = "lint"
    TEST = "test"
    ANALYZER = "analyzer"


# ---------------------------------------------------------------- records stored in RUN/*.json

type Range = tuple[int, int]
type Ranges = dict[str, list[Range]]  # path -> new-side line ranges


class Hunk(TypedDict):
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added: list[tuple[int, str]]  # (new line number, text); JSON turns tuples into lists
    removed: list[str]
    churn: NotRequired[int]


class DiffFile(TypedDict):
    path: str
    old_path: str | None
    lang: Lang
    added: int
    deleted: int
    churn: int
    binary: bool
    hunks: list[Hunk]
    excluded: str | None


class Piece(TypedDict):
    """One file's share of a unit: the whole file, a chunk of its hunks, or (hier) line sub-ranges of them."""

    path: str
    lang: Lang
    hunks: list[int]
    churn: int
    file_churn: int
    lines: NotRequired[list[Range]]  # new-side sub-ranges of `hunks`; absent means the whole hunks


class Unit(TypedDict):
    id: str
    lang: Lang
    langs: list[Lang]
    files: list[Piece]
    churn: int
    plan_required: bool
    triggers: NotRequired[list[str]]
    ranges: NotRequired[Ranges]
    context: NotRequired[str]  # hier: the unit context map (signatures, never bodies)


class Symbol(TypedDict):
    """One changed top-level symbol or method in the PR change manifest (base vs head `ast`)."""

    path: str
    qualname: str
    kind: str  # function | method | class
    change: SymbolChange
    old_sig: str
    new_sig: str
    unit: str
    lines: NotRequired[Range]  # head-side span (decorators to end)
    old_path: NotRequired[str]
    old_qualname: NotRequired[str]
    callers: NotRequired[list[str]]  # path:line, depth 1, capped
    callers_more: NotRequired[int]  # callers left out by the cap


class ToolSpec(TypedDict):
    name: str
    kind: ToolKind
    cmd: list[str]
    lang: NotRequired[Lang]
    root: NotRequired[str]
    source: NotRequired[str]  # project | installed | ephemeral
    needs: NotRequired[str]  # ephemeral binary name under the tool cache
    parse: NotRequired[str]  # semgrep | bandit | gosec | eslint | raw
    net: NotRequired[bool]  # needs network, so runs outside the sandbox (never executes repo code)
    pm: NotRequired[str]
    available: NotRequired[bool]


class ExecRecord(TypedDict):
    exec_id: str
    cmd: str
    argv: list[str]
    cwd: str
    base: bool
    exit_code: int
    stdout_tail: str
    stderr_tail: str
    duration_s: float
    timed_out: bool


class ProofRun(TypedDict):
    exec_id: str
    cmd: NotRequired[str]
    exit_code: NotRequired[int]
    output_excerpt: NotRequired[str]


class Proof(TypedDict):
    rung: Rung
    result: ProofResult
    before: NotRequired[ProofRun]
    after: NotRequired[ProofRun]
    oracle_source: NotRequired[str]
    artifact: NotRequired[str]
    check: NotRequired[str]


class ProofPlan(TypedDict):
    rung: Rung
    idea: str


class VoteRecord(TypedDict):
    verdict: Verdict
    severity: Severity
    reason: str
    cited: list[str]
    lens: NotRequired[str]
    finding_id: NotRequired[str]


# functional syntax because one stored key, "pass", is a Python keyword
Finding = TypedDict(
    "Finding",
    {
        # emitted by agents (validated in findings.validate_candidate)
        "axis": Axis,
        "severity": Severity,
        "type": str,
        "file": str,
        "line": int,
        "end_line": int,
        "claim": str,
        "trigger": str,
        "evidence_lines": list[str],
        "cwe": int,
        "rule": str,
        "precedent": str,
        "code_judo": bool,
        "fix": str,
        "proof_plan": ProofPlan,
        # filled by arbiter: provenance, merge, tally, proof and gate
        "id": str,
        "agent": str,
        "pass": int,
        "unit": str,
        "group": Group,
        "source": str,
        "axes": list[Axis],
        "agents": list[str],
        "passes": dict[str, list[int]],
        "status": Status,
        "status_reason": str,
        "proof": Proof,
        "proof_attempts": list[dict[str, object]],
        "proof_note": str,
        "placement": Placement,
        "placement_reason": str,
        "support": list[dict[str, object]],
        "locations": list[str],  # hier root-cause clustering: other path:line sites of the same changed symbol
    },
    total=False,
)
