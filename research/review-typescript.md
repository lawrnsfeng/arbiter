# TypeScript Code Review: Language-Specific Canon

Scope: idiom, clean code, API/type design for TypeScript (+ brief React). Generic review process lives elsewhere.
Citation keys → URLs in §1. `[from memory]` = not verified this session. Research date 2026-11-21.

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

## 2. Tool-enforced layer (reviewer stays silent on these)

### 2a. Compiler (`tsconfig.json`)
| Flag | Catches | Source |
|---|---|---|
| `strict` (default `true` in TS 7) | implicit any, null misuse, unsound function params, untyped `this`, uninitialized class fields | TT-TSC, TS7 |
| `noUncheckedIndexedAccess` | adds `undefined` to index-signature and array reads | TSC-noUncheckedIndexedAccess; TT-TSC says it "should *really* be included in `strict`" |
| `exactOptionalPropertyTypes` | treats `prop?: T` as "absent", not "`T \| undefined`" | TSC-exactOptionalPropertyTypes |
| `verbatimModuleSyntax` | WYSIWYG imports: imports marked `type` are dropped, all others are kept; replaces `importsNotUsedAsValues` and `preserveValueImports` | TSC-verbatimModuleSyntax, TT-TSC |
| `isolatedDeclarations` (5.5) | exports must carry enough annotation for other tools to emit `.d.ts`; enables parallel declaration emit | TSC-isolatedDeclarations, TS7 |
| `erasableSyntaxOnly` (5.8) | bans enums, namespaces with runtime code, parameter properties, `import =` and `export =` | TS58 |
| `noImplicitOverride` | requires the `override` keyword | TT-TSC |
| `isolatedModules`, `moduleDetection: force` | per-file transpile safety | TT-TSC |

TT-TSC calls `noImplicitReturns`, `noUnusedLocals`, `noUnusedParameters` and `noFallthroughCasesInSwitch` noisy and optional. Do not demand them.

### 2b. typescript-eslint (✅ recommended, 🔒 strict, 🎨 stylistic, 💭 needs type info) [TSE-RULES]
| Theme | Rules |
|---|---|
| `any` leakage | `no-explicit-any` ✅; `no-unsafe-argument`, `-assignment`, `-call`, `-member-access`, `-return` ✅💭; `no-unsafe-type-assertion` (no preset) 💭; `no-unsafe-function-type` ✅; `no-wrapper-object-types` ✅; `no-empty-object-type` ✅ |
| Promises | `no-floating-promises` ✅💭; `no-misused-promises` ✅💭; `await-thenable` ✅💭; `require-await` ✅💭; `return-await` 🔒💭; `promise-function-async` (no preset); `prefer-promise-reject-errors` ✅💭 |
| Errors | `only-throw-error` ✅💭; `use-unknown-in-catch-callback-variable` 🔒💭 |
| Assertions | `no-non-null-assertion` 🔒; `no-unnecessary-type-assertion` ✅💭; `consistent-type-assertions` 🎨; `non-nullable-type-assertion-style` 🎨💭; `no-non-null-asserted-optional-chain` ✅ |
| Conditions | `no-unnecessary-condition` 🔒💭; `strict-boolean-expressions` (no preset) 💭; `prefer-nullish-coalescing` 🎨💭; `prefer-optional-chain` 🎨💭 |
| Exhaustiveness | `switch-exhaustiveness-check` (no preset) 💭 |
| Imports and modules | `consistent-type-imports` (no preset, autofix); `consistent-type-exports` 💭; `no-import-type-side-effects`; `no-namespace` ✅; `no-require-imports` ✅; `triple-slash-reference` ✅ |
| Generics | `no-unnecessary-type-parameters` 🔒💭; `no-unnecessary-type-constraint` ✅ |
| Classes | `no-extraneous-class` 🔒 (classes used as namespaces); `prefer-readonly` (no preset) 💭; `prefer-readonly-parameter-types` (no preset) 💭 |
| Enums | `no-mixed-enums` 🔒💭; `prefer-literal-enum-member` 🔒; `no-unsafe-enum-comparison` ✅💭 |
| Misc | `ban-ts-comment` ✅; `no-deprecated` 🔒💭; `restrict-template-expressions` ✅💭; `restrict-plus-operands` ✅💭; `unbound-method` ✅💭; `no-base-to-string` ✅💭; `no-misused-spread` 🔒💭; `require-array-sort-compare` (no preset) 💭; `naming-convention` (no preset) 💭 |

