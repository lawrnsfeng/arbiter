# Hierarchical, syntax-aware decomposition for arbiter: does it raise review accuracy?

Access date for every source: 2026-11-23. This report extends `research/research-decompose-verify.md` §1 (cited as `[DV-Sx]`) and `research/research-ai-review-systems.md` §2–§4 (cited as `[AI-§x]`). It does not repeat their evidence except where a source was re-opened and a new number or caveat was found.

Tags: **V** = opened this session and the quoted claim was read in the source. `[unverified]` = could not open. `[from memory]` = not checked. `[INFERENCE]` = my synthesis; no source states it.

---

## 1. Short answer

**Smaller review inputs raise LLM bug-detection accuracy. Syntax-aware boundaries have not been shown to beat line or hunk boundaries. Splitting has a measured cost: it loses interprocedural context, and that loss is the main cause of false positives in project-scale LLM detection.**

- **Size effect: moderate–strong, from several independent settings.**
  - CRBugBench (1,800 tasks, agentic reviewers with full repos): "larger diffs significantly decrease detection probability (OR=0.591, \*\*\*)".
  - *Lost in the End* (FSE 2025): shrinking the input raises vulnerability recall by "over 37%" on average.
  - CASTLE: LLM "accuracy declines, and hallucinations increase as the code size grows".
  - Chain-of-Agents: chunked workers beat full-context by up to 10%, and by about 100% on inputs over 400k tokens.
  - *Bigger Isn't Always Better*: F1 0.657 under 10 lines vs 0.043 over 150 lines. **This study is weaker than `[DV-S4]` presented it.** Its own contribution list calls diff size "the dominant **confound**" of its synthetic-to-real gap. Its size buckets are small: 10–50 lines n=10, 150–600 lines n=14.
- **Syntax-aware vs line-based boundaries: weak, mixed or negative.**
  - Positive: cAST (EMNLP Findings 2025) gains +4.3 Recall@5 and +2.67 Pass@1 for *retrieval* chunks.
  - Negative: a controlled 864-setting study finds **function chunking is worst**, by 3.57–5.64 pp, with Cliff's δ = −1.0. It also finds cAST ≈ sliding window.
  - Negative: JetBrains' Long Code Arena study finds "simple line-based chunking matches syntax-aware splitting across budgets".
  - All three are RAG retrieval studies. **No study compares AST-bounded and hunk-bounded *review units* for code review.**
- **Context loss from splitting: strong.**
  - PrimeVul: function-level detection falls to near random once data is realistic (7B model: 68.26% F1 on BigVul, 3.09% on PrimeVul).
  - Project-scale LLM detectors: "truncated interprocedural context" accounts for 861 false positives. Misclassified program points account for 3,734.
  - CRBugBench: bugs that need non-local reasoning are harder, and proprietary repos drop up to 25.5%.
  - OCR/AACR-Bench: "overly fine partitioning (e.g., per hunk or per function review) … fragments a coherent change across isolated agents".
- **Conditions.**
  - Splitting **helps** when one unit is large (>~150 changed lines, or a long single-hunk new file) and the unit carries a cheap interface map, so the finder can fetch callers and callees on demand.
  - Splitting **hurts** when it cuts an interface change away from its call sites, when units fall below a function's worth of context, or when bulk caller/callee bodies are dumped in as context. On that last point, JitVul's Dep-Aug feeds "Top-5 callers and callees all at once, which may introduce noise", and its pairwise accuracy (pAcc) is lower than the plain LLM's in some settings.
- **For arbiter specifically** `[INFERENCE]`, from arbiter's own plans:
  - Today's OCR splitter already keeps 137/137 seeded runs and 37/40 SWR-sample PRs in single units of at most 150 lines. Hierarchical splitting changes nothing there.
  - The gap is narrow. A file with one huge hunk (usually a new file) cannot be split today. sentry PR 95633 has units of 345, 421 and 318 changed lines, each a single file with one hunk.
  - Findings outside the finder's own unit are rejected by `findings.in_hunks`. Any finer split therefore loses cross-unit findings unless that rule changes.

**Verdict:** use AST boundaries **only to split oversized units and to group cohesive code**, not to shrink units in general. Ship it behind a flag and adopt it only if the A/B in §5 passes.

---

## 2. Source table

