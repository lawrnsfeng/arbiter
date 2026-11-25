# Local prior art for e2e-design (A) and e2e-suite-judge (B)

Scope read: curve skills/research, arbiter skills, devrem agents/skills, ~/.claude/skills, remedy and remembrance e2e harnesses.
I did not read: curve/*.py pipeline code, arbiter/research, devrem reviewer.md/architect.md bodies, remedy capture.js, remembrance eventflow_test.go, scenarios/schema.json, curve research/*.md bodies other than via evidence.md.

## 1. Assets

### devrem
| Asset | What it does | A | B |
|---|---|---|---|
| `devrem/skills/test-strength/SKILL.md` | Scores every unit/integ/e2e test on 7 criteria: failure oracle, assertion strength, "error, edge and corner coverage", "Branch reach … each early return, each error propagation", realistic multiplicity, replayable fixture, self-explaining. Verdicts STRONG/THIN/WEAK/MERGE; optional ≤3 hand mutants per file. | partial (lists missing cases) | **strong overlap**, but it judges tests against the *code's* branches ("list its branches and error paths from the source"), not against requirements |
| `devrem/agents/test-quality-reviewer.md` | Go-only (remembrance) weak-assertion reviewer. "name a realistic defect … that makes this fail. If you cannot, it is WEAK." Output: `file:line \| test \| verdict \| defect that would slip \| suggested assertion`. | no | overlap (subset of test-strength, Go only) |
| `devrem/agents/test-engineer.md` | Writes failing tests "from the **spec**, not from the code", "one or more per AC/EC, named after them" (`ac1_…`, `TestEC2_…`). Tiers: rstest/proptest/mock server (Rust); table, testcontainers, fuzz, contract (Go). Must fail "for the reason the AC describes". | **overlap** (unit/integ tier; not Playwright-e2e) | no |
| `devrem/skills/forge/references/spec-template.md` | Spec shape: `AC1: <given …, when …, then …>`, `## Edge cases (from the hunt)` `EC1: <scenario> → <expected behaviour>`, Contract, Out of scope. "No 'should be fast', no 'handles errors'." | input format for both | input format |
| `devrem/skills/forge/SKILL.md` Phase 2 (l.135-142) | Edge hunt: a fresh adversarial agent, "has not seen the architect's reasoning", walks `edge-cases.md`, max 15 items each with `path:line`; "each accepted edge case becomes an AC with prefix `EC`; each rejected one goes under **Out of scope**… Never drop one silently." | **overlap** (case enumeration) | the independence pattern can be reused |
| `devrem/skills/forge/references/edge-cases.md` | Category checklist: Inputs, Errors and failure ("Partial failure: step 2 of 3 fails — what state is left behind?", "Retries: idempotent?", "is every user-triggered error surfaced in the UI"), Concurrency, Time, State and data, remedy↔remembrance HTTP boundary, Security. | **overlap** (unhappy-path taxonomy) | can be reused as a checklist |
| `devrem/agents/ui-tester.md` | Remedy only. Drives the Playwright harness at 390/834/1440 and reports screenshots plus overflow/clipping/console-error/blank-page diagnostics, per UI AC. "Prove the harness before blaming the app". | executes e2e; does not design | no |
| `devrem/skills/planner/references/issue-template.md` (l.38,70) | Issue template; Goal, Problem, Today, Acceptance criteria, Contract, Out of scope and Verification are mandatory. | requirement input | requirement input |
| `devrem/skills/github-issue/SKILL.md` l.45-48 | Enriches an issue lacking ACs: "derive them from…", then `gh issue edit` adds `## Acceptance criteria` + `## Verification`. | upstream | — |

### curve
| Asset | What it does | A | B |
|---|---|---|---|
| `curve/skills/curve-review/references/agents/SPEC.md` | Checks each claim/AC against the code and reports partial/wrong/missing, plus scope creep. Proof hints: "E4: one test per failing acceptance criterion, with the oracle quoted from the spec"; "E9: an end-to-end run … when the criterion is about the whole flow." | partial (one test per AC) | adjacent: judges the *code* vs the spec, not the suite |
| `curve/skills/curve-review/references/evidence.md` | Ladder E0–E9 (E7 mutation: "surviving mutant = concrete proof" of weak tests; E9 "Integration / e2e (Playwright, containers)"). Verifier rules: "Spec-first oracle. The test author sees signature, docstring and caller contract, not the buggy body"; "Separate writer and judge"; "Tests are read-only"; fail-before/pass-after. Axis `tests` accepts E4, E7. | rules to reuse | **overlap**: the "Weak / missing tests" row needs E7 |
| `curve/skills/curve-review/references/axes.md` | Axis 2 robustness ("null/empty, overflow, encoding…", proof = "boundary-input test or property test"); errors axis ("S21: 92% of catastrophic failures from mishandled non-fatal errors", proof = "fault-injection test"); spec axis; test adequacy ("test passes when the change is reverted"). | taxonomy with sources | taxonomy with sources |
| `curve/research/research-decompose-verify.md`, `research-axes.md` | Sources behind evidence.md and axes.md (S-ids). | cite | cite |
| `curve/skills/{go,python,rust,ts}-review` | Language review skills with references `canon/cookbook/design/idioms/security/severity/tools.md`. | no | no |

### arbiter
| `arbiter/skills/arbiter-review` + 4 language skills | Same text as curve-review with the name `arbiter` ("arbiter is a deterministic pipeline (`arbiter run`)"). Code-diff review gate. | no | no (diff review, not suite judging) |

### ~/.claude/skills
The entries are `ts-review, rust-review, python-review, go-review, arbiter-review` plus the dirs `endless/` and `synced/`. Curve skills are not linked there. devrem skills arrive through the plugin, not via symlinks.

### Harnesses
| Asset | What it does |
|---|---|
| remedy `Makefile:421-441` `ui-build / ui-serve / ui-stop / ui-check` | Static web bundle on :8897; `ui-check ROUTES=<routes.json> VP=… OUT=…` runs `scripts/ui-fixture/audit/capture.js` (playwright-core) under `heavy-gate --class chromium --max-of-class 1`. It captures screenshots and diagnostics; whether it has assertion-style e2e is not determinable from what I read. |
| remedy `scripts/ui-fixture/{setup.sh,seed.py,token.sh,README.md}` | Seeded test account + data, backend :8883, `routes.json`. |
| remedy `tests/scenarios/` (remembrance keeps a pinned copy at `test/scenarios/`, `PINNED_FROM`) | "One catalog of expense behaviour, reviewed like code and run in every layer." JSON per scenario, `<ID>-<slug>.json`, `schema.json` (JSON Schema 2020-12), `GLOSSARY.md`, `plans/`. Has `seed` + ordered `steps` (HTTP `request` or `action`: clock moves, peer edits, worker runs, `await-sync`, **`fail-next` injects one failure**). Areas A–L, T (splits, sync, authz, censoring, undo, notify…). Placeholder tag `stub-needs-steps` + `coverage_seed.py --check`. **Most direct prior art for (A)'s output format and fault injection.** |
| remembrance `Makefile:229-270` | `test-unit` (TEST_TIER=unit, -race), `test-integration` (TEST_TIER=integration, `-p 1`, testcontainers), `ci-integration` → `vial gaps` "nothing may be gated out of the tier that runs everything" (anti-no-op), `test-catalog`/`vial inventory` (catalogue of every test: file, line, tier, infra). |
| remembrance `test/integration/eventflow_test.go` | Cross-service integration test (body not read). |

## 2. Packaging conventions
- **curve**: `Makefile install` symlinks `skills/*` → `~/.claude/skills/<name>` (`ln -sfn`; refuses if a non-symlink exists); `uninstall` removes only links pointing into the checkout. No plugin manifest. Not currently linked.
- **arbiter**: `make install` = `uv tool install --editable` (puts the `arbiter` CLI on PATH) + symlinks into `~/.omp/agent/skills`; `make install-claude` also links into `~/.claude/skills` (currently linked).
- **devrem**: Claude Code plugin `.claude-plugin/plugin.json` (v1.9.0) + `marketplace.json`; omp reads `package.json`. `make update` runs `claude plugin marketplace update devrem; claude plugin update devrem@devrem` and the omp equivalent; `make bump` syncs the version across both manifests. Skills are invoked as `/devrem:<name>`. It also ships `agents/*.md`. Its description says it "Ships the workflow agents user-wide (… test-engineer … ui-tester, test-quality-reviewer, scout)".
- **SKILL.md frontmatter**:
  - devrem uses `name`, `description` (long, with trigger phrases "Use when the user types /devrem:… or asks…"), with references in `skills/<s>/references/*.md` cited by relative path (`../forge/references/decision-questions.md`).
  - curve/arbiter use `name`, `description`, `argument-hint`, with references in `references/` and per-agent prompts in `references/agents/<ID>.md`. Those prompts carry their own frontmatter `id`, `output`, `refs` and fixed sections: Mission / Axes / Checklist / Do not report / Proof plan hints / Output.
  - Agents (devrem) use `name, description, tools, model, effort, color`.

## 3. Overlap / no-duplicate notes
- (B) must not re-implement the test-strength criteria 1–7 or the test-quality-reviewer "one question"; it can cite them. Gap left: neither maps tests to **requirement clauses**. Both use code branches as the yardstick.
- (A) must not duplicate the test-engineer per-AC naming (`ac1_`, `TestEC2_`) or the forge edge hunt. Gap left: no asset designs **Playwright/system-level** e2e from ACs, or asserts unhappy-path *actions* (default return, error surfaced in UI, log/queue/alert emission). edge-cases.md only asks "is every user-triggered error surfaced in the UI".
- The scenario JSON schema (`seed`/`steps`/`fail-next`) already gives a replayable e2e scenario format with fault injection. A new format would duplicate it.
- The evidence.md rules "Spec-first oracle", "Separate writer and judge" and E7 already encode A/B independence and mutation-based judging.

## 4. Where the skills could live (evidence)
- **devrem** (strongest fit): it already owns the requirement inputs (spec-template ACs/ECs, issue-template), the edge-case taxonomy, the per-AC test writer, the suite judge (`test-strength`, which "Judge[s] how strong each unit, integration and e2e test is in any repo"), the Playwright runner (`ui-tester`), and plugin distribution to Claude Code and omp. (B) could be an extension of test-strength (a new requirement-clause yardstick), or a sibling skill that reuses its criteria.
- **curve**: holds the research/evidence base (E-ladder, axes with sources, SPEC agent). Its skills are diff-review pipelines run by `curve run`, and it is not installed in ~/.claude/skills. The skills could cite `evidence.md` §3c rather than copy it.
- **arbiter**: a copy of curve-review under another name. I found nothing test-design-specific.

## Actionable rules
1. Take requirements in the devrem spec-template shape (AC = given/when/then; EC = scenario → expected behaviour); every AC/EC maps to ≥1 e2e test id.
2. Name tests after their clause (`ac<N>_…` / `TestEC<N>_…`, per test-engineer).
3. Write the oracle from the spec, never from the code under test (evidence.md §3c rule 3).
4. The designer and the judge are separate agents; the judge must not see the designer's reasoning (forge Phase 2 / §3c rule 2).
5. Walk every edge-cases.md category; each one is accepted as an EC or listed under Out of scope with a reason, never dropped silently.
6. Every unhappy clause asserts its exact action: default value, error kind/message, delegated call, UI-visible failure, or emitted log/queue/alert record.
7. Express fault injection and replay as scenario `seed` + `steps` (`fail-next`, clock moves, `await-sync`) in the existing schema.
8. The judge scores each test on test-strength's 7 criteria plus a clause→test traceability matrix; an uncovered clause = THIN/missing.
9. A "suite is weak" verdict needs E7 proof: a surviving mutant on the requirement's code path, or a named slipped defect.
10. Tests are read-only for the judge (§3c rule 4); it adds cases, never edits existing ones.
11. Remedy UI e2e runs only through `make ui-check` (one Chromium, heavy-gate); remembrance integration runs `TEST_TIER=integration … -p 1`.
12. Nothing may be gated out of the full tier (`vial gaps` anti-no-op).

## Research agent notes (unverified sources)

I left the curve pipeline Python, remedy `capture.js` and the scenario `schema.json` fields unread. Not determined: whether capture.js has assertions beyond diagnostics.