- **Presets [TSE-CFG]:** use `strict-type-checked` plus `stylistic-type-checked` when the team is TS-proficient. `strict*` and `all` are not semver-stable. No preset enables formatting rules; Prettier or an equivalent handles formatting.
- **Notable defaults:**
  - `strict-boolean-expressions` allows `string`, `number` and nullable objects. It rejects nullable boolean, string and number, and `any` [TSE-SBE].
  - `no-floating-promises` accepts `void p` (`ignoreVoid: true`). Voiding marks intent only; a rejection stays unhandled [TSE-NFP].
  - `switch-exhaustiveness-check` defaults to `considerDefaultExhaustiveForUnions: false`, so a `default:` branch does not hide a missing union member [TSE-SEC].

### 2c. Alternatives
- **Biome [BIOME, BIOME-CMP]:**
  - 816 rules. Names use camelCase `use*`/`no*` (ESLint `eqeqeq` becomes `noDoubleEquals`). Diagnostics separate safe from unsafe fixes. The formatter matches Prettier output in 97% of cases.
  - Type-aware rules (v2+, e.g. `noFloatingPromises`) use Biome's own type inference, not `typescript`. Coverage is "considerably smaller" than typescript-eslint's.
  - Plugins are written in GritQL; Biome cannot run ESLint JS plugins.
- **Oxlint [BIOME-CMP]:** `oxlint-tsgolint` is built on typescript-go and "includes most of typescript-eslint's type-aware rules".
- **React [R-RULES, R-HOOKS]:** `eslint-plugin-react-hooks` plus `<StrictMode>`.
- **Declarations [DT]:** dtslint and `@arethetypeswrong/cli` check published `.d.ts`.

### 2d. What tools CANNOT catch (reviewer's job)
- Whether the types model the domain: valid-states-only, unions vs flag bags, brands for IDs and units [ET29, ET64].
- Whether an `as` or `!` is actually justified, and whether the justifying comment is true [GTS].
- Missing runtime validation where outside data enters. `JSON.parse`, `fetch().json()` and `req.body` all type as `any` or `unknown`, and a cast passes lint once `unknown` is used [ET74].
- User-defined type guards (`x is T`) and assertion functions whose body does not prove the claim. Tools trust the signature [HB-NAR], [ET45].
- API surface: export minimality, return-only generics, overload shape. Only `unified-signatures` is partially mechanized.
- Error-strategy consistency: throw vs `Result`, whether `cause` is chained, error granularity.
- Async semantics: sequential `await` in loops that should run in parallel, missing cancellation/`AbortSignal`, races, unbounded `Promise.all`.
- Mutation of shared or argument data that `readonly` does not cover (deep structures, `Map`/`Set` contents).
- Barrel-file and module-boundary architecture; accidental circular imports.
- Naming quality, domain vocabulary, comment value [GTS], [CCJS].
- React: effect misuse (derived state in effects), the wrong state shape, key-based resets [R-EFFECT]. The hooks lint catches only call-site rules.

## 3. Idiom checklist (reviewer-only)

