import unittest
from dataclasses import dataclass, field
from unittest.mock import MagicMock


@dataclass(frozen=True)
class LockerSlot:
    number: int
    depth_cm: int

    def fits(self, parcel_depth_cm: int) -> bool:
        return parcel_depth_cm <= self.depth_cm


class DropOffDesk:
    def __init__(self, bank, site: str) -> None:
        self._bank = bank
        self._site = site

    def assign(self, parcel_depth_cm: int) -> int | None:
        for slot in self._bank.free_slots(self._site):
            if slot.fits(parcel_depth_cm):
                self._bank.reserve(slot.number)
                return slot.number
        return None


@dataclass
class StubBank:
    """Answers `free_slots` per site from a fixed table and keeps the reserved numbers."""

    slots: dict[str, list[LockerSlot]]
    reserved: list[int] = field(default_factory=list)

    def free_slots(self, site: str) -> list[LockerSlot]:
        return self.slots.get(site, [])

    def reserve(self, number: int) -> None:
        self.reserved.append(number)


def test_locker_slot_fits_boundary() -> None:
    """LockerSlot.fits: equal depth fits, one centimetre more does not."""
    slot: LockerSlot = LockerSlot(3, 40)
    assert slot.fits(40)
    assert not slot.fits(41)


def test_assign_skips_shallow_slot() -> None:
    """DropOffDesk.assign takes the first slot deep enough."""
    bank: StubBank = StubBank({"harbour": [LockerSlot(1, 20), LockerSlot(2, 60)]})
    assert DropOffDesk(bank, "harbour").assign(45) == 2
    assert bank.reserved == [2]


def test_assign_full_bank_goes_to_counter() -> None:
    bank: StubBank = StubBank({})
    assert DropOffDesk(bank, "harbour").assign(10) is None
    assert bank.reserved == []


def test_assign_reserve_arguments() -> None:
    bank: MagicMock = MagicMock()
    bank.free_slots.return_value = [LockerSlot(7, 30)]
    assert DropOffDesk(bank, "station").assign(30) == 7
    bank.reserve.assert_called_once_with(7)
    bank.free_slots.assert_called_once_with("station")


def test_assign_too_deep_reserves_nothing() -> None:
    bank: MagicMock = MagicMock()
    bank.free_slots.return_value = [LockerSlot(7, 30)]
    DropOffDesk(bank, "station").assign(90)
    assert not bank.reserve.called
    assert bank.reserve.call_count < 1


class DropOffDeskTest(unittest.TestCase):
    def test_assign_none_reserved(self) -> None:
        bank: MagicMock = MagicMock()
        bank.free_slots.return_value = []
        DropOffDesk(bank, "station").assign(5)
        self.assertEqual(bank.reserve.call_count, 0)


def test_assign_unknown_site_reserves_nothing() -> None:
    bank: MagicMock = MagicMock()
    bank.free_slots.return_value = []
    DropOffDesk(bank, "nowhere").assign(5)
    assert bank.reserve.called is not True
    assert 1 > bank.reserve.call_count
