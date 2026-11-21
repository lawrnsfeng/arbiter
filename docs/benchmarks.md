# Benchmarks: datasets, ground truth, scoring and results

All numbers in this file were measured on 2026-11-21 with `arbiter eval`. The raw result files are listed in
§6, and anyone can recompute every figure from them.

## 1. Datasets

### 1.1 Seeded corpus (`eval/seeded/`)

The corpus has 28 small projects: 7 per language, 5 with a planted bug and 2 clean.

- Each case directory holds a `base/` project that builds and passes its tests, a `change.patch`, and `expected.json`.
- `arbiter eval seeded build` turns a case into a git repository under `eval/results/repos/<lang>-<case>/`.
  - It commits `base/` as the base, applies the patch and commits the head.
  - The commit messages are neutral ("chore: initial project", "feat: extend the project"), so they don't give the bug away to A0 or SPEC.
- Every patch looks like a plausible feature change that carries the bug.
- The project's existing tests still pass after the patch, so the bug is latent and the test gate alone cannot find it.

**Ground truth.** Each bug case's `expected.json` lists entries `{file, line, axes, must, note}`; clean cases list `[]`.
- Line numbers refer to the patched file.
- `must: false` marks a valid but optional finding (Rust 05 has two). It counts as a match when found, but not in the recall denominator.
- Each case author checked that the patch applies, that the tests pass before and after it, and that `sed -n <line>p` shows the bug line.
- Some bugs were also reproduced with throwaway tests:
  - go-01: `Has(6)` panics with an index out of range.
  - go-02: a missing include returns a nil error.
  - go-03: `-race` reports a data race with 4 documents.
  - rust-01: `Addr::parse("h:x")` panics.
  - rust-02: the header says length 1 for a 65541-byte frame.

| Case | Bug (ground truth) | Expected axes |
|---|---|---|
| go-01 | `inventory.go:21` binary search `hi := len(ids)` with `lo <= hi` | logic, edge |
| go-02 | `config.go:29` inner `err :=` shadows the outer error, so `Load` returns nil | errors |
| go-03 | `count.go:19` map written from goroutines without a mutex | concurrency |
| go-04 | `server.go:30` `exec.Command("sh","-c", "ping -c 1 "+host)` from an HTTP query parameter (CWE-78) | security |
| go-05 | `user/user.go:16` producer-side interface + `UserService` stutter; `:35` `GetName` getter; `:47` leftover `u := u` | idiom, design |
| python-01 | `pager/core.py:19` `items[start:end + 1]` | logic, edge |
| python-02 | `notes/store.py:6` `bucket: list[str] = []`; `:25` `except Exception: pass` around a file read | edge/logic; errors/edge |
| python-03 | `inventory/db.py:30` f-string SQL with an HTTP parameter, server on `0.0.0.0` (CWE-89) | security |
| python-04 | `fetcher/load.py:19` `asyncio.create_task` result dropped; `:30` `time.sleep` in `async def` | concurrency, errors, performance |
| python-05 | `plugins/registry.py:11` GoF Singleton; `:7` `TypeVar`/`Generic[T]` in a 3.12 project; `:28` `for i in range(len(names))` | idiom, design |
| rust-01 | `src/lib.rs:28` `port.parse::<u32>().unwrap()` in a public parser | edge, errors |
| rust-02 | `src/lib.rs:39` `(head.len() + body.len()) as u16` | logic |
| rust-03 | `src/lib.rs:28` `std::sync::Mutex` guard held across `.await` | concurrency |
| rust-04 | `src/lib.rs:28` `unsafe { get_unchecked(i) }` in a safe public fn, no bounds check, no `// SAFETY:` | resources, edge |
| rust-05 | `src/lib.rs:24` `&Vec<Item>, &String`; `:34` `Box<dyn Error>` in a public lib API (`:25` index loop and `:26` needless clone are optional) | idiom, design |
| ts-01 | `src/sync.ts:14` `items.forEach(async x => await save(x))`, with the caller assuming completion | errors, concurrency |
| ts-02 | `src/signup.ts:11` `JSON.parse(body) as User` used without validation | edge, security |
| ts-03 | `src/heading.ts:5` `el.innerHTML` from a URL parameter (CWE-79) | security |
| ts-04 | `src/report.ts:8` `b.day < to` where the docstring says both days are included | logic, edge |
| ts-05 | `src/status.ts:1` `enum` where a union fits; `:8` `any` parameter + default export; `:9` non-exhaustive `switch` | idiom, design |
| *-06 | Rename refactor with updated tests | clean |
| *-07 | New idiomatic pure function with tests | clean |

