from pathlib import Path


class Station:
    def __init__(self, root: Path) -> None:
        self.root = root

    def calibrate(self, offset: float) -> None:
        self.offset = offset

    def export_csv(self, target: Path) -> None:
        target.write_text(self.root.name)


class Sensor:
    def record(self, value: float) -> None:
        self.values.append(value)

    def reset(self) -> None:
        self.values.clear()


class ArchiveFolder:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def store(self, payload: bytes) -> None:
        (self.folder / "latest.bin").write_bytes(payload)

    def prune(self, keep: int) -> None:
        for old in sorted(self.folder.iterdir())[:-keep]:
            old.unlink()


class Dashboard:
    def show(self, station: Station) -> None:
        print(station.root)

    def title(self, text: str) -> str:
        return text.title()


def summarize(station: Station) -> str:
    return station.root.name


def pair(sensor: Sensor, other: Sensor) -> tuple[Sensor, Sensor]:
    return sensor, other


def celsius(value: float) -> float:
    return (value - 32) / 1.8
