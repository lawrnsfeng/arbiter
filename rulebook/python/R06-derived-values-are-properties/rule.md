---
id: R6
title: Derived values are properties; I/O members stay methods
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs property (https://docs.python.org/3/library/functions.html#property), Effective Python 2nd ed. Item 44 "Use Plain Attributes Instead of Setter and Getter Methods", Google Python Style Guide 2.13 "Properties" (https://google.github.io/styleguide/pyguide.html#213-properties)
---
## Rule

- A no-argument member that returns a value derived from `self` is a `@property`, not a method. (C1)
- This includes members that build output lines (for example a view's `lines`). (C2)
- Callers do not recompute a derived value from an object's methods inline (for example
  `sorted(obj.list_items(...).keys())`); that value is a property of the object. (C3)
- A member doing I/O (for example reading a file) is not a property; it stays a method. (C4)
- A member that prints is not a property; it stays a method. (C5)
- A member taking parameters is not a property; it stays a method. (C6)
- Such methods keep a verb name. (C7)
- A member that takes only `self` and whose logic refers to no variable from an outer scope (an enclosing function's
  variable or module-level mutable state) is always a `@property`, including `*_path` members that derive a path from
  `self`. (C8, owner ruling)
- Precedence: when this rule and another rule (such as R29's method-shaped path accessors) disagree on a small point,
  the property wins. (C9, owner ruling)
- Imported names, builtins and module-level UPPER_CASE constants are not outer-scope variables: reading a constant
  (as R1 requires for file names) does not demote a property. (C10, owner ruling as interpreted by the maintainer)

## Incorrect

- A no-argument method returning `self.weight_g / 1000`.
- A no-argument method returning a list of formatted output lines from `self.events`.
- A property that reads the tracking log file.
- A property that prints the parcel's status.
- A caller computing `sorted(depot.parcels_by_code().keys())` inline (model only).
- A method that does I/O named as a noun, `history()` (model only).
- A `label_path()` method deriving a path from `self` through `Path(...)`, `.joinpath()` and a module constant.
- A `tracking_code()` method returning `self.code.strip().upper()`.

## Correct

- `@property` members for derived values, output lines and a `label_path` built from `self` and a module constant;
  I/O and printing as verb-named methods (`load_history()`, `print_status()`); a method taking a parameter.
- Look-alikes: a dunder method, an `@abstractmethod`, a method overriding a same-named method of another class, a
  no-argument method that calls out to a service, a hook method on a subclass of a third-party view class, a
  conversion method `as_label()` (`to_*` / `as_*` conversions such as `as_dict()` stay methods), a method reading
  module-level mutable state (`_seen_codes`), which is an outer-scope variable.

## Detection

`check.py` reports:
- an undecorated method taking only `self`, not a dunder and not a `to_*` / `as_*` conversion, whose body is a single
  `return` of an expression that uses `self`, names nothing but `self`, builtins, imported names, UPPER_CASE
  constants and comprehension variables (so no outer-scope variable), and calls only pure builtins (`len`, `sorted`,
  ...), imported CapWords constructors (`Path(...)`) and value methods (`.strip()`, `.joinpath()`, `.with_suffix()`,
  ...), in a class whose bases are all scanned classes (or `object` / `ABC` / `Generic`), unless another
  scanned class defines a method of the same name; an outside base or a shared name marks a framework or overridden
  contract (C1, C2, C8, C10);
- a `@property` / `@cached_property` whose body calls `open`, `print`, `input`, file read/write methods
  (`read_text`, `write_bytes`, ...), `echo`, `subprocess` / HTTP calls (C4, C5).

## LLM scan

- Report no-argument methods returning a value derived from `self` in shapes the detector skips (several statements,
  helper calls on own attributes, list building loops), including members that build output lines and `*_path`
  accessors (C1, C2, C8). Only a read of an enclosing function's variable or of module-level mutable state keeps such
  a member a method; imported names, builtins and UPPER_CASE constants do not (C10).
- Where another rule's correct example keeps a derived value as a method (for example a path accessor), the property
  wins (C9).
- Report callers that recompute a value from an object's methods inline when it should be a property of that object
  (C3).
- Report properties doing I/O, printing, network or subprocess work the detector misses (C4, C5), and members that
  take parameters but are properties in disguise (setters with arguments emulated by methods are fine) (C6).
- Report methods doing I/O or printing that have noun names instead of verb names (C7).
- Do not flag methods that implement an interface or a framework hook requiring a method, or expensive computations
  deliberately kept as methods to signal cost.
