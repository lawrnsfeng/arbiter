# Rust design and smells

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
