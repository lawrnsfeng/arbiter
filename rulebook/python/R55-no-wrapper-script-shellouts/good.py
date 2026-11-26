import subprocess
from pathlib import Path

from cookbook.shell import Command


def make_thumbnail(photo: str) -> str:
    resize: Command = Command("convert").arg(photo).option("-resize", "200x200").arg(f"{photo}.thumb.png")
    done: subprocess.CompletedProcess[str] = subprocess.run(resize.argv(), capture_output=True, text=True, check=True)
    return done.stdout


def compress(src: str) -> None:
    gzip: Command = Command("gzip").flag("--keep").arg(src)
    subprocess.run(gzip.argv(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def revision() -> str:
    return subprocess.check_output(Command("git").arg("rev-parse").arg("HEAD").argv(), text=True).strip()


def describe_script(script_path: Path) -> str:
    return script_path.read_text()  # reads a script, does not run it


def edit_recipe(path: str) -> None:
    subprocess.run(Command("vim").arg(path).argv(), check=True)  # interactive: the user must see it


def recipe_history(transcript_dir: str) -> str:
    log: Command = Command("/usr/bin/env").arg("LANG=C").arg("git").arg("log").arg(transcript_dir)
    done: subprocess.CompletedProcess[str] = subprocess.run(log.argv(), capture_output=True, text=True)
    return done.stdout
