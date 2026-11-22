# Go command cookbook

`V` = verified in the source column. `†` = from memory. Every command runs in the sandbox from §4.

| Task | Command |
|---|---|
| **Enumerate modules** | `go list -json ./...` V (S26) |
| **Dependency graph** | `go list -deps -test -json ./...` with `Imports`, `Deps`, `TestImports`, `XTestImports` V (S26) |
| **Graph-agnostic** | `codegraph impact <sym> --depth 2 --json`; `codegraph affected <files>`; `codegraph cycles` V (S10) |
| **Single test** | `go test -run '^TestX$' -count=1 ./pkg` † (`-count` V S26) |
| **Property testing** | `rapid.Check(t, func(t *rapid.T){...})` V (S42). `testing/quick` (frozen) † |
| **Fuzzing** | `go test -fuzz=FuzzX -fuzztime=60s ./pkg`. Failing input goes to `testdata/fuzz/FuzzX/<hash>` and becomes a regression test. Coverage only on amd64/arm64. Per-input timeout is 1 s. V (S25) |
| **Mutation (test strength)** | `gremlins unleash` V (S42). go-mutesting † |
| **Sanitizer / race** | `go test -race ./pkg`. It finds races **only on executed paths**. Exit code 66. V (S24) |
| **Type checker as oracle** | `go vet` †, `staticcheck ./...` † |
| **SAST** | semgrep (same flags) V. `gosec ./...` †. `govulncheck ./...` † |
| **API break** | `apidiff` (sorts changes into incompatible and compatible) V (S41). `gorelease` (S41 secondary) |
| **Benchmark** | `go test -run='^$' -bench=. -count=10 > old.txt`, same for `new.txt`, then `benchstat old.txt new.txt`. Use **≥10 runs, ideally 20.** V (S31) |
| **e2e** | `go test -tags=integration` † |
| Build gate | `go build ./...` |
| Vet gate | `go vet ./...` |
| Lint gate | `golangci-lint run --new-from-rev=<base>` (when `.golangci.*` exists) or `staticcheck ./...` |
| Test gate | `go test -count=1 <pkgs>` |
| Race | `go test -race -count=1 <pkgs>` |
| Analyzers | `gosec -fmt=json ./...`; `govulncheck -json ./...` |
