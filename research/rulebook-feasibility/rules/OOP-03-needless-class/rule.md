---
id: OOP-03
title: Class that should be a function
tier: ast
severity: should-fix
---
Pattern: a class with no base class, an `__init__` that only stores its arguments, and exactly one other public
method. It is a function wearing a class. Semgrep cannot count methods, so this rule is a stdlib `ast` check.

× `class Greeter: def __init__(self, name): self.name = name; def greet(self): return f"hi {self.name}"`
✓ `def greet(name): return f"hi {name}"`
