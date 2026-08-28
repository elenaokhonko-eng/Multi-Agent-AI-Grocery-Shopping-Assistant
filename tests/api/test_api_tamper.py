import pytest
from sqlmodel import Session
from datetime import datetime, timezone, timedelta
import uuid

from domain.models.core import ShoppingList, ComparisonSnapshot, ComparisonRun, StoreQuote, Approval
from tests.conftest import test_engine

def test_tamper_approval_payload_rejects_extra_fields(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Test List")
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
            cart_fingerprint="auth_fingerprint_123",
            subtotal_cents=2500,
            gross_total_cents=2500,
            derived_net_cents=2294,
            gst_cents=206,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(quote)
        session.commit()
        session.refresh(quote)
        quote_id = str(quote.id)

    resp = client.post(f"/quotes/{quote_id}/approve", json={"delivery_slot_id": "slot_morning"})
    assert resp.status_code == 200
    approval_data = resp.json()
    assert approval_data["gross_total_cents"] == 2500

def test_expired_quote_rejection(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Expired List")
        session.add(sl)
        session.commit()

        snapshot = ComparisonSnapshot(shopping_list_id=sl.id, list_version=1, frozen_items_json=[])
        session.add(snapshot)
        session.commit()

        run = ComparisonRun(snapshot_id=snapshot.id, status="QUEUED")
        session.add(run)
        session.commit()

        expired_quote = StoreQuote(
            run_id=run.id,
            retailer_id="fairprice",
            cart_fingerprint="expired_fp",
            subtotal_cents=1000,
            gross_total_cents=1000,
            derived_net_cents=917,
            gst_cents=83,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        session.add(expired_quote)
        session.commit()
        session.refresh(expired_quote)
        quote_id = str(expired_quote.id)

    resp = client.post(f"/quotes/{quote_id}/approve", json={"delivery_slot_id": "slot_1"})
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()

def test_reused_approval_token_rejection(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Used Token List")
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
            cart_fingerprint="fp_reused",
            subtotal_cents=1000,
            gross_total_cents=1000,
            derived_net_cents=917,
            gst_cents=83,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(quote)
        session.commit()

        approval = Approval(
            quote_id=quote.id,
            approval_token="tok_already_used",
            idempotency_key="idem_used",
            delivery_slot_id="slot_1",
            expected_fingerprint="fp_reused",
            is_used=True,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)
        approval_id = str(approval.id)

    resp = client.post(f"/approvals/{approval_id}/submit", json={"approval_token": "tok_already_used"})
    assert resp.status_code == 409
    assert "already been used" in resp.json()["detail"].lower()

def test_invalid_token_rejection(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Wrong Token List")
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
            cart_fingerprint="fp_auth",
            subtotal_cents=1000,
            gross_total_cents=1000,
            derived_net_cents=917,
            gst_cents=83,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(quote)
        session.commit()

        approval = Approval(
            quote_id=quote.id,
            approval_token="tok_legit_secret",
            idempotency_key="idem_secret",
            delivery_slot_id="slot_1",
            expected_fingerprint="fp_auth",
            is_used=False,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)
        approval_id = str(approval.id)

    resp = client.post(f"/approvals/{approval_id}/submit", json={"approval_token": "tok_forged_token"})
    assert resp.status_code == 403
    assert "Invalid approval token" in resp.json()["detail"]