| ID | Source | Venue / date | Setting | Granularity compared | Metric and quoted numbers | URL | Tag |
|---|---|---|---|---|---|---|---|
| D1 | Yang et al., **CRBugBench**, *(When) Should a Software Factory be Lights-off?* | arXiv 2610.13668, Oct 2026 (CMU/Microsoft) | review (agentic, bug detection) | PR size (logistic regression); single agent vs multi-agent | Best agent catches "71.9% of bugs within its top-5 comments". Larger diffs: "OR=0.591, \*\*\*". Heterogeneous diffs: "OR=0.795, \*". Proprietary repos: "dropping up to 25.5%". Exploration prompts "+5.8% (1.10x cost)"; multi-agents "+4.7% (5.55x cost)". "Comprehensive prompting is more cost-effective … than multi-agents". Median churn 189 lines | https://arxiv.org/abs/2610.13668 | V (scale of the OR predictor not stated in text I read: `[unverified]`) |
| D2 | Kumar et al., *Bigger Isn't Always Better* | arXiv 2606.15689, 2026 | review | diff-size buckets | F1 "0.657 on diffs under 10 lines to 0.043 on diffs over 150 lines". Buckets: Tiny n=92, Small (10–50) n=10, Medium n=34, Large (150–600) n=14. "The 10–50 line bucket performs best". Authors call size "the dominant confound" of synthetic vs real (100 synthetic + 50 real) | https://arxiv.org/html/2606.15689 | V; **mixed** (confounded, small n) |
| D3 | Zeng et al., **SWR-Bench** | arXiv 2509.01494 (FSE 2026 per `[AI-§3]`) | review | PR-level with full repo (its Table 2 lists Tufano: method; CodeReviewer: "Diff Hunk", 10,000; SWR: "Pull Request, Complete Codebase") | Multi-review aggregation "increasing F1 scores by up to 43.67%" | https://arxiv.org/html/2509.01494v2 | V |
| D4 | Hu et al., **ContextCRBench** | arXiv 2511.07017, FSE 2026 | review (hunk QE, line localization, comment generation) | diff alone vs + code context (full function/class) vs + textual context (issue/PR) | "textual context such as issue and PR descriptions providing a greater boost than the code context of surrounding functions". ByteDance deployment "+61.98%" relative | https://arxiv.org/abs/2511.07017 | V; **mixed** for code context |
| D5 | Li et al., **OpenCodeReview** on **AACR-Bench** | arXiv 2608.09290, Aug 2026 (Alibaba) | review | monolithic agent vs file-level parallel SubAgents (no isolated ablation found) | SEM-F1 "25.10% vs. 11.57%", "5-15x fewer tokens". Quote: "overly fine partitioning (e.g., per hunk or per function review) maximizes parallelism but fragments a coherent change". Each SubAgent gets "the file's diff, the resolved rule, the list of other changed files" plus a `file_read_diff` tool | https://arxiv.org/html/2608.09290 | V; **negative** on function-level |
| D6 | Zhang et al., **c-CRAB** | arXiv 2603.23448, Mar 2026 | review (comments judged by fix-and-test) | none varied | Hunk datasets "isolating individual diff hunks and abstracting away the broader pull requests and repository context". Union of 4 tools passes "97 out of the 234 tests … (41.5%)" | https://arxiv.org/html/2603.23448v3 | V (no granularity experiment) |
| D7 | Ding et al., **PrimeVul** | ICSE 2025 | vulnerability detection | function-level, realistic data | "a state-of-the-art 7B model scored 68.26% F1 on BigVul but only 3.09% F1 on PrimeVul". GPT-3.5/4 "akin to random guessing in the most stringent settings" | https://arxiv.org/abs/2403.18624 | V; **negative** for isolated functions |
| D8 | Dubniczky et al., **CASTLE** | arXiv 2503.09433, 2025 | vulnerability detection (250 micro-programs, 25 CWEs) | code size | LLMs "perform exceptionally well … in small code snippets. However, their accuracy declines, and hallucinations increase as the code size grows" | https://arxiv.org/abs/2503.09433 | V (qualitative in abstract) |
| D9 | Ahmed et al., **SecVulEval** | arXiv 2505.19828, 2025 | vulnerability detection, statement-level | function-only vs with context | Function-only datasets "miss broader program context, like data/control dependencies and interprocedural interactions". Best: "Claude-3.7-Sonnet … 23.83% F1-score" | https://arxiv.org/abs/2505.19828 | V; **negative** for isolated functions |
| D10 | Yildiz et al., **JitVul** | ACL 2025 | vulnerability detection (879 CVEs) | plain function vs Dep-Aug (top-5 callers/callees pasted) vs ReAct agent (on-demand callers/callees) | ReAct improves pAcc "0.1% to 16.61%". Dep-Aug "do not show consistent improvements … and even exhibit performance degradation". ReAct vs Dep-Aug "+9.46%" (4o-mini), "+8.42%" (4o) pAcc | https://arxiv.org/html/2503.03586 | V; **mixed**: pasted context hurts, fetched context helps |
| D11 | Li et al., *LLM-based Vulnerability Detection at Project Scale* | arXiv 2601.19239, 2026 | vulnerability detection, project scale | per-unit LLM detectors vs static analyzers | FP root causes: "truncated interprocedural context, incorrect program-point classification, and overlooked key program points … 861, 3734 and 543 false positives". Cost "up to more than $1,000" | https://arxiv.org/html/2601.19239 | V; **negative**: cost of cutting context |
| D12 | Sovrano et al. `[from memory: authors]`, *LLMs for In-File Vulnerability Localization Can Be "Lost in the End"* | FSE 2025 | vulnerability detection (XSS, SQLi, path traversal) | file size × bug position; chunk sizes | Detection falls toward the end of large files (p<.05). Chunking: "average recall increase of over 37%", "up to +95%". Optimal chunks: "500 to 1,500 characters" for frequent CWEs, "up to 6,500 characters" for others. CWE-89 fails above "4,000 characters" | https://arxiv.org/abs/2502.06898 | V; **positive** for smaller inputs |
| D13 | Lekssays et al., **LLMxCPG** | USENIX Security 2025 | vulnerability detection | full function/codebase vs CPG slice | Slicing "reduces code size by 67.84 to 90.93%"; "15-40% improvements in F1-score"; finds bugs "that span multiple functions" | https://arxiv.org/abs/2507.16585 | V; **positive** for slicing |
| D14 | Guo et al. `[from memory: authors]`, **RepoAudit** | ICML 2025 | bug detection, repo level | per-function data-flow + on-demand exploration + validator | "40 true bugs … precision of 78.43% … $2.54 per project"; "185 new bugs … 174 confirmed or fixed" | https://arxiv.org/abs/2501.18160 | V |
| D15 | Li et al., **IRIS** | arXiv 2405.17238 (ICLR 2025 `[from memory]`) | vulnerability detection, whole repo | LLM-inferred taint specs + CodeQL | "CodeQL detects only 27 … IRIS with GPT-4 detects 55 (+28)" | https://arxiv.org/abs/2405.17238 | V |
| D16 | Ding et al., **CrossCodeEval** | NeurIPS 2023 D&B | code completion | in-file vs + retrieved cross-file context | StarCoder-15.5B Python EM 8.82 → 15.72 (+retrieval) → 21.01 (+ref). From Retrieval to Retrieval w/ Ref (StarCoder, Python): "327 correct generations changed to incorrect, and 468 … the other way around". Retrieval "in fixed lines of code that do not often follow code structure" is hard to digest | https://arxiv.org/html/2310.11248v2 | V; **mixed** (gain plus large churn) |
| D17 | Zhang et al. `[from memory: authors]`, **cAST** | EMNLP Findings 2025 | RAG retrieval + generation | AST split-then-merge vs fixed-size chunks | "Recall@5 by 4.3 points on RepoEval", "Pass@1 by 2.67 points on SWE-bench". Size counted in "non-whitespace characters rather than by lines". Peak at "max_chunk_size … between 2000 and 2500 characters" | https://arxiv.org/html/2506.15655 | V; positive (retrieval only) |
| D18 | Wu et al., *How Does Chunking Affect Retrieval-Augmented Code Completion?* | arXiv 2605.04763, May 2026 | RAG code completion (864 settings) | Function vs Declaration vs Sliding Window vs cAST | "chunking based on functions underperforms all other strategies by 3.57--5.64 percentage points on RepoEval (Cliff's delta = -1.0)". "Function chunking is never Pareto-optimal". Context length dominates: up to "+4.2 pp" from 2k to 8k tokens | https://arxiv.org/abs/2605.04763 | V; **negative** for function units |
| D19 | Galimzyanov et al., *Practical Code RAG at Scale* | arXiv 2510.20609, Oct 2025 | RAG completion + bug localization | line vs syntax-aware splitting; chunk size | "Simple line-based chunking matches syntax-aware splitting across budgets". "32–64 line chunks work best at small budgets, and whole-file retrieval becomes competitive at 16000 tokens" | https://arxiv.org/abs/2510.20609 | V; **negative** for syntax-aware |
| D20 | Zhang et al., **Chain-of-Agents** | arXiv 2406.02818 (NeurIPS 2024 `[from memory]`) | long-context QA, summarization, code completion (RepoBench-P) | full context vs RAG vs sequential chunk workers + manager | "improvements by up to 10% over strong baselines of RAG, Full-Context". BookSum: "improvement of CoA reaches around 100% when the length is larger than 400k". "mitigates the lost-in-the-middle issue" | https://arxiv.org/abs/2406.02818 | V |
| D21 | Hsieh et al., **RULER** | COLM 2024 | synthetic long-context | context length | "only half of them can maintain satisfactory performance at the length of 32K" | https://arxiv.org/abs/2404.06654 | V |
| D22 | Bai et al., **LongBench v2** | arXiv 2412.15204 | long-context QA incl. code-repo understanding | direct vs longer reasoning | Best direct "50.1%"; o1-preview "57.7%"; humans "53.7%" | https://arxiv.org/abs/2412.15204 | V |
| D23 | Li et al., *RAG or Long-Context LLMs?* (Self-Route) | EMNLP 2024 industry | long-context QA | long context vs RAG chunks | "when resourced sufficiently, LC consistently outperforms RAG", RAG cheaper | https://arxiv.org/abs/2407.16833 | V; **mixed** (whole beats chunks when model is strong) |
| D24 | Jin et al., *Long-Context LLMs Meet RAG* | arXiv 2410.05983 | RAG QA | number of retrieved passages | Quality "initially improves first, but then subsequently declines as the number of retrieved passages increases"; cause: "hard negatives" | https://arxiv.org/abs/2410.05983 | V |
| D25 | Chroma, **Context Rot** | tech report, Jul 2025 | long-context, 18 models | focused (~300 tok) vs full (113k) | "consistent performance degradation with the full inputs" | https://www.trychroma.com/research/context-rot | V (also `[DV-S3]`) |
| D26 | Greptile, *Codebases are uniquely hard to search semantically* | vendor blog, Apr 2025 | retrieval | file vs function chunk embedding | Similarity: full file 0.718, file containing function 0.739, function alone 0.768; "chunk more 'tightly' - on a per-function level" | https://greptile.com/blog/semantic-codebase-search | V (n=1 toy example) |
| D27 | Greptile, *How to build a code review agent* | vendor blog, Oct 2026 | review | none | Cheap model screens file reads; model inversion "bug catch rates go up ~10%" | https://www.greptile.com/blog/how-to-build-a-code-review-agent | V |
| D28 | Cursor, *Building Bugbot* | vendor blog, 2025 | review | whole diff × 8 shuffled orders | "Run eight parallel passes with randomized diff order … Majority voting … Merge each bucket" | https://cursor.com/blog/building-bugbot | V |
| D29 | CodeRabbit docs (Explain / Change Stack; Plans) + blog *massive codebases* | docs 2026; blog Sep 2025 | review | coherent "layers" ordered by dependency, ranges inside files | PR grouped "into coherent areas, ordered so foundations come before the code that depends on them". Files/review 150–300 by plan; ">300 files are not supported". Codegraph of definitions, references and co-change | https://docs.coderabbit.ai/pr-reviews/coderabbit-review · https://docs.coderabbit.ai/management/plans · https://coderabbit.ai/blog/how-coderabbit-delivers-accurate-ai-code-reviews-on-massive-codebases | V (no accuracy numbers) |
| D30 | Qodo PR-Agent compression strategy | docs | review | whole PR packed by token budget | Drops deletion-only hunks, sorts by language then tokens, overflow listed as "other modified files"; enclosing function/class can extend context | https://raw.githubusercontent.com/qodo-ai/pr-agent/main/docs/docs/core-abilities/compression_strategy.md | V |
| D31 | Google, **AutoCommenter** | AIware 2024 | best-practice review | per file | Service "takes as input one or more source files … For each file, it constructs a model input". "85% of files have exactly one relevant code comment" | https://arxiv.org/html/2405.13565 | V |
| D32 | Sadowski et al., *Modern Code Review: A Case Study at Google* | ICSE-SEIP 2018 | human review | change size | "median number of lines modified is 24"; ">35% … modify only a single file"; comments per change peak "12.5 … for changes of about 1250 lines". Directory ownership drives reviewer choice | https://sback.it/publications/icse2018seip.pdf | V |
| D33 | Meta, **RADAR** | arXiv 2605.30208, 2026 | review triage | per-diff risk funnel | 535K+ diffs reviewed, 331K+ landed; revert rate "1/3" of non-RADAR | https://arxiv.org/abs/2605.30208 | V (no split granularity published) |
| D34 | Anthropic, Code Review docs + *How the Claude Code team does code review* | docs; blog Oct 2026 | review | whole PR, several parallel agents | "Find: several agents examine the diff and the surrounding code in parallel … Rank: … deduplicated". "Most PRs over 1,000 lines get findings, and most small ones come back clean." Substantive-comment share "16% to 54%" | https://code.claude.com/docs/en/code-review · https://claude.dev/blog/solving-code-review-at-anthropic | V (split rule not published) |
| D35 | Python tooling docs: `ast`, LibCST metadata, grimp, LlamaIndex CodeSplitter | docs | tooling | — | `ast` nodes carry `lineno`/`end_lineno`, plus `ast.get_source_segment`. LibCST: `PositionProvider`, `ParentNodeProvider`, `QualifiedNameProvider`, `FullRepoManager`. grimp: `find_upstream_modules`, `find_downstream_modules`, `find_modules_that_directly_import`. CodeSplitter defaults `chunk_lines=40`, `chunk_lines_overlap=15`, `max_chars=1500` | docs.python.org/3/library/ast.html · libcst.readthedocs.io/en/latest/metadata.html · grimp.readthedocs.io/en/stable/usage.html · docs.llamaindex.ai/en/stable/api_reference/node_parsers/code/ | V |
| D36 | Graphite, *The ideal PR is 50 lines long* | vendor blog | human review | PR size | "50-line code changes are reviewed and merged ~40% faster than 250-line changes … 15% less likely to be reverted" (search snippet only; page 404) | https://graphite.com/blog/the-ideal-pr-is-50-lines-long | `[unverified]` |
| D37 | Public rebuild of CRBugBench (malusamayo/CRBugBench) | GitHub, Oct 2026 | review benchmark | — | "995 Harbor-format code-review tasks … 98 open-source GitHub repositories"; "rebuilt from descriptions in the paper"; up to 19 GB per repo | https://github.com/malusamayo/CRBugBench | V (licence not shown) |

