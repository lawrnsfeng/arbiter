import asyncio

from fetcher.load import load_all


async def fake_loader(key: str) -> str:
    await asyncio.sleep(0)
    return key.upper()


def test_load_all():
    assert asyncio.run(load_all(["a", "b"], fake_loader)) == {"a": "A", "b": "B"}
