"""R52: a single-arm `match`; an open-set `match` without `case _`; a closed-set `match` with a dead `case _`."""

import ast

from rulekit import Hit, Module, classes, functions, local_nodes, params_of

RULE = "R52"
BUILTIN_TYPES = {"str", "int", "float", "complex", "bytes", "bool", "list", "tuple", "dict", "set", "frozenset"}


def _enum_names(modules: list[Module]) -> set[str]:
    """Names of every Enum/Flag subclass defined in the scanned modules."""
    return {
        cls.name
        for m in modules
        for cls in classes(m.tree)
        if any(
            (b.id if isinstance(b, ast.Name) else getattr(b, "attr", "")).endswith(("Enum", "Flag")) for b in cls.bases
        )
    }


def _alternatives(pattern: ast.pattern) -> list[ast.pattern]:
    return (
        [p for alt in pattern.patterns for p in _alternatives(alt)] if isinstance(pattern, ast.MatchOr) else [pattern]
    )


def _is_wildcard(case: ast.match_case) -> bool:
    return isinstance(case.pattern, ast.MatchAs) and case.pattern.pattern is None and case.guard is None


def _open_set(pattern: ast.pattern) -> bool:
    """A pattern that can only belong to an open subject: literals, builtin-type classes, sequences, mappings."""
    match pattern:
        case ast.MatchValue(value=ast.Constant()) | ast.MatchSequence() | ast.MatchMapping():
            return True
        case ast.MatchClass(cls=ast.Name(id=name)):
            return name in BUILTIN_TYPES
        case _:
            return False


def _enum_member(pattern: ast.pattern, enums: set[str]) -> bool:
    match pattern:
        case ast.MatchValue(value=ast.Attribute(value=ast.Name(id=owner))):
            return owner in enums
        case _:
            return False


def _literal_values(annotation: ast.expr | None, aliases: dict[str, ast.expr]) -> set[object] | None:
    """The values of a `Literal[...]` annotation (directly or through a module-level alias); None otherwise."""
    if isinstance(annotation, ast.Name) and annotation.id in aliases:
        annotation = aliases[annotation.id]
    if not isinstance(annotation, ast.Subscript):
        return None
    head: ast.expr = annotation.value
    if not (
        (isinstance(head, ast.Name) and head.id == "Literal")
        or (isinstance(head, ast.Attribute) and head.attr == "Literal")
    ):
        return None
    items: list[ast.expr] = annotation.slice.elts if isinstance(annotation.slice, ast.Tuple) else [annotation.slice]
    return {i.value for i in items if isinstance(i, ast.Constant)}


def _aliases(tree: ast.Module) -> dict[str, ast.expr]:
    """Module-level `Name = Literal[...]`, `Name: TypeAlias = ...` and `type Name = ...` definitions."""
    out: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            out[node.targets[0].id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            out[node.target.id] = node.value
        elif isinstance(node, ast.TypeAlias):
            out[node.name.id] = node.value
    return out


def _subject_types(tree: ast.Module) -> dict[int, ast.expr]:
    """For every `match` on a plain name inside a function: id(match) -> that name's declared annotation."""
    out: dict[int, ast.expr] = {}
    for fn in functions(tree):
        nodes: list[ast.AST] = local_nodes(fn)
        declared: dict[str, ast.expr] = {a.arg: a.annotation for a in params_of(fn) if a.annotation}
        declared |= {
            n.target.id: n.annotation for n in nodes if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
        }
        for n in nodes:
            if isinstance(n, ast.Match) and isinstance(n.subject, ast.Name) and n.subject.id in declared:
                out[id(n)] = declared[n.subject.id]
    return out


def _annotated_enum(annotation: ast.expr | None, enums: set[str]) -> bool:
    return (isinstance(annotation, ast.Name) and annotation.id in enums) or (
        isinstance(annotation, ast.Attribute) and annotation.attr in enums
    )


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    enums: set[str] = _enum_names(modules)
    for m in modules:
        aliases: dict[str, ast.expr] = _aliases(m.tree)
        subject_types: dict[int, ast.expr] = _subject_types(m.tree)
        for node in ast.walk(m.tree):
            if not isinstance(node, ast.Match):
                continue
            if len(node.cases) < 2:
                out.append(Hit(m.path, node.lineno, "R52 `match` with a single arm: write an `if`"))
                continue
            arms: list[ast.match_case] = [c for c in node.cases if not _is_wildcard(c)]
            patterns: list[ast.pattern] = [p for c in arms for p in _alternatives(c.pattern)]
            fallback: ast.match_case | None = next((c for c in node.cases if _is_wildcard(c)), None)
            declared: ast.expr | None = subject_types.get(id(node))
            literal: set[object] | None = _literal_values(declared, aliases)
            closed: bool = literal is not None or _annotated_enum(declared, enums)
            matched: set[object] = {
                p.value.value for p in patterns if isinstance(p, ast.MatchValue) and isinstance(p.value, ast.Constant)
            }
            if fallback is None and literal is not None and not literal <= matched:
                missing: str = ", ".join(sorted(map(repr, literal - matched)))
                out.append(Hit(m.path, node.lineno, f"R52 `match` over a Literal misses {missing}: it falls through"))
            elif fallback is None and not closed and any(_open_set(p) for p in patterns):
                out.append(Hit(m.path, node.lineno, "R52 `match` over an open set does not end in `case _`"))
            elif fallback is not None and (
                (_annotated_enum(declared, enums) and patterns and all(_enum_member(p, enums) for p in patterns))
                or (literal is not None and literal <= matched)
            ):  # closedness comes from the subject's declared type, never from the patterns
                out.append(
                    Hit(
                        m.path,
                        fallback.pattern.lineno,
                        "R52 dead `case _` in a `match` over a closed set hides a missing case",
                    )
                )
    return out
