import logging
import tempfile
import subprocess
from pathlib import Path

from photos.cmd import Command
from photos.constants import ARCHIVE_SUFFIX, INDEX_FILE

_mirrors: dict[str, Path] = {}


class Album:
    def __init__(self, root: Path, slug: str) -> None:
        """Album stored under `root` (e.g. ~/Pictures/albums/<slug>)."""
        self.root = root
        self.slug = slug
        self.index_path = self.root / INDEX_FILE

    @property
    def thumbnail_path(self) -> Path:
        """Thumbnail image (e.g. ~/Pictures/albums/<slug>/thumbs/<slug>.png)."""
        return self.root / "thumbs" / f"{self.slug}.png"

    @property
    def archive_path(self) -> Path:
        """Archive next to the album (e.g. ~/Pictures/albums/<slug>.tar)."""
        return self.root.with_suffix(ARCHIVE_SUFFIX)

    def verify(self) -> None:
        """Check the archive at `archive_path` (e.g. ~/Pictures/albums/<slug>.tar) is readable."""
        subprocess.run(Command("tar").with_flag("--verify").with_args(self.archive_path).tokens(), check=True)
        logging.info("verified %s", str(self.archive_path))

    # Look-alikes: routes that are not filesystem paths, and a local variable.
    @property
    def url_path(self) -> str:
        """Web route of the album's photos (e.g. /albums/<slug>/photos)."""
        return f"/albums/{self.slug}/photos"

    @property
    def route_path(self) -> str:
        """Web route of the album (e.g. /albums/<slug>)."""
        return "/albums/" + self.slug

    def describe(self) -> str:
        """Location of the album's log (e.g. ~/Pictures/albums/<slug>/log.txt)."""
        log_path: str = f"{self.root}/log.txt"
        return log_path

    # Look-alikes: a parameter beyond self, and a read of module-level mutable state, keep a method.
    def page_path(self, number: int) -> Path:
        """One scanned page (e.g. ~/Pictures/albums/<slug>/pages/3.png)."""
        return self.root / "pages" / f"{number}.png"

    def mirror_path(self) -> Path:
        """Mirror of the album if one is registered (e.g. /mnt/backup/albums/<slug>), else the album root."""
        return _mirrors.get(self.slug, self.root)

    # Look-alikes: members doing I/O stay methods (a property must not do I/O).
    def scratch_path(self) -> Path:
        """Fresh scratch directory for one export (e.g. /tmp/tmpk3j9x2)."""
        return Path(tempfile.mkdtemp())

    def cache_path(self) -> Path:
        """Cache directory, created on first use (e.g. ~/Pictures/albums/<slug>/.cache)."""
        cache: Path = self.root / ".cache"
        cache.mkdir(exist_ok=True)
        return cache
