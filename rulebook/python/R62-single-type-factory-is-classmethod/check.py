"""R62: an undecorated module-level function whose return annotation is one project-owned class."""

import ast
from pathlib import PurePath

from rulekit import Hit, Module

RULE = "R62"


def is_protocol(cls: ast.ClassDef) -> bool:
    return any((b.id if isinstance(b, ast.Name) else getattr(b, "attr", "")) == "Protocol" for b in cls.bases)


def top_classes(m: Module) -> set[str]:
    return {n.name for n in m.tree.body if isinstance(n, ast.ClassDef) and not is_protocol(n)}


def module_stem(path: str) -> str:
    p = PurePath(path).with_suffix("")
    return "/" + "/".join(p.parent.parts if p.name == "__init__" else p.parts)


class Owners:
    """Project-owned top-level classes by name, with the module paths defining them."""

    def __init__(self, modules: list[Module]) -> None:
        self.stems: dict[str, set[str]] = {}
        for m in modules:
            for name in top_classes(m):
                self.stems.setdefault(name, set()).add(module_stem(m.path))

    def defines(self, dotted: str, name: str) -> bool:
        tail = "/" + dotted.replace(".", "/")
        return any(stem.endswith(tail) for stem in self.stems.get(name, ()))


class Scope:
    """What a module's names refer to: its own classes, `from` imports, and imported module aliases."""

    def __init__(self, m: Module, owners: Owners) -> None:
        self.owners = owners
        self.local = top_classes(m)
        self.names: dict[str, tuple[int, str, str]] = {}
        self.modules: dict[str, str] = {}
        for node in ast.walk(m.tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    self.names[alias.asname or alias.name] = (node.level, node.module or "", alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.modules[alias.asname or alias.name.partition(".")[0]] = alias.name if alias.asname else ""

    def owned(self, spelling: str) -> str | None:
        head, _, name = spelling.rpartition(".")
        if not head:
            if name in self.local:
                return name
            if name not in self.names:
                return None
            level, module, original = self.names[name]
            if level and original in self.owners.stems:
                return original
            return original if self.owners.defines(module, original) else None
        root = head.partition(".")[0]
        rest = head[len(root) :]
        if root in self.modules:
            dotted = (self.modules[root] + rest) if self.modules[root] else head
        elif root in self.names:
            _, module, original = self.names[root]
            dotted = ".".join(filter(None, (module, original))) + rest
        else:
            return None
        return name if self.owners.defines(dotted, name) else None


def spelling(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    ann = fn.returns
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        return ann.value.strip()
    if isinstance(ann, ast.Name | ast.Attribute):
        return ast.unparse(ann)
    return None


def check(modules: list[Module]) -> list[Hit]:
    owners = Owners(modules)
    hits = []
    for m in modules:
        scope = Scope(m, owners)
        for fn in m.tree.body:
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) or fn.decorator_list:
                continue
            if (text := spelling(fn)) and (name := scope.owned(text)):
                hits.append(Hit(m.path, fn.lineno, f"{RULE} `{fn.name}` returns `{name}`: make it a classmethod of it"))
    return hits
