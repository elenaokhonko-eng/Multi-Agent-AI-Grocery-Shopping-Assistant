import asyncio

import pytest

from packages.retailers.base import AuthoritativeCart
from packages.retailers.littlefarms.adapter import LittleFarmsAdapter
from packages.retailers.redmart.adapter import RedMartAdapter
from packages.retailers.shengsiong.adapter import ShengSiongAdapter


class MockQuote:
    def __init__(self, retailer_id: str, lines: list, gross_total_cents: int):
        self.retailer_id = retailer_id
        self.lines = lines
        self.gross_total_cents = gross_total_cents
        self.total_cents = gross_total_cents


class MockQuoteLine:
    def __init__(self, sku: str, quantity: int, unit_price_cents: int):
        self.retailer_sku = sku
        self.sku = sku
        self.quantity = quantity
        self.packs_added = quantity
        self.unit_price_cents = unit_price_cents


def test_littlefarms_full_slice(monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "true")

    async def run_test():
        adapter = LittleFarmsAdapter()

        # 1. Pinned SKU
        pinned = await adapter.resolve_pinned_sku("LF_304050")
        assert pinned is not None
        assert pinned.retailer_sku == "LF_304050"
        assert pinned.store_id == "littlefarms"

        # 2. Search
        results = await adapter.search_candidates("milk")
        assert len(results) > 0
        assert any("barambah" in r.title.lower() or "milk" in r.title.lower() for r in results)

        # 3. Add to Cart & Cart Reading (Under $100 -> $12 delivery fee)
        added = await adapter.add_item_to_cart("LF_304050", 2)
        assert added is True

        cart = await adapter.read_cart()
        assert isinstance(cart, AuthoritativeCart)
        assert cart.subtotal_cents == 1900  # 2 * 950
        assert cart.delivery_fee_cents == 1200  # < 10000
        assert cart.service_fee_cents == 0
        assert cart.bag_fee_cents == 0
        assert cart.gross_total_cents == 1900 + 1200

        # 4. Slots
        slots = await adapter.list_delivery_slots()
        assert len(slots) > 0
        slot_selected = await adapter.select_delivery_slot(slots[0].slot_id)
        assert slot_selected is True

        # 5. Revalidation
        quote = MockQuote("littlefarms", [MockQuoteLine("LF_304050", 2, 950)], cart.gross_total_cents)
        diff = await adapter.revalidate_cart(quote)
        assert diff.has_changes is False

        # Drift detection
        drifted_quote = MockQuote("littlefarms", [MockQuoteLine("LF_304050", 1, 950)], cart.gross_total_cents - 950)
        diff_drift = await adapter.revalidate_cart(drifted_quote)
        assert diff_drift.has_changes is True

        # 6. Submit Order Guarded
        monkeypatch.setenv("LIVE_PURCHASE_ENABLED", "false")
        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.submit_order("token_123")
        assert "LIVE_PURCHASE_DISABLED" in str(exc_info.value) or "Live checkout is not yet implemented" in str(exc_info.value)

    asyncio.run(run_test())


def test_shengsiong_full_slice(monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "true")

    async def run_test():
        adapter = ShengSiongAdapter()

        # 1. Pinned SKU
        pinned = await adapter.resolve_pinned_sku("SS_203040")
        assert pinned is not None
        assert pinned.retailer_sku == "SS_203040"
        assert pinned.store_id == "shengsiong"

        # 2. Search
        results = await adapter.search_candidates("fresh milk")
        assert len(results) > 0
        assert any("meiji" in r.title.lower() or "milk" in r.title.lower() for r in results)

        # 3. Add to Cart & Cart Reading (Under $60 -> $4 delivery, $1.50 service, $0.10 bag)
        added = await adapter.add_item_to_cart("SS_203040", 2)
        assert added is True

        cart = await adapter.read_cart()
        assert isinstance(cart, AuthoritativeCart)
        assert cart.subtotal_cents == 1220  # 2 * 610
        assert cart.delivery_fee_cents == 400  # < 6000
        assert cart.service_fee_cents == 150
        assert cart.bag_fee_cents == 10
        assert cart.gross_total_cents == 1220 + 400 + 150 + 10

        # 4. Slots
        slots = await adapter.list_delivery_slots()
        assert len(slots) >= 2
        assert await adapter.select_delivery_slot(slots[0].slot_id) is True

        # 5. Revalidation
        quote = MockQuote("shengsiong", [MockQuoteLine("SS_203040", 2, 610)], cart.gross_total_cents)
        diff = await adapter.revalidate_cart(quote)
        assert diff.has_changes is False

        # 6. Submit Order Guarded
        monkeypatch.setenv("LIVE_PURCHASE_ENABLED", "false")
        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.submit_order("token_123")
        assert "LIVE_PURCHASE_DISABLED" in str(exc_info.value) or "Live checkout is not yet implemented" in str(exc_info.value)

    asyncio.run(run_test())


def test_redmart_full_slice(monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_FALLBACK", "true")

    async def run_test():
        adapter = RedMartAdapter()

        # 1. Pinned SKU
        pinned = await adapter.resolve_pinned_sku("RM_405060")
        assert pinned is not None
        assert pinned.retailer_sku == "RM_405060"
        assert pinned.store_id == "redmart"

        # 2. Search
        results = await adapter.search_candidates("milk")
        assert len(results) > 0
        assert any("milk" in r.title.lower() or "cowhead" in r.title.lower() for r in results)

        # 3. Add to Cart & Cart Reading (Under $60 -> $3.99 delivery, $0.99 service, $0.10 bag)
        added = await adapter.add_item_to_cart("RM_405060", 2)
        assert added is True

        cart = await adapter.read_cart()
        assert isinstance(cart, AuthoritativeCart)
        assert cart.subtotal_cents == 1250  # 2 * 625
        assert cart.delivery_fee_cents == 399  # < 6000
        assert cart.service_fee_cents == 99
        assert cart.bag_fee_cents == 10
        assert cart.gross_total_cents == 1250 + 399 + 99 + 10

        # 4. Slots
        slots = await adapter.list_delivery_slots()
        assert len(slots) >= 2
        assert await adapter.select_delivery_slot(slots[0].slot_id) is True

        # 5. Revalidation
        quote = MockQuote("redmart", [MockQuoteLine("RM_405060", 2, 625)], cart.gross_total_cents)
        diff = await adapter.revalidate_cart(quote)
        assert diff.has_changes is False

        # 6. Submit Order Guarded
        monkeypatch.setenv("LIVE_PURCHASE_ENABLED", "false")
        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.submit_order("token_123")
        assert "LIVE_PURCHASE_DISABLED" in str(exc_info.value) or "Live checkout is not yet implemented" in str(exc_info.value)

    asyncio.run(run_test())

