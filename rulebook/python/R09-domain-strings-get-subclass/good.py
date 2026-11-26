from pathlib import Path
from typing import BinaryIO, Self


class ShelfMark(str):
    """A shelf mark `L<floor>/<bay>`, as printed on a shelf's spine label.

    >>> ShelfMark("L3/B12").floor
    3
    """

    @classmethod
    def from_label_file(cls, path: Path) -> Self:
        return cls(path.read_text(encoding="ascii").strip())

    @property
    def floor(self) -> int:
        return int(self.partition("/")[0].removeprefix("L"))


class CardPayload(bytes):
    """A library-card frame from the desk reader, fields separated by `;`.

    >>> CardPayload(b"M0042;2026").member_id
    b'M0042'
    """

    @classmethod
    def from_reader(cls, reader: BinaryIO) -> Self:
        return cls(reader.readline().rstrip(b"\r\n"))

    @property
    def member_id(self) -> bytes:
        return self.split(b";")[0]


def first_line(text: str) -> str:
    return text.splitlines()[0]


def words(text: str) -> list[str]:
    return text.split()


def preview(blurb: str) -> str:
    return blurb[:80]


def shelf_label(floor: int, bay: str) -> str:
    return f"L{floor}/{bay}"