**Negative or mixed for finer granularity:** D2, D4, D5, D7, D9, D10, D11, D16, D18, D19, D23 (11 sources).
**Positive for smaller or focused inputs:** D1, D8, D12, D13, D20, D21, D25.
**No published accuracy numbers on review splitting:** D28–D34. No industry reviewer publishes a function-level split.

### Industry: what each splits on

| System | Split unit | Numbers | Src |
|---|---|---|---|
| Anthropic Code Review | Whole PR; several parallel finder agents over "the diff and the surrounding code"; agent count scales with PR `[AI-§2]` | "Most PRs over 1,000 lines get findings"; 16% → 54% substantive | D34 |
| CodeRabbit | Dependency-ordered "layers" (coherent areas), then files, then line ranges; codegraph and co-change context | file caps 150–300 per review | D29 |
| Greptile | Agent loop over the PR; graph context per changed function (`[DV-S12]`); function-level chunks for its **retrieval index**, not for review units | similarity 0.768 (function) vs 0.718 (file); model inversion ~+10% | D26, D27 |
| Graphite | Asks humans for small stacked PRs; reviewer scoped by category | "ideal PR 50 lines" | D36 `[unverified]` |
| Cursor Bugbot | Whole diff, 8 passes with shuffled file order, vote, merge buckets | resolution rate `[AI-§2]` | D28 |
| Qodo PR-Agent | Whole PR packed to a token budget; overflow listed by name | — | D30 |
| OpenCodeReview (Alibaba) | **File-level** SubAgents plus a list of other changed files and a `file_read_diff` tool; explicitly rejects per-hunk/per-function | 25.10% vs 11.57% SEM-F1 | D5 |
| Google | Humans: small CLs (median 24 lines), directory ownership. AutoCommenter: per file | 85% of files have one comment | D31, D32 |
| Meta RADAR | Per diff, risk-tiered funnel | reverts 1/3 | D33 |

