# TypeScript tool-enforced layer

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
