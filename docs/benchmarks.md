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

### 1.3 SWR-Bench

- Source: `ZZR0/SWRench`, MIT licence, pinned at commit `67ae1d4`. It has 1,000 real Python PRs from 12 SWE-bench repositories.
- 500 of the PRs contain issues that reviewers confirmed during the real review; the other 500 merged clean.
- **Ground truth.** Each issue PR lists its `changes`, each with:
  - a type: functional `F.1`–`F.6` (interface, logic, resource, check, support, larger defects) or evolvability `E.*`
  - the commit that introduced it
  - a summary of the reviewer discussion
- **What arbiter reviews.** Upstream's `build_dataset.py` takes the parent of the first PR commit as the base and the last pre-review PR commit as the head; arbiter does the same, so it sees the PR as the reviewers first saw it.
- **Sample** ([`eval/swr/sample.json`](../eval/swr/sample.json)): 28 issue PRs with at least one functional change and 12 clean PRs, all with diffs of at most 300 lines. They are stratified over the 12 repositories with seed 20261122. 267 issue PRs and 461 clean PRs were eligible.
- **Scoring.** The official judge prompts and answer parsers are loaded from `swrbench/evaluation_struct.py` at the pinned commit. arbiter's main findings are rendered as a plain review and judged per PR.
  - Issue PRs: true positives are review points that hit a ground-truth change. Precision, recall and F1 are pooled over PRs, as upstream's `*_total` metrics are.
  - Clean PRs: the score is whether the review is judged "good" and how many points it raises.
  - The judge is a model call through arbiter's harness, not upstream's `run_chat`.

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

### 3.5 Martian sentry, all 10 PRs (r2 briefs, omp default model = Opus)

The run of PRs 4–10 (`--offset 3`) hit the API rate limit on 3 of them: getsentry/sentry 80528, 95633 and 80168.
Those 3 exited 5 with the verdict withheld, and are excluded from the score.

| PRs scored | Main findings | TP | FP | Core comments hit | Precision | Recall | F1 | F2 |
|---|---|---|---|---|---|---|---|---|
| 3 (PRs 1–3) | 18 | 9 | 9 | 8/11 | 0.50 | 0.73 | 0.59 | 0.67 |
| 4 (PRs 4–7) | 10 | 3 | 7 | 4/16 | 0.30 | 0.25 | 0.27 | 0.26 |
| **7 of 10 (pooled)** | 28 | 12 | 16 | 12/27 | **0.43** | **0.44** | **0.44** | **0.44** |

Per PR (findings / TP / Core comments hit):

| PR | Result |
|---|---|
| getsentry/sentry 67876 | 2 / 1 / 1 of 3 |
| sentry-greptile 5 | 5 / 1 / 1 of 6 |
| getsentry/sentry 93824 | 3 / 1 / 2 of 5 |
| getsentry/sentry 77754 | 0 / 0 / 0 of 2 |

### 3.6 SWR-Bench, partial (r2 briefs, omp default model = Opus)

The rate limit stopped this run too. Of the 40 sampled PRs, 27 exited 5 because every agent call failed, and the
judge failed on 1 more. Only 12 PRs were scored: the first 12 issue PRs in sample order, one from each repository.
None of the clean PRs was scored, so false alarms on clean code are still unmeasured.

| PRs scored | Precision | Recall | F1 | Functional-change recall | Blocked |
|---|---|---|---|---|---|
| 12 issue PRs | 0.58 (7 TP, 5 FP) | 0.37 (7 of 19 changes) | 0.45 | 0.50 | 4 of 12 |

- In 6 of the 12 PRs arbiter reported nothing. The judge rated those reviews "LGTM" and counted every ground-truth change as missed.
- SWR-Bench's paper reports a best F1 of 18.73% for the strongest tool `[AX-S7]`, but over all 1,000 PRs, clean ones included. Twelve issue-only PRs are not comparable to that.
- **Cost.** These Martian and SWR runs used the omp default model, Opus, for every role, and drained the account's token budget. From now on, finders run on Haiku and the verifier, proof agent and judge on Sonnet, and Opus is refused (methodology §3.7). The 2026-11-23 matrix (§3.7) reran Python and TypeScript under that rule.

### 3.7 Model matrix, Python and TypeScript (2026-11-23, r2 briefs, standard effort, `ocr` units)

