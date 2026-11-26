import random


class Archive:
    def compact(self, year: int) -> None:
        self.volumes = [v for v in self.volumes if v.year != year]

    def sample(self, count: int) -> list["Volume"]:
        return random.sample(self.volumes, count)

    @property
    def volumes_by_isbn(self) -> dict[str, "Volume"]:
        return {v.isbn: v for v in self.volumes}

    @property
    def is_finished(self) -> bool:
        return not self.pending

    @property
    def staleness(self) -> int:
        return self.catalogue.fetch_version() - self.version

    # Look-alikes: multi-word names, and verbs that end in "ed".
    def mark_returned(self, isbn: str) -> None:
        self.pending.remove(isbn)

    def embed(self, widget: str) -> str:
        return widget

    def proceed(self) -> None:
        self.step += 1


# Look-alike: a module-level function, not a member.
def renamed(value: str) -> str:
    return value.title()
