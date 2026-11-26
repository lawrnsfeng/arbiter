"""R0: what this detector reports, in one line."""

from rulekit import Hit, Module

RULE = "R0"


def check(modules: list[Module]) -> list[Hit]:
    return []
