"""R80: a test whose only assertions say that a mock was called."""

import ast

from rulekit import Hit, Module, functions, local_nodes

RULE = "R80"
CALLED_ONLY = {"assert_called", "assert_called_once", "assert_awaited", "assert_awaited_once"}
CALL_FLAGS = {"called", "awaited"}
CALL_COUNTS = {"call_count", "await_count"}
# unittest assertions that, given a call flag or count, only restate "the mock was called"
UNITTEST_CALLED = {"assertTrue", "assertEqual", "assertGreater", "assertGreaterEqual", "assertIs"}


def is_zero(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value == 0  # False == 0 too


MIRROR: dict[type[ast.cmpop], type[ast.cmpop]] = {ast.Lt: ast.Gt, ast.Gt: ast.Lt, ast.LtE: ast.GtE, ast.GtE: ast.LtE}


def asserts_none(op: ast.cmpop, value: object) -> bool:
    """`== 0`, `<= 0`, `< 1`, `is False`, `is not True`: the comparison says the mock was NOT called."""
    if isinstance(op, ast.Eq | ast.Is | ast.LtE):
        return value == 0
    if isinstance(op, ast.NotEq | ast.IsNot):
        return value is True
    return isinstance(op, ast.Lt) and value == 1


def called_only(test: ast.expr) -> bool:
    """`m.called`, `m.called is True`, `m.call_count == 1`, `m.call_count > 0`; a not-called check is a branch."""
    if isinstance(test, ast.Attribute):
        return test.attr in CALL_FLAGS
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    left, op, right = test.left, test.ops[0], test.comparators[0]
    if isinstance(right, ast.Attribute) and not isinstance(left, ast.Attribute):
        left, right = right, left  # `1 > m.call_count` reads as `m.call_count < 1`
        op = MIRROR.get(type(op), type(op))()
    if not (isinstance(left, ast.Attribute) and left.attr in CALL_FLAGS | CALL_COUNTS):
        return False
    if not isinstance(right, ast.Constant):
        return True
    return not asserts_none(op, right.value)


def unittest_called_only(call: ast.Call) -> bool:
    """`self.assertTrue(m.called)`, `self.assertEqual(m.call_count, 1)`."""
    attr = call.func.attr if isinstance(call.func, ast.Attribute) else ""
    if attr not in UNITTEST_CALLED or any(is_zero(a) for a in call.args):
        return False
    return any(isinstance(a, ast.Attribute) and a.attr in CALL_FLAGS | CALL_COUNTS for a in call.args)


def check(modules: list[Module]) -> list[Hit]:
    hits: list[Hit] = []
    for mod in modules:
        for fn in functions(mod.tree):
            if not fn.name.startswith("test"):
                continue
            weak = strong = 0
            for node in local_nodes(fn):
                if isinstance(node, ast.Assert):
                    if called_only(node.test):
                        weak += 1
                    else:
                        strong += 1
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    attr = node.func.attr
                    if attr in CALLED_ONLY or unittest_called_only(node):
                        weak += 1
                    elif attr.startswith(("assert", "raises", "fail")):
                        strong += 1
            if weak and not strong:
                hits.append(Hit(mod.path, fn.lineno, f"R80 `{fn.name}` only asserts that a mock was called"))
    return hits