### Program slicing and change-impact analysis as unit context

- Slicing is the classical answer to "what context does this hunk need".
- LLMxCPG (D13) is the only measured LLM result found. A CPG slice cuts code 68–91% and raises F1 15–40%.
- RepoAudit (D14) and IRIS (D15) get repo-level reach by pairing per-function LLM judgments with symbolic data flow (path conditions, CodeQL taint). They do not widen the window.
- Change-impact analysis (`codegraph impact/callers`) supplies the caller set `[DV-§1a]`.
- `[INFERENCE]` For a review unit, the useful slice is: changed symbols, their direct callers and callees (signatures only), and the def-use chain of any variable that crosses the unit boundary.

---

## 3. Mechanisms

### Why smaller units help

| Mechanism | Evidence |
|---|---|
| Attention dilution with diff volume, even for agents with repo tools | D1: OR=0.591 for larger diffs, OR=0.795 for heterogeneous diffs; the authors say larger diffs "dilute review attention" |
| Position effects | Lost in the middle `[DV-S2]`. D12 "lost-in-the-end": bugs late in large files are missed (p<.05) |
| Irrelevant context degrades reasoning, not just retrieval | D25 focused vs full. D24: more passages first help, then hurt ("hard negatives"). D26: noise drags embedding similarity toward the noise level |
| Effective context is far below the advertised window | D21: half the models are unsatisfactory at 32K |
| Chunk-then-aggregate beats one long read | D20: +10%, and about +100% at >400k tokens |
| Size → hallucination | D8 |

