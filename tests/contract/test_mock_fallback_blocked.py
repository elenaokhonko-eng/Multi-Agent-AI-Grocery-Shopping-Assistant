import asyncio

import pytest

from packages.retailers import (
    FairPriceAdapter,
    LittleFarmsAdapter,
    RedMartAdapter,
    ShengSiongAdapter,
)


def test_fairprice_raises_when_mock_fallback_blocked(monkeypatch):
    async def _test():
        monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
        adapter = FairPriceAdapter()
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.search_candidates("Nonexistent Unknown Product XYZ999", None)
        assert "LIVE_RUN_MOCK_BLOCKED" in str(exc_info.value)
    asyncio.run(_test())


def test_shengsiong_raises_when_mock_fallback_blocked(monkeypatch):
    async def _test():
        monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
        adapter = ShengSiongAdapter()
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.search_candidates("Nonexistent Unknown Product XYZ999", None)
        assert "LIVE_RUN_MOCK_BLOCKED" in str(exc_info.value)
    asyncio.run(_test())


def test_littlefarms_raises_when_mock_fallback_blocked(monkeypatch):
    async def _test():
        monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
        adapter = LittleFarmsAdapter()
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.search_candidates("Nonexistent Unknown Product XYZ999", None)
        assert "LIVE_RUN_MOCK_BLOCKED" in str(exc_info.value)
    asyncio.run(_test())


def test_redmart_raises_when_mock_fallback_blocked(monkeypatch):
    async def _test():
        monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "false")
        adapter = RedMartAdapter()
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.search_candidates("Nonexistent Unknown Product XYZ999", None)
        assert "LIVE_RUN_MOCK_BLOCKED" in str(exc_info.value)
    asyncio.run(_test())

