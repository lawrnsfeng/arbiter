import logging
import shutil
from pathlib import Path

import pytest


def test_overdue_notice(service, evidence: Path) -> None:
    service.mark_overdue("loan-7")
    shutil.copy(service.log_path, evidence / "scenario.log")  # expect: R87


@pytest.fixture
def published_log(service, evidence: Path):
    yield
    (evidence / "run.log").write_text(Path(service.log_location).read_text())  # expect: R87


def test_renewal(service, evidence: Path) -> None:
    service.renew("loan-8")
    shutil.copyfile("var/library.log", evidence / "renewal.log")  # expect: R87


def test_return(service, evidence: Path) -> None:
    service.check_in("loan-9")
    text = service.log_path.read_text()
    assert "checked in loan-9" in text  # expect-llm: R87
    (evidence / "return.log").write_text(text)  # expect: R87


# producer side: inherits root WARNING, so these INFO lines never reach the file
logger = logging.getLogger(__name__)  # expect-llm: R87


def send_notice(loan_id: str) -> None:
    logger.info("notice sent for %s", loan_id)
