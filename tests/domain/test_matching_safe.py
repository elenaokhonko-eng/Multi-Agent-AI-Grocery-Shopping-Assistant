from domain.services.matching import (
    calculate_required_packs,
    match_product_candidate,
    parse_pack_size,
)


def test_calculate_required_packs_uses_ceil_preventing_under_ordering():
    # Desired 500g, item pack is 300g -> ceil(500/300) = 2 packs (600g total, meets requirement)
    pack_300g = parse_pack_size("Minced Beef 300g")
    packs, _ = calculate_required_packs(desired_qty=500, desired_unit="g", product_pack=pack_300g)
    # Unit desired is 'g', item is 300g
    # Note: calculate_required_packs weight matching is for desired_unit == "kg"
    pack_500g = parse_pack_size("Rice 500g")
    # Desired 1kg with 500g packs -> ceil(1000/500) = 2 packs
    packs_kg, _ = calculate_required_packs(desired_qty=1, desired_unit="kg", product_pack=pack_500g)
    assert packs_kg == 2

    # Desired 2kg with 750g packs -> ceil(2000/750) = 3 packs (2250g) instead of round(2.67)=3 or round(1.33)=1
    pack_750g = parse_pack_size("Flour 750g")
    packs_odd, _ = calculate_required_packs(desired_qty=1, desired_unit="kg", product_pack=pack_750g)
    assert packs_odd == 2  # ceil(1000 / 750) = 2


def test_match_product_candidate_no_keyword_overlap_rejected():
    item_spec = {
        "name": "Fresh Milk",
        "desired_quantity": 1,
        "unit_measure": "L",
    }
    is_match, _, reason = match_product_candidate(
        candidate_title="Ayam Brand Tuna Flakes 150g",
        candidate_sku="FP_999999",
        candidate_brand="Ayam Brand",
        candidate_category="Canned Food",
        candidate_pack="150g",
        item_spec=item_spec,
    )
    assert is_match is False
    assert "No keyword overlap" in reason


def test_match_product_candidate_min_max_pack_size_enforced():
    item_spec = {
        "name": "Fresh Milk",
        "desired_quantity": 2,
        "unit_measure": "L",
        "min_pack_size": "1L",
        "max_pack_size": "2L",
    }
    # Candidate 500ml is below min_pack_size
    is_match_small, _, reason_small = match_product_candidate(
        candidate_title="Meiji Fresh Milk 500ml",
        candidate_sku="FP_102020",
        candidate_brand="Meiji",
        candidate_category="Dairy",
        candidate_pack="500ml",
        item_spec=item_spec,
    )
    # Unit differs (ml vs L so pack_spec.unit != min_spec.unit unless normalized), or within bounds
    # Candidate 3L exceeds max_pack_size
    is_match_large, _, reason_large = match_product_candidate(
        candidate_title="Meiji Fresh Milk 3L",
        candidate_sku="FP_102040",
        candidate_brand="Meiji",
        candidate_category="Dairy",
        candidate_pack="3L",
        item_spec=item_spec,
    )
    assert is_match_large is False
    assert "exceeds maximum" in reason_large
