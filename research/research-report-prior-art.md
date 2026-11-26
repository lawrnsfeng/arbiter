# Prior art: how review, coverage, test and traceability tools make results fast to read

Scope: how existing tools show **requirements**, **implementation status**, **logic branches**, **test coverage**, **review findings** and a **verdict**. The goal is to pick patterns for arbiter's report. Today arbiter writes `report.md` (verdict, requirements R1…/B1…, findings by tier, 21 axes) and `report.json` (`tier`, `sarif_level`, `requirements`, `decision`). The e2e-judge writes `judge.json` (R1..R13, STRONG/GAPS/WEAK, E0–E5 evidence, O0–O3 oracles).

Tags: `[unverified]` means a claim I could not confirm from a primary source in this session. `[INFERENCE]` means my own reasoning. `[vendor]` means a claim made by the vendor about its own product.

---

## 1. Sources

| Key | Source | URL |
|---|---|---|
| RP01 | coverage.py: Branch coverage measurement | https://coverage.readthedocs.io/en/latest/branch.html |
| RP02 | coverage.py: Measurement contexts (`--show-contexts`) | https://coverage.readthedocs.io/en/latest/contexts.html |
| RP03 | Stack Overflow answer on reading an Istanbul report (E/I markers, colours); secondary source | https://stackoverflow.com/questions/26618243/how-do-i-read-an-istanbul-coverage-report |
| RP04 | Istanbul: alternative reporters (`html`, `json-summary`) | https://istanbul.js.org/docs/advanced/alternative-reporters |
| RP05 | gcovr: HTML output (`--html-details`, `--html-nested`, themes) | https://www.gcovr.com/en/stable/output/html.html |
| RP06 | JaCoCo: coverage counters (branch diamonds, line colours) | https://www.jacoco.org/jacoco/trunk/doc/counters.html |
| RP07 | llvm-cov 23.1 (`-show-branches`, `-show-mcdc`, non-executed vectors) | https://releases.llvm.org/23.1.0/docs/CommandGuide/llvm-cov.html |
| RP08 | Codecov: pull request comments (layout, `require_changes`, condensed) | https://docs.codecov.com/docs/pull-request-comments |
| RP09 | Codecov: coverage percentages (`absolute <relative> (change)`, `ø`) | https://docs.codecov.com/docs/coverage-percentages |
| RP10 | Codecov blog: sunburst chart | https://about.codecov.io/blog/identify-coverage-holes-with-the-codecov-sunburst-chart/ |
| RP11 | Coveralls: web UI docs (search snippet only) | https://docs.coveralls.io/app-ui |
| RP12 | SonarQube Server: understanding quality gates (new code, fudge factor) | https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates/ |
| RP13 | Teamscale: working with Test Gap treemaps | https://docs.teamscale.com/howto/working-with-test-gap-treemaps |
| RP14 | Stryker mutation-testing-report-schema (JSON Schema) | https://raw.githubusercontent.com/stryker-mutator/mutation-testing-elements/master/packages/report-schema/src/mutation-testing-report-schema.json |
| RP15 | Stryker: mutant states and metrics | https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics |
| RP16 | StrykerJS 5.0 blog: the test view | https://stryker-mutator.io/blog/announcing-stryker-js-5-brave-new-dimension |
| RP17 | mutation-testing-elements repo (web components + schema) | https://github.com/stryker-mutator/mutation-testing-elements |
| RP18 | PIT report walkthrough (line coverage, mutation coverage, test strength); secondary source | https://codesoapbox.dev/mutation-testing-by-example-junit-5-maven-and-pitest |
| RP19 | Allure: visual analytics (charts, coverage diff map, heat map) | https://allurereport.org/docs/visual-analytics/ |
| RP20 | Allure: categories (clustering by error message) | https://allurereport.org/docs/categories |
| RP21 | Allure 3: navigation (epic → feature → story) | https://allurereport.org/docs/v3/navigation |
| RP22 | Playwright: reporters (HTML, `onlyFailures`, dot glyphs) | https://playwright.dev/docs/test-reporters |
| RP23 | Playwright: Trace Viewer | https://playwright.dev/docs/trace-viewer |
| RP24 | CTRF specification 0.3.0 | https://github.com/ctrf-io/ctrf/blob/main/spec/ctrf.md |
| RP25 | CTRF JSON schema | https://github.com/ctrf-io/ctrf/blob/main/schema/ctrf.schema.json |
| RP26 | CTRF GitHub Test Reporter: report showcase | https://github.com/ctrf-io/github-test-reporter/blob/main/docs/report-showcase.md |
| RP27 | Serenity BDD: living documentation (requirements tab) | https://serenity-bdd.github.io/docs/reporting/living_documentation |
| RP28 | multiple-cucumber-html-reporter: live demo | https://wasiqb.github.io/multiple-cucumber-html-reporter/browsers/index.html |
| RP29 | OpenFastTrace: system requirements (deep coverage, defect, transitive defect, HTML report) | https://github.com/itsallcode/openfasttrace/blob/main/doc/spec/system_requirements.md |
| RP30 | Doorstop: integrity checks and suspect links | https://doorstop.readthedocs.io/en/latest/cli/validation.html |
| RP31 | Sphinx-needs: `needflow` | https://sphinx-needs.readthedocs.io/en/stable/directives/needflow.html |
| RP32 | Sphinx-needs: `needpie` / `needtable` | https://sphinx-needs.readthedocs.io/en/stable/directives/needpie.html |
| RP33 | ReqView: requirements traceability matrix | https://www.reqview.com/blog/requirements-traceability-matrix/ |
| RP34 | Jama Connect: Live Trace Explorer diagram (Trace Score, edge percentages) | https://internal-help.jamasoftware.net/ah/en/manage-content/coverage-and-traceability/live-trace-explorer/what-s-included-in-the-diagram.html |
| RP35 | Jama Connect: Coverage Explorer | https://help.jamasoftware.com/en/manage-content/coverage-and-traceability/coverage-explorer.html |
| RP36 | CodeRabbit: PR walkthroughs | https://docs.coderabbit.ai/pr-reviews/walkthroughs |
| RP37 | CodeRabbit: reduce review noise (profiles, V3 drops sequence diagrams) | https://docs.coderabbit.ai/configuration/guides/reduce-noise |
| RP38 | asyncapi/generator #1514: "change coderabbit's config to be less annoying" | https://github.com/asyncapi/generator/issues/1514 |
| RP39 | crossplane PR #6794: "Set CodeRabbit to chill mode" (search snippet) | https://github.com/crossplane/crossplane/pull/6794 |
| RP40 | PR-Agent reviewer prompt and output schema (v0.50.0) | https://raw.githubusercontent.com/The-PR-Agent/pr-agent/v0.50.0/pr_agent/settings/pr_reviewer_prompts.toml |
| RP41 | Greptile: anatomy of a review | https://www.greptile.com/docs/code-review/first-pr-review |
| RP42 | Graphite Agent (Diamond): review comments and dashboard | https://graphite.dev/docs/diamond-review-comments |
| RP43 | GitHub Copilot code review | https://docs.github.com/en/copilot/concepts/agent-capabilities/agent-powered-workflows-and-operations/code-review |
| RP44 | Sourcery: anatomy of a review | https://docs.sourcery.ai/reviews/anatomy-of-a-review |
| RP45 | Augment Code: high-quality review agent benchmark (search snippet) `[vendor]` | https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent |
| RP46 | Chowdhury et al., MSR '26: "From Industry Claims to Empirical Reality: Code Review Agents in PRs" | https://arxiv.org/html/2604.03196 |
| RP47 | Sun et al., 2025: "Does AI Code Review Lead to Code Changes?" | https://arxiv.org/html/2508.18771v1 |
| RP48 | GitHub: SARIF support for code scanning | https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/sarif-support-for-code-scanning |
| RP49 | GitHub: assessing code scanning alerts ("Show paths") | https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-code-scanning-alerts/assess-alerts |
| RP50 | OASIS SARIF 2.1.0 | https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html |
| RP51 | Microsoft SARIF Viewer for VS Code (README, search snippet) | https://github.com/microsoft/sarif-vscode-extension |
| RP52 | Semgrep: finding details and dataflow traces | https://semgrep.dev/docs/semgrep-code/finding-details |
| RP53 | CodeScene: hotspots and technical debt | https://codescene.io/docs/guides/technical/hotspots.html |
| RP54 | CodeCity (Wettel) | https://wettel.github.io/codecity.html |
| RP55 | Codecov: example PR behind the comment screenshot | https://github.com/codecov/codecov-api/pull/150 |

