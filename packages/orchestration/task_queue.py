import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from domain.models.core import ComparisonRun, RetailerTask, StoreQuote
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


class DurableTaskQueue:
    """
    Durable PostgreSQL/SQLite task queue for retailer workers.
    Supports atomic worker leasing, periodic heartbeats, orphan lease reclamation,
    and run-level state aggregation.
    """

    @staticmethod
    def enqueue_run_tasks(session: Session, run_id: UUID, retailer_ids: list[str]) -> list[RetailerTask]:
        tasks: list[RetailerTask] = []
        now = datetime.now(UTC)
        for rid in retailer_ids:
            task = RetailerTask(
                id=uuid4(),
                run_id=run_id,
                retailer_id=rid.lower().strip(),
                status="QUEUED",
                retry_count=0,
                max_retries=3,
                created_at=now,
                updated_at=now,
            )
            session.add(task)
            tasks.append(task)
        session.commit()
        for t in tasks:
            session.refresh(t)
        return tasks

    @staticmethod
    def claim_task(
        session: Session,
        worker_id: str,
        retailer_id: str | None = None,
        lease_duration_seconds: int = 60,
    ) -> RetailerTask | None:
        now = datetime.now(UTC)
        query = select(RetailerTask)
        if retailer_id:
            query = query.where(RetailerTask.retailer_id == retailer_id.lower().strip())

        candidates = session.exec(query).all()
        for task in candidates:
            # Check if task is QUEUED or has an expired lease
            is_queued = task.status == "QUEUED"
            is_expired_lease = (
                task.status in ("CLAIMED", "RUNNING")
                and task.lease_expires_at is not None
                and (
                    task.lease_expires_at.replace(tzinfo=UTC)
                    if task.lease_expires_at.tzinfo is None
                    else task.lease_expires_at
                )
                < now
                and task.retry_count < task.max_retries
            )

            if is_queued or is_expired_lease:
                task.status = "RUNNING"
                task.lease_token = worker_id
                task.lease_expires_at = now + timedelta(seconds=lease_duration_seconds)
                if is_expired_lease:
                    task.retry_count += 1
                task.updated_at = now
                session.add(task)
                session.commit()
                session.refresh(task)
                return task

        return None

    @staticmethod
    def heartbeat(
        session: Session,
        task_id: UUID,
        lease_token: str,
        extension_seconds: int = 60,
    ) -> bool:
        task = session.get(RetailerTask, task_id)
        if not task or task.lease_token != lease_token or task.status != "RUNNING":
            return False
        now = datetime.now(UTC)
        task.lease_expires_at = now + timedelta(seconds=extension_seconds)
        task.updated_at = now
        session.add(task)
        session.commit()
        return True

    @staticmethod
    def complete_task(
        session: Session,
        task_id: UUID,
        lease_token: str,
    ) -> None:
        task = session.get(RetailerTask, task_id)
        if task and task.lease_token == lease_token:
            now = datetime.now(UTC)
            task.status = "COMPLETED"
            task.lease_token = None
            task.lease_expires_at = None
            task.updated_at = now
            session.add(task)
            session.commit()

    @staticmethod
    def fail_task(
        session: Session,
        task_id: UUID,
        lease_token: str,
        error_message: str,
    ) -> None:
        task = session.get(RetailerTask, task_id)
        if task and task.lease_token == lease_token:
            now = datetime.now(UTC)
            task.status = "FAILED"
            task.error_message = error_message
            task.lease_token = None
            task.lease_expires_at = None
            task.updated_at = now
            session.add(task)
            session.commit()

    @staticmethod
    def set_task_action_required(
        session: Session,
        task_id: UUID,
        lease_token: str,
        detail: str,
    ) -> None:
        task = session.get(RetailerTask, task_id)
        if task and task.lease_token == lease_token:
            now = datetime.now(UTC)
            task.status = "USER_ACTION_REQUIRED"
            task.error_message = detail
            task.lease_token = None
            task.lease_expires_at = None
            task.updated_at = now
            session.add(task)
            session.commit()

    @staticmethod
    def reclaim_expired_leases(session: Session) -> int:
        now = datetime.now(UTC)
        tasks = session.exec(
            select(RetailerTask).where(RetailerTask.status.in_(["CLAIMED", "RUNNING"]))
        ).all()
        reclaimed_count = 0
        for task in tasks:
            if not task.lease_expires_at:
                continue
            lease_exp = (
                task.lease_expires_at.replace(tzinfo=UTC)
                if task.lease_expires_at.tzinfo is None
                else task.lease_expires_at
            )
            if lease_exp < now:
                if task.retry_count < task.max_retries:
                    task.status = "QUEUED"
                    task.lease_token = None
                    task.lease_expires_at = None
                    task.retry_count += 1
                else:
                    task.status = "FAILED"
                    task.error_message = "Max retries exceeded after lease expiry."
                    task.lease_expires_at = None
                task.updated_at = now
                session.add(task)
                reclaimed_count += 1

        if reclaimed_count > 0:
            session.commit()
        return reclaimed_count

    @staticmethod
    def aggregate_run_state(session: Session, run_id: UUID) -> str:
        run = session.get(ComparisonRun, run_id)
        if not run:
            return "UNKNOWN"

        tasks = session.exec(select(RetailerTask).where(RetailerTask.run_id == run_id)).all()
        if not tasks:
            return run.status

        statuses = [t.status for t in tasks]

        # Any active in flight
        if any(s in ("QUEUED", "CLAIMED", "RUNNING") for s in statuses):
            run.status = "RUNNING"
            session.add(run)
            session.commit()
            return "RUNNING"

        # Any user action required
        if any(s == "USER_ACTION_REQUIRED" for s in statuses):
            # If all are terminal / user action required
            run.status = "USER_ACTION_REQUIRED"
            session.add(run)
            session.commit()
            return "USER_ACTION_REQUIRED"

        # Check quotes generated
        quotes = session.exec(select(StoreQuote).where(StoreQuote.run_id == run_id)).all()
        now = datetime.now(UTC)
        run.completed_at = now

        if any(q.is_complete for q in quotes):
            run.status = "COMPLETED"
        elif quotes:
            run.status = "PARTIAL"
        elif all(s == "FAILED" for s in statuses):
            run.status = "FAILED"
        else:
            run.status = "COMPLETED"

        session.add(run)
        session.commit()
        return run.status
