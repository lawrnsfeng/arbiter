from dataclasses import dataclass
from typing import Self

import click
import httpx
from parcelkit.messages import Msg


@dataclass(frozen=True)
class ParcelAudit:
    region: str
    since: str
    limit: int
    api: str

    @classmethod
    def from_args(cls, args) -> Self:
        return cls(args.region or "north", args.since or "1970-01-01", args.limit or 50, args.api)

    def announce(self) -> None:
        print(Msg.auditing(region=self.region, since=self.since))

    def open_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.api, headers={"X-Region": self.region})

    def report(self, client: httpx.Client) -> int:
        parcels: list[dict] = client.get("/parcels", params={"since": self.since, "limit": self.limit}).json()
        lost: list[dict] = [p for p in parcels if p["status"] == "lost"]
        print(Msg.lost(count=len(lost)))
        return 1 if lost else 0


def cmd_audit(args) -> int:
    audit: ParcelAudit = ParcelAudit.from_args(args)
    audit.announce()
    with audit.open_client() as client:
        return audit.report(client)


@click.command()
def cmd_units() -> None:
    click.echo_via_pager({
        "kg": "kilogram",
        "g": "gram",
        "lb": "pound",
        "oz": "ounce",
        "m": "metre",
        "cm": "centimetre",
        "mm": "millimetre",
        "km": "kilometre",
        "in": "inch",
        "ft": "foot",
        "yd": "yard",
        "mi": "mile",
        "l": "litre",
        "ml": "millilitre",
        "gal": "gallon",
        "pt": "pint",
        "qt": "quart",
        "s": "second",
        "min": "minute",
        "h": "hour",
        "d": "day",
        "wk": "week",
        "mo": "month",
        "yr": "year",
        "c": "celsius",
        "f": "fahrenheit",
        "k": "kelvin",
        "pa": "pascal",
        "bar": "bar",
        "psi": "psi",
        "n": "newton",
        "j": "joule",
        "w": "watt",
    })
