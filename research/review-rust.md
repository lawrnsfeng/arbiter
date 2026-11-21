# Rust Code Review Research Base

Scope: Rust-specific canon only (generic review process covered elsewhere). Every row cites a URL opened 2026-11-21 unless tagged `[from memory]`.

---

## 1. Canon

| Source | URL | Authority | Governs | Version/date seen |
|---|---|---|---|---|
| Rust API Guidelines (checklist + chapters) | https://rust-lang.github.io/api-guidelines/checklist.html | Official (libs team; "guidelines, not mandate") | Public API naming, traits, docs, predictability, flexibility, type safety, future-proofing | Undated living doc; C-* codes |
| Rust Style Guide | https://doc.rust-lang.org/style-guide/ | Official (style team; rustfmt reference) | Formatting defaults; comment/doc/attribute style; naming advice (`advice.html`) | Style edition 2024 exists |
| Edition Guide – Rust 2024 | https://doc.rust-lang.org/edition-guide/rust-2024/index.html | Official | Edition 2024 semantic changes + migration lints | 2024 = Rust 1.85.0 (RFC 3501) |
| Clippy book – lint groups | https://doc.rust-lang.org/clippy/lints.html | Official | Meaning + recommended use of each lint group | Current |
| Clippy lint index | https://rust-lang.github.io/rust-clippy/stable/index.html | Official | Per-lint group/default level/config | 832 lints at read time |
| Cargo `[lints]` table | https://doc.rust-lang.org/cargo/reference/manifest.html#the-lints-section | Official | Workspace/package lint config, `priority` | Current |
| Rust Design Patterns (rust-unofficial/patterns) | https://rust-unofficial.github.io/patterns/ | Community (canonical) | Idioms, design patterns, anti-patterns | Last news 2025-12-14 |
| Effective Rust (David Drysdale) | https://effective-rust.com/print.html | Community/O'Reilly book, CC BY-NC-ND | 35 Items: types, traits, errors, panics, unsafe, deps, tooling | © 2024; written for 2018 ed., rustc 1.70; **no async coverage** |
| Rustonomicon | https://doc.rust-lang.org/nomicon/safe-unsafe-meaning.html | Official | Unsafe contracts, soundness, unsafe traits | Current |
| std-dev-guide: Safety comments policy | https://std-dev-guide.rust-lang.org/policy/safety-comments.html | Official (libs team) | `SAFETY:` comment rules; `# Safety` docs | Current |
| std-dev-guide: Reviewing PRs | https://std-dev-guide.rust-lang.org/print.html (§"Reviewing PRs") | Official (libs team) | Std review checklist: unsafe, `#[inline]`, breakage, new impls, `#[non_exhaustive]`, Drop, Miri | Guide self-described "not very complete" |
| Rust Forge – Compiler Review Policy | https://forge.rust-lang.org/compiler/reviews.html | Official (compiler team) | Reviewer/author checklists, reverts, rollups | Current |
| rustc-dev-guide – PR lifecycle | https://rustc-dev-guide.rust-lang.org/pr-lifecycle.html | Official | `r?`, `r+`, `@rustbot ready/author`, no merge commits | Current |
| Tokio docs (Mutex, select!, spawn, spawn_blocking) | https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html, https://docs.rs/tokio/latest/tokio/macro.select.html, https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html | De-facto standard runtime | Async lock choice, cancellation safety, blocking | tokio 1.54.1 |
| Rust Blog: async fn / RPIT in traits | https://blog.rust-lang.org/2023/12/21/async-fn-rpit-in-traits/ | Official (Async WG) | `Send` bounds in public async traits, `trait_variant` | 2023-12-21 (Rust 1.75) |
| anyhow docs | https://docs.rs/anyhow/latest/anyhow/ | De-facto (dtolnay) | App error handling, `context` | 1.0.104 |
| Miri | https://github.com/rust-lang/miri | Official tool | UB detection limits | Current README |
| cargo-deny | https://embarkstudios.github.io/cargo-deny/checks/index.html | Org (Embark) | licenses/bans/advisories/sources | Current |
| cargo-audit | https://github.com/rustsec/rustsec/tree/main/cargo-audit | Org (RustSec WG) | RustSec advisory check | requires Rust 1.74+ |
| cargo-semver-checks | https://github.com/obi1kenobi/cargo-semver-checks | Community (widely adopted) | Semver violation lints vs baseline | Current README |

