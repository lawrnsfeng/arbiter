# Rust idioms

## 3. Idiom checklist (reviewer-only)

| Area | Flag | Don't flag (exception) | Source |
|---|---|---|---|
| Naming | `get_foo()` plain getter | `get` when single obvious thing (`Cell::get`), `get`/`get_mut`/`get_unchecked` for indexed access | C-GETTER https://rust-lang.github.io/api-guidelines/naming.html |
| Naming | `as_` that allocates/does work; `to_` that's free; `into_` not consuming self | `to_` on `Copy` owned→owned (`f64::to_radians`) | C-CONV (api-guidelines print) |
| Naming | `as_slice_mut` | — use `as_mut_slice` (mut as in type) | C-CONV |
| Naming | iterator methods not `iter`/`iter_mut`/`into_iter`; iterator type names ≠ method (`Iter`, `IntoIter`) | — | C-ITER, C-ITER-TY |
| Naming | `UUID`, `StdIn`, `b_tree_map`, crate named `foo-rs` | `PI_2` (single-letter last word ok) | C-CASE |
| Naming | misspelled keyword (`krate`, `typ`) | `r#crate` or `crate_` | style-guide advice.html |
| Naming | Cargo feature `use-std`, `with-serde` | `std`, `serde` | C-FEATURE |
| Naming | inconsistent word order (`ParseIntError` vs `IntParseError` mix) | — | C-WORD-ORDER |
| Error handling | `Result<T, ()>` or `Result<T, String>` in pub API | private helpers, prototypes | C-GOOD-ERR; Effective Rust Item 4 |
| Error handling | pub error type not `Error + Send + Sync + 'static`, missing `Display`/`source()` | no_std where `Error` unavailable | C-GOOD-ERR |
| Error handling | `anyhow::Error`/`Box<dyn Error>` in **library** public signatures | binaries / app top-level; internal lib code | Effective Rust Item 4 "Libraries Versus Applications"; anyhow docs ("for … applications") |
| Error handling | hand-written enum boilerplate (Display/From/source) | tiny crates avoiding deps | Effective Rust Item 4 (thiserror) |
| Error handling | app errors without context (`?` straight from io in `main`) | — | anyhow `.context()` / `.with_context()` |
| Error handling | `unwrap()`/`expect()`/`[i]`/`/` on input-derived values in libs | in `main`, tests, provably-infallible with `expect("why")`, internal-invariant violation | Effective Rust Item 18 |
| Error handling | `catch_unwind` used as exception handling | at FFI boundary (required) | Effective Rust Item 18 |
| Error handling | pub panicking fn without `# Panics`; fallible without `# Errors` | — | C-FAILURE; std-dev-guide docs |
| Error handling | explicit `match` on `Option`/`Result` doing what `map`/`ok_or`/`and_then`/`?` does | complex multi-arm logic | Effective Rust Item 3 |
| Resource mgmt | manual cleanup calls instead of RAII guard/`Drop` | — | Effective Rust Item 11; patterns "RAII with guards" |
| Resource mgmt | `Drop` that can fail/panic or block | provide `close() -> Result`, Drop ignores/logs | C-DTOR-FAIL, C-DTOR-BLOCK |
| Resource mgmt | code relying on `Drop` running for **safety** | — leaks are safe (`mem::forget`) | std-dev-guide §mem::forget |
| API design | `&String`, `&Vec<T>`, `&Box<T>` params | — (`ptr_arg` catches most) | patterns "Use borrowed types for arguments" |
| API design | borrow-then-clone inside fn (`fn f(b:&Bar){ let b=b.clone(); }`) | — take `Bar` by value | C-CALLER-CONTROL |
| API design | taking ownership only to read | — take `&T` | C-CALLER-CONTROL |
| API design | concrete types where `impl AsRef<Path>`, `impl IntoIterator`, `R: Read` fit | hot non-generic paths (code size) | C-GENERIC, C-RW-VALUE |
| API design | `bool`/`Option` positional args (`new(true,false)`) | — enum/newtype | C-CUSTOM-TYPE |
| API design | out-parameters `fn f(out:&mut T)` | buffer reuse APIs (`read(&mut buf)`) | C-NO-OUT |
| API design | free fn with obvious receiver | — | C-METHOD |
| API design | constructor not `new`/`with_*`/`from_*`; `new()` w/o `Default` | — | C-CTOR; patterns "Constructors", "Default trait" |
| API design | `-> impl Trait`/`async fn` in **public** trait without deciding `Send` | private traits | Rust Blog 2023-12-21 |
| API design | trait that should be dyn-usable isn't object-safe | — | C-OBJECT |
| API design | pub trait not meant for downstream impl isn't sealed | — | C-SEALED |
| Types | primitive obsession (`u64` user id, meters vs feet) | — newtype | C-NEWTYPE; Effective Rust Item 6 |
| Types | enum for combinable flags | — bitflags | C-BITFLAG |
| Types | pub types missing `Debug`, `Clone`, `PartialEq`, `Default`… | when semantically wrong (e.g. `Copy` on large/handle types) | C-COMMON-TRAITS, C-DEBUG |
| Types | `Debug` printing empty | — | C-DEBUG-NONEMPTY |
| Types | `as` numeric casts that can truncate | widening known-safe; use `From`/`TryFrom` | Effective Rust Item 5 |
| Data modeling | invalid states representable (parallel `Option`s, bool+data) | — enum with data | Effective Rust Item 1 |
| Data modeling | pub struct fields on types with invariants | plain-data/POD structs | C-STRUCT-PRIVATE |
| Data modeling | trait bounds on struct def duplicating derive bounds (`struct S<T: Clone>`) | bounds required by fields | C-STRUCT-BOUNDS |
| Data modeling | pub enum/struct likely to grow without `#[non_exhaustive]` | exhaustive by design (e.g. `Ordering`) | std-dev-guide "Are there public enums?"; patterns `#[non_exhaustive]` |
| Data modeling | many-optional-field constructor | — builder | C-BUILDER; Effective Rust Item 7 |
| Concurrency | std `MutexGuard` held across `.await` | — scope it, or tokio Mutex for IO resources | clippy `await_holding_lock`; tokio Mutex docs |
| Concurrency | `tokio::sync::Mutex` for plain data | guard truly needs to span `.await` | tokio Mutex docs ("blocking mutex should be preferred") |
| Concurrency | blocking I/O / heavy CPU in async fn | wrapped in `spawn_blocking` (bounded) / dedicated thread (long-lived) / rayon | tokio spawn_blocking docs |
| Concurrency | non-cancel-safe future in looping `select!` (`read_exact`, `write_all`, `Mutex::lock`, `Semaphore::acquire`, `Notify::notified`) | shutdown branches where loss is fine | tokio select! docs §Cancellation safety |
| Concurrency | `!Send` value (Rc, RefCell guard) held across `.await` in spawned task | `LocalSet`/current-thread | tokio spawn docs |
| Concurrency | `spawn_blocking` task assumed abortable | — it isn't once started | tokio spawn_blocking docs |
| Concurrency | ad-hoc shared state w/o clear lock order | message passing / actor task | Effective Rust Item 17; tokio Mutex docs |
| Concurrency | pub types needlessly `!Send`/`!Sync` | — | C-SEND-SYNC |
| Mutability/ownership | `.clone()` to silence borrowck | `Rc`/`Arc` clones; prototypes | patterns anti-pattern "Clone to satisfy the borrow checker" |
| Mutability/ownership | `Option::take` dance / clone to move out of `&mut` enum | — `mem::take`/`mem::replace` | patterns idiom |
| Mutability/ownership | `let mut` kept mutable after setup | — shadow to immutable | patterns "Temporary mutability" |
| Mutability/ownership | whole-struct borrow conflicts → refactor into sub-structs | — | patterns "Struct decomposition" |
| Mutability/ownership | unconditional allocation where input is often borrowed | — `Cow<'_, str>` | `[from memory]` (std `Cow` docs) |
| Modules/visibility | `pub` where `pub(crate)`/private suffices | — | Effective Rust Item 22 |
| Modules/visibility | glob imports of external crates | preludes, `use super::*` in tests | Effective Rust Item 23 |
| Modules/visibility | dep types in pub API not re-exported | — | Effective Rust Item 24 |
| Modules/visibility | `Deref` to emulate inheritance | true smart pointers | C-DEREF; patterns anti-pattern "Deref polymorphism" |
| Modules/visibility | `#[path]` attributes | generated code | style-guide advice |
| Modules/visibility | feature flags that change pub API non-additively | — | Effective Rust Item 26 |
| Testing | unsafe code without Miri in CI | FFI-only paths Miri can't run (`#[cfg_attr(miri, ignore)]`) | Miri README; Effective Rust Item 16 |
| Testing | doc examples using `unwrap`/`try!` | — use `?` | C-QUESTION-MARK |
| Testing | doc code blocks marked `ignore` | `no_run`, `should_panic`, `compile_fail` | std-dev-guide docs |
| Testing | only unit tests for pub API | — add integration/doc/fuzz/property tests | Effective Rust Item 30 |
| Docs | pub item lacks rustdoc example; crate lacks crate-level docs | — | C-EXAMPLE, C-CRATE-DOC |
| Docs | type names not intra-doc linked | the item being documented | C-LINK; std-dev-guide |
| Docs | `unsafe fn` lacks `# Safety` section | — (clippy `missing_safety_doc` catches pub) | std safety-comments policy |
| Docs | impl details visible (`#[doc(hidden)]` missing on internal pub items) | — | C-HIDDEN |
| Perf | `#[inline]` on generic fns / non-default trait methods; `#[inline(always)]` without benchmark | small pub non-generic fns | std-dev-guide "Is that #[inline] right?" |
| Perf | index loops `for i in 0..v.len()` | needs index arithmetic across slices | Effective Rust Item 9 |
| Perf | `collect()` then iterate again | — | Effective Rust Item 9 (`needless_collect` is nursery) |
| Perf | premature `unsafe`/micro-opt without measurement | — | Effective Rust Item 20; std-dev-guide perf section |
| Perf | `format!` in hot loop for concatenation | readability-first code | patterns "Concatenating strings with format!" |
| Security | `unsafe` without `// SAFETY:` explaining invariants | — | std safety-comments; clippy `undocumented_unsafe_blocks` |
| Security | SAFETY comment in safe fn depending on caller beyond type validity | — | std safety-comments "Inside safe elements" |
| Security | `unsafe fn` body ops not wrapped in `unsafe {}` | — (2024 warns) | edition guide unsafe_op_in_unsafe_fn |
| Security | unsafe code trusting generic safe trait impls (`Ord`, `Hash`, closures) for soundness | `unsafe trait` contract | Nomicon "How Safe and Unsafe Interact" |
| Security | `unsafe impl Send/Sync` without justification | — | Nomicon; clippy `non_send_fields_in_send_ty` (nursery) |
| Security | `env::set_var`/`remove_var` with other threads alive | single-threaded startup | edition guide "Unsafe functions" |
| Security | `static mut` | — use atomics/`OnceLock`/`Mutex` | edition guide `static_mut_refs` |
| Security | panics escaping across FFI | — `catch_unwind` | Effective Rust Item 18, 34 |
| Security | manual `Drop` on generic w/ `MaybeUninit`/raw ptr lacking `PhantomData<T>` | — | std-dev-guide "Is there a manual Drop" |

