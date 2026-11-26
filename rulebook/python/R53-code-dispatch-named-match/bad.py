class BadRequest(Exception):
    pass


class QuotaExceeded(Exception):
    pass


class StationOffline(Exception):
    pass


def fetch_reading(session, station):
    response = session.get(f"/readings/{station}")
    if response.status == 400:  # expect: R53
        raise BadRequest(station)
    elif response.status == 429:
        raise QuotaExceeded(station)
    elif response.status == 503:
        raise StationOffline(station)
    return response.json()


def fetch_forecast(session, station):
    response = session.get(f"/forecast/{station}")
    if response.status == 429:  # expect: R53
        raise QuotaExceeded(station)
    if 503 == response.status:
        raise StationOffline(station)
    return response.json()


_SENSOR_PARSERS = {"temp": parse_temperature, "rain": parse_rainfall, "wind": parse_wind}


def parser_for(kind):  # expect: R53
    return _SENSOR_PARSERS.get(kind)


_ALERTS: dict[tuple[str, str], type] = {("wind", "high"): StormWarning, ("rain", "high"): FloodWarning}


def alert_for(reading):  # expect: R53
    """Pick the alert class for a reading."""
    return _ALERTS[(reading.kind, reading.level)]


def refusal(status):
    return {400: BadRequest, 429: QuotaExceeded}[status]  # expect-llm: R53


def outage_text(status):
    if status == 404:  # expect: R53
        return "station not found"
    if status == 503:
        return "station offline"
    return "unknown"