### Why smaller units hurt

| Mechanism | Evidence |
|---|---|
| Lost caller/callee and data-flow context | D7 (function-level F1 3.09%), D9, D11 (861 FPs from truncated interprocedural context), D1 (non-local bugs harder; −25.5% where project context is needed) |
| A coherent change is fragmented across agents | D5 (quoted: per-hunk/per-function "fragments a coherent change") |
| Function-sized chunks are too small to be useful | D18 (function chunking worst, −3.57 to −5.64 pp); D2 (best bucket 10–50 lines, not <10, though n=10) |
| Syntax boundaries buy little over line boundaries | D19, D18 (cAST ≈ sliding window) |
| Pasted context is noise; fetched context helps | D10 (Dep-Aug top-5 callers/callees sometimes below plain; ReAct +8–9 pp pAcc over Dep-Aug); D16 (retrieved context flips 327 right answers to wrong) |
| Whole-input wins when the model is strong enough | D23 (LC > RAG when resourced) |
| Cost per call and duplicated findings | D1 multi-agent 5.55× cost for +4.7% vs prompting 1.10× for +5.8%; D28/D34 need explicit bucket/dedup stages |

---

## 4. Design recommendations for arbiter (Python first)

### 4.0 Facts about today's arbiter that constrain the design (read from the code)

