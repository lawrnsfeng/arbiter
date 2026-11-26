import asyncio
import os
import subprocess
import subprocess as proc
from subprocess import check_output


def archive_recipes(tar: str, folder: str) -> None:
    subprocess.run([tar, "-czf", "recipes.tgz", folder], check=True)  # expect: R61


def station_log(station: str) -> str:
    return check_output(("journalctl", "-u", station, "--no-pager"), text=True)  # expect: R61


def start_parcel_worker(python: str, queue: str) -> subprocess.Popen[bytes]:
    return subprocess.Popen(args=[python, "-m", "parcels.worker", "--queue", queue])  # expect: R61


async def mirror_catalogue(rsync: str, target: str) -> None:
    base = [rsync, "-a"]
    await asyncio.create_subprocess_exec(*[*base, "catalogue/", target])  # expect: R61
    await asyncio.create_subprocess_exec(rsync, "-a", "covers/", target)  # expect: R61


def rebuild_shelves(make: str) -> None:
    os.execvp(make, [make, "shelves"])  # expect: R61

def rebuild_catalogue(make: str) -> None:
    os.execlp(make, make, "catalogue")  # expect: R61


def spawn_thumbnailer(convert: str, cover: str) -> int:
    return os.spawnl(os.P_WAIT, convert, convert, cover, "thumb.png")  # expect: R61


def count_overdue(sqlite: str) -> bytes:
    return proc.check_output([sqlite, "loans.db", "select count(*) from overdue"])  # expect: R61



def rebuild_index(make: str) -> None:
    argv = [make, "index", "--jobs", "4"]  # expect-llm: R61
    subprocess.run(argv, check=True)
