# Rust tool-enforced layer

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
