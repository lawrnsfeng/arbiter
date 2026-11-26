"""Constants of a weather-collector package, edited by hand at every site."""

from typing import Final

SENSOR_GATEWAY_HOST: str = "gateway.north-field.internal"  # expect: R59
GATEWAY_PORT = 8471  # expect-llm: R59
UPLOAD_URL = "https://ingest.example.net/v2/readings"  # expect-llm: R59
RADAR_SERVER = "10.20.0.15"  # expect: R59
ARCHIVE_BUCKET: Final = "readings-archive-eu"  # expect: R59
LOCAL_TIMEZONE = "Europe/Oslo"  # expect-llm: R59
