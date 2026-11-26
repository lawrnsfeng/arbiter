class BadRequest(Exception):
    pass


class QuotaExceeded(Exception):
    pass


class WeatherClient:
    def refusal_class(self, status: int) -> type[Exception] | None:
        """The refusal a status code stands for; None when the request succeeded."""
        match status:
            case 400:
                return BadRequest
            case 429:
                return QuotaExceeded
            case _:
                return None


UNITS: dict[str, str] = {"temp": "C", "rain": "mm", "wind": "km/h"}


def unit_for(kind: str) -> str:
    return UNITS[kind]


def legend() -> list[str]:
    return [f"{kind} ({unit})" for kind, unit in UNITS.items()]  # callers enumerate the mapping


MONTHS: dict[int, str] = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def month_name(number: int) -> str:
    return MONTHS[number]  # more than eight keys of pure data, no default


def classify(celsius: float) -> str:
    if celsius == 0:  # a single test is not a ladder
        return "freezing point"
    return "other"


def normalise(kind: str) -> str:
    if kind == "temp":  # branches rebind, they do not select and return
        kind = "temperature"
    elif kind == "rain":
        kind = "rainfall"
    return kind


def pressure_steps(n: int) -> int:
    if n == 0:  # recursion base cases compute values, they do not select objects
        return 0
    if n == 1:
        return 1
    return pressure_steps(n - 1) + pressure_steps(n - 2)
