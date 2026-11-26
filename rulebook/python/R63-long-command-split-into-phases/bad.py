import json
import sys

import click
import httpx


def cmd_audit(args) -> int:  # expect: R63
    """Audit parcels in transit."""
    region = args.region or "north"
    limit = args.limit or 50
    if args.since:
        since = args.since
    else:
        since = "1970-01-01"
    verbose = args.verbose
    print(f"auditing {region} since {since}")
    if verbose:
        print(f"limit {limit}")
    client = httpx.Client(base_url=args.api)
    client.headers["X-Region"] = region
    response = client.get("/parcels", params={"since": since, "limit": limit})
    response.raise_for_status()
    parcels = response.json()
    late = []
    lost = []
    for parcel in parcels:
        if parcel["status"] == "lost":
            lost.append(parcel)
        elif parcel["eta"] < parcel["promised"]:
            continue
        else:
            late.append(parcel)
    print(f"{len(late)} late")
    print(f"{len(lost)} lost")
    if args.json:
        json.dump({"late": late, "lost": lost}, sys.stdout)
    if lost:
        client.post("/alerts", json={"lost": [p["id"] for p in lost]})
    client.close()
    return 1 if lost else 0


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--depot")
def sync_parcels(depot: str) -> None:  # expect: R63
    depot = depot or "central"
    click.echo(f"syncing {depot}")
    client = httpx.Client()
    page = 1
    seen = 0
    while True:
        batch = client.get("/parcels", params={"depot": depot, "page": page}).json()
        if not batch:
            break
        for parcel in batch:
            seen += 1
            if parcel["weight"] > 30:
                click.echo(f"heavy {parcel['id']}")
            if parcel["fragile"]:
                click.echo(f"fragile {parcel['id']}")
        page += 1
    click.echo(f"{seen} parcels")
    if seen == 0:
        click.echo("nothing to do")
        return
    summary = client.get("/summary", params={"depot": depot}).json()
    click.echo(json.dumps(summary))
    totals = {}
    for key, value in summary.items():
        totals[key] = value
    click.echo(f"{len(totals)} totals")
    client.post("/synced", json={"depot": depot, "seen": seen})
    client.close()
    click.echo("done")
    click.echo("bye")
    click.echo("")


async def cmd_dispatch(args) -> None:  # expect: R63
    van = args.van
    route = args.route
    stops = args.stops.split(",")
    async with httpx.AsyncClient() as client:
        await client.post("/vans/claim", json={"van": van})
        for stop in stops:
            await client.post("/stops", json={"van": van, "stop": stop, "route": route})
        status = await client.get(f"/vans/{van}")
        state = status.json()
        if state["fuel"] < 10:
            await client.post("/vans/refuel", json={"van": van})
        if state["driver"] is None:
            await client.post("/vans/assign", json={"van": van})
        print(state)
        print(route)
        print(stops)
        await client.post("/routes/open", json={"route": route})
        await client.post("/routes/notify", json={"route": route})
        await client.post("/routes/lock", json={"route": route})
        await client.post("/routes/print", json={"route": route})
        await client.post("/routes/tag", json={"route": route})
        await client.post("/routes/seal", json={"route": route})
        await client.post("/routes/load", json={"route": route})
        await client.post("/routes/depart", json={"route": route})
        await client.post("/routes/track", json={"route": route})
        await client.post("/routes/ping", json={"route": route})
        await client.post("/routes/eta", json={"route": route})
        await client.post("/routes/close", json={"route": route})
        await client.post("/routes/archive", json={"route": route})
        await client.post("/vans/release", json={"van": van})
    print("dispatched")


def cmd_label(args) -> None:  # expect-llm: R63
    printer = args.printer or "default"
    size = args.size or "a6"
    print(f"printing on {printer} ({size})")
    client = httpx.Client()
    for parcel in client.get("/parcels/unlabelled").json():
        client.post("/labels", json={"parcel": parcel["id"], "size": size, "printer": printer})
    client.close()
