from pathlib import Path


class ShelfMark(str):
    """A shelf mark built from an ISBN: its last four digits over its prefix.

    >>> ShelfMark("9780441013593")
    '3593/978'
    """

    def __new__(cls, isbn: str) -> "ShelfMark":
        return super().__new__(cls, f"{isbn[-4:]}/{isbn[:3]}")


class CarrierName(str):
    """A carrier's name, unverified until checked.

    >>> CarrierName("Fastway").verified
    False
    """

    def __init__(self, value: str) -> None:
        self.verified = False


class PostcodeError(ValueError):
    def __init__(self, text: str) -> None:
        super().__init__(f"not a postcode: {text!r}")


class Postcode(str):
    """A postcode, normalised to upper case with one space before the inward part.

    >>> Postcode("sw1a 1aa")
    'SW1A 1AA'
    >>> Postcode("12")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    PostcodeError: not a postcode: '12'
    """

    MIN_LENGTH = 5

    def __new__(cls, text: str) -> "Postcode":
        text = "".join(ch for ch in text if ch.isalnum()).upper()
        if len(text) < cls.MIN_LENGTH:
            raise PostcodeError(text)
        return super().__new__(cls, f"{text[:-3]} {text[-3:]}")


# look-alike: several alternative constructors
class Barcode(str):
    """A twelve-digit barcode.

    >>> Barcode.from_digits("42")
    '000000000042'
    """

    @classmethod
    def from_digits(cls, digits: str) -> "Barcode":
        return cls(digits.zfill(12))

    @classmethod
    def from_bytes(cls, data: bytes) -> "Barcode":
        return cls(data.decode("ascii"))


# look-alike: the input is not a plain str
class ManifestName(str):
    """A manifest's name, taken from its file.

    >>> ManifestName.from_path(Path("2026-03.json"))
    '2026-03'
    """

    @classmethod
    def from_path(cls, path: Path) -> "ManifestName":
        return cls(path.stem)


# look-alike: not a str subclass
class Route:
    @classmethod
    def from_text(cls, text: str) -> "Route":
        return cls(text.split(">"))
