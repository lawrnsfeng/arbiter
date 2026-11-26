import httpx


class CatalogClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def search_books(  # expect: R77
        self,
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        language: str = "en",
        available_only: bool = True,
        page: int = 1,
        per_page: int = 50,
        sort: str = "title",
        order: str = "asc",
    ) -> list[dict]:
        params = {
            "title": title,
            "author": author,
            "genre": genre,
            "language": language,
            "available": available_only,
            "page": page,
            "per_page": per_page,
            "sort": sort,
            "order": order,
        }
        response = await self._http.get("/books", params={k: v for k, v in params.items() if v is not None})
        return response.json()["items"]


class ForecastClient:
    def __init__(self, session) -> None:
        self._session = session

    def readings(self, station, start=None, end=None, unit="c", step="1h", fields=None, limit=500):  # expect: R77
        return self._session.request(
            "GET", f"/stations/{station}/readings", start=start, end=end, unit=unit, step=step, fields=fields, limit=limit
        )


class ParcelApi:
    def __init__(self, transport) -> None:
        self._transport = transport

    def track(self, *, carrier=None, status=None, since=None, until=None, region=None, signed=None):  # expect: R77
        self._transport.send("track", {"carrier": carrier, "status": status, "since": since, "until": until, "region": region, "signed": signed})

    # a create call that renames and merges keywords before sending is no longer 1:1
    def create_parcel(self, *, sender=None, recipient=None, weight_g=0, width=0, height=0, depth=0):  # expect-llm: R77
        dims = f"{width}x{height}x{depth}"
        self._transport.send("create", {"from": sender, "to": recipient, "grams": weight_g, "dims": dims})