---

## 2. Tool-enforced layer (reviewer stays silent on these)

### 2.1 Formatter
| Tool | Enforces | Config | Reviewer silent on |
|---|---|---|---|
| `rustfmt` / `cargo fmt` | Style Guide defaults: 4-space indent, 100-col max, block indent, trailing commas, version-sorted imports, single `derive` | `rustfmt.toml`: `style_edition = "2024"` (defaults to crate edition) | All whitespace/layout/import-order. Style guide: "Comments … recommendations only, a mechanical formatter might skip formatting of comments" → comment prose is NOT enforced. (src: style-guide, edition-guide §Rustfmt: Style edition) |

### 2.2 Clippy groups (src: https://doc.rust-lang.org/clippy/lints.html)
| Group | Default | Official guidance | Review stance |
|---|---|---|---|
| `correctness` | **deny** | "outright wrong or useless"; don't `#[allow]` | Any `#[allow(clippy::<correctness>)]` → block |
| `suspicious` | warn | fix; if intentional, local `#[allow]` **with reason** | Flag allow without reason |
| `complexity` | warn | simplify; allow case-by-case | silent |
| `perf` | warn | "usually easy to apply" | silent |
| `style` | warn | most opinionated; crate-wide `#![allow]` acceptable | silent; don't relitigate a crate-level allow |
| `pedantic` | allow | cherry-pick; "expect to use #[allow] generously" (Clippy itself enables whole group) | Respect team's choice |
| `nursery` | allow | "buggy or need more work"; cherry-pick | Not relied upon → reviewer must catch these manually |
| `restriction` | allow | **never enable whole group** (clippy warns if you do); cherry-pick | Team policy |
| `cargo` | allow | Cargo.toml metadata | silent |

Configure in `Cargo.toml` `[lints.clippy]` / `[lints.rust]` with `priority` to let individual lints override groups (src: cargo manifest §lints).

### 2.3 Notable non-default lints teams enable (group + level verified in lint index)
| Lint | Group | Why teams enable | Typical scope |
|---|---|---|---|
| `unwrap_used`, `expect_used` | restriction | ban panicking unwrap in prod code | libs, services; allow in tests |
| `indexing_slicing` | restriction | `v[i]` panics OOB | parsers, untrusted input |
| `panic`, `todo`, `unimplemented`, `unreachable` | restriction | no panics/stubs | libs |
| `unwrap_in_result`, `panic_in_result_fn` | restriction | fn returning `Result` shouldn't panic | libs |
| `get_unwrap` | restriction | `.get(i).unwrap()` hides intent | — |
| `arithmetic_side_effects`, `integer_division`, `as_conversions` | restriction | overflow/trunc safety | crypto, finance, parsers |
| `string_slice` | restriction | `&s[a..b]` panics on non-char boundary | text handling |
| `undocumented_unsafe_blocks` | restriction | requires `// SAFETY:` on line(s) directly preceding `unsafe` block/impl | any crate with unsafe |
| `multiple_unsafe_ops_per_block` | restriction | one op per unsafe block | unsafe-heavy |
| `unnecessary_safety_comment` | restriction | stale SAFETY on safe code | — |
| `mem_forget` | restriction | leaking guards | — |
| `dbg_macro`, `print_stdout`, `print_stderr` | restriction | no debug output in libs | libs |
| `allow_attributes_without_reason`, `allow_attributes` (→`#[expect]`) | restriction | every suppression justified | all |
| `exhaustive_enums`/`exhaustive_structs` | restriction | force `#[non_exhaustive]` on pub types | stable libs |
| `std_instead_of_core`, `alloc_instead_of_core` | restriction | no_std readiness | embedded |
| `clone_on_ref_ptr` | restriction | `Arc::clone(&x)` not `x.clone()` | — |
| `let_underscore_must_use`, `let_underscore_untyped`, `unused_result_ok` | restriction | silent error discard | — |
| `wildcard_enum_match_arm` | restriction | `_` arm hides new variants | — |
| `missing_errors_doc`, `missing_panics_doc` | pedantic | C-FAILURE docs | pub libs |
| `must_use_candidate`, `return_self_not_must_use` | pedantic | builder/pure fn results | libs |
| `needless_pass_by_value`, `trivially_copy_pass_by_ref`, `large_types_passed_by_value` | pedantic | C-CALLER-CONTROL | — |
| `cast_possible_truncation`, `cast_sign_loss` | pedantic | lossy `as` | — |
| `wildcard_imports`, `enum_glob_use` | pedantic | Effective Rust Item 23 | — |
| `large_futures`, `unused_async` | pedantic | async hygiene | async |
| `fn_params_excessive_bools`, `struct_excessive_bools` | pedantic | C-CUSTOM-TYPE | — |
| `redundant_clone` | **nursery** | needless clones | — |
| `future_not_send`, `significant_drop_tightening`, `significant_drop_in_scrutinee` | **nursery** | async Send / guard lifetime | async |
| `missing_const_for_fn`, `use_self`, `option_if_let_else`, `or_fun_call`, `needless_collect` | **nursery** | — | — |
| `uninlined_format_args` | **pedantic** (not style) | `format!("{x}")` | — |

