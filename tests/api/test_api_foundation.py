import pytest
from sqlmodel import Session
import uuid

from domain.models.core import ShoppingList, ShoppingListItem, StoreQuote, Approval
from domain.services.fingerprint import compute_quote_fingerprint
from tests.conftest import test_engine

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "live_purchase_enabled" in data

def test_shopping_list_crud(client):
    # 1. Create list
    create_resp = client.post("/shopping-lists", json={"name": "Weekly Test List", "description": "Testing"})
    assert create_resp.status_code == 201
    list_data = create_resp.json()
    list_id = list_data["id"]
    assert list_data["name"] == "Weekly Test List"
    assert list_data["version"] == 1

    # 2. Add item
    item_resp = client.post(f"/shopping-lists/{list_id}/items", json={
        "name": "Meiji Milk 2L",
        "category": "Dairy",
        "desired_quantity": 2,
        "unit_measure": "L",
        "must_have": True,
        "preferred_brands": ["Meiji"],
        "pinned_skus": {"fairprice": "FP_123"}
    })
    assert item_resp.status_code == 201
    item_data = item_resp.json()
    item_id = item_data["id"]
    assert item_data["name"] == "Meiji Milk 2L"

    # 3. Get list with items
    get_resp = client.get(f"/shopping-lists/{list_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert len(get_data["items"]) == 1
    assert get_data["version"] == 2  # Incremented on item addition

    # 4. Patch item
    patch_resp = client.patch(f"/shopping-lists/{list_id}/items/{item_id}", json={"desired_quantity": 3})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["desired_quantity"] == 3

    # 5. Delete item
    del_resp = client.delete(f"/shopping-lists/{list_id}/items/{item_id}")
    assert del_resp.status_code == 204

def test_comparison_run_and_approval_flow(client):
    # 1. Create list and item
    list_resp = client.post("/shopping-lists", json={"name": "Run List"})
    list_id = list_resp.json()["id"]
    client.post(f"/shopping-lists/{list_id}/items", json={"name": "Eggs 10s", "desired_quantity": 1, "must_have": True})

    # 2. Start comparison run
    run_resp = client.post("/comparison-runs", json={
        "shopping_list_id": list_id,
        "retailer_ids": ["fairprice", "shengsiong"]
    })
    assert run_resp.status_code == 202
    run_data = run_resp.json()
    run_id = run_data["run_id"]
    assert run_data["status"] == "QUEUED"
    assert "snapshot_id" in run_data

    # 3. Fetch comparison run
    get_run_resp = client.get(f"/comparison-runs/{run_id}")
    assert get_run_resp.status_code == 200

def test_live_purchase_safety_guard(client):
    list_resp = client.post("/shopping-lists", json={"name": "Safety List"})
    list_id = list_resp.json()["id"]
    item_resp = client.post(f"/shopping-lists/{list_id}/items", json={"name": "Lemons", "desired_quantity": 2})

    # Create dummy quote in DB
    with Session(test_engine) as session:
        from domain.models.core import ComparisonSnapshot, ComparisonRun, StoreQuote
        from datetime import datetime, timezone, timedelta
        
        snapshot = ComparisonSnapshot(shopping_list_id=uuid.UUID(list_id), list_version=1, frozen_items_json=[])
        session.add(snapshot)
        session.commit()
        
        run = ComparisonRun(snapshot_id=snapshot.id, status="QUEUED")
        session.add(run)
        session.commit()

        quote = StoreQuote(
            run_id=run.id,
            retailer_id="fairprice",
            cart_fingerprint="dummy_fp",
            subtotal_cents=1000,
            gross_total_cents=1000,
            derived_net_cents=917,
            gst_cents=83,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        session.add(quote)
        session.commit()
        session.refresh(quote)
        quote_id = str(quote.id)

    # Approve quote
    app_resp = client.post(f"/quotes/{quote_id}/approve", json={"delivery_slot_id": "slot_fp_morning"})
    assert app_resp.status_code == 200
    approval_id = app_resp.json()["approval_id"]
    approval_token = app_resp.json()["approval_token"]

    # Submit approval -> Must return 403 because LIVE_PURCHASE_ENABLED is False
    sub_resp = client.post(f"/approvals/{approval_id}/submit", json={"approval_token": approval_token})
    assert sub_resp.status_code == 403
    assert "LIVE_PURCHASE_DISABLED" in sub_resp.json()["detail"]

def test_quote_fingerprint_determinism():
    lines = [
        {"retailer_sku": "SKU_B", "quantity": 1, "unit_price_cents": 500, "line_total_cents": 500},
        {"retailer_sku": "SKU_A", "quantity": 2, "unit_price_cents": 300, "line_total_cents": 600},
    ]
    fp1 = compute_quote_fingerprint("fairprice", lines, "slot_1", 1100, 0, 1100)
    fp2 = compute_quote_fingerprint("fairprice", list(reversed(lines)), "slot_1", 1100, 0, 1100)
    assert fp1 == fp2
    assert len(fp1) == 64
