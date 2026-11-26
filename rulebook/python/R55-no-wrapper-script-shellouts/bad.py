import os
import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).parent / "scripts"
PHOTO_TOOL = "/usr/local/bin/recipe-photo-sync"


def sync_recipes():
    subprocess.run([str(SCRIPTS / "sync.sh")], check=True)  # expect: R55


def make_thumbnail(photo):
    subprocess.run(["bash", "thumbs.sh", photo], capture_output=True, check=True)  # expect: R55


def print_card(card_path):
    subprocess.run(f"lp -d kitchen {card_path}", shell=True, check=True)  # expect: R55


def convert(script_path, src):
    return subprocess.check_output([script_path, src])  # expect: R55


def clear_cache():
    os.system("rm -rf /tmp/recipe-cache")  # expect: R55


def compress(src):
    # replaces scripts/compress.sh, but its output still goes to the terminal instead of being captured
    subprocess.run(["gzip", "--keep", src], check=True)  # expect-llm: R55


def rotate_logs():
    subprocess.run(["/usr/bin/env", "LANG=C", "bash", "rotate.sh"], capture_output=False)  # expect: R55


def sync_photos():
    # the tool above is a two-line script that only execs rsync with fixed flags
    return subprocess.run([PHOTO_TOOL], capture_output=True, check=True)  # expect-llm: R55
