import asyncio
import logging
import os
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from domain.models.core import StoreEventLog
from orchestration.state_machine import StoreState, StoreStateEvent
from sqlmodel import Session, create_engine

from packages.retailers.base import RetailerAdapter
from packages.retailers.fairprice.adapter import FairPriceAdapter
from packages.retailers.littlefarms.adapter import LittleFarmsAdapter
from packages.retailers.redmart.adapter import RedMartAdapter
from packages.retailers.shengsiong.adapter import ShengSiongAdapter

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grocery_assistant.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


ADAPTER_MAP: dict[str, type[RetailerAdapter] | Any] = {
    "fairprice": FairPriceAdapter,
    "shengsiong": ShengSiongAdapter,
    "littlefarms": LittleFarmsAdapter,
    "redmart": RedMartAdapter,
}

RUN_EVENT_QUEUES: dict[str, list[asyncio.Queue]] = {}


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def broadcast_run_event(
    run_id: str,
    event: StoreStateEvent,
    session: Session | None = None,
):
    if run_id in RUN_EVENT_QUEUES:
        for q in RUN_EVENT_QUEUES[run_id]:
            q.put_nowait(event)

    try:
        from_st = str(event.from_state.value if isinstance(event.from_state, StoreState) else (event.from_state or ""))
        to_st = str(
            event.to_state.value
            if isinstance(event.to_state, StoreState)
            else (event.to_state or (event.state.value if isinstance(event.state, StoreState) else event.state))
        )

        db_event = StoreEventLog(
            run_id=UUID(run_id),
            retailer_id=event.retailer_id,
            from_state=from_st,
            to_state=to_st,
            progress_pct=event.progress_pct,
            message=event.detail or "",
            action_type=event.challenge_type,
            resume_token=event.resume_token,
            created_at=datetime.now(UTC),
        )

        if session:
            session.add(db_event)
            session.commit()
        else:
            try:
                from apps.api.main import app

                override_fn = app.dependency_overrides.get(get_session, get_session)
                active_session = next(override_fn())
                active_session.add(db_event)
                active_session.commit()
                active_session.close()
            except Exception:
                with Session(engine) as s:
                    s.add(db_event)
                    s.commit()
    except Exception as e:
        logger.warning("Failed to persist StoreEventLog for run %s: %s", run_id, e)