## Community review practice

### 6.1 Compiler review policy (Forge) — https://forge.rust-lang.org/compiler/reviews.html
- Purpose: reduce bugs/regressions; keep code maintainable (readable, documented, well-tested); check big-picture context.
- Author must supply: what, why, how (if non-trivial), points of contention/alternatives/risks, links to issues/RFCs/MCPs.
- Checklist: regression test? coverage? MCP needed? **perf run**? other teams' sign-off (t-lang)? Reference/Edition Guide updates? Regressions in error messages, maintainability ("complex code, no documentation, unsafe"), targets, tooling, compile time, memory.
- Reviewer self-check: right person? would I spot side effects / fix a bug it introduces? impartial? under pressure to approve?
- Before merge: title/description still accurate; commit history clean ("do not need 16 'fix typo' commits").
- Large PRs: reviewers "not expected to stomach" them; split into self-contained PRs.
- Reverts: revert first on meaningful regression, reland with fix + regression test; prefer revert over follow-up patching.

### 6.2 Std/libs review checklist — https://std-dev-guide.rust-lang.org/print.html §Reviewing PRs
Questions asked on every library PR: RFC needed? **Any `unsafe`?** (comment required, tidy-enforced; "also needs to actually be ok"; ping UCG WG if any doubt). **`#[inline]` right?** **Potential breakage?** (RFC 1105; crater). **Behavior changed?** (behavioral changes to stable fns generally unacceptable). **New impls of stable traits?** (breaks inference / deref coercion). Could it reuse existing functionality? `#[fundamental]` types? Specialization (only `min_specialization`, via private trait)? **Pub enums `#[non_exhaustive]`?** Drop order changed? Manual `Drop` + `#[may_dangle]` + `PhantomData`? `mem::replace/swap/forget` assumptions? **Miri** coverage? Perf impact? Tidy commit log (no merge commits)?

### 6.3 Comment & workflow conventions (rustc-dev-guide PR lifecycle; Forge)
| Convention | Meaning |
|---|---|
| `r? @user` / `r? compiler` | assign / reroll reviewer |
| `@bors r+` | approve → merge queue (never merge by hand) |
| `r=me after fixing …` / `@bors r=reviewer` | conditional approval; author lands after trivial fixes |
| `@bors r+ rollup` / `rollup=always|maybe|iffy|never` | batching risk level; give reason for iffy/never |
| `@rustbot author` / `@rustbot ready` | toggle S-waiting-on-author / S-waiting-on-review |
| FCP / crater / perf (`rust-timer`) | team consensus / ecosystem breakage / perf evidence |
| "nit:" prefix for non-blocking comments | `[from memory]` — common in rust-lang PRs; not codified in docs read |

### 6.4 Linting culture
- Effective Rust Item 29 "Listen to Clippy"; Item 31–32 tooling + CI (fmt, clippy, tests, Miri, deny/audit, semver-checks).
- Clippy docs: suspicious allows must carry a reason; restriction lints cherry-picked.