Default-on lints worth knowing (reviewer silent): `ptr_arg` (style: `&Vec<T>`/`&String` params), `missing_safety_doc` (style: pub `unsafe fn` needs `# Safety`), `new_without_default`, `should_implement_trait`, `wrong_self_convention` (C-CONV), `len_without_is_empty` (style); `await_holding_lock`, `await_holding_refcell_ref`, `await_holding_invalid_type`, `let_underscore_future` (suspicious); `large_enum_variant`, `result_large_err`, `box_collection` (perf); `too_many_arguments` (complexity).

### 2.4 rustc lints
| Lint | Status | Note |
|---|---|---|
| `unsafe_op_in_unsafe_fn` | **warn by default in 2024** | unsafe ops inside `unsafe fn` need inner `unsafe {}` (edition guide) |
| `static_mut_refs` | **deny in 2024** | any `&`/`&mut` to `static mut` is instant UB |
| `missing_docs`, `missing_debug_implementations`, `unused_results`, `unreachable_pub`, `unsafe_code` (`forbid`) | allow-by-default | common opt-ins; patterns book recommends naming lints instead of `#![deny(warnings)]` |
| `#![forbid(unsafe_code)]` | — | Nomicon: statically guarantees Safe Rust only |

### 2.5 Supply chain / API / UB tools
| Tool | Catches | Cannot catch |
|---|---|---|
| `cargo deny check` | licenses, bans (specific crates + duplicates), advisories (vulns, unmaintained, yanked), sources | whether a dep is *needed*; feature creep; API exposure of dep types |
| `cargo audit` | RustSec vulns in `Cargo.lock`; `audit bin` on binaries (full accuracy only with `cargo auditable`) | unreported vulns; whether vulnerable path is reachable (README points to experimental `reachsec`). Don't run on untrusted projects without `--file` |
| `cargo semver-checks` | many semver breaks vs baseline (no-false-positive design goal) | README: **not** type changes of fields/params, generics/lifetime changes, breaks under feature subsets |
| Miri (`cargo +nightly miri test`) | OOB, UAF, uninit reads, invalid values, alignment, data races, Stacked/Tree Borrows violations, leaks | Soundness proof ("cannot ensure your code is sound"); only executed paths; most FFI/networking; complete weak-memory (use `loom`) |
| Clippy/rustc | all of 2.3/2.4 | see §3 |

