<!-- generated from decisions.jsonl by arbiter ledger render; edit the JSONL -->
# Decision ledger

This ledger records every technical idea and concern raised for arbiter, whatever happened to it: adopted, adopted behind a switch, proposed, deferred or dropped. Each row names where the idea came from, the evidence, and where the result lives. The reasoning behind the adopted design is in [methodology.md](methodology.md) §2–§5. Rejected approaches live in §8 with four fields: the tool or framework the idea came from, what it is, why that tool uses it, and why arbiter dropped it.

**Rule:** any new idea, concern, experiment or rejection gets a row in `decisions.jsonl` in the same change that raises it; `arbiter ledger render` regenerates this file and `arbiter ledger check` fails when it is stale. When an idea's status changes, edit its row and add the date; do not delete rows. [CHANGELOG.md](../CHANGELOG.md) says what shipped, and this file says what was decided.

Status values:
- `adopted`: in the code.
- `switch`: in the code, off by default until a test decides.
- `proposed`: researched, not built.
- `deferred`: wanted, postponed on purpose.
- `dropped`: rejected, with the reason.
- `open`: a known concern with no fix yet.

Source keys (`[DV-S4]`, `[DH-D10]`, `[AT-…]`, `[LR-…]`, `[CQ-…]`, `[LD1]`) resolve through [sources.md](sources.md). The research file for each prefix:

| Prefix | File |
|---|---|
| AT | `research/research-accuracy-techniques.md` |
| LR | `research/research-learned-rules.md` |
| CQ | `research/research-code-quality-platforms.md` |
| DH | `research/research-decompose-hierarchical.md` |
| LD | `research/research-leader-approaches.md` |
| RC, RP, RS, RM, RA | `research/research-report-{cognition,prior-art,render-stack,components,situations}.md`, synthesised in `research/research-report-ux.md` |