| Area | Flag | Don't flag (exception) | Source |
|---|---|---|---|
| Naming | Ambiguous abbreviations, letters deleted inside words, Hungarian prefixes (`kFoo`), `customerID` instead of `customerId` | Short names in scopes of ≤10 lines that are not exported API; well-known acronyms (DNS, URL, Id) | GTS §Descriptive names |
| Naming | Same concept with several names (`getUserInfo`/`getClientData`/`getCustomerRecord`); type or field repeats its context (`Car.carColor`) | — | CCJS |
| Naming | `_` prefix on a used identifier, or used for "private" | `_` / `_name` for syntactically required unused params; `using _cleanup = …` | GTS §Underscore |
| Naming | Type names not in domain language (`Data`, `Info`, `Obj`) | — | ET Item 41 |
| Errors | `throw 'str'`, `Promise.reject('x')`, `abort('reason string')` | — (lint covers throw and reject only; **`AbortController.abort(string)` is reviewer-only**) | GTS §Only throw errors |
| Errors | Rethrow that loses the original error | `new Error(msg, {cause: e})` | GTS, MDN-CAUSE |
| Errors | `new Error('x', e)`: an Error passed as ErrorOptions. Type-checks, almost surely a bug | — | GTS §ErrorOptions |
| Errors | Non-Error `cause` | Deliberate structured data in `cause` (`{code, values}`) when documented. MDN allows it, GTS forbids it; follow the repo | MDN-CAUSE vs GTS |
| Errors | Empty `catch` without a comment explaining why | Commented intentional fallthrough | GTS §Empty catch, CCJS |
| Errors | `try` blocks wrapping non-throwing lines (hides which call throws) | `try` around a whole loop for perf | GTS §Keep try blocks focused |
| Errors | Defensive `typeof e === 'string'` branches in catch | When the API is known to throw non-Errors, with a comment naming it | GTS §Catching and rethrowing |
| Errors | Mixed strategies in one module (some functions throw, siblings return `{error}`) | Consistent `Result<T,E>` / discriminated-union returns in codebases that chose them. GTS prefers exceptions; follow the repo | GTS §Exception handling |
| Errors | Multiple independent failures collapsed into the first | `AggregateError`; `SuppressedError` for errors during cleanup | MDN-CAUSE, TS52 |
| Resources | Manual cleanup duplicated on every early return; cleanup missing on throw | `using` / `await using` with `Disposable`/`AsyncDisposable`; `try/finally` where the target lacks `using` | TS52 |
| Resources | Listeners, timers or subscriptions with no teardown (effect, class, module) | — | R-EFFECT (cleanup), [from memory] general |
| API design | Overloads differing only in trailing params or one param's type | Return type differs by input → overloads (or conditional types, ET Item 52) | HB-DD |
| API design | General overload before specific | — | HB-DD |
| API design | Callback param marked optional "because caller may ignore it"; callback return typed `any` | `() => void` callbacks | HB-DD |
| API design | Return-type-only generics (`parse<T>(s): T`) = disguised assertion | `new Map<string, number>()`; identity-style `<T>(x: T): T` | GTS §Return type only generics, DT, ET Item 51 |
| API design | ≥3 positional params, boolean flag params, adjacent params of the same type (`(from: string, to: string)`) | Options object with destructuring; branded types for same-typed params | CCJS, ET Item 38 |
| API design | Function compromises its own signature to silence an internal error | Unsafe cast hidden inside a well-typed function with a comment | ET45 |
| API design | Accepts narrow, returns loose (e.g. returns `T \| undefined` everywhere, takes only `T[]`) | "Liberal in what you accept, strict in what you produce": `Iterable`/`readonly T[]` in, concrete out | ET Item 30, DT (`ReadonlyArray` for non-mutated params) |
| API design | Types used in the public API but not exported | — | ET Item 67 |
| Types | `any` outside migration code; `string \| any` (collapses to any) | `unknown` for opaque values; `any` in a narrow, commented scope | HB-DD, DT, ET Items 43–46 |
| Types | `Function`, `Object`, `{}`, `String`/`Number`/`Boolean` | `object`, `unknown`, `Record<string, T>`, explicit function types | HB-DD, GTS §{} Type, DT |
| Types | `x as Foo` / `y!` with no runtime check or comment | Comment stating why it holds; obvious context (e.g. proto fields) | GTS §Type assertions |
| Types | `{...} as Foo` on object literals (no excess-property check) | `const x: Foo = {...}` or `satisfies Foo` | GTS, ET Item 9, TS49 |
| Types | Double assertion via `any` or `{}` | `as unknown as T` with a comment | GTS §Double assertions |
| Types | Type guard `(x): x is T` with a weak body (checks one field only); assertion fn (`asserts x is T`) that doesn't throw on every mismatch | Guards backed by a schema (`v.is`, zod `safeParse`) | HB-NAR, VALI |
| Types | Annotation that widens a config object (`const routes: Record<string, Route> = {...}` loses keys) | `satisfies Record<string, Route>` keeps the literal type and validates it | TS49 |
| Types | Mutable literal where a fixed set is meant (`const ROLES = ['a','b']` typed `string[]`) | `as const` + `typeof ROLES[number]` | TS49 / [from memory] `as const` (TS 3.4) |
| Types | New `enum` (esp. numeric: reverse mapping, accepts any number), mixed enums | String-literal union or `as const` object; existing string enums when the repo has no `erasableSyntaxOnly`. GTS allows plain `enum` and bans `const enum` | TT-ENUM, TS58, GTS §Const enums |
| Types | Complex mapped/conditional types where an interface `extends` would do | Type-level code that removes real duplication and has type tests | GTS §Mapped and conditional types, ET Items 15, 55 |
| Types | `\|null`/`\|undefined` baked into a type alias | Add nullability at the use site | GTS §Nullable aliases, ET Item 32 |
| Types | Sentinel values (`-1`, `""`) meaning "absent" | `null` / a distinct type | ET Item 36 |
| Types | `interface` vs `type` choice | **Don't flag.** GTS: interface for object shapes; TT-TVI: `type` by default, `interface extends` for inheritance. Follow `consistent-type-definitions` | GTS, TT-TVI |
| Data modeling | Bag of flags/optionals encoding a state machine (`isLoading`, `error?`, `data?`) | Discriminated union keyed on a literal tag | ET29, ET Item 34 |
| Data modeling | Many optional props in a domain type | Separate types per variant; optional only where truly optional | ET Item 37 |
| Data modeling | Primitive IDs/units interchangeable (`userId: string`, `ms: number`) | Brands: `string & {_brand:'UserId'}` or `unique symbol`, built only via a validating function | ET64 |
| Data modeling | `string` where a closed set exists | Literal unions / template-literal types | ET Item 35, 54 |
| Data modeling | Object-as-map with dynamic keys | `Map`/`Set`; or `Record<K,V>` for a known key set | GTS §Indexable types, ET Item 16 |
| Data modeling | Exhaustiveness relies on `default:` alone | `default: { const _x: never = v; throw … }` or `satisfies never`. Keep `default` when values may come from a newer server version | HB-NAR, TSE-SEC, ET Item 59 |
| Trust boundary | `JSON.parse`, `fetch().json()`, `req.body`, `process.env`, `localStorage`, `postMessage` data cast with `as` | Schema parse (zod `parse`/`safeParse`, valibot `parse`/`safeParse`/`is`) at the edge; types inferred from the schema (`z.infer`, `v.InferOutput`) | ET74, ZOD, VALI |
| Trust boundary | Hand-written interface and schema kept separately (drift) | One source of truth: schema→type or spec→codegen | ET74, ET Item 58 |
| Concurrency | `await` inside a `for` over independent work | `Promise.all` / `allSettled`; bounded pool for large N | [from memory] common idiom; TSE-NFP lists combinators |
| Concurrency | `Promise.all` where partial failure must be reported | `Promise.allSettled` | TSE-NFP (lists it) |
| Concurrency | `void promise` to silence the linter where the failure matters | `.catch(handler)` or `await` | TSE-NFP §ignoreVoid |
| Concurrency | Async fn passed where a `void` callback is expected (event handler, `forEach`) | Wrap: `onClick={() => { void save().catch(report) }}`; `for…of` + `await` | TSE-NMP |
| Concurrency | Long-running async with no cancellation | Accepts `AbortSignal` | [from memory] |
| Concurrency | Callbacks/`.then` chains in new code | `async`/`await` (better type flow) | ET Item 27, CCJS |
| Mutability | Fields never reassigned but not `readonly` | — (mechanizable via `prefer-readonly` only if on) | GTS §Use readonly, ET Item 14 |
| Mutability | Function mutates array/object args | `readonly T[]` / `Readonly<T>` params; return new values | ET Item 14, DT, CCJS §Avoid side effects |
| Mutability | `export let` / mutable module state | Getter function | GTS §Mutable exports |
| Mutability | Mutating props, state or values after passing them to JSX or hooks | Copy-on-write | R-RULES |
| Modules | `default` exports in app code | Named exports (canonical name, import errors on typos). Framework-mandated defaults (Next.js pages etc.) are fine | GTS §Exports |
| Modules | Exporting internals "for tests" | Minimal surface | GTS §Export visibility |
| Modules | Static-only container classes; `namespace`; `require`; `/// <reference>` | File = namespace; ES imports | GTS §Container classes, §Use modules not namespaces |
| Modules | New internal barrel (`index.ts` re-exporting a folder), especially nested barrels | Package entry points of published libraries | ATL |
| Modules | `import()` inside type positions | `import type` | GTS §Dynamic import type |
| Classes | Parameter properties / `#private` | Follow repo: GTS prefers parameter properties and TS `private`; `erasableSyntaxOnly` bans parameter properties; ET Item 72 "prefer ECMAScript features" | GTS, TS58, ET |
| Classes | Getter/setter pairs with no logic; classes with only static members | Plain properties; module functions | GTS, ET blog "Don't write traditional getters/setters" |
| Classes | Inheritance for code reuse | Composition | CCJS §Prefer composition |
| Testing | `@ts-ignore`/`@ts-expect-error` to "fix" types | `@ts-expect-error` in tests for negative type cases, with a description | GTS §@ts-ignore, TSE `ban-ts-comment` |
| Testing | `try { f(); fail() } catch {}`: catches the `fail` | `expect(() => f()).toThrow()` / `assertThrows` | GTS §Empty catch |
| Testing | Complex generic types without type tests | `expectTypeOf`, `tsd`, `@ts-expect-error` assertions | ET Item 55 |
| Testing | Several concepts per test | One concept per test | CCJS §Testing |
| Docs | JSDoc repeating types (`@param {string}`) | TSDoc prose; types stay in signatures | ET Item 31, 68 |
| Docs | Undocumented exported symbols; comments restating code | Doc all top-level exports; comments that add information | GTS §Document all top-level exports |
| Docs | Commented-out code, journal comments, positional banners | — | CCJS §Comments |
| Performance | Intersections (`A & B`) for object inheritance in hot type paths | `interface B extends A` (cached by name) | TT-TVI |
| Performance | Deep recursive/conditional types slowing the editor | Tail-recursive types; codegen | ET Items 57, 58, 78 |
| Performance | Barrel imports pulling large graphs into tests/TS server | Direct imports | ATL (75% fewer build minutes; 88% fewer unit tests run) |
| Performance | Premature micro-optimisation | — | CCJS §Don't over-optimize |
| Security | `eval`, `new Function`, `innerHTML` with dynamic data, `with` | Framework escaping; Trusted Types | GTS §Dynamic code evaluation, §Conformance (tsec) |
| Security | Unvalidated external data narrowed by cast (see Trust boundary) | Schema parse | ET74 |
| Security | Modifying built-ins/prototypes; monkey patching | Module augmentation | GTS §Modifying built-in objects, ET Items 47, 71 |
| React | Hooks in conditions, loops, after early return, in handlers, in `try`, in `useMemo` callbacks | Top level of components and custom hooks | R-HOOKS |
| React | Derived data stored in state and synced via `useEffect`; resetting state in an effect on prop change | Compute during render; `useMemo` if measured ≥~1ms; `key` to reset | R-EFFECT |
| React | Event-specific logic in effects | Event handlers | R-EFFECT |
| React | Calling components as functions; passing hooks as values | JSX; call hooks directly | R-RULES |
| React | Manual `useMemo`/`useCallback` everywhere | Fine when React Compiler is on; it memoizes automatically | R-EFFECT note |

