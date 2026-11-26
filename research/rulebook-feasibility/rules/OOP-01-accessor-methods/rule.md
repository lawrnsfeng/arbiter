---
id: OOP-01
title: Java-style accessor methods
tier: semgrep
severity: should-fix
---
Pattern: a method whose only job is to return or assign one instance attribute (`get_x()` / `set_x(v)`).
Use a public attribute, or `@property` when access needs logic.

× `def get_name(self): return self._name`
✓ `name: str` as a public attribute, or `@property def name(self) -> str: return self._name`
