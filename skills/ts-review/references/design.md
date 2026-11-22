# TypeScript design and smells

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
