---
id: R61
title: Subprocess argv is always built by the project's command builder
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/subprocess.html#frequently-used-arguments, Fowler Refactoring "Replace Primitive with Object", owner convention
---
## Rule

- Every argv handed to a subprocess is built through the project's command-builder class (a small object that collects the program, flags, options and positional arguments and hands back the finished token sequence). (C1)
- No bare argv list or tuple literal is written at a spawn/run call site (`subprocess.run([...])`, `Popen([...])`, `check_output((...))`, `create_subprocess_exec(*[...])`, `os.exec*`/`os.spawn*`, and the like). (C2)

## Incorrect

- `subprocess.run([tar, "-czf", ...], check=True)`: argv list literal at the run site.
- `subprocess.check_output(("journalctl", ...))`: argv tuple literal.
- `subprocess.Popen(args=[...])`: literal passed by keyword.
- `asyncio.create_subprocess_exec(*[*base, ...])` and `create_subprocess_exec("rsync", "-a", src, dst)`: argv spelled out at the spawn site.
- `os.execvp(make, [make, "all"])`: literal argv to an exec call.
- `os.execlp(make, make, "catalogue")` and `os.spawnl(os.P_WAIT, convert, ...)`: argv spelled as loose arguments to the `l` forms.
- `proc.check_output([...])` through `import subprocess as proc`: an aliased module.
- (LLM) argv assembled as a local list literal one line earlier and passed by name.

## Correct

- `sp.run(Cmd(tar, "create").with_flag("-z").with_option("--file", name).with_args(folder).tokens(), check=True)`: argv from the builder, through an aliased module.
- `create_subprocess_exec(*cmd.tokens())` and `create_subprocess_exec(program, *rest.tokens())`: starred builder output.
- Look-alike: `scheduler.run([job_a, job_b])` is not a subprocess call and stays silent.

## Detection

Resolves `subprocess`, `os` and `asyncio` under any import alias (`import subprocess as sp`) and names imported from them. Reports each call to `subprocess.run/call/check_call/check_output/Popen`, `os.execv*`, `os.spawnv*` and `os.posix_spawn*` whose argv argument is a list or tuple literal (also when starred or passed as `args=`), and each call to `asyncio.create_subprocess_exec`, `os.execl*` and `os.spawnl*` that has a plain (non-starred) or starred-literal argument in its argv positions (after the program, and after the mode for `spawnl*`). Covers C2 and the call-site part of C1.

## LLM scan

- Flag argv lists built by hand away from the call site (a local `argv = [...]`, `+` concatenation, `.append` chains, `shlex.split` of a formatted string, `shell=True` with an f-string) and then passed to a spawn call: the argv must come from the project's command builder (C1).
- Do not flag argv that comes from the builder's output, or from a parameter typed as the builder's product.
- Do not flag list literals passed to methods that merely share a name with subprocess functions (`scheduler.run([...])`).
