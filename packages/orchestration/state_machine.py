import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StoreState(str, Enum):
    QUEUED = "QUEUED"
    SESSION_CHECK = "SESSION_CHECK"
    SEARCHING = "SEARCHING"
    MATCHING = "MATCHING"
    CART_PREPARING = "CART_PREPARING"
    CART_READING = "CART_READING"
    QUOTED = "QUOTED"
    PARTIAL = "PARTIAL"
    USER_ACTION_REQUIRED = "USER_ACTION_REQUIRED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    REVALIDATING = "REVALIDATING"
    REAPPROVAL_REQUIRED = "REAPPROVAL_REQUIRED"
    SUBMITTING = "SUBMITTING"
    CONFIRMED = "CONFIRMED"
    SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"


class StoreStateEvent(BaseModel):
    retailer_id: str
    run_id: str
    state: StoreState
    from_state: StoreState | None = None
    to_state: StoreState | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    progress_pct: int = 0
    detail: str | None = None
    challenge_type: str | None = None
    resume_token: str | None = None
    quote_id: str | None = None
    error_code: str | None = None

    @property
    def store_id(self) -> str:
        return self.retailer_id


class StateMachine:
    def __init__(self, run_id: str, retailer_id: str, event_callback: Callable[[StoreStateEvent], Any] | None = None):
        self.run_id = run_id
        self.retailer_id = retailer_id
        self.current_state = StoreState.QUEUED
        self.event_callback = event_callback
        self.history: list[StoreStateEvent] = []

    async def transition(
        self,
        new_state: StoreState,
        progress_pct: int = 0,
        detail: str | None = None,
        challenge_type: str | None = None,
        resume_token: str | None = None,
        quote_id: str | None = None,
        error_code: str | None = None
    ) -> StoreStateEvent:
        prev_state = self.current_state
        self.current_state = new_state
        event = StoreStateEvent(
            retailer_id=self.retailer_id,
            run_id=self.run_id,
            state=new_state,
            from_state=prev_state,
            to_state=new_state,
            progress_pct=progress_pct,
            detail=detail,
            challenge_type=challenge_type,
            resume_token=resume_token,
            quote_id=quote_id,
            error_code=error_code
        )
        self.history.append(event)
        if self.event_callback:
            res = self.event_callback(event)
            if asyncio.iscoroutine(res):
                await res
        return event