## 4. Design patterns & architecture

| Classic pattern | Verdict in TS | Native replacement | Source |
|---|---|---|---|
| State | Class hierarchy anti-idiomatic for data | Discriminated union + exhaustive `switch` / handler map `Record<Tag, Fn>` | ET29, HB-NAR |
| Strategy / Command | Interface + N classes is often overkill | Function types / object of functions; `satisfies Record<K, Handler>` to keep keys | TS49, [from memory] |
| Singleton | Anti-idiomatic class | ES module scope (a module evaluates once) | GTS §Container classes |
| Static utility class | Anti-idiomatic | Exported functions | GTS, TSE `no-extraneous-class` |
| Factory | Fine as plain functions; return interface types | Factory function + private constructor or brand for invariants | ET64 |
| Builder | Usually unneeded | Options object with defaults/destructuring; method chaining OK | CCJS §Use method chaining, §Function arguments |
| Visitor | Replaced | Exhaustive switch over a union tag | ET Item 59 |
| Template method / inheritance | Discouraged | Composition, higher-order functions | CCJS §Prefer composition |
| Observer | OK | Typed `EventTarget`/emitter; teardown via `Disposable`/`using` | TS52 |
| Decorator (GoF) | OK as wrappers | — **TS `@decorators`:** GTS forbids defining new ones (framework ones only) | GTS §Decorators |
| Adapter / anti-corruption layer | Encouraged at boundaries | Schema-validated mapping from external DTO to domain type | ET74, ET Item 70 (mirror types) |
| Nominal value object | Needed due to structural typing | Branded types | ET64 |
| Namespaces / enums as modules | Avoid | Modules; `as const` objects | GTS, TT-ENUM, TS58 |

