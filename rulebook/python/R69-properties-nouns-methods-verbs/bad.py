from functools import cached_property


class Plot:
    @property
    def calculate_area(self) -> float:  # expect: R69
        return self.width * self.depth

    @cached_property
    def get_label(self) -> str:  # expect: R69
        return f"plot {self.code}"

    @property
    def fetch(self) -> dict:  # expect: R69
        return self.client.get(self.code)

    def normalized(self) -> "Plot":  # expect: R69
        return Plot(self.code.upper())


class Catalogue:
    def sorted_by_due(self, reverse: bool) -> list:  # expect: R69
        return sorted(self.loans, key=lambda loan: loan.due, reverse=reverse)

    def summary(self) -> str:  # expect-llm: R69
        return f"{len(self.loans)} loans"
