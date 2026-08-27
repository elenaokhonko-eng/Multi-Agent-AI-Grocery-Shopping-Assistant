from typing import List, Optional
from domain.models.core import ShoppingList, StoreQuote


def evaluate_quote_completeness(
    shopping_list: ShoppingList, 
    quote: StoreQuote
) -> bool:
    """
    Evaluates whether a quote fulfills all 'must_have' items in the shopping list.
    If an item is marked 'must_have', the quote must contain at least one line item
    corresponding to a candidate for that intent.
    
    For now, we simplify: a quote is complete if it has a line item for EVERY
    must-have item in the shopping list.
    """
    must_have_item_ids = {item.id for item in shopping_list.items if item.must_have}
    
    # In a real implementation, we would map the quote.lines back to 
    # the shopping list item via MatchDecision. 
    # Here, we assume quote_lines reference product_candidates, which 
    # link to match_decisions, which link to shopping_list_items.
    
    fulfilled_item_ids = set()
    for line in quote.lines:
        candidate = line.product_candidate
        for match in candidate.match_decisions:
            if match.is_match:
                fulfilled_item_ids.add(match.item_id)
                
    return must_have_item_ids.issubset(fulfilled_item_ids)


def rank_quotes(quotes: List[StoreQuote]) -> List[StoreQuote]:
    """
    Rank quotes based on the primary rule:
    1. Complete quotes always outrank incomplete quotes.
    2. Within the same completeness tier, rank by lowest total_cents.
    """
    def sorting_key(q: StoreQuote) -> tuple[int, int]:
        # Sort by is_complete (True comes first, so we invert it with `not`), then by total_cents
        return (not q.is_complete, q.total_cents)
        
    return sorted(quotes, key=sorting_key)


def get_cheapest_complete_quote(quotes: List[StoreQuote]) -> Optional[StoreQuote]:
    """
    Returns the cheapest quote that is fully complete, or None if no complete quotes exist.
    """
    complete_quotes = [q for q in quotes if q.is_complete]
    if not complete_quotes:
        return None
    return rank_quotes(complete_quotes)[0]
