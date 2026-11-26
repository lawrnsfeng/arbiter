import logging

logger = logging.getLogger(__name__)


def probe(config) -> dict:
    return {"healthy": True, "store": str(config.database_url)}  # expect: R85


def connect_carrier(api_key: str) -> None:
    logger.info("connecting to the carrier with %s", api_key)  # expect: R85


class TrackingFeed:
    def __init__(self, token: str, log: logging.Logger) -> None:
        self.token = token
        self.log = log

    def refresh(self) -> None:
        self.log.warning(f"feed rejected token {self.token}")  # expect: R85


def open_store(dsn: str):
    raise ConnectionError(f"cannot reach parcel store at {dsn}")  # expect: R85


def debug_session(session_cookie: str) -> None:
    print("session: " + session_cookie)  # expect: R85


def write_report(verdict: dict, out) -> None:
    out.write_text(SECRET_PATTERN.sub("***", json.dumps(verdict)))  # expect-llm: R85


def artifact_target(user: str, pw: str, host: str) -> str:
    target = f"postgresql://{user}:{pw}@{host}/parcels"  # expect-llm: R85
    return target


def connect_depot(depot_dsn: str, log: logging.Logger) -> None:
    log.info("connecting", extra={"dsn": depot_dsn})  # expect: R85
    log.debug("auth", token=depot_dsn)  # expect: R85


def open_archive(archive_db_url: str):
    msg = f"archive unreachable: {archive_db_url}"
    raise ConnectionError(msg)  # expect: R85
