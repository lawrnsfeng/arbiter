"""File extension -> arbiter language."""

from pathlib import PurePosixPath

from .model import Lang

EXT: dict[str, Lang] = {
    ".py": Lang.PYTHON,
    ".pyi": Lang.PYTHON,
    ".go": Lang.GO,
    ".rs": Lang.RUST,
    **dict.fromkeys((".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"), Lang.TYPESCRIPT),
}
REVIEWED = (Lang.PYTHON, Lang.GO, Lang.RUST, Lang.TYPESCRIPT)
# skills/<dir>-review holds each language's references
SKILL_DIR = {Lang.PYTHON: "python", Lang.GO: "go", Lang.RUST: "rust", Lang.TYPESCRIPT: "ts"}


def of(path: str) -> Lang:
    return EXT.get(PurePosixPath(path).suffix, Lang.OTHER)
