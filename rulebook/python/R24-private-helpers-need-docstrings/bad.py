def _to_celsius(fahrenheit: float) -> float:  # expect: R24
    return (fahrenheit - 32) * 5 / 9


def _round_tenth(value: float) -> float:  # expect: R24
    # Round to one decimal place.
    return round(value, 1)


def _blank(value: float) -> float:  # expect: R24
    """"""
    return value


class Gauge:
    def _bucket(self, reading: float) -> int:  # expect: R24
        return int(reading // 5)

    async def _poll(self) -> float:  # expect: R24
        return await self.sensor.read()

    def __hidden(self) -> None:  # expect: R24
        pass
