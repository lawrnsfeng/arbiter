class User:
    def __init__(self, name: str, age: int) -> None:
        self._name = name
        self._age = age

    def get_name(self):  # expect: OOP-01
        return self._name

    def set_name(self, value):  # expect: OOP-01
        self._name = value

    def get_age(self) -> int:  # expect: OOP-01
        """Return the age."""
        return self._age

    @staticmethod
    def helper() -> None:
        pass


class Account:
    def get_balance(  # expect: OOP-01
        self,
    ):
        return self.balance
