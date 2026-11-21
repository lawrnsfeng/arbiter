# Rust severity guidance

## 7. Severity guidance

| Block (must fix) | Rationale/source |
|---|---|
| Unsound safe API; UB; Miri failure | Nomicon soundness property; Miri README |
| `unsafe` without true `SAFETY:` justification; unsafe trusting generic safe impls | std safety policy; Nomicon |
| `unsafe impl Send/Sync` unjustified; `static mut` refs | Nomicon; edition 2024 deny |
| Edition-2024 auto-migration `unsafe { env::set_var(..) }` without thread-safety argument | edition guide (`deprecated_safe_2024` inserts block automatically) |
| Panic reachable from untrusted/external input in library or server | Effective Rust Item 18 |
| std Mutex/RefCell guard across `.await`; blocking I/O in async runtime threads | clippy suspicious; tokio docs |
| Non-cancel-safe op in looping `select!` where data loss matters | tokio select! |
| Semver break in published lib without major bump (incl. new impl of stable trait breaking inference, removing `non_exhaustive` reliance) | cargo-semver-checks; std-dev-guide |
| Pub error type `()`/`String`, or `anyhow` in lib pub API | C-GOOD-ERR; Effective Rust Item 4 |
| Destructor that can panic/fail | C-DTOR-FAIL |
| Pub API that permits invalid states where a type could forbid them, on 1.0+ crate (hard to fix later) | C-VALIDATE, C-STRUCT-PRIVATE |
| `#[allow]` on `clippy::correctness` | clippy docs |
| New RustSec advisory / disallowed license via cargo-deny | cargo-deny/audit |
| Behavior change to stable fn without discussion | std-dev-guide |
| Pub `async fn`/RPIT in pub trait with no Send decision (locked in post-release) | Rust Blog 2023-12-21 |

| `Nit:` (non-blocking) | Source |
|---|---|
| `get_` prefix, `as_/to_/into_` naming in private code | C-GETTER, C-CONV |
| index loop where iterator reads cleaner | Effective Rust Item 9 |
| explicit `match` vs combinator | Effective Rust Item 3 |
| `format!` vs `push_str` | patterns idiom |
| missing `Default` / common derives on internal types | C-COMMON-TRAITS |
| temporary mutability, shadowing | patterns idiom |
| extra clone in non-hot, non-API path | patterns (inefficiency acceptable for readability) |
| missing doc example on internal item | C-EXAMPLE |
| `pub` that could be `pub(crate)` in a bin crate | Effective Rust Item 22 |
| glob imports | Effective Rust Item 23 |
| `#[inline]` placement | std-dev-guide ("can always be introduced later") |
| comment prose style (sentence case, period, `//` over `/* */`) | style guide (not rustfmt-enforced) |
| `#[allow]` → `#[expect(.., reason)]` | clippy restriction |
| Cargo.toml metadata (C-METADATA) | — |
| Same items get promoted to **block** in pub API of a published library (naming, missing traits, missing `# Errors/# Panics`) because they're semver-frozen | C-* (future-proofing section) |
| Anything rustfmt/default clippy catches → **say nothing**, point to CI | §2 |
