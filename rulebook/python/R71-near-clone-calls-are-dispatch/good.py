from library.catalogue import Section


class UnknownSection(LookupError):
    """Raised for a catalogue section the shelver has no placement for."""


class Shelver:
    def __init__(self, index, scanner, journal) -> None:
        self.index = index
        self.scanner = scanner
        self.journal = journal

    def shelve(self, section: Section, book) -> None:
        match section:
            case Section.FICTION:
                self._place_by_surname(book)
            case Section.REFERENCE:
                self._place_by_call_number(book)
            case _:
                raise UnknownSection(section)


def returns_desk(shelver: Shelver, book) -> None:
    shelver.shelve(book.section, book)


def weigh(scale, unit, rounding, parcels) -> list[float]:
    first: float = convert(scale, unit, rounding, parcels[0].grams * 2)
    rest: float = convert(scale, unit, rounding, parcels[1].grams + 5)
    return [first, rest]


def zoom(canvas, layer, cursor) -> None:
    scale(canvas, layer, cursor, 0.5)
    scale(canvas, layer, cursor, 2.0)


def labels(printer) -> None:
    printer.print("a", "b", "c", copies=1)
    printer.print("a", "b", "c", copies=2)
