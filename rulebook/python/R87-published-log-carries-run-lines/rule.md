---
id: R87
title: A published log section carries the run's own lines, and its producer can emit them
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs logging (logger hierarchy, effective level, lastResort WARNING), Python Logging HOWTO, pytest docs caplog
---
## Rule

- A published LOG section carries lines the run itself produced; an empty published log section is a violation. (C1)
- Both halves hold: the test writes the log file the report reads, and the producer emits the line. (C2)
- A log assertion reads only the lines produced for the scenario under test: it slices from a byte-offset mark taken before the action. (C3)
- Publish exactly that slice; copying the whole log file is a violation. (C4)
- The producer's logger level is set explicitly, not inherited (a bare module logger inherits the root's WARNING and drops INFO). (C5)
- The producer's level is configurable, so an environment that does not read the log can silence it. (C6)
- A suite whose log section is evidence sets (pins) that level itself rather than inheriting it from the ambient environment. (C7)

## Incorrect

- A test copying the service's whole log file into the evidence folder with `shutil.copy`.
- A fixture writing `log_path.read_text()` wholesale into the artifact file.
- A test using `shutil.copyfile` on the log after the scenario.
- A test reading the whole log into a local, asserting on it (C3, model only), then writing that local to the artifact.
- A producer module logging at INFO through a bare `getLogger(__name__)` with no level (model only).
- A scenario that asserts lines but never writes the file the report reads (model only).

## Correct

- A test pinning the producer's level through the producer's explicit `configure_*_logging(level)` hook, marking the log's byte size before the action, reading only the bytes added since, asserting one line per event, and writing exactly that slice to the report's log file.
- Look-alikes: copying fixture files (a CSV, a logging config, an access log used as input) into `tmp_path`; `copy.copy` of a list named `log_lines`.

## Detection

In test code (a module named `test_*.py`, `*_test.py` or `conftest.py`, or a function named `test*` or decorated as a
fixture), `check.py` reports whole-file publication of a log (C4): a `shutil.copy`/`copy2`/`copyfile`/`copyfileobj`
(or a bare `copy2`/`copyfile`/`copyfileobj`) whose source is a log file and whose destination is a published place,
and a `write_text`/`write_bytes` into a published place whose argument is a log file's `read_text()`/`read_bytes()`,
directly or through a local bound to it. A log file is a string ending `.log`, or a name/attribute containing `log` and
ending in `log`/`path`/`file`/`location`/`filename` (`log_path`, `service_log`), so `log_config.yaml` and `log_lines`
are not. A published place is a destination naming `evidence`, `artifact(s)`, `report(s)`, `publish(ed)`, `results` or
`outputs`, so copying a log fixture into `tmp_path` is not. C3 (assertions read only the slice since a mark) is the
model's.

## LLM scan

- For each published report or evidence artifact with a LOG section, check the test writes the file the report reads
  (C2) and that the section cannot be empty for a passing scenario (C1).
- Report every log assertion that reads the whole file instead of the bytes since a mark taken before the action (C3),
  whether or not the file is published, and whole-file publication the detector misses (open/read/write loops, `cat`,
  archive copies) (C4).
- For each producer whose lines are evidence, check its logger level is set explicitly (C5), configurable (C6), and
  pinned by the suite that publishes the evidence rather than inherited from an ambient setting (C7).
- Dismiss copies of logs that are test inputs (a fixture copied into a temporary directory) rather than published
  evidence; report whole-log copies into any published destination the detector's word list misses (C4).
- Do not flag logs that are never asserted on nor published, or copies of files that are not logs.
