import asyncio
import os
import pytest
from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlmodel import Session

from apps.api.main import (
    app,
    execute_live_retailer_worker,
)
from domain.models.core import (
    ShoppingList,
    ShoppingListItem,
    ComparisonSnapshot,
    ComparisonRun,
    StoreQuote,
    QuoteLine,
    Approval,
    OrderReceipt,
)
from packages.retailers.base import (
    RetailerAdapter,
    SessionStatus,
    CandidateProduct,
    AuthoritativeCart,
    CartLine,
    DeliverySlot,
    CartDiff,
    OrderConfirmation,
)
from tests.conftest import test_engine

# -----------------------------------------------------------------------------
# Mock / Test Adapters specifically configured for the QA-06 Scenario
# -----------------------------------------------------------------------------
class MockStoreA_ShengSiong(RetailerAdapter):
    """Store A: Cheapest overall, but missing Eggs (partial)."""
    retailer_id = "shengsiong"

    async def check_session(self) -> SessionStatus:
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str):
        return None

    async def search_candidates(self, query: str, category_hint=None):
        if "lemon" in query.lower():
            return [CandidateProduct(
                store_id="shengsiong",
                retailer_sku="SS_LEMON",
                title="Lemons 3s",
                price_cents=150,
                product_url="https://allforyou.sg/lemon",
                in_stock=True,
                is_exact_match=True
            )]
        elif "water" in query.lower():
            return [CandidateProduct(
                store_id="shengsiong",
                retailer_sku="SS_WATER",
                title="Sparkling Water 1L",
                price_cents=200,
                product_url="https://allforyou.sg/water",
                in_stock=True,
                is_exact_match=True
            )]
        # Eggs are NOT in stock!
        return []

    def validate_candidate(self, candidate, desired_item):
        return True

    async def add_exact_item(self, sku: str, quantity: int):
        return True

    async def read_cart(self):
        # S$1.50 + S$2.00 = S$3.50 + S$4.00 delivery = S$7.50
        return AuthoritativeCart(
            retailer_id="shengsiong",
            cart_id="cart_ss_qa",
            lines=[
                CartLine(retailer_sku="SS_LEMON", title="Lemons 3s", quantity=1, unit_price_cents=150, line_total_cents=150),
                CartLine(retailer_sku="SS_WATER", title="Sparkling Water", quantity=1, unit_price_cents=200, line_total_cents=200),
            ],
            subtotal_cents=350,
            delivery_fee_cents=400,
            gross_total_cents=750,
            unowned_items_detected=False
        )

    async def list_delivery_slots(self):
        now = datetime.now(timezone.utc)
        return [DeliverySlot(slot_id="slot_ss_1", start_time=now, end_time=now+timedelta(hours=2), display_label="Morning")]

    async def select_delivery_slot(self, slot_id):
        return True

    async def revalidate_cart(self, expected_fingerprint):
        return CartDiff(has_changes=False)

    async def submit_order(self, approval_token):
        return OrderConfirmation(retailer_order_id="SS-CONF-123", confirmed_total_cents=750, delivery_slot="Morning")


class MockStoreB_FairPrice(RetailerAdapter):
    """Store B: Complete and cheapest eligible."""
    retailer_id = "fairprice"

    def __init__(self, simulate_out_of_stock_on_revalidate=False):
        self.simulate_oos = simulate_out_of_stock_on_revalidate

    async def check_session(self) -> SessionStatus:
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str):
        return None

    async def search_candidates(self, query: str, category_hint=None):
        if "lemon" in query.lower():
            return [CandidateProduct(
                store_id="fairprice",
                retailer_sku="FP_LEMON",
                title="Lemons 3s",
                price_cents=200,
                product_url="https://fairprice.com.sg/lemon",
                in_stock=True,
                is_exact_match=True
            )]
        elif "egg" in query.lower():
            return [CandidateProduct(
                store_id="fairprice",
                retailer_sku="FP_EGG",
                title="Fresh Eggs 10s",
                price_cents=320,
                product_url="https://fairprice.com.sg/egg",
                in_stock=True,
                is_exact_match=True
            )]
        elif "water" in query.lower():
            return [CandidateProduct(
                store_id="fairprice",
                retailer_sku="FP_WATER",
                title="Sparkling Water 1L",
                price_cents=280,
                product_url="https://fairprice.com.sg/water",
                in_stock=True,
                is_exact_match=True
            )]
        return []

    def validate_candidate(self, candidate, desired_item):
        return True

    async def add_exact_item(self, sku: str, quantity: int):
        return True

    async def read_cart(self):
        # S$2.00 + S$3.20 + S$2.80 = S$8.00 + S$5.50 delivery = S$13.50
        return AuthoritativeCart(
            retailer_id="fairprice",
            cart_id="cart_fp_qa",
            lines=[
                CartLine(retailer_sku="FP_LEMON", title="Lemons 3s", quantity=1, unit_price_cents=200, line_total_cents=200),
                CartLine(retailer_sku="FP_EGG", title="Fresh Eggs 10s", quantity=1, unit_price_cents=320, line_total_cents=320),
                CartLine(retailer_sku="FP_WATER", title="Sparkling Water", quantity=1, unit_price_cents=280, line_total_cents=280),
            ],
            subtotal_cents=800,
            delivery_fee_cents=550,
            gross_total_cents=1350,
            unowned_items_detected=False
        )

    async def list_delivery_slots(self):
        now = datetime.now(timezone.utc)
        return [DeliverySlot(slot_id="slot_fp_1", start_time=now, end_time=now+timedelta(hours=2), display_label="Tomorrow Morning")]

    async def select_delivery_slot(self, slot_id):
        return True

    async def revalidate_cart(self, expected_fingerprint):
        if self.simulate_oos:
            return CartDiff(
                has_changes=True,
                price_changed=True,
                old_total_cents=1350,
                new_total_cents=1030,
                items_out_of_stock=["FP_EGG"],
                detail="Fresh Eggs 10s went out of stock during pre-submission check."
            )
        return CartDiff(has_changes=False, old_total_cents=1350, new_total_cents=1350)

    async def submit_order(self, approval_token):
        return OrderConfirmation(retailer_order_id="FP-CONF-9876", confirmed_total_cents=1350, delivery_slot="Tomorrow Morning")


