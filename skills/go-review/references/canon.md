# Go canon

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

## Known gaps

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
