# ruff: noqa: D103  # expect: R17
from typing import cast


def eta_hours(parcel_id: str, schedule: dict[str, int] | None) -> int:
    return schedule[parcel_id]  # type: ignore[index]  # expect: R17


to_kilograms = lambda grams: grams / 1000  # noqa: E731  # expect: R17


def dispatch(origin, destination, weight_g, courier, priority, insured):  # noqa: PLR0913  # expect: R17
    return courier.book(origin, destination, weight_g, priority, insured)


def depot_name(scan) -> str:
    return scan.depot.lower()  # pyright: ignore[reportOptionalMemberAccess]  # expect: R17


def label_count(manifest: object) -> int:  # pylint: disable=unused-argument  # expect: R17
    return cast(int, getattr(manifest, "labels"))  # expect-llm: R17