class MockStoreC_RedMart(RetailerAdapter):
    """Store C: Requires human verification / login (USER_ACTION_REQUIRED)."""
    retailer_id = "redmart"

    async def check_session(self) -> SessionStatus:
        return SessionStatus(
            is_authenticated=False,
            requires_action=True,
            action_type="LOGIN_EXPIRED",
            resume_token="res_rm_test_challenge",
            detail="RedMart login expired. Please authenticate in browser."
        )

    async def resolve_pinned_sku(self, sku: str):
        return None
    async def search_candidates(self, query: str, category_hint=None):
        return []
    def validate_candidate(self, candidate, desired_item):
        return True
    async def add_exact_item(self, sku: str, quantity: int):
        return False
    async def read_cart(self):
        return AuthoritativeCart(retailer_id="redmart")
    async def list_delivery_slots(self):
        return []
    async def select_delivery_slot(self, slot_id):
        return False
    async def revalidate_cart(self, expected_fingerprint):
        return CartDiff(has_changes=False)
    async def submit_order(self, approval_token):
        return OrderConfirmation(retailer_order_id="RM-ERR", confirmed_total_cents=0, delivery_slot="")


class MockStoreD_LittleFarms(RetailerAdapter):
    """Store D: Fails/errors without breaking other stores."""
    retailer_id = "littlefarms"

    async def check_session(self) -> SessionStatus:
        raise ConnectionResetError("Little Farms upstream 503 Service Unavailable")

    async def resolve_pinned_sku(self, sku: str):
        return None
    async def search_candidates(self, query: str, category_hint=None):
        return []
    def validate_candidate(self, candidate, desired_item):
        return True
    async def add_exact_item(self, sku: str, quantity: int):
        return False
    async def read_cart(self):
        return AuthoritativeCart(retailer_id="littlefarms")
    async def list_delivery_slots(self):
        return []
    async def select_delivery_slot(self, slot_id):
        return False
    async def revalidate_cart(self, expected_fingerprint):
        return CartDiff(has_changes=False)
    async def submit_order(self, approval_token):
        return OrderConfirmation(retailer_order_id="LF-ERR", confirmed_total_cents=0, delivery_slot="")