Layering and package structure:
- **Folders and files.** One concept per file; file scope is the namespace. Use named exports and a minimal export surface [GTS].
- **Validation at the edges.** Parse at the I/O edge into domain types. The interior trusts types and pushes null to the perimeter [ET74, ET Item 33].
- **Barrels.** Avoid internal barrels in apps and monorepos. Keep a single entry point (`package.json#exports`) for published libraries [ATL].
  - Path aliases: prefer `package.json#imports` over `tsconfig paths` when running under type stripping or `erasableSyntaxOnly` [TT-ESO].
- **Library builds.** Use `declaration`, `composite` and `declarationMap` in monorepos [TT-TSC]. `isolatedDeclarations` lets builds parallelize [TS7].
- **Type-only edges.** Use `import type` / `export type` so bundlers and type-strippers can erase them [GTS, TSC-verbatimModuleSyntax].

## 5. Language-specific smells → refactoring

| Symptom | Refactoring | Source |
|---|---|---|
| `isLoading && !error && data!` scattered checks | Model as a `{state:'pending'}\|{state:'error',error}\|{state:'ok',data}` union | ET29 |
| `as SomeType` on `res.json()` | Schema parse; `z.infer` the type | ET74, ZOD |
| Cast repeated at every call site | One well-typed wrapper hides the single cast | ET45 |
| Exported `function f(): any` / leaking `any` | Return `unknown` or a concrete type; narrow inside | HB-DD, ET Item 46 |
| `if (x)` on `number \| undefined` / `string \| null` | `x != null` / `x ?? default` | TSE-SBE, HB-NAR |
| `a \|\| b` where `0`/`""` are valid | `a ?? b` | TSE `prefer-nullish-coalescing` |
| `switch` over a union with a silent `default` | Explicit cases + `never` check | HB-NAR, TSE-SEC |
| Numeric enum | `as const` object + `(typeof X)[keyof typeof X]` union | TT-ENUM, TS58 |
| `const enum` | Plain union / enum (GTS) | GTS |
| `function get<T>(k): T` | Accept a schema/decoder param, or return `unknown` | DT, GTS |
| Nested `if` type checks on params (`typeof x === 'string'` everywhere) | Union param narrowed once, or overload-free union design | CCJS §Avoid type-checking, HB-DD |
| `Pick<User,'a'\|'b'>` chains hard to read | Named interface + `extends` | GTS §Mapped types |
| Many optional fields "for flexibility" | Split into variant types | ET Item 37 |
| `class Utils { static … }` | Module functions | GTS |
| `export default` | Named export | GTS |
| `index.ts` re-exporting a folder | Direct imports; delete the barrel | ATL |
| `try { … whole function … } catch {}` | Narrow `try`; handle or rethrow with `cause` | GTS |
| `for (…) await work(i)` on independent work | `await Promise.all(items.map(work))` | TSE-NFP |
| `arr.forEach(async x => …)` | `for…of` + `await`, or `Promise.all(map)` | TSE-NMP |
| try/finally cleanup duplicated | `using` + `Disposable` | TS52 |
| `useEffect(() => setFull(a+b), [a,b])` | `const full = a + b` | R-EFFECT |
| `@ts-ignore` | Fix the type; else `@ts-expect-error -- reason` (tests) | GTS, TSE `ban-ts-comment` |
| `string` IDs mixed up | Brand types + smart constructor | ET64 |

