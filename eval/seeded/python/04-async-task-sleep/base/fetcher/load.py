"""Concurrent loading of values by key."""

import asyncio
from collections.abc import Awaitable, Callable

Loader = Callable[[str], Awaitable[str]]


async def load_all(keys: list[str], loader: Loader) -> dict[str, str]:
    """Load every key concurrently and return a key -> value map."""
    values = await asyncio.gather(*(loader(key) for key in keys))
    return dict(zip(keys, values, strict=True))
