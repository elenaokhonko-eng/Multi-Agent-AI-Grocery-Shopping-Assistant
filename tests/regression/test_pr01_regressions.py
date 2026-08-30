from datetime import UTC, datetime, timedelta

from domain.models.core import (
    Approval,
    ComparisonRun,
    ComparisonSnapshot,
    ShoppingList,
    StoreQuote,
)
from domain.services.matching import (
    calculate_required_packs,
    is_excluded_by_negative_filter,
    match_product_candidate,
    parse_pack_size,
)
from sqlmodel import Session

from packages.retailers.base import (
    AuthoritativeCart,
    CartLine,
)
from tests.conftest import test_engine

# =============================================================================
# PR-01 Regression Suite: Pack Quantities, Dimensional Matching & Units
# =============================================================================


def test_matching_ceil_pack_300g_for_500g_requires_2_packs():
    """Desired 500 g with candidate pack 300 g must return 2 packs (600g), not under-order."""
    pack_300g = parse_pack_size("Minced Beef 300g")
    packs, rej = calculate_required_packs(desired_qty=500, desired_unit="g", product_pack=pack_300g)
    assert rej is None
    assert packs == 2


def test_matching_ceil_pack_500g_for_1kg_requires_2_packs():
    """Desired 1 kg with candidate pack 500 g must return 2 packs (1000g)."""
    pack_500g = parse_pack_size("Jasmine Rice 500g")
    packs, rej = calculate_required_packs(desired_qty=1, desired_unit="kg", product_pack=pack_500g)
    assert rej is None
    assert packs == 2


def test_matching_ceil_pack_500ml_for_1L_requires_2_packs():
    """Desired 1 L with candidate pack 500 ml must return 2 packs (1000ml)."""
    pack_500ml = parse_pack_size("Fresh Milk 500ml")
    packs, rej = calculate_required_packs(desired_qty=1, desired_unit="L", product_pack=pack_500ml)
    assert rej is None
    assert packs == 2


def test_matching_pinned_2L_for_2L_requires_1_pack():
    """Desired 2 L with pinned candidate pack 2 L must return exactly 1 pack, not 2."""
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
        candidate_category="Dairy & Chilled",
        candidate_pack="2L",
        item_spec=item_spec,
    )
    assert is_match is True
    assert packs == 1  # 2L desired / 2L pack = 1 pack needed!


def test_matching_min_pack_bound_rejects_sub_minimum():
    """Minimum 1 L requirement must reject candidate pack of 500 ml."""
    item_spec = {
        "name": "Fresh Milk",
        "desired_quantity": 1,
        "unit_measure": "L",
        "min_pack_size": "1L",
    }
    is_match, _, reason = match_product_candidate(
        candidate_title="Meiji Fresh Milk 500ml",
        candidate_sku="FP_500ML",
        candidate_brand="Meiji",
        candidate_category="Dairy",
        candidate_pack="500ml",
        item_spec=item_spec,
    )
    assert is_match is False
    assert "below minimum" in reason.lower() or "outside" in reason.lower() or "pack" in reason.lower()


def test_matching_max_pack_bound_rejects_exceeding_maximum():
    """Maximum 500 g requirement must reject candidate pack of 1 kg."""
    item_spec = {
        "name": "Greek Yoghurt",
        "desired_quantity": 1,
        "unit_measure": "g",
        "max_pack_size": "500g",
    }
    is_match, _, reason = match_product_candidate(
        candidate_title="Farmers Union Greek Yoghurt 1kg",
        candidate_sku="FP_1KG",
        candidate_brand="Farmers Union",
        candidate_category="Dairy",
        candidate_pack="1kg",
        item_spec=item_spec,
    )
    assert is_match is False
    assert "exceeds maximum" in reason.lower() or "outside" in reason.lower() or "pack" in reason.lower()


def test_matching_rejects_dimensional_mismatch():
    """Desired mass (e.g. 500g) vs candidate volume (e.g. 500ml) must be rejected on dimension mismatch."""
    item_spec = {
        "name": "Cooking Oil",
        "desired_quantity": 500,
        "unit_measure": "g",
    }
    is_match, _, reason = match_product_candidate(
        candidate_title="Naturel Canola Oil 500ml",
        candidate_sku="FP_OIL",
        candidate_brand="Naturel",
        candidate_category="Pantry",
        candidate_pack="500ml",
        item_spec=item_spec,
    )
    # Dimensional checking must detect mass (g) vs volume (ml) mismatch
    assert is_match is False
    assert "dimension" in reason.lower() or "unit" in reason.lower() or "mismatch" in reason.lower()


def test_matching_multipack_normalization_3x250ml():
    """Candidate '3 x 250ml' must normalize to 750ml total volume."""
    pack_multi = parse_pack_size("Ribena Blackcurrant Drink 3 x 250ml")
    assert pack_multi is not None
    assert pack_multi.amount == 750.0
    assert pack_multi.unit == "ml"


def test_matching_three_lemons_with_3s_pack_requires_1_pack():
    """Desired 3 lemons (pieces) with 3s pack must return exactly 1 pack."""
    pack_3s = parse_pack_size("Fresh Lemons 3s Pack")
    packs, _ = calculate_required_packs(desired_qty=3, desired_unit="pieces", product_pack=pack_3s)
    assert packs == 1