- **Units** (`units.py`) split only at hunk boundaries. A single-hunk file (usually a new file) cannot be split. Measured in `eval/results/**/plan.json`:
  - 10 Martian sentry PRs have 63 units; 11 Python units exceed 150 churn, up to 421.
  - 0 of 137 seeded plans and 0 of 40 SWR-sample plans have a unit over 150.
- **Finders are agentic.** `Tools.FINDER` = read, grep and glob in the HEAD worktree, so a unit is not context-isolated. Per JitVul and OCR, this is the right base.
- **`findings.merge` rejects findings outside the finder's own unit hunks ±3** (`in_hunks(c, ranges_by_unit[c["unit"]])`). A finder that sees a broken caller in another unit's hunk is discarded. Finer splitting makes this worse.
- **Dedup** (`_overlaps`) is already cross-unit: same file, same group, lines within ±3.
- **Prompt ordering** already puts the task first and last (`agents.build_prompt`).
- Standard effort runs 8 per-unit agents; deep runs 18 (K3 agents × 3).

### 4.1 Split hierarchy and stop criterion

Recursive split-then-merge in cAST style (D17). It replaces only `_pieces`/`_groups` and keeps the OCR fallbacks.

1. **Project root** (existing marker logic).
2. **Import package.** Group files by their nearest `__init__.py` package, not just by directory. Then merge sibling modules that import each other, using stdlib `ast` `Import`/`ImportFrom` on HEAD. grimp is optional.
3. **Module (file).** A package group over budget → one piece per module, then greedy-merge adjacent modules up to budget (existing `_mergeable`).
4. **Top-level definition.** A module over budget → map every hunk's added lines to the enclosing top-level node (`ast.parse(HEAD)`, `node.lineno`..`node.end_lineno`). Module-level statements between definitions form their own node. Greedy-merge adjacent nodes in source order up to budget. **This is the one new capability**: it splits single-hunk files.
5. **Method.** A class over budget → split by method. Carry the class header (bases, decorators, class-level assignments, `__init__` signature) as read-only context.
6. **Statement.** A single function over budget → split its body at top-level statement boundaries. The function signature is the context.
7. **Unparseable file** (syntax error, non-Python) → today's hunk chunking.

**Stop criterion:** changed lines (churn) ≤ **B = 150**, the existing cap. Add a **floor**: never emit a unit under ~40 changed lines while a sibling at the same level can absorb it.

- Why keep lines: every review-sizing number in the evidence is in changed lines (D1, D2, D32, `[DV-S1]`). Arbiter already measures churn. No source gives a review-unit budget in tokens.
- Why 150, not 50:
  - The <50-line advantage in D2 rests on n=10 and is confounded with synthetic data.
  - D18 and D5 show function-sized units lose.
  - D19's best retrieval chunk was 32–64 lines, but whole files were competitive once the budget was large.
- Secondary guard, in characters: cap the rendered unit prompt (diff + context map) at about **24k non-whitespace characters** (≈6–8k tokens). Character count follows cAST, which argues it beats lines because chunks vary in density. D12's optimal sizes (0.5–6.5k characters) were for whole-file vulnerability localization, not diffs.
  - `[INFERENCE]`: the 24k figure is my choice, sized to stay well inside D21's "satisfactory" range. No source gives it.
- Test the budget, do not assume it: arm C in §5 runs B=75.

### 4.2 Shared context per unit (signatures, not bodies)

Order: task, diff, then the map, then the task again (already the order).

- **PR change manifest.** Same for every unit; built locally with zero model calls by diffing `ast` of base and head:
  - One line per changed top-level symbol: `qualname | kind | added/removed/modified/signature-changed/renamed | old sig → new sig | unit id`.
  - Covers cross-unit interface changes cheaply.
  - D4 says textual intent context beats surrounding code, so also pass the **A0 intent claims and commit messages**. A0 already produces these. Today `_finder_jobs` passes only `unit_notes`.
