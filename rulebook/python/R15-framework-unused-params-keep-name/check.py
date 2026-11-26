"""R15: unused-argument lint silenced inline instead of by a documented per-file ruff ignore."""

import io
import re
import tokenize

from rulekit import Hit, Module

RULE = "R15"
# a line-level or file-level (ruff-prefixed) noqa directive, anywhere in the comment, e.g. after a pragma comment
INLINE = re.compile(r"#\s*(?:ruff\s*:\s*)?noqa\s*:[^#]*\b(?P<code>ARG00[1-5])\b", re.IGNORECASE)


def check(modules: list[Module]) -> list[Hit]:
    out: list[Hit] = []
    for m in modules:
        out += [
            Hit(
                m.path, tok.start[0], f"{RULE} in-source `noqa: {found['code']}`: use a documented per-file ruff ignore"
            )
            for tok in tokenize.generate_tokens(io.StringIO(m.source).readline)
            if tok.type == tokenize.COMMENT and (found := INLINE.search(tok.string))
        ]
    return out