Two setups, same briefs and datasets:
- **H+S:** Haiku 5.5 finders; Sonnet 5.5 verifier, proof agent and judge (the defaults).
- **S+S:** Sonnet 5.5 for every role (`--model anthropic/claude-sonnet-5-5`).

Go and Rust (grafana, seeded go/rust) were postponed by the user. `ARBITER_JOBS=4`, seeded and SWR at `--parallel 2`. Every PR and case was scored; none failed or was rate-limited. The H+S SWR row pools 28 PRs scored on 2026-11-23 03:13 with the 12 rerun in the matrix (`--skip-scored`); the S+S row ran all 40.

| Dataset | Setup | Precision | Recall | F1 | F2 | Detail |
|---|---|---|---|---|---|---|
| Seeded Python+TS, 14 cases | H+S | **0.56** | 0.69 | **0.61** | 0.66 | 8 FP; 11/16 must-find; 4 bug cases blocked; 0 clean-case findings; 45 min of review wall time |
| Seeded Python+TS, 14 cases | S+S | 0.48 | **0.81** | 0.60 | **0.71** | 12 FP; 13/16 must-find; 4 bug cases blocked; 0 clean-case findings; 69 min |
| Martian sentry, 10 PRs | H+S | **0.31** | 0.36 | 0.34 | 0.35 | TP 10, FP 22, Core 12/33 |
| Martian sentry, 10 PRs | S+S | 0.29 | **0.42** | 0.34 | **0.39** | TP 15, FP 37, Core 14/33 |
| Martian cal.com, 10 PRs | H+S | **0.42** | 0.43 | **0.43** | 0.43 | TP 19, FP 26, Core 16/37 |
| Martian cal.com, 10 PRs | S+S | 0.36 | **0.51** | 0.42 | **0.47** | TP 22, FP 39, Core 19/37 |
| SWR-Bench, 40 PRs (28 issue, 12 clean) | H+S | **0.67** | **0.26** | **0.38** | **0.30** | TP 12, FP 6, FN 34; 5/28 issue PRs blocked; functional recall 11/33; clean judged good 12/12, 0 blocked |
| SWR-Bench, 40 PRs (28 issue, 12 clean) | S+S | 0.38 | 0.24 | 0.29 | 0.26 | TP 11, FP 18, FN 35; 4/28 issue PRs blocked; functional recall 11/33; clean judged good 12/12, 0 blocked |

- **Sonnet finders buy recall with precision.** On seeded and Martian, S+S gains 6–12 points of recall and loses 2–8 points of precision. F1 ties within 0.01, and F2 favours S+S by 4–5 points.
- **On SWR-Bench, Sonnet finders lose on every metric.** S+S raised 3× the false positives of H+S (18 against 6), with one fewer true positive and the same functional recall. SWR is the largest and most realistic sample here.
- **Clean code stays clean in both setups.** There were no findings on clean seeded cases, and no clean SWR PR was blocked.
- **Haiku against Opus.** The Opus-era rows above (§3.4–§3.6) were partial and rate-limited, so they are not a like-for-like baseline. On Martian sentry, H+S over 10 PRs (F2 0.35) sits below Opus over 7 (F2 0.44). On cal.com, H+S over 10 PRs (F2 0.43) beats Opus over 3 (F2 0.29).
- **Against the Martian tools on the same 20 PRs.** Martian publishes every tool's judged reviews (`offline/results/<judge>/evaluations.json` at the pinned commit). The table re-scores 49 tools with arbiter's Core rule on the 10 sentry and 10 cal.com PRs arbiter ran: a match to a non-Core comment is neutral, and every unmatched candidate is a false positive. Martian's Sonnet 4.5 judge results are used; arbiter's own judge is Sonnet 5.5.

  | Rank of 51 | Tool | Precision | Recall | F2 (Core, 20 PRs) |
  |---|---|---|---|---|
  | 1 | Augment | 0.53 | 0.69 | 0.65 |
  | 2 | Qodo v2 | 0.55 | 0.63 | 0.61 |
  | 8 | CodeRabbit | 0.34 | 0.61 | 0.53 |
  | 14 | Bugbot | 0.57 | 0.44 | 0.46 |
  | 15 | **arbiter S+S** | 0.33 | 0.47 | **0.43** |
  | 16 | Claude Code | 0.40 | 0.41 | 0.41 |
  | 18 | **arbiter H+S** | 0.38 | 0.40 | **0.40** |
  | 28 | Claude (plain) | 0.43 | 0.33 | 0.34 |
  | — | mean of the 49 tools | | | 0.34 (median 0.35) |

  Caveats:
  - The tools ran months earlier, on older models, and were scored by a different judge.
  - For 22 older tool versions, between 1 and 10 of their matched golden comments use wording older than the pinned golden set. Those matches could not be categorised and are not counted, so those tools are slightly understated.
  - Twenty PRs give each F2 an uncertainty of several points.
