# Changelog

All notable changes to arbiter are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

Every entry carries an **Approach** line: the approach that was tried and the evidence or result that led to it.
Scores and their caveats are in [docs/benchmarks.md](docs/benchmarks.md); decisions and deviations in
[docs/methodology.md](docs/methodology.md) §4–§5.

## [Unreleased]

Hierarchical, syntax-aware review units, from `research/research-decompose-hierarchical.md` (`[DH-]` keys).

**Hypothesis.** On large Python PRs, OCR-style units cannot split a single-hunk file: 11 Martian sentry units
exceed the 150-churn budget, up to 421, while no seeded or SWR-sample unit does. Splitting along syntax, with
signatures of the surrounding code as shared context, should raise recall on large PRs without losing defects
that span units.

**Status.** Behind a switch, A/B pending. `--decompose ocr` stays the default; `hier` becomes the default only if
the §5 A/B passes its acceptance rule ([roadmap](docs/roadmap.md) P4).

### Added

- Decision ledger as `docs/decisions.jsonl` with `arbiter ledger list|show|render|check`; `docs/decisions.md` is
  generated. **Approach:** the user asked for a structured, queryable ledger; the markdown tables could only be
  grepped and drifted in column layout between sections.
- Requirement-first report: `RUN/report.md` leads with the verdict, tier counts and next action, then a table of
  requirements (A0 claims `R1…`, `[block]` repo rules `B1…`) with the findings that put each at risk, then findings
  by action tier (must fix, should fix, verify, optional, pre-existing) with folded evidence, the sandbox fix diff of
  a confirmed proof and up to two suggestion patches, and a table of all 21 axes. Finders get the requirements and may
  set `addresses` and `patches`; `report.json` gains `tier`, `sarif_level`, `requirements` and `decision`.
  **Approach:** the user asked for a condensed report that starts from the requirements, shows every axis and tells
  the author what to act on.
- `--decide`: one end-of-run Opus call per review (claim file, no retry, no tools, omp `--max-cost`, default $1.00)
  that links findings to requirements, dismisses non-blocking noise, challenges must-fix findings and adds at most
  three unverified concerns; it cannot add or remove a block. Every omp call loads `arbiter/omp-overlay.yml` to keep
  omp's advisor off. **Approach:** omp's advisor runtime retries and falls back across models, so it cannot keep the
  user's one-Opus-call budget; arbiter makes the call itself. Measured in [benchmarks §3.9](docs/benchmarks.md).
- Recall techniques T-27 (trigger and evidence before claim, on), and behind switches T-19 (`ARBITER_BASE_READS=1`,
  base checkout path for old-code reads), T-04 (`ARBITER_COCHANGE=1`, co-change neighbours from the last 500
  commits) and T-01 (`ARBITER_SAST_CANDIDATES=1`, uncovered analyzer hits on added lines become verifier
  candidates). **Approach:** the next-ranked items of the accuracy research. Together they scored F2 0.196 vs 0.198
  for master on 5 AACR PRs, and none showed a visible effect (benchmarks §3.9), so the three code paths are off.
- `arbiter eval aacr rescore`: judge several finished runs in one pass with one judge, plus their union.
  **Approach:** separate runs were judged on different days, so judge drift hid small differences.
- Leader study `research/research-leader-approaches.md` (Augment, Qodo 2.0 and PR-Agent, cubic, alibaba
  OpenCodeReview and AACR-Bench), ledger §4b and §4c, and ledger §8 "Rejected approaches": every dropped idea with
  its source tool, what it is, why that tool uses it and why arbiter dropped it. **Approach:** the user asked for the
  leaders to be mined and every rejection to be traceable; the leaders score F2 0.58–0.65 on arbiter's 20 Martian PRs
  against 0.40.
- Verified-but-unproven findings whose proof could not run here (sandbox unavailable, dependency fetch failed for
  their project root) go to the main section as should-fix, in a "Should-fix (verified; no proof possible here)"
  section, instead of Suspected (ledger T-12). **Approach:** the Martian loss trace found 2 such findings, both High
  golden bugs the top tools report; blocking still needs a proof.
- Evidence repair and quote relocation (T-13, T-18): an empty or malformed `evidence_lines` is set from the
  finding's `file:line`, and a finding outside the hunks moves to the added line its new `quote` field names before
  the hunk rule rejects it. **Approach:** 3 golden bugs were lost to these validation slips; OCR anchors comments by
  quoted snippet. Only the hunk stage is built.
