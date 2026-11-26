def describe(reading) -> str:
    match reading:
        case Rain():
            return f"{reading.mm} mm rain"
        case Snow():
            return f"{reading.cm} cm snow"
        case _:
            return "dry"


def normalize(tags) -> list[str]:
    if isinstance(tags, str):
        tags = [tags]
    return sorted(tags)


def merge(left, right) -> dict:
    if isinstance(left, dict):
        left = dict(left)
    if isinstance(right, dict):
        right = dict(right)
    return {**left, **right}


def compatible(a, b) -> bool:
    return isinstance(a, Book) and isinstance(b, Book)


def unit_name(code: str) -> str:
    match code:
        case "C":
            return "celsius"
        case "F":
            return "fahrenheit"
        case _:
            raise UnknownUnit(code)


class UnknownUnit(LookupError):
    """Raised for a unit code outside the supported set."""


def area(shape: Circle | Square) -> float:
    match shape:
        case Circle(r=r):
            return 3.14159 * r * r
        case Square(side=s):
            return s * s
