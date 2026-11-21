---
id: A5b
output: findings
refs: [{"file": "security.md", "section": "Supply chain"}]
---
# A5b supply chain
## Mission
Find risky new or updated dependencies and build or CI changes in the manifests, lockfiles and workflows this change touches.
## Axes
`deps` (research-axes.md §2c axis 19); `security` with a CWE for build-time code execution or CI secret exposure (research-security.md §4, design implication 12).
## Read these language references
`security.md` section Supply chain (appended below).
## Checklist
1. For each added or bumped dependency in a manifest: is it used by the added code (grep its import name)? An unused new dependency is a finding.
2. Does the lockfile agree with the manifest? A manifest change without the lockfile update, or a lockfile change with no manifest reason, is a finding.
3. Name risk: typosquat-like names near a popular package, or a package name no code imports (S28: 5.2–21.7% of LLM-suggested packages do not exist). Report only what you can show from the files.
4. Exotic sources: git URLs, local paths, tarball URLs, a new registry or index in `.npmrc`/`pip.conf`/`Cargo.toml`, `replace` directives, `GONOSUMDB`/`GOPRIVATE`/`GOFLAGS=-insecure` changes.
5. Build-time code: new install scripts (`preinstall`, `postinstall`), new `build.rs`, new proc-macro crates, `setup.py` side effects.
6. CI: `pull_request_target` checking out PR code, secrets passed to untrusted steps, actions pinned to a branch instead of a SHA, `permissions: write-all`.
7. Licence: a new dependency whose licence (in the lockfile or vendored metadata) conflicts with the repo's licence.
## Do not report
- Version bumps within the same major with no other signal.
- Facts you would need the network to check (registry age, CVEs); the tool layer covers those.
- Lockfile noise from a routine re-resolve.
## Proof plan hints
- E1: a measured fact: `grep -c <import>` = 0 for an unused dependency; the exact manifest and lockfile lines that disagree; the workflow line with `pull_request_target` and the checkout of `github.event.pull_request.head.sha`.
## Output
`{"findings": [...]}`; `axis` `deps` (or `security` with `cwe`, e.g. 829, 494); `trigger` names the dependency or workflow line.