- **Where H+S loses recall on those 20 PRs.** One Sonnet call per PR mapped each of the 70 Core golden comments to arbiter's raw finder output (`raw.json`). Each match was then traced through validation, the verifier panel and placement. 40 of the 70 comments were caught by at least 3 of the top 4 tools (Augment, Qodo v2, cubic v2, Qodo extended v2); this "consensus" set excludes contested goldens.

  | Stage where the comment was lost | All 70 | Consensus 40 |
  |---|---|---|
  | Reported in the main section (hit) | 28 | 20 |
  | Never raised by any finder | 32 | 12 |
  | Raised, rejected by validation (2 had empty `evidence_lines`, 1 was outside the unit's hunks ±3) | 3 | 2 |
  | Raised, dropped by the verifier panel as a false positive | 5 | 4 |
  | Raised, verified TRUE_POSITIVE, but placed in Suspected for lack of an execution proof | 2 | 2 |

  - **Finders account for most of the gap.** Of the 20 missed consensus comments, 12 were never raised. Several are cross-file contract breaks, such as an interface signature change whose implementations were not updated, or a wrong argument passed to a helper. The `hier` contract pass targets that kind of bug.
  - **The rest were found and then thrown away.** The other 8 were raised by a finder and lost after it.
    - **Suspected placement.** The 2 verified-but-unproven findings are both High golden bugs. They were the only findings placed that way in the 20 PRs, so promoting them costs no precision. Dependency fetch fails on sentry, so no proof could run.
    - **Verifier drops.** The panel dropped 62 findings in all, 5 of them true. Its reasons argue the trigger is unreachable. Overall it is right about 90% of the time, so loosening it wholesale would cost precision.
  - **By severity**, H+S caught 3/3 Critical, 13/28 High, 8/25 Medium and 4/14 Low. Augment caught 23/28 High and 16/25 Medium, with 4.7 comments per PR against arbiter's 3.9.
- **Decision.** H+S stays the default (ledger M-02). Sonnet finders cost Sonnet prices for a recall gain seen only on the two smaller sets. They cost precision everywhere, and lose outright on SWR-Bench.

Commands (from the repo root):

```sh
arbiter eval seeded run --lang python,ts --parallel 2 [--model anthropic/claude-sonnet-5-5]
arbiter eval martian run --repo sentry|cal_dot_com [--model anthropic/claude-sonnet-5-5]
arbiter eval swr run --parallel 2 [--skip-scored eval/scores/swr-20261123031300.json] [--model anthropic/claude-sonnet-5-5]
```

Each run was done once, and run-to-run variance was not measured (§5). Differences of a few points between setups may be noise; the SWR precision gap (0.67 against 0.38) is the only large one.

### 3.8 Wave 1 spot check (2026-11-24)

Old arm: master `8f04917`, run through `--review-from ~/relic/arbiter`. That checkout predates PRs #3 and #4. #4 is docs only, and #3 adds the `hier` mode behind a switch and claims `ocr` merging is unchanged byte for byte (methodology §4), so on `ocr` units the old arm should behave like wave 1's base; this was not measured separately. New arm: wave 1 code, identical to PR #5's `5ef1788` under `arbiter/` and `skills/` (T-12, T-13 + T-18, MA-03 facts, A6d, MA-05), before the review fixes. Both arms ran on the same day with Haiku finders, a Sonnet verifier and judge, `standard` effort and `ocr` units. One extra arm ran the new code with `--decompose hier` on the AACR item only.

Single runs on 3 items: a direction check, not an accuracy claim (E-11).

| Item | Arm | Main findings | Precision | Recall | F2 | Maintainability recall | Evolvability findings | Verdict | Model calls (agents + verifier) | Wall |
|---|---|---|---|---|---|---|---|---|---|---|
| AACR ComfyUI 9560 (Python) | old | 0 | 0.00 | 0/6 | 0.00 | 0/3 | 0 | pass | 23 + 0 | 168 s |
| AACR ComfyUI 9560 | new | 2 | 0.00 | 0/6 | 0.00 | 0/3 | 1 | pass | 25 + 9 | 193 s |
| AACR ComfyUI 9560 | new + `hier` | 3 | 0.33 | 1/6 | 0.19 | 1/3 | 1 | pass | 37 + 15 | 384 s |
| Martian sentry-greptile 3 (worst) | old | 6 | 0.00 | 0/3 Core | 0.00 | no `style` goldens | 1 | pass | 47 + 33 | 650 s |
| Martian sentry-greptile 3 | new | 4 | 0.00 | 0/3 Core | 0.00 | no `style` goldens | 1 | pass | 51 + 36 | 509 s |
| Martian cal.com 8330 (best) | old | 3 | 0.33 | 1/2 Core | 0.45 | no `style` goldens | 0 | block | 12 + 12 | 424 s |
| Martian cal.com 8330 | new | 3 | 0.33 | 1/2 Core | 0.45 | no `style` goldens | 1 | pass | 13 + 15 | 775 s |

AACR precision and recall use AACR's file-level semantic coverage (one judge call per finding, a reference counted once); Martian uses the Core profile. Model calls exclude the judge and proof agents.

**Item choice.** The last H+S run's best PR was cal.com 8330 (F2 0.91, Core 2/2), and its worst was sentry-greptile 3 (F2 0, Core 0/3, 5 FP). The AACR item is ComfyUI 9560: Python, 319 changed lines, 3 Code Defect and 3 Maintainability and Readability references. Best and worst items regress toward the mean on any rerun, so the old arm reran both Martian PRs on the same day; today cal.com 8330 scored 1/2 in both arms. The `hier` arm ran on the AACR item only, because it is the only item large enough to split.

**What changed.**
- No Core or AACR recall was lost on any item; recall is identical across the two `ocr` arms.
- Maintainability: arbiter measured 2 facts on ComfyUI. `server.py` crossed 1,000 lines (985 → 1005, block-eligible), and `cache_control` complexity rose from 4 to 11. A6d reported the complexity fact as a nit in both new arms and matched no reference; no agent cited the file fact, so nothing blocked. The 3 maintainability references ask to exclude 304 responses from the image rule, merge branches that set identical headers, and unify duplicate `no-cache` assignments (lines 60–72). Only the `hier` arm covered one of them (1/3).
- T-13 repaired one finding's empty `evidence_lines` in each new AACR run. No finding was relocated by `quote` (T-18). T-12 placed nothing: dependency fetch failed on sentry and cal.com, but no verified finding there was left without a proof (0 Suspected in both new runs).
- sentry-greptile 3: 4 instead of 6 false positives; both arms still miss all 3 Core bugs.
- cal.com 8330: both arms proved a logic finding on the same golden bug. The old arm's panel kept it at block, while the new arm's panel rated it should-fix, so the verdicts differ (block vs pass). Neither wave 1 nor #3 changes functional severity, so this is run-to-run variance in the panel.
- Cost: the new arm spends 1–4 more agent calls per run (A6d), plus verifier calls on the extra findings.

#### Three AACR samples, old vs new (2026-11-24)

Two more Python AACR items ran later the same day, same models, effort and `ocr` units: ComfyUI 7952 (323 lines; 4 Code Defect, 1 Maintainability and Readability) and ragflow 7151 (207 lines; 6 Code Defect, 2 Security Vulnerability, 1 Maintainability and Readability). Both have more than 150 changed lines and a maintainability reference. With ComfyUI 9560 from the table above, that makes 3 AACR samples. The new arm is the pre-review wave 1 code, as above.

| Item | Arm | Main findings | Matched (new refs) | Defect + security covered | Maintainability covered | Verdict | Model calls | Wall |
|---|---|---|---|---|---|---|---|---|
| ComfyUI 9560 | old | 0 | 0 | 0/3 | 0/3 | pass | 23 + 0 | 168 s |
| ComfyUI 9560 | new | 2 | 0 | 0/3 | 0/3 | pass | 25 + 9 | 193 s |
| ComfyUI 7952 | old | 5 | 2 | 1/4 | 1/1 | pass | 20 + 15 | 350 s |
| ComfyUI 7952 | new | 6 | 3 | 2/4 | 1/1 | pass | 22 + 21 | 328 s |
| ragflow 7151 | old | 7 | 1 | 0/8 | 1/1 | pass | 12 + 12 | 279 s |
| ragflow 7151 | new | 9 | 1 | 0/8 | 1/1 | **block** | 13 + 18 | 337 s |
| **Total** | **old** | 12 | 3 | **1/15** | **2/5** | | 55 + 27 | 797 s |
| **Total** | **new** | 17 | 4 | **2/15** | **2/5** | | 60 + 48 | 858 s |

| Over the 3 samples (AACR metric) | Old | New |
|---|---|---|
| Precision (findings covering a new reference / findings) | 3/12 = 0.25 | 4/17 = 0.24 |
| Recall (references covered) | 3/20 = 0.15 | 4/20 = 0.20 |
| F1 / F2 | 0.19 / 0.16 | 0.22 / 0.21 |
| Functional (defect + security) recall | 1/15 | 2/15 |
| Maintainability recall | 2/5 | 2/5 |
| Model calls (agents + verifier) | 82 | 108 (+32%) |

- **Recall up by one reference.** On ComfyUI 7952, the new arm's A1a also found that `RegexExtract` "All Matches" returns capture-group contents instead of full matches (reference at line 275). Both arms reported the `None` optional-group bug at line 297. Per category, the new arm covered at least as many references as the old one on every item.
- **Precision flat.** 5 more findings, 1 more match. On ragflow both arms report ruff hits and maintainability findings that no reference names.
- **ragflow 7151 blocks under the new policy (MA-05).** arbiter measured `InfinityConnection.update` complexity rising from 11 to 22, across the block line of 20. A6a and A6d both reported it with `measure: m03`, so it blocked. This is the user's blocking rule working as designed. The AACR references do not mention it, so it counts as an unmatched finding.
- **Maintainability recall is the same, 2/5.** Both covered references were found by checks that predate wave 1, in both arms: A6b's unused `normalize_path` (ComfyUI 7952) and the ruff gate's SIM201 on `not res.total == 0` (ragflow 7151). The facts and A6d added findings, but none of them matched a reference.
- Cost: 32% more agent and verifier calls, and 8% more wall time.
- Three items, one run each: this is a direction check (E-11). A difference of one reference is within run-to-run noise.

#### Three most complex Python AACR PRs, old vs new (2026-11-24)

These are the largest Python AACR PRs not yet run, by changed lines: ComfyUI 8446 (971 lines; 13 Code Defect, 1 Performance, 4 Maintainability and Readability), langflow 6044 (882; 9 Code Defect) and langflow 6652 (387; 5 Code Defect). The old arm is master `8f04917`, as above. The new arm is PR #5's head `0bc9487`, which includes the review fixes. Same models, `standard` effort, `ocr` units, one run each.

| Item | Arm | Main findings | Matched (new refs) | Defect + perf covered | Maintainability covered | Verdict | Model calls | Wall |
|---|---|---|---|---|---|---|---|---|
| ComfyUI 8446 | old | 12 | 5 | 5/14 | 0/4 | pass | 41 + 54 | 1409 s |
| ComfyUI 8446 | new | 14 | 5 | 5/14 | 0/4 | pass | 45 + 66 | 1383 s |
| langflow 6044 | old | 9 | 1 | 1/9 | — | block | 61 + 27 | 2263 s |
| langflow 6044 | new | 11 | 1 | 1/9 | — | block | 67 + 48 | 1574 s |
| langflow 6652 | old | 1 | 0 | 0/5 | — | pass | 29 + 9 | 1204 s |
| langflow 6652 | new | 3 | 3 | 3/5 | — | pass | 32 + 15 | 425 s |
| **Total** | **old** | 22 | 6 | **6/28** | **0/4** | | 221 | 4876 s |
| **Total** | **new** | 28 | 9 | **9/28** | **0/4** | | 273 (+24%) | 3382 s |

| Over the 3 complex PRs (AACR metric) | Old | New |
|---|---|---|
| Precision | 6/22 = 0.27 | 9/28 = 0.32 |
| Recall | 6/32 = 0.19 | 9/32 = 0.28 |
| F1 / F2 | 0.22 / 0.20 | 0.30 / 0.29 |

- **The whole gain comes from langflow 6652, and it is not a wave-1 effect.** None of the 3 matched findings went through a wave-1 mechanism: no facts were measured, A6d found nothing, nothing was relocated, and T-12 placed nothing. T-13 repaired one candidate (an A6b/A6c duplicate-helper finding), but the panel dropped it. The new run's finders simply raised 7 raw candidates instead of 4. A1a and A1b proved an E4 logic bug (`_clean_args` rejects inputs before the `stringify` check), and A6c and SPEC added two more findings; all 3 matched references. These agents and briefs are unchanged by wave 1, apart from one preamble sentence asking for `quote`. Treat this as run-to-run finder variance.
- **ComfyUI 8446 and langflow 6044: identical coverage.** The new arm added 2 findings on each, none matched.
- **Maintainability 0/4 in both arms.** A6d reported 4 findings on ComfyUI 8446: dead `tucker_weight`, `plot_loss` length, `TrainLoraNode.train` complexity 26 and `load_and_process_images` complexity 12. The 4 references ask for a consistent residual-add style, matching tensor shapes between two helpers, no hardcoded tuple indexing, and removing commented-out debug code. A6d's `tucker_weight` finding sits on a referenced line (`base.py:133`) but raises a different concern.
- **The blocking rule did not fire.** Block-eligible facts were measured: `TrainLoraNode.train` (new, complexity 26, nesting 7, 164 lines) and langflow `_serialize_dispatcher` (new, complexity 33). A6d reported both but rated them should-fix, so they did not block. langflow 6044 blocked in both arms on the same mypy gate errors in its tests.
- Cost: 24% more model calls. Wall time was lower for the new arm (3382 s vs 4876 s), driven by langflow run-to-run variance.

**All 6 AACR samples so far (both comparisons):**

| | Old | New |
|---|---|---|
| Precision | 9/34 = 0.26 | 13/45 = 0.29 |
| Recall | 9/52 = 0.17 | 13/52 = 0.25 |
| F2 | 0.19 | 0.26 |
| Defect + security + perf recall | 7/43 | 11/43 |
| Maintainability recall | 2/9 | 2/9 |
| Model calls | 303 | 381 (+26%) |

Of the 4 extra references the new arm covered, 3 came from langflow 6652's finder variance and 1 from ComfyUI 7952. None came from a wave-1 mechanism. Wave 1 has not been shown to raise recall; it has been shown not to lower it, and it costs about a quarter more model calls.

Wave-1 acceptance (roadmap Phase A): "no Core recall loss" holds on all 8 items (6 AACR, 2 Martian). "Maintainability recall up on AACR" does not hold with `ocr` units (2/9 → 2/9); only the single `hier` run on ComfyUI 9560 raised it (0/3 → 1/3).

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

## 6. Result files

The score files for every run reported here are tracked in git under [`eval/scores/`](../eval/scores/). Each holds
the summary (precision, recall, model, effort) and one row per case or PR. For seeded runs, each row also lists the
unmatched findings.

| File | Run |
|---|---|
| [`seeded-20261121045059.json`](../eval/scores/seeded-20261121045059.json) | seeded r0 |
| [`seeded-20261121073701.json`](../eval/scores/seeded-20261121073701.json) | seeded r1 |
| [`seeded-20261121082622.json`](../eval/scores/seeded-20261121082622.json) | seeded r2 (current briefs) |
| [`seeded-20261121090807.json`](../eval/scores/seeded-20261121090807.json) | seeded, Haiku |
| [`martian-sentry-20261121083041.json`](../eval/scores/martian-sentry-20261121083041.json) | Martian sentry |
| [`martian-grafana-20261121092410.json`](../eval/scores/martian-grafana-20261121092410.json) | Martian grafana |
| [`martian-cal_dot_com-20261121171127.json`](../eval/scores/martian-cal_dot_com-20261121171127.json) | Martian cal.com, rerun after the rate limit reset |
| [`martian-sentry-20261122152534.json`](../eval/scores/martian-sentry-20261122152534.json) | Martian sentry PRs 4–10 (4 scored, 3 rate-limited) |
| [`swr-20261122154039.json`](../eval/scores/swr-20261122154039.json) | SWR-Bench, partial (12 of 40 scored) |
| [`seeded-20261123142051.json`](../eval/scores/seeded-20261123142051.json) | Matrix H+S, seeded Python+TS |
| [`seeded-20261123192323.json`](../eval/scores/seeded-20261123192323.json) | Matrix S+S, seeded Python+TS |
| [`martian-sentry-20261123142140.json`](../eval/scores/martian-sentry-20261123142140.json) | Matrix H+S, Martian sentry |
| [`martian-sentry-20261123192349.json`](../eval/scores/martian-sentry-20261123192349.json) | Matrix S+S, Martian sentry |
| [`martian-cal_dot_com-20261123162336.json`](../eval/scores/martian-cal_dot_com-20261123162336.json) | Matrix H+S, Martian cal.com |
| [`martian-cal_dot_com-20261123233602.json`](../eval/scores/martian-cal_dot_com-20261123233602.json) | Matrix S+S, Martian cal.com |
| [`swr-20261123031300.json`](../eval/scores/swr-20261123031300.json) | Matrix H+S, SWR-Bench, first 28 of 40 |
| [`swr-20261123144505.json`](../eval/scores/swr-20261123144505.json) | Matrix H+S, SWR-Bench, remaining 12 |
| [`swr-20261123195901.json`](../eval/scores/swr-20261123195901.json) | Matrix S+S, SWR-Bench, all 40 |
| [`aacr-20261124033739.json`](../eval/scores/aacr-20261124033739.json) | Wave 1 spot check, old arm, AACR ComfyUI 9560 |
| [`aacr-20261124040208.json`](../eval/scores/aacr-20261124040208.json) | Wave 1 spot check, new arm, AACR ComfyUI 9560 |
| [`aacr-20261124042829.json`](../eval/scores/aacr-20261124042829.json) | Wave 1 spot check, new arm with `hier`, AACR ComfyUI 9560 |
| [`aacr-20261124102355.json`](../eval/scores/aacr-20261124102355.json) | Wave 1, old arm, AACR ComfyUI 7952 and ragflow 7151 |
| [`aacr-20261124103609.json`](../eval/scores/aacr-20261124103609.json) | Wave 1, new arm, AACR ComfyUI 7952 and ragflow 7151 |
| [`aacr-20261124122426.json`](../eval/scores/aacr-20261124122426.json) | Wave 1, old arm, AACR ComfyUI 8446, langflow 6044 and 6652 |
| [`aacr-20261124134825.json`](../eval/scores/aacr-20261124134825.json) | Wave 1, new arm (with review fixes), AACR ComfyUI 8446, langflow 6044 and 6652 |
| [`martian-sentry-20261124034041.json`](../eval/scores/martian-sentry-20261124034041.json) | Wave 1 spot check, old arm, sentry-greptile 3 |
| [`martian-sentry-20261124040537.json`](../eval/scores/martian-sentry-20261124040537.json) | Wave 1 spot check, new arm, sentry-greptile 3 |
| [`martian-cal_dot_com-20261124035405.json`](../eval/scores/martian-cal_dot_com-20261124035405.json) | Wave 1 spot check, old arm, cal.com 8330 |
| [`martian-cal_dot_com-20261124041504.json`](../eval/scores/martian-cal_dot_com-20261124041504.json) | Wave 1 spot check, new arm, cal.com 8330 |

Four earlier Martian files are not tracked: one per repo, plus a second for cal.com. The API rate limit made agents fail in all four, and the reruns above replace them.

Every review's full RUN directory (plan, prompts, votes, proofs, exec records, `report.md`) stays in
`eval/results/runs/<timestamp>/<case>/` and `eval/results/martian/<timestamp>/<pr>/`. Git ignores these because
they are large, so they exist only on the machine that ran them. `arbiter eval` writes new score files to
`eval/results/`; copy them into `eval/scores/` when they are reported.

Reproduce with:

```bash
uv run arbiter eval seeded build && uv run arbiter eval seeded run --effort standard
uv run arbiter eval martian fetch && uv run arbiter eval martian run --repo sentry --limit 3
```
