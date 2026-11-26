from functools import cached_property


class Plot:
    @property
    def area(self) -> float:
        return self.width * self.depth

    @cached_property
    def label(self) -> str:
        return f"plot {self.code}"

    @label.setter
    def label(self, value: str) -> None:
        self.code = value

    @property
    def overdue_days(self) -> int:
        return (self.today - self.due).days

    @property
    def run_id(self) -> str:
        return self.code

    @property
    def check_digit(self) -> int:
        return sum(map(int, self.code)) % 10

    @property
    def format(self) -> str:
        return "csv"

    def normalize(self) -> "Plot":
        return Plot(self.code.upper())

    def embed(self, other: "Plot") -> None:
        self.children.append(other)

    def proceed(self) -> None:
        self.stage += 1

    def shred(self) -> None:
        self.children.clear()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Plot) and other.code == self.code


def sorted_codes(plots: list[Plot]) -> list[str]:
    return sorted(p.code for p in plots)
