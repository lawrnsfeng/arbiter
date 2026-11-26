import hashlib
import logging
from dataclasses import dataclass
from string import Template
from typing import ClassVar, Self
from urllib.parse import SplitResult, urlsplit

import httpx

logger: logging.Logger = logging.getLogger(__name__)


class ParcelError(Exception):
    """Base error; each subclass states its wording as a template over the values it takes."""

    TEMPLATE: ClassVar[Template] = Template("parcel service error")

    def __init__(self, **values: object) -> None:
        super().__init__(type(self).TEMPLATE.substitute(**values))


class StoreUnreachable(ParcelError):
    TEMPLATE: ClassVar[Template] = Template("cannot reach parcel store at $host")

    def __init__(self, host: str) -> None:
        super().__init__(host=host)


class NoParcelsAfter(ParcelError):
    TEMPLATE: ClassVar[Template] = Template("no parcels after cursor $cursor")

    def __init__(self, cursor: str | None) -> None:
        super().__init__(cursor=cursor)


@dataclass(frozen=True)
class StoreIdentity:
    scheme: str
    host: str | None
    port: int | None
    database: str

    @classmethod
    def from_config(cls, config) -> Self:
        """The store's identity from the configured URL, without its userinfo."""
        parts: SplitResult = urlsplit(str(config.database_url))
        return cls(parts.scheme, parts.hostname, parts.port, parts.path.lstrip("/"))


def fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:8]


def connect_carrier(api_key: str | None) -> httpx.Client:
    logger.info("carrier key configured: %s", bool(api_key))
    logger.info("carrier key fingerprint: %s", fingerprint(api_key or ""))
    return httpx.Client(headers={"Authorization": f"Bearer {api_key}"})


def open_store(host: str, token: str | None) -> None:
    logger.debug("store token present: %s", token is not None)
    raise StoreUnreachable(host)


def artifact_target(host: str, port: int) -> str:
    return f"postgresql://{host}:{port}/parcels"


def list_parcels(client, next_page_token: str | None) -> list[dict]:
    logger.info("fetching parcels after cursor %s", next_page_token)
    if next_page_token is None:
        raise NoParcelsAfter(cursor=next_page_token)
    return client.list(page_token=next_page_token)
