---
id: R32
title: A StrEnum member whose value is its lowercased name uses auto()
tier: ast
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/enum.html#enum.StrEnum, https://docs.python.org/3/library/enum.html#enum.auto
---
## Rule

- In a `StrEnum`, a member whose value equals its lowercased name is written `auto()`. (C1)
- An explicit value is written only when it differs from the lowercased name. (C2)

## Incorrect

- `StrEnum` members spelled `CLEAR = "clear"`, `OVERCAST = "overcast"`.
- A multi-word member `WIND_SPEED = "wind_speed"` in an `enum.StrEnum`.
- A lowercase member name repeated as its value.

## Correct

- Members written `auto()`; explicit values only where they differ (`"hPa"`, `"feels-like"`).
- Look-alikes: a `str, Enum` mixin (where `auto()` does not produce the name) and a plain class of string constants.

## Detection

Reports every member of a class with a `StrEnum` base (`StrEnum` or `enum.StrEnum`) assigned a string literal equal
to the member name lowercased (C1, C2).
