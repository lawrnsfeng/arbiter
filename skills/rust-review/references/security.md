# Rust security checklist

### 3d. Rust

| Vuln class | Flag | Don't flag | Verify | CWE |
|---|---|---|---|---|
| Unsoundness at the safe/unsafe boundary | Safe `fn` whose `unsafe` block relies on caller-supplied invariants; `transmute`/cast `&`→`&mut`; `assume_init` before full init; `static mut`; `repr(packed)` field refs; `mem::zeroed`/`uninitialized` (S24) | `unsafe` with a `// SAFETY:` comment whose invariant is local and type-enforced | **P:** Miri test `cargo +nightly miri test` `[from memory]`; ToB `rust-review` skill (S24) | 119, 416, 787, 908 |
| Panic as DoS | `unwrap`/`expect`, indexing, `&str` slicing, `RefCell::borrow_mut`, `HeaderMap` over 32,768 entries, `Duration::from_secs_f64(neg)` on attacker data in a long-running server (S24) | CLIs, tests, or invariant-proven indices; also S35 excludes DoS by default, so gate on the threat model | **T:** clippy `unwrap_used`, `indexing_slicing` `[from memory]`, `string_slice` (S24); **P:** proptest or fuzz input that panics | 248 `[from memory]`, 129 |
| Integer overflow in release | Arithmetic on lengths, offsets or money from input. Release builds may silently wrap (S23) | `checked_*`/`saturating_*`/`wrapping_*`, `Wrapping<T>`, or `overflow-checks = true` | **T:** clippy `arithmetic_side_effects` (S24); **P:** a test that runs under `--release` and shows the wrap | 190 |
| Validation in `debug_assert!` | `debug_assert!` used as the only guard (removed in release, S24) | `assert!` or explicit `if … return Err` | **P:** release-mode test | 20, 617 |
| Allocation / recursion DoS | `Vec::with_capacity(user_len)`, including via serde `size_hint`; deeply nested structs whose drop overflows the stack (S24) | Capped capacity | **P:** a 10⁹-length header or a 100k-depth JSON fixture | 770, 674 |
| Path traversal | `base.join(user)` where `user` may be absolute, which replaces `base` (S24) | A component check before the join | **P:** `join("/etc/passwd")` unit test | 22 |
| Partial-match comparisons | `starts_with`/`contains`/case-insensitive comparison in authz, host or path checks (S24) | Exact equality on a normalized form | **P:** bypass test such as `admin.evil.com` | 697 |
| FFI | Lifetime of `CString::as_ptr`; ownership/free across the boundary; panics crossing `extern "C"` `[from memory]` | `bindgen` wrappers with a documented contract | **P:** ASan or Miri test `[from memory]` | 762, 416 |
| Test features in prod | Mock or test features in `[dependencies]` or `default` (S24) | `dev-dependencies` | **T:** `cargo tree -e features` | 489 |
| Secret zeroization | Secret built in a growing `Vec`, then wrapped in `Zeroizing` (reallocation copies survive, S24) | Pre-sized buffer zeroized from creation | ToB `zeroize-audit` skill (S39 repo) | 226 |
| Known-vulnerable deps | RUSTSEC advisory in `Cargo.lock` | Advisory scoped to a feature or target that is unused (state why) | **T:** `cargo audit`, `cargo deny check advisories` (S24, S26) | 1395 |

## Supply chain

| Ecosystem | Review on every lockfile/manifest diff | Policy to check exists | Tool or evidence |
|---|---|---|---|
| **Cargo** | New crates; new or changed `build.rs` and proc-macros, which run on the build host (S25); duplicate versions; git or alternate-registry sources | `cargo deny` advisories, bans, sources, licenses (S26); `cargo vet` with imported audits (Google, Bytecode Alliance) (S24); crates.io trusted publishing since July 2025 (S28) | `cargo audit`; `cackle` for unexpected FS/network API use; `cargo-supply-chain` for publisher sprawl (S24) |
| **GitHub Actions / CI** | `pull_request_target` or `workflow_run` plus checkout of PR code (critical, S33); `${{ github.event.* }}` interpolated into `run:`; actions not pinned by SHA; broad `GITHUB_TOKEN` permissions `[from memory: Scorecard Pinned-Dependencies / Token-Permissions]` | Branch protection: 1–2 reviewers, code owners, status checks (S33); SLSA Build L2+ signed provenance (S34); a published artifact matches its source (S29) | Scorecard `Dangerous-Workflow`, `Branch-Protection`, `Binary-Artifacts` (S33); ToB `agentic-actions-auditor`, `supply-chain-risk-auditor` skills (S39 repo) |

**Supply-chain "don't flag" defaults:** outdated-but-not-vulnerable dependencies. S35 exclusion 9 routes known-CVE dependency findings to a separate SCA gate instead of the code reviewer.
