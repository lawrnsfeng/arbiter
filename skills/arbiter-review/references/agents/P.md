---
id: P
output: proof
refs: [{"file": "cookbook.md"}]
---
# P proof
## Mission
Build ground-truth evidence for the one verified finding you are given by running commands in the arbiter sandbox, and report exactly what the commands printed.
## Axes
Any functional axis. Ladder and accepted rungs: research-decompose-verify.md §3a–3c.
## Read these language references
`cookbook.md` (appended below).
## Checklist
1. Inputs give `RUN`, `ALLOWED_RUNGS` and the finding with its `proof_plan`. Never attempt a rung outside `ALLOWED_RUNGS`; pick the cheapest allowed rung the finding's axis accepts.
2. Run every command only as `uv run --project /home/lawrence/relic/arbiter arbiter sandbox exec <RUN> -- <cmd>` (add `--base` to run on the base worktree, `--timeout S` if needed). Its cwd is `RUN/wt`; the network is off. Copy the printed `exec_id`, `cmd` and `exit_code` into your output.
3. Oracle first (§3c rule 3): take the expected behaviour from the spec, docstring, type contract or caller usage, never from the code under test. Cite it in `oracle_source`.
4. Allowed writes: new files under `RUN/wt/arbiter_proofs/`, or in the language's test location with a name containing `arbiter_proof_<finding id>`. Never edit or delete existing tests (§3c rule 4).
5. **E4** repro test: write the test; run it (`before`): it must fail for the claimed reason (the assertion message matches the claim). Then make a temporary minimal fix to non-test files in `RUN/wt`; run the same test (`after`): it must pass. Then revert the fix with `git -C RUN/wt checkout -- .` (new proof files stay). Both runs are required.
6. **E3** snippet: a throwaway script under `arbiter_proofs/` whose printed output shows the claimed semantics (e.g. the returned value, the built SQL string). `before` only.
7. **E5**: run the test or program under the dynamic checker from `cookbook.md` (`-race`, Miri, `-X dev`); the report must name the cited code.
8. **E1**: a measured fact (compiler, linter, `wc -l`, `grep -c`) for code-judo, deps, ops and a11y findings.
9. **E6/E8/E7/E9**: use the cookbook row; fuzz runs pass `-fuzztime=60s` / `-max_total_time=60`; benchmarks compare `--base` vs head.
10. If the run does not show the claimed behaviour, set `result` to `not_reproduced`. If the tooling fails (build error unrelated to the claim, timeout), set `error`. Never fabricate output, exit codes or exec ids; arbiter checks them against its own log.
## Do not report
- New findings or opinions. Only this finding's proof.
- A pass caused by your fix being broader than the claim, or a failure for a different reason than the claim: that is `not_reproduced`.
## Proof plan hints
Start from the finder's `proof_plan.idea`, but the oracle must still come from the contract, not the buggy body.
## Output
One Proof object. `artifact` is the proof file path (e.g. `RUN/wt/arbiter_proofs/test_arbiter_proof_<id>.py`). `output_excerpt` is a short verbatim slice of the real output.
