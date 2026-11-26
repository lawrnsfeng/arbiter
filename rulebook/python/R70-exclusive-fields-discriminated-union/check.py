"""R70: counting validators over optional fields; union variants without forbid/tag; per-variant fallbacks."""

import ast

from rulekit import Hit, Module, classes

RULE = "R70"
VALIDATORS = {"model_validator", "root_validator", "validator", "field_validator"}
CONSTRUCTORS = {"__post_init__", "__init__"}


def name_of(node: ast.expr) -> str:
    node = node.func if isinstance(node, ast.Call) else node
    return node.id if isinstance(node, ast.Name) else getattr(node, "attr", "")


def is_optional(ann: ast.expr | None) -> bool:
    if isinstance(ann, ast.Subscript) and name_of(ann.value) == "Optional":
        return True
    return isinstance(ann, ast.BinOp) and any(isinstance(n, ast.Constant) and n.value is None for n in ast.walk(ann))


def optional_fields(cls: ast.ClassDef) -> int:
    return sum(1 for s in cls.body if isinstance(s, ast.AnnAssign) and is_optional(s.annotation))


def field_list(node: ast.expr) -> list[ast.expr] | None:
    """The elements of a literal tuple/list of fields (`(self.a, self.b)`), else None."""
    if isinstance(node, ast.List | ast.Tuple) and all(isinstance(e, ast.Name | ast.Attribute) for e in node.elts):
        return node.elts
    return None


def none_count(node: ast.AST) -> tuple[int, bool] | None:
    """For a count over a literal list of fields: (number of fields, True when it counts set fields, False for None)."""
    if not isinstance(node, ast.Call):
        return None
    if name_of(node.func) in {"sum", "len"} and len(node.args) == 1:
        arg = node.args[0]
        if not isinstance(arg, ast.GeneratorExp | ast.ListComp) or len(arg.generators) != 1:
            return None
        fields = field_list(arg.generators[0].iter)
        ops = {
            type(op)
            for c in ast.walk(arg)
            if isinstance(c, ast.Compare)
            and any(isinstance(v, ast.Constant) and v.value is None for v in c.comparators)
            for op in c.ops
        }
        if not fields or len(ops & {ast.Is, ast.IsNot}) != 1:
            return None
        return len(fields), ast.IsNot in ops
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "count"
        and (fields := field_list(node.func.value))
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value is None
    ):
        return len(fields), False
    return None


def exactly_one(fn: ast.FunctionDef, count: ast.Call, fields: int, counts_set: bool) -> bool:
    """The count is compared so that exactly one (or at most one) field may be set.

    Counting set fields: `== 1`, `!= 1`, `> 1`, `>= 2`. Counting None: `== n-1`, `!= n-1`, `< n-1`, `<= n-2`.
    Any other bound (`== 0`, `== 2` of set fields, `count(None) == n`) is not exclusivity.
    """
    one = 1 if counts_set else fields - 1
    beyond = (ast.Gt, 1, ast.GtE, 2) if counts_set else (ast.Lt, fields - 1, ast.LtE, fields - 2)
    aliases = {
        t.id
        for n in ast.walk(fn)
        if isinstance(n, ast.Assign) and n.value is count
        for t in n.targets
        if isinstance(t, ast.Name)
    }
    for cmp in (n for n in ast.walk(fn) if isinstance(n, ast.Compare) and len(n.ops) == 1):
        left, right = cmp.left, cmp.comparators[0]
        side = left is count or (isinstance(left, ast.Name) and left.id in aliases)
        if not side or not isinstance(right, ast.Constant) or not isinstance(right.value, int):
            continue
        bound, op = right.value, cmp.ops[0]
        if isinstance(op, ast.Eq | ast.NotEq) and bound == one:
            return True
        if (isinstance(op, beyond[0]) and bound == beyond[1]) or (isinstance(op, beyond[2]) and bound == beyond[3]):
            return True
    return False


def counting_hits(m: Module) -> list[Hit]:
    hits = []
    for cls in classes(m.tree):
        if optional_fields(cls) < 2:
            continue
        for fn in cls.body:
            if not isinstance(fn, ast.FunctionDef):
                continue
            if fn.name in CONSTRUCTORS or {name_of(d) for d in fn.decorator_list} & VALIDATORS:
                hits.extend(
                    Hit(
                        m.path,
                        n.lineno,
                        f"{RULE} `{cls.name}` enforces exactly one field: make it a discriminated union",
                    )
                    for n in ast.walk(fn)
                    if isinstance(n, ast.Call) and (k := none_count(n)) and exactly_one(fn, n, *k)
                )
    return hits


