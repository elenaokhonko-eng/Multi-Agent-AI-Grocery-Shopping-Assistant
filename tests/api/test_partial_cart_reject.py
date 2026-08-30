from datetime import UTC, datetime, timedelta

from domain.models.core import ComparisonRun, ComparisonSnapshot, ShoppingList, StoreQuote
from sqlmodel import Session

from tests.conftest import test_engine


def test_approve_incomplete_quote_direct_rejected_with_422(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Incomplete Cart List")
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
            cart_fingerprint="fp_incomplete",
            subtotal_cents=1500,
            gross_total_cents=1500,
            derived_net_cents=1376,
            gst_cents=124,
            is_complete=False,
            missing_must_have_count=2,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(quote)
        session.commit()
        session.refresh(quote)
        quote_id = str(quote.id)

    # Attempt direct approval of an incomplete quote
    resp = client.post(f"/quotes/{quote_id}/approve", json={"delivery_slot_id": "slot_std"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "INCOMPLETE_QUOTE_APPROVAL_FORBIDDEN"


def test_create_approval_incomplete_quote_rejected_with_422(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Incomplete Cart List 2")
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
            retailer_id="shengsiong",
            cart_fingerprint="fp_ss_incomplete",
            subtotal_cents=1200,
            gross_total_cents=1200,
            derived_net_cents=1101,
            gst_cents=99,
            is_complete=False,
            missing_must_have_count=1,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(quote)
        session.commit()
        session.refresh(quote)
        quote_id = str(quote.id)

    # Attempt approval via /approvals
    resp = client.post("/approvals", json={"quote_id": quote_id, "delivery_slot_id": "slot_std"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "INCOMPLETE_QUOTE_APPROVAL_FORBIDDEN"
