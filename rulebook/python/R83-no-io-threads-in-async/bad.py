import asyncio
import threading

from fastapi import FastAPI

app = FastAPI()


class StationPoller:
    def __init__(self, client) -> None:
        self._client = client
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)  # expect: R83
        self._thread.start()

    def _run(self) -> None:
        loop = asyncio.new_event_loop()  # expect: R83
        while True:
            loop.run_until_complete(self._client.fetch_latest())


class ArchiveUploader(threading.Thread):  # expect: R83
    def run(self) -> None:
        upload_archive("readings.tar")


threading.Thread(target=flush_readings_forever, daemon=True).start()  # expect: R83


class GaugeTask:
    def __init__(self) -> None:
        self._stop = asyncio.Event()

    async def run(self, client) -> None:
        while not self._stop.is_set():  # expect-llm: R83
            await client.fetch_latest()
            await asyncio.sleep(5)


class RetryScheduler:
    def schedule(self, delay_s: float) -> None:
        threading.Timer(delay_s, self.retry_upload).start()  # expect: R83


async def latest_humidity(station: str) -> float:
    return requests.get(f"https://weather.example/{station}/humidity").json()["value"]  # expect-llm: R83
