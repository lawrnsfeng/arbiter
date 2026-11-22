# TypeScript canon

## 1. Canon

| Key | Source | URL | Authority | Governs | Version/date |
|---|---|---|---|---|---|
| HB-DD | TS Handbook "Do's and Don'ts" | https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html | official | primitive types, `any`, callback types, overload design | page updated 2026-11-21 |
| HB-NAR | TS Handbook "Narrowing" | https://www.typescriptlang.org/docs/handbook/2/narrowing.html | official | type guards, predicates, `never` exhaustiveness | current |
| TS49 | TS 4.9 notes (`satisfies`) | https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html | official | `satisfies` | 4.9 |
| TS52 | TS 5.2 notes (`using`) | https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html | official | explicit resource mgmt, `SuppressedError` | 5.2 |
| TS58 | TS 5.8 notes | https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html | official | `erasableSyntaxOnly`, `module node18` | 5.8 |
| TS7 | Announcing TypeScript 7.0 | https://devblogs.microsoft.com/typescript/announcing-typescript-7-0 | official | native compiler, new defaults, hard deprecations | 2026-07-08 |
| TSC-* | tsconfig reference: `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, `isolatedDeclarations` | https://www.typescriptlang.org/tsconfig/ (pages `noUncheckedIndexedAccess.html`, `exactOptionalPropertyTypes.html`, `verbatimModuleSyntax.html`, `isolatedDeclarations.html`) | official | strictness flags | current |
| GTS | Google TypeScript Style Guide | https://google.github.io/styleguide/tsguide.html | org | full style + type system + review-decided items (RFC 2119 wording) | pushed on demand; no version |
| TSE-CFG | typescript-eslint shared configs | https://typescript-eslint.io/users/configs/ | official tooling | recommended / strict / stylistic (+ `-type-checked`) | v8.7x (v8.73.0 released 2026-11-16 per GitHub releases search result) |
| TSE-RULES | typescript-eslint rules index | https://typescript-eslint.io/rules/ | official tooling | rule→preset membership | same |
| TSE-NFP / NMP / SBE / SEC | rule pages: no-floating-promises, no-misused-promises, strict-boolean-expressions, switch-exhaustiveness-check | https://typescript-eslint.io/rules/no-floating-promises/ · /no-misused-promises/ · /strict-boolean-expressions/ · /switch-exhaustiveness-check/ | official tooling | async + boolean + exhaustiveness | same |
| BIOME / BIOME-CMP | Biome linter; Biome vs ESLint/Oxc | https://biomejs.dev/linter/ · https://biomejs.dev/introduction/comparison-with-other-tools | official tooling | 816 rules, own type inference | v2.x |
| ET | Effective TypeScript 2e, 83 items (Vanderkam) | https://github.com/danvk/effective-typescript (+ https://effectivetypescript.com/) | community (book, O'Reilly) | type design, inference, `any`, generics | 2nd ed. May 2024, TS 5.4.5 |
| ET29/45/64/74 | Item samples: valid states, hide unsafe casts, brands, runtime types | https://github.com/danvk/effective-typescript/blob/main/samples/ (ch-design/valid-states.md, ch-any/hide-unsafe-casts.md, ch-recipes/brands.md, ch-write-run/runtime-types.md) | community | as named | 2e |
| TT-TSC | Total TypeScript tsconfig cheat sheet | https://www.totaltypescript.com/tsconfig-cheat-sheet | community (Matt Pocock) | recommended tsconfig | changelog 2024-04-23 |
| TT-ENUM / TT-TVI / TT-ESO | Why I don't like enums; Type vs interface; erasableSyntaxOnly | https://www.totaltypescript.com/why-i-dont-like-typescript-enums · /type-vs-interface-which-should-you-use · /erasable-syntax-only | community | enums, type vs interface | undated |
| MDN-CAUSE | MDN `Error: cause` | https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/cause | reference | error chaining, `AggregateError`, `SuppressedError` | current |
| ZOD / VALI | Zod; Valibot | https://zod.dev/ · https://valibot.dev/guides/introduction/ | library docs | validating data at trust boundaries | Zod 4.6, needs TS ≥5.5 + `strict` |
| R-HOOKS / R-RULES / R-EFFECT | Rules of Hooks; Rules of React; You Might Not Need an Effect | https://react.dev/reference/rules/rules-of-hooks · https://react.dev/reference/rules · https://react.dev/learn/you-might-not-need-an-effect | official (React) | hooks, purity, effects | current |
| CCJS | clean-code-javascript | https://github.com/ryanmcdermott/clean-code-javascript | community (94.7k★) | Clean Code adapted to JS | living README |
| ATL | Atlassian: removing barrel files | https://www.atlassian.com/blog/atlassian-engineering/faster-builds-when-removing-barrel-files | org (case study) | barrel files cost | 2025-06-26 |
| DT | DefinitelyTyped README, "Common mistakes" | https://raw.githubusercontent.com/DefinitelyTyped/DefinitelyTyped/master/README.md | official (MS/DT) | `.d.ts` review checklist | living |
| TSE-PR | typescript-eslint Pull Requests guide | https://typescript-eslint.io/contributing/pull-requests | project | PR review norms | living |

### TS 5.x → 7 status (verified)
- **TS 7.0 (2026-07-08)** is the Go native port: 8–12× faster full builds, parallel `--checkers` (default 4), `--builders`, `--singleThreaded` [TS7].
- **New defaults in 7.0 (inherited from 6.0):** `strict: true`, `module: esnext`, `noUncheckedSideEffectImports: true`, `types: []`, `rootDir: ./`, `stableTypeOrdering` always on [TS7].
- **Now hard errors:** `target: es5`, `moduleResolution: node/node10/classic`, `baseUrl`, AMD/UMD/System modules, `esModuleInterop: false`, `module` keyword for namespaces, `assert` import assertions [TS7].
- **No compiler API in 7.0.** typescript-eslint, Vue, Svelte, Astro and Angular templates keep using TS 6 through the `@typescript/typescript6` alias [TS7]. A 7.1 beta (2026-10-20) restores an API; I saw this only in a search snippet (InfoQ / GitHub releases), not on a page I opened.
- **Reviewer implication:** `"strict": false` or a deprecated flag in a 2026 tsconfig is a migration-blocker finding, not style.

## Known gaps

- **Effective TypeScript:** only the 83 item titles and samples for Items 29, 45, 64 and 74 were opened; other item claims rest on titles. The book text is paywalled.
- **Total TypeScript:** the "Cursor rules" page (Result types etc.) is gated; its body was not visible. Pocock's specific Result-pattern guidance is unverified. Result-type guidance here otherwise rests on general practice `[from memory]`.
- **Google guide:** I read the Policies/Consistency body only as a heading.
- **TS 7.1 beta and its API:** seen only in search snippets (InfoQ, GitHub releases). typescript-eslint's TS 7 support status is beyond the TS7 blog's alias advice: unverified (issue #10940 not opened).
- **Biome:** its exact list of type-aware rules was not opened.
- **`isolatedDeclarations`:** I did not open its 5.5 release-note details.
- **From memory:** `as const` (TS 3.4 origin), bounded concurrency pools and `AbortSignal` advice.
- **No published TS-specific reviewer comment convention** beyond Google's RFC-2119 wording was found.
- **React:** the React Compiler ESLint rules and the current `eslint-plugin-react-hooks` rule names were not verified.
