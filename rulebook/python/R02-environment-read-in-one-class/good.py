"""Library settings: the environment is read once, here, by one class."""

import os
import subprocess
from dataclasses import dataclass
from functools import cache
from unittest.mock import patch


def run_report(extra: dict[str, str]):
    return subprocess.run(["report"], env={**os.environ, **extra}, check=True)


def set_branch(branch: str) -> None:
    os.environ["LIBRARY_BRANCH"] = branch
    del os.environ["LIBRARY_QUIET"]
    os.environ.update({"LIBRARY_USER": "x"})


def test_loan_days():
    with patch.dict(os.environ, {"LOAN_DAYS": "14"}):
        assert borrower().loan_days == 14


def borrower(settings_cls=None):
    return (settings_cls or Settings).current()