- **Unit context map:**
  - The module docstring and the import block of each file in the unit.
  - The enclosing class header for method-level units.
  - Signatures (`def` line + docstring first line) of repo-defined **callees** referenced in changed lines. Resolve them with `codegraph callees` when `.codegraph/` exists (arbiter already shells out to `codegraph affected`). Otherwise use `ast` name resolution within the module and its `from x import y` targets.
  - **Callers** of any signature-changed, removed or renamed symbol: `codegraph callers <sym>`, depth 1, capped at 10, with a "truncated" note.
- **Do not paste caller/callee bodies.** D10 shows pasted bodies are noise. D10, D5 and D14 show fetching on demand works. Finders already have read and grep; tell them the map lists where to look.
- **List of other changed files with churn and their unit ids**, as OCR does (D5). Optionally, the finder may read another unit's diff, as with OCR's `file_read_diff`.

### 4.3 Dedup and merge across units

1. **Widen the acceptance rule.** Accept a candidate whose line falls in *any* changed hunk of the PR ±3, not just its own unit's hunks. Keep `unit` as provenance. Keep rejecting lines outside every hunk (pre-existing code); that is what `PREDATES_CHANGE` is for.
2. **Location dedup** stays as is (file, group, ±3 lines).
3. **Root-cause clustering.** Add a second key: the changed symbol a finding's `evidence_lines` cite, from the manifest. Several "stale caller of `f`" findings across units merge into one finding with multiple locations. This is Bugbot's "combine similar bugs into one bucket" (D28) and Anthropic's dedup stage (D34), made deterministic.
4. Voting and the verifier panel are unchanged. They already run per merged finding, so dedup before them saves verifier calls.

### 4.4 Changes that span units (renames, signature changes)

- **Affinity before budget.** If a changed definition and its in-diff call sites fit together in ≤1.33·B, keep them in one unit, even if that crosses a module boundary. This is a merge rule in step 2/3.
- **Otherwise split, and link.** Each unit holding a call site gets the old and new signature in its map. Each unit holding the definition gets the call-site list.
- **One PR-level contract pass** when the manifest shows a signature change, removal or rename. Reuse A5 (API/contract) with the manifest plus `codegraph callers` output across the repo, not just the diff. This adds 1 call per PR with interface changes, not per unit. It covers callers outside the diff, which D1 and `[DV-§1a]` identify as a main miss.
- **Pure renames** (same body hash, new qualname): no finder unit at all. Keep them in the manifest only. The contract pass checks for stragglers with `grep`.

### 4.5 Cost estimate

| Corpus | Today | Hierarchical, B=150 | Δ finder calls (standard, 8/unit) | Δ deep (18/unit) |
|---|---|---|---|---|
| Seeded (28 cases) | all units ≤150 | identical | 0 | 0 |
| SWR sample (40 PRs, ≤300 lines) | 0 units >150 | identical | 0 | 0 |
| Martian sentry (10 PRs) | 63 units | ≥77 units (+14, lower bound `Σ ceil(churn/150)−1` over the 11 oversized units) | ≥ +112 total (+22%) | ≥ +252 |

- Plus 1 contract call per PR with interface changes. The manifest and AST work cost zero model calls.
- Package-cohesion merging can also *remove* units, so the net could be smaller `[INFERENCE]`.
- At B=75, the sentry Δ roughly doubles `[INFERENCE]`.
- The existing `max_agents` budget drops triggered agents first, so cost stays capped. Recall on large PRs then becomes the thing to watch.

### 4.6 Python tooling

| Need | Tool | Why |
|---|---|---|
| Node spans, top-level/class/method boundaries, signatures, docstrings, imports | **stdlib `ast`** (`lineno`/`end_lineno`, `get_source_segment`, `get_docstring`) | Arbiter is stdlib-only; this is enough for steps 4–6 and for the manifest |
| Exact positions with comments, qualified names, scope/parent | LibCST (`PositionProvider`, `QualifiedNameProvider`, `ParentNodeProvider`, `FullRepoManager`) | Only if `ast` name resolution proves too weak. Adds a dependency |
| Multi-language splitting later (Go/Rust/TS) | tree-sitter (`py-tree-sitter` + grammars); LlamaIndex `CodeSplitter` shows the pattern (`chunk_lines=40`, `max_chars=1500`) | Same algorithm across languages. Adds dependencies |
| Package import graph, upstream/downstream modules | grimp (`find_upstream_modules`, `find_modules_that_directly_import`) or `ast` imports | Step 2 cohesion; `ast` suffices for in-diff edges |
| Callers/callees across the repo | `codegraph callers/callees/impact` (already shelled out to for `affected`) | Compiler-free, cross-file, truncation reported |

---

## 5. Experiment plan