### 1.2 Martian Code Review Bench, offline golden set

- Source: `withmartian/code-review-benchmark`, MIT licence. The files `offline/golden_comments/{sentry,grafana,cal_dot_com}.json` were fetched by `arbiter eval martian fetch`. The commit SHA is pinned in `eval/martian/golden/SOURCE.json`.
- The golden comments are human-curated review comments on real PRs. Each has a severity and a category.
- These three repos give 10 PRs each: sentry is Python, grafana is Go and cal.com is TypeScript.
- Martian's full set has 50 PRs and 173 comments over 5 repos `[AI-§3]`. The other two repos are Java and Ruby, which arbiter does not support.
- arbiter clones each PR's repository with a blob-less filter (`--filter=blob:none`), checks out `pull/<n>/head`, and reviews it against `origin/<base.ref>`.

## 2. Scoring

### 2.1 Seeded

A main-section finding **matches** an expected entry when all three hold:
- it is in the same file
- its line is within ±3 of the expected line
- at least one of its axes is among the expected axes

The finding's axes are its representative axis plus every axis merged into it.

| Metric | Definition |
|---|---|
| Precision | matched main findings / all main findings, over all 28 cases. Gate findings count. Findings on clean cases count as false positives. |
| Recall | `must` entries hit by at least one main finding / all `must` entries (29) |
| Clean-case findings | main findings on the 8 clean cases (target 0) |
| Suspected | counted separately, never in precision |

Targets from the plan: precision ≥ 0.80, recall ≥ 0.70, and 0 findings on clean cases.

### 2.2 Martian

- Every main-section finding is paired with every golden comment of its PR. An LLM judge (`ARBITER_VERIFY_MODEL`) answers "Do these describe the same underlying issue?" with `{"match": true|false}`.
- **Core profile:** the categories are bug, security, concurrency, data, api, perf, test_gap and doc_defect. A finding that matches only a non-Core comment (style, speculative) is neutral: neither a true nor a false positive.
- Precision = TP / (TP + FP). Recall = Core comments matched / Core comments. F1 and F2 are the usual F-beta scores.
- **Differences from Martian's official protocol:**
  - Martian scores with three judges (Opus 4.5, GPT-5.2 and Sonnet 4.5) and reports each one. arbiter uses one judge, the omp default model.
  - Only 3 PRs per repo were run.
  - The numbers are therefore indicative, not comparable to the published leaderboard.

## 3. Results

### 3.1 Seeded corpus: summary

| Run | Briefs | Finder / verifier model | Main findings | Matched | Precision | Recall (must) | Clean-case findings | Block verdicts |
|---|---|---|---|---|---|---|---|---|
| r0 | as built | omp default (`anthropic/claude-opus-5-5`) | 55 | 22 | 0.40 | 0.83 (24/29) | 1 | 9 |
| r1 | revision 1 | same | 41 | 24 | 0.585 | 0.83 (24/29) | 0 | 12 |
| r2 | revision 2 (current) | same | 33 | 20 | 0.606 | 0.76 (22/29) | 0 | 10 |
| haiku | revision 2 | `anthropic/claude-haiku-5-5` / same | 29 | 20 | 0.69 | 0.62 (18/29) | 1 | 10 |

Effort was `standard` for every run, with 2–3 cases in parallel. Per case, r2 averaged 15.9 model calls and 176 s
of wall time; the Haiku run averaged 15.4 calls and 241 s.

What changed between runs:
- **r0 → r1** (commit `c1e4291`):
  - A1c no longer reports "no test covers X" for new code.
  - A6a no longer copies functional bugs as idiom findings.
  - A6b dropped small duplication and bug-shaped design points.
  - A6c no longer turns a doc that states the contract into a docs finding.
  - Core changes: retry of transient harness errors, and the fail-closed rule on more than 25% failed calls.
- **r1 → r2** (commit `76fa2f7`):
  - A1c: tests that miss a boundary are not broken tests.
  - A6a: no "use the stdlib" finding without a repo precedent.
  - A6c: no docs findings about failure modes of code that should not fail.
  - rustfmt gate findings carry a message.

