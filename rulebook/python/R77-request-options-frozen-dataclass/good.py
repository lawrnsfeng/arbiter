from dataclasses import asdict, dataclass

import httpx


@dataclass(frozen=True)
class SearchOptions:
    title: str | None = None
    author: str | None = None
    genre: str | None = None
    language: str = "en"
    available_only: bool = True
    page: int = 1
    per_page: int = 50
    sort: str = "title"
    order: str = "asc"


class CatalogClient:
    def __init__(self, http: httpx.AsyncClient, *, base=None, timeout=10, retries=3, proxy=None, verify=True, agent=None) -> None:
        self._http = http

    async def search_books(self, options: SearchOptions | None = None) -> list[Book]:
        params: dict[str, object] = {k: v for k, v in asdict(options or SearchOptions()).items() if v is not None}
        response: httpx.Response = await self._http.get("/books", params=params)
        return BookPage.from_json(response.content).items


class ParcelApi:
    def __init__(self, transport) -> None:
        self._transport = transport

    # 1:1 create call: every keyword is one server field of the same name
    def create_parcel(self, *, sender=None, recipient=None, weight_g=0, width=0, height=0, depth=0):
        self._transport.send(
            "create",
            {"sender": sender, "recipient": recipient, "weight_g": weight_g, "width": width, "height": height, "depth": depth},
        )

    # seven keywords spread over separate calls: not one forwarded request
    def configure(self, *, retries=3, backoff=1.0, timeout=5, region="eu", verbose=False, cache=True, tag=None):
        self._transport.set_retry(retries, backoff)
        self._transport.set_timeout(timeout)
        self._transport.set_region(region)
        self._transport.set_logging(verbose, tag)
        self._transport.set_cache(cache)