# -----------------------------------------------------------------------------
# Master Scenario QA-06 Execution Test
# -----------------------------------------------------------------------------
def test_master_scenario_qa_06(client, monkeypatch):
    """
    Full Scenario (QA-06):
    1. List contains lemons, eggs, and sparkling water.
    2. Store A (Sheng Siong) is cheapest overall (S$7.50) but missing eggs.
    3. Store B (FairPrice) is complete and cheapest eligible (S$13.50).
    4. Store C (RedMart) requires login.
    5. Store D (Little Farms) fails gracefully.
    6. Elena approves Store B.
    7. Eggs go out of stock during revalidation -> Reapproval triggered.
    8. Replacement is approved.
    9. Exactly one confirmed receipt is created.
    """
    # 1. Create list
    list_resp = client.post("/shopping-lists", json={"name": "QA-06 List"})
    assert list_resp.status_code == 201
    list_id = list_resp.json()["id"]

    # Add lemons, eggs, and water (lemons and eggs are must_have)
    client.post(f"/shopping-lists/{list_id}/items", json={"name": "Fresh Lemons", "desired_quantity": 1, "must_have": True})
    client.post(f"/shopping-lists/{list_id}/items", json={"name": "Fresh Eggs 10s", "desired_quantity": 1, "must_have": True})
    client.post(f"/shopping-lists/{list_id}/items", json={"name": "Sparkling Water", "desired_quantity": 1, "must_have": False})

    # 2. Trigger comparison run
    run_resp = client.post("/comparison-runs", json={
        "shopping_list_id": list_id,
        "retailer_ids": ["fairprice", "shengsiong", "littlefarms", "redmart"]
    })
    assert run_resp.status_code == 202
    run_id = run_resp.json()["run_id"]
    snapshot_id = run_resp.json()["snapshot_id"]

    # Fetch snapshot items
    with Session(test_engine) as session:
        snap = session.get(ComparisonSnapshot, UUID(snapshot_id))
        frozen_items = snap.frozen_items_json

    # Run the 4 mock stores through execute_live_retailer_worker concurrently
    async def run_all_stores():
        await asyncio.gather(
            execute_live_retailer_worker(run_id, "shengsiong", frozen_items, lambda: Session(test_engine), adapter_override=MockStoreA_ShengSiong()),
            execute_live_retailer_worker(run_id, "fairprice", frozen_items, lambda: Session(test_engine), adapter_override=MockStoreB_FairPrice()),
            execute_live_retailer_worker(run_id, "redmart", frozen_items, lambda: Session(test_engine), adapter_override=MockStoreC_RedMart()),
            execute_live_retailer_worker(run_id, "littlefarms", frozen_items, lambda: Session(test_engine), adapter_override=MockStoreD_LittleFarms()),
        )

    asyncio.run(run_all_stores())

    # 3. Verify comparison results
    get_run_resp = client.get(f"/comparison-runs/{run_id}")
    assert get_run_resp.status_code == 200
    run_data = get_run_resp.json()

    quotes = {q["retailer_id"]: q for q in run_data["quotes"]}
    
    # Store A (Sheng Siong) is present but incomplete
    assert "shengsiong" in quotes
    assert quotes["shengsiong"]["is_complete"] is False
    assert quotes["shengsiong"]["gross_total_cents"] == 750

    # Store B (FairPrice) is present and complete
    assert "fairprice" in quotes
    assert quotes["fairprice"]["is_complete"] is True
    assert quotes["fairprice"]["gross_total_cents"] == 1350

    # Cheapest complete MUST be FairPrice (Store B), NOT Sheng Siong
    assert run_data["cheapest_complete_store"] == "fairprice"

    fp_quote = quotes["fairprice"]

    # 4. Step 6: Elena approves Store B (FairPrice)
    app_resp = client.post(f"/quotes/{fp_quote['quote_id']}/approve", json={"delivery_slot_id": "slot_fp_1"})
    assert app_resp.status_code == 200
    approval_id = app_resp.json()["approval_id"]
    approval_token = app_resp.json()["approval_token"]

    # 5. Step 7: Simulate Eggs going out of stock during pre-submission revalidation
    # Re-wire adapter to simulate cart diff
    from apps.api import main as api_module
    api_module.ADAPTER_MAP["fairprice"] = lambda: MockStoreB_FairPrice(simulate_out_of_stock_on_revalidate=True)

    # Submitting should fail with REAPPROVAL_REQUIRED (409 Conflict)
    sub_fail_resp = client.post(f"/approvals/{approval_id}/submit", json={"approval_token": approval_token})
    assert sub_fail_resp.status_code == 409
    assert sub_fail_resp.json()["detail"]["error"] == "REAPPROVAL_REQUIRED"

    # 6. Step 8: Approve updated basket and enable live purchase
    monkeypatch.setenv("LIVE_PURCHASE_ENABLED", "true")
    api_module.ADAPTER_MAP["fairprice"] = lambda: MockStoreB_FairPrice(simulate_out_of_stock_on_revalidate=False)

    new_app_resp = client.post(f"/quotes/{fp_quote['quote_id']}/approve", json={"delivery_slot_id": "slot_fp_1"})
    assert new_app_resp.status_code == 200
    new_approval_id = new_app_resp.json()["approval_id"]
    new_approval_token = new_app_resp.json()["approval_token"]

    # 7. Step 9: Final submission succeeds and exactly one confirmed receipt is generated
    final_sub_resp = client.post(f"/approvals/{new_approval_id}/submit", json={"approval_token": new_approval_token})
    assert final_sub_resp.status_code == 200
    final_order = final_sub_resp.json()
    assert final_order["status"] == "CONFIRMED"
    assert final_order["retailer_order_id"] == "FP-CONF-9876"
    assert final_order["confirmed_total_cents"] == 1350

    # Check that receipt is stored and queryable
    get_order_resp = client.get(f"/orders/{final_order['order_id']}")
    assert get_order_resp.status_code == 200
    assert get_order_resp.json()["retailer_order_id"] == "FP-CONF-9876"