### 3.2 Seeded corpus: per case

Each cell shows main findings / matched findings / must entries hit.

| Case | r0 | r1 | r2 | Haiku |
|---|---|---|---|---|
| go-01-binary-search-bound | 2/1/1-of-1 | 2/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 |
| go-02-err-shadowing | 4/1/1-of-1 | 4/1/1-of-1 | 2/0/0-of-1 | 3/1/1-of-1 |
| go-03-concurrent-map-writes | 1/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 |
| go-04-exec-shell-injection | 1/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 |
| go-05-idiom-stutter-getter | 2/1/1-of-3 | 1/1/1-of-3 | 1/1/1-of-3 | 1/1/1-of-3 |
| go-06-clean-rename | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 |
| go-07-clean-pure-fn | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 |
| python-01-pagination-off-by-one | 3/1/1-of-1 | 2/1/1-of-1 | 2/1/1-of-1 | 1/1/1-of-1 |
| python-02-mutable-default-swallow | 3/2/2-of-2 | 2/2/2-of-2 | 2/2/2-of-2 | 2/2/2-of-2 |
| python-03-sql-injection | 4/1/1-of-1 | 2/1/1-of-1 | 2/1/1-of-1 | 2/0/0-of-1 |
| python-04-async-task-sleep | 2/1/1-of-2 | 1/1/1-of-2 | 1/1/1-of-2 | 1/1/1-of-2 |
| python-05-singleton-generic-rangelen | 4/2/3-of-3 | 3/2/3-of-3 | 2/1/2-of-3 | 0/0/0-of-3 |
| python-06-clean-rename | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 |
| python-07-clean-pure-fn | 1/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 1/0/0-of-0 |
| rust-01-parse-unwrap | 3/1/1-of-1 | 3/1/1-of-1 | 2/1/1-of-1 | 2/1/1-of-1 |
| rust-02-sum-truncation | 3/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 |
| rust-03-mutex-across-await | 3/1/1-of-1 | 2/1/1-of-1 | 2/1/1-of-1 | 2/0/0-of-1 |
| rust-04-unchecked-index | 2/1/1-of-1 | 2/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 |
| rust-05-idiom-string-ref | 5/2/2-of-2 | 5/3/1-of-2 | 3/1/1-of-2 | 5/4/2-of-2 |
| rust-06-clean-rename | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 |
| rust-07-clean-pure-fn | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 |
| ts-01-foreach-async | 6/1/1-of-1 | 3/1/1-of-1 | 3/1/1-of-1 | 1/1/1-of-1 |
| ts-02-json-parse-cast | 2/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 |
| ts-03-innerhtml-xss | 2/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 | 1/1/1-of-1 |
| ts-04-date-range-boundary | 1/0/0-of-1 | 2/1/1-of-1 | 2/1/1-of-1 | 1/1/1-of-1 |
| ts-05-idiom-enum-any | 1/1/2-of-3 | 2/1/2-of-3 | 2/1/2-of-3 | 0/0/0-of-3 |
| ts-06-clean-rename | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 |
| ts-07-clean-pure-fn | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 | 0/0/0-of-0 |

### 3.3 Seeded corpus: what the 13 unmatched r2 findings were

| Kind | Count | Findings |
|---|---|---|
| Deterministic gate hits | 5 | staticcheck SA4006 and SA4017 on the shadowed `err` (go-02); rustfmt diffs in rust-01, rust-03 and rust-05 |
| Real defects on an axis the corpus does not list | 4 | missing `Cancelled` case as logic (ts-05); `Box<dyn Error>` as errors (rust-05); unequal list lengths in `register_all` as edge (python-05); `main` always reports "synced 0" as spec (ts-01) |
| Judgment findings | 4 | weak boundary tests (python-01, ts-04); unlogged 500 (python-03, observability); docstring disagreement (ts-01, docs) |

### 3.4 Martian sample (r2 briefs, omp default model, standard effort)

| Repo | PRs | Main findings | TP | FP | Core comments hit | Precision | Recall | F1 | F2 |
|---|---|---|---|---|---|---|---|---|---|
| sentry (Python) | 3 | 18 | 9 | 9 | 8/11 | 0.50 | 0.73 | 0.59 | 0.67 |
| grafana (Go) | 3 | 5 | 2 | 3 | 2/11 | 0.40 | 0.18 | 0.25 | 0.20 |
| cal.com (TS) | 3 | 20 | 5 | 15 | 3/10 | 0.25 | 0.30 | 0.27 | 0.29 |

