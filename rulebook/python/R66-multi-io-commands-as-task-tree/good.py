import asyncio
import logging
from dataclasses import dataclass

from weatherkit.flow import FlowNarrator, Leaf, run_tree
from weatherkit.stations import ping_station
from weatherkit.tasks import StationsTask

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StationProbe(Leaf):
    code: str

    async def run(self) -> bool:
        return await asyncio.to_thread(ping_station, self.code)


def cmd_health(args) -> None:
    root: StationsTask = StationsTask(tuple(StationProbe(code) for code in args.stations))
    run_tree(root, depth=2, progress=FlowNarrator(verbose=True))


def cmd_list(args) -> None:
    for station in args.stations:
        print(station)
        log.info("listed %s", station)


def cmd_merge(args) -> None:
    summary: dict[str, int] = {}
    for chunk in args.chunks:
        summary = fold(summary, chunk)
    print(summary)


def probe_all(stations: list[str]) -> None:
    for station in stations:
        probe(station)