## 6. How the community actually reviews

| Venue | Practice | Source |
|---|---|---|
| Google | Guide states that annotations on complex expressions and return types are **decided by the code reviewer** ("Reviewers *may* ask for annotations…"). Unsafe assertions need a justifying comment. Conformance (tsetse, tsec) is mandatory | GTS §Type inference, §Return types, §Conformance |
| Google | Consistency policy: match the file's style; don't reformat existing code in unrelated changes | GTS §Policies (section header seen; body not read) |
| DefinitelyTyped | "Common mistakes" checklist is the reviewer bar: follow HB-DD; `ReadonlyArray` for non-mutated params; no return-only generics; no `Function`/`Object`; no `string \| any`. Package-wide lint disables are rejected ("harder to review"); use per-line disables. Owners' reviews weigh more with the mergebot; every PR is reviewed by a TS/DT team member. tsconfig must enable `noImplicitAny`, `noImplicitThis`, `strictNullChecks`, `strictFunctionTypes` | DT |
| typescript-eslint | PRs only for `accepting prs` issues. No force-push after opening (breaks incremental review). Line comments so threads resolve. Re-request review after addressing. Aim for 100% coverage; valid+invalid cases, one error per invalid case. Conventional-commit PR titles `<type>(<package>): …`. Separate AI contribution policy | TSE-PR |
| microsoft/TypeScript | Team does not review PRs for changes not pre-approved (issue must be accepted/milestoned) | https://raw.githubusercontent.com/microsoft/TypeScript/main/CONTRIBUTING.md (lines 18, 63, 66) |
| React | Treat Rules of React as rules ("if they are broken, your app likely has bugs"), enforced by the ESLint plugin + StrictMode | R-RULES |
| Comment conventions | `Nit:` / `Optional:` prefixes come from Google eng-practices (covered elsewhere). No TS-specific convention found beyond the RFC-2119 wording in GTS | GTS §Terminology |

