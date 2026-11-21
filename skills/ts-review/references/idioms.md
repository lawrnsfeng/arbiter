# TypeScript idioms

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

## Community review practice

| Venue | Practice | Source |
|---|---|---|
| Google | Guide states that annotations on complex expressions and return types are **decided by the code reviewer** ("Reviewers *may* ask for annotations…"). Unsafe assertions need a justifying comment. Conformance (tsetse, tsec) is mandatory | GTS §Type inference, §Return types, §Conformance |
| Google | Consistency policy: match the file's style; don't reformat existing code in unrelated changes | GTS §Policies (section header seen; body not read) |
| DefinitelyTyped | "Common mistakes" checklist is the reviewer bar: follow HB-DD; `ReadonlyArray` for non-mutated params; no return-only generics; no `Function`/`Object`; no `string \| any`. Package-wide lint disables are rejected ("harder to review"); use per-line disables. Owners' reviews weigh more with the mergebot; every PR is reviewed by a TS/DT team member. tsconfig must enable `noImplicitAny`, `noImplicitThis`, `strictNullChecks`, `strictFunctionTypes` | DT |
| typescript-eslint | PRs only for `accepting prs` issues. No force-push after opening (breaks incremental review). Line comments so threads resolve. Re-request review after addressing. Aim for 100% coverage; valid+invalid cases, one error per invalid case. Conventional-commit PR titles `<type>(<package>): …`. Separate AI contribution policy | TSE-PR |
| microsoft/TypeScript | Team does not review PRs for changes not pre-approved (issue must be accepted/milestoned) | https://raw.githubusercontent.com/microsoft/TypeScript/main/CONTRIBUTING.md (lines 18, 63, 66) |
| React | Treat Rules of React as rules ("if they are broken, your app likely has bugs"), enforced by the ESLint plugin + StrictMode | R-RULES |
| Comment conventions | `Nit:` / `Optional:` prefixes come from Google eng-practices (covered elsewhere). No TS-specific convention found beyond the RFC-2119 wording in GTS | GTS §Terminology |
