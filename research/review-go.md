# Go code review research base

Ref keys used in tables → see §1. `[from memory]` = not verified this session.

## 1. Canon

| Key | Source | URL | Authority | Governs | Version/date |
|---|---|---|---|---|---|
| EG | Effective Go | https://go.dev/doc/effective_go | official (Go team) | baseline idioms: names, getters, `-er` interfaces, control flow, defer, embedding, concurrency | 2009 text, frozen; still referenced as baseline by GSG |
| CRC | Go Code Review Comments | https://go.dev/wiki/CodeReviewComments | official wiki | shorthand review comments (contexts, errors, interfaces, receivers, naming, goroutine lifetimes) | living wiki; edits require discussion |
| TC | Go Test Comments | https://go.dev/wiki/TestComments | official wiki | test-code review (no assert libs, got/want, cmp, t.Error vs t.Fatal, helpers) | living wiki |
| CRW | Go Wiki: CodeReview | https://go.dev/wiki/CodeReview | official wiki | reviewer parlance (LGTM, PTAL, s/foo/bar/), CL directives | living |
| CONTRIB | Contribution Guide | https://go.dev/doc/contribute | official | Gerrit votes (+1/+2/Hold), "comment = ticket", commit format | living |
| GSG-idx | Google Go Style overview | https://google.github.io/styleguide/go/ | org | defines Guide (normative+canonical), Decisions (normative), Best Practices (neither) | living |
| GSG | Google Go Style Guide | https://google.github.io/styleguide/go/guide | org, canonical | principles: Clarity > Simplicity > Concision > Maintainability > Consistency; least mechanism | living |
| GSD | Google Style Decisions | https://google.github.io/styleguide/go/decisions | org, normative | naming, repetition, errors, Must funcs, goroutine lifetimes, interfaces, generics, receivers | living |
| GSB | Google Best Practices | https://google.github.io/styleguide/go/best-practices | org, advisory | util pkgs, package size, error structure/wrapping/%w placement, logging, panics, options, global state, tests | living |
| UBER | Uber Go Style Guide | https://github.com/uber-go/guide/blob/master/style.md (read raw) | org | interface compliance, mutex zero value, copy at boundaries, channel size, enums, errors once, no fire-and-forget goroutines, init, exit in main, functional options, lint set | living |
| PROV | Go Proverbs | https://go-proverbs.github.io/ | community canon (Pike 2015) | design philosophy | 2015 talk |
| B-ERR | Working with Errors in Go 1.13 | https://go.dev/blog/go1.13-errors | official blog | Is/As/Unwrap, %w, "whether to wrap" = API commitment | 2019-10-17 |
| B-GEN | When To Use Generics | https://go.dev/blog/when-generics | official blog | when type params help / don't | 2022-04-12 |
| B-SLOG | Structured Logging with slog | https://go.dev/blog/slog | official blog | slog API, LogAttrs, With, LogValuer, vet check | 2023-08-22 |
| B-LOOP | Fixing For Loops in Go 1.22 | https://go.dev/blog/loopvar-preview | official blog | per-iteration loop vars; `x := x` now noise | 2023-09-19 |
| R122 | Go 1.22 release notes | https://go.dev/doc/go1.22 | official | loopvar shipped; range over int | 2024-02 |
| B-ITER | Range Over Function Types | https://go.dev/blog/range-functions | official blog | iter.Seq/Seq2, `All` method convention, iter.Pull + stop | 2024-08-20 |
| B-CTXS | Contexts and structs | https://go.dev/blog/context-and-structs | official blog | don't store ctx in structs; `FooContext` duplication exception | 2021-02-24 |
| CTX | context package source doc | https://raw.githubusercontent.com/golang/go/master/src/context/context.go | official | no ctx in structs, no nil ctx, Values request-scoped only, call CancelFunc | tip |
| SYNC | sync.Mutex / WaitGroup source | https://raw.githubusercontent.com/golang/go/master/src/sync/mutex.go , .../waitgroup.go | official | zero Mutex is unlocked; must not be copied; `WaitGroup.Go` exists | tip |
| EGRP | errgroup source | https://raw.githubusercontent.com/golang/sync/master/errgroup/errgroup.go | official x/ | Group, WithContext, first error cancels, zero Group valid | tip |
| LAYOUT | Organizing a Go module | https://go.dev/doc/modules/layout | official | `internal/`, `cmd/`, server layout | living |
| VET | cmd/vet | https://pkg.go.dev/cmd/vet | official | analyzer list | go1.27.4 (2026-11-10) |
| SC | Staticcheck checks | https://staticcheck.dev/docs/checks/ | community (de-facto std) | SA/S/ST/QF codes | living |
| GCL | golangci-lint linters | https://golangci-lint.run/docs/linters/ | community | linter catalog | page updated 2026-11-17 |
| GCL-QS | golangci-lint quick start | https://golangci-lint.run/docs/welcome/quick-start/ | community | default linters | 2026-11-17 |
| REVIVE | revive rule descriptions | https://raw.githubusercontent.com/mgechev/revive/master/RULES_DESCRIPTIONS.md | community | golint successor rules | tip |
| GOSEC | gosec README + RULES.md | https://raw.githubusercontent.com/securego/gosec/master/README.md , .../RULES.md | community | G1xx–G7xx security rules | tip (needs Go ≥1.25) |
| VULN | Go Vulnerability Management | https://go.dev/doc/security/vuln/ | official | govulncheck (reachability-based) | living |

