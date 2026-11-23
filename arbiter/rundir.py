"""The RUN directory: every stage reads and writes JSON there, so any stage can be rerun alone."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import diff


def _default(o: object) -> object:
    if isinstance(o, set | frozenset):
        return sorted(o)
    raise TypeError(f"not JSON serializable: {type(o).__name__}")


@dataclass(frozen=True, slots=True)
class RunDir:
    path: Path

    @classmethod
    def default_for(cls, repo: Path) -> "RunDir":
        head = diff.git(repo, "rev-parse", "--short=7", "HEAD").strip()
        stamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        return cls(Path(f"/tmp/arbiter-{repo.resolve().name}-{head}-{stamp}"))

    def __truediv__(self, name: str) -> Path:
        return self.path / name

    def load(self, name: str, default: Any = None) -> Any:
        p = self.path / name
        return json.loads(p.read_text()) if p.exists() else default

    def save(self, name: str, data: object) -> None:
        (self.path / name).write_text(json.dumps(data, indent=2, default=_default))

    def text(self, name: str) -> str:
        p = self.path / name
        return p.read_text() if p.exists() else ""

    def cov(self, **kv: object) -> None:
        """Merge keys into coverage.json: lists extend, dicts update, anything else replaces."""
        c = self.load("coverage.json", {})
        for k, v in kv.items():
            match v:
                case list():
                    c.setdefault(k, []).extend(v)
                case dict():
                    c.setdefault(k, {}).update(v)
                case _:
                    c[k] = v
        self.save("coverage.json", c)

    @property
    def worktree(self) -> Path | None:
        wt = self.path / "wt"
        return wt if wt.exists() else None
