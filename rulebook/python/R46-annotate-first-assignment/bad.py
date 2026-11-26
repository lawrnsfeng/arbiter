from dataclasses import dataclass


def average_rainfall(readings):
    totals = {}  # expect: R46
    for station, millimetres in readings:
        totals[station] = totals.get(station, 0.0) + millimetres
    count = len(readings)  # expect: R46
    count = count or 1
    return {k: v / count for k, v in totals.items()}


async def fetch_latest(client, station: str):
    response = await client.get(f"/stations/{station}")  # expect: R46
    if response.ok:
        payload = response.json()  # expect: R46
    else:
        payload: dict[str, float] = {}
    return payload


class Thermometer:
    unit = "celsius"  # expect: R46
    precision: int = 1


@dataclass
class StationReport:
    station: str
    peak_gust: float
    MAX_GUST_KMH: float = 250.0  # expect: R46

    def summary(self) -> str:
        def label(value):
            text = f"{value:.1f} km/h"  # expect: R46
            return text

        line = f"{self.station}: {label(self.peak_gust)}"  # expect: R46
        return line