---

## 2. Per-tool table

### 2a. Coverage

| Tool | Views | Backing schema | What makes it fast to read | Weakness | Screenshot / demo |
|---|---|---|---|---|---|
| coverage.py HTML | Index table per file. Source page: missed lines red, partial branches yellow, with the **missing destination line numbers** in the right margin (`2->4`) [RP01]. `--show-contexts` adds a per-line count of the tests that ran it; click to list them [RP02]. | `.coverage` SQLite database, plus `coverage json`/`xml` with separate statement and branch percentages [RP01][RP02] | Yellow means "a branch was not taken". The margin note names exactly where control never went. Per-line test lists answer "which test hit this?" | Branch shows as line pairs (`4->2`), not as true/false of a condition. Loop back-edges confuse readers [RP01]. File-centric, with no link to requirements. | Docs examples [RP01] |
| Istanbul / nyc lcov HTML | Directory table with Stmts / Branches / Funcs / Lines %. Source page with `xN` hit counts and markers **`E`** (else path not taken) and **`I`** (if path not taken). Colours: pink for statements, orange for functions, yellow for branches [RP03]. | lcov `.info`; `coverage-final.json`; `coverage-summary.json` totals per file [RP04] | One-letter markers sit inline at the branch, so the reader sees which side is missing without counting. | Four percentages per row without guidance on which matters. Markers are tiny. Source is a secondary SO answer [RP03]. | `[unverified]` |
| gcovr | Single summary page; `--html-details` per file; `--html-nested` per directory. Themes `github.green/blue/dark-*` [RP05]. `--decisions` adds decision coverage [RP05 search snippet]. | gcov `.gcno/.gcda`; JSON, Cobertura, SonarQube outputs | Self-contained single HTML file. Familiar GitHub colour scheme. | Line/branch counts only, with no "who covered it". | https://www.gcovr.com/en/stable/_images/screenshot-html-details.example.cpp.jpeg |
| JaCoCo HTML (reference for branch glyphs) | Drill-down package → class → method → line. **Diamond per decision line**: red (no branch), yellow (partial), green (all). Line background uses the same three colours. Missed-complexity counter [RP06]. | `jacoco.exec`, XML, CSV | A three-state glyph in the gutter is the most compact branch encoding. "Missed complexity" ≈ number of tests still needed [RP06]. | Red/green is hard for colour-blind readers (open issue jacoco#144, search snippet). Bytecode-level synthetic branches confuse readers [RP06]. | Docs |
| llvm-cov | `show` with `-show-branches=count/percent`; `-show-mcdc` per boolean expression. `-show-mcdc-non-executed-vectors` lists the **condition vectors never run** [RP07]. | Coverage mapping in the binary; `llvm-cov export` JSON | The MC/DC view says which condition was never shown to flip the outcome. That is the strongest "logic branch exercised?" answer of any tool here. | Text-heavy; aimed at safety-critical work. | Docs [RP07] |
| Codecov | PR comment: header (head %, **patch %**, change), flags, components, **impacted-files table** with `absolute <relative> (change)` and `ø` for "not affected" [RP08][RP09]. Condensed layout is recommended. `require_changes: "uncovered_patch"` posts only when the diff has uncovered lines [RP08]. Repo page: interactive **sunburst**, two levels deep, red/yellow/green by `coverage.range` (default 60..80); click to drill [RP10]. | Ingests lcov/cobertura/etc. Public API has `sunburst` and `icicle` endpoints (search snippet) | **Patch coverage**: one number for "is what I changed tested". The triple packs three facts in one cell. The sunburst shows holes by size and colour at a glance. | Users missed the sunburst when it was removed, so it was brought back [RP10]. The triple notation needs a legend [RP09]. Every new comment emails all PR subscribers [RP08]. | https://files.readme.io/a4e697c-example_PR_comment.png ; PR [RP55]; sunburst image in [RP10] |
| Coveralls | Repo page: coverage %, **coverage trend graph**, PR comments, file source view [RP11, snippet]. | Coveralls JSON API (`.json` suffix on build/file URLs) [RP11 snippet] | Trend line plus one headline %. | Line-only focus. I did not read primary UI detail `[unverified]`. | https://coveralls.io/features |
| SonarQube quality gate | Summary page: **Passed/Failed** gate with **New Code / Overall Code** tabs and issue counts per quality. PR decoration and CI status [RP12]. | Conditions = metric + operator + error value. PRs apply only new-code conditions. **Fudge factor**: coverage/duplication conditions are ignored under 20 new lines [RP12]. | One binary answer ("ready for release?"). A failed gate lists exactly which conditions failed. The "new code" scope removes legacy noise [RP12]. | The gate hides why a metric matters. Overall-code tab invites distraction. | Image in [RP12] |
| Teamscale Test Gap Analysis | **Treemap**: rectangle = method, size = SLOC. Gray = unchanged; green = changed and tested; **yellow = changed and not tested**; **red = new and not tested**. "Hide unchanged methods", zoom, CSV export with a criticality score [RP13]. | Static change history plus profiler coverage (e.g. JaCoCo), in partitions per test stage [RP13] | Four colours map exactly to the question "did tests run my change?". The docs warn that all-green proves nothing [RP13]. | Method granularity only; it does not show which branch inside a method. | Images in [RP13] |

### 2b. Mutation testing

| Tool | Views | Backing schema | What makes it fast to read | Weakness | Screenshot / demo |
|---|---|---|---|---|---|
| Stryker `mutation-testing-elements` | Web component `<mutation-test-report-app>`. File tree with a metrics table, and a source view with mutant markers by status. **Test view**: each test is **Killing / Covering / Not covering**; click to see the mutants it killed or covered [RP16][RP17]. Thresholds high/low drive the colour [RP14]. | **mutation-testing-report-schema** (JSON Schema draft-07): `files{path:{language,source,mutants[]}}`. Each mutant has `id, mutatorName, location, status ∈ {Killed, Survived, NoCoverage, CompileError, RuntimeError, Timeout, Ignored, Pending}, coveredBy[], killedBy[], replacement, statusReason`. Plus `testFiles{…tests[{id,name,location}]}` and `thresholds{high,low}` [RP14]. Metrics: detected = killed + timeout; score = detected / valid [RP15]. | The schema is tool-neutral (Stryker, Stryker.NET, Stryker4s, Infection, Pitest). One HTML file renders any producer [RP14][RP17]. The test view answers "is this test useless?" in one glance [RP16]. | Only one killer test is recorded because runs bail on the first failure, so "Covering" can mislead [RP16]. Static mutants show as Not covering [RP16]. | Images in [RP16] |
| PIT (Pitest) | Index with three metrics: **line coverage, mutation coverage, test strength**. Per-class source with line colouring and a mutation list [RP18, secondary]. | PIT XML/HTML; can emit the Stryker schema via plugin (Pitest is listed in schema examples [RP14]) | Three bars side by side separate "executed" from "asserted". | Dated UI. Long per-line mutation lists `[INFERENCE]`. | https://pitest.org/ |

### 2c. Test reports

| Tool | Views | Backing schema | What makes it fast to read | Weakness | Screenshot / demo |
|---|---|---|---|---|---|
| Allure Report (2/3) | Trees: **Behaviors (epic → feature → story)**, Suites, Packages [RP21]. **Categories**: failures clustered by status, then by error message ("Product errors" = failed, "Test errors" = broken) [RP20]. Charts: status pie with % passed in the centre plus new/flaky/retries; severity × status; status dynamics; **coverage diff treemap** (feature rectangles, size = tests, green = added/enabled, red = deleted/disabled); feature × environment failure **heat map**; stability distribution by epic/feature/story; **status age pyramid**; testing pyramid by layer; timeline [RP19]. | `*-result.json` per test with labels (`epic`, `feature`, `story`, `severity`, `layer`…) and `history.jsonl` for trends [RP19][RP20] | The central number plus colour gives health in under 5 s. The category tree merges 50 failures with one message into one line [RP20]. The coverage diff map exposes silently deleted tests [RP19]. | More than 15 chart types; the docs teach "tricks" to read them, which signals load [RP19]. History is needed for half the charts [RP19]. | Images in [RP19] |
| Playwright HTML report + Trace Viewer | HTML report: self-contained folder that opens automatically on failure. `onlyFailures` keeps only unexpected, flaky and interrupted tests [RP22]. Dot reporter glyphs: `·` pass, `F` fail, `×` will retry, `±` flaky, `T` timeout, `°` skip [RP22]. Trace Viewer: actions list, **film strip of screenshots**, Before/Action/After DOM snapshots, source line, errors marked with a **red line on the timeline**, network and console filtered to the selected action [RP23]. | `trace.zip`; JSON/JUnit/blob reporters; Perfetto trace-event JSON [RP22] | **Evidence is visual**: the screenshot strip shows what happened without reading logs. The error position appears on a timeline [RP23]. | Per test only; no requirement layer. | https://trace.playwright.dev/?trace=https://demo.playwright.dev/reports/todomvc/data/e6099cadf79aa753d5500aa9508f9d1dbd87b5ee.zip [RP23] |
| CTRF + reporters | Spec: one logical run; **flat** test list; hierarchy only via `suite`, `filePath`, `tags`, `parameters`; optional `insights` and `baseline` for cross-run deltas; `extra` is the only extension point [RP24]. GitHub Test Reporter: emoji summary table (Tests 📝, Passed ✅, Failed ❌, Skipped ⏭️, Pending ⏳, Other ❓, Flaky 🍂, Duration ⏱️), **delta row** (`58 ↑2`, `11.2s ↓2ms`), file report with `<details>` per file, failed/flaky/fail-rate/slowest/timeline/insights reports; Handlebars custom templates [RP26]. | **CTRF JSON Schema** (draft-07, normative) [RP24][RP25] | A single emoji row fits in a PR comment. The delta shows change since baseline. `<details>` keeps passing tests out of view [RP26]. | Pre-1.0, so field semantics may still change [RP24]. Has no requirement or coverage concepts. | [RP26] |
| Serenity BDD living documentation | **Requirements tab**: capability → feature → scenario tree with a result icon per node. Requirements with no tests show as **pending**. Child counts. A readme.md narrative per level. **Functional coverage** section breaks results down by child requirement. Donut plus table mix automated and manual (manual in a lighter tone) [RP27]. | Directory/package hierarchy or `@Epic/@Feature/@Story` annotations; Cucumber feature files [RP27] | The tree starts from what the product must do, not from test files. "Pending" makes unimplemented requirements visible [RP27]. | The hierarchy depends on folder structure. Uneven depths confuse readers [RP27]. | Images in [RP27] |
| Cucumber reports (multiple-cucumber-html-reporter) | Dashboard: Features chart, Scenarios chart, each with status percentages (passed, failed, ambiguous, not defined, pending, skipped) and a progress bar; per-feature drill-down [RP28]. | Cucumber JSON | "Not defined / pending" states show spec-vs-implementation gaps. | Two pies say the same thing twice `[INFERENCE]`. | [RP28] |

### 2d. Traceability

| Tool | Views | Backing schema | What makes it fast to read | Weakness | Screenshot / demo |
|---|---|---|---|---|---|
| OpenFastTrace | Plain-text and **single-file HTML** report. Summary = result status, item count, **completion progress bar**, direct and transitive defect counts. Details expanded or collapsed by config. **❎ marks a transitive defect** (an item that fails only because something it depends on fails) [RP29]. Per item: status, broken/total incoming and outgoing links, artifact types covered [RP29]. | Specification items: `id~name~revision`, Covers, Depends, **Needs** (artifact types such as `dsn`, `impl`, `utest`). Link statuses: covered shallow, unwanted, predated, outdated. **Deep coverage**: the item and all it needs are covered recursively [RP29]. | Explicitly built "to find gaps fast", not for auditors [RP29]. "Needs: dsn impl utest" makes the gap concrete: which artifact type is missing. The transitive mark separates root cause from fallout [RP29]. | Revision-suffixed IDs are noisy to read `[INFERENCE]`. | `[unverified]` (no public HTML demo found) |
| Doorstop | CLI tree of documents (REQ → TUT → HLT, LLT). `WARNING`/`ERROR` lines, e.g. "no links from document", **"suspect link"** when the parent's fingerprint changed since the link was reviewed [RP30]. Publishes HTML. | YAML/Markdown item files under git: `links` with parent fingerprint, `reviewed` hash, `normative`, `derived`, `active` [RP30] | **Suspect link** = "this requirement changed after the test was linked". It is a cheap staleness signal [RP30]. | Text warnings, no visual summary. | [RP30] |
| Sphinx-needs | `needtable` (filtered table), `needpie` (status pie), **`needflow`**: a graph of needs and their links, rooted at `root_id` with direction and depth limits, link names and a legend [RP31][RP32]. | Need objects with type, status, tags and typed links, declared in RST [RP31] | `root_id` plus `root_depth: 1` shows one requirement and its direct tests, a small and readable subgraph [RP31]. | Whole-project graphs become hairballs; filters are mandatory `[INFERENCE]`. | Rendered examples in [RP31] |
| ReqView | **RTM**: rows = requirements; traceability columns "Satisfies" and "Is verified by" show linked items with **test status**; Handlebars template columns print **warnings for missing links**; filter `NOT Is satisfied by`; impact analysis view [RP33]. | JSON project of documents and typed links; ReqIF [RP33] | Rows carry their own gap warnings, so the reader scans one column. The post itself says scrolling a 100×100 Excel RTM is unusable [RP33]. | Needs per-project template setup. | Images in [RP33] |
| Jama Connect | **Live Trace Explorer**: tiles per container joined by **trace paths with a % of valid (green) vs suspect (red) links**, gray = none. Overall **Trace Score** 0–100% with a calculation breakdown. Per-tile coverage per relationship rule; click goes to a filtered Trace View [RP34]. Coverage Explorer: downstream relationships or the lack of them, exportable to Excel [RP35]. | Relationship rules (the Traceability Information Model) [RP34] | Coverage sits on the **edges** of the V-model as percentages. One score, then a drill-down [RP34]. | Proprietary; the score hides which items fail until drilled. | Image in [RP34] |
| Polarion | Traceability matrices and suspect links (search snippets only) | — | — | Not verified from a primary source `[unverified]` | — |

### 2e. AI review tools

| Tool | Views | Backing schema | What makes it fast to read | Weakness | Screenshot / demo |
|---|---|---|---|---|---|
| CodeRabbit | Walkthrough comment, **collapsed `<details>` by default**: changed-files summary that **groups related files into one row**, Mermaid sequence diagrams, effort 1–5, **Merge Risk Minimal…Critical**, linked-issue assessment, related PRs, suggested labels and reviewers, optional poem [RP36]. Inline comments by profile: `quiet` (critical and major only), `chill` (up to 20, then collapses minor and major), `assertive` (everything) [RP37]. | Markdown in the PR; `.coderabbit.yaml` | Grouping rows (one source file plus 27 locale files becomes 2 rows) [RP36]. A hard cap of 20 inline comments, then collapse [RP37]. | Users call it "too verbose or too repetitive". For small PRs it is "overkill": Summary, Walkthrough, Changes and Sequence Diagram repeat the same facts. The sequence diagram is "too long, and often not that useful" [RP38]. **V3 config fixes `sequence_diagrams` at false** [RP37]. On one PR, assertive mode was approaching 200 comments [RP39, snippet]. | Docs [RP36] |
| Qodo / PR-Agent `/review` | Markdown review with optional sections. **Schema is explicit (Pydantic → YAML)**: `ticket_compliance_check[]` with **`fully_compliant_requirements` / `not_compliant_requirements` / `requires_further_human_verification`**; `estimated_effort_to_review_[1-5]`; `risk_level` low/medium/high; `merge_recommendation` ∈ {no_concerns_found, needs_review, changes_required}; `failure_modes[≤3]` {what, where, trigger, detected_by, **covered_in_this_pr**}; `key_issues_to_review[0..N]` {file, 1–2-word header, content, start/end line}; `relevant_tests` Yes/No; `security_concerns`; `can_be_split` [RP40]. | Same Pydantic model [RP40] | A three-bucket requirement check (met / not met / needs a human) maps directly onto arbiter's requirements. The prompt orders "write so the reader grasps the point immediately" and "prefer not reporting over guessing" [RP40]. | Many optional sections; with all of them on, it becomes a wall `[INFERENCE]`. | [RP40] |
| Greptile | Summary comment: plain-language summary, **confidence score 0–5** with a Merge / fix / rework / rethink legend, findings list linked to inline comments, **one auto-chosen diagram** (sequence, ER, class or flow; none for trivial PRs). Inline badges **P0/P1/P2**; types logic / syntax / style, configurable to drop style. Footer with review count and last reviewed commit [RP41]. | Markdown; `.greptile/config.json` [RP41] | One number answers "merge?". Severity badges let the reader scan only P0. The diagram type follows the change type, and trivial changes get none [RP41]. | The score is "contextual": 3/5 on payments ≠ 3/5 on a script [RP41], so it is not comparable across PRs. | Images in [RP41] |
| Graphite Agent (Diamond) | Inline comments only, each = problem + why + fix suggestion (one-click commit). Dashboard: issues found, **acceptance rate**, downvote rate, per-category acceptance [RP42]. | — | Each comment has three fixed parts. The tool measures its own acceptance [RP42]. | Augment's vendor benchmark says Graphite reached 75% precision but only 8.8% recall (12 of 137 bugs) [RP45 `[vendor]`]. | Images in [RP42] |
| GitHub Copilot code review | Overview comment with an **approval assessment** and the effort level used per run. Inline suggestions applied in a couple of clicks. Effort Lite / Balanced / Max / Adaptive [RP43]. | GitHub review API | Native review UI; approval state is binary [RP43]. | In the MSR '26 sample, Copilot's average signal ratio was 19.79% [RP46]. | [RP43] |
| Sourcery | Summary in the PR **description** (stays on top). **Reviewer's guide**: overview plus a table of what changed per file and why. Inline comments prefixed with a **type label** (`issue (bug_risk):`, `nitpick (performance):`, 🚨 security). One **status check**. Re-reviews resolve the threads that new commits addressed instead of re-posting [RP44]. | Markdown; status check | The label prefix tells the reader whether to read on. Re-reviews do not repeat themselves [RP44]. | The reviewer's guide is another prose wall on big PRs `[INFERENCE]`. | [RP44] |
| Augment Code Review | Inline comments; marketed on precision/recall [RP45]. | — | — | Vendor numbers only `[vendor]` | — |

**Evidence on noise (independent studies):**

| Finding | Source |
|---|---|
| CRA-only PRs merged 45.20% vs human-only 68.37%; abandonment 34.88% vs 21.60% (n = 3,109 PRs, χ² p < 0.001). | RP46 |
| 60.2% of closed CRA-only PRs had a 0–30% signal ratio. 12 of 13 CRAs averaged below 60% signal. High-signal reviews cluster at 1–3 comments. | RP46 |
| Human review comments were addressed ~60% of the time vs 0.9–19.2% for CRA comments (Gan et al., as cited). | RP46 |
| Hunk-level AI comments led to code changes 43.88% of the time vs 13.89% for file-level (human 84.75%). Comments that are **concise, contain code snippets and are manually triggered** are more likely to be acted on. | RP47 |

### 2f. Static analysis / SARIF

| Tool | Views | Backing schema | What makes it fast to read | Weakness | Screenshot / demo |
|---|---|---|---|---|---|
| GitHub code scanning | Alert list with filters (`is:open severity:high branch:main`, tool, tag, autofilter for application code). Alert page: **Show paths**, a numbered list of steps **source → sink**, with a dropdown when several paths exist ("3 paths available"). Show more for fix guidance. PR annotations appear only when all of the alert's lines are in the diff [RP48][RP49]. | SARIF 2.1.0 subset: `result.level`, `message.text` (only the first sentence shows when space is tight), `locations[0]`, `partialFingerprints`, **`codeFlows[].threadFlows[].locations[]`**; rule `properties.precision` and `security-severity` **decide default ordering**. Caps: top 5,000 results, 1,000 thread-flow locations [RP48]. | Ordering by severity × precision puts the likely-true, serious alerts first [RP48]. Numbered path steps turn data flow into a short list [RP49]. Diff-only annotation removes legacy noise [RP48]. | Path view is a list, not a graph. Long paths are tedious `[INFERENCE]`. | Images in [RP49] |
| Microsoft SARIF Viewer (VS Code) | Results as squiggles in the source, in the Problems list, or in a dedicated SARIF Results panel; code-flow stepping [RP51, snippet]. | SARIF 2.1.0 [RP50] | Findings appear where the code is. | Editor-only. | [RP51] |
| Semgrep | Finding page: description, rule, CWE, snippet, **dataflow trace** (source, intermediate steps, sink; click a step to highlight it in the file), autofix, activity log, AI true/false-positive verdict with reasoning [RP52]. | Semgrep JSON / SARIF | The trace is in context; clicking a step jumps the source pane to it [RP52]. | Reports only the shortest taint path by default (KB, search snippet). | [RP52] |

### 2g. Risk maps

| Tool | Views | Backing schema | What makes it fast to read | Weakness | Screenshot / demo |
|---|---|---|---|---|---|
| CodeScene | **Circle-packing hotspot map**: folders as circles, files inside. Colour combines selectable aspects (hotspot activity, low code health, defects, costs). Zoom, breadcrumbs, change-coupling lines on hover. A ranked refactoring-target list (red first, then yellow) [RP53]. | Git history plus code-health metrics plus a PM tool [RP53] | Combines **priority (churn)** with **severity (health)**, so a red, large circle means "fix here first". "You'll never get a list of 5,000 items to fix" [RP53]. | Needs history. Circle sizes are hard to compare exactly `[INFERENCE]`. | Images in [RP53] |
| CodeCity | 3D city: classes are buildings, packages are districts; visual properties encode chosen metrics [RP54]. | Moose model [RP54] | Gestalt overview of a large system. | 3D navigation cost; not suited to a per-PR report `[INFERENCE]`. | https://wettel.github.io/pics/codecity_screenshot.png |
| Codecov sunburst / Teamscale treemap / Allure coverage diff map | See 2a/2c: partition charts coloured by status [RP10][RP13][RP19]. | — | Size = volume, colour = status. | — | — |

### 2h. Logic-branch visualisation (which branches exist, which tests take them)

| Tool | What it shows | Granularity | Per-test? | Source |
|---|---|---|---|---|
| coverage.py | Partial-branch line plus missing destination; with contexts, which tests ran each line | line → line transition | Yes, per line (contexts) | RP01, RP02 |
| Istanbul | `E`/`I` markers at the `if` | if/else side | No | RP03 |
| JaCoCo | Red/yellow/green diamond per decision line; missed complexity | bytecode branch | No | RP06 |
| llvm-cov | Branch true/false counts; MC/DC per condition, including **non-executed test vectors** | condition | No (aggregate) | RP07 |
| Stryker | Mutant per operator/condition with `coveredBy`/`killedBy` test IDs; test view Killing/Covering/Not covering | expression | **Yes**: which test kills which mutant | RP14, RP16 |
| Teamscale | Changed method tested or not | method | Per test stage (partition) | RP13 |
| CodeQL / Semgrep / SARIF `codeFlows` | Ordered execution path for one finding | statement path | n/a | RP48, RP49, RP52 |
| Greptile | Auto flow diagram when control flow or business logic changed | AI-drawn | No | RP41 |

No tool found renders a **decision table or state diagram of the changed code joined to the tests that exercise each row**. The closest are llvm-cov MC/DC vectors (rows = condition combinations, executed or not) [RP07] and Stryker's mutant↔test matrix [RP14][RP16]. `[INFERENCE]`: this is an open slot arbiter could own, because e2e-judge already computes e2e-only branch coverage and targeted mutants.

---

## 3. Cross-tool pattern catalogue

| # | Pattern | Tools using it | Question answered in < 5 s |
|---|---|---|---|
| P1 | **Single gate verdict plus the failed conditions** | SonarQube gate [RP12]; Sourcery status check [RP44]; Copilot approval assessment [RP43]; PR-Agent `merge_recommendation` [RP40]; OFT result status [RP29] | Can I merge, and what exactly blocks it? |
| P2 | **Diff-scoped "new code" metrics** (with a small-change fudge factor) | Sonar new code plus fudge factor [RP12]; Codecov patch % [RP09]; Teamscale since-baseline [RP13]; GitHub diff-only annotations [RP48] | Is *my change* clean and tested, ignoring legacy? |
| P3 | **Requirement row with a status glyph and a gap reason** | Serenity tree with pending [RP27]; OFT Needs/covered types [RP29]; ReqView warning column [RP33]; PR-Agent met / not met / needs human [RP40] | Which requirements are done, missing or unverifiable? |
| P4 | **Transitive vs direct defect mark** | OFT ❎ [RP29] | Is this item broken itself, or only because of a dependency? |
| P5 | **Coverage on trace edges** (% valid / suspect per link type, plus one score) | Jama Live Trace Explorer, Trace Score [RP34]; OFT progress bar [RP29] | Which V-model hop (req → impl → test) is weakest? |
| P6 | **Suspect / stale link** | Doorstop fingerprints [RP30]; Jama suspect red [RP34] | Did the requirement change after the test was linked? |
| P7 | **Status-coloured partition chart** (size = volume, colour = status, click to drill) | Codecov sunburst [RP10]; Teamscale treemap [RP13]; Allure coverage diff map [RP19]; CodeScene circles [RP53] | Where are the big untested or unhealthy areas? |
| P8 | **Gutter glyph per branch** with the missing side named | JaCoCo diamonds [RP06]; Istanbul E/I [RP03]; coverage.py margin arrows [RP01]; llvm-cov branch counts [RP07] | Which side of this condition was never taken? |
| P9 | **Who-exercised-this drill-down** (line/mutant ↔ test) | coverage.py contexts [RP02]; Stryker `coveredBy`/`killedBy` plus test view [RP14][RP16] | Which test covers this, and does it actually assert? |
| P10 | **Executed vs asserted split** (coverage vs mutation score; Killing / Covering / Not covering) | Stryker [RP15][RP16]; PIT three bars [RP18] | Is the code merely run, or are results checked? |
| P11 | **Severity badge plus type label at the start of each finding** | Greptile P0/P1/P2 [RP41]; Sourcery `issue (bug_risk):` [RP44]; SARIF level [RP48] | Must I read this one? |
| P12 | **Rank by severity × precision (confidence)** | GitHub SARIF ordering [RP48]; PR-Agent "prefer not reporting over guessing" [RP40] | What is most likely real and serious? |
| P13 | **Hard volume cap, then collapse the rest** | CodeRabbit chill: 20 then collapse; quiet [RP37]; PR-Agent 0–N findings [RP40]; GitHub top 5,000 [RP48]; CodeScene "never 5,000 items" [RP53] | Is the list short enough to finish? |
| P14 | **Collapsed-by-default details** (progressive disclosure) | CodeRabbit `<details>` [RP36]; CTRF file report [RP26]; OFT details collapsed [RP29]; Codecov condensed [RP08] | Overview first; details only on click. |
| P15 | **Only-failures / post-only-if-changed** | Playwright `onlyFailures`, opens on failure [RP22]; Codecov `require_changes` [RP08] | Is there anything to look at at all? |
| P16 | **Cluster by root cause / message** | Allure categories [RP20]; CodeRabbit grouped file rows [RP36] | Are 30 failures really one problem? |
| P17 | **Numbered source → sink path** | CodeQL Show paths [RP49]; Semgrep trace [RP52]; SARIF `codeFlows` [RP48][RP50] | How does bad input reach the dangerous call? |
| P18 | **Visual evidence strip** (screenshots/timeline per step, red error marker) | Playwright Trace Viewer [RP23]; Allure timeline [RP19] | What did the user-visible system do when it failed? |
| P19 | **Delta vs baseline in the same cell** | Codecov `absolute <relative> (change)` [RP09]; CTRF `58 ↑2` [RP26]; Allure status dynamics [RP19] | Did this run get better or worse? |
| P20 | **One numeric risk / effort / confidence score** | Greptile 0–5 [RP41]; CodeRabbit effort 1–5 and Merge Risk [RP36]; PR-Agent effort and risk [RP40]; Jama Trace Score [RP34] | How worried should I be? |
| P21 | **Auto-picked change diagram (or none)** | Greptile picks type, none for trivial [RP41]; CodeRabbit sequence diagram, now off in V3 [RP36][RP37] | How do components interact after this change? |
| P22 | **Problem / why / fix triple per finding** | Graphite [RP42]; PR-Agent issue header and content [RP40] | What to do about this finding? |
| P23 | **Self-measured acceptance rate** | Graphite dashboard [RP42] | Is the reviewer worth listening to? |

---

## 4. Implications for arbiter

Ranked per area. Each recommendation cites the patterns and findings it rests on. "Adopt" means use the pattern. "Reuse schema" means emit or align with an existing open schema instead of inventing one.

### 4.1 Verdict

| Rank | Recommendation | Basis |
|---|---|---|
| 1 | Put **one verdict line first**: `BLOCK` / `PASS` (review) and `STRONG/GAPS/WEAK` (e2e). Under it, list **only the failed gate conditions** as short lines ("2 must-fix findings", "R3 not verified"). Never put prose first. | P1 [RP12][RP40][RP44] |
| 2 | Scope the gate to the **diff** (new code). Keep a fudge-factor-style rule so tiny changes are not failed on percentages. | P2 [RP12][RP09] |
| 3 | Add a **delta vs the previous arbiter run** on the same PR (fixed / new / still open) instead of re-printing everything; resolve addressed items as Sourcery does. | P19 [RP26][RP44] |
| 4 | Do **not** add a free-floating 0–5 confidence score. Greptile admits its score is not comparable across PRs. Arbiter's tier counts are already a checkable score. `[INFERENCE]` | P20 weakness [RP41] |

### 4.2 Requirements status

| Rank | Recommendation | Basis |
|---|---|---|
| 1 | Render requirements as a **matrix: rows = R1…/B1…, columns = Implemented · Tested (e2e obligation) · Evidence level (E0–E5) · Oracle (O0–O3) · Findings at risk**. Each cell is a glyph (✅ / ⚠️ / ❌ / ❔), and the row ends with a **one-phrase gap reason** ("no negative oracle"). | P3, P5 [RP29][RP33][RP34] |
| 2 | Use **PR-Agent's three buckets** for each requirement: met / not met / **needs a human** (unverifiable by code). This maps onto arbiter's VERIFY tier. | P3 [RP40] |
| 3 | Add OFT-style **transitive marking**: a requirement at risk only because a shared finding blocks it gets ❎ and a link to the root finding, so one bug does not look like five. | P4 [RP29] |
| 4 | Show **"Needs" per requirement** (impl, unit, e2e, …) and mark which artifact type is missing. This is more concrete than a percentage. | P3 [RP29] |
| 5 | Optional small **graph per requirement** (`root_id` + depth 1: requirement → code hunks → tests → findings), Mermaid, rendered only on expand. Never a whole-repo graph. | P5, P14 [RP31] |
| 6 | When a requirement's text changed after its tests were written (spec edited in the PR), flag the link as **suspect**. | P6 [RP30] |

### 4.3 Logic branches (branch coverage)

| Rank | Recommendation | Basis |
|---|---|---|
| 1 | For each changed function, show a **compact branch strip**: one glyph per decision (◆ green taken both ways, ◆ yellow one side, ◆ red neither) and the **name of the missing side** ("`if retries > 3` → false never taken"). | P8 [RP06][RP03][RP01] |
| 2 | Click a branch to see **which tests (e2e obligations) take it**. Store this as `coveredBy` / `killedBy` test IDs per branch, like Stryker. | P9 [RP02][RP14] |
| 3 | Split **executed vs asserted**: a branch taken by an e2e test whose targeted mutant survived is "covered, not asserted" (yellow), not green. This is arbiter's differentiator, since e2e-judge already runs mutants. | P10 [RP15][RP16] |
| 4 | For compound conditions, show a **mini decision table** (rows = condition combinations, column = exercised by which test, like llvm-cov's non-executed MC/DC vectors). Show it only on expand. No surveyed tool joins decision tables to tests per PR, so this is a gap arbiter can fill `[INFERENCE]`. | §2h [RP07] |
| 5 | Diff scope only: change-aware colours as Teamscale uses them (new and untested = red, changed and untested = yellow, unchanged = hidden). | P2, P7 [RP13] |

### 4.4 Test coverage

| Rank | Recommendation | Basis |
|---|---|---|
| 1 | **Reuse `mutation-testing-report-schema`** for e2e-judge's targeted mutants. Its `mutation-test-report-app` web component then renders file tree, mutant markers and the Killing/Covering/Not covering test view for free. | P9, P10 [RP14][RP16][RP17] |
| 2 | Emit **CTRF** for the e2e test run (flat tests plus `tags` = requirement IDs; `extra` for obligation, oracle and evidence level). A single emoji summary row plus a delta works in a PR comment. | P15, P19 [RP24][RP26] |
| 3 | Headline **patch coverage** of e2e on the diff (one number), not project coverage. | P2 [RP09] |
| 4 | Attach **visual evidence** per e2e obligation: link the Playwright trace / screenshot strip for failed or weak obligations. Show nothing for passing ones (`onlyFailures`). | P18, P15 [RP22][RP23] |
| 5 | Optional **treemap/sunburst of changed files** coloured by tested/untested, sized by changed lines, for large PRs only. | P7 [RP10][RP13] |

### 4.5 Findings

| Rank | Recommendation | Basis |
|---|---|---|
| 1 | **Hard cap the visible list** (e.g. all MUST, then at most N SHOULD), and put the rest in a collapsed section. Independent studies tie high comment counts and low signal to abandoned PRs, and high-signal reviews cluster at 1–3 comments. | P13 [RP46][RP37] |
| 2 | Each finding is **one line**: tier badge + type label + 1–2-word header + `file:line` + one-sentence why. The proof, diff and patch sit inside `<details>`. Concise, hunk-anchored comments with code snippets are the ones developers act on. | P11, P14, P22 [RP47][RP41][RP44][RP40] |
| 3 | **Order by tier × confidence** (proof result), as GitHub orders by severity × precision. Arbiter already writes `sarif_level`, so also emit `properties.precision` and `codeFlows` and **upload SARIF** to get GitHub's native alert UI and diff-only annotations. | P12, P17 [RP48] |
| 4 | **Cluster duplicates** by root cause (same rule or message across files) into one row with a count. | P16 [RP20][RP36] |
| 5 | For data-flow findings, show a **numbered source → sink path** (SARIF `codeFlows`), not prose. | P17 [RP49][RP52] |
| 6 | **Do not auto-generate sequence diagrams** by default. CodeRabbit users rejected them and V3 fixed them off. If arbiter adds a diagram, pick its type from the change, as Greptile does, and skip trivial PRs. | P21 [RP38][RP37][RP41] |
| 7 | Track arbiter's own **acceptance rate** (findings fixed vs dismissed) across runs, as Graphite does; the eval harness already has the data. | P23 [RP42] |

### 4.6 Cross-cutting

| Rank | Recommendation | Basis |
|---|---|---|
| 1 | **Layered disclosure**: L0 verdict line → L1 requirement matrix and capped findings → L2 per-branch strips and per-finding proofs (collapsed) → L3 raw JSON / SARIF / CTRF / mutation reports. | P14 [RP36][RP26][RP29] |
| 2 | **Single self-contained HTML file** next to `report.md`, as OFT and gcovr do, so it opens offline from a CI artifact. | [RP29][RP05][RP22] |
| 3 | Colour plus **shape/glyph** for every status (never colour alone), as OFT requires font-style differences for colour-blind readers. | [RP29][RP06] |
| 4 | **Reuse open schemas** for machine views (SARIF for findings, CTRF for tests, Stryker schema for mutants). Keep arbiter-specific data (requirements, obligations, evidence) in one small top-level JSON that references them by ID. | [RP14][RP24][RP48] |

---

Skipped or not verified:
- Polarion and Coveralls UI details: search snippets only.
- No public OpenFastTrace HTML demo found.
- The CodeCity controlled experiment PDF did not load.
- PIT and Istanbul details come from secondary sources.
- Vendor precision/recall numbers (Augment, Graphite) are unaudited.
