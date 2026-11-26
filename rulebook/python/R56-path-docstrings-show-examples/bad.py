import os
from pathlib import Path
from typing import Final


class TrackerDirs:
    """Where the parcel tracker keeps its files.

    `BASE`: the tracker's data directory.
    """

    BASE: Final[Path] = Path.home() / ".local" / "share" / "parcels"  # expect: R56
    CACHE: Final[Path] = Path.home() / ".cache" / "parcels"  # expect: R56

    @property
    def labels(self) -> Path:  # expect: R56
        """Printed shipping labels."""
        return self.BASE / "labels"

    def manifest(self, day: str) -> Path:  # expect: R56
        return self.BASE / "manifests" / f"{day}.json"

    def ensure(self) -> None:  # expect: R56
        self.BASE.mkdir(parents=True, exist_ok=True)

    @classmethod
    def sync_log(cls) -> Path:
        """The courier sync log (e.g. ~/.local/state/parcels/sync.log)."""
        return Path.home() / ".local/state/parcels/sync.log"


class Locations:
    def __init__(self, root: str) -> None:
        self.root = root

    def inbox(self):  # expect-llm: R56
        """Incoming scans."""
        return os.path.join(self.root, "inbox")

    def outbox(self):  # expect-llm: R56
        """Scans waiting for upload."""
        return os.path.join(self.root, "outbox")
