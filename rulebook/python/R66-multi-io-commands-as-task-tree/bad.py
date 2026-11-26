import os

import click
import httpx


def cmd_health(args) -> None:
    stations = args.stations
    for station in stations:  # expect: R66
        probe(station)


@click.command()
def check_mirrors(mirrors: list[tuple[str, int]]) -> None:
    results = {}
    for host, port in mirrors:  # expect: R66
        reachable = ping(host, port)
        results[host] = reachable
    click.echo(results)


async def cmd_fetch(urls: list[str]) -> None:
    async with httpx.AsyncClient() as client:
        for url in urls:  # expect: R66
            await client.get(url)


def cmd_sizes(paths: list[str]) -> None:
    sizes = []
    for path in paths:  # expect-llm: R66
        sizes.append(os.path.getsize(path))
    print(sum(sizes))
