from domain.services.matching import (
    calculate_required_packs,
    is_excluded_by_negative_filter,
    match_product_candidate,
    parse_pack_size,
)


def test_parse_pack_size_various_formats():
    p1 = parse_pack_size("Meiji Fresh Milk 2L")
    assert p1 is not None
    assert p1.amount == 2.0
    assert p1.unit.lower() == "l"

    p2 = parse_pack_size("Chew's Fresh Eggs 10s")
    assert p2 is not None
    assert p2.amount == 10.0
    assert p2.unit.lower() in ["s", "pieces"]

    p3 = parse_pack_size("Fresh South African Lemons 3s Pack")
    assert p3 is not None
    assert p3.amount == 3.0
    assert p3.unit.lower() in ["s", "pieces"]

    p4 = parse_pack_size("Barambah Organic Greek Yoghurt 500g")
    assert p4 is not None
    assert p4.amount == 500.0
    assert p4.unit.lower() == "g"


def test_calculate_required_packs_lemons_pieces_vs_packs():
    # User requests 3 lemons in "pieces"
    pack_3s = parse_pack_size("Fresh Lemons 3s Pack")
    packs, _ = calculate_required_packs(desired_qty=3, desired_unit="pieces", product_pack=pack_3s)
    # 3 desired lemons / 3 in a pack = 1 pack needed
    assert packs == 1

    # User requests 6 lemons in "pieces"
    packs_6, _ = calculate_required_packs(desired_qty=6, desired_unit="pieces", product_pack=pack_3s)
    assert packs_6 == 2


def test_negative_exclusion_filter_lemons():
    # Fresh food produces should be allowed
    is_exc, _ = is_excluded_by_negative_filter("Fresh South African Lemons 3s", category="Produce")
    assert is_exc is False

    # Non-food products must be rejected by produce negative keywords
    is_exc_dishwash, reason = is_excluded_by_negative_filter(
        "Mama Lemon Dishwashing Liquid 750ml", category="Household"
    )
    assert is_exc_dishwash is True
    assert "dishwash" in reason.lower()

    is_exc_tea, reason_tea = is_excluded_by_negative_filter("Lipton Lemon Tea Bag 25s", category="Beverages")
    assert is_exc_tea is True
    assert "tea" in reason_tea.lower()


def test_match_product_candidate_pinned_sku_override():
    item_spec = {
        "name": "Fresh Milk",
        "desired_quantity": 2,
        "unit_measure": "L",
        "pinned_skus": {"fairprice": "FP_102030"},
    }

    is_match, packs, _ = match_product_candidate(
        candidate_title="Meiji Fresh Milk 2L",
        candidate_sku="FP_102030",
        candidate_brand="Meiji",
        candidate_category="Dairy",
        candidate_pack="2L",
        item_spec=item_spec,
    )
    assert is_match is True
    # 2L desired / 2L pack = 1 pack needed
    assert packs == 1
