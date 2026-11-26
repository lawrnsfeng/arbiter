from dataclasses import dataclass


@dataclass
class User:
    name: str
    age: int


class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    def get_fahrenheit(self) -> float:  # computes, not an accessor
        return self._celsius * 9 / 5 + 32


class Repo:
    def get_user(self, user_id: int) -> User:  # takes an argument: a query, not an accessor
        return self.users[user_id]
