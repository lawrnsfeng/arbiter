# Rust command cookbook

`V` = verified in the source column. `†` = from memory. Every command runs in the sandbox from §4.

| Task | Command |
|---|---|
| **Enumerate modules** | `cargo metadata --format-version 1 --no-deps` (`packages`, `targets`, `workspace_members`) V (S34). `cargo modules structure` V (S38) |
| **Dependency graph** | `cargo metadata` `resolve` graph V. `cargo modules dependencies --lib --acyclic` (cycle error) V (S38) |
| **Graph-agnostic** | `codegraph impact <sym> --depth 2 --json`; `codegraph affected <files>`; `codegraph cycles` V (S10) (avoid rust-analyzer per your rules) |
| **Single test** | `cargo test test_name -- --exact` † |
| **Property testing** | `proptest! { ... }` †. quickcheck † |
| **Fuzzing** | `cargo fuzz init` / `add <t>` / `run <t> -- -max_total_time=60` (init/add/run V S42; the time flag †) |
| **Mutation (test strength)** | `cargo mutants --in-diff <(git diff base)` V (S29). Edits to test code alone yield no mutants. |
| **Sanitizer / race** | `cargo +nightly miri test` catches UB, data races and leaks on executed paths. "No UB found" does not mean sound. No networking or most FFI. V (S27). `RUSTFLAGS=-Zsanitizer=thread cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu` V (S28) |
| **Type checker as oracle** | `cargo clippy --all-targets -- -D warnings` † |
| **SAST** | semgrep V. `cargo geiger` † (unsafe census). `cargo audit` † |
| **API break** | `cargo semver-checks --baseline-rev <base>` V (S39) |
| **Benchmark** | `cargo bench -- --save-baseline main`, then `-- --baseline main` (criterion) V (S43) |
| **e2e** | `cargo test --test it` † |
| Lint gate | `cargo clippy --all-targets --locked --message-format=short` |
| Format gate | `cargo fmt --check` |
| Test gate | `cargo test --locked` |
| Analyzers | `cargo deny check` (when `deny.toml` exists); `semgrep --config p/rust` |
