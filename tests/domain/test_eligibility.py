import uuid
from datetime import datetime, timezone
from domain.models.core import ShoppingList, ShoppingListItem, StoreQuote, QuoteLine
from domain.services.eligibility import evaluate_quote_completeness, rank_quotes, get_cheapest_complete_quote

def _create_mock_shopping_list():
    sl_id = uuid.uuid4()
    item1 = ShoppingListItem(id=uuid.uuid4(), name="eggs", desired_quantity=1, must_have=True, shopping_list_id=sl_id)
    item2 = ShoppingListItem(id=uuid.uuid4(), name="milk", desired_quantity=1, must_have=True, shopping_list_id=sl_id)
    item3 = ShoppingListItem(id=uuid.uuid4(), name="apples", desired_quantity=1, must_have=False, shopping_list_id=sl_id)
    
    sl = ShoppingList(id=sl_id, name="Groceries")
    sl.items = [item1, item2, item3]
    return sl, item1, item2, item3

def test_evaluate_quote_completeness_complete():
    sl, item1, item2, item3 = _create_mock_shopping_list()
    
    quote = StoreQuote(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        retailer_id="StoreA",
        cart_fingerprint="fp1",
        subtotal_cents=800,
        delivery_fee_cents=0,
        gross_total_cents=800,
        derived_net_cents=734,
        gst_cents=66,
        expires_at=datetime.now(timezone.utc)
    )
    ql1 = QuoteLine(
        id=uuid.uuid4(),
        quote_id=quote.id,
        shopping_item_id=item1.id,
        retailer_sku="sku1",
        product_title="Eggs",
        product_url="https://store.a/eggs",
        requested_quantity=1,
        packs_added=1,
        is_in_stock=True,
        is_exact_match=True,
        unit_price_cents=500,
        line_total_cents=500
    )
    ql2 = QuoteLine(
        id=uuid.uuid4(),
        quote_id=quote.id,
        shopping_item_id=item2.id,
        retailer_sku="sku2",
        product_title="Milk",
        product_url="https://store.a/milk",
        requested_quantity=1,
        packs_added=1,
        is_in_stock=True,
        is_exact_match=True,
        unit_price_cents=300,
        line_total_cents=300
    )
    
    quote.lines = [ql1, ql2]
    
    assert evaluate_quote_completeness(sl, quote) is True

def test_evaluate_quote_completeness_incomplete():
    sl, item1, item2, item3 = _create_mock_shopping_list()
    
    # Missing milk (item2)
    quote = StoreQuote(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        retailer_id="StoreA",
        cart_fingerprint="fp1",
        subtotal_cents=500,
        delivery_fee_cents=0,
        gross_total_cents=500,
        derived_net_cents=459,
        gst_cents=41,
        expires_at=datetime.now(timezone.utc)
    )
    ql1 = QuoteLine(
        id=uuid.uuid4(),
        quote_id=quote.id,
        shopping_item_id=item1.id,
        retailer_sku="sku1",
        product_title="Eggs",
        product_url="https://store.a/eggs",
        requested_quantity=1,
        packs_added=1,
        is_in_stock=True,
        is_exact_match=True,
        unit_price_cents=500,
        line_total_cents=500
    )
    
    quote.lines = [ql1]
    
    assert evaluate_quote_completeness(sl, quote) is False

def test_rank_quotes_partial_never_outranks_complete():
    # Quote A: Incomplete but cheaper (S$30)
    quote_a = StoreQuote(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        retailer_id="StoreA",
        cart_fingerprint="fpa",
        subtotal_cents=3000,
        delivery_fee_cents=0,
        gross_total_cents=3000,
        derived_net_cents=2752,
        gst_cents=248,
        is_complete=False,
        expires_at=datetime.now(timezone.utc)
    )
    
    # Quote B: Complete but more expensive (S$40)
    quote_b = StoreQuote(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        retailer_id="StoreB",
        cart_fingerprint="fpb",
        subtotal_cents=4000,
        delivery_fee_cents=0,
        gross_total_cents=4000,
        derived_net_cents=3670,
        gst_cents=330,
        is_complete=True,
        expires_at=datetime.now(timezone.utc)
    )
    
    ranked = rank_quotes([quote_a, quote_b])
    
    assert ranked[0].id == quote_b.id
    assert ranked[1].id == quote_a.id

def test_cheapest_complete_quote():
    q1 = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), retailer_id="StoreA", cart_fingerprint="fp1", subtotal_cents=3000, delivery_fee_cents=0, gross_total_cents=3000, derived_net_cents=2752, gst_cents=248, is_complete=False, expires_at=datetime.now(timezone.utc))
    q2 = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), retailer_id="StoreB", cart_fingerprint="fp2", subtotal_cents=5000, delivery_fee_cents=0, gross_total_cents=5000, derived_net_cents=4587, gst_cents=413, is_complete=True, expires_at=datetime.now(timezone.utc))
    q3 = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), retailer_id="StoreC", cart_fingerprint="fp3", subtotal_cents=4500, delivery_fee_cents=0, gross_total_cents=4500, derived_net_cents=4128, gst_cents=372, is_complete=True, expires_at=datetime.now(timezone.utc))
    
    best = get_cheapest_complete_quote([q1, q2, q3])
    
    assert best is not None
    assert best.id == q3.id
