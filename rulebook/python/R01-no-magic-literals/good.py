"""Weather station client: every host, port, file name, threshold and the program name are named constants."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from skywatch.constants import (
    ARCHIVE_HOST,
    ARCHIVE_PORT,
    FORECAST_RETRIES,
    FORECAST_TIMEOUT_S,
    PROG,
    READINGS_FILE,
    STATIONS_FILE,
    Feed,
    StationState,
)

VERSION = "1.2.3"


@dataclass
class UplinkConfig:
    """Overridable from uplink.toml; the field default is the documented fallback, not a call-site literal."""

    gateway: str = "10.0.0.1"


class StormDetector:
    """Gust and cold limits belong to this one class, so they are its attributes."""

    STORM_GUST_KMH = 90
    FAULT_CELSIUS = -40

    def classify(self, reading) -> str | None:
        if reading.gust_kmh > self.STORM_GUST_KMH:
            return "storm"
        if reading.celsius < self.FAULT_CELSIUS:
            return "sensor fault"
        return None


def build_parser():
    return argparse.ArgumentParser(prog=PROG)


def connect_archive(client_cls):
    return client_cls(host=ARCHIVE_HOST, port=ARCHIVE_PORT)


def fetch_forecast(client, region):
    return client.get(f"/forecast/{region}", timeout=FORECAST_TIMEOUT_S, max_retries=FORECAST_RETRIES)


def readings_file(root: Path) -> Path:
    return root / READINGS_FILE


def load_stations(root: Path):
    return (root / STATIONS_FILE).read_text()


def subscribe_hourly(bus):
    bus.subscribe(Feed.METAR, every=Feed.HOURLY, progress="spinner")


def is_reporting(station) -> bool:
    return station.state != StationState.OFFLINE


def recent(readings: list) -> list:
    if len(readings) > 0 and readings[0].count >= 1:
        return readings[-3:]
    return []


def host_label(station):
    return {"host": station.name}


def connect(client_cls, port=ARCHIVE_PORT):
    return client_cls(port=port)


def test_storm_threshold():
    assert StormDetector().classify(type("R", (), {"gust_kmh": 95, "celsius": 3})()) == "storm"
    assert len(recent([])) < 2