**Arms**, all at standard effort with the same models and k:
- **A**: today's OCR units.
- **B**: hierarchical, B=150, with manifest, map, widened acceptance and root-cause dedup.
- **C** (optional): B with B=75.
- **Ablation B′**: hierarchical split *without* the manifest and the widened acceptance rule. This isolates the context-loss mechanism.

**Only PRs whose unit sets differ between A and B are run.** Elsewhere the arms are identical by construction.

**Corpora:**

| Corpus | Size | Role |
|---|---|---|
| Seeded corpus, 28 cases | identical units | Regression gate: arm B must reproduce arm A's results exactly, because the inputs are byte-identical |
| **New seeded "large/cross-unit" Python cases** | 12 cases: 6 bugs inside a >150-line single-hunk new file, 4 signature changes or renames with a stale caller in another module, 2 clean large refactors | Directly tests both the help and the hurt mechanism |
| SWR-Bench Python: all issue PRs with churn >150 | **20 PRs, 21 F-changes** (counted from `swr_datasets_d5c5.jsonl` with arbiter's `_diff_lines`; 12 have a file >150) plus 20 clean PRs >150 | Real but small. Directional only |
| Martian sentry | 10 PRs, 11 oversized units | Directional; check its golden comments for cross-unit issues |
| **CRBugBench Python subset** (public rebuild, D37) | sample 150 tasks with churn 150–1,500 | The only powered real-PR corpus with large diffs (median churn 189). Licence and disk (≤19 GB/repo) to check first |

**Metrics:**
- Per ground-truth issue: detected yes/no. Recall is primary.
- Precision and F1 pooled as SWR-Bench does. Arbiter's evidence-gated verified count.
- **Cross-unit recall**: the subset of issues whose fix or evidence touches more than one arm-B unit.
- False positives on clean PRs. Finder and verifier calls, tokens, wall time.

**Sample size:**
- Paired design, McNemar on per-issue detection. To detect a +10 pp recall change at α=0.05 with 80% power, assuming 25% discordant pairs, you need ≈195 issues.
- The CRBugBench subset (about 150 tasks × ~1.3 bugs) plus SWR (21) plus seeded (10) reaches that.
- Run each arm twice; score per-issue detection as the mean over the two runs (0, 0.5 or 1). Use a paired bootstrap (10k resamples) for confidence intervals, because single LLM runs are stochastic (D3).

**Stopping rule:**
- One interim look at 50% of issues.
- **Stop for futility** if the upper 95% CI of Δrecall is < +3 pp.
- **Stop for harm** if Δcross-unit-recall < −10 pp with its upper CI < 0.
- Otherwise run to completion. No early stop for efficacy.

**Adopt hierarchical units only if all of these hold:**
1. Δrecall ≥ +5 pp, with the 95% CI excluding 0.
2. Precision is non-inferior: Δ ≥ −2 pp at the lower CI.
3. Cross-unit recall is non-inferior: Δ ≥ −5 pp.
4. The seeded regression is exact.
5. Finder calls rise ≤ +30% on the changed PRs.

If arm B passes but B′ fails on cross-unit recall, the manifest and acceptance rule are the active ingredients. Keep them even if the split itself is dropped.

---

## 6. Gaps

- **No direct evidence on syntax-aware review units.** Every AST-vs-lines comparison found (D17, D18, D19) is for RAG retrieval. Every size result for review (D1, D2) varies PR size, not the split. Nobody has measured "split the same PR by function vs by hunk" for review.
- **D2's size curve is confounded.** Synthetic tiny diffs vs real large PRs; n=10 and n=14 in the key buckets. `[DV-S4]`'s "cliff at >150" should be read as directional.
- **D1's OR=0.591**: I did not find the unit of the diff-size predictor (per line? per log-line? standardized?). `[unverified]`.
- **D5 has no ablation** isolating file-level SubAgents vs monolithic review; its "overly fine partitioning" claim is argument, not measurement.
- **Industry**: none of Anthropic, Greptile, Bugbot, Qodo, Meta or Google publishes how splitting changes accuracy. CodeRabbit's layers have no numbers. Graphite's 50-line page returned 404 (`[unverified]`, snippet only).
- **Venues `[from memory]`**: IRIS at ICLR 2025, Chain-of-Agents at NeurIPS 2024. **Authors `[from memory]`**: D12, D14, D17.
- **SWR-Bench size**: arbiter's `_diff_lines` gives only 20 issue PRs >150 lines, while the paper reports an average of ~118 added / 64 deleted per PR `[DV-S5]`. The two counts disagree. I did not reconcile which commits each counts.
- **CRBugBench rebuild** is unofficial ("rebuilt from descriptions in the paper"), and its licence is not shown in the README.
- **Budget in tokens**: no source gives a review-unit token budget. The 24k-character guard in §4.1 is `[INFERENCE]`.