Precedence for an AI reviewer: language spec / official docs (EG, CRC, TC, blogs) > GSG (canonical) > GSD > UBER ≈ GSB > linters' opinions. GSG-idx itself says: don't nit-pick every violation; don't cause churn in existing code [GSG-idx].

## 2. Tool-enforced layer (reviewer stays silent on these)

### 2.1 Formatters
| Tool | Catches | Src |
|---|---|---|
| `gofmt` | all layout/indent/spacing; "majority of mechanical style issues" | CRC#gofmt |
| `goimports` | gofmt + add/remove imports + stdlib-first grouping | CRC#imports |
| `gofmt -s` | composite-literal simplification `[from memory]` | — |

### 2.2 `go vet` analyzers (default-on in `go test` subset `[from memory]`; full list [VET])
`appends, asmdecl, assign, atomic, bools, buildtag, cgocall, composites` (unkeyed literals), `copylocks` (locks passed by value), `defers, directive, errorsas` (non-pointer to errors.As), `framepointer, hostport, httpresponse` (use resp before err check), `ifaceassert, loopclosure, lostcancel` (CancelFunc not called), `nilfunc, printf, shift, sigchanyzer, slog` (bad key/value pairs), `stdmethods, stdversion, stringintconv, structtag, testinggoroutine` (t.Fatal from goroutine), `tests, timeformat` (2006-02-01), `unmarshal, unreachable, unsafeptr, unusedresult, waitgroup` (misuse of WaitGroup).

### 2.3 Staticcheck [SC]
| Family | Representative codes (reviewer silent) |
|---|---|
| SA1 stdlib misuse | SA1006 Printf dynamic fmt; SA1012 nil ctx; SA1015 `time.Tick` leak; SA1019 deprecated API; SA1029 bad `context.WithValue` key; SA1032 `errors.Is` arg order |
| SA2 concurrency | SA2000 `wg.Add` inside goroutine; SA2001 empty critical section; SA2002 `t.FailNow` in goroutine; SA2003 deferred Lock |
| SA3 tests | SA3000 TestMain no os.Exit; SA3001 assigning b.N |
| SA4 no-op code | SA4006 value overwritten unread (forgotten err check); SA4010 unused append; SA4023 interface vs untyped nil; SA4031 never-nil check |
| SA5 correctness | SA5000 nil map write; SA5001 defer Close before err check; SA5007 infinite recursion; SA5008 bad struct tag; SA5010 impossible assertion |
| SA6 perf | SA6000 regexp in loop; SA6002 non-pointer in sync.Pool; SA6005 ToLower compare |
| SA9 dubious | SA9001 defer in range loop; SA9003 empty branch; SA9010 returned func should be deferred |
| S1 simplify | S1000…S1040 (e.g. S1008 return bool expr, S1012 time.Since, S1028 fmt.Errorf) |
| ST1 style | ST1000 package comment; ST1001 dot import; ST1003 naming/initialisms; ST1005 error strings; ST1006 receiver name; ST1008 error last; ST1012 err var naming; ST1013 HTTP status consts; ST1016 consistent receivers; ST1017 Yoda; ST1020–1022 doc starts with name |
| QF1 quickfix | QF1001 De Morgan … QF1012 Fprintf |

