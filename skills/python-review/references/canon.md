# Python canon

## 1. Canon

| Key | Source | URL | Authority | Governs | Version/date |
|---|---|---|---|---|---|
| P8 | PEP 8 Style Guide | https://peps.python.org/pep-0008/ | official | layout, naming, programming recs | Active; stdlib 79/72 cols, teams may go to 99 |
| P20 | PEP 20 Zen | https://peps.python.org/pep-0020/ | official | design values ("Errors should never pass silently", "Flat is better than nested", "Namespaces…") | Active |
| P257 | PEP 257 Docstrings | https://peps.python.org/pep-0257/ | official | docstring structure (imperative summary, blank line, args/raises/side effects) | Active |
| P572 | PEP 572 walrus | https://peps.python.org/pep-0572/ | official | `:=`; style recs: prefer statements; restructure if execution order is ambiguous | Final, 3.8 |
| P3134 | PEP 3134 exception chaining | https://peps.python.org/pep-3134/ | official | `__context__` (implicit), `__cause__` via `raise … from` | Final, 3.0 |
| P695 | PEP 695 type params | https://peps.python.org/pep-0695/ | official | `class C[T]`, `def f[T]`, `type X = …` | Final, 3.12 |
| P698 | PEP 698 `@override` | https://peps.python.org/pep-0698/ | official | explicit override marker | Final, 3.12 |
| P742 | PEP 742 `TypeIs` | https://peps.python.org/pep-0742/ | official | narrowing; "most users should use TypeIs, TypeGuard reserved for rare cases" | Final, 3.13 |
| PTY | PEPs 544 Protocol (3.8), 585 builtin generics (3.9), 593 Annotated (3.9), 604 `X|Y` (3.10), 612 ParamSpec (3.10), 646 TypeVarTuple (3.11), 681 dataclass_transform (3.11) | https://peps.python.org/pep-0544/ etc. | official | typing evolution | versions confirmed from PEP headers; 484/526/3107 `[from memory]` |
| P765 | PEP 765 | https://peps.python.org/pep-0765/ | official | `return/break/continue` exiting `finally` → SyntaxWarning in 3.14 | Final |
| P779 | PEP 779 | https://peps.python.org/pep-0779/ | official | free-threaded build "officially supported" (phase II of PEP 703) | 3.14 |
| W313/W314/W315 | What's New 3.13 / 3.14 / 3.15 | https://docs.python.org/3/whatsnew/3.13.html · …/3.14.html · …/3.15.html | official | modern features to prefer | 3.15 released 2026-10-09 |
| DEVV | Status of versions | https://devguide.python.org/versions/ | official | support windows | 3.15/3.14 bugfix; 3.11–3.13 security; 3.10 EOL 2026-10-01 |
| TBP | Typing Best Practices | https://typing.python.org/en/latest/reference/best_practices.html | official (typing council docs) | `object` vs `Any`, abstract params/concrete returns, `X | None`, builtin generics | living doc |
| AIO | asyncio Tasks docs | https://docs.python.org/3/library/asyncio-task.html | official | TaskGroup, strong refs to tasks | 3.15 docs |
| GSG | Google Python Style Guide | https://google.github.io/styleguide/pyguide.html | org | language rules (§2) + style (§3) | current (mentions pyrefly) |
| DJS / DJP | Django coding style; Submitting patches (review checklist) | https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/ · …/submitting-patches/ | org (large project) | project conventions; review checklist | dev docs |
| EP3 | Effective Python 3e (Slatkin), 125 items (TOC) | https://www.pearson.de/media/muster/toc/toc_9780138172244.pdf | community canon (book) | idioms; item headers only | 2024 |
| RH | Hettinger "Transforming Code into Beautiful, Idiomatic Python" (PyCon 2013) notes | https://github.com/JeffPaine/beautiful_idiomatic_python | community (3rd-party transcript, Py2-era) | looping/dict/unpacking idioms | 2013 |
| BR | python-patterns.guide (Brandon Rhodes) | https://python-patterns.guide/ | community | GoF patterns in Python | ©2018–2020 |
| RUFF / RUFFD / R16 | Ruff rules; default rules; v0.16 blog | https://docs.astral.sh/ruff/rules/ · https://docs.astral.sh/ruff/default-rules/ · https://astral.sh/blog/ruff-v0.16.0 | tool | mechanized canon | 0.17.x (Nov 2026); 0.16 default set = 413 rules |
| MYPY | mypy existing-code guide (`--strict` equivalent) + CLI | https://mypy.readthedocs.io/en/stable/existing_code.html · …/command_line.html | tool | strict type checking | strict list "may change over time" |
| PYR | pyright configuration | https://github.com/microsoft/pyright/blob/main/docs/configuration.md | tool | `typeCheckingMode: strict` + opt-in rules | current |
| DEVPR / DEVC | CPython devguide: PR lifecycle; Accepting PRs | https://devguide.python.org/getting-started/pull-request-lifecycle/ · https://devguide.python.org/core-team/committing/ | official | how CPython reviews | current |

## Known gaps

- PEPs 343, 484, 526, 634–636 and 3107 were not opened. Statements about them are `[from memory]`. PEP 703 was checked only through P779 and W313.
- PTY versions come from PEP headers via grep. The text of PEPs 544, 593, 612, 646 and 681 was not read in depth.
- The Hettinger material is a third-party transcript of a 2013 Python 2 talk. It uses `xrange`/`izip`, so its idioms were translated to Python 3 in this doc.
- Effective Python 3e: only item headings were read, not the bodies.
- python-patterns.guide was last updated in 2020. The Composite page verdict was not read.
- The pyright strict-mode rule table was not read (only the config option list). The mypy `--strict` list comes from the "as of mypy 1.0" config. The mypy `explicit-override` code is `[from memory]`.
- No CPython or Django source defines a `Nit:` or severity-prefix convention.
- Not covered: Astral `ty`, Meta `pyrefly` (mentioned in GSG 3.19.7), pylint-only checks, Hypothesis/property-testing norms, packaging (PEP 517/621, `py.typed`), the NumPy/SciPy docstring standard.
- `copy.replace` (3.13) and `itertools.batched` (3.12) are `[from memory]`.
