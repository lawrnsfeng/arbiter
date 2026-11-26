"""Universal constants stay constants; site values are config fields with in-code defaults."""

from dataclasses import dataclass

SECONDS_PER_HOUR = 3600
KELVIN_OFFSET = 273.15
CONFIG_FILE_NAME = "collector.yaml"
URL = "url"  # a token name, not an address
HTTPS_PORT = 443  # IANA system ports are standards
SMTP_SUBMISSION_PORT = 587
PACKAGE_INDEX_URL = "https://pypi.org/simple"  # a public, universal address
LOOPBACK_HOST = "127.0.0.1"  # universal addresses
BIND_HOST = "0.0.0.0"
STATUS_URL = "https://{host}/status"  # a template, not an address
HEALTH_ENDPOINT = "health"  # a path


@dataclass
class CollectorConfig:
    """Overridable in collector.yaml."""

    gateway_host: str = "gateway"
    gateway_port: int = 8471
    upload_url: str = "https://ingest.example.net/v2/readings"
    timezone: str = "UTC"


class Units:
    WIND_SPEED_UNIT: str = "km/h"  # a class constant, and not an environment value
