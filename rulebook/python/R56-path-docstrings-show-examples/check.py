"""R56: a member of a paths-providing class without a docstring showing a concrete example path."""

import ast
import re

from rulekit import Hit, Module, classes

RULE = "R56"
PATH_TYPES = {"Path", "PurePath", "PosixPath", "WindowsPath"}
RECORD_BASES = {"NamedTuple", "TypedDict", "BaseModel", "Struct"}
EXAMPLE_PATH = re.compile(
    r"""
    (?:^|[\s(`'"])        # starts a word
    (?:~|\$\{?\w+\}?|<[\w-]+>|[A-Za-z]:|\.{1,2})?  # optional home, variable, placeholder, drive or dot root
    /[^\s/`'"]+           # a first segment
    /[^\s`'"]+            # and at least one more
    """,
    re.VERBOSE,
)


def _named_path(node: ast.expr) -> bool:
    return (isinstance(node, ast.Name) and node.id in PATH_TYPES) or (
        isinstance(node, ast.Attribute) and node.attr in PATH_TYPES
    )


def _path_annotation(node: ast.expr | None) -> bool:
    """`Path`, `Path | None`, `Final[Path]`, `ClassVar[Path]`, `Optional[Path]`."""
    match node:
        case None:
            return False
        case ast.BinOp(op=ast.BitOr()):
            return _path_annotation(node.left) or _path_annotation(node.right)
        case ast.Subscript():
            return _path_annotation(node.slice)
        case _:
            return _named_path(node)


def _builds_path(node: ast.expr | None) -> bool:
    """The value calls `Path(...)` or a `Path` classmethod such as `Path.home()`."""
    calls: list[ast.expr] = [n.func for n in ast.walk(node) if isinstance(n, ast.Call)] if node else []
    return any(_named_path(f) or (isinstance(f, ast.Attribute) and _named_path(f.value)) for f in calls)


def _record(cls: ast.ClassDef) -> bool:
    """A data record: its annotated attributes are per-instance fields, not paths the class provides."""
    decorated: bool = any(
        _last_name(d.func if isinstance(d, ast.Call) else d) in {"dataclass", "define", "frozen", "attrs"}
        for d in cls.decorator_list
    )
    return decorated or any(_last_name(b) in RECORD_BASES for b in cls.bases)


def _last_name(node: ast.expr) -> str:
    return node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""


def _class_level(annotation: ast.expr) -> bool:
    """`ClassVar[...]` or `Final[...]`: a value of the class itself, even in a record."""
    head: ast.expr = annotation.value if isinstance(annotation, ast.Subscript) else annotation
    return _last_name(head) in {"ClassVar", "Final"}


def _members(cls: ast.ClassDef) -> list[tuple[str, int, str | None, bool]]:
    """(name, line, docstring, provides a path) of every non-dunder method and class attribute."""
    out: list[tuple[str, int, str | None, bool]] = []
    record: bool = _record(cls)
    class_doc: list[str] = (ast.get_docstring(cls) or "").splitlines()

    def attr_doc(name: str) -> str | None:
        """The class docstring lines naming the attribute: a bare string after an assignment is no docstring."""
        lines: list[str] = [ln for ln in class_doc if re.search(rf"\b{re.escape(name)}\b", ln)]
        return "\n".join(lines) or None

    for node in cls.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.name.startswith("__"):
            out.append((node.name, node.lineno, ast.get_docstring(node), _path_annotation(node.returns)))
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and not node.target.id.startswith("__")
        ):
            provided: bool = node.value is not None and (_path_annotation(node.annotation) or _builds_path(node.value))
            out.append(
                (
                    node.target.id,
                    node.lineno,
                    attr_doc(node.target.id),
                    provided and (not record or _class_level(node.annotation)),
                )
            )
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and not node.targets[0].id.startswith("__")
        ):
            out.append((node.targets[0].id, node.lineno, attr_doc(node.targets[0].id), _builds_path(node.value)))
    return out


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        for cls in classes(m.tree):
            members: list[tuple[str, int, str | None, bool]] = _members(cls)
            if sum(provided for *_, provided in members) < 2:
                continue  # not a paths-providing class
            for name, line, doc, _ in members:
                if doc is None:
                    out.append(Hit(m.path, line, f"R56 member `{cls.name}.{name}` of a paths class has no docstring"))
                elif not EXAMPLE_PATH.search(doc):
                    out.append(Hit(m.path, line, f"R56 docstring of `{cls.name}.{name}` shows no example path"))
    return out
