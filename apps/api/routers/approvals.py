import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from domain.models.core import Approval, QuoteLine, StoreQuote
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from apps.api.core import ensure_utc, get_session
from apps.api.schemas import ApprovalCreate, QuoteApproveRequest

router = APIRouter(tags=["Approvals"])


@router.post("/quotes/{quote_id}/approve", status_code=status.HTTP_200_OK)
def approve_quote(
    quote_id: UUID,
    approve_req: QuoteApproveRequest,
    session: Session = Depends(get_session),
):
    quote = session.get(StoreQuote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store quote not found")

    if not quote.is_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INCOMPLETE_QUOTE_APPROVAL_FORBIDDEN",
                "message": "Cannot approve incomplete quote: missing required/must-have items.",
            },
        )

    if ensure_utc(quote.expires_at) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Store quote has expired. Please run a new comparison."
        )

    approval_token = f"appr_{uuid.uuid4().hex}"
    idempotency_key = approve_req.idempotency_key or f"idem_{uuid.uuid4().hex}"

    approval = Approval(
        quote_id=quote.id,
        approval_token=approval_token,
        idempotency_key=idempotency_key,
        delivery_slot_id=approve_req.delivery_slot_id,
        expected_fingerprint=quote.cart_fingerprint,
        is_used=False,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)

    lines = session.exec(select(QuoteLine).where(QuoteLine.quote_id == quote.id)).all()

    return {
        "approval_id": approval.id,
        "approval_token": approval.approval_token,
        "quote_id": quote.id,
        "retailer_id": quote.retailer_id,
        "gross_total_cents": quote.gross_total_cents,
        "expected_fingerprint": quote.cart_fingerprint,
        "delivery_slot_id": approval.delivery_slot_id,
        "expires_at": approval.expires_at,
        "lines": lines,
    }


@router.post("/approvals", status_code=status.HTTP_200_OK)
def create_approval(
    appr_req: ApprovalCreate,
    session: Session = Depends(get_session),
):
    quote = session.get(StoreQuote, appr_req.quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store quote not found")

    if not quote.is_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INCOMPLETE_QUOTE_APPROVAL_FORBIDDEN",
                "message": "Cannot approve incomplete quote: missing required/must-have items.",
            },
        )

    if ensure_utc(quote.expires_at) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Store quote has expired. Please run a new comparison."
        )

    approval_token = f"appr_{uuid.uuid4().hex}"
    idempotency_key = appr_req.idempotency_key or f"idem_{uuid.uuid4().hex}"

    approval = Approval(
        quote_id=quote.id,
        approval_token=approval_token,
        idempotency_key=idempotency_key,
        delivery_slot_id=appr_req.delivery_slot_id,
        expected_fingerprint=quote.cart_fingerprint,
        is_used=False,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)

    return {
        "approval_id": approval.id,
        "approval_token": approval.approval_token,
        "quote_id": quote.id,
        "retailer_id": quote.retailer_id,
        "gross_total_cents": quote.gross_total_cents,
        "expected_fingerprint": quote.cart_fingerprint,
        "delivery_slot_id": approval.delivery_slot_id,
        "expires_at": approval.expires_at,
    }


@router.get("/approvals/{approval_id}")
def get_approval(approval_id: UUID, session: Session = Depends(get_session)):
    approval = session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

    quote = session.get(StoreQuote, approval.quote_id)
    lines = session.exec(select(QuoteLine).where(QuoteLine.quote_id == approval.quote_id)).all() if quote else []

    return {
        "id": approval.id,
        "quote_id": approval.quote_id,
        "retailer_id": quote.retailer_id if quote else None,
        "delivery_slot_id": approval.delivery_slot_id,
        "expected_fingerprint": approval.expected_fingerprint,
        "is_used": approval.is_used,
        "approved_at": approval.approved_at,
        "expires_at": approval.expires_at,
        "quote": quote,
        "lines": lines,
    }