- Maintainability as a first-class axis (MA-03, MA-04, MA-05): `arbiter/maintain.py` measures complexity, nesting,
  length, parameters and file size, base vs head, on Python functions the change touched (zero model calls); a new
  A6d readability agent gets those facts; a maintainability finding blocks only with a block-eligible measured fact
  or a repo rule heading marked `[block]`, otherwise it is capped at should-fix. The report section is now
  "Maintainability (readability · idiom · design · docs)". **Approach:** user decision; evolvability is about 75% of
  human review fixes and arbiter found 1 of 13 SWR-Bench evolvability changes.
- Maintainability recall scored separately in every eval summary (MA-02): SWR `E.*`, Martian `style`, AACR
  "Maintainability and Readability", seeded evolvability axes, plus evolvability finding counts. **Approach:**
  folding it into one recall number hid the 1-of-13 result.
- `--review-from DIR` on every `arbiter eval … run` (review with another checkout's `.venv`) and `--pr TEXT` on
  `martian` and `aacr` runs (E-13). **Approach:** items picked as best or worst regress to the mean on a rerun, so an
  old-vs-new comparison needs both arms on the same day.
- `arbiter eval aacr fetch|run`: AACR-Bench v2 (151 PRs, 10 languages) pinned by commit, repositories from AACR's
  pinned Hugging Face snapshots, scored with its file-level semantic coverage and recall per category (E-12).
  **Approach:** a larger, multi-language benchmark with a maintainability category; the PR target commits are not on
  GitHub, so the adapter follows AACR's own snapshot-first repository setup.
- Wave 1 spot check (`docs/benchmarks.md` §3.8, 11 score files in `eval/scores/`): old (master) vs new on 6 AACR
  Python samples (ComfyUI 9560, 7952 and 8446, ragflow 7151, langflow 6044 and 6652; 8446, 6044 and 6652 are the
  largest Python PRs in the set) and the last run's best and worst Martian PRs, plus new with `hier` on ComfyUI 9560.
  **Approach:** same-day arms through `--review-from`, one run each. **Result:** no recall lost on any item. AACR
  over 6 samples: recall 9/52 → 13/52, precision 0.26 → 0.29, F2 0.19 → 0.26, maintainability recall 2/9 → 2/9,
  model calls +26%. None of the 4 extra references came through a wave-1 mechanism: they are finder run-to-run
  variance. The new blocking policy blocked ragflow 7151 on a measured complexity rise (11 → 22). Sentry false
  positives 6 → 4. T-12 and T-18 did not fire.
- Review fixes before merge: failed dependency fetches count only for the finding's own ecosystem and never for a
  policy limit; moved and unparseable-base code no longer produces false block-eligible facts; quote relocation
  stays inside the unit; AACR snapshots lose their hooks and config, and commit values must be full SHAs; `--pr`
  matches the URL suffix. **Approach:** independent review of PR #5 (REQUEST_CHANGES, 10 findings, then APPROVE).
- Model matrix results for Python and TypeScript (`docs/benchmarks.md` §3.7, score files in `eval/scores/`). Haiku
  finders with a Sonnet verifier against Sonnet in every role, on seeded, Martian sentry and cal.com, and the 40-PR
  SWR-Bench sample. **Approach:** the same datasets and r2 briefs per setup, one run each, Go and Rust postponed.
  **Result:** Sonnet finders lose precision everywhere and lose on every metric on SWR-Bench, so Haiku finders stay
  the default (ledger M-11).
- `docs/decisions.md`: a ledger of every idea and concern raised, adopted, behind a switch, proposed, deferred or
  dropped, with its evidence. **Approach:** the user asked that technical decisions stay traceable, including the
  rejected ones; methodology's decision log only listed adopted design.
- Research reports `research/research-accuracy-techniques.md`, `research/research-learned-rules.md` and
  `research/research-code-quality-platforms.md`. **Approach:** surveys requested before building; their proposals are
  tracked in the ledger as `proposed`, none built yet.
- `--decompose ocr|hier|hier-split` on `arbiter run` and `arbiter plan` (default `ocr`, or `ARBITER_DECOMPOSE`), and
  a `--decompose` passthrough on `arbiter eval seeded|martian|swr run` that exports `ARBITER_DECOMPOSE` to each child
  run and records it in the eval summary. The mode goes into `plan.json` and the report's Coverage section.
  - **Approach:** a switch instead of a cutover, because no source measures "split one PR by syntax vs by hunk" for
    review `[DH-§6]`; the research makes adoption conditional on the A/B.
- `arbiter/decompose.py`, the hierarchical splitter (`hier`, `hier-split`): import package, then module, then
  top-level definition (module-level statements between definitions form one node), then method with the class
  header as context, then statement. Budget 150 churn (`ARBITER_UNIT_BUDGET` for the B=75 arm), a 40-churn floor,
  and a 1.33·B affinity ceiling that keeps a definition with its in-diff call sites. Unparseable and non-Python
  files keep the hunk chunking.
  - **Approach:** cAST-style recursive split-then-merge with stdlib `ast` `[DH-D17]`; budget in changed lines
    because every review-size number in the evidence is in lines `[DH-D1, D2, D32]`, and 150 rather than 50
    because function-sized units lose `[DH-D5, D18]`. Measured with `arbiter plan` on sentry PR 95633: `ocr` 7
    units (318, 345 and 421 churn among them) → `hier` 10 units, all but one within 150. Unit sets differ on 7 of the
    9 Martian sentry and sentry-greptile PRs tried; affinity, package and floor merges lower the count on some
    (sentry-greptile 5: 30 → 29; sentry 80528: 4 → 2, its pure moves leaving the finder units).
- A piece can cover part of one hunk (`Piece.lines`); unit ranges, triggers and the unit diff use the sub-range,
  and the diff marks clipped lines with `⋯`.
  - **Approach:** required by the split itself: a single-hunk new file was the case OCR units could not divide.
- `hier` shared context, zero model calls: a PR change manifest from base vs head `ast` (added, removed, modified,
  signature-changed, renamed; old → new signature; unit id), a per-unit context map (docstring and imports, class
  header, callee signatures, callers of changed interfaces via `codegraph` or `git grep`, capped at 10), the other
  changed files with unit ids, and the A0 intent claims and commit messages. Finder briefs say the map lists where
  to look and bodies are fetched with tools. The map is cut to keep diff plus map within 24k characters.
  - **Approach:** signatures, never bodies: pasted bodies are noise and on-demand fetching works
    `[DH-D10, D5, D14]`; textual intent beats surrounding code `[DH-D4]`, and A0 already produced it but finders
    only saw `unit_notes`.
- `hier` merge: a candidate is accepted on any changed hunk of the PR ±3, and findings citing the same
  signature-changed or renamed symbol from outside it cluster into one finding with `locations`.
  - **Approach:** finer units make the own-unit acceptance rule discard true cross-unit findings `[DH-§4.0]`;
    root-cause buckets follow Bugbot and Anthropic's dedup stage, made deterministic `[DH-D28, D34]`. The `ocr`
    merge is unchanged.
- `hier` contract pass: one run-level A5 call per PR when the manifest shows a signature change, removal or rename,
  with repo-wide callers. A file whose only change is a pure rename gets no finder unit.
  - **Approach:** callers outside the diff are a main miss `[DH-D1]`; one call per PR, not per unit, keeps the cost
    at +1 call `[DH-§4.4]`.
- `CHANGELOG.md`.

## [0.2.0] - 2026-11-23

Cheap-model defaults, SWR-Bench, and a modern Python structure (PR #2, squash commit `8f04917`).

### Added
- `arbiter eval swr fetch|sample|run`: SWR-Bench pinned at upstream `67ae1d4` (MIT), with a stratified 40-PR Python
  sample (28 with a functional issue, 12 clean, diff ≤ 300 lines, seed 20261122). Scoring loads the official judge
  prompts and parsers from the pinned checkout.
  - **Approach:** reuse the benchmark's own scorer instead of re-implementing it, so numbers stay comparable. Result:
    12 of 40 PRs scored before the rate limit, precision 0.58, recall 0.37, F1 0.45.
- `arbiter eval martian --offset N` to continue a sample.
  - **Approach:** the sentry run lost PRs 80528, 95633 and 80168 to the rate limit; resuming beats rerunning.
- Models resolved from omp roles (`arbiter-finder`, else `smol`, else Haiku; `arbiter-verify`, else Sonnet), with
  `--model @role`, and a preflight per model (read a file with the tool, answer in JSON) before any review work.
  - **Approach:** arbiter must run on any cheap model omp can reach (Haiku, DeepSeek, GPT-mini); an unconfigured
    model had made every agent call crash, so a bad model now exits 2 up front.
- `make install` (arbiter on PATH via `uv tool install --editable`, skills linked into `~/.omp/agent/skills`),
  `make install-claude`, `make check`.
  - **Approach:** the skills had found arbiter through a `~/.claude/skills` symlink, and the proof brief hard-coded
    this machine's checkout path; the proof agent now gets its sandbox command from its inputs.
- ruff and mypy configuration for Python 3.13.

### Changed
- Default models: Haiku for finders, A0 and SPEC; Sonnet for the verifier, proof agent and eval judge. A model is
  always passed explicitly, and the cost ceiling blocks `opus,fable` by default (`ARBITER_BLOCKED_MODELS`).
  - **Approach:** first tried the omp default model (Opus) for every role in 0.1.0. The Martian and SWR runs on Opus
    drained the account's token budget, so the user set Sonnet as the ceiling. Haiku on the seeded corpus scored
    precision 0.69, recall 0.62.
- Restructured for modern Python: `model.py` StrEnums and TypedDicts for every `RUN/*.json` record; `pipeline.py`
  split into `plan.py`, `gates.py` and the agent stages on a `RunDir` store; `tomllib` instead of regexes;
  `match` dispatch; keyword-only arguments for long signatures; shared eval helpers in `eval/common.py`.
  - **Approach:** behaviour-preserving refactor, checked by 125 passing tests, the round-2 seeded reports
    re-scoring identically, and a fake-harness run of python-03 completing end to end.

### Fixed
- Findings from arbiter's review of its own branch: eslint no longer runs on the host when the sandbox is down; a
  missing gate binary is a failed gate with its cause, not a timeout; ruff is detected from `[tool.uv]`
  dev-dependencies and `uv.lock` by exact name; invalid pyproject TOML is reported; the semgrep rules download has a
  timeout; a failing `codegraph affected` falls back to all tests and says so; a bad `--jobs` is exit 2; the first
  harness error is printed before the retry; a Martian judge failure is "unjudged", not a false positive; SWR blank
  patch lines are not changed lines, and a failed worktree or fetch marks the PR unavailable.
  - **Approach:** dogfooding: arbiter reviewed its own PR, and each finding was checked against the code before
    being fixed.

## [0.1.0] - 2026-11-22

Autonomous, evidence-gated multi-language code review (PR #1, squash commit `65f4c0f`).

### Added
- Deterministic pipeline: plan → sandbox → gates → intent (A0) → finders → merge → verify → proofs → gate →
  report, every stage reading and writing JSON in the RUN directory; stdlib-only Python.
  - **Approach:** orchestration in code, not an LLM coordinator, because cheap models cannot be trusted to plan and
    vote arithmetic and gating must be exact.
- OCR-style units: a file over 200 changed lines split into chunks of at most 150, grouped by project marker and
  directory, adjacent groups merged up to 150 lines and 10 files.
  - **Approach:** alibaba OCR's defaults `[DV-S6..S8]`; caps of 500 files / 8000 lines exit 4 per the size evidence
    `[DV-S4]`.
- 18 one-job agent briefs (A0–A9, SPEC, V, P), a 3-lens disprove panel, the E0–E9 evidence ladder, and a bubblewrap
  sandbox in which functional findings must be proven before they can block.
  - **Approach:** split agents by how each axis is verified `[AX-§3]`; finders and the verifier get read, grep and
    glob but no shell, because a prompt-injected agent with bash outside the sandbox could run anything; the gate
    trusts only arbiter's own exec records, because cheap models fabricate output.
- Language skills for Python, Go, Rust and TypeScript; the seeded corpus (28 cases) and the Martian harness.

### Changed
- Merge by location under the highest-priority axis.
  - **Approach:** a smoke run turned one f-string SQL query into three findings (logic, tests, security), so
    overlapping findings merge into one, described by the most consequential axis. Known cost: in round 2 it hid
    go-02's proven shadowed-`err` bug behind a weaker security claim (roadmap P1.1).
- Seeded brief revision r0 → r1: A1c stops "no test covers X" on new code, A6a stops copying functional bugs as
  idiom, A6b drops small duplication and bug-shaped design points, A6c stops turning a doc that states the contract
  into a docs finding.
  - **Approach:** round 0 (as built, omp default model) scored precision 0.40, recall 0.83; 33 of 55 main findings
    were false positives, clustered in A1c, A6a, A6b and A6c. Round 1: precision 0.585, recall 0.83, no clean-case
    findings.
- Seeded brief revision r1 → r2: A1c treats a test missing a boundary as a missing case, A6a needs a repo
  precedent for "use the stdlib", A6c skips failure modes of code that should not fail; rustfmt gate findings carry
  a message.
  - **Approach:** round 1 still had 17 of 41 main findings false. Round 2: precision 0.606, recall 0.76, no
    clean-case findings; precision missed the 0.80 target after the 2 allowed revisions, and both revisions were
    tuned on the scoring set (roadmap P0.3).

### Fixed
- Fail closed: more than 25% failed agent calls withholds a passing verdict (exit 5, INCOMPLETE report); a harness
  failure other than a timeout is retried once after 30 s; evals no longer score runs that exit 2–5.
  - **Approach:** a rate-limited run had reported PASS with zero working agents; a gate must not pass on silence.
- Formatter diffs that carry no message are described.
  - **Approach:** rustfmt reports a diff with no message, so its gate findings had no text to show.

[Unreleased]: https://github.com/lawrnsfeng/arbiter/compare/8f04917...HEAD
[0.2.0]: https://github.com/lawrnsfeng/arbiter/compare/65f4c0f...8f04917
[0.1.0]: https://github.com/lawrnsfeng/arbiter/commit/65f4c0f