### 2.6 What tools CANNOT catch (→ §3 is the reviewer's job)
API shape (C-* items mostly unlinted: C-CUSTOM-TYPE beyond bool count, C-NEWTYPE, C-SEALED, C-STRUCT-PRIVATE, C-GOOD-ERR); whether a `SAFETY:` comment is *true*; soundness of safe wrappers; panic reachability from untrusted input when restriction lints are off; error-type strategy (lib vs app); clones that are semantically needed vs borrow-checker appeasement (redundant_clone is nursery and misses most); cancellation safety; blocking calls inside async (no default lint); lock ordering/deadlocks; `Deref` misuse; visibility over-exposure; semver break classes listed above; edition-2024 drop-order behavior changes in custom `Drop`; doc prose correctness.

---

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

---

## 4. Design patterns & architecture

### 4.1 Classic patterns in Rust (src: https://rust-unofficial.github.io/patterns/print.html unless noted)
| Pattern | Rust status | Rust-native form |
|---|---|---|
| Builder | **Idiomatic** (no overloading/default args) | `FooBuilder` by-value or `&mut self` chain; `#[must_use]`; C-BUILDER; Effective Rust Item 7 |
| Newtype | **Idiomatic** | tuple struct; zero cost; C-NEWTYPE, C-NEWTYPE-HIDE |
| RAII guards | **Idiomatic** | `Drop` on guard type (`MutexGuard`) |
| Strategy/Policy | Idiomatic via generics/traits/closures | `impl Fn`, trait param |
| Command | Idiomatic via trait objects or closures (`Box<dyn Fn>`) | — |
| Visitor / Fold | Idiomatic for heterogeneous trees (ASTs) | trait w/ `visit_*` default methods |
| Interpreter | Idiomatic w/ enums + macros | — |
| Constructor | `new` assoc fn, not language ctor; add `Default` | patterns "Constructors" |
| Typestate | Idiomatic: encode state in type params so invalid transitions don't compile | `[from memory]` (not a chapter in patterns book) |
| Inheritance via `Deref` | **Anti-pattern** | composition + trait; C-DEREF |
| Singleton/global mutable | Anti-idiomatic (`static mut` deny in 2024) | `OnceLock`/`LazyLock`, pass context explicitly `[from memory for LazyLock]` |
| Observer w/ shared back-pointers | Friction (`Rc<RefCell>` cycles) | channels/message passing (tokio Mutex docs recommend task + message passing for IO resources) |
| Abstract factory/deep hierarchies | Anti-idiomatic | enums (closed set) or traits (open set) — Effective Rust Item 12 generics vs trait objects |
| Reflection/`Any` dispatch | Discouraged | Effective Rust Item 19 |
| Custom trait to bundle bounds | Idiomatic (new 2025-12) | `trait Foo: A + B + C {}` + blanket impl; patterns "Use custom traits to avoid complex type bounds" |
| `#![deny(warnings)]` in source | **Anti-pattern** | `RUSTFLAGS="-D warnings"` in CI or deny named lints; patterns anti-pattern |

### 4.2 Structure / layering
| Convention | Source |
|---|---|
| Contain unsafety in small modules with a safe API wrapper; unsafe is the first suspect | patterns "Contain unsafety in small modules"; Effective Rust Item 16 |
| Prefer small crates | patterns "Prefer small crates" |
| FFI: object-based APIs, consolidate types into wrappers, prefer `bindgen` | patterns FFI; Effective Rust Item 34–35 |
| Minimize visibility; re-export dep types in your API; manage dep graph; avoid feature creep | Effective Rust Items 22, 24, 25, 26 |
| Consider `no_std` for libs | Effective Rust Item 33 |
| Lib = typed errors (enum/thiserror); bin = `anyhow` + context at edges | Effective Rust Item 4 |
| Pub deps of a stable crate are stable (1.0+) | C-STABLE |
| Async: wrap `Arc<Mutex<_>>` in struct with non-async methods locking internally (mini-redis `db.rs`) | tokio Mutex docs |

