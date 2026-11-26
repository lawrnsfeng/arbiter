"""R17: comments that suppress a type checker or linter (type: ignore, noqa, pyright, pylint, mypy, nosec)."""

import io
import re
import tokenize

from rulekit import Hit, Module

RULE = "R17"
_SUPPRESS = re.compile(
    r"#\s*(type:\s*ignore|(?:ruff:\s*)?noqa\b|pyright:\s*ignore|pylint:\s*disable|mypy:\s*ignore-errors|nosec\b)",
    re.IGNORECASE,
)


def check(modules: list[Module]) -> list[Hit]:
    hits = []
    for m in modules:
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(m.source).readline))
        except (tokenize.TokenError, SyntaxError):
            continue
        hits += [
            Hit(m.path, tok.start[0], f"{RULE} `{found[1]}` suppression; fix the design or ask first")
            for tok in tokens
            if tok.type == tokenize.COMMENT and (found := _SUPPRESS.search(tok.string))
        ]
    return hits
