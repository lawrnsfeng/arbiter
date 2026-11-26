class ShelfMark(str):
    @classmethod
    def from_isbn(cls, isbn: str) -> "ShelfMark":  # expect: R35
        return cls(f"{isbn[-4:]}/{isbn[:3]}")


class Postcode(str):
    @classmethod
    def from_text(cls, text: str) -> "Postcode":  # expect: R35
        compact = "".join(ch for ch in text if ch.isalnum()).upper()
        if len(compact) < 5:
            raise ValueError(text)
        return cls(f"{compact[:-3]} {compact[-3:]}")


class CarrierName(str):
    def __new__(cls, value: str) -> "CarrierName":  # expect: R35
        instance = super().__new__(cls, value)
        instance.verified = False
        return instance


class LockerId(str):
    @classmethod
    def from_scan(cls, scanned):  # expect-llm: R35
        return cls(scanned.partition(":")[2])
