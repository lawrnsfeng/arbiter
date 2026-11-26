---
id: R18
title: Raw dicts from an I/O boundary become a typed dataclass at the read point
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler: Encapsulate Record, Python docs dataclasses, Alexis King: Parse, don't validate
---
## Rule

- A raw dict that comes from an I/O boundary (JSON, TOML/YAML, an HTTP response body, a database driver) is converted to a typed dataclass immediately at the read point. (C1)
- A plain dict is allowed only at the exact read point: inside the conversion pair (e.g. `from_record` / `to_record`) that turns it into the dataclass and back. (C2)
- Indexing such a dict by a string key anywhere after domain code takes over, outside the conversion pair, is a violation. (C3)
- Domain code uses attribute access on the dataclass (e.g. `reading.celsius`). (C4)

## Incorrect

- `raw = json.load(fh)` then `raw["readings"]` in the same function.
- `json.loads(blob)["station"]["name"]`: indexing the reader call's result directly.
- `settings = tomllib.loads(text)` then `settings.get("threshold", 30)`.
- `reply = session.get(url).json()` then `reply["latest"]`.
- A domain helper indexing a dict it received as a parameter, `reading["wind_kph"]` (model only).

## Correct

- `Reading.from_record(raw)` / `reading.to_record()` conversion pair; domain code reads `reading.celsius`.
- Look-alikes: string-key indexing of a dict the function built itself; an integer index into a parsed JSON list.

## Detection

`check.py` reports, per function (and at module level), each string-key subscript `x["k"]` and each `x.get("k", …)`
whose target is either a call to a known reader (`json.load(s)`, `tomllib.load(s)`, `yaml.load`/`safe_load`,
`toml.load(s)`, a no-argument `.json()` on a response) or a name assigned from such a call in the same function.
Functions whose name starts with `from_`, `as_` or `to_` are the conversion pair and are skipped (C2). Covers C3 for
dicts read and indexed in one scope.

## LLM scan

Follow raw dicts the detector cannot track: one returned or passed from the reading function into domain code, an
element of a raw list (`for r in raw["readings"]: r["celsius"]`), a row from a database driver or `csv.DictReader`,
a parameter annotated `dict`/`Mapping`/`Any` that carries parsed I/O data. Flag string-key access on them outside the
conversion pair (C3) and propose the dataclass with its `from_record`/`to_record` pair (C1, C4). Do not flag dicts that are
genuinely dynamic maps (keys are data, e.g. counts per station), `**kwargs`, or dicts built in-process and never read
from I/O.
