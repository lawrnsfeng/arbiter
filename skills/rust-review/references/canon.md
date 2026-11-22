# Rust canon

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

## Known gaps

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
