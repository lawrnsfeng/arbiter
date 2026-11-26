import os
import subprocess


def borrower_name(name=None):
    return name or os.environ.get("LIBRARY_USER", "guest")  # expect: R2


def loan_days():
    return int(os.environ["LOAN_DAYS"])  # expect: R2


def catalogue_url():
    return os.getenv("CATALOGUE_URL")  # expect: R2


def is_quiet():
    return "LIBRARY_QUIET" in os.environ  # expect: R2


def run_report(extra):
    env = os.environ.copy()  # expect: R2
    env.update(extra)
    return subprocess.run(["report"], env=env, check=True)


class LibrarySettings:
    @property
    def branch(self):
        return os.environ.get("LIBRARY_BRANCH", "main")  # expect: R2
