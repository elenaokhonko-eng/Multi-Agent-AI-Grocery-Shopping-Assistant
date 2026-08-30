from datetime import UTC, datetime, timedelta

from domain.models.core import Approval, ComparisonRun, ComparisonSnapshot, ShoppingList, StoreQuote
from sqlmodel import Session

from tests.conftest import test_engine


def test_submit_order_rejects_tampered_fingerprint_with_409(client):
    with Session(test_engine) as session:
        sl = ShoppingList(name="Fingerprint Integrity List")
        session.add(sl)
        session.commit()

        snapshot = ComparisonSnapshot(shopping_list_id=sl.id, list_version=1, frozen_items_json=[])
        session.add(snapshot)
        session.commit()

        run = ComparisonRun(snapshot_id=snapshot.id, status="QUEUED")
        session.add(run)
        session.commit()

        # Quote stored with one fingerprint
        quote = StoreQuote(
            run_id=run.id,
            retailer_id="fairprice",
            cart_fingerprint="fp_changed_999",
            subtotal_cents=2500,
            gross_total_cents=2500,
            derived_net_cents=2294,
            gst_cents=206,
            is_complete=True,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(quote)
        session.commit()

        # Approval was created with an older/different fingerprint
        approval = Approval(
            quote_id=quote.id,
            approval_token="tok_fp_tamper",
            idempotency_key="idem_fp_tamper",
            delivery_slot_id="slot_morning",
            expected_fingerprint="fp_original_111",
            is_used=False,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
        session.add(approval)
        session.commit()
        session.refresh(approval)
        approval_id = str(approval.id)

    # Submitting with mismatched fingerprint must return 409 FINGERPRINT_MISMATCH
    resp = client.post(f"/approvals/{approval_id}/submit", json={"approval_token": "tok_fp_tamper"})
    assert resp.status_code == 409
    data = resp.json()
    assert data["detail"]["error"] == "FINGERPRINT_MISMATCH"
