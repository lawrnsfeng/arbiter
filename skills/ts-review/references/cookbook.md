# TypeScript command cookbook

`V` = verified in the source column. `†` = from memory. Every command runs in the sandbox from §4.

| Task | Command |
|---|---|
| **Enumerate modules** | `codegraph files --format package` V (S10). `tsc -b` with project references † |
| **Dependency graph** | `npx depcruise src --include-only "^src" --output-type json` V (S36). `madge --circular --ts-config tsconfig.json src` (`--circular`, `--json`, `--depends`) V (S37) |
| **Graph-agnostic** | `codegraph impact <sym> --depth 2 --json`; `codegraph affected <files>`; `codegraph cycles` V (S10) |
| **Single test** | `npx vitest run file.test.ts -t "name"` † |
| **Property testing** | `fc.assert(fc.property(fc.string(), ...))` V (S42) |
| **Fuzzing** | `npx jazzer FuzzTarget`; Jest `it.fuzz(...)` via `@jazzer.js/jest-runner` V (S42) |
| **Mutation (test strength)** | `npx stryker run --incremental --force --mutate src/a.ts:5-7` V (S30) |
| **Sanitizer / race** | `node --trace-warnings` †. `--unhandled-rejections=strict` † |
| **Type checker as oracle** | `tsc --noEmit -p tsconfig.json` † |
| **SAST** | semgrep V. `eslint-plugin-security` †. CodeQL † |
| **API break** | `api-extractor` † |
| **Benchmark** | `bench('name', () => ...)` with `vitest bench` V (S43). tinybench † |
| **e2e** | `npx playwright test file.spec.ts` † |
| Type gate | `npx tsc --noEmit -p .` (when `tsconfig.json` exists) |
| Lint gate | `npx eslint -f unix <files>` (when an eslint config exists) |
| Test gate | the package `test` script / `vitest run <files>` / `jest <files>` / `node --test` |
| Analyzers | `semgrep --config p/typescript` |
