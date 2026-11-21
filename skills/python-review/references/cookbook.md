# Python command cookbook

`V` = verified in the source column. `†` = from memory. Every command runs in the sandbox from §4.

| Task | Command |
|---|---|
| **Enumerate modules** | `grimp.build_graph('pkg')`, then `.modules` and `.find_children()` V (S35) |
| **Dependency graph** | grimp `find_upstream_modules` / `find_downstream_modules` / `find_matching_direct_imports("a.* -> b.*")` V (S35). `pydeps` †. `import-linter` (`lint-imports`) † |
| **Graph-agnostic** | `codegraph impact <sym> --depth 2 --json`; `codegraph affected <files>`; `codegraph cycles` V (S10) |
| **Single test** | `pytest path/test_x.py::test_name -x` † |
| **Property testing** | Hypothesis `@given(st.integers())` † |
| **Fuzzing** | atheris: `with atheris.instrument_imports(): ...`, `atheris.Setup(sys.argv, f)`, `atheris.Fuzz()` V (S42) |
| **Mutation (test strength)** | `mutmut run "pkg.mod.func*"`, then `mutmut browse` V (S42). cosmic-ray † |
| **Sanitizer / race** | `python -X dev` (faulthandler, ResourceWarning, asyncio debug, malloc debug hooks) plus `-X tracemalloc=5` for allocation sites V (S33) |
| **Type checker as oracle** | `pyright --strict` † / `mypy --strict` † |
| **SAST** | `semgrep scan --config p/python --baseline-commit $BASE --dataflow-traces --json` V (S32). `bandit -r` † |
| **API break** | `griffe check -s src pkg -a <base-ref>` V (S40) |
| **Benchmark** | `pytest --benchmark-autosave`, then `--benchmark-compare --benchmark-compare-fail=mean:5%` V (S43) |
| **e2e** | pytest + containers † |
| Lint gate | `uv run ruff check --output-format=concise <files>` (when ruff is a project dependency); otherwise `ruff check --output-format=concise <files>` via the cached tool, only when `[tool.ruff]` exists |
| Type gate | `uv run mypy` (when `[tool.mypy]` exists) / `uv run pyright` (when `[tool.pyright]` exists) |
| Test gate | `uv run pytest -q -x <selected>` |
| Analyzers | `bandit -f json -r <files>`; `semgrep scan --config p/python --baseline-commit <base> --json --dataflow-traces --metrics=off` |
