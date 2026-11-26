import unittest
from dataclasses import dataclass
from unittest.mock import MagicMock

from lockers import HttpLockerBank


@dataclass(frozen=True)
class LockerSlot:
    number: int
    depth_cm: int

    def fits(self, parcel_depth_cm: int) -> bool:  # expect-llm: R80
        return parcel_depth_cm <= self.depth_cm


class DropOffDesk:
    def __init__(self, bank) -> None:
        self._bank = bank

    def assign(self, parcel_depth_cm: int) -> int | None:
        for slot in self._bank.free_slots():
            if slot.fits(parcel_depth_cm):
                self._bank.reserve(slot.number)
                return slot.number
        return None


def test_assign_reserves() -> None:  # expect: R80
    bank = MagicMock()
    bank.free_slots.return_value = [LockerSlot(4, 40)]
    DropOffDesk(bank).assign(30)
    bank.reserve.assert_called_once()


def test_assign_reserves_flag() -> None:  # expect: R80
    bank = MagicMock()
    bank.free_slots.return_value = [LockerSlot(2, 60)]
    DropOffDesk(bank).assign(10)
    assert bank.reserve.called


class DropOffDeskTest(unittest.TestCase):
    def test_assign_counts(self) -> None:  # expect: R80
        bank = MagicMock()
        bank.free_slots.return_value = [LockerSlot(9, 50)]
        DropOffDesk(bank).assign(20)
        self.assertEqual(bank.reserve.call_count, 1)

    def test_assign_flag(self) -> None:  # expect: R80
        bank = MagicMock()
        bank.free_slots.return_value = [LockerSlot(1, 50)]
        DropOffDesk(bank).assign(20)
        self.assertTrue(bank.reserve.called)


def test_assign_real_bank() -> None:  # expect-llm: R80
    bank = HttpLockerBank("https://lockers.example")
    assert DropOffDesk(bank).assign(25) is not None


def test_assign_reserves_is_true() -> None:  # expect: R80
    bank = MagicMock()
    bank.free_slots.return_value = [LockerSlot(3, 45)]
    DropOffDesk(bank).assign(15)
    assert bank.reserve.called is True


def test_assign_reserves_some() -> None:  # expect: R80
    bank = MagicMock()
    bank.free_slots.return_value = [LockerSlot(5, 45)]
    DropOffDesk(bank).assign(15)
    assert bank.reserve.call_count > 0


def test_assign_reserves_mirrored() -> None:  # expect: R80
    bank = MagicMock()
    bank.free_slots.return_value = [LockerSlot(6, 45)]
    DropOffDesk(bank).assign(15)
    assert 0 < bank.reserve.call_count
