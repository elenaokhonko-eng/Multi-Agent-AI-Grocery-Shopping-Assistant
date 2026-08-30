from domain.models.core import ShoppingList, StoreQuote


def evaluate_quote_completeness(shopping_list: ShoppingList, quote: StoreQuote) -> bool:
    """
    Evaluates whether a quote fulfills all 'must_have' items in the shopping list.
    """
    must_have_item_ids = {item.id for item in shopping_list.items if item.must_have}

    fulfilled_item_ids = set()
    for line in quote.lines:
        if line.is_in_stock:
            fulfilled_item_ids.add(line.shopping_item_id)

    return must_have_item_ids.issubset(fulfilled_item_ids)


def rank_quotes(quotes: list[StoreQuote]) -> list[StoreQuote]:
    """
    Rank quotes based on the primary rule:
    1. Complete quotes always outrank incomplete quotes.
    2. Within the same completeness tier, rank by lowest gross_total_cents.
    """

    def sorting_key(q: StoreQuote) -> tuple[int, int]:
        total = getattr(q, "gross_total_cents", getattr(q, "total_cents", 0))
        return (not q.is_complete, total)

    return sorted(quotes, key=sorting_key)


def get_cheapest_complete_quote(quotes: list[StoreQuote]) -> StoreQuote | None:
    """
    Returns the cheapest quote that is fully complete, or None if no complete quotes exist.
    """
    complete_quotes = [q for q in quotes if q.is_complete]
    if not complete_quotes:
        return None
    return rank_quotes(complete_quotes)[0]
