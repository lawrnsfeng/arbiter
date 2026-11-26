---
id: R58
title: Rendering picks its construct from the taxonomy, never a loose module function
tier: ast+semantic
severity: should-fix
status: ok
refs: Jinja2 docs (Loaders, Environment.get_template), Python docs (str subclassing, property, classmethod)
---
## Rule

- An ultra-long template that needs human viewing is a jinja2 template file, loaded into a variable. (C1)
- Many things rendered with a pre-configured configuration are rendered by a renderer class. (C2)
- A trivial rendering with a string-like result is a `str` subclass with a `from_*` classmethod taking the ingredients. (C3)
- A rendering that is effectively another class's `__repr__` is a property of that class. (C4)
- Loose module-level rendering functions (e.g. `def render_x(...) -> str` writing through a global UI object) are forbidden. (C5)

## Incorrect

- A module-level `render_*` function writing through a global console and returning the captured text.
- A private `_render_*` module function joining lines.
- A module-level async `render` function.
- A `@click.command()` named `render_week` that renders inline in a loop.
- A single-statement `@click.command()` that joins f-strings itself instead of calling a renderer.
- A loose rendering function whose name does not say `render` (model only).

## Correct

- A jinja2 template file loaded once into a module variable.
- A `str` subclass with a `from_*` classmethod.
- A renderer class whose `render` method shares configuration.
- A property rendering its own class's data.
- A module check function named `renderable` (not `render_`).
- A `@click.command()` entry point named `render` that only calls a renderer.
- A command that hands over to a renderer with integer arithmetic in its arguments (`width=margin + 20`).

## Detection

Covers the name-visible part of C5: every function defined directly at module level whose name is `render` or starts
with `render_` (leading underscores allowed), unless it is decorated as a CLI command (`@click.command()`,
`@group.command()`, `@app.callback()`) whose body (docstring aside) is one statement handing over to a renderer: it calls `.render(...)`, a `from_*`
constructor or a `*Renderer`/`*Template` class, and assembles no text itself (no f-string, `%`/`+` with a string or
f-string operand, `.join` or `.format`; integer arithmetic such as `margin + 20` is not text building). A command that renders inline is reported. Methods are not reported.

## LLM scan

Beyond the detector: find module-level functions that render output under another name (`format_*`, `*_table`,
`show_*`, `print_*`, `*_text`), especially ones writing through a global UI/console object or returning assembled
display text, and report them (C5) with the construct that fits: a jinja2 template file for long human-viewed text
(C1), a renderer class when several things share configuration (C2), a `str` subclass with a `from_*` classmethod for a
short string result (C3), or a property when the output is effectively another class's `__repr__` (C4). Also report
long inline template strings that should be template files (C1). Report CLI commands that render inline (loops of print/echo calls, assembled
display text) under any name. Do not flag functions that build data rather than display text, CLI entry points
whose body only hands over to a renderer, or methods of renderer classes.
