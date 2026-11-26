from dataclasses import dataclass
from pathlib import Path
from typing import Final


class TrackerDirs:
    """Where the parcel tracker keeps its files.

    `BASE`: the tracker's data directory (e.g. ~/.local/share/parcels).
    `CACHE`: downloaded carrier pages (e.g. `~/.cache/parcels/`).
    """

    BASE: Final[Path] = Path.home() / ".local" / "share" / "parcels"
    CACHE: Final[Path] = Path.home() / ".cache" / "parcels"

    @property
    def labels(self) -> Path:
        """Printed shipping labels (e.g. ~/.local/share/parcels/labels)."""
        return self.BASE / "labels"

    def manifest(self, day: str) -> Path | None:
        """The day's manifest, e.g. $XDG_DATA_HOME/parcels/manifests/2026-01-31.json."""
        return self.BASE / "manifests" / f"{day}.json"

    def ensure(self) -> None:
        """Create the data directory and its parents (e.g. ~/.local/share/parcels)."""
        self.BASE.mkdir(parents=True, exist_ok=True)


class Parcel:
    """One shipment; a single path member does not make a paths-providing class."""

    label_file: Path

    def weight_kg(self) -> float:
        return 1.0


@dataclass
class TransferJob:
    """A data record holding two paths per instance: not a paths-providing class."""

    source: Path
    target: Path
    retries: int = 3

    @property
    def summary(self) -> str:
        return f"{self.source} -> {self.target}"
