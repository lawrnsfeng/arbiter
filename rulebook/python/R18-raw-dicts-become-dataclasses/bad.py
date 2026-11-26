import json
import tomllib


def mean_temperature(path: str) -> float:
    with open(path) as fh:
        raw = json.load(fh)
    readings = raw["readings"]  # expect: R18
    return sum(r["celsius"] for r in readings) / len(readings)  # expect-llm: R18


def station_name(blob: bytes) -> str:
    return json.loads(blob)["station"]["name"]  # expect: R18


def alert_threshold(text: str) -> int:
    settings = tomllib.loads(text)
    return int(settings.get("threshold", 30))  # expect: R18


def latest(session, url: str) -> float:
    reply = session.get(url).json()
    return reply["latest"]  # expect: R18


def wind(reading: dict) -> float:
    return reading["wind_kph"]  # expect-llm: R18
