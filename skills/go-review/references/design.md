# Go design and smells

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
