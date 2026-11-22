# Python design and smells

## 4. Design patterns & architecture

| Pattern | Pythonic verdict | Native replacement | Source |
|---|---|---|---|
| Singleton (GoF `instance()`) | Anti-idiomatic | Module-level global object; `__new__` if forced | BR singleton |
| Abstract Factory | "awkward workaround for lack of first-class functions" | Pass a class or factory callable (`json.loads(parse_float=Decimal)`) | BR abstract-factory |
| Factory Method | "poor fit for Python" | Dependency injection; class-/instance-attribute factory | BR factory-method |
| Builder | Mostly convenience; immutable-pair builder "never necessary" | Keyword args w/ defaults; dataclass + `dataclasses.replace` / `copy.replace` (3.13) `[from memory]` | BR builder |
| Prototype | "isn't necessary" | Pass classes/callables | BR prototype |
| Flyweight | Good fit (interning, caches) | `sys.intern`, `functools.cache` on module functions | BR flyweight |
| Iterator | Built into syntax | Generators, `__iter__`, `itertools` | BR iterator; EP3 Items 24, 43–46 |
| Decorator (GoF) | Useful when wrapping objects you can't subclass; ≠ `@decorator` | Wrapper class / `__getattr__` delegation | BR decorator-pattern |
| Strategy / Command | Classes are ceremony | Pass functions | EP3 Item 48 |
| Visitor / type switch | — | `functools.singledispatch`; `match` with class patterns; polymorphism | EP3 Items 49–50 |
| Sentinel / Null object | Idiomatic | `None`, or unique `object()`; 3.15 `sentinel` builtin | BR sentinel; W315 PEP 661 |
| Template method / deep inheritance | Discouraged | Composition (Adapter/Bridge/Decorator); avoid "subclass explosion" | BR composition-over-inheritance |
| Mixins | Contested: BR "Dodge: Mixins"; EP3 Item 54 "Consider" | Accept small stateless mixins; flag stateful/multi-axis mixins | BR; EP3 |
| Accessors | Anti-idiomatic | Public attributes, then `@property` | EP3 Items 55, 58–59; GSG 3.15 |
| Metaclasses | Power feature | `__init_subclass__`, `__set_name__`, class decorators | EP3 Items 62–66; GSG 2.19 |
| Global mutable state | Avoid | Pass dependencies explicitly | GSG 2.5; BR global-object |

Layering/packaging:
- Package exposes a stable API through `__init__`/`__all__`. Internals take a `_` prefix (EP3 Item 119; P8 Public and Internal Interfaces).
- Give each library one root exception, with subclasses designed for catchers (EP3 Item 121; P8).
- Treat import cycles as an architecture smell. Fix them by moving shared types down a layer, not with local imports (EP3 Item 122; GSG 3.19.14; PYR `reportImportCycles`).
- Keep configuration at the edges: module-scoped deployment config (EP3 Item 120) and `main()` behind a guard (GSG 3.17).
- One class per module is not required. Group related classes and functions (GSG 3.16.2).
- Import style depends on the house: Google prefers absolute module imports (GSG 2.2.4), while Django uses one-dot relative imports for local code (DJS). Follow the project.

## 5. Language-specific smells → refactoring

