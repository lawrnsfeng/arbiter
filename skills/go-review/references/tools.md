# Go tool-enforced layer

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
