from abc import ABC, abstractmethod
from pathlib import Path

from django.views.generic import DetailView
from parceldesk.constants import LABEL_SUFFIX

_seen_codes: dict[str, int] = {}


class Parcel:
    def __init__(self, code: str, weight_g: int, events: list) -> None:
        self.code = code
        self.weight_g = weight_g
        self.events = events

    @property
    def weight_kg(self) -> float:
        return self.weight_g / 1000

    @property
    def lines(self) -> list[str]:
        return [f"{e.when:%H:%M} {e.place}" for e in sorted(self.events)]

    @property
    def label_path(self) -> Path:
        return Path(self.spool_dir).joinpath(self.code).with_suffix(LABEL_SUFFIX)

    def scan_count(self) -> int:
        return _seen_codes.get(self.code, 0)

    def load_history(self, folder: Path) -> str:
        return (folder / f"{self.code}.txt").read_text()

    def print_status(self) -> None:
        print(self.events[-1].place)

    def heavier_than(self, grams: int) -> bool:
        return self.weight_g > grams

    def __len__(self) -> int:
        return len(self.events)

    def refresh(self):
        return self.tracker.poll(self.code)

    def as_label(self) -> str:
        return f"{self.code}:{self.weight_g}"


class Carrier(ABC):
    @abstractmethod
    def label(self) -> str: ...


class Courier(Carrier):
    def label(self) -> str:
        return self.name.upper()


class ParcelPage(DetailView):
    def get_success_url(self) -> str:
        return f"/parcels/{self.code}"
