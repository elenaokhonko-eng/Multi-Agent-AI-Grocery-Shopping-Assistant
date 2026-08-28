import asyncio
import pytest
from packages.retailers.fairprice.adapter import FairPriceAdapter
from packages.retailers.shengsiong.adapter import ShengSiongAdapter
from packages.retailers.littlefarms.adapter import LittleFarmsAdapter
from packages.retailers.redmart.adapter import RedMartAdapter
from packages.retailers.base import RetailerAdapter, CandidateProduct

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

        # 2. Candidate Validation
        is_valid = adapter.validate_candidate(candidate, {
            "name": "Fresh Milk",
            "category": "Dairy",
            "exclusions": ["soy", "almond"]
        })
        assert is_valid is True

        # 3. Add Exact Item
        add_success = await adapter.add_exact_item(candidate.retailer_sku, quantity=2)
        assert add_success is True

        # 4. Read Cart
        cart = await adapter.read_cart()
        assert cart.retailer_id == store_id
        assert len(cart.lines) >= 1
        assert cart.subtotal_cents > 0
        assert cart.gross_total_cents >= cart.subtotal_cents
        assert cart.unowned_items_detected is False

        # 5. List and Select Delivery Slots
        slots = await adapter.list_delivery_slots()
        assert len(slots) > 0
        assert slots[0].is_available is True
        select_success = await adapter.select_delivery_slot(slots[0].slot_id)
        assert select_success is True

        # 6. Revalidate Cart
        diff = await adapter.revalidate_cart("dummy_fp")
        assert diff.has_changes is False

        # 7. Order Confirmation
        conf = await adapter.submit_order("tok_test_approval")
        assert conf.retailer_order_id.startswith(expected_prefix)
        assert conf.confirmed_total_cents == cart.gross_total_cents
        assert conf.is_uncertain is False

    asyncio.run(_test())

def test_shengsiong_lemon_exclusion_gate():
    async def _test():
        # Sheng Siong lemon search must strictly reject detergents and teas (SS-07)
        adapter = ShengSiongAdapter()
        candidates = await adapter.search_candidates("lemon")
        
        # 3 candidates: fresh lemons, lemon dishwashing detergent, lemon tea
        assert len(candidates) == 3

        desired_item = {
            "name": "Fresh Lemons",
            "category": "Produce",
            "exclusions": ["detergent", "dishwashing", "tea", "beer", "cleaning"]
        }

        results = {c.title: adapter.validate_candidate(c, desired_item) for c in candidates}

        # Fresh lemons must pass
        assert results["Fresh South African Lemons 3s"] is True
        # Detergent and Tea must fail
        assert results["Lemon Dishwashing Liquid Detergent 1L"] is False
        assert results["Lemon Tea 6x250ml"] is False

    asyncio.run(_test())
