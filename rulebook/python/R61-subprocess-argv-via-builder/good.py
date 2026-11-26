import asyncio
import subprocess as sp

from shelltools import Cmd


def archive_recipes(tar: str, folder: str) -> None:
    create: Cmd = Cmd(tar, "create").with_flag("-z").with_option("--file", "recipes.tgz").with_args(folder)
    sp.run(create.tokens(), check=True)


async def mirror_catalogue(sync: Cmd, target: str) -> None:
    await asyncio.create_subprocess_exec(*sync.with_args("catalogue/", target).tokens())


async def mirror_covers(program: str, rest: Cmd) -> None:
    await asyncio.create_subprocess_exec(program, *rest.tokens())


def nightly(scheduler, job_a, job_b) -> None:
    scheduler.run([job_a, job_b])
    scheduler.subprocess.Popen
