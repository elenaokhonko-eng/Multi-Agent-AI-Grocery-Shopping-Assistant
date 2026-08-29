import asyncio

import pytest

from packages.domain.services.matching import is_excluded_by_negative_filter
from packages.retailers.base import CandidateProduct, RetailerAdapter
from packages.retailers.fairprice.adapter import FairPriceAdapter
from packages.retailers.littlefarms.adapter import LittleFarmsAdapter
from packages.retailers.redmart.adapter import RedMartAdapter
from packages.retailers.shengsiong.adapter import ShengSiongAdapter


@pytest.mark.parametrize("adapter_cls, store_id, expected_prefix", [
    (FairPriceAdapter, "fairprice", "FP-"),
    (ShengSiongAdapter, "shengsiong", "SS-"),
    (LittleFarmsAdapter, "littlefarms", "LF-"),
    (RedMartAdapter, "redmart", "RM-"),
])
def test_adapter_contract_full_lifecycle(adapter_cls, store_id, expected_prefix):
    async def _test():
        adapter: RetailerAdapter = adapter_cls()
        assert adapter.retailer_id == store_id

        # 1. Search Candidates
        candidates = await adapter.search_candidates("milk")
        assert len(candidates) > 0
        candidate = candidates[0]
        assert isinstance(candidate, CandidateProduct)
        assert candidate.store_id == store_id
        assert candidate.price_cents > 0
        assert candidate.in_stock is True

        # 2. Add Item To Cart
        add_success = await adapter.add_item_to_cart(candidate.retailer_sku, quantity=2)
        assert add_success is True

        # 3. Read Cart
        cart = await adapter.read_cart()
        assert cart.retailer_id == store_id
        assert len(cart.lines) >= 1
        assert cart.subtotal_cents > 0
        assert cart.gross_total_cents >= cart.subtotal_cents
        assert cart.unowned_items_detected is False

        # 4. List and Select Delivery Slots
        slots = await adapter.list_delivery_slots()
        assert len(slots) > 0
        assert slots[0].is_available is True
        select_success = await adapter.select_delivery_slot(slots[0].slot_id)
        assert select_success is True

        # 5. Revalidate Cart
        diff = await adapter.revalidate_cart(cart)
        assert diff.has_changes is False

        # 6. Order Confirmation
        conf = await adapter.submit_order("tok_test_approval")
        assert conf.retailer_order_id.startswith(expected_prefix)
        assert conf.confirmed_total_cents == cart.gross_total_cents

    asyncio.run(_test())


def test_shengsiong_lemon_exclusion_gate():
    # Negative exclusion check for produce
    cand_fresh = "Fresh South African Lemons 3s"
    cand_detergent = "Lemon Dishwashing Liquid Detergent 1L"
    cand_tea = "Lemon Tea 6x250ml"

    exc_fresh, _ = is_excluded_by_negative_filter(cand_fresh, category="Produce")
    assert exc_fresh is False

    exc_det, reason_det = is_excluded_by_negative_filter(cand_detergent, category="Household")
    assert exc_det is True
    assert "detergent" in reason_det.lower() or "dishwash" in reason_det.lower()

    exc_tea, reason_tea = is_excluded_by_negative_filter(cand_tea, category="Beverages")
    assert exc_tea is True
    assert "tea" in reason_tea.lower()
