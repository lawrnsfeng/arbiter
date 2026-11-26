import asyncio
import queue
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI

from weather.constants import SENSOR_PORT


class StationPoller:
    def __init__(self, client) -> None:
        self._client = client
        self._lock = asyncio.Lock()
        self.pending: queue.Queue[str] = queue.Queue()

    async def run(self) -> None:
        while True:
            async with self._lock:
                await self._client.fetch_latest()
            humidity: float = await asyncio.to_thread(read_serial_sensor, SENSOR_PORT)
            self.pending.put(str(humidity))
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    poller: StationPoller = StationPoller(app.state.client)
    task: asyncio.Task[None] = asyncio.create_task(poller.run())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(lifespan=lifespan)


def main() -> None:
    # main-thread entry point of a CLI: the one loop of the process
    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(sync_stations())
    finally:
        loop.close()


@pytest.fixture
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    yield loop
    loop.close()
