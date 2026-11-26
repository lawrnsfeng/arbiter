import random


class Archive:
    def compacted(self, year: int) -> None:  # expect: R28
        self.volumes = [v for v in self.volumes if v.year != year]

    def shuffled(self, count: int) -> list["Volume"]:  # expect: R28
        return random.sample(self.volumes, count)

    def _indexed(self):  # expect: R28
        return {v.isbn: v for v in self.volumes}

    def finished(self) -> bool:  # expect: R28
        return not self.pending

    @property
    def stale(self) -> bool:  # expect-llm: R28
        return self.catalogue.fetch_version() != self.version
