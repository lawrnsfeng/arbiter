"""File extension -> arbiter language."""

from pathlib import PurePosixPath

EXT = {
    ".py": "python", ".pyi": "python",
    ".go": "go",
    ".rs": "rust",
    **dict.fromkeys((".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"), "typescript"),
}
LANGS = ("python", "go", "rust", "typescript")
# skills/<dir>-review holds each language's references
SKILL_DIR = {"python": "python", "go": "go", "rust": "rust", "typescript": "ts"}


def of(path: str) -> str:
    return EXT.get(PurePosixPath(path).suffix, "other")
