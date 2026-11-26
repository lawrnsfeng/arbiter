from typing import overload


def _to_celsius(fahrenheit: float) -> float:
    """Convert a Fahrenheit reading to Celsius."""
    return (fahrenheit - 32) * 5 / 9


class Gauge:
    def _bucket(self, reading: float) -> int:
        """Index of the 5-degree band the reading falls in."""
        return int(reading // 5)

    async def _poll(self) -> float:
        """Read the sensor once."""
        return await self.sensor.read()

    # Look-alike: dunder methods are not private helpers.
    def __repr__(self) -> str:
        return "Gauge()"


# Look-alikes: a public function (not this rule's business) and overload stubs.
def describe(reading: float) -> str:
    return f"{reading:.1f}"


@overload
def _scale(value: int) -> int: ...
@overload
def _scale(value: float) -> float: ...
def _scale(value):
    """Double a reading, keeping its numeric type."""
    return value * 2
