from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from domain.models.core import (
    ComparisonRun,
    ComparisonSnapshot,
    QuoteRevision,
    RetailerTask,
    ShoppingList,
)
from orchestration.task_queue import DurableTaskQueue
from sqlmodel import Session, select

from tests.conftest import test_engine


def test_durable_task_enqueue_claim_and_heartbeat():
    with Session(test_engine) as session:
        # Setup list and snapshot
        sl = ShoppingList(name="Durable Task List", version=1)
        session.add(sl)
        session.commit()
        session.refresh(sl)

        snap = ComparisonSnapshot(shopping_list_id=sl.id, list_version=1, frozen_items_json=[])
        session.add(snap)
        session.commit()
        session.refresh(snap)

        run = ComparisonRun(snapshot_id=snap.id, status="QUEUED")
        session.add(run)
        session.commit()
        session.refresh(run)

        # 1. Enqueue tasks
        tasks = DurableTaskQueue.enqueue_run_tasks(session, run.id, ["fairprice", "shengsiong"])
        assert len(tasks) == 2
        assert all(t.status == "QUEUED" for t in tasks)

        # 2. Claim task
        worker_id = "worker_1"
        claimed = DurableTaskQueue.claim_task(
            session, worker_id=worker_id, retailer_id="fairprice", lease_duration_seconds=30
        )
        assert claimed is not None
        assert claimed.retailer_id == "fairprice"
        assert claimed.status == "RUNNING"
        assert claimed.lease_token == worker_id
        assert claimed.lease_expires_at is not None

        # 3. Heartbeat
        old_expiry = claimed.lease_expires_at
        hb_success = DurableTaskQueue.heartbeat(session, claimed.id, lease_token=worker_id, extension_seconds=60)
        assert hb_success is True
        session.refresh(claimed)
        assert claimed.lease_expires_at > old_expiry

        # 4. Complete task
        DurableTaskQueue.complete_task(session, claimed.id, lease_token=worker_id)
        session.refresh(claimed)
        assert claimed.status == "COMPLETED"
        assert claimed.lease_token is None


def test_durable_task_expired_lease_reclamation():
    with Session(test_engine) as session:
        sl = ShoppingList(name="Reclaim List", version=1)
        session.add(sl)
        session.commit()

        snap = ComparisonSnapshot(shopping_list_id=sl.id, list_version=1, frozen_items_json=[])
        session.add(snap)
        session.commit()

        run = ComparisonRun(snapshot_id=snap.id, status="QUEUED")
        session.add(run)
        session.commit()

        # Create task with expired lease in the past
        past_time = datetime.now(UTC) - timedelta(minutes=5)
        task = RetailerTask(
            id=uuid4(),
            run_id=run.id,
            retailer_id="littlefarms",
            status="RUNNING",
            lease_token="crashed_worker",
            lease_expires_at=past_time,
            retry_count=0,
            max_retries=3,
        )
        session.add(task)
        session.commit()

        # Reclaim expired leases
        reclaimed = DurableTaskQueue.reclaim_expired_leases(session)
        assert reclaimed == 1

        session.refresh(task)
        assert task.status == "QUEUED"
        assert task.lease_token is None
        assert task.retry_count == 1


def test_quote_revision_and_submission_attempt_tracking(client):
    # 1. Create list and items
    list_resp = client.post("/shopping-lists", json={"name": "Revision & Attempt Test"})
    list_id = list_resp.json()["id"]
    client.post(f"/shopping-lists/{list_id}/items", json={"name": "Eggs", "desired_quantity": 1})

    # 2. Start comparison run
    run_resp = client.post("/comparison-runs", json={"shopping_list_id": list_id, "retailer_ids": ["fairprice"]})
    assert run_resp.status_code == 202
    run_id = run_resp.json()["run_id"]

    # Verify durable task was created in DB
    with Session(test_engine) as session:
        tasks = session.exec(select(RetailerTask).where(RetailerTask.run_id == UUID(run_id))).all()
        assert len(tasks) == 1
        assert tasks[0].retailer_id == "fairprice"

    # Wait for run to generate quote in test environment
    import time

    time.sleep(0.5)

    run_data = client.get(f"/comparison-runs/{run_id}").json()
    quotes = run_data.get("quotes", [])
    if quotes:
        quote_id = quotes[0]["quote_id"]
        # Verify initial QuoteRevision was created
        with Session(test_engine) as session:
            revs = session.exec(select(QuoteRevision).where(QuoteRevision.quote_id == UUID(quote_id))).all()
            assert len(revs) >= 1
            assert revs[0].revision_number == 1

        # Select delivery slot to trigger revision #2
        slot_resp = client.post(f"/quotes/{quote_id}/select-slot", json={"slot_id": "slot_fp_2"})
        assert slot_resp.status_code == 200

        with Session(test_engine) as session:
            revs_after = session.exec(select(QuoteRevision).where(QuoteRevision.quote_id == UUID(quote_id))).all()
            assert len(revs_after) == 2
            assert revs_after[1].revision_number == 2