def unions(modules: list[Module]) -> dict[str, str]:
    """Member class name -> discriminator tag, for every `Annotated[A | B, ..., Field(discriminator=...)]`."""
    members: dict[str, str] = {}
    for m in modules:
        for node in ast.walk(m.tree):
            if not (isinstance(node, ast.Subscript) and name_of(node.value) == "Annotated"):
                continue
            if not isinstance(node.slice, ast.Tuple) or not node.slice.elts:
                continue
            union, *extras = node.slice.elts
            for extra in extras:
                if isinstance(extra, ast.Call) and name_of(extra.func) == "Field":
                    for kw in extra.keywords:
                        if kw.arg == "discriminator" and isinstance(kw.value, ast.Constant):
                            for n in ast.walk(union):
                                if isinstance(n, ast.Name) and n.id not in {"Union", "Annotated"}:
                                    members[n.id] = kw.value.value
    return members


def forbids_here(cls: ast.ClassDef) -> bool:
    """`extra="forbid"` as a class keyword, in a decorator's `config=ConfigDict(...)`, or in the class body."""
    if any(
        kw.arg == "extra" and isinstance(kw.value, ast.Constant) and kw.value.value == "forbid" for kw in cls.keywords
    ):
        return True
    if any(
        isinstance(n, ast.keyword) and n.arg == "extra" and getattr(n.value, "value", None) == "forbid"
        for deco in cls.decorator_list
        for n in ast.walk(deco)
    ):
        return True
    for stmt in cls.body:
        nodes = ast.walk(stmt) if isinstance(stmt, ast.Assign | ast.ClassDef) else ()
        for n in nodes:
            if isinstance(n, ast.keyword) and n.arg == "extra" and getattr(n.value, "value", None) == "forbid":
                return True
            if isinstance(n, ast.Dict) and any(
                getattr(k, "value", None) == "extra" and getattr(v, "value", None) == "forbid"
                for k, v in zip(n.keys, n.values, strict=True)
            ):
                return True
            forbid = getattr(n, "value", None)
            if (
                isinstance(n, ast.Assign)
                and any(name_of(t) == "extra" for t in n.targets)
                and "forbid"
                in {
                    getattr(forbid, "value", None),
                    getattr(forbid, "attr", None),
                }
            ):
                return True
    return False


def has_tag_here(cls: ast.ClassDef, tag: str) -> bool:
    return any(
        isinstance(s, ast.AnnAssign)
        and name_of(s.target) == tag
        and isinstance(s.annotation, ast.Subscript)
        and name_of(s.annotation.value) == "Literal"
        for s in cls.body
    )


def inherits(cls: ast.ClassDef, owned: dict[str, ast.ClassDef], test, seen: set[str]) -> bool:
    if test(cls):
        return True
    seen.add(cls.name)
    return any(inherits(owned[b], owned, test, seen) for b in map(name_of, cls.bases) if b in owned and b not in seen)


def variant_hits(modules: list[Module]) -> list[Hit]:
    members = unions(modules)
    owned = {cls.name: (m, cls) for m in modules for cls in classes(m.tree)}
    by_name = {name: cls for name, (_, cls) in owned.items()}
    hits = []
    for name, tag in members.items():
        if name not in owned:
            continue
        m, cls = owned[name]
        missing = []
        if not inherits(cls, by_name, forbids_here, set()):
            missing.append('`extra="forbid"`')
        if not inherits(cls, by_name, lambda c, t=tag: has_tag_here(c, t), set()):
            missing.append(f"a `Literal` `{tag}` tag")
        if missing:
            hits.append(Hit(m.path, cls.lineno, f"{RULE} union variant `{name}` lacks {' and '.join(missing)}"))
        message = f"{RULE} variant `{name}` normalizes payloads itself: use one BeforeValidator on the union"
        hits.extend(
            Hit(m.path, deco.lineno, message)
            for fn in cls.body
            for deco in getattr(fn, "decorator_list", [])
            if isinstance(deco, ast.Call)
            and name_of(deco.func) == "model_validator"
            and any(kw.arg == "mode" and getattr(kw.value, "value", None) == "before" for kw in deco.keywords)
        )
    return hits


def check(modules: list[Module]) -> list[Hit]:
    return [hit for m in modules for hit in counting_hits(m)] + variant_hits(modules)