Per PR, in `findings / TP / Core comments hit` form:

| PR | Result |
|---|---|
| sentry 1 | 5 / 4 / 3 of 4 |
| sentry 2 | 6 / 4 / 4 of 4 |
| sentry 3 | 7 / 1 / 1 of 3 |
| grafana 79265 | 4 / 1 / 1 of 5 |
| grafana 103633 | 1 / 1 / 1 of 3 |
| grafana 76186 | 0 / 0 / 0 of 3 |
| cal.com 8087 | 3 / 3 / 1 of 1 |
| cal.com 10600 | 5 / 1 / 1 of 4 |
| cal.com 10967 | 12 / 1 / 1 of 5 |

Things that limited these numbers:
- **Dependency fetch failed on all three real repos.**
  - sentry's `uv sync` fails with "Could not create temporary file". yarn and pnpm are not installed. grafana's frontend packages fail too.
  - Proofs that need imports or builds could therefore not run. grafana's `go build` HEAD-vs-base comparison was skipped by the rule in methodology §3.5.
- **Most sentry false positives are evolvability or spec findings** (docs, design, idiom, spec), which have no execution proof.
- **cal.com PR 10967 alone produced 12 findings with 1 TP.** It touches 5 units across calendar integrations.
- **The first Martian attempt hit the account's API rate limit.** All agents failed and the run reported PASS. That led to the fail-closed rule; the numbers above are from the rerun after the limit reset.

For reference, Martian publishes F2 Core of 47.7 for "Claude Code CLI" and 65.1 for the top tool, over the full
50 PRs with three judges `[AI-§3]`.

## 4. Verdict-level view (r2)

- Of the 15 functional bug cases, 10 ended with a BLOCK verdict.
- In 4 of the other 5, arbiter found and proved the bug, but the verifier panel rated it should-fix:
  - python-01: pagination off-by-one
  - python-02: mutable default and swallowed exception
  - rust-01: panic on bad port
  - rust-02: length truncation
- In the fifth, go-02, the true finding never reached the main section (see §5).
- No clean case blocked or produced a main finding.

## 5. Threats to validity

- **Tuned on the test set.** Briefs were revised twice using the same 28 cases they are scored on. r1 and r2 precision is optimistic. A held-out set is the first roadmap item.
- **Synthetic bugs are easier than real ones.** `[DV-S4]` reports F1 0.847 on synthetic bugs against 0.066 on real PRs. The seeded corpus measures plumbing and filtering, not real-world recall. The Martian sample is the real-world check, and it is small.
- **Axis matching is strict.** A real defect reported on an axis the corpus does not list counts as a false positive (4 of 13 in r2), so precision is a lower bound for "correct findings".
- **One judge, one sample.** Martian scoring used one LLM judge and 9 PRs.
- **The merge rule hid one true finding.** go-02 in r2 lost its true finding because of the location-merge rule.
  - A3 reported a security finding 2 lines from the shadowed `err` and became the representative. The panel disputed it, and the merged finding went to "Suspected".
  - The rule picks the highest-priority axis, not the best-supported claim. Fixing it is a Python-plan item.
- **Non-determinism.** Every run was done once; variance across runs was not measured.
- **No token counts.** Cost is approximated by model calls and wall time.

## 6. Raw results

The result files are in `eval/results/`, which git ignores, so they exist only on the machine that ran them.

| File | Run |
|---|---|
| `seeded-20261121045059.json` | r0 |
| `seeded-20261121073701.json` | r1 |
| `seeded-20261121082622.json` | r2 |
| `seeded-20261121090807.json` | Haiku |
| `martian-sentry-20261121083041.json` | sentry |
| `martian-grafana-20261121092410.json` | grafana |
| `martian-cal_dot_com-*` | cal.com; the latest file is the rerun |
| `eval/results/runs/<timestamp>/<case>/` and `eval/results/martian/<timestamp>/<pr>/` | every RUN directory: plan, prompts, votes, proofs, exec records, `report.md` |

Reproduce with:

```bash
uv run arbiter eval seeded build && uv run arbiter eval seeded run --effort standard
uv run arbiter eval martian fetch && uv run arbiter eval martian run --repo sentry --limit 3
```
