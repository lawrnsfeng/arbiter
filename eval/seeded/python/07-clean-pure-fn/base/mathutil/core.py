"""Small numeric helpers."""


def lerp(start: float, end: float, t: float) -> float:
    """Return the point `t` of the way from `start` to `end`."""
    return start + (end - start) * t
