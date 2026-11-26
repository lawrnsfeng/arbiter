import argparse
import socket
from pathlib import Path

STATION_HOST = "10.0.0.17"  # expect-llm: R1
FEED = "metar"  # expect-llm: R1


def build_parser():
    return argparse.ArgumentParser(prog="skywatch")  # expect: R1


def open_station_socket():
    return socket.create_connection(("192.168.1.40", 4001))  # expect: R1


def connect_archive(client_cls):
    return client_cls(host="archive.weather.test", port=6379)  # expect: R1


def readings_file(root: Path) -> Path:
    return root / "readings.csv"  # expect: R1


def load_stations():
    with open("stations.json") as fh:  # expect: R1
        return fh.read()


def subscribe_hourly(bus):
    bus.subscribe("metar", every="1h")  # expect-llm: R1


def storm_warning(reading):
    if reading.gust_kmh > 90:  # expect: R1
        return "storm"
    if reading.celsius < -40:  # expect: R1
        return "sensor fault"
    return None


def fetch_forecast(client, region):
    return client.get(f"/forecast/{region}", timeout=15, max_retries=4)  # expect: R1


def is_reporting(station):
    return station.state == "offline"  # expect-llm: R1


class StationRecord(Model):
    name = CharField(max_length=64)  # expect-llm: R1
