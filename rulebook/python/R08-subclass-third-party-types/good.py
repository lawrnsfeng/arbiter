import hashlib

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from redis import Redis


class LibraryApi(httpx.Client):
    def holds(self, member: str) -> list:
        reply = self.get(f"/members/{member}/holds")
        reply.raise_for_status()
        return reply.json()

    def renew(self, loan_id: str) -> None:
        self.post(f"/loans/{loan_id}/renew").raise_for_status()


class WaitList(Redis):
    def waiting(self, isbn: str) -> int:
        return self.llen(f"waitlist:{isbn}")


def plain_client(base_url: str) -> httpx.Client:
    client = httpx.Client(base_url=base_url)
    client.headers["Accept"] = "application/json"
    return client


def loans_csv(rows: list[dict[str, str]]) -> str:
    frame = pd.DataFrame(rows)
    return frame.to_csv(index=False)


def page_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("h1").get_text()


def cover_digest(image: bytes) -> str:
    digest = hashlib.sha256(image)
    return digest.hexdigest()