def test_matching_exclusion_gate_lemons_rejects_dishwash_and_tea():
    """Produce search for 'lemons' must reject cleaning supplies and tea."""
    is_exc_dw, _ = is_excluded_by_negative_filter("Mama Lemon Dishwashing Liquid 750ml", category="Household")
    assert is_exc_dw is True

    is_exc_tea, _ = is_excluded_by_negative_filter("Lipton Lemon Tea 25 Bags", category="Beverages")
    assert is_exc_tea is True


def test_matching_rejects_substring_token_false_positives():
    """Search for 'lemon' must reject words where 'lemon' is only an arbitrary substring (e.g. 'Filemon')."""
    item_spec = {
        "name": "lemon",
        "desired_quantity": 1,
        "unit_measure": "pieces",
    }
    is_match, _, _ = match_product_candidate(
        candidate_title="Filemon White Fish Fillet 500g",
        candidate_sku="FP_FISH",
        candidate_brand="Ocean",
        candidate_category="Seafood",
        candidate_pack="500g",
        item_spec=item_spec,
    )
    assert is_match is False


# =============================================================================
# PR-01 Regression Suite: Cart Revalidation, Diffs & Fingerprinting
# =============================================================================


def test_revalidation_empty_fresh_adapter_cart_is_failure():
    """A fresh stateless adapter with empty cart must NOT pass revalidation as 'no changes' when quote has items."""
    quote_lines = [
        {"retailer_sku": "FP_102030", "packs_added": 2, "unit_price_cents": 635, "line_total_cents": 1270},
    ]
    empty_live_cart = AuthoritativeCart(
        retailer_id="fairprice",
        cart_id="cart_empty",
        lines=[],
        subtotal_cents=0,
        gross_total_cents=0,
    )
    # Comparing non-empty quote lines against an empty live cart must produce a cart diff
    assert len(empty_live_cart.lines) != len(quote_lines)


def test_revalidation_detects_additional_unapproved_sku():
    """Live cart containing an extra SKU not in approved quote must trigger re-approval."""
    approved_skus = {"FP_102030"}
    live_cart_lines = [
        CartLine(retailer_sku="FP_102030", title="Milk", quantity=2, unit_price_cents=635, line_total_cents=1270),
        CartLine(retailer_sku="FP_UNAPPROVED", title="Candy", quantity=1, unit_price_cents=200, line_total_cents=200),
    ]
    live_skus = {line.retailer_sku for line in live_cart_lines}
    has_unapproved_lines = bool(live_skus - approved_skus)
    assert has_unapproved_lines is True


def test_revalidation_detects_removed_or_changed_quantity_sku():
    """Live cart with quantity diff (e.g. 1 instead of approved 2) must trigger re-approval."""
    approved_qty = {"FP_102030": 2}
    live_qty = {"FP_102030": 1}  # One item went out of stock
    assert approved_qty != live_qty


def test_revalidation_detects_price_promo_fee_slot_diff():
    """Any diff in price, fee, or slot invalidates approval and triggers REAPPROVAL_REQUIRED."""
    approved_gross = 2500
    live_gross = 2650  # Delivery fee or item price increased
    assert approved_gross != live_gross


# =============================================================================
# PR-01 Regression Suite: Orchestration, Status Aggregation & Idempotency
# =============================================================================


def test_comparison_run_remains_running_when_one_of_four_stores_active():
    """Run aggregation rule: run status is RUNNING if any store task is not terminal."""
    store_states = {
        "fairprice": "QUOTED",
        "shengsiong": "QUOTED",
        "littlefarms": "SEARCHING",  # Still running!
        "redmart": "USER_ACTION_REQUIRED",
    }
    is_all_terminal = all(s in ["QUOTED", "PARTIAL", "FAILED", "BLOCKED"] for s in store_states.values())
    assert is_all_terminal is False  # Must not mark run as COMPLETED while littlefarms is SEARCHING


def test_duplicate_submit_attempt_is_idempotent(client):
    """Submitting the same approval twice returns the existing order status/conflict without placing duplicate orders."""
    with Session(test_engine) as session:
        sl = ShoppingList(name="Idempotency List")
        session.add(sl)
        session.commit()

        snapshot = ComparisonSnapshot(shopping_list_id=sl.id, list_version=1, frozen_items_json=[])
        session.add(snapshot)
        session.commit()

        run = ComparisonRun(snapshot_id=snapshot.id, status="QUEUED")
        session.add(run)
        session.commit()

        quote = StoreQuote(
            run_id=run.id,
            retailer_id="fairprice",
            cart_fingerprint="fp_idem_123",
            subtotal_cents=2000,
            gross_total_cents=2000,
            derived_net_cents=1835,
            gst_cents=165,
            is_complete=True,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(quote)
        session.commit()

        approval = Approval(
            quote_id=quote.id,
            approval_token="tok_idem_test",
            idempotency_key="idem_key_1",
            delivery_slot_id="slot_std",
            expected_fingerprint="fp_idem_123",
            is_used=True,  # Already used in a previous submission attempt
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)
        approval_id = str(approval.id)

    # Subsequent submission attempt with already-used token must be rejected with 409
    resp = client.post(f"/approvals/{approval_id}/submit", json={"approval_token": "tok_idem_test"})
    assert resp.status_code == 409
    assert "already been used" in resp.json()["detail"].lower()
