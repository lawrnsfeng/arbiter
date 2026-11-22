# TypeScript severity guidance

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
