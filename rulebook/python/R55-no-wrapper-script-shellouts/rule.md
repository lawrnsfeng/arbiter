---
id: R55
title: Never shell out to a wrapper script; build the native argv
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs subprocess (Security Considerations, Frequently Used Arguments), Bandit B602/B605
---
## Rule

- Never run a wrapper script (one whose body is a single `exec` of a binary with fixed arguments) from Python. (C1)
- Invoke the binary directly, with the explicit argv built in Python. (C2)
- Use no shell (`shell=False`). (C3)
- Capture the output of the call that runs the binary in the script's place. (C4)
- The code does not depend on the script's path or shebang; the script may stay for the user's own use, such as cron. (C5)

## Incorrect

- `subprocess.run` of a script path built from a scripts directory.
- A `.sh` file run through `bash`.
- A command string with `shell=True`.
- `check_output` of a variable named as a script path.
- `os.system` with a command string.
- A script run through `bash` behind `/usr/bin/env`, with `capture_output=False`.
- A native argv that replaced a wrapper script but leaves output uncaptured (model only).
- A binary path constant that is in fact a wrapper script (model only).

## Correct

- The binary called directly with an argv built in Python (through the project's command builder) and `capture_output=True` (or `stdout=`/`stderr=` pipes).
- `check_output`, which captures by itself.
- Reading a script's text without running it.
- An interactive editor run without capturing (it is not replacing a script).
- `/usr/bin/env LANG=C git ...` and an argument whose name merely contains the letters `script` (`transcript_dir`).

## Detection

Covers C1 (script-shaped commands), C2, C3, and C4 on those calls, for `subprocess.run/call/check_call/check_output/
Popen` and `os.system/os.popen`. One hit per call listing every problem: `shell=True` (C3); an argv list whose program
(after an `env` prefix and its `NAME=value` / option arguments) is a shell interpreter (`bash`, `sh`, ...), a `*.sh`
/ `./x` literal, or an expression with an identifier word `script`/`scripts` or a `*.sh` string (C1, C5); an argv
given as one string or f-string (C2). When a `run`/`call`/`check_call` already has one of these problems, a missing
capture is added: no `capture_output` or `stdout`, or `capture_output=False` / `stdout=None` (C4). Every
`os.system`/`os.popen` call (C3).

## LLM scan

Beyond the detector: for every subprocess call whose program is a path or constant without "script" in its name,
check whether the target is a wrapper script — a file in the repository or a path documented as a shell script whose
body only `exec`s another binary with fixed flags (C1). Report it with the binary and flags to call instead (C2), and
report code that relies on a script's location or shebang (C5). For a call that replaces a wrapper script, check its
output is captured (C4). Do not flag calls of real binaries (`git`, `gzip`,
`convert`) with list argv and captured output, interactive programs the user must see (editors, pagers), and do not ask to delete the script itself: it may stay for the user's
own cron.