### 2.4 golangci-lint
Defaults: `errcheck, govet, ineffassign, staticcheck, unused` [GCL-QS]. Uber minimum: errcheck, goimports, revive, govet, staticcheck; runner = golangci-lint [UBER#linting].

| Linter | Mechanizes | Src |
|---|---|---|
| errcheck | unchecked errors (CRC "Handle Errors") | GCL |
| revive | golint successor: `context-as-argument`, `error-strings`, `exported`, `indent-error-flow`, `receiver-naming`, `unexported-return`, `var-naming`, error-naming (Err/err prefix) | REVIVE |
| gocritic | bug/perf/style diagnostics; individual check names `[from memory]`: `hugeParam`, `rangeValCopy`, `appendAssign`, `ifElseChain` | GCL |
| errorlint | Go 1.13 wrapping problems (== on errors, type assertion on errors, %v instead of %w) — subchecks `[from memory]` | GCL |
| wrapcheck | errors from external packages returned unwrapped | GCL |
| contextcheck | function uses non-inherited context | GCL |
| containedctx / fatcontext / noctx | ctx in struct; nested ctx in loops; missing ctx | GCL |
| gosec | G101 hardcoded creds, G104 unchecked errors, G107 tainted URL, G115 int overflow conversion, G201/G202 SQL via fmt/concat, G204 exec, G304 tainted file path, G401 MD5/SHA1, G402 bad TLS, G404 weak rand, G601 range aliasing (≤1.21), G7xx taint | GOSEC |
| errname, nilerr, nilnil, bodyclose, rowserrcheck, sqlclosecheck, sloglint, loggercheck, thelper, tparallel, usetesting, copyloopvar, intrange, modernize, ireturn, iface, interfacebloat, recvcheck, predeclared, gochecknoinits, gochecknoglobals, musttag, exhaustive | see one-line descriptions on GCL | GCL |

### 2.5 Supply chain
`govulncheck ./...` — reports only vulns reachable from your call graph [VULN]. Reviewer: silent on known CVEs if CI runs it; flag if not wired.

### 2.6 What tools CANNOT catch (reviewer's job)
1. Interface placed at producer / defined before a 2nd use / too wide [CRC#interfaces, GSD#interfaces].
2. Wrap (`%w`) vs hide (`%v`) as API commitment [B-ERR, GSB].
3. Error handled twice (log + return) [UBER, GSB#logging-errors].
4. Goroutine lifetime unclear / no owner of shutdown [CRC, GSD].
5. Who closes a channel; buffered size justification [UBER#channel-size].
6. Async API where sync would do [CRC#synchronous-functions].
7. Package naming/stutter, util/common pkgs, package boundaries [CRC, GSD, GSB].
8. Generics where an interface or concrete type suffices [B-GEN, GSD].
9. Context stored in struct (containedctx catches field, not intent/exceptions) [B-CTXS].
10. Mutable package state in a library API [GSB#global-state].
11. Doc comments that restate code / miss concurrency, cleanup, error contracts [GSB documentation conventions].
12. Test quality: assert libs, got/want order, missing input in message, change-detector tests [TC].
13. Zero-value usefulness of new types [PROV].
14. Panic crossing package boundary; recover-to-hide [GSB#when-to-panic].

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

## 4. Design patterns & architecture

| Pattern | Go verdict | Go-native form | Source |
|---|---|---|---|
| Strategy | idiomatic | func value or small consumer-side interface | GSD#interfaces (lists strategy), B-GEN (pass funcs) |
| Iterator | idiomatic since 1.23 | `iter.Seq[V]`/`Seq2[K,V]`, `All()` method; `iter.Pull` for pull | B-ITER |
| Builder | mostly anti-idiomatic | option struct or functional options | GSB#option-structure, UBER#functional-options |
| Functional options | idiomatic for optional config | `New(x, opts ...Option)` | GSB#variadic-options, UBER |
| Factory / abstract factory | factory OK, returning concrete type | `NewX(...) *X`; interface return only for encapsulation | GSD#interfaces |
| Singleton | anti-idiomatic in libraries | explicit instance passed as dependency; optional default instance | GSB#global-state |
| Dependency injection frameworks | anti-idiomatic default | constructor params in `main` | GSB#global-state |
| Repository/Service layers | allowed only with real need | don't create "service"/"repository" interfaces by name | GSD#interfaces |
| Template method / inheritance | anti-idiomatic | composition + embedding (unexported), interfaces | UBER#embedding, EG |
| Observer / pub-sub | channels if lifetime clear | channel with documented owner/closer, or callback | CRC#goroutine-lifetimes |
| Decorator/middleware | idiomatic | `func(http.Handler) http.Handler`, wrapping slog.Handler | B-SLOG |
| Adapter | idiomatic | func type implementing interface (`http.HandlerFunc`) `[from memory]` | — |
| Visitor | rarely needed | type switch | EG#type-switch |
| Null object | built-in | useful zero value | PROV |
| Worker pool | idiomatic w/ bounds | `errgroup` + `SetLimit` `[SetLimit from memory]`, ctx cancel | EGRP |
| Must-wrapper | idiomatic at init only | `MustParse` for package vars/tests | GSD#must-functions |

Layering / packages:
- Group by responsibility, not by kind (`models`, `utils`, `interfaces` = smell) [CRC#package-names, GSB#util-packages].
- Couple tightly-related types in one package; split if users would need both packages anyway → merge [GSB#package-size].
- `internal/` first; `cmd/<prog>/main.go` for binaries; server logic under `internal/` [LAYOUT].
- Interfaces live with consumers; producers return concrete types [CRC#interfaces].
- `main` wires dependencies, parses flags, owns `os.Exit` / `log.Fatal` [UBER#exit-in-main, GSB#program-initialization].
- Sharable code grows → split into separate module [LAYOUT].

## 5. Language-specific smells → refactoring

| Symptom | Refactor | Source |
|---|---|---|
| `type FooService interface` + `fooServiceImpl` in same pkg | Delete interface; export struct; consumer defines minimal interface | CRC#interfaces |
| `pkg.PkgThing` stutter | Rename to `pkg.Thing`; `NewThing`→`New` | GSD#repetition |
| `utils.go` / `package common` | Move funcs next to their single user or into a named package | GSB#util-packages |
| `if err != nil {…} else {happy}` | Early return, dedent | CRC#indent-error-flow |
| Error chain `failed to a: failed to b: …` | Verb-noun context only | UBER, GSB |
| `log.Error(err); return err` | Return wrapped; log at top | UBER#handle-errors-once |
| `strings.Contains(err.Error(), "not found")` | Sentinel/typed error + `errors.Is/As` | GSB#error-structure |
| `return nil, nil` meaning "absent" | `(T, bool)` or sentinel error | CRC#in-band-errors (nilnil) |
| `go doWork()` in loop, no wait | `errgroup.WithContext`; `g.Wait()` | GSD#goroutine-lifetimes, EGRP |
| `done := make(chan bool)` + mutex + err var | errgroup | EGRP |
| `make(chan T, 100)` "just in case" | Unbuffered or 1; backpressure design | UBER |
| `type S struct { ctx context.Context }` | Per-method `ctx` param | B-CTXS |
| `ctx.Value("userID")` string key | Unexported key type + typed accessor; or explicit param | CTX (SA1029) |
| `func F(a, b, c string, x, y bool, n int)` | Option struct / functional options | GSB |
| `func Max[T any](...)` used with one type | Drop type params | GSD#generics |
| `func Read[T io.Reader](r T)` | `func Read(r io.Reader)` | B-GEN |
| `[]interface{}` + type switch for containers | Generic container | B-GEN |
| `ForEach(func(T) bool)` container API | `All() iter.Seq[T]` | B-ITER |
| `v := v` in 1.22+ module | Delete line | B-LOOP |
| Package-level `var DB *sql.DB` in library | Instance struct passed explicitly | GSB#global-state |
| `init()` reading env/files | Explicit setup in `main` | UBER#avoid-init |
| Exported struct embedding `sync.Mutex` | Unexported `mu sync.Mutex` field | UBER |
| `mu *sync.Mutex` field | Value field (zero usable) | UBER, SYNC |
| Value receiver on struct with mutex | Pointer receiver everywhere | CRC#receiver-type |
| Mixed value/pointer receivers | Pick one | CRC#receiver-type (recvcheck) |
| `assert.Equal(t, want, got)` style | `if diff := cmp.Diff(want, got); diff != "" { t.Errorf("F(%v) mismatch (-want +got):\n%s", in, diff) }` | TC |
| `t.Errorf("got %v want %v")` | `t.Errorf("F(%q) = %v, want %v", in, got, want)` | TC |
| Mock interface for RPC client | Real transport / fake server | GSD#interfaces |
| `panic(err)` in library | Return error; `Must*` variant only for init | CRC, GSD |
| `math/rand` token | `crypto/rand.Text()` | CRC#crypto-rand |
| `log.Printf("user %s did %s", u, a)` | `slog.Info("action", "user", u, "action", a)` | B-SLOG |
| GetX() getters | `X()` | EG#getters |
| Huge interface (10+ methods) | Split into role interfaces at consumers | PROV, GSD |

## 6. How the Go community actually reviews

- **Gerrit CLs, not PRs.** GitHub PRs mirrored via GerritBot. Votes: **+2** approve (maintainers only), **+1** looks good / non-maintainer, **Hold +1** blocks (e.g. pending proposal review). Submission needs +2, no Hold, and 2 Google employees involved [CONTRIB].
- **Every comment is a ticket**: author must close each by "Done" or reply explaining why not [CONTRIB#reviews].
- **Gerrit reviews implementation only**; merit is settled earlier on the issue tracker / proposal process. No issue → only trivial changes accepted [CONTRIB].
- **First-pass beginner checks**: commit message format (`pkg: lowercase summary` completing "This change modifies Go to ___"), linked issue, freeze timing (`R=go1.XX`) [CONTRIB].
- **Parlance**: `LGTM`, `SGTM`, `PTAL`, `s/foo/bar/(g)`; `DO NOT SUBMIT`, `DO NOT REVIEW` on line 2; `Fixes #N` / `Updates #N` [CRW].
- **Shorthand-by-link**: CRC exists "so that a single detailed explanation can be referred to by shorthands" — reviewers link anchors (e.g. `go.dev/wiki/CodeReviewComments#indent-error-flow`) instead of explaining [CRC]. Revive rule docs also link CRC anchors [REVIVE]. → AI reviewer should cite the anchor.
- **Google readability**: GSD is the reference for "readability mentors"; authors not expected to know it; reviewers "do not need to nit-pick every violation"; style docs are "no reason to cause extra churn in existing codebases" [GSG-idx].
- **Perf claims need benchstat numbers** in the change description [CONTRIB#main-content].

## 7. Severity guidance

| Level | Items |
|---|---|
| **Block** | Ignored errors on fallible I/O/state changes; goroutine leak / no exit path; send-on-closed / multiple closers; data race (copied mutex, unsynchronized shared state); ctx not propagated on request path (lost cancellation/deadlines); panic escaping library boundary or recover-to-hide; `%w` leaking implementation errors in a public API (irreversible API commitment) — or `%v` dropping a cause callers are documented to inspect; security: `math/rand` keys, SQL/command injection, `InsecureSkipVerify`, secrets/PII in logs; exported API shape errors that can't be undone after release (returns interface needlessly, ctx in struct, mutable package globals, exported embedding) [B-ERR, GSB, CRC, GOSEC, CTX] |
| **Should fix (non-blocking, explain)** | Log-and-return; error string-matching; interface at producer / premature interface; unnecessary generics; async API where sync suffices; option sprawl; missing doc on exported identifiers or concurrency/cleanup contracts; test messages without inputs/got-want; assert libs in new code; unjustified buffered channel; `init()` side effects; util packages |
| **`Nit:`** | Stutter in unexported names; variable name length; receiver name choice; `failed to` phrasing; `%w` placement; named results; `x := x` leftovers in 1.22+ modules; `GetX` getter; slice capacity hints; comment wording; import aliasing |
| **Silent** | Anything gofmt/goimports/vet/staticcheck/enabled golangci linters flag (§2) — assume CI enforces; existing-code style drift not touched by the diff [GSG-idx] |

Calibration: GSG principle order (Clarity > Simplicity > Concision > Maintainability > Consistency) breaks ties [GSG]. Consistency with surrounding repo code beats an external style guide for Nit-level items [GSG-idx, UBER#be-consistent].

## 8. Gaps

- gocritic and errorlint sub-check names: only linter one-liners verified; check names `[from memory]`.
- staticcheck: only the index table read; per-check rationale beyond SA1000–SA1006 not opened.
- Uber sections cited by heading only (not body-read): verify interface compliance ✔ read; channel size ✔; errors once/wrapping/naming ✔; **not body-read**: zero-value mutexes, copy at boundaries, enums, time, avoid embedding, init, exit in main, field tags, fire-and-forget goroutines, functional options, perf sections.
- GSD read only for repetition, Must, goroutine lifetimes, interfaces, generics, pass values, receiver type. GSB read for util pkgs, package size, error handling/%w placement, logging, panics, option struct, global state; documentation-conventions and test sections cited by heading only.
- Effective Go: only section headings + getter/`-er` lines verified.
- `sync.WaitGroup.Go` exists (verified in source) but the Go version that added it (1.25) is `[from memory]`; same for `errgroup.SetLimit`, `errors.Join` (1.20), `t.Context` (1.24), `testing/synctest`.
- gopls `modernize` analyzer suite: only golangci-lint one-liner seen.
- Google GoTips (#13, #48, #49, #78, #89…) referenced by GSG but not publicly readable.
- Channel-close ownership ("sender closes") is community canon `[from memory]`; GSD only verifies "send on closed channel panics".
- pkg.go.dev rendering failed for `context` and `errgroup`; used raw source doc comments instead.