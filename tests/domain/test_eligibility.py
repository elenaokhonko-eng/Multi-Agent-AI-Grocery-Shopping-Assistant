import uuid
from domain.models.core import ShoppingList, ShoppingListItem, StoreQuote, QuoteLine, ProductCandidate, MatchDecision
from domain.services.eligibility import evaluate_quote_completeness, rank_quotes, get_cheapest_complete_quote

def _create_mock_shopping_list():
    item1 = ShoppingListItem(id=uuid.uuid4(), keyword="eggs", quantity=1, must_have=True, shopping_list_id=uuid.uuid4())
    item2 = ShoppingListItem(id=uuid.uuid4(), keyword="milk", quantity=1, must_have=True, shopping_list_id=uuid.uuid4())
    item3 = ShoppingListItem(id=uuid.uuid4(), keyword="apples", quantity=1, must_have=False, shopping_list_id=uuid.uuid4())
    
    sl = ShoppingList(id=uuid.uuid4(), name="Groceries")
    sl.items = [item1, item2, item3]
    return sl, item1, item2, item3

def test_evaluate_quote_completeness_complete():
    sl, item1, item2, item3 = _create_mock_shopping_list()
    
    # Create product candidates and match decisions
    pc1 = ProductCandidate(id=uuid.uuid4(), store_name="StoreA", retailer_sku="sku1", title="Eggs", price_cents=500)
    pc2 = ProductCandidate(id=uuid.uuid4(), store_name="StoreA", retailer_sku="sku2", title="Milk", price_cents=300)
    
    md1 = MatchDecision(item_id=item1.id, candidate_id=pc1.id, is_match=True, confidence_score=0.99)
    md2 = MatchDecision(item_id=item2.id, candidate_id=pc2.id, is_match=True, confidence_score=0.99)
    
    pc1.match_decisions = [md1]
    pc2.match_decisions = [md2]
    
    # Create quote
    quote = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), store_name="StoreA", subtotal_cents=800, delivery_fee_cents=0, total_cents=800)
    ql1 = QuoteLine(id=uuid.uuid4(), quote_id=quote.id, candidate_id=pc1.id, quantity=1, line_total_cents=500)
    ql1.product_candidate = pc1
    ql2 = QuoteLine(id=uuid.uuid4(), quote_id=quote.id, candidate_id=pc2.id, quantity=1, line_total_cents=300)
    ql2.product_candidate = pc2
    
    quote.lines = [ql1, ql2]
    
    assert evaluate_quote_completeness(sl, quote) is True

def test_evaluate_quote_completeness_incomplete():
    sl, item1, item2, item3 = _create_mock_shopping_list()
    
    # Missing milk
    pc1 = ProductCandidate(id=uuid.uuid4(), store_name="StoreA", retailer_sku="sku1", title="Eggs", price_cents=500)
    md1 = MatchDecision(item_id=item1.id, candidate_id=pc1.id, is_match=True, confidence_score=0.99)
    pc1.match_decisions = [md1]
    
    quote = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), store_name="StoreA", subtotal_cents=500, delivery_fee_cents=0, total_cents=500)
    ql1 = QuoteLine(id=uuid.uuid4(), quote_id=quote.id, candidate_id=pc1.id, quantity=1, line_total_cents=500)
    ql1.product_candidate = pc1
    
    quote.lines = [ql1]
    
    assert evaluate_quote_completeness(sl, quote) is False

def test_rank_quotes_partial_never_outranks_complete():
    # Quote A: Incomplete but cheaper (S$30)
    quote_a = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), store_name="StoreA", subtotal_cents=3000, delivery_fee_cents=0, total_cents=3000, is_complete=False)
    
    # Quote B: Complete but more expensive (S$40)
    quote_b = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), store_name="StoreB", subtotal_cents=4000, delivery_fee_cents=0, total_cents=4000, is_complete=True)
    
    ranked = rank_quotes([quote_a, quote_b])
    
    assert ranked[0].id == quote_b.id
    assert ranked[1].id == quote_a.id

def test_cheapest_complete_quote():
    q1 = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), store_name="StoreA", subtotal_cents=3000, delivery_fee_cents=0, total_cents=3000, is_complete=False)
    q2 = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), store_name="StoreB", subtotal_cents=5000, delivery_fee_cents=0, total_cents=5000, is_complete=True)
    q3 = StoreQuote(id=uuid.uuid4(), run_id=uuid.uuid4(), store_name="StoreC", subtotal_cents=4500, delivery_fee_cents=0, total_cents=4500, is_complete=True)
    
    best = get_cheapest_complete_quote([q1, q2, q3])
    
    assert best is not None
    assert best.id == q3.id
