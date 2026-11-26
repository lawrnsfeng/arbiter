import copy
import logging
import shutil
from pathlib import Path

from library.constants import CATALOG_CSV, LOGGING_CONFIG, NGINX_ACCESS_LOG, SCENARIO_LOG

logger: logging.Logger = logging.getLogger(__name__)


def configure_notice_logging(level: int) -> None:
    """Set the producer's level explicitly; the composition root passes it from configuration."""
    logger.setLevel(level)


def send_notice(loan_id: str) -> None:
    logger.info("notice sent for %s", loan_id)


def lines_since(log_path: Path, mark: int) -> list[str]:
    with log_path.open("rb") as log:
        log.seek(mark)
        return log.read().decode().splitlines()


def test_overdue_notice(service, evidence: Path) -> None:
    configure_notice_logging(logging.INFO)  # the suite pins the level its evidence depends on
    mark: int = service.log_path.stat().st_size
    service.mark_overdue("loan-7")
    lines: list[str] = lines_since(service.log_path, mark)
    assert lines == ["notice sent for loan-7"]
    (evidence / SCENARIO_LOG).write_text("\n".join(lines) + "\n")


def test_catalog_import(fixtures: Path, tmp_path: Path) -> None:
    shutil.copy(fixtures / CATALOG_CSV, tmp_path / CATALOG_CSV)
    shutil.copy(fixtures / LOGGING_CONFIG, tmp_path / LOGGING_CONFIG)
    shutil.copy(fixtures / NGINX_ACCESS_LOG, tmp_path / NGINX_ACCESS_LOG)  # an input fixture, never published


def test_notice_lines_are_copied() -> None:
    log_lines: list[str] = ["notice sent for loan-1"]
    snapshot: list[str] = copy.copy(log_lines)
    assert snapshot == log_lines
