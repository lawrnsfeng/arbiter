import os
import subprocess


class Album:
    def __init__(self, root: str, slug: str) -> None:
        self.root = root
        self.slug = slug
        self.index_path = self.root + "/index.json"  # expect: R29

    def thumbnail_path(self) -> str:  # expect: R29
        return f"{self.root}/thumbs/{self.slug}.png"  # expect: R29

    @property
    def cache_path(self) -> str:
        return os.path.join(self.root, ".cache")  # expect: R29

    def archive_path(self):  # expect: R29
        return self.root + ".tar"  # expect-llm: R29

    def verify(self) -> None:
        subprocess.run([str(self.archive_path()), "--verify"], check=True)  # expect: R29

    @property
    def export_path(self) -> str:
        return str(self.root_dir / "export")  # expect: R29

    @property
    def config_path(self) -> str:  # expect-llm: R29
        return self.settings.value("config")
