import asyncio
from collections.abc import Callable
from functools import lru_cache

import httpx

_loop = None


def background_loop() -> asyncio.AbstractEventLoop:
    global _loop  # expect: R79
    if _loop is None:
        _loop = asyncio.new_event_loop()
    return _loop


@lru_cache
def station_client() -> httpx.Client:  # expect: R79
    return httpx.Client(base_url="https://weather.example/api")


_READINGS: dict[str, list[float]] = {}  # expect: R79


def record(station: str, celsius: float) -> None:
    _READINGS.setdefault(station, []).append(celsius)


http = httpx.Client(timeout=10)  # expect: R79

_PARSERS = {}  # expect: R79


def parser(fmt: str) -> Callable:
    def register(fn: Callable) -> Callable:
        _PARSERS[fmt] = fn
        return fn

    return register


class _Holder:
    conn = None


_holder = _Holder()


def connection():
    if _holder.conn is None:
        _holder.conn = open_archive("readings.db")  # expect-llm: R79
    return _holder.conn
