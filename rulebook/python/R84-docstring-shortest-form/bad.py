"""Weather station ingestion.

This module imports the HTTP client, the unit converter and the storage layer.
It first fetches readings, then converts them, and finally stores them.
"""  # expect: R84


def ingest(station: str, hours: int) -> int:
    """Fetch the last readings for a station from the remote API and store
    them in the local archive.

    First we build the request URL from the station code and the hour count,
    then we call the remote API and decode the JSON body.

    After that we loop over every reading, convert Fahrenheit to Celsius,
    and append each one to the archive before returning the count.
    """  # expect: R84
    return archive_readings(fetch(station, hours))


def convert(value: float, unit: str) -> float:
    """Convert a reading to Celsius.

    Raises:
        ValueError: when the unit is not c or f.
    """  # expect: R84
    if unit not in {"c", "f"}:
        raise ValueError(unit)
    return value if unit == "c" else (value - 32) * 5 / 9


def average(values: list[float]) -> float:
    """Average of the readings.

    Args:
        values: list of float values.

    Returns:
        float: the average.

    """  # expect-llm: R84
    return sum(values) / len(values)


def latest(station: str) -> float:
    """Latest reading.

    First we look up the station, then we read its newest row.
    """  # expect-llm: R84
    return newest_row(lookup(station))
