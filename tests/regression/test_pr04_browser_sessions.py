import asyncio
import tempfile
from uuid import UUID

from domain.models.core import ComparisonSnapshot
from sqlmodel import Session

from apps.api.main import execute_live_retailer_worker
from apps.browser_worker.session_manager import SessionManager
from packages.retailers.base import AuthoritativeCart, CartLine, RetailerAdapter, SessionStatus
from tests.conftest import test_engine


def test_session_manager_directory_creation_and_isolation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        sm = SessionManager(base_profile_dir=tmp_dir)
        fp_path = sm.get_profile_path("fairprice")
        ss_path = sm.get_profile_path("shengsiong")

        assert fp_path.exists()
        assert ss_path.exists()
        assert fp_path != ss_path
        assert fp_path.name == "fairprice"
        assert ss_path.name == "shengsiong"


def test_session_manager_concurrency_lock_per_retailer():
    sm = SessionManager()
    lock1 = sm.get_retailer_lock("fairprice")
    lock2 = sm.get_retailer_lock("fairprice")
    lock_ss = sm.get_retailer_lock("shengsiong")

    assert lock1 is lock2
    assert lock1 is not lock_ss


class CartConflictMockAdapter(RetailerAdapter):
    retailer_id = "fairprice"

    async def check_session(self):
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str):
        return None

    async def search_candidates(self, query: str, category_hint=None):
        return []

    async def read_cart(self):
        return AuthoritativeCart(
            retailer_id="fairprice",
            lines=[
                CartLine(
                    retailer_sku="UNOWNED_123",
                    title="User Existing Item",
                    quantity=1,
                    unit_price_cents=500,
                    line_total_cents=500,
                    is_unowned=True,
                )
            ],
            subtotal_cents=500,
            unowned_items_detected=True,
        )

    async def list_delivery_slots(self):
        return []

    async def select_delivery_slot(self, slot_id: str):
        return False

    async def revalidate_cart(self, expected_quote):
        return None

    async def submit_order(self, approval_token: str, slot_id: str = ""):
        raise NotImplementedError()


def test_pre_mutation_cart_conflict_triggers_user_action_required(client):
    # 1. Create list and run
    list_resp = client.post("/shopping-lists", json={"name": "Cart Conflict Test"})
    list_id = list_resp.json()["id"]
    client.post(f"/shopping-lists/{list_id}/items", json={"name": "Milk", "desired_quantity": 1})

    run_resp = client.post("/comparison-runs", json={"shopping_list_id": list_id, "retailer_ids": ["fairprice"]})
    run_id = run_resp.json()["run_id"]
    snapshot_id = run_resp.json()["snapshot_id"]

    with Session(test_engine) as session:
        snap = session.get(ComparisonSnapshot, UUID(snapshot_id))
        frozen_items = snap.frozen_items_json if snap else []

    # Run mock adapter with unowned items detected
    async def run_worker():
        await execute_live_retailer_worker(
            run_id=run_id,
            retailer_id="fairprice",
            frozen_items=frozen_items,
            session_factory=lambda: Session(test_engine),
            adapter_override=CartConflictMockAdapter(),
        )

    asyncio.run(run_worker())

    # Verify run event logs recorded USER_ACTION_REQUIRED with CART_CONFLICT
    run_data = client.get(f"/comparison-runs/{run_id}").json()
    events = run_data.get("event_logs", [])
    cart_conflict_events = [e for e in events if e.get("action_type") == "CART_CONFLICT"]
    assert len(cart_conflict_events) > 0
    assert cart_conflict_events[0]["to_state"] == "USER_ACTION_REQUIRED"
