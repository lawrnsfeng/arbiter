"""R75: definite comment shapes (TODO, apology, banner, narration, prose beside a directive) and :param restatements."""

import ast
import io
import re
import tokenize

from rulekit import Hit, Module

RULE = "R75"
SEGMENT = re.compile(r"\s+#\s*")
REPLAY_MARKER = re.compile(r"^expect(-llm)?:\s*[\w-]+$")
PERMITTED = re.compile(r"^(review|rv|\?|shortcut):")
DIRECTIVE = re.compile(
    r"^(type:\s*ignore(\[[^\]]*\])?"
    r"|noqa(:\s*[A-Z]+\d+([,\s]+[A-Z]+\d+)*)?"
    r"|fmt:\s*(off|on|skip)"
    r"|pragma:\s*no\s*(cover|branch)"
    r"|pyright:\s*\w+(\[[^\]]*\])?"
    r"|ruff:\s*noqa(:\s*[A-Z]+\d+([,\s]+[A-Z]+\d+)*)?"
    r"|isort:\s*[\w-]+"
    r"|pylint:\s*[\w-]+=[\w,-]+"
    r"|mypy:\s*[\w-]+(=\S+)?)"
)
SHAPES = (
    (re.compile(r"^(?i:todo|fixme|hack)\b|^XXX\b"), "defers a case: pin it with code, a named error or a test"),
    (re.compile(r"(?i)\b(workaround|work around|kludge|hack|temporary|for now)\b"), "apologizes for the shape"),
    (re.compile(r"^[-=*#~_]{3,}|^[-=*#~_]{2,}.*[-=*#~_]{2,}$"), "sections the code"),
    (re.compile(r"(?i)^(now|then|next|first|finally)\b|^(?i:step)\s*\d+"), "narrates a step"),
)
CODING = re.compile(r"coding[:=]")


def comment_problem(text: str) -> str | None:
    segments = [s.strip() for s in SEGMENT.split(" " + text.lstrip("#")) if s.strip()]
    segments = [s for s in segments if not REPLAY_MARKER.match(s) and not PERMITTED.match(s)]
    directives = [s for s in segments if DIRECTIVE.match(s)]
    if directives:
        prose = [s for s in segments if not DIRECTIVE.match(s)]
        if prose or any(DIRECTIVE.sub("", s).strip() for s in directives):
            return "puts prose beside a directive"
        return None
    for segment in segments:
        for shape, problem in SHAPES:
            if shape.search(segment):
                return problem
    return None


def comment_hits(m: Module) -> list[Hit]:
    hits = []
    for tok in tokenize.generate_tokens(io.StringIO(m.source).readline):
        if tok.type != tokenize.COMMENT:
            continue
        row = tok.start[0]
        if (row == 1 and tok.string.startswith("#!")) or (row <= 2 and CODING.search(tok.string)):
            continue
        if problem := comment_problem(tok.string):
            hits.append(Hit(m.path, row, f"{RULE} comment {problem}"))
    return hits


def restates(line: str) -> bool:
    found = re.match(r"^\s*:param\s+(\w+):\s*(.*?)\s*(#\s*expect.*)?$", line)
    if not found:
        return False
    words = re.sub(r"^(the|a|an)\s+", "", found[2].lower()).rstrip(".").split()
    return words == found[1].lower().strip("_").split("_")


def docstring_hits(m: Module) -> list[Hit]:
    hits = []
    for node in ast.walk(m.tree):
        body = getattr(node, "body", None)
        if not (body and isinstance(body, list) and isinstance(body[0], ast.Expr)):
            continue
        doc = body[0].value
        if isinstance(doc, ast.Constant) and isinstance(doc.value, str):
            hits.extend(
                Hit(m.path, doc.lineno + offset, f"{RULE} docstring `:param` only restates the name")
                for offset, line in enumerate(doc.value.split("\n"))
                if restates(line)
            )
    return hits


def check(modules: list[Module]) -> list[Hit]:
    return [hit for m in modules for hit in comment_hits(m) + docstring_hits(m)]
