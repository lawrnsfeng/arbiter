from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum
from functools import cache, lru_cache
from typing import ClassVar

import httpx
from fastapi import FastAPI

FREEZING_C = 0.0
UNITS = frozenset({"c", "f", "k"})
stations = ["oslo", "lima"]


class Unit(StrEnum):
    CELSIUS = "c"
    FAHRENHEIT = "f"


@lru_cache(maxsize=256)
def to_kelvin(celsius: float) -> float:
    return celsius + 273.15


@cache
def unit_names() -> frozenset[str]:
    return frozenset(u.name.lower() for u in Unit)


def add_station(stations: list[str], name: str) -> None:
    stations.append(name)


class WeatherService:
    TIMEOUT: ClassVar[float] = 30.0

    def __init__(self, base_url: str) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=self.TIMEOUT)
        self._readings: dict[str, list[float]] = {}

    def record(self, station: str, celsius: float) -> None:
        self._readings.setdefault(station, []).append(celsius)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "WeatherService":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    service: WeatherService = WeatherService("https://weather.example/api")
    app.state.weather = service
    try:
        yield
    finally:
        service.close()


def create_app() -> FastAPI:
    return FastAPI(lifespan=lifespan)


def worker_main() -> None:
    with WeatherService("https://weather.example/api") as service:
        service.record("oslo", 3.5)


def test_record() -> None:
    service: WeatherService = WeatherService("http://testserver")
    try:
        service.record("lima", 18.0)
    finally:
        service.close()
