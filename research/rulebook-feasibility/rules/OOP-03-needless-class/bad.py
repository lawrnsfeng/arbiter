class Greeter:  # expect: OOP-03
    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        return f"hi {self.name}"


class PriceCalculator:  # expect: OOP-03
    """Computes a price."""

    def __init__(self, base: float, tax: float) -> None:
        self.base = base
        self.tax: float = tax

    def total(self) -> float:
        return self.base * (1 + self.tax)