| Symptom | Refactoring | Source |
|---|---|---|
| `for i in range(len(xs))` | `for x in xs` / `enumerate` / `zip(strict=True)` / `reversed` | RH; EP3 Items 17–18 |
| `if k not in d: d[k] = 0; d[k] += 1` | `d.get(k, 0) + 1`, `defaultdict`, `Counter` | RH; EP3 Items 26–27 |
| `while True: x = f(); if x == s: break` | `iter(partial(f, n), s)` or walrus `while x := f()` | RH; P572 |
| `cmp=` style / custom compare funcs | `key=` | RH; EP3 Item 100 |
| `found` flag loops | `for … else` or `next((…), default)`/`any()` | RH; EP3 Item 23 |
| Indexing tuples `t[0], t[1]` | Unpacking; catch-all `first, *rest` | EP3 Items 5, 16 |
| Return 4+ values as tuple | Dataclass / NamedTuple result object | EP3 Item 31 |
| Nested dict-of-dict-of-list state | Small classes/dataclasses | EP3 Item 29 |
| `isinstance` switch for behavior | Methods / `singledispatch` / `match` | EP3 Items 49–50 |
| Getter/setter methods | Public attribute → `@property` when needed | EP3 Items 58–59 |
| Singleton class / factory classes | Module global / pass callable | BR |
| Metaclass for registration/validation | `__init_subclass__` | EP3 Items 62–63 |
| Repeated try/finally | `@contextlib.contextmanager` | EP3 Item 82 |
| `try` around many lines | Shrink to the raising call + `else:` | P8; EP3 Item 83 |
| `raise NewError(...)` in except (no chain) | `raise NewError(...) from err` | P8; P3134 |
| `return None` on failure | Raise; document in docstring | EP3 Item 32 |
| `def f(a, b, flag=False)` called `f(1, 2, True)` | Keyword-only `*, flag=False` | EP3 Item 37 |
| `x = lambda …` | `def` | P8 |
| Comprehension with multiple `for`/`if` | Helper generator or loop | GSG 2.7.4; EP3 Item 41 |
| Return list from big producer | Generator | EP3 Item 43 |
| Thread per task / unbounded threads | `ThreadPoolExecutor`; asyncio `TaskGroup` | EP3 Item 74; AIO |
| `asyncio.gather` of owned subtasks | `async with asyncio.TaskGroup()` | AIO |
| Function-level imports for startup | `lazy import` (3.15+) | W315 |
| `_MISSING = object()` sentinels | `sentinel` builtin (3.15+) | W315 |
| `MappingProxyType` / defensive dict copies | `frozendict` (3.15+) | W315 |
| `itertools.chain.from_iterable(...)` in comprehensions | `[*xs for xs in seqs]` (3.15+) | W315 PEP 798 |
| `TypeVar` + `Generic[T]`, `TypeAlias` | PEP 695 syntax (3.12+) | P695 |
| Quoted forward refs / `from __future__ import annotations` for forward refs | Unquoted (3.14+ deferred annotations) | W314 PEP 649/749 |
| `TypeGuard` narrowing | `TypeIs` (3.13+) | P742 |

### Version-gated modernization (flag only if `requires-python` ≥ version)

| Min version | Prefer | Over | Source |
|---|---|---|---|
| 3.9 | `list[int]`, `dict[str, X]`; `str.removeprefix` | `typing.List`; slice-prefix | PTY (585); FURB188 |
| 3.10 | `X | Y`, `X | None`; `match`; `zip(strict=True)`; ParamSpec | `Union/Optional`; long if-chains on structure | PTY (604, 612); B905 |
| 3.11 | `Self`; `asyncio.TaskGroup`; TypeVarTuple; `dataclass_transform` | custom self-TypeVar; `gather` | PYI019; AIO; PTY (646, 681) |
| 3.12 | `class C[T]`, `def f[T]`, `type Alias = …`; `@override` | `Generic[T]`, `TypeAlias` | P695; P698 |
| 3.13 | `TypeIs`; `warnings.deprecated`; TypeVar defaults; `ReadOnly` TypedDict items | `TypeGuard`; ad-hoc deprecation | W313 (PEPs 702, 696, 705, 742) |
| 3.14 | Unquoted forward refs; `annotationlib`; t-strings for safe interpolation; `except A, B:` without parens; `concurrent.interpreters`; `compression.zstd` | string annotations; f-strings into SQL/HTML | W314 (PEPs 649/749, 750, 758, 734, 784) |
| 3.15 | `lazy import`; `frozendict`; `sentinel`; `*`/`**` unpacking in comprehensions; TypedDict `extra_items`; `TypeForm`; `profiling.sampling` | local imports; `object()` sentinels; `chain.from_iterable` | W315 (PEPs 810, 814, 661, 798, 728, 747, 799) |

Note: 3.15 makes UTF-8 the default encoding (PEP 686, W315). Code supporting <3.15 still needs `encoding=` (PLW1514).