## 7. Severity guidance

| Block (must fix) | Should fix (non-blocking unless repeated) | `Nit:` / don't flag |
|---|---|---|
| Unvalidated external data cast to domain types | `interface` used where `type` is the house style (or vice versa) | `type` vs `interface` when the repo has no rule |
| `any` escaping a module boundary; `as`/`!` without a provable invariant | Missing `readonly` on never-reassigned fields | Return-type annotations on internal functions (GTS: author's choice) |
| Floating/misused promises; `forEach(async)`; voided promises whose failure matters | Default export in non-framework code | Import ordering, quotes, formatting (formatter's job) |
| Non-exhaustive handling of a union that will grow (no `never` check) | Unneeded type parameters; overloads collapsible to a union | Short names in tiny scopes |
| Swallowed errors; rethrow without `cause`; throwing non-Errors | New barrel files in app code | `Array<T>` vs `T[]` |
| Type guards/assertion functions that lie | Over-clever mapped/conditional types where an interface reads better | Existing string enums (don't churn; TT-ENUM) |
| Rules-of-Hooks violations; mutating props/state | Effects computing derived state | `useMemo` presence/absence without measurement |
| `eval`/`innerHTML` with untrusted data; prototype patching | Tests missing for new type-level code | Parameter property vs explicit field (follow tsconfig) |
| `strict: false` or TS 7-removed flags in tsconfig | `noUncheckedIndexedAccess` off in new projects | Optional strictness flags TT-TSC calls noisy |
| Public API leaks unexported types; breaking `.d.ts` changes | Enum added where a union fits | `@ts-expect-error -- reason` in tests |

Rule of thumb: block if the issue breaks soundness, data integrity, error propagation or the public contract. A rule that the repo's linter would enforce if enabled is a config suggestion, not a review comment.

## 8. Gaps

- **Effective TypeScript:** only the 83 item titles and samples for Items 29, 45, 64 and 74 were opened; other item claims rest on titles. The book text is paywalled.
- **Total TypeScript:** the "Cursor rules" page (Result types etc.) is gated; its body was not visible. Pocock's specific Result-pattern guidance is unverified. Result-type guidance here otherwise rests on general practice `[from memory]`.
- **Google guide:** I read the Policies/Consistency body only as a heading.
- **TS 7.1 beta and its API:** seen only in search snippets (InfoQ, GitHub releases). typescript-eslint's TS 7 support status is beyond the TS7 blog's alias advice: unverified (issue #10940 not opened).
- **Biome:** its exact list of type-aware rules was not opened.
- **`isolatedDeclarations`:** I did not open its 5.5 release-note details.
- **From memory:** `as const` (TS 3.4 origin), bounded concurrency pools and `AbortSignal` advice.
- **No published TS-specific reviewer comment convention** beyond Google's RFC-2119 wording was found.
- **React:** the React Compiler ESLint rules and the current `eslint-plugin-react-hooks` rule names were not verified.