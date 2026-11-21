# Go severity guidance

## 7. Severity guidance

| Level | Items |
|---|---|
| **Block** | Ignored errors on fallible I/O/state changes; goroutine leak / no exit path; send-on-closed / multiple closers; data race (copied mutex, unsynchronized shared state); ctx not propagated on request path (lost cancellation/deadlines); panic escaping library boundary or recover-to-hide; `%w` leaking implementation errors in a public API (irreversible API commitment) — or `%v` dropping a cause callers are documented to inspect; security: `math/rand` keys, SQL/command injection, `InsecureSkipVerify`, secrets/PII in logs; exported API shape errors that can't be undone after release (returns interface needlessly, ctx in struct, mutable package globals, exported embedding) [B-ERR, GSB, CRC, GOSEC, CTX] |
| **Should fix (non-blocking, explain)** | Log-and-return; error string-matching; interface at producer / premature interface; unnecessary generics; async API where sync suffices; option sprawl; missing doc on exported identifiers or concurrency/cleanup contracts; test messages without inputs/got-want; assert libs in new code; unjustified buffered channel; `init()` side effects; util packages |
| **`Nit:`** | Stutter in unexported names; variable name length; receiver name choice; `failed to` phrasing; `%w` placement; named results; `x := x` leftovers in 1.22+ modules; `GetX` getter; slice capacity hints; comment wording; import aliasing |
| **Silent** | Anything gofmt/goimports/vet/staticcheck/enabled golangci linters flag (§2) — assume CI enforces; existing-code style drift not touched by the diff [GSG-idx] |

Calibration: GSG principle order (Clarity > Simplicity > Concision > Maintainability > Consistency) breaks ties [GSG]. Consistency with surrounding repo code beats an external style guide for Nit-level items [GSG-idx, UBER#be-consistent].
