"""Load and save a plain-text list of notes, one per line."""

from pathlib import Path


def load_notes(path: Path) -> list[str]:
    """Return the non-blank lines of `path`, stripped."""
    text = path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def save_notes(path: Path, notes: list[str]) -> None:
    """Write `notes` to `path`, one per line."""
    path.write_text("".join(f"{note}\n" for note in notes), encoding="utf-8")
