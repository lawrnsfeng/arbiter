# Go idioms

## 3. Idiom checklist (reviewer-only)

| Area | Flag | Don't flag (exception) | Source |
|---|---|---|---|
| Naming | Stutter: `widget.NewWidget`, `chubby.ChubbyFile`, `(p *Project) ProjectName()` | Package exports one type named like pkg → constructor `New` is canonical | CRC#package-names, GSD#repetition |
| Naming | Type in var name: `numUsers int`, `nameString` | Value appears twice in two forms (`limitRaw`/`limit`) | GSD#repetition |
| Naming | Long names for short-lived locals; short names for package-level/far-used | Loop index/reader single letter OK | CRC#variable-names |
| Naming | `GetOwner()` getter | Setter `SetOwner` is fine | EG#getters |
| Naming | Single-method interface not `-er` (`Reader`, `Formatter`) | Established domain names | EG#interface-names |
| Naming | `Url`, `Id`, `HttpServer` | protoc-generated code | CRC#initialisms (ST1003 catches most) |
| Naming | Receiver `this`/`self`/`me`; inconsistent across methods | — | CRC#receiver-names |
| Naming | Package `util`, `common`, `misc`, `helper`, `types`, `interfaces`, `api` | As *part* of a name (`spannertest`, `gtutil`) | CRC, GSB#util-packages |
| Naming | Sentinel not `ErrX`/`errX`; error type not `XError` | — | UBER#error-naming (errname/revive) |
| Naming | Printf-like func without `f` suffix | — | UBER#naming-printf (goprintffuncname) |
| Errors | `_ = f()` / ignored error | Documented never-fails (e.g. `bytes.Buffer.Write`) `[from memory]`; errgroup "only first error useful" | CRC#handle-errors, GSB#error-handling |
| Errors | In-band error (`-1`, `""`) where caller must check | Value is a valid result; `strings` style | CRC#in-band-errors |
| Errors | `%w` wrapping implementation-detail errors (e.g. `sql.ErrNoRows` from a repo layer) → leaks abstraction, becomes API | Caller-supplied dependency errors (e.g. reader they passed in) — wrap | B-ERR#whether-to-wrap |
| Errors | `%v` where callers are documented to `errors.Is` the cause | Boundary translation (RPC/storage) → `%v` or canonical status deliberate | GSB#adding-information |
| Errors | `failed to`, `unable to`, `couldn't` prefixes | Message leaving system (log `err` tag) | UBER#error-wrapping, GSB |
| Errors | Annotation repeating info callee already has (`open settings.txt: open settings.txt: ...`) | — | GSB |
| Errors | `fmt.Errorf("failed: %v", err)` adding nothing | — | GSB ("just return err") |
| Errors | `%w` not at end | Sentinel categorization `%w: detail` | GSB#placement-of-w |
| Errors | `err.Error()` string matching / regex on messages | Tests checking message mentions a param | GSB#error-structure, TC |
| Errors | `err == ErrX` / `err.(*T)` on possibly-wrapped errors | Error known unwrapped by contract (errorlint catches) | B-ERR |
| Errors | Log **and** return same error | Recoverable → log & degrade | UBER#handle-errors-once, GSB#logging-errors |
| Errors | Capitalized / punctuated error strings | Proper nouns, acronyms | CRC#error-strings (ST1005) |
| Errors | `panic` for ordinary failure in library | Invariant/API misuse; `Must*` at init; internal panic+recover never crossing pkg boundary | CRC#dont-panic, GSD#must-functions, GSB#when-to-panic |
| Errors | `recover()` to keep server alive / hide bugs | — (net/http's recover called "historical mistake") | GSB#program-checks |
| Errors | `log.Fatal`/`os.Exit` outside `main` | Init-time unrecoverable state | UBER#exit-in-main, GSB#program-initialization |
| Errors | Error not last result | — | ST1008 (tool) |
| Control flow | `else` after error-return; happy path indented | — | CRC#indent-error-flow (revive) |
| Control flow | Subtle `=` vs `:=` shadow in `if v, err = ...` | Explicit, commented | GSG#maintainability |
| Resources | Missing `defer Close/Unlock/cancel` immediately after acquire | Write-path Close whose error matters → check it explicitly | UBER#defer-to-clean-up; GOSEC G307 retired rationale |
| Resources | `defer` in loop body | Wrap body in a func | SA9001 (tool) — flag only intent |
| Resources | `resp.Body` not closed; `rows.Err()` unchecked | — | bodyclose/rowserrcheck (tools) |
| API design | Interface returned from constructor ("for mocking") | `error`; encapsulation for strategy/factory/chaining; interface *is* the product (`io.Reader`) | CRC#interfaces, GSD#interfaces |
| API design | Interface defined in producer package, or before any consumer exists | Protocol packages | CRC#interfaces |
| API design | Interface wider than consumer uses | — | GSD#interfaces, PROV "bigger interface, weaker abstraction" |
| API design | Interface wrapping RPC client just for tests | Use real transport / dedicated test pkg (`spannertest`) | GSD#interfaces |
| API design | Signature with many same-typed params / bool flags | Option struct; variadic options when most callers pass none | GSB#function-argument-lists, UBER#avoid-naked-parameters |
| API design | `context.Context` inside option struct | Never allowed | GSB#option-structure |
| API design | `*string`, `*io.Reader` params; pointer to save bytes | Large or growing structs; protos | CRC#pass-values |
| API design | Named results only to enable naked return / that stutter in godoc | Same-typed multiple results; deferred modification | CRC#named-result-parameters |
| API design | Async API (returns chan / starts goroutine) where sync works | Inherently streaming | CRC#synchronous-functions |
| API design | Exported func returns unexported type | Exported alias | revive `unexported-return` |
| API design | Distinguishing nil vs empty slice in API semantics | JSON `[]` vs `null` needed | CRC#declaring-empty-slices |
| API design | Library exports mutable package-level config / registry | Provide instance + optional default instance | GSB#global-state, UBER#avoid-mutable-globals |
| API design | Embedding a type in a public struct (leaks methods, blocks evolution) | Unexported structs; deliberate promotion | UBER#avoid-embedding-types-in-public-structs |
| Types | `interface{}`/`any` + type switches where generics fit | — | PROV "interface{} says nothing", GSD#generics |
| Types | Generics with only one instantiation | Container/algorithms over slices/maps/chans; general data structures; identical method impls | B-GEN, GSD#generics |
| Types | `func F[T io.Reader](r T)` | Never — use the interface | B-GEN |
| Types | Constraint requiring `Less` method on element | Pass a `cmp func(T,T) int` instead | B-GEN |
| Types | Generic DSLs / error-handling or assert frameworks | — | GSD#generics |
| Types | Single-value type assertion `x.(T)` on untrusted input | Invariant-guaranteed | UBER#handle-type-assertion-failures (forcetypeassert) |
| Types | Missing `var _ I = (*T)(nil)` for exported types that must satisfy I | Not part of contract | UBER#verify-interface-compliance |
| Data modeling | Enum iota starting at 0 where zero = valid state | Zero is meaningful default | UBER#start-enums-at-one |
| Data modeling | `int` seconds / ms for durations; `int64` epoch for instants | External format needs it — name with unit | UBER#use-time |
| Data modeling | Type whose zero value is unusable without constructor | Documented `New` required | PROV "make the zero value useful" |
| Data modeling | Marshaled struct without field tags | — | UBER#use-field-tags (musttag) |
| Data modeling | Storing caller's slice/map without copy; returning internal slice/map | Documented ownership transfer | UBER#copy-slices-and-maps-at-boundaries |
| Data modeling | `map[string]bool` replaced by 3rd-party set lib | Complex set algebra | GSG#least-mechanism |
| Concurrency | `go f()` with no stated exit / no WaitGroup/errgroup/ctx | Process-lifetime daemons documented | CRC#goroutine-lifetimes, GSD, UBER#dont-fire-and-forget |
| Concurrency | Goroutine blocked forever on send/recv (leak) | — | CRC#goroutine-lifetimes |
| Concurrency | Receiver/consumer closes channel; multiple closers | Sender owns close `[from memory: canonical rule; supported by GSD "send on closed channel panics"]` | GSD#goroutine-lifetimes |
| Concurrency | Buffered channel size >1 without justification | Size 1 or 0 | UBER#channel-size |
| Concurrency | Hand-rolled WaitGroup + error var + mutex for fan-out | `errgroup.Group` / `WithContext` (first error cancels) | EGRP, GSB#error-handling |
| Concurrency | `wg.Add(1); go func(){defer wg.Done()...}` boilerplate on Go ≥1.25 | `wg.Go(f)` exists (version `[from memory]`) | SYNC |
| Concurrency | `mu := new(sync.Mutex)` / `*sync.Mutex` field | Zero `sync.Mutex` is valid | UBER#zero-value-mutexes, SYNC |
| Concurrency | Struct with Mutex copied / value receiver | — | CRC#receiver-type, SYNC "must not be copied" (copylocks catches pass-by-value) |
| Concurrency | Embedded `sync.Mutex` in exported struct (exposes Lock/Unlock) | Unexported type | UBER#zero-value-mutexes |
| Concurrency | goroutines in `init()` | — | UBER#no-goroutines-in-init |
| Concurrency | Channels used to serialize state where mutex is simpler (or vice-versa) | "Channels orchestrate; mutexes serialize" | PROV |
| Context | ctx not first param; named other than `ctx` | Interface-mandated signatures | CRC#contexts (revive context-as-argument) |
| Context | ctx stored in struct field | Backward-compat retrofit (`http.Request`); prefer `FooContext` duplicate | B-CTXS, CTX |
| Context | `context.Background()` deep in request path | `main`, init, tests, truly non-request work | CRC#contexts |
| Context | Custom Context type / interface | — | CRC#contexts |
| Context | Values used for optional params / dependencies | Request-scoped data crossing API/process boundaries | CTX |
| Context | `WithCancel/Timeout` cancel not called on all paths | — | CTX, vet lostcancel |
| Loops (1.22+) | `x := x` / `v := v` copies in modules with `go ≥1.22` | Module `go` line < 1.22 | B-LOOP, R122 (copyloopvar autofix) |
| Loops (1.22+) | `for i := 0; i < n; i++` with unused complexity | `for i := range n` | R122 (intrange) |
| Iterators (1.23+) | Custom `Push`/`Pull`/`Each(func)` loop APIs on new containers | Return `iter.Seq`/`Seq2` via `All()` method | B-ITER |
| Iterators | Iterator ignores `yield` returning false | Must return immediately | B-ITER |
| Iterators | `iter.Pull` without `defer stop()` | Fully drained | B-ITER |
| Iterators | Channel+goroutine iterator | Push iterator (no goroutine) | B-ITER |
| Modules/visibility | New support packages exported by default | Start in `internal/` | LAYOUT |
| Modules/visibility | `import _` outside main/tests | — | CRC#import-blank |
| Modules/visibility | `import .` | Circular-dep test case | CRC#import-dot (ST1001) |
| Modules/visibility | Import renamed without collision | Collision: rename most local | CRC#imports |
| Modules/visibility | `init()` with side effects / I/O | Deterministic, no env/IO | UBER#avoid-init (gochecknoinits) |
| Modules/visibility | One-file-per-type; 5k-line files | Group by concern | GSB#package-size |
| Modules/visibility | New dependency for a few lines | — | PROV "a little copying…", GSG#least-mechanism |
| Testing | assert/require libraries | Repo already standardizes on one (consistency) | TC#assert-libraries, GSD#generics |
| Testing | `got`/`want` reversed or unlabeled | — | TC#got-before-want |
| Testing | Failure message omits function name / inputs; uses table index | — | TC#identify-the-function/-input |
| Testing | `t.Fatal` where `t.Error` lets test keep going | Setup failure; inside subtest | TC#keep-going |
| Testing | Helper without `t.Helper()`; `t.Helper` used to build assert lib | — | TC#mark-test-helpers |
| Testing | Field-by-field struct compare; `reflect.DeepEqual` | `cmp.Diff(want, got)` with "-want +got" | TC#compare-full-structures, #equality |
| Testing | Exact JSON string compare | Parse and compare semantically | TC#compare-stable-results |
| Testing | Error string comparison | Message contains param name | TC#test-error-semantics |
| Testing | Tables with per-row branching logic | Split into multiple test funcs | TC#table-driven |
| Testing | `t.Fatal` from goroutine | — | GSB#dont-call-tfatal-from-goroutines (vet testinggoroutine) |
| Testing | Interface + mock where real impl usable | — | CRC#interfaces, GSD |
| Testing | New package with no Example | — | CRC#examples |
| Docs | Exported name without doc; doc not starting with name; not full sentence | — | CRC#doc-comments (revive exported, ST1020-22) |
| Docs | Comment explains *what* not *why* | — | GSG#clarity |
| Docs | Missing doc of concurrency safety, cleanup obligations, returned sentinel errors, ctx behavior | Obvious defaults (read-only methods safe) | GSB documentation conventions |
| Docs | Subtle code (e.g. `err == nil` check) not signal-boosted | — | GSG#concision |
| Logging | `log.Printf` / string-concat in new server code | slog with key/value attrs | B-SLOG |
| Logging | Odd key/value count, non-constant keys | — | vet slog, sloglint |
| Logging | Hot path using alternating args | `LogAttrs` + typed Attrs | B-SLOG |
| Logging | Repeated attrs on every call | `logger.With(...)` | B-SLOG |
| Logging | Logger smuggled via ctx | Explicit dependency (feature removed from slog for this reason) | B-SLOG |
| Logging | PII/secrets in logs | `LogValuer` redaction | B-SLOG, GSB#logging-errors |
| Perf | Premature value receivers/pointers "for speed" w/o profile | Measured | CRC#receiver-type |
| Perf | `fmt.Sprint` for int→string | `strconv` | UBER#prefer-strconv (perfsprint) |
| Perf | Known-size slice/map without capacity hint | Unknown size | UBER#container-capacity (prealloc) |
| Perf | Repeated `[]byte("const")` in loop | Hoist | UBER |
| Perf | Unexplained clever perf code | Commented as perf-critical | GSG#simplicity |
| Security | `math/rand` for keys/tokens | `crypto/rand.Text` / `Reader` | CRC#crypto-rand (gosec G404) |
| Security | SQL via `fmt`/concat; `exec.Command("sh","-c", userInput)` | Parameterized | GOSEC G201/G202/G204 |
| Security | `InsecureSkipVerify: true` | Tests w/ `#nosec G402 -- reason` | GOSEC |
| Security | `#nosec` without justification | `-- reason` present | GOSEC |
| Security | `unsafe`, cgo, syscall without build tags / rationale | — | PROV |
| Security | govulncheck absent from CI | — | VULN |

## Community review practice

- **Gerrit CLs, not PRs.** GitHub PRs mirrored via GerritBot. Votes: **+2** approve (maintainers only), **+1** looks good / non-maintainer, **Hold +1** blocks (e.g. pending proposal review). Submission needs +2, no Hold, and 2 Google employees involved [CONTRIB].
- **Every comment is a ticket**: author must close each by "Done" or reply explaining why not [CONTRIB#reviews].
- **Gerrit reviews implementation only**; merit is settled earlier on the issue tracker / proposal process. No issue → only trivial changes accepted [CONTRIB].
- **First-pass beginner checks**: commit message format (`pkg: lowercase summary` completing "This change modifies Go to ___"), linked issue, freeze timing (`R=go1.XX`) [CONTRIB].
- **Parlance**: `LGTM`, `SGTM`, `PTAL`, `s/foo/bar/(g)`; `DO NOT SUBMIT`, `DO NOT REVIEW` on line 2; `Fixes #N` / `Updates #N` [CRW].
- **Shorthand-by-link**: CRC exists "so that a single detailed explanation can be referred to by shorthands" — reviewers link anchors (e.g. `go.dev/wiki/CodeReviewComments#indent-error-flow`) instead of explaining [CRC]. Revive rule docs also link CRC anchors [REVIVE]. → AI reviewer should cite the anchor.
- **Google readability**: GSD is the reference for "readability mentors"; authors not expected to know it; reviewers "do not need to nit-pick every violation"; style docs are "no reason to cause extra churn in existing codebases" [GSG-idx].
- **Perf claims need benchstat numbers** in the change description [CONTRIB#main-content].
