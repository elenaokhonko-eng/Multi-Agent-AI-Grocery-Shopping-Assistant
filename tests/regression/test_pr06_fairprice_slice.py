import asyncio

from packages.retailers.fairprice.adapter import FairPriceAdapter


def test_fairprice_pinned_sku_resolution():
    async def run_test():
        adapter = FairPriceAdapter()
        pinned = await adapter.resolve_pinned_sku("FP_102030")
        assert pinned is not None
        assert pinned.retailer_sku == "FP_102030"
        assert pinned.store_id == "fairprice"
        assert pinned.price_cents == 635
        assert pinned.unit_measure == "L"
        assert pinned.is_exact_match is True

        # Invalid prefix returns None
        invalid = await adapter.resolve_pinned_sku("SS_203040")
        assert invalid is None

    asyncio.run(run_test())


def test_fairprice_fee_structure_under_and_over_threshold():
    async def run_test():
        adapter = FairPriceAdapter()

        # 1. Under $80.00 threshold ($6.35 subtotal)
        await adapter.add_item_to_cart("FP_102030", 1)
        cart = await adapter.read_cart()

        assert cart.subtotal_cents == 635
        assert cart.free_delivery_threshold_cents == 8000
        assert cart.delivery_fee_cents == 599  # $5.99 delivery fee
        assert cart.service_fee_cents == 199  # $1.99 service fee
        assert cart.bag_fee_cents == 20  # $0.20 bag fee
        assert cart.slot_fee_cents == 0
        assert cart.gross_total_cents == 635 + 599 + 199 + 20  # 1453 cents ($14.53)

        # 2. Over $80.00 threshold (add 13 items -> $82.55 subtotal)
        await adapter.add_item_to_cart("FP_102030", 13)
        cart_over = await adapter.read_cart()

        assert cart_over.subtotal_cents == 635 * 13  # 8255 cents ($82.55)
        assert cart_over.delivery_fee_cents == 0  # Free delivery unlocked
        assert cart_over.service_fee_cents == 199
        assert cart_over.bag_fee_cents == 20
        assert cart_over.gross_total_cents == 8255 + 0 + 199 + 20  # 8474 cents ($84.74)

    asyncio.run(run_test())


def test_fairprice_slot_selection_and_fee_update():
    async def run_test():
        adapter = FairPriceAdapter()
        await adapter.add_item_to_cart("FP_102030", 1)

        slots = await adapter.list_delivery_slots()
        assert len(slots) >= 2

        # Select peak slot with $2.00 fee
        success = await adapter.select_delivery_slot("slot_fp_evening")
        assert success is True

        cart = await adapter.read_cart()
        assert cart.slot_fee_cents == 200
        assert cart.gross_total_cents == 635 + 599 + 199 + 20 + 200

    asyncio.run(run_test())


def test_fairprice_revalidation_diff_detection():
    async def run_test():
        adapter = FairPriceAdapter()
        await adapter.add_item_to_cart("FP_102030", 1)
        cart = await adapter.read_cart()

        # Diff against exact same quote -> no changes
        diff = await adapter.revalidate_cart(cart)
        assert diff.has_changes is False

        # Simulate unexpected price change
        class StaleQuote:
            gross_total_cents = 1000

        diff_changed = await adapter.revalidate_cart(StaleQuote())
        assert diff_changed.has_changes is True
        assert diff_changed.price_changed is True

    asyncio.run(run_test())
