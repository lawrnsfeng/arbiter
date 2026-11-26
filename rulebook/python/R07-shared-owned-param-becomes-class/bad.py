from pathlib import Path


class Station:
    def __init__(self, root: Path) -> None:
        self.root = root


class Sensor:
    name: str


def calibrate(station: Station, offset: float) -> None:  # expect: R7
    station.offset = offset


def export_csv(target: Path, station: Station) -> None:  # expect: R7
    target.write_text(station.root.name)


def last_reading(station: "Station") -> float:  # expect: R7
    return station.readings[-1]


def test_last_reading(station: Station) -> None:
    assert last_reading(station) == 21.5


class Recorder:
    def record(self, value: float, sensor: Sensor) -> None:  # expect: R7
        self.values[sensor.name] = value

    def reset(self, sensor: Sensor | None) -> None:  # expect: R7
        self.values.pop(sensor.name, None)


class Archive:
    def store(self, folder: Path, payload: bytes) -> None:  # expect-llm: R7
        (folder / "latest.bin").write_bytes(payload)

    def prune(self, keep: int, folder: Path) -> None:  # expect-llm: R7
        for old in sorted(folder.iterdir())[:-keep]:
            old.unlink()
