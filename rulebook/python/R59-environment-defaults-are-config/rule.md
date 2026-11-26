---
id: R59
title: Environment defaults are config, not constants
tier: ast+semantic
severity: should-fix
status: ok
refs: The Twelve-Factor App (III. Config)
---
## Rule

- Values that are merely correct for this environment (an organisation's realm, external-tool conventions, per-site ports) are configuration fields, not constants. (C1)
- They live in the package's config class with an in-code default, overridable in the config file. (C2)
- Only universal, package-owned values are statics in the constants module. (C3)
- A constant that has to be edited per site is a violation. (C4)

## Incorrect

- A gateway host name as an annotated module constant.
- A per-site port number as a module constant (model only: a port's number cannot tell a site choice from a standard one).
- An upload URL on a public host as a module constant (model only: the name and value cannot tell it from a universal address).
- A private IP address as a server constant.
- A storage bucket name as a `Final` module constant.
- A site's local timezone as a module constant (model only).

## Correct

- Universal constants: unit conversions, a file name the package owns.
- A config dataclass whose fields carry the site values as in-code defaults.
- Loopback and unspecified addresses, a URL template, and an endpoint path.
- A bare token name `URL = "url"`.
- Standard ports (`443`, `587`) and a public package index URL.

## Detection

Covers the subset of C1/C4 whose value can only be right for one site. Every module-level upper-case constant (plain or
annotated) with a prefixed name bound to a string literal without `{` template fields, where: the last name segment is
`REALM`, `REGION`, `BUCKET` or `DSN` (always chosen per deployment); or the segment is `HOST`, `HOSTNAME`, `SERVER`,
`ENDPOINT`, `URL` or `DOMAIN` and the value's host is private: a private-range IP (not loopback, unspecified or
link-local) or a name under `.internal`, `.local`, `.lan`, `.corp`, `.intranet`, `.home.arpa` or `.localdomain`. One
hit per constant. Ports, public addresses and bare host names are left to the model, which tells site choices from
universal ones (C3).

## LLM scan

Beyond the detector: read the constants modules and module-level constants and report values that are correct only
for one site, organisation or deployment — realms, account or tenant ids, timezones, paths on one machine, external
tool conventions, quotas set for one installation — whatever their name (C1, C4). Say which config class should own
the value as a field with an in-code default (C2). Report port constants whose number is a site's choice rather than a
protocol's registered port (`5432` for PostgreSQL is a standard; `8471` for one gateway is not). Do not flag
universal values the package owns (unit conversions, protocol constants such as a registered port defined by a standard, file names the package defines) (C3), test
fixtures, or values already read from configuration or the environment.
