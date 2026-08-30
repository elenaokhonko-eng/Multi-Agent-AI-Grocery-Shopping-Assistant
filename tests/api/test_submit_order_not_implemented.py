from datetime import UTC, datetime, timedelta

from domain.models.core import Approval, ComparisonRun, ComparisonSnapshot, ShoppingList, StoreQuote
from sqlmodel import Session

from tests.conftest import test_engine


def test_submit_order_returns_503_not_implemented(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Safety Test List")
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
            cart_fingerprint="fp_valid_123",
            subtotal_cents=2500,
            gross_total_cents=2500,
            derived_net_cents=2294,
            gst_cents=206,
            is_complete=True,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(quote)
        session.commit()

        approval = Approval(
            quote_id=quote.id,
            approval_token="tok_safe_test",
            idempotency_key="idem_safe_test",
            delivery_slot_id="slot_morning",
            expected_fingerprint="fp_valid_123",
            is_used=False,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)
        approval_id = str(approval.id)

    # Valid token submitted, but live checkout is not yet implemented -> returns 503
    resp = client.post(f"/approvals/{approval_id}/submit", json={"approval_token": "tok_safe_test"})
    assert resp.status_code == 503
    data = resp.json()
    assert data["detail"]["error"] == "LIVE_CHECKOUT_NOT_IMPLEMENTED"
    assert "Live checkout is not yet implemented" in data["detail"]["message"]