---

## 5. Language-specific smells → refactoring

| Smell | Refactoring | Source |
|---|---|---|
| `.clone()` scattered after borrowck errors | restructure borrows; `mem::take`; split struct; pass ownership | patterns anti-pattern; struct decomposition |
| `fn f(s: &String)` | `fn f(s: &str)` (`&[T]`, `&T`) | patterns idiom |
| `fn f(x: &Bar) { let x = x.clone() … }` | take `Bar` by value | C-CALLER-CONTROL |
| `new(true, false, None)` | enums / builder | C-CUSTOM-TYPE, C-BUILDER |
| `u64` ids mixed across domains | newtypes | C-NEWTYPE |
| `Result<_, String>` everywhere | error enum (thiserror) for libs; anyhow+context for apps | Effective Rust Item 4 |
| nested `match` on Option/Result | combinators + `?` | Effective Rust Item 3 |
| `for i in 0..v.len() { v[i] … }` | `iter()`/`enumerate()`/`zip()`/`windows()` | Effective Rust Item 9 |
| `if let Some(x) = opt { vec.push(x) }`-style option looping | `extend(opt)` / iterate Option | patterns "Iterating over an Option" |
| `struct Child { parent: Parent }` + `impl Deref for Child` | composition + trait | patterns Deref polymorphism |
| `#![deny(warnings)]` | CI `-D warnings` / named denies | patterns anti-pattern |
| giant `unsafe {}` block, no comment | one op per block + `// SAFETY:` each | clippy `multiple_unsafe_ops_per_block`; std policy |
| `unsafe fn` with bare unsafe ops | inner `unsafe {}` with SAFETY | 2024 `unsafe_op_in_unsafe_fn` |
| `static mut COUNTER` | `AtomicUsize` / `OnceLock` / `Mutex` | edition guide static_mut_refs |
| std Mutex guard across `.await` | inner block scope | clippy await_holding_lock |
| `std::fs`/sync HTTP in async fn | `tokio::fs` / `spawn_blocking` | tokio spawn_blocking |
| `read_exact` in `select!` loop | move read into dedicated task/stream; use cancel-safe `recv`/`next` | tokio select! |
| pub `async fn` in trait, no Send story | `fn … -> impl Future + Send` or `#[trait_variant::make(X: Send)]` | Rust Blog 2023-12-21 |
| `+ '_` / `Captures<>` hacks on RPIT | remove (2024 captures all) or `use<..>` precise capture | edition guide RPIT capture |
| `Drop` that returns errors via panic | `close() -> Result` + best-effort Drop | C-DTOR-FAIL |
| `#[allow(clippy::x)]` w/o reason | `#[expect(clippy::x, reason = "…")]` | clippy allow_attributes(_without_reason) |

---

## 6. How the Rust community actually reviews

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

---

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

---

## 8. Gaps (not verified this session)

- Typestate pattern: no official/patterns-book chapter located; claims are `[from memory]`.
- `Cow`, `LazyLock`/`OnceLock` recommendations: from memory, std docs not opened.
- "Nit:" prefix convention in rust-lang reviews: from memory; not in Forge/dev-guide pages read.
- Edition guide "Never type fallback" page states changes are "no longer edition-specific as of Rust 1.100" — quoted verbatim; could not reconcile with release timeline.
- Did not open Rust Async Book or tokio "CPU-bound tasks and blocking code" section directly; async guidance drawn from tokio API docs + Rust Blog + clippy.
- Did not verify individual Effective Rust chapter URLs (cited via `print.html` + Item number).
- cargo-deny per-check config details (e.g. `multiple-versions`, `unknown-registry`) not read beyond checks index.
- Large-org Rust style guides (Google/Android, Microsoft, Embark, Fuchsia) not surveyed.
- Clippy lint group assignments change between releases; verified against lint index "stable" on 2026-11-21 only.
- API Guidelines last-updated date not shown on pages.