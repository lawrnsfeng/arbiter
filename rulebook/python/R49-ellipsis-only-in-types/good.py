from collections.abc import Callable


def run_steps(steps: tuple[str, ...], on_step: Callable[..., None]) -> tuple[int, ...]:
    timings: tuple[int, ...] = ()
    for step in steps:
        on_step(step)
    return timings


class Oven:
    def preheat(self, celsius: int) -> None:
        raise NotImplementedError("each oven model heats differently")


def first_layer(cake_grid):
    return cake_grid[..., 0]  # array indexing is a subscript, not a body


def loading_label() -> str:
    return "..."  # a string, not the Ellipsis object
