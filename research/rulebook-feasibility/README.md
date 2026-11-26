Feasibility check, 2026-11-26: can the owner's Python rulebook (pattern + × incorrect + ✓ correct examples) become
scanners that find every occurrence, with a model for rules no scanner can express, and every rule traversed into
the verdict? Four sample OOP rules were built and run; the owner's own rules replace them when they arrive.

# Rulebook feasibility

## 1. Verdict

**Feasible, with one split the owner should accept:** a scanner guarantees that every occurrence *of the pattern
as written* is found, not that every hit is a violation. Recall comes from the scanner; precision comes from
curating ✓ examples and, where that is not enough, a model triage of each hit. Semantic rules have no recall
guarantee, only a traversal guarantee (every symbol was examined, checked against an `ast` symbol list).

| Question | Answer | Evidence (§3) |
|---|---|---|
| Can × / ✓ pairs become a scanner? | yes, for syntactic and structural rules; semgrep or stdlib `ast`, both already available to arbiter | OOP-01..03 replay PASS |
| Does a scanner beat grep/regex? | yes, by a wide margin | accessor regex: 805 hits, 59 real accessors (7%); semgrep: 70 hits, all accessors by construction |
| Does "scan everything" hold? | only if the runner enforces it: semgrep silently skipped 6 of 3,819 sentry files (`build/` default ignore) | fixed by explicit targets; runner asserts scanned = targets |
| Are scanner hits violations? | not always: the pattern is exact, the judgement is not | OOP-02: 111 type switches, sample includes exception translation; OOP-03: 33 hits, 2 of 3 sampled are false (subclassed base, stateful registry) |
| Can a model check a semantic rule? | yes on curated examples, noisier on real code | OOP-04: 2/2 hits and 0 false on the examples, twice; 1 hit on 2 real files, judged a false positive |
| Can traversal be proven? | yes: scanner runs are counted per file; the model returns `checked_symbols`, compared with `ast` | 4/4 symbols on both real files |
| Cost | scanners: about 5 s per rule over all 3,819 sentry files; semantic: one model call per rule per changed file | §3 |

## 2. Design that follows

| Tier | Use when | Recall | Precision |
|---|---|---|---|
| `semgrep` | syntactic pattern | every occurrence in every file (runner-enforced) | exact for the pattern; curate ✓ cases |
| `ast` | counting or structure (methods per class, `__init__` contents), cross-file facts (is the class subclassed) | same, for parseable files; unparsable files reported, never skipped silently | as above |
| `semantic` | judgement (responsibility, feature envy) | not guaranteed; mitigated by per-symbol listing and repeated passes | model + ✓ examples |
| triage (optional, per rule) | a deterministic rule whose hits need judgement | unchanged: the model only judges each hit, it cannot drop the hit from the ledger | raised; dismissals recorded with a reason |

Rule format and curation loop: [rulebook/README.md](../../rulebook/README.md). Curation check:
`python rulebook/replay.py [RULES_DIR]` (every `# expect:` line hit, `good.py` silent, every target scanned).

Traversal contract for the review run (not built): rule × changed Python file → `violation` / `clean` / `not run
(reason)`; violations go to the report under the verdict, `not run` counts into "what arbiter could not verify";
a rule's severity sets whether it can block (`[block]`-style flag in `rule.md`).

## 3. What was run

Samples in `rules/`: OOP-01 accessor methods (semgrep), OOP-02 `isinstance` type switch (semgrep), OOP-03 class
that should be a function (`ast`), OOP-04 feature envy (semantic). Corpus: Martian sentry checkout,
`eval/martian/cache/sentry/src`, 3,819 Python files. Semgrep 1.186.0 from arbiter's tool cache.

| Run | Result |
|---|---|
| Replay on own examples (`rulebook/replay.py research/rulebook-feasibility/rules`) | OOP-01 4/4, OOP-02 2/2, OOP-03 2/2, all with 0 false hits on `good.py` |
| Replay caught a rule bug | first OOP-02 reported a 3-branch `elif` chain twice (the tail re-matches as a nested `if`); fixed in the runner by keeping the outermost match; `pattern-not-inside` cannot do it (a match is inside itself) |
| Semgrep coverage, directory target | 3,813 / 3,819 scanned; the 6 skipped are `src/sentry/build/*.py` (semgrep's default ignore), no warning |
| Semgrep coverage, explicit targets, `--timeout 0 --max-target-bytes 0` | 3,819 / 3,819, 0 errors |
| OOP-01 on sentry | 70 hits (60 getters, 8 setters, 2 decorated getters) in about 5 s |
| Regex `def get_\w+\(self\)` on sentry | 805 hits; 59 are accessors; it also missed 1 accessor whose `def` spans lines |
| OOP-02 on sentry | 165 raw, 111 after nesting dedupe, about 4.5 s |
| OOP-03 on sentry | 33 hits, about 3 s; sampled 3: `AnalyzeQuery` plausible, `DiscordMessageComponent` false (a base class with subclasses), `_FactoryRegistry` false (stateful) → rule needs a cross-file "is subclassed" fact and a "method mutates state" exclusion |
| OOP-04 model probe (`semantic_check.sh`, Sonnet, thinking high, 1 call per file) | examples: bad 2/2 and good 0, identical over 2 runs; sentry `status_change_consumer.py`: 0 hits; `project_stacktrace_link.py`: 1 hit (`set_tags` reading a TypedDict for telemetry: a false positive by the rule's own "serialisers are fine" note); `checked_symbols` matched the `ast` symbol list 4/4 on both |

Raw model outputs: `results/`.

## 4. Risks

| Risk | Mitigation |
|---|---|
| A rule written too broadly floods the report (OOP-02: 111 hits on sentry) | review scope is the diff, not the repo; curate ✓ cases; optional triage tier; per-rule cap with a count, never a silent cut |
| Silent skips by the scanner | explicit targets, no size/time limits, assert scanned = targets, unparsable files listed |
| Model recall on semantic rules is unmeasured | seeded cases per semantic rule; measure over repeated runs before trusting a clean result |
| Rules generalised from one × / ✓ pair over-fit | every image's pair becomes the first case, then variants; real-code misses and false hits are added as cases |
| Rulebook as untrusted text in prompts | rules are the owner's and live in this repo; load the base version during a review (ledger R-00) |

## 5. Not checked

- Precision on sentry is from samples of 3, not a labelled set.
- The semantic probe is 6 calls on one rule; no recall figure.
- arbiter's existing semgrep gate passes explicit files but keeps semgrep's default 5 s timeout and 1 MB limit
  without asserting the scanned count (`arbiter/tools.py` `_semgrep`).
