"""arbiter: autonomous, evidence-gated code review."""

from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
SKILLS = HOME / "skills"


class ArbiterExit(Exception):
    """Abort with a machine-contract exit code (2 usage, 3 empty, 4 too large, 5 internal)."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
