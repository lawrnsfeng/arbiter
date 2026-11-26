# Report render stack for arbiter: research (2026-11-26)

Scope: how to turn arbiter's run data into one offline, self-contained, deterministic report (HTML file + GitHub markdown + terminal). The LLM writes data only; the renderer owns every byte of markup.

Repo facts checked first:
- `arbiter/report.py:166-243` writes `report.md` + `report.json` with keys `verdict, repo, base, head, effort, requirements, decision, findings, coverage`. Findings already carry `addresses` (requirement id), `file`, `line`, `axis`, `rule`, `claim`, `tier`, `sarif_level`.
- `pyproject.toml`: `dependencies = []`. arbiter is a zero-dependency Python package. Any renderer choice that adds a runtime Python dependency (Jinja2, rich) breaks that property.

## 1. Sources

| Key | Source | URL |
|---|---|---|
| RS1 | npm registry metadata (version, licence) for every JS package below, fetched 2026-11-26 | https://registry.npmjs.org/ |
| RS2 | jsDelivr dist files, downloaded and measured (raw bytes, gzip -9) 2026-11-26 | https://cdn.jsdelivr.net/npm/ |
| RS3 | Playwright HTML reporter source (`html.ts`): data in `<template id="playwrightReportBase64">`, JS/CSS inlined | https://github.com/microsoft/playwright/blob/main/packages/playwright/src/reporters/html.ts |
| RS4 | Stryker blog: "One mutation testing HTML report" (JSON → web component; `src=` only works when served, set `.report` property for file://) | https://stryker-mutator.io/blog/one-mutation-testing-html-report |
| RS5 | Stryker mutation-testing-report-schema (mutant: `coveredBy`, `killedBy`, `location`, `status`, `statusReason`; top level `files`, `testFiles`) | https://github.com/stryker-mutator/mutation-testing-elements/blob/master/packages/report-schema/src/mutation-testing-report-schema.json |
| RS6 | Allure Report 3 configuration (`singleFile` option per report plugin) | https://allurereport.org/docs/v3/configure |
| RS7 | pytest-html user guide: `--self-contained-html`; default keeps assets separate "to respect CSP" | https://github.com/pytest-dev/pytest-html/blob/master/docs/user_guide.rst |
| RS8 | Django `json_script` implementation (escape `<`, `>`, `&` as `\u003C` etc. inside `<script type="application/json">`) | https://github.com/django/django/blob/main/django/utils/html.py |
| RS9 | WHATWG HTML: restrictions for contents of script elements | https://html.spec.whatwg.org/multipage/scripting.html#restrictions-for-contents-of-script-elements |
| RS10 | MDN: Content-Security-Policy (directives; `frame-ancestors` etc.) | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy |
| RS11 | GitHub Docs: Creating diagrams (Mermaid, GeoJSON, TopoJSON, STL; check version with `info`) | https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams |
| RS12 | GitHub community #203196: Mermaid renders in sandboxed iframe on `viewscreen.githubusercontent.com`; renderer crashes reported Sep 2026 | https://github.com/orgs/community/discussions/203196 |
| RS13 | Mermaid v13 "going on a diet" discussion (bundle heavy; v12.1.0 122 MB unpacked; v13 alpha 80 KiB flowchart-only, DOM-free) | https://github.com/orgs/mermaid-js/discussions/8685 |
| RS14 | Mermaid `securityLevel` (strict / loose / antiscript / sandbox) | https://mermaid.js.org/config/schema-docs/config-properties-securitylevel.html |
| RS15 | Mermaid sankey (v10.3.0+), treemap, requirementDiagram, architecture (v11.1.0+, beta) docs | https://mermaid.js.org/syntax/sankey.html ; https://mermaid.js.org/syntax/treemap.html ; https://mermaid.js.org/syntax/requirementDiagram.html ; https://mermaid.js.org/syntax/architecture |
| RS16 | MermanDraw: where Mermaid renders natively; beta types lag on hosts | https://mermandraw.com/blog/where-mermaid-renders-natively |
| RS17 | D2 layout engines (dagre, ELK, TALA) | https://d2lang.com/tour/layouts/ |
| RS18 | Vega interpreter: default Vega uses `Function` constructor, needs `unsafe-eval` unless `vega-interpreter` | https://vega.github.io/vega/usage/interpreter/ |
| RS19 | @alenaksu/json-viewer README (`filter`, `search`, `expand`, `collapse` by regex or path) | https://github.com/alenaksu/json-viewer |
| RS20 | @andypf/json-viewer README (toolbar, search bar, copy, 46 themes) | https://github.com/andypf/json-viewer |
| RS21 | svelte-jsoneditor / vanilla-jsoneditor README (tree/text/table, query, search, up to 512 MB) | https://github.com/josdejong/svelte-jsoneditor |
| RS22 | JSON Crack repo (Apache-2.0); `jsoncrack-react` 1.0.5 on npm | https://github.com/AykutSarac/jsoncrack.com |
| RS23 | diff2html README (side-by-side, highlight, file list) | https://github.com/rtfpessoa/diff2html |
| RS24 | Shiki README (TextMate grammars) | https://github.com/shikijs/shiki |
| RS25 | A2UI v0.9.1 protocol spec (createSurface / updateComponents / updateDataModel; flat adjacency list; catalog JSON Schema; JSON Pointer binding) | https://a2ui.org/specification/v0.9.1-a2ui |
| RS26 | google/A2UI repo (Apache-2.0; v1.0 now current) | https://github.com/google/A2UI |
| RS27 | json-render docs: specs (`root` + `elements` map; `$state` JSON Pointer; `visible`) and catalog as guardrail | https://json-render.dev/docs/specs ; https://json-render.dev/docs/catalog |
| RS28 | SEP-1865 MCP Apps (Final): `ui://` resources, `text/html;profile=mcp-app`, mandatory sandboxed iframe | https://modelcontextprotocol.io/seps/1865-mcp-apps-interactive-user-interfaces-for-mcp |
| RS29 | OpenAI Apps SDK: "Add UI to your MCP server" (MCP Apps first, `window.openai` only for extras) | https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt |
| RS30 | Adaptive Cards (MIT; schema 1.5 JSON; TextBlock, Container, FactSet) | https://github.com/microsoft/AdaptiveCards ; https://adaptivecards.io/schemas/adaptive-card.json |
| RS31 | SARIF v2.1.0 OASIS standard (§3.27.18 codeFlows, §3.27.19 graphs, §3.27.17 partialFingerprints, §3.19.25 taxa, §3.28.7 relationships, §3.27.30 fixes) | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html |
| RS32 | GitHub SARIF limits (25,000 results/run, top 5,000 shown; 10 MB upload) | https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/troubleshoot-sarif-uploads/results-exceed-limit ; https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/troubleshoot-sarif-uploads/file-too-large |
| RS33 | CTRF spec 0.3.0 (Working Draft, pre-1.0, MIT; flat tests; `extra` is the only extension point) + schema | https://github.com/ctrf-io/ctrf/blob/main/spec/ctrf.md ; https://github.com/ctrf-io/ctrf/blob/main/schema/ctrf.schema.json |
| RS34 | in-toto test-result predicate v0.1 (`result`, `configuration`, `passedTests`/`failedTests` names only) | https://github.com/in-toto/attestation/blob/main/spec/predicates/test-result.md |
| RS35 | OpenFastTrace concepts and terms (artifact types, Needs/Covers tracing chain) | https://openfasttrace.itsallcode.org/user_guide/introduction/concepts_and_terms.html ; https://openfasttrace.itsallcode.org/user_guide/use_cases/writing_a_specification.html |
| RS36 | lcov tracefile format (`BRDA:<line>,<block>,<branch>,<taken>`) | https://manpages.debian.org/testing/lcov/geninfo.1.en.html |
| RS37 | Cobertura coverage-04.dtd (`branch-rate`, `condition-coverage`) | https://raw.githubusercontent.com/cobertura/web/master/htdocs/xml/coverage-04.dtd |
| RS38 | rich README (Table, Tree, syntax, markdown) / textual README (TUI, also servable to browser) | https://github.com/Textualize/rich ; https://github.com/Textualize/textual |
| RS39 | arbiter `arbiter/report.py`, `pyproject.toml` (local, read 2026-11-26) | /home/lawrence/relic/arbiter |

## 2. Findings

### 2.1 Single-file HTML pattern (how mature tools do it)

| Tool | Data carriage | Single file? | Notes | Keys |
|---|---|---|---|---|
| Playwright HTML report | base64 zip in `<template id="playwrightReportBase64">` appended to `index.html`; app JS/CSS inlined into `<script type="module">`/`<style>` | yes (attachments/traces in folder) | prebuilt React app, data appended at end so the writer can stream it | RS3 |
| Stryker (mutation-testing-elements) | JSON set on a web component's `.report` property; schema-versioned JSON | yes | one viewer for Stryker JS/.NET/Scala; `src=` fetch fails from file://, so data must be inline | RS4, RS5 |
| Allure 3 | `singleFile: true` per plugin (awesome, classic, dashboard) | optional | Node-based prebuilt app; default is a multi-file site | RS6 |
| pytest-html | `--self-contained-html` inlines CSS/assets | optional | default multi-file "to respect CSP"; file/link attachments still external | RS7 |
| coverage.py HTML | multi-file directory | no | `[unverified]` here: docs returned 403 to the fetcher | — |

Pattern all converge on: **prebuilt static viewer + one schema-versioned JSON payload inlined**. Data and viewer are separable, so the same JSON feeds other renderers (RS4: "any framework can support an HTML report simply by producing a JSON file").

Size budget fact: over `file://` nothing is gzip-transferred, so the **raw** minified size is what the browser parses; gzip only matters for CI artifact storage `[INFERENCE]`. base64-embedded WASM grows ~33% and compresses poorly (RS2: @hpcc-js/wasm-graphviz 800 KB raw → 621 KB gzip).

### 2.2 Escaping and CSP for untrusted strings

| Risk | Mitigation | Keys |
|---|---|---|
| `</script>` or `<!--` inside finding text breaks out of the data block | Put data in `<script type="application/json" id="data">`; serialize with `json.dumps(...)` then replace `<`→`\u003c`, `>`→`\u003e`, `&`→`\u0026` (exact Django `json_script` table). Parse with `JSON.parse(el.textContent)` | RS8, RS9 |
| Renderer inserts text as HTML | Viewer uses `textContent`/`createElement` only; never `innerHTML` on data. No markdown→HTML of LLM text (or sanitize with DOMPurify 30 KB raw if markdown is ever needed) | RS2 |
| Injected script / exfiltration | `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'sha256-…'; style-src 'sha256-…'; img-src data:">`; hashes computed by the Python writer at build. `frame-ancestors` is not honoured in meta `[unverified in RS10 extract; standard CSP behaviour]` | RS10 |
| Library needs `eval` | Vega compiles expressions with `Function` → needs `unsafe-eval` unless `vega-interpreter` | RS18 |
| Mermaid labels from untrusted text | `securityLevel: "strict"` (default) or `"sandbox"`; still escape quotes/brackets in label text before building Mermaid source `[INFERENCE]` | RS14 |
| GitHub-markdown degrade | Escape `|`, backticks, `<`, and `@` in finding text: an unescaped `@user` in a PR comment notifies that user `[INFERENCE]` | RS39 |

### 2.3 Diagram and chart renderers (measured 2026-11-26; RS1, RS2)

Raw = minified file the HTML must inline; gz = gzip -9.

| Renderer | Offline | Single-file size (raw / gz) | GitHub-native | Licence | Layout quality / fit | Keys |
|---|---|---|---|---|---|---|
| Mermaid 12.3.0 (`mermaid.min.js`) | yes | 5,408 KB / 1,542 KB | **yes** (fenced ```` ```mermaid ````; version varies, probe with `info`) | MIT | dagre default, ELK plugin; flowchart/sequence/state fine; dense graphs route poorly; v13 rewrite (80 KiB, DOM-free) is alpha, flowchart only | RS11, RS12, RS13, RS16 |
| Mermaid types for arbiter | — | — | flowchart, sequence, state, requirementDiagram: yes; `sankey-beta` (v10.3+), `architecture-beta` (v11.1+), treemap: beta, may lag on hosts | — | `requirementDiagram` has `satisfies`/`verifies` relations = native req→test vocabulary | RS15, RS16 |
| Graphviz via @viz-js/viz 3.31 (`viz-global.js`) | yes (WASM inlined) | 1,298 KB / 468 KB | no | MIT wrapper; Graphviz itself EPL `[unverified]` | best-in-class layered layout (dot) | RS2 |
| Graphviz via @hpcc-js/wasm-graphviz 1.30 | yes | 800 KB / 621 KB | no | Apache-2.0 wrapper | same engine | RS2 |
| ELK.js 0.12.2 (`elk.bundled.js`) | yes | 1,610 KB / 467 KB | no | EPL-2.0 OR GPL-3.0+ | layout only (you draw SVG); best ports/orthogonal routing | RS1, RS2 |
| D2 (`@terrastruct/d2` 0.1.33 browser) | yes | 8,002 KB / 5,883 KB | no | MPL-2.0; TALA engine proprietary | very good with ELK; heavy WASM | RS1, RS2, RS17 |
| Cytoscape 3.35 (+ cytoscape-dagre 56 KB) | yes | 432 KB / 135 KB | no | MIT | interactive pan/zoom/select graphs; layout via plugins | RS2 |
| dagre (@dagrejs/dagre 3.1.4) | yes | 48 KB / 16 KB | no | MIT | layered layout only; small | RS2 |
| Vega-Lite 6.5 (+ vega 6.4 + vega-embed) | yes | 818 KB / 274 KB total | no | BSD-3 | best declarative charts from JSON spec; needs interpreter for strict CSP | RS2, RS18 |
| Observable Plot 0.6.19 (+ d3 7.9) | yes | 480 KB / 157 KB | no | ISC | concise charts; no graph layout | RS2 |
| ECharts 6.1 | yes | 1,095 KB / 359 KB | no | Apache-2.0 | rich charts incl. sankey/treemap/graph | RS2 |
| Hand-written SVG (no lib) | yes | ~5-20 KB `[INFERENCE]` | no (but same data can emit Mermaid for GitHub) | own | perfect for fixed shapes: columns req→code→test→finding, coverage bars, branch grids | — |

### 2.4 JSON viewers (RS1, RS2, RS19-22)

| Viewer | Form | Raw / gz | Collapse | Search/filter | Licence | Fit |
|---|---|---|---|---|---|---|
| @alenaksu/json-viewer 2.1.2 | web component | 43 KB / 11 KB | yes, by regex/path glob | `filter()`, `search()` iterator | MIT | best fit: tiny, no framework, path-addressable |
| @andypf/json-viewer 2.8.1 | web component | 39 KB / 12 KB | yes | toolbar search bar, copy, 46 themes | MIT | equally good; more UI out of the box |
| vanilla-jsoneditor 3.13 (standalone) | Svelte compiled | 1,254 KB / 366 KB | yes | search, JMESPath/JS query, table mode | ISC | too big for an embedded report |
| jsoneditor 10.4 (legacy) | vanilla | 1,035 KB / 273 KB | yes | search | Apache-2.0 | superseded by vanilla-jsoneditor |
| react-json-view / @microlink fork | React component | needs React | yes | no | MIT | drags in React |
| JSON Crack (`jsoncrack-react` 1.0.5) | React graph canvas | needs React `[size not measured]` | graph | yes | Apache-2.0 | graph-of-JSON is the wrong view for findings |
| json-formatter-js / renderjson | vanilla | 13 KB / 3 KB; 11 KB / 3 KB | yes | no | MIT / ISC | minimal fallback |

### 2.5 Code and diff display

| Lib | Raw / gz | Licence | Note | Keys |
|---|---|---|---|---|
| highlight.js 11 (`highlight.min.js`, common langs) | 126 KB / 42 KB | BSD-3 | runtime, sync, good enough | RS2 |
| Shiki 4.6 | not single-file friendly (grammars + WASM regex) `[INFERENCE]` | MIT | TextMate-accurate; best used at build time in Node, not from Python | RS24 |
| diff2html 3.4 (`diff2html-ui.min.js`, bundles highlight.js) | 1,024 KB / 326 KB | MIT | GitHub-like side-by-side; heavy for a snippet view | RS2, RS23 |
| No-lib unified diff (CSS classes per `+`/`-` line) | ~1 KB | own | sufficient for evidence snippets `[INFERENCE]` | — |

### 2.6 Agent-to-UI declarative specs ("generative UI")

| Spec | Shape | Maturity | Licence | Renderer offline/single-file? | Fit for arbiter | Keys |
|---|---|---|---|---|---|---|
| Google A2UI | JSONL stream: `createSurface`, `updateComponents` (flat list, children by id), `updateDataModel` (JSON Pointer), `deleteSurface`; catalog = JSON Schema of allowed components | v0.9.1 closed; v1.0 current; ~14.9k stars | Apache-2.0 | renderers for Lit/React/Angular/Flutter; @a2ui/lit 1.3 MB unpacked | idea fits (fixed catalog, data separate from layout); protocol is streaming/interactive, overkill for a static file | RS25, RS26, RS1 |
| Vercel json-render | `{root, elements:{id:{type, props, children}}}`; `$state` JSON Pointer; `visible` conditions; catalog via zod | 0.23 (pre-1.0) | Apache-2.0 | React/Vue renderers | same idea; React dependency | RS27, RS1 |
| MCP Apps (SEP-1865) / MCP-UI | server ships HTML resource `ui://…` (`text/html;profile=mcp-app`) rendered in sandboxed iframe; JSON-RPC to host | SEP Final; ext-apps 2.0.4 | MIT (ext-apps), Apache-2.0 (@mcp-ui/client) | it *is* an HTML file + data | relevant only if arbiter becomes an MCP server; the arbiter HTML viewer could be reused as an MCP App resource | RS28, RS1 |
| OpenAI Apps SDK | now builds on MCP Apps; `structuredContent` from data tool → widget renders; `window.openai` for extras | GA | — | same as MCP Apps | same | RS29 |
| Adaptive Cards | JSON card tree (TextBlock, FactSet, Container, Action.ToggleVisibility) | stable (schema 1.5/1.6) | MIT | JS renderer 327 KB raw | Teams/Outlook only; poor for tables/graphs | RS30, RS2 |
| Claude artifacts | model writes code (HTML/React/SVG/Mermaid) | product feature | proprietary | n/a | opposite of the constraint (model writes markup) `[unverified: help page 403]` | — |

Takeaway: every spec converges on **flat id-keyed entities + fixed catalog + data by reference**. arbiter needs that discipline but not the protocols: its "catalog" is a fixed set of report sections, and its data is domain JSON, not UI JSON. Let the LLM emit domain data only; never a UI tree.

### 2.7 Data standards: which carry requirement ↔ code ↔ test ↔ finding links

| Standard | Requirement | Code location / branch | Test | Finding | Link mechanics | Keys |
|---|---|---|---|---|---|---|
| SARIF 2.1.0 | via `taxa` (a requirement taxonomy) `[INFERENCE: not the intended use, but valid]` | `locations`, `relatedLocations`, `codeFlows`/`threadFlows` (execution path steps), `graphs` | no | `result` + `rule`; `partialFingerprints` for stable ids; `fixes` | `relationships` between reportingDescriptors; `result.taxa` | RS31; GitHub caps 25,000 results/run, 10 MB | 
| CTRF 0.3.0 | no field | `filePath`, `line`, `snippet` | yes (flat `tests[]`, `status`, `retries`, `labels`, `tags`) | no | `extra` only | RS33 |
| Stryker schema | no | `files[path].mutants[].location` | `testFiles`, test ids | mutant `status`/`statusReason` | `coveredBy[]`, `killedBy[]` test ids: test↔code link | RS5 |
| lcov / Cobertura | no | lines + branches: `BRDA:line,block,branch,taken`; `condition-coverage` | no per-test link (aggregate) | no | none | RS36, RS37 |
| OpenFastTrace | yes (`req~id~rev`) | `impl` tags in code | `utest`/`itest` tags | broken/uncovered trace = defect | `Needs:` / `Covers:` chain across artifact types | RS35 |
| in-toto test-result | no | no | test names only | no | DSSE envelope for signing the report `subject` | RS34 |

None carries the full chain. OpenFastTrace has the right *link model* (artifact types + covers/needs); SARIF has the right *finding model*; Stryker has the right *test↔code* links; lcov has the *branch* model.

### 2.8 Python-side generation options

| Option | Python deps | Build/vendor cost | Supply-chain surface | Keys |
|---|---|---|---|---|
| A. stdlib string assembly (`string.Template` or one f-string) + vendored `viewer.js`/`viewer.css` as package data + inline JSON | none | none; JS hand-written | own code + ≤2 vendored files pinned by sha256 | RS39, RS8 |
| B. Jinja2 template + vendored JS libs | Jinja2 + MarkupSafe | low | adds first runtime deps to a zero-dep package | RS39 |
| C. Prebuilt viewer app (Vite + Preact/Lit, single-file inline), built in CI, committed as one `viewer.html` | none at runtime | Node toolchain in repo; rebuild on change | full npm tree at build time (lockfile + audit) | RS3, RS4, RS6 |

### 2.9 Terminal

- rich: Table, Tree, syntax, markdown in the terminal; MIT; would be arbiter's first runtime dep (RS38, RS39).
- textual: full TUI, also servable to a browser, but needs a running process, so it does not meet "open a file offline" (RS38).
- Same JSON → plain ANSI renderer (verdict line, requirement status grid with ✓/⚠/✗, top must-fix items) is ~60 lines of stdlib `[INFERENCE]`.

## 3. Implications for arbiter (ranked)

### Recommended stack (R)

| # | Decision | Why (findings) |
|---|---|---|
| R1 | **One canonical `report.json` with a versioned schema** (`"schema": "arbiter.report/1"`), flat id-keyed entity arrays, links by id. HTML, markdown and terminal are three pure functions of it. | 2.1 (Stryker/Playwright split data from viewer), 2.6 (flat id lists), 2.7 |
| R2 | **HTML = stdlib Python writer + one hand-written vendored `viewer.js` (vanilla DOM, `textContent` only) + `viewer.css`, inlined.** Data in `<script type="application/json">` escaped per Django table. CSP meta with sha256 hashes computed at write time. Target ≤150 KB raw total for viewer + libs (excluding data). | 2.1, 2.2, 2.8 option A; keeps `dependencies = []` |
| R3 | **Graphics are hand-drawn SVG for the fixed views**: (a) traceability columns req → code/branch → test → finding (a 4-column "swim" graph; edges coloured by status); (b) per-requirement status chip row; (c) branch grid (branch × test, hit/miss); (d) tier counts bar. No layout engine needed because column order is fixed. | 2.3 (Mermaid 5.4 MB, Graphviz 0.8-1.3 MB raw for a layout the data already implies) |
| R4 | **Vendor one JSON viewer: @alenaksu/json-viewer (43 KB, MIT)** for the "raw data" drawer; path-addressable `expand('findings.3.**')` gives deep links from any chip to its JSON. | 2.4 |
| R5 | **Progressive disclosure in HTML**: level 0 verdict + next action + 4 counts; level 1 requirement grid (one row each, coloured chip, click to expand); level 2 trace for one requirement; level 3 evidence/proof/diff snippet; level 4 raw JSON. Use native `<details>`; URL `#req=R2` deep links. | 2.1 (Stryker deep links), 2.6 |
| R6 | **GitHub-markdown degrade from the same JSON**: verdict line, requirement table, must-fix list, then `<details>`; plus one ```` ```mermaid flowchart LR ```` of req→test→finding (GitHub renders it). Stick to `flowchart` (avoid beta types). Escape `|`, `` ` ``, `<`, `@` in LLM text. | 2.3 (GitHub-native Mermaid; beta lag), 2.2 |
| R7 | **Terminal: stdlib ANSI renderer** (verdict, requirement grid, must-fix top N, path to `report.html`). rich only as an optional extra if ever wanted. | 2.9 |
| R8 | **Export adapters, not adoption**: emit `report.sarif` (findings; requirement ids as `taxa`; evidence paths as `codeFlows`) and optionally CTRF for tests; keep arbiter's own schema as the source of truth because no standard carries the full chain. | 2.7 |
| R9 | Pin vendored files by sha256 in a manifest; a test asserts hashes and that the HTML contains no `<` inside the data block. | 2.2, 2.8 |

### Alternatives

| Alt | What | Gains | Costs |
|---|---|---|---|
| A1 Prebuilt viewer app (Playwright/Stryker/Allure model) | Vite + Preact (4 KB gz) or Lit; built to one `viewer.html` in CI; Python only injects the JSON block | richer interactions (filters, keyboard nav, virtualised lists); reusable later as an MCP App resource (RS28) | Node toolchain + npm lockfile in a Python repo; rebuild discipline; larger review surface |
| A2 Generic diagram engine embedded | Inline Mermaid 12 (5.4 MB raw) or @viz-js/viz (1.3 MB raw) and render Mermaid/DOT strings built from the JSON | one diagram language for HTML and GitHub (Mermaid); arbitrary graph shapes later | 1-5 MB per report; Mermaid label escaping; GitHub renderer flakiness (RS12); Mermaid v13 rewrite pending (RS13) |
| A3 Charts via Vega-Lite | Vega + Vega-Lite + embed (818 KB raw) with `vega-interpreter` for CSP | declarative chart JSON from Python with zero JS authoring | +0.8 MB; still no graph layout; interpreter wiring |

Not recommended: A2UI / json-render / Adaptive Cards as the report format (protocol overhead, framework renderers, no traceability semantics); JSON Crack and vanilla-jsoneditor (size); D2 (8 MB, MPL, proprietary best engine); Shiki from Python.

### Report JSON schema sketch (top-level keys only)

```json
{
  "schema":       "arbiter.report/1 — version string; renderers refuse unknown majors",
  "run":          "repo, base, head, effort, started/finished, tool + model versions, run dir",
  "verdict":      "block|pass|follow-ups|incomplete, next_action, counts by tier, one-line summary",
  "requirements": "[{id, text, source, status, kind}] — status derived, never LLM-written",
  "locations":    "[{id, file, start_line, end_line, symbol, change}] — code touched or cited",
  "branches":     "[{id, location_id, condition, outcomes:[{label, hit, test_ids}]}] — logic branches and which tests exercise each",
  "tests":        "[{id, name, file, line, kind, status, obligation_ids, oracle_grade}] — CTRF-compatible subset",
  "obligations":  "[{id, requirement_id, clause, technique, test_ids}] — e2e-design EARS obligations",
  "findings":     "[{id, tier, axis, rule, claim, location_id, requirement_id, evidence_ids, confirmed, sarif_level, fingerprint}]",
  "evidence":     "[{id, kind: command|diff|log|mutant|trace|quote, text, location_id, exit_code}] — untrusted text lives only here and in claim/text fields",
  "judge":        "{verdict: STRONG|GAPS|WEAK, rubric: [{id: R1..R13, grade, note}], mutants, gaps}",
  "coverage":     "{gates:[...], axes:[...], line/branch rates per location}",
  "links":        "[{from, to, rel: implements|exercises|covers|violates|proves}] — explicit edges; renderers may also derive them from *_id fields",
  "provenance":   "{inputs with sha256, vendored viewer hashes, optional in-toto subject}"
}
```

Chain: `requirements.id` ← `obligations.requirement_id` → `tests.obligation_ids` → `branches.outcomes.test_ids` → `locations` ← `findings.location_id` → `evidence_ids`. Mapping to today's `report.json`: `findings[].addresses` → `requirement_id`; `file`/`line` → `locations`; `coverage` keeps its shape (RS39).

---
Skipped: did not verify GitHub's current Mermaid version (no public source; use `info`), coverage.py HTML layout (docs 403), Claude artifacts page (403), Graphviz's own licence text. Sizes are single-file dist builds from jsDelivr; tree-shaken custom builds would be smaller.
